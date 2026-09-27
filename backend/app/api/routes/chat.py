import os
import re
import json
import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.config.settings import settings
from app.config.logging import logger
from app.agents.tools import tool_get_project, tool_get_history, tool_get_shap, tool_get_milestones
from app.db.mongodb import get_database

router = APIRouter(prefix="/chat", tags=["AI Chatbot"])

# Dual-Model Fallback Architecture for Google Gemini Flash
PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-1.5-flash"

class ChatRequest(BaseModel):
    message: str
    project_id: Optional[str] = None
    user_role: Optional[str] = "PROJECT_OFFICER"
    username: Optional[str] = None
    ministry: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = []

class ChatResponse(BaseModel):
    reply: str
    intent: str
    project_id: Optional[str] = None
    grounded_evidence: List[Dict[str, Any]] = []
    suggested_actions: List[str] = []
    model_used: Optional[str] = None

def detect_intent(message: str) -> str:
    m = message.lower()
    if any(w in m for w in ["why", "explain", "reason", "cause", "driver"]):
        return "RISK_EXPLANATION"
    elif any(w in m for w in ["critical", "worst", "highest risk", "urgent", "most delayed"]):
        return "CRITICAL_PROJECTS"
    elif any(w in m for w in ["recommend", "action", "solution", "fix", "recover", "steps"]):
        return "RECOMMENDATION"
    elif any(w in m for w in ["trend", "getting worse", "trajectory", "history"]):
        return "RISK_TREND"
    elif any(w in m for w in ["portfolio", "overview", "total", "summary", "list", "all projects"]):
        return "PORTFOLIO_ANALYSIS"
    return "CONVERSATION"

