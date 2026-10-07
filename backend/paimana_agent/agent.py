"""MonitoringAgent: the piece your add/edit-project code calls.

    agent = MonitoringAgent.from_config("config.yaml")
    result = agent.on_project_saved(project_dict, event="edit")   # or "add"

Flow: validate -> features (using previous snapshot) -> 3 model predictions ->
combined-score cross-check -> tier -> alert decision (escalation / jump / cooldown)
-> explanation -> dispatch (file + email + webhook) -> persist everything.
"""
from __future__ import annotations
import logging, math, os, time, json
from typing import Callable, Optional
import numpy as np, pandas as pd, yaml

from . import events as E
from . import features as F
from . import investigator as I
from .explain import drivers, template_summary, llm_summary
from .model_io import load_model
from .notify import build_notifiers, dispatch
from .shap_explain import shap_summary_lines, shap_top_features
from .store import Store, compute_snapshot_hash
from .supervisor import SupervisorAgent
from .tracer import AgentTracer
from .snapshot import CanonicalSnapshot, SnapshotSource, FreshnessState, compute_freshness

log = logging.getLogger(__name__)
TIER_ORDER = {"Low": 0, "Medium": 1, "High": 2}


def load_config(path: str = "config.yaml") -> dict:
    if not os.path.exists(path):
        pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alt = os.path.join(pkg_dir, path)
        if os.path.exists(alt):
            path = alt
    with open(path) as f:
        return yaml.safe_load(f)


def _pct_rank(sorted_arr: np.ndarray, v: float) -> float:
    """Percentile rank of v within the training distribution (matches pandas rank(pct=True), 'average' ties)."""
    lo = np.searchsorted(sorted_arr, v, side="left")
    hi = np.searchsorted(sorted_arr, v, side="right")
    return (lo + hi + 1) / 2.0 / len(sorted_arr)


