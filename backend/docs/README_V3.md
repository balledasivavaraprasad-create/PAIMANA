# PAIMANA Continuous-Monitoring & Agentic Early Warning System (V4 / V3-Refactored)
## Comprehensive System & Architectural Documentation

> **Target Domain:** Infrastructure & Project Monitoring Division (IPMD), Ministry of Statistics and Programme Implementation (MoSPI), Government of India  
> **Architecture Version:** 4.0 (Dual-Mode Supervisor & Grounded Multi-Dimensional Confidence)  
> **Core Package Path:** `Paimana/Agents/paimana_agent_v3/paimana_agent`

---

## 📑 Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Core Predictive ML Pipelines & Cross-Check Engine](#3-core-predictive-ml-pipelines--cross-check-engine)
4. [Continuous Monitoring, Early Snapshot Hashing & Data Sync (`PaimanaDataSync`)](#4-continuous-monitoring-early-snapshot-hashing--data-sync-paimanadatasync)
5. [Smart Event Detection Taxonomy](#5-smart-event-detection-taxonomy)
6. [Dual-Mode Supervisor Agent (LLM + Dynamic Gap Planner)](#6-dual-mode-supervisor-agent-llm--dynamic-gap-planner)
7. [Competing Causal Hypotheses & Relational Evidence Graph](#7-competing-causal-hypotheses--relational-evidence-graph)
8. [Formal Tool Registry & MCP Compatibility](#8-formal-tool-registry--mcp-compatibility)
9. [Investigation State & Rich Audit History](#9-investigation-state--rich-audit-history)
10. [Separated Multi-Dimensional Confidence Model](#10-separated-multi-dimensional-confidence-model)
11. [Contradiction Detection Engine](#11-contradiction-detection-engine)
12. [Recommendation Candidate Generation, Validation & Constrained Ranking Pipeline](#12-recommendation-candidate-generation-validation--constrained-ranking-pipeline)
13. [Institutional Knowledge & Closed-Loop Precedent Learning Engine](#13-institutional-knowledge--closed-loop-precedent-learning-engine)
14. [Disciplined Causal Reasoning & Empirical Mechanism Verification Engine](#14-disciplined-causal-reasoning--empirical-mechanism-verification-engine)
15. [Human-in-the-Loop Governance Boundary](#15-human-in-the-loop-governance-boundary)
16. [Autonomous Durable Outbox Worker with Exponential Backoff](#16-autonomous-durable-outbox-worker-with-exponential-backoff)
17. [Observability & Real Langfuse Instrumentation](#17-observability--real-langfuse-instrumentation)
18. [Dynamic Hypothesis Invention & Explanatory Coverage Architecture](#18-dynamic-hypothesis-invention--explanatory-coverage-architecture)
19. [Provenance, Freshness Decay & Independent Corroboration Subsystem](#19-provenance-freshness-decay--independent-corroboration-subsystem)
20. [Multidimensional Investigation Convergence & Stopping Management](#20-multidimensional-investigation-convergence--stopping-management)
21. [Resource Governance, Investigation Budget & Portfolio Concurrency Engine](#21-resource-governance-investigation-budget--portfolio-concurrency-engine)
22. [First-Class Tool Reliability, Circuit Breaking & Recovery Management](#22-first-class-tool-reliability-circuit-breaking--recovery-management)
23. [Automated Verification: 111 Behavioral & Benchmark Test Cases Across 31 Sections](#23-automated-verification-111-behavioral--benchmark-test-cases-across-31-sections)


---

## 1. Executive Summary & Problem Statement

The Infrastructure & Project Monitoring Division (IPMD) of MoSPI monitors Central Sector Infrastructure Projects costing ₹150 Crore and above across all infrastructure Ministries and Departments. Historically, monitoring platforms functioned as retrospective reporting repositories, capturing cost overruns and timeline slippage after they had already materialized.

The **PAIMANA V4 Agentic Architecture** transforms this into a **continuous, predictive, and agentic early warning ecosystem**:
- **Continuous Monitoring with Snapshot Hashing:** Evaluates projects on every addition/edit and scheduled scans every 6 hours. Computes SHA-256 snapshot hashes to detect material changes and skip unmutated projects.
- **Dual-Mode Supervisor Reasoning Loop:** Employs an LLM-driven planner (`LLMSupervisorPlanner`) with an intelligent evidence-gap fallback (`DynamicEvidenceGapPlanner`).
- **4 Competing Causal Hypotheses:** Evaluates four distinct causal models with Bayesian-like posterior updates rather than hardcoded static templates.
- **Multi-Dimensional Grounded Confidence:** Calculates confidence across 5 explicit dimensions (quality, independence, agreement, recency, contradiction penalty) rather than simply counting tool calls.
- **Durable Background Outbox Worker:** Dispatches approved interventions with exponential backoff and dead-letter handling.

---

## 2. End-to-End System Architecture

```text
                                  PAIMANA PROJECT DATA (CUF)
                                              │
                            ┌─────────────────┴─────────────────┐
                            ▼                                   ▼
                      On-Change Trigger                   Scheduled Scan
                      (Immediate Save)                   (Every 6 Hours)
                            └─────────────────┬─────────────────┘
                                              ▼
                                Snapshot Hashing (SHA-256)
                                 (Material Change Check)
                                              │
                                              ▼
                                  CUF Validation & Features
                                        (features.py)
                                              │
                            ┌─────────────────┼─────────────────┐
                            ▼                 ▼                 ▼
                       Cost Overrun     Time Overrun       Risk Score
                        ML Pipeline      ML Pipeline       ML Pipeline
                            │                 │                 │
                            └────────┬────────┘                 │
                                     ▼                          │
                            Independent Cross-Check ────────────┤
                                     │                          │
                                     ▼                          ▼
                                Risk Tiers & Smart Event Engine
                                     (events.py)
                                              │
                          (Notable Events / Compound Anomalies)
                                              ▼
                                    SUPERVISOR AGENT LOOP
                                      (supervisor.py)
                                              │
                            ┌─────────────────┴─────────────────┐
                            ▼                                   ▼
                   LLM Dynamic Planner                 Dynamic Gap Planner
                  (Ollama / LiteLLM)                  (Deterministic Fallback)
                            └─────────────────┬─────────────────┘
                                              ▼
                                    FORMAL TOOL REGISTRY
                                        (tools.py)
                            ┌─────────────────┼─────────────────┐
                            ▼                 ▼                 ▼
                     financial_velocity milestone_audit   peer_intelligence
                            │                 │                 │
                            └─────────────────┼─────────────────┘
                                              ▼
                                   TOOL EXECUTION RECORD
                                (Unique ID, Latency, Params)
                                              ▼
                                     UPDATE ACCUMULATOR
                                    (state.py / tracer.py)
                                              ▼
                                    DETECT CONTRADICTIONS
                                    & UPDATE 4 HYPOTHESES
                                              ▼
                               EVIDENCE SUFFICIENT? / BUDGET?
                                      /             \
                                    NO               YES
                                    │                 │
                    (Loop Back to Supervisor)         ▼
                                          VALIDATION LAYER
                                        (Safety & Precedents)
                                                      │
                                                      ▼
                                            HUMAN APPROVAL GATE
                                            (pending_approval)
                                                      │
                                             (Admin Sign-Off)
                                                      ▼
                                            DURABLE OUTBOX QUEUE
                                            (Autonomous Worker)
                                                      │
                                                      ▼
                                           n8n Automation Dispatch
                                        (Exponential Retry / Backoff)
```

---

## 3. Core Predictive ML Pipelines & Cross-Check Engine

The system relies on three machine-learning models trained on historical MoSPI project records:
1. **Cost Overrun Estimator:** Predicts expected percentage cost growth ($% \Delta \text{Cost}$).
2. **Time Overrun Estimator:** Predicts expected schedule slippage in calendar months ($\Delta \text{Months}$).
3. **Composite Risk Score Model:** Predicts operational risk on a 0–100 percentile-ranked scale.

### Disagreement Cross-Check Safeguard:
The agent independently computes a rule-based combined score ($0.5 \times \text{rank}(\text{cost}) + 0.5 \times \text{rank}(\text{time})$). If the discrepancy between the composite model and the cross-check exceeds `disagreement_threshold` (default: 20 points), the alert flags a data warning.

---

## 4. Continuous Monitoring, Early Snapshot Hashing & Data Sync (`PaimanaDataSync`)

In [`store.py`](paimana_agent/store.py) and [`agent.py`](paimana_agent/agent.py), every project submission is fingerprinted via canonical SHA-256 snapshot hashing:
```python
def compute_snapshot_hash(record: Optional[dict]) -> str:
    ...
```
- **Early Snapshot Hash Check:** Evaluated at the entry of `evaluate_project()`. If the computed SHA-256 hash matches the previous evaluation snapshot and no temporal milestone drift has occurred (`material_change = False`), the agent completely bypasses expensive ML inference pipelines and SHAP permutation sampling.
- **Authoritative Data Synchronization Service (`PaimanaDataSync`):** In [`sync.py`](paimana_agent/sync.py), an ingestion service continuously consumes external API feeds, DB replicas, or JSON/CSV dumps. It leverages early hashing to skip unmutated records in bulk while immediately routing mutated projects to evaluation and event triage.

---

## 5. Smart Event Detection Taxonomy

Independent of tier thresholds, the event engine ([`events.py`](paimana_agent/events.py)) triggers investigations upon detecting specific operational signals:
1. `THRESHOLD_CROSSED`: Project risk crosses the customized per-project threshold.
2. `RISK_ACCELERATING`: Score jumps $\ge 8$ points between consecutive evaluations.
3. `COST_PROGRESS_MISMATCH`: Cumulative expenditure leads physical completion by $> 15$ percentage points.
4. `PROGRESS_STALLED`: Physical progress advances $< 0.5\%$ per month while project is $< 95\%$ complete.
5. `MILESTONE_DELAYED`: Approved completion target pushed back $> 0$ months.

---

## 6. Dual-Mode Supervisor Agent (LLM + Dynamic Gap Planner)

The **Supervisor Agent** ([`supervisor.py`](paimana_agent/supervisor.py)) operates in two distinct modes:

### Mode 1: LLM-Driven Planning (`LLMSupervisorPlanner`)
When an LLM endpoint is enabled in `config.yaml`, the supervisor prompts the model with:
- Grounded observations ("What do we know?")
- Active evidence gaps ("What don't we know?")
- Competing hypotheses & explicit falsification conditions ("What would change our mind?")
- Complete Tool Registry schemas
- Budget remaining
The LLM outputs structured JSON specifying `EXECUTE_TOOL` (with target gap) or `CONCLUDE`.

### Mode 2: Dynamic Evidence-Gap Planner (`DynamicEvidenceGapPlanner`)
If the LLM is unconfigured, disabled, or fails to respond, the gap-driven planner dynamically evaluates which tool maximizes information gain to discriminate between the top 2 competing hypotheses.

### Controlled Termination Reasons:
- `SUFFICIENT_EVIDENCE`: Top hypothesis reaches posterior probability $\ge 0.65$ with multi-source validation.
- `TOOL_LIMIT_REACHED`: Enforces tool execution budget (default: 5 steps).
- `INSUFFICIENT_DATA`: Data sources missing or empty.
- `UNRESOLVED_CONTRADICTION`: Critical conflict could not be reconciled.

---

## 7. Competing Causal Hypotheses & Relational Evidence Graph

Instead of hardcoded single-cause templates, the agent initializes and tracks 4 competing hypotheses throughout the investigation:
1. `front_loaded_billing`: Progress-expenditure decoupling; uncertified bills / front-loaded mobilization.
2. `chronic_schedule_delay`: Execution bottlenecks; contractor mobilization failures.
3. `regulatory_land_clearance`: Statutory clearances, environmental approvals, or land acquisition / RoW hurdles.
4. `reporting_discrepancy`: MPR data lag or administrative inconsistency between portal records and physical ground reality.

### Falsification Conditions ("What would change the agent's mind?"):
Each hypothesis maintains an explicit `falsification_condition`. For instance:
- `front_loaded_billing`: Falsified if independent on-site technical inspection certifies physical delivery matches cumulative disbursements within 5% tolerance.
- `chronic_schedule_delay`: Falsified if resource-loaded catch-up milestones demonstrate contractor has recovered critical-path schedule slippage with required monthly burn-down rate.

Scores are updated dynamically as observations accumulate, normalizing into evidence-weighted posterior scores:
$$\sum_{i=1}^{4} P(H_i) = 1.0$$

### Relational Evidence Graph (`evidence_graph`):
The agent records every observation's impact on hypotheses as directed edges:
`(source, relation, target, weight)` with relations `SUPPORTS`, `WEAKENS`, `CONTEXTUALIZES`, and `CONTRADICTS`.

---

## 8. Formal Tool Registry & MCP Compatibility

Specialist capabilities are encapsulated in [`tools.py`](paimana_agent/tools.py):
- **Core Diagnostic Tools:**
  - `financial_velocity`: Audits expenditure pace against certified physical completion.
  - `milestone_audit`: Audits milestone schedule slippage and project lifespan ratios.
  - `project_history`: Audits multi-month trajectory and historical issue logs.
  - `memory_retrieval`: Queries closed-loop learning memory for past intervention outcomes.
  - `shap_attribution`: Model-agnostic SHAP permutation feature attributions for risk explainability.
- **Deep Integrated Peer Intelligence Suite (`Peer_Intelligence/peer`):**
  - `peer_intelligence`: Master upgraded tool providing comprehensive discovery, benchmarks, deviations, trajectory, and outliers with legacy backward compatibility.
  - `peer_discovery`: Multi-dimensional comparable peer identification & filtering with transparent similarity explanations.
  - `peer_benchmark`: Robust statistical distributions (median, IQR, p25/p75) across peer cohorts.
  - `peer_deviation`: Target project vs peer median divergence calculations with directional interpretations.
  - `peer_trajectory`: Chronological velocity and monthly change rate comparisons across historical snapshots.
  - `peer_outlier`: Peer-relative anomaly detection cleanly separating absolute operational risk from sector context.
  - `peer_cohort_health`: Cohort size, similarity strength, and data completeness evaluations.
  - `cohort_intelligence`: Multidimensional cohort quality, distribution shape, heterogeneity, and refinement recommendations.
  - `statistical_benchmark`: Robust reference profiles, bootstrap confidence intervals, and empirical percentiles.
  - `detect_peer_anomalies`: Multi-method contextual, multivariate, and temporal anomaly detection.
  - `analyze_trajectory_intelligence`: Rolling velocity, acceleration, stagnation, recovery, and regime-shift analysis.
  - `analyze_domain_context`: Domain-specific infrastructure operational realities, statutory clearances, and terrain bottlenecks.

Every tool exports standard schemas and Model Context Protocol (MCP) definitions via `export_mcp_manifest()`.

---

## 9. Investigation State & Rich Audit History

The investigation state maintains complete structured evidence:
- **Facts:** Verified data from official records.
- **Inferences:** Analytical deductions linked to derived fact metrics.
- **Tool Executions:** List of `ToolExecutionRecord` capturing:
  - `call_id`: e.g. `exec_1_financial_velocity`
  - `tool_name`
  - `parameters`
  - `latency_ms`
  - `status` ("SUCCESS" / "ERROR")
  - `result_summary`

---

## 10. Separated Multi-Dimensional Confidence Model

The agent explicitly separates causal diagnostic confidence from action confidence:

### 1. Root-Cause Confidence (`root_cause_confidence`):
Strictly epistemic confidence in causal diagnosis evaluated across 4 grounded dimensions:
- **Evidence Quality ($0.0 - 0.25$):** Grounded facts verified from direct CUF ledgers.
- **Evidence Independence ($0.0 - 0.25$):** Distinct independent tools consulted.
- **Hypothesis Separation ($0.0 - 0.25$):** Margin between #1 and #2 hypothesis ($P(H_1) - P(H_2)$).
- **Contradiction Penalty ($-0.20$):** Deduction for active data conflicts.

$$\text{Root-Cause Confidence} = \text{Quality} + \text{Independence} + \text{Separation} - \text{Penalty}$$

### 2. Recommendation Confidence (`recommendation_confidence`):
Confidence in operational intervention success, weighted by:
- Empirical precedent outcomes in project memory ($35\%$)
- Root-cause confidence score ($35\%$)
- Administrative authority and statutory fit ($30\%$)

Overall qualitative tiers:
- **HIGH:** Score $\ge 0.70$
- **MEDIUM:** Score $\ge 0.40$
- **LOW:** Score $< 0.40$

---

## 11. Contradiction Detection Engine

The contradiction engine flags discrepancies across sources:
- Milestone schedule claims 0 slippage, but duration is $>75\%$ elapsed with physical progress $<20\%$.
- Expenditure exceeds $100\%$ while physical progress remains $<50\%$.
- Multi-snapshot progress reversals (physical completion going backwards).

Every contradiction is recorded in `state.contradictions`, penalizes confidence, and prioritizes disambiguation tools.

---

## 12. Recommendation Candidate Generation, Validation & Constrained Ranking Pipeline

The recommendation layer operates on a fundamental architectural boundary:
> **The LLM may propose and explain candidates; the deterministic ranking engine determines which validated candidate is selected.**

### 1. The End-to-End Pipeline
```text
Supported Hypotheses & Evidence Graph
               │
               ▼
   Candidate Generator (5 Sources)
  (Hypotheses, Evidence, Precedents,
   Playbooks, Structured LLM)
               │
               ▼
     5–10 Recommendation Candidates
               │
               ▼
     Candidate Deduplicator
  (Token overlap & semantic merging)
               │
               ▼
     Candidate Pre-Scoring Validation
  (Evidence existence, hypothesis alignment,
   statutory authority, failed precedent check)
               │
               ▼
     Multi-Criteria Scoring Engine
  (Benefit, Cost, Risk Reduction vs
   Implementation Risk, Lineage Evidence, Authority)
               │
               ▼
     Pareto Frontier Filtering
  (Eliminate strictly dominated candidates)
               │
               ▼
     Weighted Policy Ranking & Confidence Adjustment
               │
               ▼
     Constrained Selector
  (Terminal state check & deterministic explanation)
               │
               ▼
     Recommendation Decision
  (Selected Winner, Ranked Alternatives, Trade-offs)
               │
               ▼
     Human Approval Sign-Off Gate
               │
               ▼
     Durable Background Outbox Worker
```

### 2. First-Class `RecommendationCandidate` Structure
Every candidate is an auditable data entity with explicit metrics:
- **`expected_benefit`** ($0.0 - 1.0$): Problem resolution utility.
- **`expected_cost`** ($0.0 - 1.0$): Normalized direct, staff, overhead, and delay burden ($\text{cost\_score} = 1.0 - \text{burden}$).
- **`expected_risk_reduction`** ($0.0 - 1.0$): Project risk mitigated.
- **`implementation_risk`** ($0.0 - 1.0$): New operational/contractual hazard introduced ($\text{risk\_score} = \text{risk\_reduction} \times (1.0 - \text{implementation\_risk})$).
- **`evidence_strength`** ($0.0 - 1.0$): Aggregated across independent source groups preventing double-counting.
- **`authority_score`** ($0.0 - 1.0$): Source authority + institutional stakeholder match.
- **`confidence`**: Decision confidence based on data freshness, independence, and completeness.

### 3. Pareto Frontier Filtering
Before applying policy weights, strictly dominated candidates are removed. If Candidate B is worse than Candidate A on all five dimensions, B is dominated and filtered out. Non-dominated trade-offs remain on the frontier for weighted evaluation.

### 4. Versioned Ranking Policies & Decision Tracing
Policies configure explicit weights ($W_B, W_C, W_R, W_E, W_A$) for distinct action classes (`standard`, `early_warning`, `escalation`, `financial`, `data_quality`). The selector produces a full `RecommendationDecision` with deterministic `selection_reason`:
- `dominant_factors` (e.g. independent corroboration, high risk reduction, low implementation risk)
- `tradeoffs`
- `why_alternatives_not_selected` (specific comparative deficiencies of each runner-up)

### 5. "No Recommendation" Terminal States
The system is never forced to recommend an action. Valid outcomes include `RECOMMENDATION_SELECTED`, `MULTIPLE_CANDIDATES_REQUIRE_REVIEW`, `INSUFFICIENT_EVIDENCE`, `NO_ELIGIBLE_CANDIDATE`, `HIGH_ACTION_RISK`, `AUTHORITY_INSUFFICIENT`, and `CONFLICTING_EVIDENCE`.

---

## 13. Institutional Knowledge & Closed-Loop Precedent Learning Engine

The institutional memory system ([`paimana_agent/memory/`](paimana_agent/memory/)) transitions PAIMANA from passive retrieval to a **closed-loop precedent learning engine**:

```text
Investigation ──► CANDIDATE Precedent ──► Empirical Outcome (Δmetrics) ──► Outcome Evaluator ──► VALIDATED Precedent
                                                                                                        │
    ┌───────────────────────────────────────────────────────────────────────────────────────────────────┘
    ▼
Hybrid Retrieval:
├── Pattern Fingerprint Matching (Structured non-semantic similarity)
├── Contextual Transferability Evaluator (Sector, Contract, Cost Band, Stage, Agency)
├── Anti-Circular Corroboration (Independent authority groups prevent echo-chamber inflation)
└── Domain-Specific Temporal Decay (Half-lives from 180d for statutory policy to 3yr for engineering)
    │
    ▼
PrecedentBundle:
├── Supporting Precedents (Directly inform candidate generation & boost recommendation confidence)
├── Failed Precedents & Negative Warnings (Enforce automatic aversion vetoes against repeating past mistakes)
└── Explicit Counterexamples (Active bias refutation: same symptoms, different root cause)
```

### Key Subsystem Components
1. **`Precedent`**: Durable knowledge unit storing pattern fingerprints, context envelopes, root causes, interventions, empirical outcomes ($\Delta\text{risk}$, $\Delta\text{gap}$, $\Delta\text{delay}$), causal attribution classes, and provenance.
2. **`TransferabilityEvaluator`**: Prevents improper cross-sector transfers by scoring sector, contract type, scale band, stage, and agency affinity. Discounts cross-domain transfers by 50% if transferability $< 0.40$.
3. **`MemoryReliabilityManager`**: Computes empirical reliability via Bayesian track records with Laplace smoothing and independent group corroboration tracking.
4. **`MemoryDecayManager`**: Implements domain-specific half-life decay ($T_{1/2} = 180\text{d}$ for statutory rules, $365\text{d}$ for contracts/costs, $730\text{d}$ for civil execution).
5. **`OutcomeEvaluator`**: Separates causal efficacy from confounders and assigns attribution classes (`LIKELY_EFFECTIVE`, `POSSIBLY_EFFECTIVE`, `INCONCLUSIVE`, `LIKELY_INEFFECTIVE`, `FAILED`).
6. **`FailureMemoryManager`**: Evaluates proposed candidate actions against historical failure precedents and triggers warning notes and validator vetoes.
7. **`MemoryConsolidator`**: Manages the lifecycle promotion: completed investigations are registered as `CANDIDATE`s until real outcomes are verified and promoted to `VALIDATED`.
8. **Epistemic Hierarchy**: Authoritative current ground-truth evidence strictly overrides historical precedent memory.

---

## 14. Disciplined Causal Reasoning & Empirical Mechanism Verification Engine

```text
Observation ──► Association ──► Temporal Precedence ──► Mechanism Links ──► Confounders & Proxies ──► Causal Claim Level (0–5)
                                                                                                            │
    ┌───────────────────────────────────────────────────────────────────────────────────────────────────────┘
    ▼
Recommendation Safety Calibration (Gate 6):
├── Levels 0–2 (Observation/Association): Punitive escalations VETOED; only diagnostic/joint audits permitted.
├── Level 3 (Mechanistic Support): Moderate corrective actions permitted (catch-up schedules, re-allocation).
└── Levels 4–5 (Strong Causal / Intervention): Full contractual escalations & liquidated damages permitted.
```

The causal reasoning layer ([`paimana_agent/causal/`](paimana_agent/causal/)) enforces that PAIMANA never converts statistical correlation into causal language without empirical mechanism verification.

### Key Causal Principles & Capabilities
1. **Strict Causal Contract:** Prohibits declaring a "root cause" unless temporal precedence ($\Delta t > 0$), multi-step transmission links, absence of active falsifiers, and confounder accounting are empirically satisfied.
2. **6-Tier Claim Levels:**
   - `LEVEL_0_OBSERVATION`: Statistical co-occurrence of symptoms.
   - `LEVEL_1_ASSOCIATION`: Correlated variables without verified mechanism or sequence.
   - `LEVEL_2_TEMPORAL_ASSOCIATION`: Verified temporal precedence ($\text{Cause}$ strictly precedes $\text{Effect}$), but transmission unverified.
   - `LEVEL_3_MECHANISTIC_SUPPORT`: Verified intermediate physical or administrative transmission steps.
   - `LEVEL_4_STRONG_CAUSAL_SUPPORT`: Multi-step mechanism verified across $\ge 2$ independent source groups, no unresolved confounders, counterfactual proxy supports causality.
   - `LEVEL_5_INTERVENTION_SUPPORTED`: Real-world empirical intervention on the cause resolved the effect in project history.
3. **Canonical Mechanism Ontology:** 5 pre-calibrated infrastructure mechanisms (`M_CONTRACTOR_EXECUTION`, `M_APPROVAL_DEPENDENCY`, `M_FUNDING_CONSTRAINT`, `M_LAND_ROW_DEFICIT`, `M_DESIGN_VARIATION`) with explicit intermediate links and falsifying conditions.
4. **Temporal Reasoner:** Validates timestamp precedence and detects temporal inversions (e.g., clearance delay filed *after* project was already 2 years behind). Inversions automatically trigger `REJECTED` status and penalize causal support.
5. **Confounder Detector:** Scans for systemic third-variable drivers (e.g. state funding freezes that simultaneously delay statutory fee deposits and starve contractor cashflow). Applies penalties ($P \ge 0.15$) and issues explicit evidence requirements.
6. **Counterfactual Analyzer:** Leverages natural project comparison groups (unencumbered workfronts, same contractor on other packages) to approximate counterfactual outcomes.
7. **ML / SHAP Attribution Safety Boundary:** Model feature importances are strictly flagged `evidence_type = "MODEL_DERIVED"`. The engine forbids treating predictive feature importance as physical causal proof without independent empirical corroboration.
8. **Calibrated Recommendation Bounds (Gate 6):** Enforces that premature punitive sanctions (liquidated damages, contractor termination) are vetoed under Levels 0–2.

---

## 15. Human-in-the-Loop Governance Boundary

The agent adheres to a strict governance boundary:
- Investigations conclude in `pending_approval` state.
- External actions are never triggered autonomously.
- An authorized human administrator must explicitly approve via `approve_investigation()`.

---

## 16. Autonomous Durable Outbox Worker with Exponential Backoff

The automation outbox in [`store.py`](paimana_agent/store.py) manages downstream execution:
- **Atomic Task Leasing:** Claims tasks inside a single SQLite transaction lock, transitioning status to `processing`.
- **Idempotent Enqueue:** Prevents duplicate task execution.
- **Autonomous OutboxWorker:** Processes tasks in the background with exponential retry backoff ($\text{delay} = \min(60.0, 2^{\text{attempts}} \times 1.5)$).
- **Dead-Letter Queue:** Automatically transitions tasks exceeding max attempts to `dead_letter` for administrative inspection.

---

## 17. Observability & Real Langfuse Instrumentation

[`tracer.py`](paimana_agent/tracer.py) instruments investigations:
- Emits real Langfuse traces, generations, spans, scores, and events when configured.
- Gracefully logs locally when Langfuse is unconfigured or unreachable.

---

## 18. Dynamic Hypothesis Invention & Explanatory Coverage Architecture

In this release, PAIMANA has evolved from a fixed hypothesis-scoring system into an autonomous **Dynamic Hypothesis Invention & Explanatory Coverage Framework**:
- **First-Class Evidence Model (`Evidence`):** Observations are normalized into strongly typed evidence entities with source provenance, quantified reliability, materiality flags, and explanatory coverage statuses (`EXPLAINED`, `PARTIALLY_EXPLAINED`, `UNEXPLAINED`, `CONTRADICTORY`).
- **Dynamic Hypothesis Invention (`HypothesisGenerator`):** When active hypotheses fail to explain material evidence or persistent contradictions weaken existing explanations, the agent automatically synthesizes novel candidate hypotheses with observable predictions, discriminating evidence requirements, and explicit falsification conditions.
- **Hypothesis Validation & Anti-Hallucination Guardrail (`HypothesisValidator`):** Rejects candidates with nonexistent evidence IDs, unsubstantiated criminal/fraud assertions, or unfalsifiable claims.
- **Semantic Novelty & Parent-Child Branching (`HypothesisSimilarityChecker`):** Computes normalized Jaccard token overlap with domain synonym mapping. Redundant candidates ($>35\%$ overlap) are merged with existing hypotheses, while specialized mechanisms are branched cleanly as child hypotheses (e.g. `parent_hypothesis_id = 'chronic_schedule_delay'`).
- **Hypothesis Budget & Audit Integrity:** Strictly enforces active budget caps (`max_active=6`, `max_total_generated=10`) and **never deletes** rejected hypotheses, retaining full audit histories and rejection justifications.
- **Calibrated Recommendations & Outcome Classification:** Classifies investigations into `ROOT_CAUSE_SUPPORTED`, `ROOT_CAUSE_PARTIALLY_SUPPORTED`, `MULTIPLE_PLAUSIBLE_CAUSES`, `INSUFFICIENT_EVIDENCE`, or `CONTRADICTORY_EVIDENCE`. Inconclusive investigations recommend exploratory on-site technical audits rather than premature punitive contractual disruptions.

---

## 19. Provenance, Freshness Decay & Independent Corroboration Subsystem

To address the core scientific flaw that *"more evidence was too easily interpreted as more independent evidence"*, PAIMANA introduces a rigorous **Evidence Provenance & Independent Corroboration Model**:

### 1. Complete Source Provenance
Every evidence object tracks its lineage, authority, and retrieval metadata:
- **`source_id` & `source_system`**: Originating system (e.g. `PAIMANA`, `PMIS`, `GIS`, `AUDIT`).
- **`source_record_id` & `source_field`**: Specific underlying snapshot, row, or metric.
- **`observed_at`, `recorded_at`, `retrieved_at`**: Separate timestamps distinguishing real-world ground truth from reporting delay and agent query time.
- **`parent_evidence_ids` & `transformation_chain`**: Tracks derived analytical metrics back to their raw primary observations.
- **`independence_group_id`**: Shared partition key (e.g. `PAIMANA_SNAPSHOT_<code_month>`) linking all metrics extracted from the same underlying dataset or report.

### 2. Source Authority Registry
Pre-calibrated epistemic weights reflect true evidentiary authority:
- `official_project_record`: **1.00**
- `verified_financial_record`: **1.00**
- `ground_audit_log`: **0.95**
- `sensor_iot_telemetry`: **0.90**
- `historical_dataset`: **0.80**
- `model_inference` (ML/SHAP): **0.60**
- `peer_benchmark`: **0.50**
- `llm_claim` / `unverified_assertion`: **0.10**

### 3. Exponential Freshness Decay
Evidence freshness decays over time according to source-type half-lives ($\tau$):
$$\text{freshness} = \exp\left(-\frac{\ln(2) \cdot \Delta t}{\tau}\right)$$
- Sensor / IoT telemetry: $\tau = 7$ days
- Model inferences: $\tau = 30$ days
- Official project records: $\tau = 60$ days
- Verified financial audits: $\tau = 90$ days
- Historical baselines: $\tau = 180$ days

### 4. Independent Group-Level Aggregation
Evidence support is aggregated **by independent group** before updating hypothesis scores:
- Multiple tools analyzing the same underlying snapshot share one `independence_group_id`.
- Within a group, primary direct observations establish the base strength; derived metrics contribute a strictly capped amount ($\le 0.35$). Total contribution per group cannot exceed $1.00$.
- Five tools analyzing one snapshot **never** produce five times the confidence.
- Corroboration boost ($+0.20 \times (N_{\text{indep}} - 1)$) is awarded **only when two or more distinct independent groups** independently support the hypothesis.
- Strong verified contradictions ($\text{strength} \ge 0.90$) against uncorroborated hypotheses directly transition them to `rejected`.

### 5. Admin Evidence Quality Dashboard
Exposed on `InvestigationState` (`get_evidence_quality_dashboard()`) for executive oversight:
- **`source_authority`**: Mean authority score across all evidence.
- **`freshness`**: Mean freshness score across all evidence.
- **`independence_score`**: Ratio of independent groups to total evidence items.
- **`evidence_completeness`**: Proportion of project facets covered.
- **`contradiction_risk`**: Ratio of contradicted hypotheses to active hypotheses.
- **`lineage_quality`**: Proportion of evidence with direct primary provenance.
- **`independent_corroborating_groups`**: List of distinct independent source groups.

---

## 20. Multidimensional Investigation Convergence & Stopping Management

PAIMANA V3 terminates investigations through an explicit, two-stage convergence architecture rather than arbitrary loop limits:
- **Separation of Resource Controls & Convergence**: Hard call budgets (`max_tool_calls`) and latency deadlines act strictly as safety limits (`BUDGET_EXHAUSTED` / `TOOL_LIMIT_REACHED`). Investigation convergence is determined by multidimensional information sufficiency.
- **5 Distinct Terminal States**: `CONVERGED`, `INSUFFICIENT_EVIDENCE`, `NO_HIGH_VALUE_EVIDENCE_AVAILABLE`, `CONTRADICTORY`, and `BUDGET_EXHAUSTED`.
- **6 Evaluation Dimensions**:
  1. *Evidence Coverage*: Priority-weighted coverage against open `EvidenceNeed`s, discounting single-source group pseudo-completeness.
  2. *Hypothesis Separation*: Statistical margin between leading and runner-up explanations ($\Delta_{\text{sep}} \ge 0.20$).
  3. *Hypothesis Stability*: Distribution trajectory stability over consecutive iterations ($\Delta_{\text{stab}} \ge 0.85$).
  4. *Contradiction Resolution*: Severity-weighted evaluation (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`); high/critical contradictions strictly block convergence.
  5. *Causal Support*: Integrates verified causal claims (Levels 0 through 5).
  6. *Decision Readiness*: Confirms prerequisites for actionable recommendations (causal grounding, authority, feasibility, cost).
- **Dynamic Information Detectors**:
  - *Diminishing Returns*: Detects flattening of incremental information gains ($\Delta < 0.03$).
  - *Evidence Saturation*: Flags repeated tool executions against identical data lineages.
  - *Hypothesis Oscillation*: Identifies alternating leaders under narrow margins to prevent infinite cycling.
- **Asymmetric Reopening Hysteresis**: Reopens investigations on material risk jumps ($\ge 15$ pts), high-authority evidence ($\ge 0.85$), causal contradictions, or intervention failure, while suppressing minor noise.

---

## 21. Resource Governance, Investigation Budget & Portfolio Concurrency Engine

PAIMANA V3 incorporates a multi-dimensional resource governance architecture underneath the investigation and convergence engines:
- **First-Class Multi-Resource Budget (`InvestigationBudget`)**: Manages iterations, tool invocations, LLM calls, token usage, external API calls, latency, monetary cost, and concurrency slots as an explicit accounting ledger (`ResourceConsumption`).
- **Risk-Calibrated Budget Policy (`BudgetPolicy`)**: Calibrates resource envelopes dynamically from anomaly severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), ensuring resource spend is proportional to project risk.
- **Pre-Execution Resource Reservation (`ReservationManager`)**: Enforces pre-execution holds before tool dispatch, preventing concurrent overdrafts.
- **Cost-Aware Tool Utility (`ResourceEstimator`)**: Integrates operational cost and prevailing resource pressure ($P_{\text{res}} \in [0.0, 1.0]$) alongside information gain:
  $$\text{resource\_adjusted\_value} = \frac{\text{expected\_information\_gain} \times \text{decision\_relevance} \times \text{evidence\_quality}}{\text{estimated\_cost} + \text{latency\_penalty} + \text{resource\_pressure}}$$
- **Emergency Reserve Protection**: Reserves 15–20% of the budget envelope exclusively for resolving critical contradictions or final validation, preventing routine exploration from starving decisive evidence.
- **Graceful Degradation & Confidence Coupling (`GracefulDegradationManager`)**: Transitions across 4 operational tiers (`NORMAL`, `COST_AWARE`, `CONSTRAINED`, `SAFE_TERMINATION`). Guarantees that resource constraints explicitly reduce evidence completeness and qualify confidence (`PRELIMINARY_QUALIFIED`).
- **Auditable Budget Escalation (`BudgetEscalator`)**: Allows high-severity investigations with decisive expected information gain ($EV \ge 0.10$) to formally request budget expansion; rejects trivial requests.
- **Portfolio Concurrency & Priority Scheduling**: Admission control (`PortfolioAdmissionController`), priority scheduling (`PriorityScheduler`), and cascading cancellation (`CancellationManager`) manage simultaneous investigations across national projects.
- **Human Attention Budgeting (`HumanReviewCapacity`)**: Treats ministerial approver attention as a scarce resource, routing routine actions to automated logging and critical escalations to emergency review queues.

---

## 22. First-Class Tool Reliability, Circuit Breaking & Recovery Management

PAIMANA V4 elevates tool execution and error management from basic exception handling into a **first-class decision and evidence-acquisition signal**:
- **Epistemic Principle**: A tool invocation can succeed technically while producing unusable evidence (e.g. empty payloads, project code mismatches), and a tool invocation can fail technically without invalidating existing investigation progress.
- **Decoupled Reliability Dimensions**:
  1. *Execution Reliability ($\mathcal{R}_{\text{exec}} \in [0.0, 1.0]$)*: Technical uptime, latency predictability, timeout avoidance, and RPC completion rate.
  2. *Evidence Reliability ($\mathcal{R}_{\text{ev}} \in [0.0, 1.0]$)*: Data completeness, freshness, source authority, and absence of misattributed records.
- **Standardized `ToolResult` Contract & Status Taxonomy**: Every tool execution yields a standardized result categorized by:
  - `SUCCESS`: High quality, verified domain data.
  - `PARTIAL_SUCCESS`: Execution succeeded but with incomplete fields/records; completeness discounted.
  - `EMPTY_RESULT`: Valid query but zero matching records (`useful_evidence = False`, distinct from zero-risk).
  - `STALE_RESULT`: Data exceeds staleness half-life; freshness score exponentially decayed.
  - `TIMEOUT`: Execution deadline exceeded; triggers bounded retry.
  - `AUTH_FAILURE` / `PERMISSION_DENIED`: Authorization failure; strictly **non-retryable**, routes to fallback.
  - `RATE_LIMITED`: Upstream API throttled; retryable with exponential backoff and jitter.
  - `SOURCE_UNAVAILABLE`: Service/DB offline; retryable once, then fallback.
  - `SCHEMA_ERROR`: Payload failed structural parsing; quarantined.
  - `VALIDATION_ERROR`: Domain invariant violated (e.g. false-success project mismatch); quarantined.
  - `DEPENDENCY_FAILURE`: Prerequisite connection, store, or model missing.
  - `CIRCUIT_OPEN`: Execution blocked by active circuit breaker to prevent cascade hammering.
  - `INTERNAL_ERROR`: Unhandled Python runtime exception.
- **Finite State Machine Circuit Breakers (`CircuitBreaker`)**:
  - `CLOSED`: Normal operation; failures increment consecutive counter.
  - `OPEN`: Tripped when consecutive failures reach threshold (default: 3); primary calls bypassed immediately to fallback.
  - `HALF_OPEN`: Entered after cooldown window (default: 30s); executes a single probe invocation. Success closes circuit (`CLOSED`); failure trips back to `OPEN`.
- **Reliability-Weighted Dynamic Tool Selection**:
  $$\text{tool\_utility} = \frac{\text{expected\_information\_gain} \times \text{discrimination\_power} \times \text{source\_authority} \times \mathcal{R}_{\text{exec}}}{\text{resource\_cost} + \text{failure\_penalty} + \text{latency\_penalty}}$$
  Unreliable tools ($\mathcal{R}_{\text{exec}} \le 0.30$) are systematically ranked below reliable alternatives.
- **Source Fallback Graphs with Anti-Hallucination Lineage (`FallbackGraph`)**:
  - Predefined substitution trees: `approval_timeline` $\to$ `project_history` $\to$ `milestone_audit`; `gis_satellite_validation` $\to$ `field_muster_rolls` $\to$ `milestone_audit`; `financial_velocity` $\to$ `milestone_audit` $\to$ `project_history`.
  - *Authority Discount*: Substituted evidence applies discount ratio $\alpha = \min(1.0, \text{auth}_{\text{fallback}} / \text{auth}_{\text{primary}})$.
  - *Lineage Preservation*: Fallbacks querying the same underlying data snapshot share `independence_group_id` (`SUB_<primary>_<snapshot>`), preventing false corroboration.
- **False-Success Detection & Quarantining (`ToolResultValidator`)**:
  - Catches empty payloads, all-null records, and project code mismatches before evidence graph ingestion.
  - Penalizes the tool's persistent `useful_evidence_rate = \frac{\text{usable evidence results}}{\text{total tool calls}}`.
- **Budget Accounting & State Preservation**:
  - Retries and fallbacks are charged against the `InvestigationBudget` ledger.
  - Failures operate strictly at the tool step level, **never** wiping or resetting established hypotheses, existing evidence, or convergence states.

---

## 23. Automated Verification: 111 Behavioral & Benchmark Test Cases Across 31 Sections

The system includes **111 comprehensive automated test cases** in `tests/test_agent_behavior.py`, plus 3 full regression test suites in `tests/test_agent.py`, `tests/test_agent_v2.py`, and `tests/test_agent_v3.py`. **All test suites pass 100%.**

Run the complete behavioral and benchmark test suite:
```bash
python -m pytest tests/test_agent_behavior.py -v
```

### Complete Test Catalog:
- **Cases 1 & 2:** Dynamic Multi-Step Investigation Loop
- **Case 3:** Dynamic Path Adaptation from Tool Observations
- **Case 4:** Contradiction Detection & Confidence Downgrade
- **Case 5:** Tool Failure Recovery & Evidence Gap Recording
- **Cases 6 & 7:** Controlled Termination & Budget Limit Enforcement
- **Cases 8 & 9:** Validation Layer Safety Rejection of Unsupported Candidates
- **Case 10:** Human Approval Gate Boundary
- **Case 11:** Outbox Idempotency
- **Cases 12 & 13:** Closed-Loop Precedent Learning (Positive & Negative)
- **Case 14:** Competing Hypotheses & Evidence-Weighted Scoring
- **Case 15:** Multi-Dimensional Grounded Confidence Model
- **Case 16:** Durable Outbox Worker with Exponential Backoff & Dead-Letter
- **Case 17:** Deterministic Snapshot Hashing & Material Change Detection
- **Case 18:** Rich Tool Execution History, Latency & Parameters
- **Case 19:** Dual-Mode Supervisor Planner (LLM + Gap Fallback)
- **Case 20:** Relational Evidence Graph & Falsification Conditions
- **Case 21:** Separated Root-Cause vs Recommendation Confidence
- **Case 22:** Recommendation Candidates with Operational Tradeoffs, Risks & Uncertainty
- **Case 23:** Authoritative Data Sync (`PaimanaDataSync`) & Unmutated Skip Logic
- **Benchmark Case 1:** Explanatory Coverage Convergence (no unneeded hypothesis generated)
- **Benchmark Case 2:** Unexplained Material Evidence Triggers Novel Hypothesis Invention
- **Benchmark Case 3:** Duplicate Candidate Rejected & Merged into Existing Explanation
- **Benchmark Case 4:** Invented Claims & Non-Existent Evidence References Safely Rejected
- **Benchmark Case 5:** Disproved Hypotheses Trigger Synthesis of Active Alternative Explanations
- **Benchmark Case 6:** Indistinguishable Hypotheses Yield `INSUFFICIENT_EVIDENCE` & Exploratory Site Audit
- **Benchmark Case 7:** Contradicted Hypothesis Transitions to `rejected` with Full Audit Trail
- **Benchmark Case 8:** Parent-Child Hypothesis Branching (`chronic_schedule_delay` $\rightarrow$ `H2a_...`)
- **Provenance Case 1:** Multiple Tools on Same Snapshot Capped (no artificial confidence inflation)
- **Provenance Case 2:** Truly Independent Source Groups Boost Confidence via Corroboration
- **Provenance Case 3:** Exponential Freshness Decay Discounts Stale Evidence Over Time
- **Provenance Case 4:** Authoritative Records (1.0) Outweigh Model Inferences (0.6) and LLM Claims (0.1)
- **Provenance Case 5:** Strong Authoritative Contradiction Rejects Uncorroborated Hypotheses
- **Provenance Case 6:** Derived Analytical Metrics Track Lineage & Do Not Inflate Independence
- **Provenance Case 7:** Complete Confidence History Audit Logging (`ConfidenceUpdate`)
- **Provenance Case 8:** Admin Evidence Quality Dashboard Calculates Multi-Dimensional Metrics
- **Recommendation Case 1:** Structured Candidate Generation Across Multiple Sources (Hypotheses, Evidence, Precedents, Playbooks)
- **Recommendation Case 2:** Pre-Scoring Validation Gates (Rejecting Hallucinated Evidence, Hypothesis Misalignment & Bad Precedent)
- **Recommendation Case 3:** Lineage-Aware Evidence Scoring (Single Snapshot Capped, Independent Corroboration Boosted)
- **Recommendation Case 4:** Risk Model Separates Risk Reduction from Implementation Hazard
- **Recommendation Case 5:** Pareto Frontier Filtering Eliminates Dominated Candidates
- **Recommendation Case 6:** Weighted Multi-Criteria Ranking & Confidence-Adjusted Decision Utility
- **Recommendation Case 7:** "No Recommendation" Terminal States on Safety / Policy Constraint Failure
- **Recommendation Case 8:** Transparent Decision Trace with Dominant Factors, Trade-offs & Alternative Rationales

### Section 26: Dynamic Tool Selection & Uncertainty-Driven Evidence Acquisition (Benchmark Cases 1 - 10)
- **Tool Benchmark Case 1:** Tool selection is driven by missing empirical evidence, not initial event tag (different tools chosen for identical event based on state gaps).
- **Tool Benchmark Case 2:** Follows uncertainty under 50/50 hypothesis split (selects tool with highest discrimination power for the contested pair).
- **Tool Benchmark Case 3:** Redundant tools penalized ($R_{\text{penalty}} \ge 0.50$); fresh, independent tools preferred.
- **Tool Benchmark Case 4:** New evidence dynamically changes next tool (detected contradiction immediately shifts next tool to trajectory audit).
- **Tool Benchmark Case 5:** Low-value stopping condition terminates gracefully when remaining candidate utilities fall below threshold ($0.15$).
- **Tool Benchmark Case 6:** Tool failure recovery catches exceptions, applies failure penalties ($0.85$), and safely falls back to alternative candidates.
- **Tool Benchmark Case 7:** Stale data sources are down-weighted relative to fresh sources.
- **Tool Benchmark Case 8:** Authority preference selects tools with higher source authority when expected information gain is comparable.
- **Tool Benchmark Case 9:** Permission gating prevents unauthorized execution of privileged tools under read-only sessions.
- **Tool Benchmark Case 10:** Strict budget awareness enforces call count and latency limits, stopping gracefully with `TOOL_LIMIT_REACHED`.

### Section 27: Institutional Knowledge & Closed-Loop Precedent Learning (Benchmark Cases 1 - 9)
- **Memory Benchmark Case 1:** Hybrid retrieval evaluates pattern fingerprint, contextual transferability, reliability, and decay, identifying top precedent.
- **Memory Benchmark Case 2:** Transferability evaluator penalizes domain, scale, and contract mismatches (e.g. Minor IT software discounted across highway civil works).
- **Memory Benchmark Case 3:** Known failure precedents trigger negative experience warnings and automatic validator vetoes against recurring mistakes.
- **Memory Benchmark Case 4:** Active counterexample retrieval refutes premature confirmation bias (e.g., spend stall was legal stay rather than contractor insolvency).
- **Memory Benchmark Case 5:** Closed-loop `OutcomeEvaluator` assigns causal attribution vs inconclusive confounding (`LIKELY_EFFECTIVE`, `POSSIBLY_EFFECTIVE`, `FAILED`).
- **Memory Benchmark Case 6:** Temporal decay manager applies domain-specific half-life discounting ($180\text{d}$ for policies, $365\text{d}$ for contracts, $730\text{d}$ for civil execution).
- **Memory Benchmark Case 7:** Re-verification within the same independence group prevents circular inflation; distinct independent groups boost reliability.
- **Memory Benchmark Case 8:** Full closed-loop lifecycle: Investigation $\rightarrow$ `CANDIDATE` precedent $\rightarrow$ empirical outcome observation $\rightarrow$ `VALIDATED` precedent.
- **Memory Benchmark Case 9:** Epistemic hierarchy: Authoritative current ground truth strictly overrides historical precedent memory.

### Section 28: Disciplined Causal Reasoning & Empirical Mechanism Verification (Benchmark Cases 1 - 10)
- **Causal Benchmark Case 1:** System never converts correlation into causal claim (co-occurring spend stall and milestone delay assigned `LEVEL_1_ASSOCIATION`; root cause language prohibited).
- **Causal Benchmark Case 2:** Temporal inversion detection (clearance delay requested 2 years *after* project stalled mathematically rejected as cause; downgraded to `LEVEL_1_ASSOCIATION` with penalty).
- **Causal Benchmark Case 3:** Common cause confounder detection (state treasury cashflow freeze flagged as confounding both statutory deposit delays and contractor execution; applies penalty $\ge 0.15$).
- **Causal Benchmark Case 4:** Alternative explanations maintained under ambiguous data (system flags `UNRESOLVED_CAUSAL_CONFLICT` and preserves both contractor and regulatory mechanisms).
- **Causal Benchmark Case 5:** Causal falsification conditions (ground-truth muster rolls proving 120 skilled workers and high productivity trigger contradiction penalty $\ge 0.50$, weakening contractor shortage claim).
- **Causal Benchmark Case 6:** SHAP causal safety boundary (SHAP attributions explicitly typed `MODEL_DERIVED` and disclaimer attached; predictive feature importance forbidden from serving as causal proof).
- **Causal Benchmark Case 7:** Multi-step intermediate mechanism validation (breaks mechanism into $A \to X \to Y \to B$; missing links penalize support; fully verified links achieve `LEVEL_3_MECHANISTIC_SUPPORT`).
- **Causal Benchmark Case 8:** Independent corroboration vs single snapshot (distinct independent GIS, site audit, and MPR groups score $0.90+$; multiple metrics from same snapshot capped at $0.40$).
- **Causal Benchmark Case 9:** Closed-loop intervention-supported causality (targeted intervention resolving cause verified to resume work, elevating claim to `LEVEL_5_INTERVENTION_SUPPORTED`).
- **Causal Benchmark Case 10:** Qualified uncertainty & recommendation safety gate (insufficient causal evidence bounds claim level to $\le 3$; Gate 6 vetoes premature contractual liquidated damages).

### Section 29: Multidimensional Investigation Convergence & Stopping Management (Benchmark Cases 1 - 10)
- **Convergence Benchmark Case 1:** Natural early stopping upon convergence (stops early with `CONVERGED` when multidimensional criteria are fulfilled, preserving unused budget).
- **Convergence Benchmark Case 2:** Low evidence coverage prevented from falsely converging (stops with `INSUFFICIENT_EVIDENCE` when critical gaps cannot be resolved).
- **Convergence Benchmark Case 3:** High-value tool keeps investigation open (high expected information gain tool $EV \ge 0.15$ triggers continued execution despite moderate separation).
- **Convergence Benchmark Case 4:** Low marginal utility terminates early (`NO_HIGH_VALUE_EVIDENCE_AVAILABLE` triggered when remaining tools fall below utility threshold).
- **Convergence Benchmark Case 5:** Major/Critical contradiction blocks convergence (unresolved high-severity contradiction prevents `CONVERGED` and triggers diagnostic focus).
- **Convergence Benchmark Case 6:** Low-severity minor discrepancy does not block convergence (tolerated minor reporting latency allows solid evidence to converge).
- **Convergence Benchmark Case 7:** Hypothesis instability prevents premature convergence (recent trajectory flips $\Delta_{\text{stab}} < 0.85$ keep investigation active).
- **Convergence Benchmark Case 8:** Evidence saturation detection (repeated tool invocations querying identical data lineages terminate with `NO_HIGH_VALUE_EVIDENCE_AVAILABLE`).
- **Convergence Benchmark Case 9:** Budget exhaustion distinguished from true convergence (hitting hard invocation limit strictly yields `BUDGET_EXHAUSTED` / `TOOL_LIMIT_REACHED`, never falsely marked `CONVERGED`).
- **Convergence Benchmark Case 10:** Asymmetric hysteresis & investigation reopening (high-materiality evidence spike $\ge 0.85$ or risk jump $\ge 15$ pts cleanly reopens sealed investigation).

### Section 30: Resource Governance & Investigation Budget Management (Benchmark Cases 1 - 14)
- **Governance Benchmark Case 1:** Hard tool-call ceiling enforced (further tool invocations rejected once maximum allocation is reached).
- **Governance Benchmark Case 2:** LLM token and call ceilings enforced against model consumption (discretionary prompts exceeding remaining token allowance rejected).
- **Governance Benchmark Case 3:** External API rate boundaries respected (external calls capped per investigation to prevent ministerial API throttling).
- **Governance Benchmark Case 4:** Pre-execution resource reservation prevents overdraft (concurrent operations blocked from reserving the same scarce resource envelope).
- **Governance Benchmark Case 5:** Actual vs estimated ledger accounting (complete variance tracking across execution latency and monetary costs).
- **Governance Benchmark Case 6:** Graceful degradation transitions (escalating resource pressure smoothly shifts operations across 4 tiers: `NORMAL` $\to$ `COST_AWARE` $\to$ `CONSTRAINED` $\to$ `SAFE_TERMINATION`).
- **Governance Benchmark Case 7:** Budget exhaustion explicitly couples to qualified confidence (investigation forced to stop early reports reduced evidence completeness and `PRELIMINARY_QUALIFIED` confidence with audit caveats).
- **Governance Benchmark Case 8:** Emergency reserve protection (15-20% budget reserve strictly guarded against routine exploration; unlocked only for critical contradictions).
- **Governance Benchmark Case 9:** Auditable budget expansion (high-severity events with decisive uncertainty and high expected information gain receive formal expansion).
- **Governance Benchmark Case 10:** Denied expansion terminates strictly as `BUDGET_EXHAUSTED` (never masquerades as natural convergence).
- **Governance Benchmark Case 11:** Per-tool quotas and semantic duplicate detection (blocks runaway repetition of expensive tools and flags identical queries).
- **Governance Benchmark Case 12:** Cascading cancellation releases holds (aborting superseded investigations releases all active resource holds).
- **Governance Benchmark Case 13:** Portfolio admission control and concurrency (manages active slots and priority queuing across multiple national projects).
- **Governance Benchmark Case 14:** Priority scheduling preempts low-priority investigations (critical infrastructure emergencies receive priority over routine scans).

### Section 31: Tool Reliability, Fault-Tolerant Evidence Acquisition & Recovery (Benchmark Cases 1 - 15)
- **Reliability Benchmark Case 1:** Timeout triggers bounded retries (attempt count = 2) with backoff before gracefully executing configured fallback tool.
- **Reliability Benchmark Case 2:** Repeated service timeouts trip circuit breaker from `CLOSED` to `OPEN`, immediately bypassing primary execution for subsequent calls.
- **Reliability Benchmark Case 3:** Authorization and permission failures are classified as non-retryable, bypassing retry attempts and immediately dispatching fallback.
- **Reliability Benchmark Case 4:** Incomplete payloads are marked `PARTIAL_SUCCESS`, preserving valid metrics while penalizing completeness score ($0.40$).
- **Reliability Benchmark Case 5:** Empty payload is marked `EMPTY_RESULT` (`useful_evidence = False`), strictly distinguished from clean or zero-risk indicators.
- **Reliability Benchmark Case 6:** Data exceeding staleness threshold receives `STALE_RESULT` status and exponential freshness score decay.
- **Reliability Benchmark Case 7:** Structural schema errors and invalid payloads are quarantined without polluting investigation evidence or mutating hypotheses.
- **Reliability Benchmark Case 8:** Fallback execution attaches substitution metadata, calculates authority discount ($\alpha = 0.966$), and verifies lineage isolation.
- **Reliability Benchmark Case 9:** Reliability-weighted utility ranks a moderately-informative reliable tool above an unreliable high-gain tool ($\mathcal{R}_{\text{exec}} < 0.30$).
- **Reliability Benchmark Case 10:** Recovery operations (retries and fallbacks) are charged against the `InvestigationBudget` accounting ledger.
- **Reliability Benchmark Case 11:** Tool failures operate strictly at the tool step level, preserving existing hypotheses and accumulated evidence intact.
- **Reliability Benchmark Case 12:** Circuit breaker FSM transitions from `OPEN` to `HALF_OPEN` upon cooldown expiration and returns to `CLOSED` after a successful probe.
- **Reliability Benchmark Case 13:** Preflight dependency checker detects missing database/store prerequisites and excludes candidate tools prior to invocation.
- **Reliability Benchmark Case 14:** False success returning data for an incorrect project code is intercepted by validator and quarantined (`VALIDATION_ERROR`).
- **Reliability Benchmark Case 15:** Quarantined false successes penalize the persistent `useful_evidence_rate` metric and log diagnostic reason codes.



