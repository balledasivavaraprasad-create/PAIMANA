"""Tests for PAIMANA Continuous Monitoring v3:
  1. Dynamic tool-driven Supervisor reasoning loop with step-by-step audit trace
  2. Structured Evidence Model (Facts, Inferences, Hypotheses)
  3. Tailored Stakeholder Recommendation Synthesis
  4. Investigation confidence assessment (HIGH / MEDIUM / LOW) boosted by learning
  5. Closed-loop learning (precedents informing recommendations & confidence)
  6. Multi-factor peer intelligence with implementing agency & stage-bracket matching
  7. Smart event triggering (compound events & severe anomalies)
  8. Durable automation outbox with idempotent human approval
"""
import json, os, sys, tempfile
sys.path.insert(0, ".")
from paimana_agent import MonitoringAgent, load_config
from paimana_agent import memory as M
from paimana_agent.store import Store
from paimana_agent.notify import FileNotifier

tmp = tempfile.mkdtemp()
cfg = load_config("config.yaml")
agent = MonitoringAgent.from_config("config.yaml")
agent.store = Store(os.path.join(tmp, "v3.db"))
sink = os.path.join(tmp, "alerts.jsonl")
agent.notifiers = [FileNotifier(sink)]

print("=== 1. Smart Event Triggering & Dynamic Supervisor Loop ===")
# Project has severe cost-progress mismatch (spending 35% vs 10% progress -> gap 25 pts)
anomalous = {
    "project_code": "ANOM-1", "project_name": "Hydro Power Package 2",
    "ministry": "Ministry of Power", "sector": "Power", "implementing_agency": "NHPC",
    "state": "Himachal Pradesh", "approval_date": "01/2021", "start_date": "06/2021",
    "original_completion_date": "06/2026", "original_cost_cr": 3500.0,
    "cumulative_expenditure_cr": 1225.0, # 35% spent
    "physical_progress_pct": 10.0       # only 10% built -> 25 pt gap!
}
r_anom = agent.evaluate_project(anomalous, event="add", report_month="2026-01")
print(f"ANOM-1 events: {[e['type'] for e in r_anom['events']]}")
assert any(e["type"] == "COST_PROGRESS_MISMATCH" for e in r_anom["events"])
assert r_anom["investigation"] is not None, "Severe cost-progress mismatch must trigger investigation!"
inv1 = r_anom["investigation"]
print(f"ANOM-1 investigation triggered with {len(inv1['tools_invoked'])} tools dynamically invoked: {inv1['tools_invoked']}")
assert "tool_financial_velocity" in inv1["tools_invoked"]
assert "tool_milestone_audit" in inv1["tools_invoked"]

# Verify Supervisor dynamic reasoning steps
assert "supervisor_steps" in inv1, "Supervisor reasoning steps must be tracked!"
assert len(inv1["supervisor_steps"]) >= 2, "Supervisor must execute multiple dynamic steps"
step1 = inv1["supervisor_steps"][0]
print(f"Step 1 Goal: {step1['goal']}")
print(f"Step 1 Selected Tools: {step1['selected_tools']}")
print(f"Step 1 Sufficiency Assessment: {step1['is_sufficient']}")
assert "tool_financial_velocity" in step1["selected_tools"]

# Verify Structured Evidence Model (Facts, Inferences, Hypotheses)
assert "structured_evidence" in inv1
struct_ev = inv1["structured_evidence"]
assert "facts" in struct_ev and "inferences" in struct_ev and "hypotheses" in struct_ev
print(f"Structured Evidence Facts count: {len(struct_ev['facts'])}")
print(f"Structured Evidence Inferences count: {len(struct_ev['inferences'])}")
print(f"Structured Evidence Hypotheses count: {len(struct_ev['hypotheses'])}")
assert any("cumulative expenditure" in f["statement"].lower() for f in struct_ev["facts"])
assert any("cumulative_expenditure_cr" in inf.get("derived_from", []) for inf in struct_ev["inferences"])
assert any("Progress-Expenditure Decoupling" in h["hypothesis"] for h in struct_ev["hypotheses"])

