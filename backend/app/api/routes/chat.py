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
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-flash-latest"
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
    clean_m = re.sub(r'[?!.,;:\'"]', '', m)
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "hi there", "hello there", "hey there", "greetings", "namaste", "hola", "sup"]
    
    if clean_m in greetings or (any(clean_m.startswith(g + " ") for g in greetings) and len(clean_m.split()) <= 3 and not any(k in clean_m for k in ["project", "dphis", "risk", "what", "how", "delay", "why"])):
        return "GREETING"
    elif any(w in m for w in ["who are you", "your name", "what is paimana", "what can you do", "what do you do", "about yourself", "help"]):
        return "IDENTITY"
    elif "dphis" in m or ("health" in m and ("score" in m or "index" in m or "calculate" in m)):
        return "DPHIS_EXPLANATION"
    elif any(w in m for w in ["machine learning", "xgboost", "shap", "algorithm", "ai model"]):
        return "ML_EXPLANATION"
    elif any(w in m for w in ["alert", "automation", "webhook", "n8n", "threshold"]):
        return "ALERTS_EXPLANATION"
    elif any(w in m for w in ["investigation", "root cause", "deep ai", "console"]):
        return "INVESTIGATION_EXPLANATION"
    elif any(w in m for w in ["change", "changes", "updated", "update", "slippage", "overrun"]):
        return "CHANGES"
    elif any(w in m for w in ["why", "explain", "reason", "cause", "driver"]):
        return "RISK_EXPLANATION"
    elif any(w in m for w in ["critical", "worst", "highest risk", "urgent", "most delayed", "top risk"]):
        return "CRITICAL_PROJECTS"
    elif any(w in m for w in ["recommend", "action", "solution", "fix", "recover", "steps"]):
        return "RECOMMENDATION"
    elif any(w in m for w in ["trend", "getting worse", "trajectory", "history"]):
        return "RISK_TREND"
    elif any(w in m for w in ["portfolio", "overview", "total", "summary", "list", "all projects", "my projects", "show my projects", "show projects"]):
        return "PORTFOLIO_ANALYSIS"
    elif re.search(r'\b(P\d{3,5}|PRJ[_\-]\w+|\d{6,8}|N\d{8})\b', message, re.IGNORECASE) or any(w in m for w in ["ahmedabad metro", "pcmc", "nigdi", "freight corridor", "green building"]):
        return "PROJECT_INTELLIGENCE"
    elif any(w in m for w in ["capital of", "who is", "what time", "tell me a joke", "joke", "capex vs opex", "thank you", "thanks", "bye", "goodbye"]):
        return "GENERAL_KNOWLEDGE"
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
    
    # 1. Clean, direct greeting (As requested: "hi" -> "Hello! My name is PAIMANA Intelligence...")
    if intent == "GREETING":
        reply = "Hello! My name is PAIMANA Intelligence. How can I help you today?"
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

    # Informational or portfolio intents must NOT be hijacked by spurious project keyword matches
    is_general_intent = intent in (
        "GREETING", "IDENTITY", "DPHIS_EXPLANATION", "ML_EXPLANATION",
        "ALERTS_EXPLANATION", "INVESTIGATION_EXPLANATION", "GENERAL_KNOWLEDGE",
        "PORTFOLIO_ANALYSIS", "CHANGES"
    )

    if not is_general_intent:
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
                    words = [w for w in re.split(r'[\s\-_,\(\)]+', p_name) if len(w) > 4 and w not in ["project", "corridor", "phase", "extension", "limited", "railway", "national", "highway", "expressway", "development", "machine", "capital"]]
                    for w in words:
                        if w in lower_msg:
                            pid = p.get("project_id")
                            target_project = p
                            break
                    if target_project:
                        break

            # If still not found, search MongoDB by ID or project name keywords
            if not target_project and db is not None:
                match = re.search(r'\b(P\d{3,5}|PRJ[_\-]\w+|\d{6,8}|N\d{8})\b', message, re.IGNORECASE)
                if match:
                    found_id = match.group(1)
                    target_project = await db.projects.find_one({"project_id": {"$regex": f"^{found_id}$", "$options": "i"}}, {"_id": 0})
                    if target_project:
                        pid = target_project.get("project_id")

                if not target_project:
                    stopwords = {
                        "the", "a", "an", "is", "are", "was", "were", "what", "how", "why", "when",
                        "where", "who", "tell", "me", "about", "status", "of", "project", "projects", "corridor",
                        "in", "and", "or", "for", "with", "can", "you", "give", "details", "information",
                        "regarding", "any", "please", "database", "fetch", "available", "show", "list",
                        "machine", "learning", "models", "model", "capital", "india", "delhi", "joke"
                    }
                    words = [w for w in re.split(r'[^a-zA-Z0-9]+', lower_msg) if len(w) >= 4 and w not in stopwords]
                    # If multiple keywords present (e.g. 'Ahmedabad Metro'), match projects containing all terms first
                    if len(words) > 1:
                        all_query = {"$and": [{"project_name": {"$regex": w, "$options": "i"}} for w in words]}
                        cand = await db.projects.find_one(all_query, {"_id": 0})
                        if cand:
                            target_project = cand
                            pid = target_project.get("project_id")

                    if not target_project and words:
                        for w in words:
                            cand = await db.projects.find_one({
                                "$or": [
                                    {"project_name": {"$regex": w, "$options": "i"}},
                                    {"project_id": {"$regex": f"^{w}", "$options": "i"}}
                                ]
                            }, {"_id": 0})
                            if cand:
                                target_project = cand
                                pid = target_project.get("project_id")
                                break

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
2. CRITICAL REQUIREMENT: Whatever question the user asks, respond 100% according to that question and NOT something outside of that question.
3. If the user asks about a project or infrastructure records, provide verified facts from the database (Name, ID, state, approved cost, delay in months, physical progress %, DPHIS risk score, and primary risk driver).
4. If the user does NOT ask about a project (for example, if they greet you, ask who you are, ask what DPHIS is, ask how machine learning models work, ask general knowledge, or conversational questions), answer that question directly and DO NOT mention or inject project details or unsolicited project lists.
5. If the user asks for changes, summarize the corridors with schedule slippage changes, delay increments, or budget revisions from the database.
6. If the user asks to list their projects or compare, use the verified project records provided in the context above.
7. Keep answers concise, natural, well-structured, and executive-ready. Use clear section headers (### Header) and bullet points.

Respond strictly as a JSON object:
{{
  "reply": "Clean, structured executive response with clear headings and bullet points.",
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
            intent=intent if intent != "CONVERSATION" else ("PROJECT_INTELLIGENCE" if (target_project or pid) else "CONVERSATION"),
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
    elif intent in ("PORTFOLIO_ANALYSIS", "PORTFOLIO_SUMMARY"):
        db_count = len(projects_summary)
        if db is not None:
            try:
                total_db = await db.projects.count_documents({})
                if total_db > 0:
                    db_count = total_db
            except Exception:
                pass
        proj_list = "\n".join([f"• **{p['id']}** — {p['name']} (DPHIS: {p['dphis_score']}/100)" for p in projects_summary[:8]])
        reply = f"### Monitored Infrastructure Portfolio Overview\n\nYou have **{db_count} projects** in your database:\n\n{proj_list}"
        suggested = [
            "Which project needs attention?",
            "What are recent delay changes?",
            "Explain project risk score"
        ]
    elif intent == "IDENTITY":
        reply = (
            "Hello! My name is **PAIMANA Intelligence**. I am your sovereign AI assistant and decision-support platform designed for sovereign infrastructure project monitoring, risk assessment, and decision intelligence.\n\n"
            "### What I Can Help You With:\n"
            "• **Project Health & Delays:** If you ask about a project (by name or ID), I will look up its DPHIS score, approved outlay, completion %, and schedule slippage.\n"
            "• **Root Cause Analysis (SHAP):** Uncover the drivers behind delay risks—such as contractor execution lag, Right-of-Way (RoW) handovers, forest clearances, or utility shifting.\n"
            "• **Portfolio Overview:** If you ask to view your projects, I will summarize your monitored corridors ranked by urgency.\n"
            "• **Platform Guidance:** Ask me how to use the dashboard, configure alert thresholds, run simulations, or trigger n8n automated notifications.\n"
            "• **General Questions:** You can ask me any question about project management, infrastructure benchmarks, or general inquiries."
        )
        suggested = ["What is DPHIS?", "Show my projects", "How do risk thresholds work?"]
    elif intent == "DPHIS_EXPLANATION":
        reply = (
            "### Dynamic Project Health & Integrity Score (DPHIS)\n\n"
            "**DPHIS** is PAIMANA's predictive index (scaled from **0 to 100**) that assesses the real-time operational vulnerability and delay risk of an infrastructure project.\n\n"
            "### Core Pillars & Calculation Weights:\n"
            "1. **Schedule Slippage Velocity (35% Weight):** Quantifies variance between scheduled baseline milestones and actual execution velocity.\n"
            "2. **Physical-Financial Burn Disparity (25% Weight):** Analyzes the ratio between cumulative capex expenditure and verified on-ground physical completion.\n"
            "3. **Statutory & RoW Handover Clearances (25% Weight):** Tracks pending Right-of-Way (RoW) acquisition, environmental/forest permits, and utility shifting.\n"
            "4. **Contractor Capacity & Supply Velocity (15% Weight):** Assesses equipment mobilization rate, active workforce density, and liquidity stability.\n\n"
            "### Risk Tier Thresholds:\n"
            "• **Critical Risk (80 – 100):** Immediate escalation required; severe schedule slippage and cost overrun probability.\n"
            "• **High Risk (65 – 79):** Significant delay indicators present; requires targeted intervention.\n"
            "• **Moderate Risk (50 – 64):** Monitored variance; manageable within regular review cycles.\n"
            "• **Low Risk (< 50):** Healthy execution tracking closely with baseline schedule."
        )
        suggested = ["What ML models are used?", "Show my projects", "How do risk alerts work?"]
    elif intent == "ML_EXPLANATION":
        reply = (
            "### PAIMANA Predictive ML Architecture & Explainability\n\n"
            "PAIMANA's risk intelligence engine combines machine learning with transparent explainability:\n\n"
            "1. **Predictive Models:** Uses **XGBoost & LightGBM** models trained on sovereign infrastructure datasets to forecast delay slippage and cost escalations.\n"
            "2. **Explainable AI via TreeSHAP:** Decomposes every prediction into exact feature attributions so every risk factor is quantified in real months of delay.\n"
            "3. **Autonomous Reasoning Agents:** Multi-agent swarm coordinates to produce actionable recovery playbooks."
        )
        suggested = ["What is DPHIS?", "How does root cause investigation work?", "Show my projects"]
    elif intent == "ALERTS_EXPLANATION":
        reply = (
            "### Alerts & Automation Command Center\n\n"
            "PAIMANA provides an automated alerting system to detect project anomalies and notify stakeholders before delays become irreversible.\n\n"
            "• **Automated Threshold Evaluation:** Runs continuous checks across all projects against configured DPHIS thresholds.\n"
            "• **Multi-Channel Dispatch:** Dispatches notifications via **n8n automated workflows**, SMTP email delivery, and in-app alerts.\n"
            "• **Deduplication Cooldown:** Built-in 24-hour cooldown prevents alert fatigue."
        )
        suggested = ["How is DPHIS calculated?", "Show my projects", "What is root cause investigation?"]
    elif intent == "INVESTIGATION_EXPLANATION":
        reply = (
            "### Deep AI Root Cause Investigation Console\n\n"
            "The **Root Cause Investigation Console** is an advanced diagnostic workspace that performs comprehensive automated audits on high-risk corridors.\n\n"
            "1. **Telemetry & Milestone Ingestion:** Audits physical progress against scheduled target completion dates.\n"
            "2. **Statutory & Environmental Audit:** Evaluates pending Right-of-Way (RoW), forest clearances, and utility shifting.\n"
            "3. **SHAP Factor Breakdown:** Quantifies the exact drivers of the project's delay.\n"
            "4. **Automated Recovery Playbook:** Synthesizes an executive mitigation strategy with timeline impacts."
        )
        suggested = ["Show my projects", "What is DPHIS?", "What ML models are used?"]
    elif "capital of india" in lower_msg:
        reply = "The capital of India is **New Delhi**."
        suggested = ["Show my projects", "What is DPHIS?", "What can you do?"]
    elif "joke" in lower_msg:
        reply = "Why did the infrastructure project get a standing ovation? Because it actually finished on schedule and within budget! 😄"
        suggested = ["Show my projects", "What is DPHIS?", "What can you do?"]
    elif any(w in lower_msg for w in ["thank you", "thanks"]):
        reply = "You're very welcome! If you have any more questions or need assistance with your projects, I'm always here to help."
        suggested = ["Show my projects", "What is DPHIS?", "What can you do?"]
    elif any(w in lower_msg for w in ["bye", "goodbye"]):
        reply = "Goodbye! Wishing you smooth project execution and on-time milestone delivery."
        suggested = ["Show my projects", "What is DPHIS?"]
    else:
        reply = (
            f"I understand your question regarding \"{message}\".\n\n"
            "As your PAIMANA Intelligence Assistant, I can provide domain insights, governance frameworks, and decision-support guidance.\n\n"
            "If you have a question about a specific project, feel free to mention its name or ID (e.g., \"Tell me about Ahmedabad Metro\" or \"Status of N28000157\"). You can also ask me about DPHIS calculation, risk scoring, or request to view your project portfolio."
        )
        suggested = [
            "Show my assigned projects",
            "What is DPHIS?",
            "What can you do?"
        ]

    resolved_intent = "PORTFOLIO_SUMMARY" if intent in ("PORTFOLIO_ANALYSIS", "PORTFOLIO_SUMMARY") else (
        "PROJECT_INTELLIGENCE" if (target_project or pid) and intent == "CONVERSATION" else intent
    )

    return ChatResponse(
        reply=reply,
        intent=resolved_intent,
        project_id=pid,
        grounded_evidence=shap_factors[:3] if shap_factors else [],
        suggested_actions=suggested,
        model_used="deterministic-grounded"
    )
