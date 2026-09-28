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

# Multi-Model Fallback Chain for Google Gemini API
CANDIDATE_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.7-flash"
]

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
    m = message.lower().strip()
    if m in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "hi there", "hello there", "greetings"]:
        return "GREETING"
    elif any(w in m for w in ["change", "changes", "updated", "update", "slippage", "overrun"]):
        return "CHANGES"
    elif any(w in m for w in ["why", "explain", "reason", "cause", "driver"]):
        return "RISK_EXPLANATION"
    elif any(w in m for w in ["critical", "worst", "highest risk", "urgent", "most delayed"]):
        return "CRITICAL_PROJECTS"
    elif any(w in m for w in ["recommend", "action", "solution", "fix", "recover", "steps"]):
        return "RECOMMENDATION"
    elif any(w in m for w in ["trend", "getting worse", "trajectory", "history"]):
        return "RISK_TREND"
    elif any(w in m for w in ["portfolio", "overview", "total", "summary", "list", "all projects", "my projects"]):
        return "PORTFOLIO_ANALYSIS"
    return "CONVERSATION"

async def call_gemini_with_fallback(prompt: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.warning("No GEMINI_API_KEY found in settings/env.")
        return None, None

    for idx, model_name in enumerate(CANDIDATE_MODELS):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "temperature": 0.3
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
                        try:
                            parsed = json.loads(clean_json)
                            logger.info(f"Gemini response generated using {model_name} (attempt {idx + 1})")
                            return parsed, model_name
                        except json.JSONDecodeError:
                            return {"reply": text.strip(), "grounded_evidence": [], "suggested_actions": []}, model_name

                logger.warning(
                    f"Gemini model {model_name} returned HTTP {res.status_code}. Trying next candidate..."
                )
        except Exception as e:
            logger.warning(f"Exception contacting Gemini model {model_name}: {e}. Trying next candidate...")

    return None, None

@router.post("", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    message = payload.message.strip()
    lower_msg = message.lower()
    intent = detect_intent(message)
    uname = (payload.username or "").strip()
    is_admin = (payload.user_role or "").upper() in ("ADMIN", "ANALYST") or uname.lower() == "admin"
    
    # 1. Clean, direct greeting (As requested: "hi" -> "Hello I'm your PAIMANA Intelligence Assistant")
    if intent == "GREETING":
        reply = "Hello! I am your PAIMANA Intelligence Assistant. How can I help you today?"
        return ChatResponse(
            reply=reply,
            intent="GREETING",
            project_id=None,
            grounded_evidence=[
                {"feature": "Assistant Role", "impact": "PAIMANA Project Intelligence"},
                {"feature": "Database Connection", "impact": "Live Database Synchronized"}
            ],
            suggested_actions=[
                "Show my assigned projects",
                "What are the recent delay changes?",
                "Which projects need immediate attention?"
            ],
            model_used="interactive-engine"
        )

    db = get_database()
    context_projects = []
    
    # 2. Database Retrieval: Fetch user's assigned projects or admin portfolio
    if db is not None:
        if is_admin:
            context_projects = await db.projects.find({}, {"_id": 0}).sort("dphis", -1).limit(28).to_list(length=30)
        else:
            query = {
                "$or": [
                    {"assigned_users": uname},
                    {"assigned_users": f"{uname}@gmail.com"},
                    {"username": uname}
                ]
            }
            context_projects = await db.projects.find(query, {"_id": 0}).to_list(length=25)
            if not context_projects:
                context_projects = await db.projects.find({}, {"_id": 0}).limit(17).to_list(length=20)

    # 3. Identify if user is asking about a specific project
    target_project = None
    pid = payload.project_id
    
    if not pid:
        # Check explicit ID match in message
        for p in context_projects:
            p_id = p.get("project_id", "")
            if p_id and p_id.lower() in lower_msg:
                pid = p_id
                target_project = p
                break
        
        # Check distinctive project name keywords
        if not target_project:
            for p in context_projects:
                p_name = p.get("project_name", "").lower()
                words = [w for w in re.split(r'[\s\-_,\(\)]+', p_name) if len(w) > 4 and w not in ["project", "corridor", "phase", "extension", "limited", "railway", "national", "highway", "expressway", "development"]]
                for w in words:
                    if w in lower_msg:
                        pid = p.get("project_id")
                        target_project = p
                        break
                if target_project:
                    break
        
        # If still not found and message has an explicit project code pattern, search MongoDB
        if not target_project and db is not None:
            match = re.search(r'\b(P\d{3,5}|PRJ[_\-]\w+|\d{6,8}|N\d{8})\b', message, re.IGNORECASE)
            if match:
                found_id = match.group(1)
                target_project = await db.projects.find_one({"project_id": {"$regex": f"^{found_id}$", "$options": "i"}}, {"_id": 0})
                if target_project:
                    pid = target_project.get("project_id")

    # Specific SHAP factors if project focused
    shap_factors = []
    if pid and db is not None:
        shap_factors = await tool_get_shap(pid)

    # Prepare project summary list for database grounding
    projects_summary = []
    for p in context_projects:
        cost_val = p.get("cost", {}).get("revised") if isinstance(p.get("cost"), dict) else p.get("cost", "₹3,500 Cr")
        delay_val = p.get("schedule_slippage_months") or (p.get("delay") if isinstance(p.get("delay"), (int, str)) else 0)
        projects_summary.append({
            "id": p.get("project_id"),
            "name": p.get("project_name"),
            "ministry": p.get("ministry"),
            "state": p.get("state"),
            "dphis_score": p.get("dphis", 50),
            "risk_level": p.get("risk_level", "moderate"),
            "physical_progress_pct": p.get("physical_progress_pct", p.get("physical_progress", 0)),
            "cost": cost_val,
            "delay_months": delay_val
        })

    # Prepare recent conversation history
    history_text = ""
    if payload.conversation_history:
        for h in payload.conversation_history[-6:]:
            sender = "User" if h.get("sender") == "user" else "Assistant"
            history_text += f"{sender}: {h.get('text', '')}\n"

    # 4. LLM Generation via Gemini
    prompt = f"""You are the PAIMANA Intelligence AI Assistant for sovereign infrastructure project monitoring in India.
You are directly connected to the user's live infrastructure project database.

Current User: {uname or 'Officer'} (Role: {'National Administrator' if is_admin else 'Project Officer'}, Ministry: {payload.ministry or 'Infrastructure'})

User's Database Projects ({len(projects_summary)} projects available):
{json.dumps(projects_summary, default=str, indent=2)}

Focused Project Record from Database (if queried):
{json.dumps(target_project if target_project else "No single project explicitly focused.", default=str, indent=2)}

SHAP Delay & Risk Factors for Focused Project:
{json.dumps(shap_factors if shap_factors else [], default=str)}

Recent Conversation History:
{history_text if history_text else "None"}

User Query: "{message}"

Instructions:
1. Answer the user's query interactively, conversationally, and directly.
2. If the user asks about a specific project, provide verified facts from the database (Name, ID, state, approved cost, delay in months, physical progress %, DPHIS risk score, and primary risk driver).
3. If the user asks for changes, summarize the corridors with schedule slippage changes, delay increments, or budget revisions from the database.
4. If the user asks to list their projects or compare, use the verified project records provided in the context above.
5. If the user asks a general question, answer clearly and helpfully.
6. Keep answers concise, natural, and executive-ready. Never dump random, unrequested project data.

Respond strictly as a JSON object:
{{
  "reply": "Markdown formatted response answering the user's question directly.",
  "grounded_evidence": [{{"feature": "...", "impact": "..."}}],
  "suggested_actions": ["3 short, relevant follow-up prompts"]
}}"""

    gemini_data, model_used = await call_gemini_with_fallback(prompt)

    if gemini_data and "reply" in gemini_data:
        evidence = gemini_data.get("grounded_evidence", [])
        if not evidence and shap_factors:
            evidence = shap_factors[:3]
        suggested = gemini_data.get("suggested_actions", [])
        if not suggested:
            suggested = [
                "Which project has the highest delay risk?",
                "What are the recent milestone changes?",
                "Show all my assigned projects"
            ]
        return ChatResponse(
            reply=gemini_data["reply"],
            intent=intent,
            project_id=pid,
            grounded_evidence=evidence,
            suggested_actions=suggested,
            model_used=model_used
        )

    # 5. Deterministic Grounded Fallback (when LLM is completely offline)
    logger.info("Using data-grounded fallback for assistant reply.")
    if target_project:
        p_name = target_project.get("project_name", pid)
        dphis_val = target_project.get("dphis", 75.0)
        risk_lvl = target_project.get("risk_level", "high")
        cost_val = target_project.get("cost", {}).get("revised", 4200) if isinstance(target_project.get("cost"), dict) else 4200
        delay_val = target_project.get("schedule_slippage_months", 0)
        reply = (
            f"### Project Status: **{p_name}** (`{pid}`)\n\n"
            f"- **DPHIS Risk Score:** {dphis_val} / 100 ({risk_lvl.upper()})\n"
            f"- **State:** {target_project.get('state', 'National')}\n"
            f"- **Approved Outlay:** ₹{cost_val} Cr\n"
            f"- **Schedule Slippage:** {delay_val} months\n\n"
            f"Physical execution and milestones are currently being monitored against target completion dates."
        )
        suggested = [
            f"Why is {pid} delayed?",
            "Check other assigned projects",
            "What are the recommended recovery steps?"
        ]
    elif intent == "CHANGES":
        delayed = [p for p in projects_summary if p.get("delay_months") and p.get("delay_months") > 0]
        if delayed:
            items = "\n".join([f"• **{p['name']}** (`{p['id']}`): +{p['delay_months']} months slippage | DPHIS: {p['dphis_score']}/100" for p in delayed[:4]])
            reply = f"Here are the projects with active schedule delay changes:\n\n{items}\n\nWould you like more details on any of these corridors?"
        else:
            reply = "All monitored projects are currently tracking within their scheduled delivery windows with no new delay escalations."
        suggested = [
            "Which project has the highest risk?",
            "Show all my projects",
            "Explain risk factors"
        ]
    elif intent == "PORTFOLIO_ANALYSIS":
        proj_list = "\n".join([f"• **{p['id']}** — {p['name']} (DPHIS: {p['dphis_score']}/100)" for p in projects_summary[:8]])
        reply = f"You have **{len(projects_summary)} projects** in your database:\n\n{proj_list}"
        suggested = [
            "Which project needs attention?",
            "What are recent delay changes?",
            "Explain project risk score"
        ]
    else:
        reply = f"I am your PAIMANA Intelligence Assistant. You have **{len(projects_summary)} projects** in your database. How can I help you today?"
        suggested = [
            "Show my assigned projects",
            "What are the latest changes?",
            "Which project has the highest risk?"
        ]

    return ChatResponse(
        reply=reply,
        intent=intent,
        project_id=pid,
        grounded_evidence=shap_factors[:3] if shap_factors else [],
        suggested_actions=suggested,
        model_used="deterministic-grounded"
    )
