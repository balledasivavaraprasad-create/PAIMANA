# PAIMANA / InfraBuild-AI — CI/CD Pipeline Architecture & Setup Guide

**Author**: PAIMANA Architecture Team  
**Date**: September 28, 2026  
**Repository**: [balledasivavaraprasad-create/PAIMANA](https://github.com/balledasivavaraprasad-create/PAIMANA)  

---

## 1. Overview & Pipeline Philosophy

The InfraBuild-AI / PAIMANA repository implements a modern, dual-tier Continuous Integration and Continuous Deployment (CI/CD) system utilizing GitHub Actions.

### Operational Principles
- **No Platform Migration**: Backend runs on Render (`https://paimana-backend.onrender.com`); Frontend runs on Vercel (`https://paimana-seven.vercel.app`). Neither service is migrated or rebuilt from scratch.
- **Strict Quality Gating**: No code is verified for production unless all 44 backend tests, 6 frontend tests, security scanners, and bundle builds pass 100%.
- **Zero-Downtime Deployment & Automated Smoke Tests**: After push to `main`, deployment hooks or git integration triggers deployment, followed immediately by automated smoke tests with polling retries against live production endpoints.

---

## 2. CI/CD Architecture Flow

```
+-------------------------------------------------------------+
|                GIT COMMIT / PULL REQUEST                    |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|     GITHUB ACTIONS CI WORKFLOW (.github/workflows/ci.yml)    |
|                                                             |
|  +------------------------+  +---------------------------+  |
|  |   Backend Tests (Py)   |  |   Frontend Tests (Vitest) |  |
|  | - 44 Pytest Suites     |  | - 6 Unit Component Tests  |  |
|  | - Coverage Report      |  | - Vite Production Build   |  |
|  | - Real Model Smoke     |  | - Verify dist/ Artifacts  |  |
|  +------------------------+  +---------------------------+  |
|                             |                               |
|              +-----------------------------+                |
|              | Security & API Key Scanners |                |
|              +-----------------------------+                |
|                             |                               |
|                             v                               |
|              +-----------------------------+                |
|              |         CI GATE PASS        |                |
|              +-----------------------------+                |
+-------------------------------------------------------------+
                              | (Only on push to `main` passing CI)
                              v
+-------------------------------------------------------------+
|     GITHUB ACTIONS CD WORKFLOW (.github/workflows/cd.yml)    |
|                                                             |
|  +---------------------------+  +------------------------+  |
|  | Deploy Backend → RENDER   |  | Deploy Frontend → VERCEL|  |
|  | - Render Webhook / GitSync|  | - Vercel Git Integration|  |
|  | - Wait for Service Spin-up|  | - Wait for Edge Bundle |  |
|  | - Smoke Test /health (200)|  | - Smoke Test Live URL  |  |
|  | - Smoke Test /risk-ovw    |  | - Verify SPA #root DOM |  |
|  +---------------------------+  +------------------------+  |
|                              |                              |
|                              v                              |
|  +-------------------------------------------------------+  |
|  |             PRODUCTION DEPLOYMENT VERIFIED            |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
```

---

## 3. Workflow Specifications

### A. CI Pipeline (`.github/workflows/ci.yml`)
Triggered on every `push` to `main`, `pull_request` to `main`, and manual dispatch (`workflow_dispatch`).

1. **Job 1: `backend-agent-tests`**
   - Sets up Python 3.11 with pip caching.
   - Installs backend dependencies from `backend/requirements.txt`.
   - Runs `pytest tests -v --cov=app --cov-report=term-missing --cov-report=xml`.
   - Generates and uploads code coverage report artifact.
   - Uses in-memory `AsyncMongoMockClient` fallback if external database is unavailable.

2. **Job 2: `frontend-tests-and-build`**
   - Sets up Node.js 22 with npm caching.
   - Installs dependencies via `npm ci || npm install`.
   - Executes Vitest unit tests via `npm test`.
   - Compiles production distribution bundle via `npm run build`.
   - Asserts `dist/index.html` and `dist/assets` exist.

3. **Job 3: `security-and-lint`**
   - Scans codebase for accidentally committed Google API keys (`AIzaSy...`) or plaintext MongoDB credentials outside secure environment configurations.

4. **Job 4: `ci-gate`**
   - Collects results from all prerequisite jobs.
   - Enforces 100% success before clearing the commit for deployment.

---

### B. CD Pipeline (`.github/workflows/cd.yml`)
Triggered automatically when the CI Pipeline workflow completes successfully on `main`, or manually via `workflow_dispatch`.

1. **Job 1: `deploy-and-smoke-backend`**
   - Optionally fires `RENDER_DEPLOY_HOOK_URL` if configured in repository secrets.
   - Executes automated polling health check against `https://paimana-backend.onrender.com/health` (up to 12 attempts with 10s backoff).
   - Asserts response code is `HTTP 200` and service reports `healthy`.
   - Smoke tests the public risk overview endpoint `https://paimana-backend.onrender.com/api/v1/public/risk-overview`.

2. **Job 2: `deploy-and-smoke-frontend`**
   - Optionally fires `VERCEL_DEPLOY_HOOK_URL` if configured in repository secrets.
   - Executes automated polling smoke check against `https://paimana-seven.vercel.app` (up to 6 attempts with 10s backoff).
   - Validates `HTTP 200 OK` and confirms presence of the single-page application root DOM mount point.

3. **Job 3: `deployment-status`**
   - Summarizes verified live URLs and logs deployment success.

---

## 4. GitHub Repository Secrets Setup

To enable automated webhooks and external services in GitHub Actions, configure the following secrets in **GitHub > Repository Settings > Secrets and variables > Actions**:

| Secret Name | Required? | Purpose | Example Value |
|---|---|---|---|
| `RENDER_DEPLOY_HOOK_URL` | Optional | Deploy Hook to immediately trigger Render backend deployment | `https://api.render.com/deploy/srv-xxxxxx?key=yyyyyy` |
| `VERCEL_DEPLOY_HOOK_URL` | Optional | Deploy Hook to immediately trigger Vercel frontend deployment | `https://api.vercel.com/v1/integrations/deploy/prj_xxxx/yyyy` |
| `MONGODB_URL` | Optional | Live MongoDB Atlas connection string for CI runs (defaults to in-memory mock if omitted) | `mongodb+srv://...` |
| `SECRET_KEY` | Optional | JWT signing secret for backend security | `your-secure-random-token` |
| `N8N_RISK_WEBHOOK_URL` | Optional | Production n8n webhook destination for high-risk alerts | `https://.../webhook/paimana-alerts` |

> **Note**: Even if deploy hooks are not configured, Render and Vercel automatically deploy commits pushed to `main` via their native GitHub integrations. The CD workflow will still execute and smoke-test both live URLs after deployment.

---

## 5. Local Pre-Commit Verification

Before opening a pull request or pushing to `main`, execute the local verification sequence:

```bash
# 1. Run all backend tests and verify 100% pass
cd backend
source .venv/bin/activate
pytest tests -v --cov=app

# 2. Run frontend tests and verify 100% pass
cd ..
npm test

# 3. Verify production frontend build compiles without errors
npm run build
```

---

## 6. Live Production Endpoints

- **Frontend Application**: [https://paimana-seven.vercel.app](https://paimana-seven.vercel.app)
- **Backend API Base**: [https://paimana-backend.onrender.com](https://paimana-backend.onrender.com)
- **Backend Health Check**: [https://paimana-backend.onrender.com/health](https://paimana-backend.onrender.com/health)
- **Public Risk Overview**: [https://paimana-backend.onrender.com/api/v1/public/risk-overview](https://paimana-backend.onrender.com/api/v1/public/risk-overview)
- **Interactive OpenAPI Docs**: [https://paimana-backend.onrender.com/docs](https://paimana-backend.onrender.com/docs)
