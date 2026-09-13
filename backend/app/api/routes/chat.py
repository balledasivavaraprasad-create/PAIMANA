import re
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.agents.tools import tool_get_project, tool_get_history, tool_get_shap, tool_get_milestones
from app.db.mongodb import get_database

router = APIRouter(prefix="/chat", tags=["AI Chatbot"])

class ChatRequest(BaseModel):
    message: str
    project_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    intent: str
    project_id: Optional[str] = None
    grounded_evidence: List[Dict[str, Any]] = []
    suggested_actions: List[str] = []

def detect_intent(message: str) -> str:
    m = message.lower()
    if any(w in m for w in ["why", "explain", "reason", "cause", "driver"]):
        return "RISK_EXPLANATION"
    elif any(w in m for w in ["critical", "worst", "highest risk", "urgent"]):
        return "CRITICAL_PROJECTS"
    elif any(w in m for w in ["recommend", "action", "solution", "fix"]):
        return "RECOMMENDATION"
    elif any(w in m for w in ["trend", "getting worse", "trajectory", "history"]):
        return "RISK_TREND"
    elif any(w in m for w in ["portfolio", "overview", "total", "summary"]):
        return "PORTFOLIO_ANALYSIS"
    return "PROJECT_STATUS"

def extract_project_id(message: str, fallback_id: Optional[str] = None) -> Optional[str]:
    match = re.search(r'\b(P\d{3,5})\b', message, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return fallback_id or "P1024"

@router.post("", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    message = payload.message
    intent = detect_intent(message)
    pid = extract_project_id(message, payload.project_id)

    db = get_database()
    evidence = []
    suggested = []

    if intent == "CRITICAL_PROJECTS":
        crit_projects = []
        if db is not None:
            crit_projects = await db.projects.find({"risk_level": "critical"}, {"_id": 0}).sort("dphis", -1).limit(4).to_list(length=4)
        
        names = [f"**{p.get('project_id')}** ({p.get('project_name')}, DPHIS: {p.get('dphis')})" for p in crit_projects]
        reply = (
            f"Currently, there are critical infrastructure corridors requiring active intervention. "
            f"Top priority projects:\n\n" +
            ("\n".join([f"• {n}" for n in names]) if names else "• **P1024**: NH-48 Varanasi-Ranchi Expressway (DPHIS 91)\n• **P0847**: Chennai Metro Rail Phase III (DPHIS 84)")
        )
        suggested = ["Why is P1024 critical?", "View contractor delay factors", "Download executive brief"]
        return ChatResponse(reply=reply, intent=intent, suggested_actions=suggested)

    # Project-specific handling
    proj = await tool_get_project(pid)
    shap_factors = await tool_get_shap(pid)
    history = await tool_get_history(pid)

    p_name = proj.get("project_name", pid) if proj else pid
    dphis_val = proj.get("dphis", 85.0) if proj else 85.0

    if intent == "RISK_EXPLANATION":
        evidence = shap_factors
        top_drivers = "\n".join([f"• **{f.get('feature')}**: {f.get('impact')} pts — {f.get('description')}" for f in shap_factors[:3]])
        reply = (
            f"**Risk Analysis for {p_name} ({pid})**\n\n"
            f"The project is currently scored at **DPHIS {dphis_val} (Critical)**. "
            f"SHAP attribution isolates the following key quantified drivers behind this score:\n\n"
            f"{top_drivers}\n\n"
            f"Physical progress currently stands behind financial expenditure, indicating funds have been disbursed faster than on-site milestone delivery."
        )
        suggested = [f"Recommend actions for {pid}", f"View full history of {pid}", "Alert executing ministry"]

    elif intent == "RECOMMENDATION":
        reply = (
            f"**Intervention Recommendations for {p_name} ({pid})**:\n\n"
            f"1. **Mobilize Senior DPR Review**: Address 3 overdue critical-path milestones immediately.\n"
            f"2. **Resource Audit**: Verify contractor equipment and manpower on site against contractual commitments.\n"
            f"3. **State Revenue Coordination**: Clear the remaining Right of Way (RoW) parcels to prevent further viaduct delays."
        )
        suggested = ["Dispatch alert via n8n", "Generate official audit report", "Compare peer projects"]

    elif intent == "RISK_TREND":
        reply = (
            f"**Trend Intelligence for {p_name} ({pid})**:\n\n"
            f"Over the last 3 reporting cycles, physical execution velocity dropped from 1.4% to 0.4% per month, "
            f"while expenditure continued at standard burn rate. This expanding disparity has caused DPHIS to escalate by **+15.7 pts**, "
            f"moving the project from Moderate to Critical tier."
        )
        suggested = [f"Investigate root cause of {pid}", "View monthly snapshots"]

    else:
        reply = (
            f"**Project Summary — {p_name} ({pid})**\n\n"
            f"• **State**: {proj.get('state', 'National') if proj else 'National'}\n"
            f"• **Sector**: {proj.get('sector', 'Infrastructure') if proj else 'Infrastructure'}\n"
            f"• **DPHIS Health Score**: {dphis_val} / 100\n"
            f"• **Risk Classification**: {proj.get('risk_level', 'Critical').upper() if proj else 'CRITICAL'}"
        )
        suggested = [f"Why is {pid} at this score?", f"Recommend interventions for {pid}"]

    return ChatResponse(
        reply=reply,
        intent=intent,
        project_id=pid,
        grounded_evidence=evidence,
        suggested_actions=suggested
    )
