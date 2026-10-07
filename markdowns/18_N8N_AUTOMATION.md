# n8n Automation Specification

## Objective

Connect the monitoring agent's authoritative alert decision to reliable automated notification.

## Flow

```text
Monitoring
 ↓
DPHIS / Event decision
 ↓
Alert event
 ↓
Durable outbox
 ↓
Signed POST to n8n
 ↓
Webhook validation
 ↓
Idempotency check
 ↓
OpenAI / ChatGPT email generation
 ↓
Email validation
 ↓
Email provider
 ↓
Delivery log
```

## Separation of responsibilities

### Backend
Decides:

- whether an event occurred
- whether an alert should be created
- recipient identity
- project facts
- risk values
- investigation link

### n8n
Handles:

- webhook receipt
- validation
- formatting/orchestration
- OpenAI wording
- email send
- delivery workflow

### OpenAI/ChatGPT
Only converts verified structured facts into readable email copy.

It must not invent project facts or independently decide whether the project is risky.

## Security

Never expose webhook URL or API keys to the frontend.

Prefer signed requests or an n8n-compatible shared secret.

## Idempotency

Use a unique event ID.

Repeated delivery of the same event must not produce repeated emails.

## Failure handling

```text
n8n unavailable
→ retryable
→ outbox retry

OpenAI unavailable
→ fallback deterministic template

Email provider unavailable
→ retryable

Permanent failure
→ dead letter
→ visible admin status
```

## Email structure

1. Project
2. Trigger
3. Current vs previous DPHIS
4. key observed signals
5. model predictions
6. peer context if available
7. investigation link
8. project link

## Language rules

Use:

- observed
- predicted
- indicated
- comparable projects showed
- possible explanation

Avoid unsupported:

- caused by
- definitely due to
- guaranteed
- will fail

## Testing

At minimum test:

- threshold crossing
- duplicate event
- malformed payload
- invalid signature
- OpenAI failure
- email failure
- n8n timeout
- retry
- missing peer data
- missing SHAP data
