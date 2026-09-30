# InfraBuild-AI / PAIMANA: Production n8n Webhook Alert Automation Setup

## 1. Architectural Overview & Core Principles

The InfraBuild-AI alert automation connects PAIMANA's sovereign continuous-monitoring engine with an **n8n webhook workflow** and **OpenAI/ChatGPT** to deliver factual, human-readable alert notifications to project stakeholders while guaranteeing that:

1. **Backend is the Sole Source of Truth**: The PAIMANA backend (XGBoost + LightGBM models, DPHIS engine, and alert threshold policies) determines **WHEN** an alert condition is triggered and **WHAT** verified facts occurred. n8n and ChatGPT never evaluate business rules or decide risk scores.
2. **AI Model Transforms Facts (Does Not Hallucinate Decisions)**: ChatGPT/OpenAI is strictly utilized to format verified facts (observed progress, predictive indicators, empirical peer cohort comparison, and SHAP drivers) into concise, government-appropriate alert notifications. If AI generation is unavailable, an automated deterministic fallback template is sent immediately.
3. **Strict Separation of Alerting vs Consequential Interventions**: This workflow is dedicated to **automated alerting**. Automated execution of consequential government interventions is strictly forbidden; human review and administrative approval remain mandatory.
4. **Durable Outbox & Zero Data Loss**: Every alert event is durably committed to the MongoDB `alerts` and `outbox_events` collections *prior* to network dispatch. Network timeouts, HTTP 5xx errors, or worker unreachability automatically transition events to `failed_retryable` with exponential backoff.
5. **Cryptographic Security & Idempotency**: All webhook requests are signed with HMAC-SHA256 (`X-PAIMANA-Signature`) and stamped with a unique `event_id` (`X-PAIMANA-Event-ID`) to reject unauthorized payloads and eliminate duplicate notifications.

```
PAIMANA / Project State
        ↓
Snapshot & Change Detection
        ↓
XGBoost & LightGBM Prediction
        ↓
DPHIS Calculation
        ↓
Event Engine & Threshold Evaluation
        ↓ (Threshold crossed / genuine transition)
NotificationAutomationService
        ↓
Durable Outbox (MongoDB)
        ↓
HMAC-SHA256 Signed POST
        ↓
========================= n8n Automation =========================
01 — PAIMANA Risk Webhook
        ↓
02 — Verify Signature (HMAC-SHA256 constant-time)
        ↓
03 — Validate Alert Payload (Mandatory field checks)
        ↓
04 — Idempotency Check (Suppresses repeated event_ids)
        ↓
05 — Build AI Context (Strict factual prompt & fallback template)
        ↓
06 — Generate Alert Email (OpenAI gpt-4o-mini / temp: 0.2)
        ↓
07 — Validate Email Content (Hallucination check & fallback resolution)
        ↓
08 — Send Infrastructure Alert (SMTP / Email Node)
        ↓
09 — Record Delivery (Audit logging & message reference)
        ↓
10 — Respond to PAIMANA (HTTP 200 with structured JSON)
==================================================================
        ↓
Recipient Receives Alert (Distinguishing observed facts from predictions)
```

---

## 2. Environment Variables Configuration

Configure the following environment variables in your backend environment (`.env`) and n8n environment:

### Backend Variables (`backend/.env`)

```ini
# n8n Alert Webhook Endpoint
N8N_ALERT_WEBHOOK_URL=http://localhost:5678/webhook/paimana-risk-alert
# Fallback / Alternative Webhook
N8N_THRESHOLD_WEBHOOK_URL=http://localhost:5678/webhook/paimana-risk-alert

# Cryptographic Shared Secret for HMAC-SHA256 signing
N8N_WEBHOOK_SECRET=paimana-n8n-alert-secret-key-2026

# OpenAI API Key (Optional for backend fallback generator)
OPENAI_API_KEY=sk-...

# Sender Address for System Alerts
EMAIL_FROM=infrabuild-ai@paimana.gov.in

# Outbox Retry Settings
OUTBOX_MAX_RETRIES=3
OUTBOX_RETRY_BACKOFF_MINUTES=5
```

