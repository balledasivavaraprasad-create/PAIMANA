# Observability

## System layers to observe

### Application

- request count
- latency
- error rate

### Monitoring

- scan duration
- projects evaluated
- projects skipped due to no material change
- events generated
- alerts generated

### Agent

- investigation count
- tool count
- tool latency
- investigation duration
- termination reason
- evidence count
- contradiction count
- model/tool failures

### n8n

- webhook acceptance
- processing time
- OpenAI calls
- email delivery status
- retries
- dead letters

## Langfuse

Use Langfuse for agent/LLM observability where integrated.

Suggested trace hierarchy:

```text
monitoring_cycle
 └── project_evaluation
      └── investigation
           ├── planner_generation
           ├── tool_span
           ├── observation
           ├── hypothesis_update
           └── recommendation_generation
```

Do not make Langfuse a runtime dependency for core monitoring correctness.

## UI observability

Normal users should see:

- monitoring status
- last sync
- investigation status
- notification status

Advanced users/admins may see:

- execution trace
- latency
- failure counts
- tool-level status

## Privacy/security

Never put:

- secrets
- SMTP credentials
- webhook secrets
- API keys

into traces.