class MonitoringAgent:
    def __init__(self, cfg: dict, models: dict, ref: dict, store: Store, notifiers=None):
        self.cfg, self.models, self.ref, self.store = cfg, models, ref, store
        self.notifiers = notifiers if notifiers is not None else build_notifiers(cfg)
        self._cost_sorted = np.array(ref["cost_overrun_sorted"])
        self._time_sorted = np.array(ref["slippage_sorted"])
        # rolling SHAP background (problem #5): real feature rows this agent has actually
        # seen, since reference_stats.json doesn't carry raw training rows. Starts empty
        # and SHAP enrichment quietly switches on once there's enough of it (>=5 rows);
        # until then the rule-based drivers in explain.py are the only explanation, same
        # as before -- SHAP is an enrichment, never a hard requirement.
        import collections
        self._shap_background = collections.deque(maxlen=50)
        self._risk_feature_cols = list(getattr(models["risk_score"], "feature_names_in_", []))

    def _remember_features(self, feats: dict):
        if self._risk_feature_cols:
            self._shap_background.append({c: feats.get(c) for c in self._risk_feature_cols})

    def _shap_bg_df(self) -> Optional[pd.DataFrame]:
        if len(self._shap_background) < 5:
            return None
        return pd.DataFrame(list(self._shap_background), columns=self._risk_feature_cols)

    @classmethod
    def from_config(cls, path="config.yaml"):
        if not os.path.exists(path):
            pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            alt = os.path.join(pkg_dir, path)
            if os.path.exists(alt):
                path = alt
        cfg = load_config(path)
        base = os.path.dirname(os.path.abspath(path))
        rp = lambda p: p if os.path.isabs(p) else os.path.join(base, p)
        models = {k: load_model(rp(v)) for k, v in cfg["models"].items()}
        with open(rp(cfg["reference_stats"])) as f:
            ref = json.load(f)
        return cls(cfg, models, ref, Store(rp(cfg["database"])))

    # ---------- prediction ----------
    def _predict(self, name: str, feats: dict) -> float:
        m = self.models[name]
        cols = list(getattr(m, "feature_names_in_", []))
        if not cols:
            raise RuntimeError(f"model {name} exposes no feature_names_in_")
        missing = [c for c in cols if c not in feats]
        if missing:
            raise RuntimeError(f"model {name} needs unknown features {missing}; update features.py")
        X = pd.DataFrame([{c: feats[c] for c in cols}], columns=cols)
        X = X.replace([np.inf, -np.inf], np.nan)
        return float(m.predict(X)[0])

    def combined_score(self, cost_pct: float, slip_months: float) -> float:
        """Rule-based 0-100 score from the two predictions, using the notebook-03 definition
        (0.5*pct-rank(cost) + 0.5*pct-rank(slip), negatives clipped to 0)."""
        c = _pct_rank(self._cost_sorted, max(cost_pct, 0.0))
        t = _pct_rank(self._time_sorted, max(slip_months, 0.0))
        return (0.5 * c + 0.5 * t) * 100.0

    def tier(self, score: float) -> str:
        r = self.cfg["risk"]
        return "High" if score >= r["high"] else "Medium" if score >= r["medium"] else "Low"

    # ---------- main entry ----------
    def on_project_saved(self, project: dict, event: str = "edit", report_month: Optional[str] = None, source: Optional[str] = None) -> dict:
        """The immediate, on-change trigger (README's original entry point)."""
        src = source or ("USER_EDIT" if event in ("add", "edit") else None)
        return self.evaluate_project(project, event=event, report_month=report_month, source=src)

    def run_scheduled_scan(self, projects: list[dict]) -> list[dict]:
        """The periodic trigger (scheduler.py, problem #1): re-evaluate every project
        supplied by the caller's project_provider even if nobody edited it, so slow
        drift (a milestone quietly slipping) surfaces without an add/edit. One bad
        record must not abort the whole scan."""
        out = []
        for proj in projects:
            try:
                out.append(self.evaluate_project(proj, event="scheduled", source="SCHEDULED_SCAN"))
            except F.ValidationError as ex:
                log.warning("scheduled scan: skipping invalid project %s: %s", proj.get("project_code"), ex)
            except Exception as ex:
                log.warning("scheduled scan: error evaluating project %s: %s", proj.get("project_code"), ex)
        return out

    def evaluate_project(self, project: dict, event: str = "edit", report_month: Optional[str] = None,
                         source: Optional[str] = None, source_record_id: Optional[str] = None) -> dict:
        p = F.validate(project)
        rep_period = report_month or p.get("report_month")
        R = F.report_index(rep_period)
        code = p["project_code"]

        # Canonical Snapshot construction
        canonical_snap = CanonicalSnapshot.create(
            p,
            source=source or event,
            source_record_id=source_record_id,
            report_month=rep_period
        )
        cur_hash = canonical_snap.snapshot_hash
        freshness_state = canonical_snap.freshness_state
        freshness_lag_months = canonical_snap.freshness_lag_months

        # Fast-Path: Material change detection via snapshot hashing BEFORE heavy ML prediction
        latest_snap = self.store.latest_snapshot(code)
        prev_hash = latest_snap.get("snapshot_hash") if latest_snap else None
        if not prev_hash and latest_snap:
            prev_hash = compute_snapshot_hash(latest_snap)
        last = self.store.last_prediction(code)
        is_same_month = (latest_snap is not None and latest_snap.get("report_index") == R)
        material_change = (prev_hash is None) or (cur_hash != prev_hash) or (not is_same_month)

        prev = self.store.previous_snapshot(code, R)
        feats = F.build_features(p, self.ref, prev, rep_period)

        warnings = []
        bg = None
        if not material_change and last is not None:
            # Bypass heavy ML prediction & SHAP: project data is unmutated
            cost = float(last["cost_overrun_pct"])
            slip = float(last["slippage_months"])
            risk_model = float(last["risk_score"])
            combined = float(last["combined_score"])
            shap_lines, shap_top = None, None
            self.store.record_project_check(code, False, "unmutated_check")
        else:
            cost = self._predict("cost_overrun", feats)
            slip = self._predict("time_overrun", feats)
            risk_model = self._predict("risk_score", feats)
            # sanity clamps: the score is 0-100 by construction, overrun can't go below -100%
            risk_model = float(np.clip(risk_model, 0, 100))
            cost = max(cost, -100.0)
            combined = self.combined_score(cost, slip)

            # SHAP enrichment (problem #5): real attributions once there's enough background
            self._remember_features(feats)
            shap_lines, shap_top = None, None
            bg = self._shap_bg_df()
            if bg is not None:
                shap_top = shap_top_features(self.models["risk_score"], feats, self._risk_feature_cols, bg)
                if shap_top:
                    shap_lines = shap_summary_lines(shap_top)
            self.store.record_project_check(code, True, "material_change")

        # Data freshness evaluation
        if freshness_state == FreshnessState.STALE:
            warnings.append(f"reporting data is {freshness_lag_months} months behind current calendar cycle (stale submission)")
        elif freshness_state == FreshnessState.UNAVAILABLE:
            warnings.append("reporting period unavailable or unparseable; freshness is UNAVAILABLE")
        feats["freshness_lag_months"] = freshness_lag_months
        feats["is_stale"] = float(freshness_state == FreshnessState.STALE)
        feats["freshness_state"] = freshness_state.value

        if abs(risk_model - combined) > self.cfg["risk"]["disagreement_threshold"]:
            warnings.append(f"risk model ({risk_model:.0f}) and combined cost/time score ({combined:.0f}) disagree; treat with caution")
        if math.isnan(feats["project_age_months"]):
            warnings.append("start_date missing: age/duration features unavailable, prediction less reliable")
        if prev is None:
            warnings.append("no earlier-month snapshot: progress-velocity features unavailable")

        # Concept Separation
        cur_tier = self.tier(risk_model)
        current_risk_state = {
            "risk_score": risk_model,
            "tier": cur_tier,
            "cost_overrun_pct": cost,
            "slippage_months": slip,
            "combined_score": combined,
        }

        prev_score = float(last["risk_score"]) if last else None
        prev_tier = last["tier"] if last else None
        delta_score = (risk_model - prev_score) if prev_score is not None else 0.0
        is_escalation = (last is not None and TIER_ORDER[cur_tier] > TIER_ORDER[prev_tier])
        is_jump = (prev_score is not None and delta_score >= self.cfg["alerting"]["min_score_jump"])
        risk_change = {
            "prev_score": prev_score,
            "current_score": risk_model,
            "delta_score": round(delta_score, 2),
            "prev_tier": prev_tier,
            "current_tier": cur_tier,
            "is_escalation": is_escalation,
            "is_jump": is_jump,
            "is_transition": is_escalation or (last is not None and TIER_ORDER[cur_tier] != TIER_ORDER[prev_tier]),
        }

        res = {"project_code": code, "project_name": p["project_name"], "event": event,
               "cost_overrun_pct": cost, "slippage_months": slip, "risk_score": risk_model,
               "combined_score": combined, "tier": cur_tier, "warnings": warnings,
               "material_change": material_change, "snapshot_hash": cur_hash,
               "data_freshness_months": freshness_lag_months,
               "is_stale": (freshness_state == FreshnessState.STALE),
               "freshness_state": freshness_state.value,
               "snapshot_id": canonical_snap.snapshot_id,
               "source": canonical_snap.source.value,
               "canonical_snapshot": canonical_snap.to_dict(),
               "current_risk_state": current_risk_state,
               "risk_change": risk_change,
               "material_data_change": material_change}
        ds = drivers(p, feats, res)
        res["drivers"] = ds
        res["summary"] = template_summary(p, res, ds)
        res["why_changed"] = shap_lines or [f"(rule-based, SHAP not yet available) {d}" for d in ds]
        res["detail"] = {"drivers": ds, "warnings": warnings, "shap": shap_top}

        last = self.store.last_prediction(code)          # read BEFORE we write the new one
        decision = self._decide(res, last, material_change=material_change)
        res["alert"] = None

        # Event engine: do not emit duplicate events on unchanged snapshot!
        if not material_change and last is not None:
            evs = []
            event_ids = []
        else:
            threshold = self.store.get_threshold(code, self.cfg["risk"].get("event_threshold", self.cfg["risk"]["high"]))
            evs = E.detect_events(res, feats, prev, last, threshold, self.cfg.get("events", {}))
            event_ids = [self.store.add_event(code, e["type"], e["severity"], e["message"],
                                              {"tier": res["tier"], "score": res["risk_score"]}) for e in evs]
        res["events"] = evs

        # Agentic investigation layer: triggered by operational events
        res["investigation"] = None
        if E.worth_investigating(evs, feats=feats, res=res):
            sup = SupervisorAgent(tracer=AgentTracer.auto_configure(self.cfg), llm_cfg=self.cfg.get("llm"))
            report = I.investigate(self.store, p, res, ds, evs, model=self.models["risk_score"],
                                   feats=feats, feature_cols=self._risk_feature_cols, background=bg,
                                   event_id=event_ids[0] if event_ids else None, ref_stats=self.ref,
                                   supervisor=sup)
            res["investigation"] = report
            for eid in event_ids:
                self.store.mark_investigated(eid)

        if decision["send"]:
            res["alert"] = self._send_alert(p, res, decision, shap_lines)

        self.store.save_snapshot(code, R, p, snapshot=canonical_snap)
        self.store.add_prediction(code, event, res)
        return res

    # ---------- alert policy ----------
    def _decide(self, res: dict, last: Optional[dict], material_change: bool = True) -> dict:
        a = self.cfg["alerting"]
        tier, score = res["tier"], res["risk_score"]
        at_risk = tier in a["alert_on"]
        prev_tier = last["tier"] if last else None
        escalated = last is not None and TIER_ORDER[tier] > TIER_ORDER[prev_tier]
        jump = last is not None and (score - last["risk_score"]) >= a["min_score_jump"]

        if escalated and a["alert_on_escalation"] and TIER_ORDER[tier] >= 1:
            return {"send": True, "reason": f"risk escalated {prev_tier} -> {tier}"}
        if not at_risk:
            return {"send": False, "reason": "below alert tier"}
        if last is None:
            return {"send": True, "reason": "new project rated at-risk"}
        if jump:
            return {"send": True, "reason": f"risk score up {score - last['risk_score']:.0f} points since last evaluation"}

        # Alert Deduplication: Suppress repeated alerts if no new material change
        if not material_change:
            return {"send": False, "reason": f"suppressed: project remains {tier} risk with no material change"}

        la = self.store.last_alert(res["project_code"])
        if la and (time.time() - la["ts"]) < a["cooldown_hours"] * 3600 and la["tier"] == tier:
            return {"send": False, "reason": "duplicate within cooldown"}
        return {"send": True, "reason": f"material change detected: project remains {tier} risk"}

    def _send_alert(self, p, res, decision, shap_lines: Optional[list[str]] = None) -> dict:
        sev = "CRITICAL" if res["tier"] == "High" else "WARNING"
        summary = llm_summary(self.cfg.get("llm", {}), p, res, res["drivers"], res["summary"])
        lines = [summary, "", f"Reason for alert: {decision['reason']}",
                 f"Predicted cost overrun: {res['cost_overrun_pct']:+.1f}%",
                 f"Predicted schedule slip: {res['slippage_months']:.0f} months",
                 f"Risk score: {res['risk_score']:.0f}/100 (combined cost/time cross-check: {res['combined_score']:.0f})"]
        if shap_lines:
            lines += ["", "Why did risk change? (top SHAP contributors)"] + [f"  {s}" for s in shap_lines]
        if res.get("events"):
            lines += ["", "Events:"] + [f"- {e['type']}: {e['message']}" for e in res["events"]]
        if res.get("investigation"):
            inv = res["investigation"]
            lines += ["", f"Agent Investigation ({inv.get('confidence', 'MEDIUM')} Confidence):",
                      f"  Hypothesis: {inv.get('root_cause_hypothesis') or inv.get('root_cause')}",
                      f"  Recommendation: {inv.get('recommendation')}"]
        if res["warnings"]:
            lines += ["", "Data/model cautions:"] + [f"- {w}" for w in res["warnings"]]
        alert = {"severity": sev, "project_code": res["project_code"], "project_name": res["project_name"],
                 "tier": res["tier"], "risk_score": res["risk_score"], "reason": decision["reason"],
                 "subject": f"[{sev}] {res['tier']} risk: {res['project_name'][:80]} ({res['project_code']})",
                 "message": "\n".join(lines), "ts": time.time()}
        channels, external = dispatch(self.notifiers, alert)
        alert["channels"], alert["delivered_external"] = channels, external
        alert["id"] = self.store.add_alert(res["project_code"], sev, res["tier"], res["risk_score"],
                                           decision["reason"], alert["message"], channels, external)
        if not external and len(self.notifiers) > 1:
            log.error("alert %s could not be delivered on any external channel", alert["id"])
        return alert