### n8n Environment Variables

```ini
# Port and Webhook Configuration
N8N_PORT=5678
WEBHOOK_URL=http://localhost:5678/

# Shared Secret matching the backend
N8N_WEBHOOK_SECRET=paimana-n8n-alert-secret-key-2026
STRICT_HMAC_REQUIRED=true

# OpenAI API Key for AI email generation
OPENAI_API_KEY=sk-...

# SMTP Configuration
EMAIL_FROM=infrabuild-ai@paimana.gov.in
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-alerts@example.gov.in
SMTP_PASSWORD=your-app-password
SMTP_SSL=false
```

---

## 3. Webhook Specification

- **Method**: `POST`
- **Path**: `/webhook/paimana-risk-alert`
- **Content-Type**: `application/json`

### HTTP Headers

| Header | Description |
| :--- | :--- |
| `Content-Type` | `application/json` |
| `X-PAIMANA-Signature` | `sha256=<hex_digest>` computed over raw request body with `N8N_WEBHOOK_SECRET` |
| `X-PAIMANA-Event-ID` | Unique UUID event identifier (e.g., `evt_4a7b9c1d2e3f`) |
| `X-PAIMANA-Timestamp` | ISO 8601 UTC timestamp of event generation |

### Standard Payload Schema

```json
{
  "event_id": "evt_abc123456789",
  "event_type": "THRESHOLD_CROSSED",
  "project": {
    "project_code": "612786",
    "project_id": "612786",
    "project_name": "Bengaluru Suburban Rail Project Corridor 2",
    "ministry": "Ministry of Railways",
    "sector": "Railways & Urban Transit",
    "implementing_agency": "K-RIDE",
    "state": "Karnataka"
  },
  "recipient": {
    "email": "official@kride.gov.in",
    "name": "Shri Ramesh Kumar"
  },
  "user": {
    "user_id": "USR-OFFICER-44",
    "name": "Shri Ramesh Kumar",
    "email": "official@kride.gov.in"
  },
  "admin": {
    "email": "syntaxtrrors@gmail.com"
  },
  "risk": {
    "previous_dphis": 61.4,
    "current_dphis": 77.2,
    "threshold": 70.0,
    "risk_tier": "High",
    "risk_trend": "increasing",
    "severity": "HIGH",
    "crossed_by": 7.2
  },
  "predictions": {
    "predicted_cost_overrun_pct": 18.4,
    "predicted_schedule_slippage_months": 7.2
  },
  "progress": {
    "physical_progress_pct": 48.2,
    "expenditure_pct": 67.5
  },
  "events": [
    "THRESHOLD_CROSSED",
    "COST_PROGRESS_MISMATCH"
  ],
  "explanations": {
    "shap_drivers": [
      "expenditure_progress_gap",
      "schedule_slippage",
      "project_age"
    ],
    "summary": "Risk escalation driven by: expenditure progress gap, schedule slippage."
  },
  "peer_intelligence": {
    "available": true,
    "peer_count": 14,
    "peer_median_dphis": 49.8,
    "peer_deviation": 27.4,
    "peer_status": "project_specific_outlier"
  },
  "investigation": {
    "status": "pending",
    "investigation_id": "inv_612786_e8c19a"
  },
  "links": {
    "project_url": "https://paimana-seven.vercel.app?project=612786",
    "investigation_url": "https://paimana-seven.vercel.app?investigation=612786"
  },
  "project_url": "https://paimana-seven.vercel.app?project=612786",
  "metadata": {
    "observed_at": "2026-09-30T15:00:00Z",
    "source": "paimana_monitor",
    "model_version": "v2.4-XGBoost+LightGBM"
  }
}
```

---

## 4. n8n 10-Node Workflow Architecture