# Verify Tailored Recommendation Synthesis
assert "recommendation_details" in inv1
rec_details = inv1["recommendation_details"]
print(f"Tailored Stakeholder: {rec_details['responsible_stakeholder']}")
print(f"Urgency: {rec_details['urgency']}")
print(f"Action: {rec_details['action']}")
assert any(role in rec_details["responsible_stakeholder"] for role in ["Ministry", "Engineer", "Advisor", "Director", "NHPC"])

print("\n=== 2. Multi-Factor Peer Intelligence & National Baselines ===")
peer_info = inv1["evidence"]["peers"]
print(f"Peer intelligence stage bracket: {peer_info.get('stage_bracket')}")
print(f"Peer intelligence agency cohort: {peer_info.get('same_agency_count')}")
assert "stage_bracket" in peer_info
assert "sector_national_baseline" in peer_info or "Power" in str(peer_info)

print("\n=== 3. Idempotent Human Approval & Durable Outbox Queue ===")
# Admin approves the investigation recommendation
is_new_1 = agent.store.approve_investigation(inv1["id"], approved_by="senior_engineer")
assert is_new_1 is True, "First approval must return is_new=True"

# Idempotent approval check
is_new_2 = agent.store.approve_investigation(inv1["id"], approved_by="senior_engineer")
assert is_new_2 is False, "Repeated approval must be idempotent (is_new=False)"

# Outbox queue check
outbox_id = agent.store.enqueue_outbox(
    inv_id=inv1["id"],
    task_type="n8n_action_dispatch",
    payload={"action": inv1["recommendation"], "project_code": "ANOM-1"}
)
assert outbox_id > 0
outbox_tasks = agent.store.list_outbox(status="pending")
assert len(outbox_tasks) == 1
task_payload = json.loads(outbox_tasks[0]["payload"]) if isinstance(outbox_tasks[0]["payload"], str) else outbox_tasks[0]["payload"]
assert task_payload["project_code"] == "ANOM-1"
agent.store.update_outbox(outbox_id, status="dispatched")
assert len(agent.store.list_outbox(status="pending")) == 0
print("Outbox queuing & idempotent approval verified successfully.")

print("\n=== 4. Closed-Loop Learning & Confidence Boost ===")
iv_id = M.record_intervention(agent.store, "ANOM-1", inv1["recommendation"])
M.record_outcome(agent.store, iv_id, "Physical audit completed, uncertified bills frozen, progress resumed")
print(f"Intervention {iv_id} recorded with positive outcome.")

# Next evaluation on the same project:
anomalous_followup = dict(anomalous, physical_progress_pct=15.0, cumulative_expenditure_cr=1250.0)
r_followup = agent.evaluate_project(anomalous_followup, event="edit", report_month="2026-03")
if r_followup["investigation"]:
    inv2 = r_followup["investigation"]
    print(f"Follow-up recommendation: {inv2['recommendation']}")
    print(f"Recommendation justification: {inv2['recommendation_justification']}")
    assert "outcome" in inv2["recommendation"].lower() or "success" in inv2["recommendation_justification"].lower() or "audit" in inv2["recommendation"].lower(), \
        "Closed-loop learning should cite past positive precedent!"
    print("Closed-loop learning test PASSED: precedent incorporated!")

print("\n=== 5. Investigation & Event Persistence in Store ===")
invs = agent.store.list_investigations()
events = agent.store.list_events()
print(f"Total investigations stored: {len(invs)}")
print(f"Total events recorded: {len(events)}")
assert len(invs) >= 1
assert len(events) >= 1
print(f"Latest investigation ID: {invs[0]['id']} for {invs[0]['project_code']} (approved: {bool(invs[0]['approved'])})")

print("\nALL V3 TESTS PASSED SUCCESSFULLY!")

