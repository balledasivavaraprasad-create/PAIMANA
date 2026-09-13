# PAIMANA — National Infrastructure Intelligence & AI Decision-Support Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![MongoDB](https://img.shields.io/badge/MongoDB-Motor-47A248.svg?style=flat&logo=mongodb)](https://www.mongodb.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-ML-EB5424.svg?style=flat)](https://xgboost.readthedocs.io)
[![SHAP](https://img.shields.io/badge/SHAP-Explainable_AI-FF6F00.svg?style=flat)](https://shap.readthedocs.io)

**PAIMANA** is a national-scale project intelligence and decision-support platform designed for central infrastructure ministries (MoSPI, MoRTH, Railways, Urban Affairs, Power, Shipping). Instead of a standard CRUD dashboard, PAIMANA implements a complete 10-step intelligence loop:

$$\text{Ingest} \to \text{Validate} \to \text{Engineer Features} \to \text{Predict (XGBoost)} \to \text{Score (DPHIS)} \to \text{Explain (SHAP)} \to \text{Investigate (LangGraph)} \to \text{Recommend} \to \text{Alert} \to \text{Learn}$$

---

## System Architecture

```text
PAIMANA Sources (CSV / Seed / API)
        │
        ▼
Data Ingestion (Pydantic Validation + Quality Score 0-100)
        │
        ▼
Project Intelligence DB (MongoDB: projects, project_snapshots, predictions, etc.)
        │
        ▼
Feature Engineering Engine (Financial, Schedule, Progress Velocity, Environmental, GIS)
        │
        ▼
ML Prediction Pipeline (XGBoost Cost Overrun + Schedule Delay + Risk Classification)
        │
        ▼
SHAP Explainability Service (Exact Feature Contribution Attribution)
        │
        ▼
DPHIS Engine (Dynamic Project Health & Intervention Score 0-100 + Trend Escalation Multiplier)
        │
   High Risk / Escalation?
   /                     \
  NO                     YES
  │                       │
  │                       ▼
  │               LangGraph Agentic Investigator (Evidence-First Tool Calling)
  │                       │
  │                       ▼
  │               Structured Recommendations with Grounded Evidence
  │                       │
  └───────────────────────┼───────────────────────┐
                          ▼                       │
                   Alert Engine                   │
          (Severity Escalation & Cooldown)        │
                          │                       │
                          ▼                       │
               FastAPI Webhook / n8n ◄────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
     React Frontend    AI Chat       Audit & Reports
```

---

## Features

1. **Executive Motion**: Cinematic 4-stage hero presentation with non-looping video, scroll-driven dimming, national health benchmarks, SHAP drivers, and nationwide project telemetry table.
2. **Project Intelligence**: Live DPHIS gauges, component breakdown bars, SHAP attribution, and XGBoost regressor estimates.
3. **Evidence-First Agentic Investigator**: Autonomous 6-tool execution sequence without hallucination (`tool_get_project`, `tool_get_history`, `tool_get_shap`, `tool_get_milestones`, `tool_get_environment`, `tool_compare_peers`).
4. **Macro Analytics**: Real-time aggregation across 1,500 projects and 18,000 monthly snapshots with 6-month risk trend analysis.
5. **Executive AI Assistant**: Intent-driven conversational assistant answering queries grounded in live MongoDB data.
6. **Alerts & Early Warnings**: State-transition deduplication, 24-hour cooldown, and outbound n8n webhook notifications.

---

## Quickstart Guide

### 1. Prerequisites
- Node.js 18+ & npm
- Python 3.11+
- MongoDB (Running locally on `mongodb://localhost:27017` or MongoDB Atlas)

### 2. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy environment settings
cp .env.example .env

# Seed realistic 1,500 projects & 18,000 monthly trajectory snapshots
PYTHONPATH=. python scripts/seed_data.py

# Train time-aware XGBoost models & save artifacts
PYTHONPATH=. python app/ml/training/train_pipeline.py

# Run test suite
PYTHONPATH=. pytest -v -o asyncio_mode=auto tests/test_backend.py

# Start FastAPI server (runs on http://localhost:8000)
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive Swagger API docs available at: **`http://localhost:8000/docs`**

### 3. Frontend Setup
```bash
# In the root project directory
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## Default Demo Credentials
- **Admin**: `username: admin`, `password: paimana2026`
- **Analyst**: `username: analyst`, `password: paimana2026`

---

## Project Structure
```text
PAIMANA/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI routers (auth, projects, risk, chat, etc.)
│   │   ├── config/              # Application settings and logging
│   │   ├── db/                  # Motor MongoDB connection and index management
│   │   ├── models/              # Pydantic data models
│   │   ├── services/            # Feature engine, DPHIS, SHAP, and alert services
│   │   ├── ml/                  # XGBoost models, artifacts, and training pipeline
│   │   ├── agents/              # LangGraph tools, investigator, and prompts
│   │   └── security/            # JWT, bcrypt, and RBAC permissions
│   ├── scripts/                 # Realistic database synthesizer (seed_data.py)
│   ├── tests/                   # Pytest test suite
│   ├── requirements.txt
│   └── .env.example
├── src/
│   ├── components/              # HeaderNav, CeoPinManager, GlassCard, etc.
│   ├── pages/                   # ProjectIntelligence, Investigation, Analytics, etc.
│   ├── lib/                     # Typed API client (api.ts)
│   ├── App.tsx                  # Executive Motion and module viewport
│   └── index.css                # Obsidian & Frosted Glass design tokens
├── public/                      # Static assets (video.mp4)
├── package.json
└── README.md
```