The production workflow file is located at `n8n_paimana_risk_alert_workflow.json` (also mirrored at `n8n/n8n_paimana_risk_alert_workflow.json`). It contains 10 distinct, observable nodes:

```
[01 — PAIMANA Risk Webhook]
          ↓
[02 — Verify Signature]
          ↓
[03 — Validate Alert Payload]
          ↓
[04 — Idempotency Check]
          ↓
[05 — Build AI Context]
          ↓
[06 — Generate Alert Email]
          ↓
[07 — Validate Email Content]
          ↓
[08 — Send Infrastructure Alert]
          ↓
[09 — Record Delivery]
          ↓
[10 — Respond to PAIMANA]
```

### Node Descriptions

1. **`01 — PAIMANA Risk Webhook`**: Receives signed incoming HTTP POST events at `/webhook/paimana-risk-alert`. Configured in `responseNode` mode so response is deferred to Node 10.
2. **`02 — Verify Signature`**: Computes HMAC-SHA256 of raw body against `N8N_WEBHOOK_SECRET` and executes timing-safe comparison with `X-PAIMANA-Signature`. Rejects forged or tampered requests immediately.
3. **`03 — Validate Alert Payload`**: Verifies presence of mandatory fields (`event_id`, `project_code`, `current_dphis`, `recipient.email`). Emits `malformed_payload` error if requirements are not met.
4. **`04 — Idempotency Check`**: Consults `$getWorkflowStaticData('global')` cache for `event_id`. If previously processed, marks state as `duplicate` and routes directly to response, preventing duplicate emails.
5. **`05 — Build AI Context`**: Assembles strict system and user prompts for OpenAI. Concurrently generates a deterministic fallback template containing all verified facts, links, and benchmarks.
6. **`06 — Generate Alert Email`**: Calls OpenAI Chat Completions API (`gpt-4o-mini`, temperature `0.2`) with `continueOnFail: true`. Requests JSON output containing `subject` and `text_content`.
7. **`07 — Validate Email Content`**: Inspects AI response. If AI succeeds, converts to responsive HTML; if OpenAI fails, times out, or returns invalid JSON, automatically activates the deterministic fallback template.
8. **`08 — Send Infrastructure Alert`**: Transmits email via SMTP to `recipient.email` with `continueOnFail: true`.
9. **`09 — Record Delivery`**: Formulates audit delivery record (`event_id`, `project_code`, `recipient`, `event_type`, `email_status`, `provider_reference`).
10. **`10 — Respond to PAIMANA`**: Returns JSON response with `ok`, `event_id`, `status` (`accepted` / `duplicate` / `rejected`), and `delivery_status`.

---

## 5. OpenAI / ChatGPT Grounding & Strict Prompt Rules

The AI model is configured strictly as a **transformer of verified facts into human-readable text**, NOT an analytical decision-maker.

### System Prompt

```text
You are writing an infrastructure project monitoring alert for an authorized project stakeholder.

Use only the structured facts supplied in the input.
Do not invent facts.
Do not claim causal certainty unless the evidence explicitly supports it.
Clearly distinguish observed facts from possible explanations.
Be concise and professional.
The purpose of the email is to inform the recipient that a monitoring condition has been detected and direct them to the relevant project/investigation page.
```

### Email Structure & Standards

- **Subject**: `[PAIMANA ALERT] <Project Name> — DPHIS threshold crossed`
- **Distinction of Signals**:
  - **Observed facts**: *"Observed data indicates that expenditure has increased faster than physical progress."*
  - **Model predictions**: *"Model predictions indicate elevated schedule risk (+7.2 months)."*
  - **Peer benchmark**: *"Peer comparison places this project above the current peer-cohort risk benchmark."* (Or explicitly: *"Peer comparison was not used because insufficient comparable projects were available."*)
  - **Actionable Links**: Direct links to the deep AI investigation dossier and project dashboard.
  - **Human Review Safeguard**: Explicit disclaimer that consequential interventions require administrative approval.