def extract_project_id(message: str, fallback_id: Optional[str] = None, available_ids: List[str] = []) -> Optional[str]:
    # Check explicit pattern P1024 or PRJ_123 or numbers
    match = re.search(r'\b(P\d{3,5}|PRJ[_\-]\w+|\d{6,8})\b', message, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    # Check if any available project id is in the message
    m_upper = message.upper()
    for pid in available_ids:
        if pid.upper() in m_upper:
            return pid
    return fallback_id if fallback_id else None

async def call_gemini_with_fallback(prompt: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Invokes Gemini Flash API with automatic dual-model fallback mechanism:
    1. Primary: gemini-3.8-flash
    2. Fallback: gemini-flash-latest (triggers on 429 token/rate limit, 503, 500, or network error)
    Returns (parsed_json_dict, model_name).
    """
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("No GEMINI_API_KEY found in settings/env.")
        return None, None

    models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]

    for idx, model_name in enumerate(models_to_try):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            async with httpx.AsyncClient(timeout=18.0) as client:
                res = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "temperature": 0.25
                        }
                    }
                )

                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        clean_json = re.sub(r"^```json\s*", "", text.strip())
                        clean_json = re.sub(r"\s*```$", "", clean_json.strip())
                        parsed = json.loads(clean_json)
                        logger.info(f"Gemini response generated using {model_name} (attempt {idx + 1})")
                        return parsed, model_name

                logger.warning(
                    f"Gemini model {model_name} returned HTTP {res.status_code}: {res.text[:120]}. "
                    f"Triggering fallback..."
                )
        except Exception as e:
            logger.warning(f"Exception contacting Gemini model {model_name}: {e}. Triggering fallback...")

    return None, None

@router.post("", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    message = payload.message.strip()
    intent = detect_intent(message)
    is_admin = (payload.user_role or "").upper() in ("ADMIN", "ANALYST")
    
    db = get_database()
    
    # Retrieve user projects or national portfolio projects for context
    context_projects = []
    if db is not None:
        if is_admin:
            context_projects = await db.projects.find({}, {"_id": 0}).sort("dphis", -1).limit(12).to_list(length=12)
        else:
            uname = (payload.username or "").strip()
            min_filter = (payload.ministry or "").strip()
            query = {}
            if uname:
                u = await db.users.find_one({"username": uname})
                if u and u.get("assigned_projects"):
                    query = {"project_id": {"$in": u["assigned_projects"]}}
                else:
                    query = {"$or": [{"assigned_users": uname}, {"username": uname}]}
            elif min_filter and min_filter.lower() not in ("all", "central infrastructure", "mospi"):
                query = {"ministry": {"$regex": min_filter, "$options": "i"}}
                
            context_projects = await db.projects.find(query, {"_id": 0}).limit(10).to_list(length=10)
            if not context_projects:
                context_projects = await db.projects.find({}, {"_id": 0}).limit(6).to_list(length=6)

    available_pids = [p.get("project_id", "") for p in context_projects if p.get("project_id")]
    pid = extract_project_id(message, payload.project_id, available_pids)
    
    # Specific project data if focused
    target_project = None
    shap_factors = []
    if pid and db is not None:
        target_project = await db.projects.find_one({"project_id": {"$regex": f"^{pid}$", "$options": "i"}}, {"_id": 0})
        if target_project:
            shap_factors = await tool_get_shap(pid)
    
    if not target_project and pid:
        target_project = await tool_get_project(pid)

    # Prepare project summary list for grounding
    projects_summary = []
    for p in context_projects:
        projects_summary.append({
            "id": p.get("project_id"),
            "name": p.get("project_name"),
            "ministry": p.get("ministry"),
            "state": p.get("state"),
            "dphis_score": p.get("dphis", 50),
            "risk_level": p.get("risk_level", "moderate"),
            "physical_progress": p.get("physical_progress", 0),
            "cost_cr": p.get("cost", {}).get("revised") if isinstance(p.get("cost"), dict) else 1000,
            "delay": p.get("schedule_slippage_months", 0)
        })

    # Prepare role-based system prompts
    if is_admin:
        role_instruction = (
            "You are the InfraBuild AI National Infrastructure Director & Executive Assistant for MoSPI Admin. "
            "You provide high-level national oversight, systemic risk analysis, inter-ministerial comparisons, "
            "and portfolio-wide health evaluations across all states and central ministries."
        )
    else:
        role_instruction = (
            f"You are the InfraBuild AI Project Officer Assistant dedicated to supporting the project monitoring officer "
            f"({payload.username or 'Officer'}) under {payload.ministry or 'their department'}. "
            "You speak conversationally, answering their specific queries, comparing their assigned projects, "
            "explaining physical milestone lags, and suggesting realistic ground-level recovery steps."
        )

    # Format recent conversation history
    history_text = ""
    if payload.conversation_history:
        recent = payload.conversation_history[-4:]
        for h in recent:
            sender = "User" if h.get("sender") == "user" else "Assistant"
            history_text += f"{sender}: {h.get('text', '')}\n"

    # Targeted prompt engineering
    prompt = f"""
{role_instruction}

Context of Available Projects in this Account:
{json.dumps(projects_summary, indent=2)}

Focused Project (if specified by user or context):
{json.dumps(target_project if target_project else "No specific project selected yet. User is asking across their portfolio or general question.", indent=2)}

Specific SHAP Explainability Factors for Focused Project:
{json.dumps(shap_factors[:3] if shap_factors else [])}

Recent Conversation History:
{history_text if history_text else "None (New Conversation)"}

Current User Message: "{message}"

Instructions:
- Be interactive, natural, and helpful.
- If the user asks about a specific project, provide targeted insights, verified figures (cost, physical progress, DPHIS), and recovery recommendations.
- If the user asks generally (e.g. 'Which projects need attention?', 'Hello', 'What can you do?'), interact warmly, summarize their key projects from context, and invite them to explore specific projects.
- Never hallucinate data outside the provided projects context.

Respond strictly as a JSON object with:
1. "reply": Markdown formatted string with clear headings, bullet points, and actionable next steps.
2. "grounded_evidence": Array of 2 to 4 objects with "feature" and "impact" (e.g. [{{"feature": "Physical Progress", "impact": "34% vs 78% target"}}]).
3. "suggested_actions": Array of 3 short follow-up questions or actions relevant to the response.
"""

    gemini_data, model_used = await call_gemini_with_fallback(prompt)

    if gemini_data and "reply" in gemini_data:
        evidence = gemini_data.get("grounded_evidence", [])
        if not evidence and shap_factors:
            evidence = shap_factors[:3]
        suggested = gemini_data.get("suggested_actions", [])
        if not suggested:
            suggested = [
                "Which project has the highest delay risk?",
                "What are the main causes of cost overrun?",
                "Recommend an action plan for recovery"
            ]
        return ChatResponse(
            reply=gemini_data["reply"],
            intent=intent,
            project_id=pid,
            grounded_evidence=evidence,
            suggested_actions=suggested,
            model_used=model_used
        )

    # Deterministic Data-Grounded Fallback
    logger.info("Using deterministic data-grounded fallback for assistant reply.")
    if target_project:
        p_name = target_project.get("project_name", pid)
        dphis_val = target_project.get("dphis", 75.0)
        risk_lvl = target_project.get("risk_level", "high")
        cost_val = target_project.get("cost", {}).get("revised", 4200) if isinstance(target_project.get("cost"), dict) else 4200
        reply = (
            f"### Project Intelligence: **{p_name}** (`{pid}`)\n\n"
            f"- **DPHIS Health Score:** {dphis_val} / 100 ({risk_lvl.upper()})\n"
            f"- **Department:** {target_project.get('ministry', 'Central Infrastructure')}\n"
            f"- **Location:** {target_project.get('state', 'National')}\n"
            f"- **Approved Outlay:** ₹{cost_val} Cr\n\n"
            f"**Key Diagnosis:** Physical construction progress is lagging behind contractual targets. "
            f"Expenditure velocity should be reviewed against verified on-site milestones.\n\n"
            f"Would you like an in-depth investigation report or recommended recovery actions for this corridor?"
        )
        suggested = [
            f"Why is {pid} delayed?",
            f"Recommend catch-up plan for {pid}",
            "Check other assigned projects"
        ]
    elif projects_summary:
        top_delayed = sorted(projects_summary, key=lambda x: x.get("dphis_score", 0), reverse=True)[:3]
        proj_list = "\n".join([f"• **{p['id']}** ({p['name']}) — DPHIS: **{p['dphis_score']}** ({p['risk_level'].title()})" for p in top_delayed])
        reply = (
            f"Hello! I am your InfraBuild AI Assistant. You currently have **{len(projects_summary)} projects** monitored in your system.\n\n"
            f"**Projects Requiring Nearest Attention:**\n{proj_list}\n\n"
            f"Which of these projects would you like to inspect in detail, or how can I help you today?"
        )
        suggested = [
            f"Tell me about {top_delayed[0]['id']}" if top_delayed else "Show critical projects",
            "What is causing overall delays?",
            "How is DPHIS score calculated?"
        ]
    else:
        reply = (
            "Hello! I am your InfraBuild AI Assistant. I am connected to the national project monitoring engine. "
            "How can I help you monitor project delivery schedules, calculate budget burn risks, or inspect critical milestones today?"
        )
        suggested = [
            "Which projects are at highest risk?",
            "Explain schedule delay factors",
            "Show national portfolio overview"
        ]

    return ChatResponse(
        reply=reply,
        intent=intent,
        project_id=pid,
        grounded_evidence=shap_factors[:3] if shap_factors else [],
        suggested_actions=suggested,
        model_used="deterministic-engine"
    )
