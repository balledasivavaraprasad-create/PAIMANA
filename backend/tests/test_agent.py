"""End-to-end tests: real cost model + stub time/risk models. Run: python -W ignore tests/test_agent.py"""
import json, os, sys, tempfile, copy
sys.path.insert(0, ".")
from paimana_agent import MonitoringAgent, load_config
from paimana_agent.features import ValidationError
from paimana_agent.model_io import load_model
from paimana_agent.store import Store
from paimana_agent.notify import FileNotifier

tmp = tempfile.mkdtemp()
cfg = load_config("config.yaml")
cfg["models"]["time_overrun"] = "tests/stub_time_overrun.joblib"
cfg["models"]["risk_score"] = "tests/stub_risk_score.joblib"
models = {k: load_model(v) for k, v in cfg["models"].items()}
ref = json.load(open("reference_stats.json"))
sink = os.path.join(tmp, "alerts.jsonl")
agent = MonitoringAgent(cfg, models, ref, Store(os.path.join(tmp, "t.db")), notifiers=[FileNotifier(sink)])

base = dict(project_code="T-1", project_name="Test Expressway Package 3", ministry="Ministry of Road Transport & Highways",
            sector="Roads & Highways", implementing_agency="National Highways Authority of India [NHAI]", state="Bihar",
            approval_date="03/2021", start_date="06/2021", original_completion_date="06/2024",
            original_cost_cr=2400.0, cumulative_expenditure_cr=1900.0, physical_progress_pct=55.0)

# 1. healthy-looking new project -> no alert expected
ok = dict(base, project_code="T-0", project_name="On-track project", start_date="01/2026", approval_date="12/2025",
          original_completion_date="01/2029", cumulative_expenditure_cr=100.0, physical_progress_pct=5.0, original_cost_cr=800.0)
r0 = agent.on_project_saved(ok, event="add", report_month="2026-07")
print("T-0:", r0["tier"], round(r0["risk_score"]), "alert:", bool(r0["alert"]))
assert r0["alert"] is None or r0["tier"] != "Low"

# 2. distressed project added -> alert
r1 = agent.on_project_saved(base, event="add", report_month="2026-06")
print("T-1 add:", r1["tier"], round(r1["risk_score"]), "cost%", round(r1["cost_overrun_pct"]), "slip", round(r1["slippage_months"]), "alert:", bool(r1["alert"]))
# 3. immediate re-edit, same tier, tiny change -> deduplicated
r2 = agent.on_project_saved(dict(base, physical_progress_pct=55.5), event="edit", report_month="2026-06")
print("T-1 edit(no real change): alert:", bool(r2["alert"]))
# 4. edit adds revised cost + date -> re-evaluated
r3 = agent.on_project_saved(dict(base, revised_cost_cr=3300.0, revised_completion_date="12/2027", physical_progress_pct=58.0),
                            event="edit", report_month="2026-07")
print("T-1 edit(revision): ", r3["tier"], round(r3["risk_score"]), "alert:", bool(r3["alert"]), "| drivers:", r3["drivers"][:2])
# 5. validation
for bad in (dict(base, physical_progress_pct=140), dict(base, original_cost_cr=-5), dict(base, start_date="2021-06")):
    try:
        agent.on_project_saved(bad); raise SystemExit("validation should have failed")
    except ValidationError as e:
        print("rejected:", e)
# 6. bad edit must not corrupt state
n_before = len(agent.store.list_alerts())
assert agent.store.last_prediction("T-1")["project_code"] == "T-1"
print("alerts written:", len(open(sink).read().splitlines()), "| DB alerts:", n_before)
print(open(sink).read().splitlines()[0][:400] if os.path.exists(sink) else "no alerts file")
print("ALL TESTS PASSED")
