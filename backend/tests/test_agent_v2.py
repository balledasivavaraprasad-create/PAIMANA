"""Smoke test for the v2 additions (events, per-project thresholds, scheduler,
investigator, SHAP, project memory) against the REAL models. Run:
  python -W ignore tests/test_agent_v2.py
"""
import json, os, sys, tempfile, copy
sys.path.insert(0, ".")
from paimana_agent import MonitoringAgent, load_config, Scheduler
from paimana_agent import memory as M
from paimana_agent.store import Store
from paimana_agent.notify import FileNotifier

tmp = tempfile.mkdtemp()
cfg = load_config("config.yaml")
agent = MonitoringAgent.from_config("config.yaml")
agent.store = Store(os.path.join(tmp, "v2.db"))
agent.notifiers = [FileNotifier(os.path.join(tmp, "alerts.jsonl"))]

base = dict(project_code="V-1", project_name="Test Bridge Corridor", ministry="Ministry of Road Transport & Highways",
            sector="Roads & Highways", implementing_agency="National Highways Authority of India [NHAI]", state="Bihar",
            approval_date="03/2019", start_date="06/2019", original_completion_date="06/2022",
            original_cost_cr=1800.0, cumulative_expenditure_cr=1200.0, physical_progress_pct=45.0)

peer = dict(base, project_code="V-2", project_name="Peer Bridge Corridor", cumulative_expenditure_cr=2000.0,
            revised_cost_cr=2600.0, physical_progress_pct=60.0)
agent.evaluate_project(peer, event="add", report_month="2026-01")
print("seeded 1 peer project for the Peer agent")

# per-project threshold (problem #4)
agent.store.set_threshold("V-1", 55)
print("set V-1's own alert threshold to 55")

r1 = agent.evaluate_project(base, event="add", report_month="2026-01")
print(f"V-1 add: tier={r1['tier']} score={round(r1['risk_score'])} events={[e['type'] for e in r1['events']]}")

# distressed follow-up edit -> should cross the low custom threshold and accelerate
distressed = dict(base, revised_cost_cr=2900.0, revised_completion_date="12/2027", physical_progress_pct=48.0)
r2 = agent.evaluate_project(distressed, event="edit", report_month="2026-03")
print(f"V-1 edit: tier={r2['tier']} score={round(r2['risk_score'])} events={[e['type'] for e in r2['events']]}")
print("why_changed:", r2["why_changed"][:3])
assert r2["events"], "expected at least one event on a distressed edit with a low custom threshold"

if r2["investigation"]:
    inv = r2["investigation"]
    print("investigation root_cause:", inv["root_cause"][:200])
    print("investigation recommendation:", inv["recommendation"])
    print("peer evidence:", inv["evidence"]["peers"])
    # human approval -> intervention recorded -> outcome recorded (problem #7 loop)
    agent.store.approve_investigation(inv["id"], approved_by="test-admin")
    iv_id = M.record_intervention(agent.store, "V-1", inv["recommendation"])
    M.record_outcome(agent.store, iv_id, "contractor recovery plan submitted, progress resumed next month")
    print("recorded intervention + outcome")
else:
    print("no investigation triggered on this run (events didn't include THRESHOLD_CROSSED/RISK_ACCELERATING)")

mem = M.project_memory(agent.store, "V-1")
print("project memory risk_history:", mem["risk_history"])
print("project memory issues:", mem["detected_issues"][:3])
print("project memory interventions:", mem["past_interventions"])
assert len(mem["risk_history"]) == 2

# scheduler / continuous trigger (problem #1): re-scan without any edit
scan_results = agent.run_scheduled_scan([distressed])
print("scheduled scan re-evaluated", len(scan_results), "project(s) with no edit")
assert scan_results[0]["event"] == "scheduled"

print("ALL V2 TESTS PASSED")