---

## 6. Durable Outbox & Failure Resilience

1. **Before Network Call**: An outbox record (`outbox_id`, `event_id`, `status: pending`, payload, headers) is committed to MongoDB `outbox_events`.
2. **Success (HTTP 200/201/202)**: Outbox status updated to `dispatched` with `latency_ms` and `response_status_code`.
3. **Transient Failure (HTTP 5xx, Network Timeout, Connection Refused)**:
   - Outbox status updated to `failed_retryable`.
   - `next_retry_at` scheduled with exponential backoff (default +5 minutes).
   - Alert in `alerts` collection marked `notification_status: failed`.
   - Continuous monitoring scan does **NOT** crash; scanning continues uninterrupted.
4. **Retry Mechanism**: The background job `notification_automation_service.process_outbox_retries(max_retries=3)` scans for pending retries and re-dispatches them with original HMAC signatures.
5. **Dead Letter**: If retries exceed `max_retries`, the event is transitioned to `dead_letter` for operator inspection.

---

## 7. Testing & Verification

All 15 verification scenarios have been implemented and validated in `backend/tests/test_n8n_alert_automation.py`:

```bash
# Run the 15 alert automation scenarios
./backend/.venv/bin/pytest backend/tests/test_n8n_alert_automation.py -v

# Run the integration and RBAC test suite
./backend/.venv/bin/pytest backend/tests/test_integrations_and_rbac.py -v

# Run the threshold event engine tests
./backend/.venv/bin/pytest backend/tests/test_thresholds_and_events.py -v

# Run frontend tests
npm test -- --run
```

### Verified Test Matrix

| # | Test Scenario | Verified Behavior |
| :--- | :--- | :--- |
| 1 | DPHIS crosses threshold | Webhook event created, signed, and dispatched; alert saved with status `sent`. |
| 2 | DPHIS already above threshold | Continuous high score ($74 \to 75$) suppressed; no duplicate webhook or email. |
| 3 | Risk acceleration | `RISK_ACCELERATING` event dispatched with acceleration metadata. |
| 4 | No meaningful change | Unchanged score below threshold suppressed; no webhook fired. |
| 5 | Duplicate `event_id` | n8n / backend idempotency check suppresses duplicate email; returns `duplicate`. |
| 6 | n8n network timeout | Caught gracefully; event saved as `failed_retryable` in outbox with `next_retry_at`. |
| 7 | n8n HTTP 500 error | Saved as `failed_retryable` in outbox; monitoring scan does not crash. |
| 8 | Malformed payload | Missing `project_id` or `current_dphis` rejected safely at validation boundary. |
| 9 | Invalid signature | Tampered HMAC-SHA256 signature rejected in constant time. |
| 10 | Missing recipient email | Validation fails safely with descriptive error; no unhandled crash. |
| 11 | OpenAI failure | Deterministic fallback template activates with observed facts and links. |
| 12 | Email send failure | Outbox retry engine retries with backoff and routes to `dead_letter` on max retries. |
| 13 | Missing peer data | Fallback text states insufficient comparable peers; email sends successfully. |
| 14 | Missing SHAP data | Falls back to generic risk driver summary without raising exceptions. |
| 15 | Unavailable investigation URL | Default portal URLs generated safely without broken links. |

---

## 8. Importing the Workflow into n8n

1. Open your n8n web interface (e.g. `http://localhost:5678`).
2. Go to **Workflows** $\to$ **Add Workflow** $\to$ **Import from File**.
3. Select `n8n_paimana_risk_alert_workflow.json`.
4. Configure credentials:
   - In **06 — Generate Alert Email**: Ensure `OPENAI_API_KEY` is present in your n8n environment or configure Header Auth.
   - In **08 — Send Infrastructure Alert**: Select your SMTP credential or enter SMTP account details.
5. Click **Save** and toggle the workflow to **Active**.
6. The webhook is now listening at `POST /webhook/paimana-risk-alert`.
