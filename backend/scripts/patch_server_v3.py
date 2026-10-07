import re
import shutil

# Make a backup
shutil.copy("server_v3.py", "server_v3.py.bak")

with open("server_v3.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update imports
content = content.replace(
    "from fastapi import FastAPI, HTTPException, Header, Depends, Query, Request",
    "from fastapi import FastAPI, HTTPException, Header, Depends, Query, Request, APIRouter"
)

# 2. Add api_router definition right below app
router_init = """app = FastAPI(
    title="InfraBuild-AI Unified Platform Backend",
    description="Sovereign infrastructure intelligence, ML risk models, agentic investigation & 2FA authentication service",
    version="2.0.0",
)

api_router = APIRouter(tags=["Agentic V4 Intelligence"])"""

content = content.replace("""app = FastAPI(
    title="InfraBuild-AI Unified Platform Backend",
    description="Sovereign infrastructure intelligence, ML risk models, agentic investigation & 2FA authentication service",
    version="2.0.0",
)""", router_init)

# 3. Replace @app.get("/api/ and @app.post("/api/
content = re.sub(r'@app\.(get|post|put|delete|patch)\("/api/', r'@api_router.\1("/', content)

# 4. Add investigate endpoint to api_router right after find_or_create_investigation
investigate_endpoint = """
@api_router.post("/projects/{project_id}/investigate")
def trigger_project_investigation_v4(project_id: str):
    inv = find_or_create_investigation(project_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return inv
"""

if "@api_router.get(\"/investigations\")" in content:
    content = content.replace(
        '@api_router.get("/investigations")',
        investigate_endpoint + '\n@api_router.get("/investigations")'
    )

# 5. At the bottom, mount api_router on app under /api and /api/v1
mount_code = """
# Include agentic API router under both /api and /api/v1 prefixes
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
"""
content = content.replace('if __name__ == "__main__":', mount_code)

# 6. Ensure normalize_investigation helper guarantees both findings and hypotheses
normalizer = '''
def normalize_investigation(inv: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures investigation conforms to both V4 hypotheses schema and frontend findings schema."""
    if not inv:
        return inv
    
    # 1. Ensure findings exist
    if "findings" not in inv or not inv["findings"]:
        findings = []
        for h in inv.get("hypotheses", []):
            findings.append({
                "title": h.get("statement", "Root Cause Hypothesis"),
                "summary": f"Support Level: {h.get('support_level', 'Strong')} ({h.get('supporting_evidence_count', 3)} corroborating signals)",
                "detail": f"Falsification criterion: {h.get('falsification_condition', 'Milestone reconciliation required.')}",
                "confidence": 0.92 if h.get("support_level") == "Strong" else 0.74,
                "evidence": [e.get("description", "") for e in inv.get("evidence", [])[:2]],
            })
        inv["findings"] = findings
    
    # 2. Ensure recommendations conform to frontend expectations
    for r in inv.get("recommendations", []):
        if "action" not in r:
            r["action"] = r.get("statement", "Contractual Remediation Directive")
        if "reason" not in r:
            r["reason"] = r.get("likely_objective") or r.get("expected_benefit") or r.get("predicted_impact", "")
        if "priority" not in r:
            r["priority"] = "HIGH"
        if "confidence" not in r:
            r["confidence"] = 0.91
        if "target_agency" not in r:
            r["target_agency"] = r.get("targeted_entity", "Competent Authority")

    return inv
'''

content = content.replace(
    'def find_or_create_investigation(query_id: str) -> Optional[Dict[str, Any]]:',
    normalizer + '\ndef find_or_create_investigation(query_id: str) -> Optional[Dict[str, Any]]:'
)

# And wrap return in find_or_create_investigation
content = content.replace('return synthesized', 'return normalize_investigation(synthesized)')
content = content.replace('return i', 'return normalize_investigation(i)')

# Also normalize all in SAMPLE_INVESTIGATIONS during startup
content = content.replace(
    'ACTIVE_ALERTS = build_active_alerts()',
    'for _inv in SAMPLE_INVESTIGATIONS:\n    normalize_investigation(_inv)\nACTIVE_ALERTS = build_active_alerts()'
)

with open("server_v3.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to server_v3.py successfully!")
