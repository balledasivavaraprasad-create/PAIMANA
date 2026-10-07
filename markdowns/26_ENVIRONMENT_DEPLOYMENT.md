# Environment and Deployment

## Environment classes

```text
local
staging
production
```

## Frontend

Expected deployment platform: Vercel or existing frontend platform.

## Backend

Expected deployment platform: Render or existing backend platform.

Use existing auto-deploy integrations if already configured.

## Environment variables

Frontend should contain only browser-safe variables.

Backend-only secrets:

```text
DATABASE_URL
OPENAI_API_KEY
N8N_ALERT_WEBHOOK_URL
N8N_WEBHOOK_SECRET
EMAIL_FROM
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY
LANGFUSE_HOST
```

Use actual names from the existing application when possible rather than creating duplicate variables.

## Build requirements

CI should run:

- frontend typecheck
- frontend lint
- frontend build
- backend tests
- agent tests
- contract/schema checks

## Deployment principle

Do not deploy frontend/backend changes that silently depend on environment variables not present in staging/production.

## Smoke tests

After deployment:

- health endpoint
- auth
- portfolio endpoint
- analytics endpoint
- agent integration health
- n8n webhook test route where safe
