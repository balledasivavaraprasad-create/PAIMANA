# Security

## Principles

Security must be applied at the backend boundary and integration boundary, not only in the UI.

## Secrets

Use environment variables or a secrets manager.

Never commit:

- OpenAI keys
- n8n webhook secrets
- SMTP passwords
- database credentials

## Webhooks

Use signature/shared-secret validation.

Do not expose webhook URLs to the browser.

## API

Require authentication for authenticated routes.

Enforce authorization server-side.

Validate IDs and payloads.

## Input validation

Projects and external feeds must pass schema and domain validation before entering the monitoring pipeline.

## Audit

Record consequential operations.

## Data minimization

Only send the minimum data required to a downstream integration.

## Dependency security

Pin or constrain critical versions where model serialization and runtime compatibility matters.

## Browser security

Use standard secure headers through the deployment platform/backend.

## XSS / HTML email

Treat generated email content carefully. If using HTML, sanitize/validate generated markup before sending.
