# PAIMANA Agentic Architecture Specification (V4 / V3-Refactored)

> **Document Version:** 4.0 (Grounded Agentic Upgrade)  
> **Status:** Production Reference & Implementation Specification  
> **Target System:** IPMD MoSPI Infrastructure Monitoring Agent  
> **Architecture Paradigm:** Dual-Mode LLM Supervisor with Deterministic Safety Constraints

---

## 1. Executive Overview: Transition to True Agentic Architecture

The PAIMANA Continuous Monitoring & Early Warning System has transitioned from a predefined multi-step branching script to a **genuinely stateful, evidence-gap-driven Agentic Architecture**.

### The Fundamental Paradigm Shift

```text
OLD PARADIGM (Predefined Workflow):
Event ──► Hardcoded Sequence (Tool A ─► Tool B ─► Tool C) ──► Fixed Template ──► Recommendation

NEW PARADIGM (Evidence-Gap Driven Agent):
Event / Goal
   │
   ▼
Supervisor Agent ◄────────────────────────┐
   │ (Analyzes Active Evidence Gaps        │
   │  & Competing Hypotheses)              │
   ▼                                      │
Select Next Tool Dynamically              │ (Observation modifies next action
   │ (LLM Planner with Gap-Directed        │  and updates posterior probabilities)
   │  Safety Fallback)                    │
   ▼                                      │
Execute Tool via ToolRegistry             │
   │                                      │
Record Rich Audit Execution (ID, Latency) │
   │                                      │
Observe Result & Update State             │
   │                                      │
Extract Facts & Inferences                │
   │                                      │
Detect Cross-Source Contradictions        │
   │                                      │
Update 4 Competing Hypotheses & Confidence│
   │                                      │
Evidence Sufficient / Budget Exhausted? ──┘
   │ (YES)
   ▼
Evidence Validation Layer
   │
Candidate Recommendation Evaluation (Against Precedents & Safety Rules)
   │
Human-in-the-Loop Sign-off Boundary
   │
Durable Automation Outbox (Autonomous Worker with Exponential Backoff)
```

---

## 2. Stateful Dual-Mode Supervisor Architecture

The **Supervisor Agent** ([`supervisor.py`](paimana_agent/supervisor.py)) is a stateful orchestrator that formulates an explicit investigation objective, dynamically decides what information is missing, chooses tools step by step, and stops when sufficient evidence has been gathered.

### 1. Dual-Mode Planner:
- **LLMSupervisorPlanner**: When an LLM endpoint is enabled in `config.yaml` (`cfg['llm']`), the supervisor prompts the LLM with active evidence gaps, 4 competing hypotheses with prior/posterior probabilities, tool definitions/schemas, and remaining budget. The LLM outputs a structured JSON decision (`EXECUTE_TOOL` or `CONCLUDE`).
- **DynamicEvidenceGapPlanner (Deterministic Safety Fallback)**: If the LLM is unconfigured, disabled, or unreachable, an intelligent gap-directed planner evaluates which tool provides the highest information gain to discriminate between the top 2 competing hypotheses.

### 2. Explicit Controlled Termination Criteria:
- `SUFFICIENT_EVIDENCE`: Top hypothesis posterior probability reaches discrimination threshold ($\ge 0.65$), multi-source cross-verification is complete, and no unresolved contradictions remain.
- `TOOL_LIMIT_REACHED`: Maximum tool execution budget exhausted (default: 5 tools) to prevent runaway execution.
- `INSUFFICIENT_DATA`: Data sources unavailable or project lacks historical snapshots.
- `UNRESOLVED_CONTRADICTION`: Critical cross-source discrepancy prevents conclusive diagnosis.

---

## 3. Investigation State Model

The investigation state ([`state.py`](paimana_agent/state.py)) persists throughout the entire investigation and acts as the single source of truth:

```python
@dataclass
class ToolExecutionRecord:
    call_id: str                          # Unique execution identifier (e.g. exec_1_financial_velocity)
    tool_name: str
    parameters: dict                      # Runtime invocation parameters
    result_summary: str
    result_data: Any
    status: str = "success"               # success, error, partial
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

@dataclass
class Hypothesis:
    name: str
    hypothesis: str
    status: str = "COMPETING"             # PRIMARY, COMPETING, WEAKENED, REJECTED
    confidence: str = "MEDIUM"            # HIGH, MEDIUM, LOW
    prior_prob: float = 0.25              # Initial normalized prior
    posterior_prob: float = 0.25          # Evidence-weighted posterior probability
    supporting_evidence_ids: list[str]
    contradicting_evidence_ids: list[str]
    falsification_condition: str = ""     # Explicit criteria that would falsify this hypothesis
    net_score: float = 0.0

@dataclass
class RecommendationCandidate:
    action: str
    responsible_stakeholder: str
    urgency: str                          # CRITICAL, HIGH, MEDIUM, ROUTINE
    justification: str
    supporting_evidence: list[str]
    candidate_type: str = "PRIMARY_RECOVERY"  # PRIMARY_RECOVERY, FORENSIC_AUDIT, INTERIM_MITIGATION, BASELINE_REVIEW
    tradeoffs: str = ""                   # Operational trade-offs accepted
    risks: str = ""                       # Downstream friction / implementation risks
    uncertainty: str = "LOW"              # LOW, MEDIUM, HIGH
    precedent_outcome: Optional[str] = None
    expected_impact: str = ""
    validated: bool = False
    validation_reasons: list[str] = field(default_factory=list)

@dataclass
class InvestigationState:
    objective: str
    project_code: str
    project_name: str
    triggering_events: list[dict]
    
    # Structured Evidence & Relational Graph
    facts: list[Fact]                     # Verified ground-truth metrics from CUF
    inferences: list[Inference]           # Derived analytical signals
    hypotheses: list[Hypothesis]          # 4 competing causal explanations
    contradictions: list[Contradiction]   # Explicitly recorded data conflicts
    evidence_gaps: list[str]              # Missing evidence items dynamically tracked
    evidence_graph: list[dict]            # Relational edges (source, relation, target, weight)
    
    # Tool Execution & Rich Audit Trail
    tools_used: list[str]
    tool_executions: list[ToolExecutionRecord]
    observations: dict[str, Any]
    
    # Dynamic Reasoning Trace & Separated Grounded Confidence
    investigation_steps: list[dict]
    decision_trace: list[dict]
    evidence_confidence: str              # HIGH, MEDIUM, LOW
    confidence_score: float               # Backward-compatible alias
    root_cause_confidence: float          # Epistemic confidence in diagnosis (0.0 to 1.0)
    recommendation_confidence: float      # Action feasibility & precedent confidence (0.0 to 1.0)
    confidence_breakdown: dict[str, float] # Explicit dimensional scores
    confidence_reasons: list[str]
    tool_budget: int
    termination_reason: str
    
    # Recommendations
    candidate_recommendations: list[RecommendationCandidate]
    selected_recommendation: Optional[RecommendationCandidate]
```

---

## 4. The 4 Competing Causal Hypotheses & Falsification Conditions

Rather than using single static templates, every investigation continuously discriminates between four competing causal hypotheses, each with an explicit **falsification condition** ("What would change the agent's mind?"):

| Hypothesis ID | Title | Core Causal Claim | Falsification Condition | Primary Discriminating Tool |
| :--- | :--- | :--- | :--- | :--- |
| `front_loaded_billing` | Expenditure-Physical Decoupling | Funds drawn/billed ahead of certified physical milestone delivery. | Independent technical audit certifies physical works match disbursements within 5% tolerance. | `financial_velocity` + `milestone_audit` |
| `chronic_schedule_delay` | Execution & Mobilization Delay | Civil work, manpower, or equipment bottlenecks causing structural schedule slippage. | Resource-loaded catch-up milestones demonstrate contractor has recovered critical-path schedule. | `milestone_audit` + `project_history` |
| `regulatory_land_clearance` | Regulatory Clearances & RoW | Statutory approvals, environmental clearances, or land acquisition stalled site handover. | Portal records verify 100% encumbrance-free RoW and Stage-2 statutory approvals in hand. | `peer_intelligence` + `project_history` |
| `reporting_discrepancy` | MPR Data Inconsistency | Administrative delay or discrepancy between physical MPR and financial ledger. | Reconciliation of field engineer progress books proves data entry consistency with zero lag. | `milestone_audit` + cross-source checks |

---

## 5. Separated Multi-Dimensional Confidence Architecture

The system avoids conflating epistemic diagnostic certainty with action efficacy by separating:

### 1. Root-Cause Confidence (`root_cause_confidence`):
Grounded strictly in data quality, independent sources, and hypothesis margin:
$$\text{Root-Cause Confidence} = \text{Quality} + \text{Independence} + \text{Separation} - \text{Contradiction Penalty}$$

1. **Evidence Quality ($0.0 - 0.25$):** Ratio of verified facts extracted directly from official CUF ledgers.
2. **Evidence Independence ($0.0 - 0.25$):** Number of distinct independent tools consulted.
3. **Hypothesis Separation ($0.0 - 0.25$):** Separation margin between #1 and #2 hypothesis ($P(H_1) - P(H_2)$).
4. **Contradiction Penalty ($-0.20$):** Active discrepancies across data sources deduct from overall confidence.

### 2. Recommendation Confidence (`recommendation_confidence`):
Evaluates operational intervention likelihood of success:
$$\text{Recommendation Confidence} = 0.35 \times \text{Precedent Factor} + 0.35 \times \text{Root-Cause Confidence} + 0.30 \times \text{Authority Fit}$$

---

## 6. Early Snapshot Hashing, Continuous Monitoring & Data Sync

To prevent wasted ML inference and redundant investigations, the agent implements **Early Deterministic Snapshot Hashing** and the **Authoritative Data Synchronization Service** ([`sync.py`](paimana_agent/sync.py)):
- Computes SHA-256 hash of core project attributes:
  ```python
  snapshot_hash = compute_snapshot_hash(project_dict)
  ```
- Evaluated at the top of `evaluate_project()`. If unmutated (`material_change: False`), ML predictors (cost overrun, time overrun, risk score) and SHAP feature attributions are completely bypassed.
- **PaimanaDataSync:** Ingestion layer that handles batch API and JSON/CSV feeds, skipping unmutated projects and isolating mutated records for immediate evaluation.

---

## 7. Autonomous Durable Outbox Worker with Exponential Backoff

The outbox queue ([`store.py`](paimana_agent/store.py)) guarantees delivery of human-approved actions to downstream automation workflows (n8n webhooks, email alerts, APIs):
- **Atomic Task Leasing:** Claims tasks inside a single SQLite transaction lock, transitioning status to `processing`.
- **Idempotency:** Repeated approvals return `is_new: False` and enqueue tasks exactly once.
- **Autonomous OutboxWorker:** Runs in the background (or synchronously via `drain_once()`).
- **Retry Schedule with Exponential Backoff:**
  - `retrying` status with `next_retry_at = time.time() + backoff` ($\text{delay} = \min(60.0, 2^{\text{attempts}} \times 1.5)$).
  - Transition to `dead_letter` queue upon reaching `max_attempts` (default: 4), preserving error traces for administrators.

---

## 8. Real Langfuse Instrumentation

The telemetry tracer ([`tracer.py`](paimana_agent/tracer.py)) instruments the investigation lifecycle:
- Automatically detects and initializes Langfuse client when configured.
- Emits real Langfuse primitives:
  - `trace`: Investigation lifecycle with project code, objective, and triggers.
  - `generation`: Supervisor reasoning plans and tool decisions.
  - `span`: Tool executions with latency, inputs, and results.
  - `event`: Contradictions detected, hypothesis updates, and recommendation validations.
  - `score`: Grounded multi-dimensional confidence scores.
- Non-blocking: Gracefully logs internally if Langfuse is absent or offline.

---

## 9. Comprehensive Behavioral Verification Matrix (23 Test Cases)

All 23 conceptual test cases (covered across 19 executable pytest functions in [`tests/test_agent_behavior.py`](tests/test_agent_behavior.py)) pass on Anaconda Python 3.14:

| Test Case | Description | Verified Behavior |
| :--- | :--- | :--- |
| **Case 1 & 2** | Dynamic Multi-step Investigation | Supervisor expands investigation dynamically when initial evidence is insufficient. |
| **Case 3** | Dynamic Path Adaptation | Supervisor alters tool sequence based on whether trigger is schedule delay vs spend gap. |
| **Case 4** | Contradiction Detection | Schedule vs physical progress conflict detected and penalizes confidence. |
| **Case 5** | Tool Failure Recovery | Tool timeout/failure handled gracefully without crashing investigation. |
| **Case 6 & 7** | Controlled Budget Termination | Explicit termination reason (`TOOL_LIMIT_REACHED` / `SUFFICIENT_EVIDENCE`) under budget. |
| **Case 8 & 9** | Validation Layer Rejection | Rejects recommendation candidates lacking supporting evidence or proper authority. |
| **Case 10** | Human Approval Boundary | Actions remain in `pending_approval` until explicit authorized human sign-off. |
| **Case 11** | Outbox Idempotency | Duplicate enqueue returns existing task ID. |
| **Case 12 & 13** | Precedent Learning & Avoidance | Positive precedent cited; past failed action avoided. |
| **Case 14** | Competing Hypotheses | 4 competing causal hypotheses tracked with evidence-weighted posterior scoring. |
| **Case 15** | Multi-Dimensional Confidence | 5 distinct grounded confidence dimensions evaluated and reported. |
| **Case 16** | Outbox Worker & Dead-Letter | Retry backoff and dead-letter queue transition verified. |
| **Case 17** | Snapshot Hashing | Unmutated edits detected as `material_change: False`. |
| **Case 18** | Rich Tool Execution Audit | Records individual tool invocations with unique IDs, parameters, and latencies. |
| **Case 19** | Dual-Mode LLM & Fallback | LLM planner with dynamic gap planner fallback verified. |
| **Case 20** | Relational Evidence Graph & Falsification | Directed evidence graph and explicit falsification conditions on all hypotheses. |
| **Case 21** | Separated Confidences | Root-cause confidence separated from action/recommendation confidence. |
| **Case 22** | Recommendation Candidate Tradeoffs | Candidates include explicit operational tradeoffs, risks, and uncertainty levels. |
| **Case 23** | Authoritative Data Sync (`PaimanaDataSync`) | Batch ingestion skipping unmutated projects and evaluating mutated ones. |
| **Benchmark 1** | Explanatory Coverage Convergence | Existing hypothesis explains all evidence; suppresses redundant generation. |
| **Benchmark 2** | Dynamic Hypothesis Generation | Unexplained material evidence triggers invention of novel hypothesis candidate. |
| **Benchmark 3** | Semantic Deduplication & Merging | Duplicate candidate rejected and merged with existing hypothesis. |
| **Benchmark 4** | Invented Claim & Hallucination Guardrail | Non-existent evidence references and unsupported accusations safely rejected. |
| **Benchmark 5** | Disproved Hypothesis Alternative Synthesis | Disproved hypotheses trigger generation of active alternative explanations. |
| **Benchmark 6** | Indistinguishable Evidence Calibration | Indistinguishable hypotheses result in INSUFFICIENT_EVIDENCE & forensic audit. |
| **Benchmark 7** | Contradiction State Transition | Contradicted hypothesis transitions to 'rejected' with full audit trail preserved. |
| **Benchmark 8** | Parent-Child Hypothesis Branching | Broad hypothesis cleanly branches into specialized child explanations (e.g. H2a). |

---

## 10. Dynamic Hypothesis Invention & Evidence Lifecycle (V4+)

The PAIMANA Agentic Layer has evolved beyond fixed hypothesis-scoring templates into a **fully dynamic, evidence-driven hypothesis invention and explanatory coverage architecture**.

### 1. The Explanatory Coverage Loop

```text
Incoming Anomaly Event
          │
          ▼
Normalize Baseline Ground Truth Facts into First-Class Evidence
          │
          ▼
Seed Initial Competing Hypotheses
          │
          ▼
┌────────────────────────────────────────────────────────┐
│             DYNAMIC INVESTIGATION LOOP                 │
│                                                        │
│ 1. Plan Next Action (LLM / Evidence-Gap Fallback)      │
│ 2. Execute Discriminating Tool                         │
│ 3. Normalize Output into First-Class Evidence Items    │
│ 4. Evaluate Explanatory Coverage:                      │
│    - EXPLAINED / PARTIALLY_EXPLAINED                   │
│    - UNEXPLAINED / CONTRADICTORY                       │
│ 5. Coverage Check: Do current hypotheses explain it?   │
│    ├── YES: Continue testing / converge                │
│    └── NO: Trigger Dynamic Hypothesis Generation       │
│         - Condition A: Material evidence unexplained   │
│         - Condition B: Leading hypotheses weakened     │
│         - Condition C: Persistent contradictions       │
│ 6. Validate Candidates (Schema, Evidence IDs, Truth)   │
│ 7. Check Semantic Overlap (Deduplicate / Branch H2a)   │
│ 8. Enforce Hypothesis Budgets (Max 6 Active, 10 Total) │
│ 9. Update Support, Contradiction & Confidence Scores   │
└────────────────────────────────────────────────────────┘
          │ (Conclude / Tool Budget Limit Reached)
          ▼
Determine Investigation Outcome:
- ROOT_CAUSE_SUPPORTED
- ROOT_CAUSE_PARTIALLY_SUPPORTED
- MULTIPLE_PLAUSIBLE_CAUSES
- INSUFFICIENT_EVIDENCE
- CONTRADICTORY_EVIDENCE
          │
          ▼
Calibrate Recommendations:
- High Confidence: Actionable Intervention with Responsible Stakeholder
- Inconclusive / Low Confidence: Targeted Forensic Site Audit
```

### 2. First-Class `Evidence` Entity
Each observation is normalized into a strongly-typed entity (`paimana_agent/evidence/model.py`):
- `id`: Unique identifier (e.g. `ev_financial_velocity_gap`).
- `source_tool`: The originating tool (`financial_velocity`, `milestone_audit`, etc.).
- `source_type`: `GROUND_TRUTH_METRIC`, `TOOL_OUTPUT`, or `DERIVED_SIGNAL`.
- `claim`: Natural-language factual assertion.
- `raw_value` & `derived_value`: Quantitative audit values.
- `reliability`: Epistemic weight ($0.0 - 1.0$).
- `supports_hypotheses` & `contradicts_hypotheses`: Targeted linkages.
- `is_material`: Flags high-significance facts.
- `coverage_status`: `EXPLAINED`, `PARTIALLY_EXPLAINED`, `UNEXPLAINED`, or `CONTRADICTORY`.

### 3. Dynamic Hypothesis Invention (`HypothesisGenerator`)
Triggered automatically when:
- Unexplained material evidence exists after observation updates.
- All active hypotheses fall below a confidence threshold ($\le 0.35$).
- Direct contradictions disprove the leading seeded explanations.

Candidates must strictly define:
- `statement` & causal `mechanism`.
- `predicted_observations`: What future tools should observe if true.
- `discriminating_evidence`: What specific data would distinguish it from other explanations.
- `falsification_condition`: What ground fact would disprove it.

### 4. Hypothesis Validation & Similarity Guardrails
- **`HypothesisValidator`**: Ensures all cited evidence IDs exist, rejects invented facts or ungrounded accusations (e.g. fraud without explicit audit evidence), and enforces falsifiability.
- **`HypothesisSimilarityChecker`**: Computes Jaccard semantic overlap with domain synonym mapping. Candidates with $>35\%$ token overlap are deduplicated and merged; candidates that provide specialized causal mechanisms are cleanly branched as child hypotheses (e.g. `parent_hypothesis_id = 'chronic_schedule_delay'`).
- **Hypothesis Budget Enforcement**: Strict runtime constraints prevent hypothesis sprawl (`max_active=6`, `max_generated_per_iteration=2`, `max_total_generated=10`).
- **Audit Integrity**: Rejected hypotheses are **never deleted**; they transition to `rejected` with `rejection_reason` preserved for complete inspection.

### 5. Calibrated Recommendation Policy
Recommendations are strictly bound to investigation outcome certainty:
- **`ROOT_CAUSE_SUPPORTED`**: Generates high-urgency, domain-specific mitigation (e.g. Joint Financial-Physical Audit Taskforce or Catch-Up Schedule) assigned to appropriate statutory authorities.
- **`INSUFFICIENT_EVIDENCE` / `CONTRADICTORY_EVIDENCE`**: Restricts recommendations to exploratory, non-disruptive technical inspections rather than punitive contractual actions.

---

## 6. Provenance, Freshness Decay & Independent Corroboration Specification

### 1. The Core Scientific Premise
Confidence in an investigation must reflect **independent verification**, not repeated measurements of the same data point. If multiple analytical tools (e.g., `financial_velocity`, milestone audits, risk models) all ingest the same monthly project snapshot, they belong to the same underlying partition (`independence_group_id = 'PAIMANA_SNAPSHOT_<code_month>'`).

### 2. Provenance Data Structures
- **`SourceLineage`**: Records `source_id`, `source_type`, `source_system`, `source_record_id`, `source_field`, `observed_at`, `recorded_at`, `retrieved_at`, and `authority_score`.
- **`EvidenceGroup`**: Partitions evidence by `group_id`, grouping direct observations (`base_evidence_ids`) and derived analytical signals (`derived_evidence_ids`), tracking group-level net strength.
- **`ConfidenceUpdate`**: High-resolution audit log of every confidence update, capturing `prev_confidence`, `new_confidence`, `support_delta`, `contradiction_delta`, `independent_groups`, and natural-language justification.

### 3. Source Authority Scale & Half-Life Freshness
```python
SOURCE_AUTHORITY = {
    "official_project_record": 1.00,
    "verified_financial_record": 1.00,
    "ground_audit_log": 0.95,
    "sensor_iot_telemetry": 0.90,
    "historical_dataset": 0.80,
    "model_inference": 0.60,
    "peer_benchmark": 0.50,
    "llm_claim": 0.10,
    "unverified_assertion": 0.10,
}
```
Freshness decay is calculated continuously via:
$$\text{freshness} = \exp\left(-\frac{\ln(2) \cdot \text{age\_days}}{\tau}\right)$$
where $\tau$ ranges from 7 days (IoT sensor feeds) to 180 days (historical datasets).

### 4. Independent Group-Level Aggregation Formula
For each distinct `independence_group_id` supporting a hypothesis:
$$\text{Group Strength} = \min\left(1.0, \text{Primary Base Strength} + \min(0.35, 0.25 \times \sum \text{Derived Strength})\right)$$
Total support across $N_{\text{indep}}$ independent groups:
$$\text{Total Support} = \sum_{g=1}^{N_{\text{indep}}} \text{Group Strength}_g + 0.20 \times (N_{\text{indep}} - 1) \quad (\text{for } N_{\text{indep}} \ge 2)$$

### 5. Verified Contradiction Rejection Rule
When an authoritative, verified source ($\text{authority} \ge 0.90$, $\text{effective strength} \ge 0.90$) directly contradicts a hypothesis with lower or zero support:
$$\text{Status} \rightarrow \text{"rejected"}$$
Preserving full audit logs, contradicting group IDs, and rejection explanations.

---

## 7. Recommendation Candidate Generation, Validation & Constrained Ranking Specification

### 1. The Fundamental Architectural Boundary
> **The LLM may propose and explain candidates; the ranking engine determines which validated candidate is selected.**

This prevents the generative model from silently optimizing its own recommendation and ensures that every intervention selected for human sign-off is mathematically justified by empirical evidence, institutional authority, and cost-benefit trade-offs.

### 2. Multi-Criteria Evaluation Models
Each validated candidate is scored across five explicit normalized dimensions ($0.0 - 1.0$):
1. **Expected Benefit Utility ($U_B$):**
   $$U_B = 0.35 \cdot \text{risk\_reduction} + 0.25 \cdot \text{schedule\_improvement} + 0.25 \cdot \text{cost\_avoidance} + 0.15 \cdot \text{problem\_resolution}$$
2. **Cost Utility ($U_C$):**
   Normalized burden combines direct financial cost, staff effort, management overhead, and intervention-induced schedule pauses:
   $$U_C = 1.0 - \text{normalized\_burden}$$
3. **Balanced Risk ($U_R$):**
   Separates project risk mitigated from new operational/contractual hazard introduced:
   $$U_R = \text{expected\_risk\_reduction} \times (1.0 - \text{implementation\_risk})$$
4. **Lineage-Aware Evidence Strength ($U_E$):**
   Evaluates cited evidence items grouped by `independence_group_id`. Single snapshots are capped ($\le 0.80$); corroborated multi-group evidence achieves up to $1.00$. Contradiction penalties apply directly.
5. **Authority Score ($U_A$):**
   Combines mean epistemic authority of cited sources with institutional fit against statutory stakeholder levels.

### 3. Pareto Frontier Filtering
Prior to weighted ranking, candidate $A$ strictly dominates candidate $B$ if:
$$A \ge B \quad \forall \text{ dimensions} \quad \text{and} \quad \exists d \text{ s.t. } A_d > B_d$$
Strictly dominated candidates are filtered out (`is_dominated = True`), while genuine operational trade-offs remain on the Pareto frontier.

### 4. Weighted Multi-Criteria Utility & Confidence Adjustment
$$U_{\text{raw}} = W_B U_B + W_C U_C + W_R U_R + W_E U_E + W_A U_A$$
$$\text{Adjusted Score} = U_{\text{raw}} \times (0.50 + 0.50 \times \text{decision\_confidence})$$
Where weights sum to $1.0$ and are configured per policy class (`standard`, `early_warning`, `escalation`, `financial`, `data_quality`).

### 5. Auditable Decision Trace & "No Recommendation" States
The selector outputs a `RecommendationDecision` with explicit `selection_reason`:
- `dominant_factors`: Key mathematical advantages of the winner.
- `tradeoffs`: Necessary compromises declared explicitly.
- `why_alternatives_not_selected`: Structured breakdown of why runners-up lost.
- Terminal outcomes safely handle failures without forcing an intervention: `RECOMMENDATION_SELECTED`, `MULTIPLE_CANDIDATES_REQUIRE_REVIEW`, `INSUFFICIENT_EVIDENCE`, `NO_ELIGIBLE_CANDIDATE`, `HIGH_ACTION_RISK`, `AUTHORITY_INSUFFICIENT`, `CONFLICTING_EVIDENCE`.

---

## 8. Dynamic Tool Selection & Uncertainty-Driven Evidence Acquisition Framework

### 1. The Fundamental Architectural Shift
Prior systems routed tool invocations statically based on initial event keywords:
$$\text{EVENT} \rightarrow \text{Event Keyword} \rightarrow \text{Static Tool Sequence}$$

The PAIMANA V3+ Dynamic Investigation Engine models tool invocation as an **explicit optimal information acquisition problem**:
$$\text{InvestigationState} \xrightarrow[\text{gaps \& conflicts}]{\text{Analyze}} \text{EvidenceNeeds} \xrightarrow[\text{utility scoring}]{\text{Evaluate Candidates}} \text{Optimal Next Tool} \rightarrow \text{Observation} \rightarrow \text{State Update}$$

The agent chooses a tool **not because the event type suggests it, but because that tool reduces critical evidentiary uncertainty and discriminates competing hypotheses at minimal cost and redundancy**.

### 2. Specialist Tool Descriptors (`ToolDescriptor`)
Every capability in `ToolRegistry` is defined with a comprehensive operational descriptor:
- **Capabilities**: Specific analytical questions answered (e.g., `audit_spend_progress_decoupling`, `audit_milestone_schedule_slippage`).
- **Evidence Types Generated**: Canonical data outputs produced (e.g., `financial_audit`, `schedule_milestone`, `peer_baseline`, `precedent_memory`, `trajectory_history`, `model_attribution`).
- **Hypothesis Domains**: Causal explanations targeted for confirmation or falsification.
- **Source Authority ($A \in [0, 1]$)**: Epistemic trustworthiness of underlying data (CUF ledger: 0.92, Milestone schedule: 0.90, Historical database: 0.85, Peer baseline: 0.80, SHAP attribution: 0.75).
- **Operational Profile**: Typical latency (ms), execution cost ($C \in [0, 1]$), and freshness half-life.
- **Discrimination Targets**: Specific hypothesis pairs the tool is designed to differentiate.
- **Prerequisites & Authorization**: Required runtime objects (`store`, `model`, `p`) and permission gating (`read_only` vs `privileged`).

### 3. First-Class `EvidenceNeed` Declarations
Evidence gaps are not unstructured strings, but first-class entities with explicit attributes:
- `id`: Unique need identifier (e.g., `need_financial_velocity`, `need_discriminate_H1_H2`).
- `question`: Precise operational question requiring empirical observation.
- `target_hypothesis_ids`: Competing hypotheses affected by this evidence.
- `required_evidence_types`: Accepted canonical evidence categories.
- `priority & urgency`: Dynamic weights ($0.0 - 1.0$) calibrated against anomaly severity and state entropy.
- `discrimination_power`: Measure of how decisively resolving this need separates competing explanations.
- `status`: Lifecycle state (`OPEN` $\rightarrow$ `SATISFIED` $\mid$ `UNRESOLVABLE`).

### 4. Dynamic Information Gain & Hypothesis Discrimination
Information gain is calculated dynamically based on active hypothesis entropy and open needs:
1. **Uncertainty Scaling**: Highest when competing hypotheses are closely contested (e.g., 50/50 split margin $\approx 0.0$):
   $$\text{Uncertainty} = \max\left(0.20, 1.0 - |\text{conf}(H_1) - \text{conf}(H_2)|\right)$$
2. **Diminishing Need Sum**: When a tool addresses multiple open needs, contributions are combined with diminishing marginal returns:
   $$\text{Gain}_{\text{needs}} = \sum_{i=1}^k g_i \cdot (0.35)^{i-1} \quad (g_1 \ge g_2 \ge \dots)$$
3. **Pair Discrimination Boost**: If the tool explicitly targets the active competing hypothesis pair:
   $$\text{Gain} = \min\left(1.0, 1.20 \cdot \text{Gain}_{\text{needs}} \cdot \text{Uncertainty}\right)$$

### 5. Multi-Criteria Tool Utility Engine ($U_{\text{tool}}$)
For each eligible candidate tool $t$, net utility is computed across six weighted dimensions minus operational penalties:
$$U_{\text{net}}(t) = w_{\text{gain}} \cdot \text{Gain} + w_{\text{disc}} \cdot \text{Disc} + w_{\text{auth}} \cdot \text{Auth} + w_{\text{fresh}} \cdot \text{Fresh} - w_{\text{cost}} \cdot \text{Cost} - w_{\text{lat}} \cdot \text{LatNorm} - R_{\text{penalty}} - F_{\text{penalty}}$$
Default weights: $w_{\text{gain}} = 0.35, w_{\text{disc}} = 0.25, w_{\text{auth}} = 0.15, w_{\text{fresh}} = 0.10, w_{\text{cost}} = 0.08, w_{\text{lat}} = 0.07$.

- **Redundancy Penalty ($R_{\text{penalty}} \ge 0.60$)**: Applied if the tool has already executed in this session on the same static dataset, or queries an already verified independent group without novel insight.
- **Failure Penalty ($F_{\text{penalty}} \ge 0.85$)**: Applied if previous tool execution failed or threw exceptions, ensuring automatic fallback.
- **Permission Gating**: Ineligible if caller authorization level is lower than statutory requirement (e.g., `privileged` tool requested under `read_only` session).

### 6. Operational Phases & Budget Enforcement (`InvestigationBudget`)
Investigations progress adaptively through structured phases:
1. `ORIENTATION`: Initial triage of primary anomaly indicators.
2. `DISCRIMINATION`: Targeted probing to separate contested hypotheses.
3. `VALIDATION`: Independent cross-source corroboration of leading hypothesis.
4. `DECISION_SUPPORT`: Precedent learning and recommendation calibration.
5. `CONCLUDED`: Terminal state.

**Controlled Stopping Policy (`ConvergenceDetector`):**
- `CONVERGED`: Dominant hypothesis confidence $\ge 0.70$, margin over runner-up $\ge 0.25$, corroborated by $\ge 2$ independent source groups.
- `SUFFICIENT_EVIDENCE`: All declared evidence needs satisfied.
- `NO_HIGH_VALUE_TOOL_REMAINING`: Maximum eligible candidate utility $< \text{min\_utility\_threshold}$ ($0.15$). Prevents wasteful tool invocations.
- `TOOL_LIMIT_REACHED` / `INVESTIGATION_BUDGET_EXCEEDED`: Hard call count or cumulative latency ceiling reached.

---

## 9. Institutional Knowledge & Closed-Loop Precedent Learning Engine

Memory has transitioned from simple key-value retrieval (`store -> retrieve -> display`) to a true **institutional learning lifecycle**:
$$\text{investigation} \longrightarrow \text{outcome} \longrightarrow \text{evaluate} \longrightarrow \text{validate} \longrightarrow \text{consolidate} \longrightarrow \text{retrieve} \longrightarrow \text{adapt} \longrightarrow \text{reuse} \longrightarrow \text{learn}$$

### 1. Durable Unit: First-Class `Precedent`
The primary atomic unit of durable institutional memory is a validated `Precedent`:
- **Pattern Fingerprint**: Compact, structured representation of anomaly dynamics (`financial_velocity`, `milestone_slippage`, `progress_variance`, `risk_velocity`, `risk_direction`, `approval_delay`, `contractor_delay`).
- **Context Envelope (`PrecedentContext`)**: Sector, project type, scale band (Mega $>1000\text{Cr}$, Standard, Minor), lifecycle stage bracket (Early $<25\%$, Mid $25-75\%$, Late $>75\%$), implementing agency, and contract type (EPC, HAM, Item Rate).
- **Evidentiary & Causal Signatures**: Hypotheses tested, established root cause, and base evidentiary confidence.
- **Intervention & Empirical Outcome**: Specific action executed, expected impact, and observed empirical outcome ($\Delta\text{metrics}$).
- **Attribution Class**: Rigorous causal classification (`LIKELY_EFFECTIVE`, `POSSIBLY_EFFECTIVE`, `INCONCLUSIVE`, `LIKELY_INEFFECTIVE`, `FAILED`).
- **Memory Reliability ($R \in [0, 1]$)**: Calculated via Bayesian track record with Laplace smoothing and independent corroboration tracking.
- **Traceability & Provenance**: Source investigation IDs, source project IDs, and independent authority groups.

### 2. Multi-Dimensional Contextual Transferability (`TransferabilityEvaluator`)
When considering a historical precedent for a current investigation, the system calculates contextual transferability across 5 dimensions:
$$\text{Transferability} = 0.30 \cdot \text{Sector} + 0.20 \cdot \text{Contract} + 0.20 \cdot \text{CostBand} + 0.15 \cdot \text{Stage} + 0.15 \cdot \text{Agency}$$
- **Transferability Discounting**: If transferability falls below $0.40$ (e.g., cross-applying IT software practices to mega highway civil works), the precedent composite relevance is discounted by 50% to prevent false positive transfers.

### 3. Anti-Circular Reinforcement & Independence Groups
To prevent the echo-chamber phenomenon where running 10 investigations on the same project falsely inflates confidence, precedents track `independence_group_ids`:
- Confirmations from the *same* project or authority group do not increase the independent corroboration factor.
- Corroborations from *distinct, independent* regional offices or agencies boost reliability up to $1.00$.

### 4. Domain-Specific Temporal Decay (`MemoryDecayManager`)
Precedents age according to domain-calibrated half-lives:
$$\text{Decay} = 2^{-\Delta t / T_{1/2}}$$
- Statutory regulations & circulars: $T_{1/2} = 180\text{ days}$ (~6 months)
- Contractual norms & cost benchmarks: $T_{1/2} = 365\text{ days}$ (~1 year)
- General infrastructure civil execution: $T_{1/2} = 730\text{ days}$ (~2 years)
- Physical geology & engineering patterns: $T_{1/2} = 1095\text{ days}$ (~3 years)

### 5. Tri-Perspective `PrecedentBundle` Retrieval
Retrieval generates a balanced bundle to eliminate confirmation bias:
1. **Supporting Precedents**: Validated actions that successfully resolved similar patterns in comparable contexts.
2. **Failed Precedents & Negative Warnings**: Past actions that backfired (e.g. premature show-cause notices while land remained encumbered), providing active veto warnings to the recommendation engine.
3. **Explicit Counterexamples**: Cases that exhibited identical symptoms but possessed completely different root causes (e.g., spend stall caused by an NGT legal injunction rather than contractor cashflow distress).

### 6. Closed-Loop Consolidation Pipeline (`MemoryConsolidator`)
Completed investigations do not automatically become canon:
1. Concluded investigation creates a `CANDIDATE` precedent (reliability $\approx 0.30 - 0.50$).
2. Months later, physical/financial data is monitored and `OutcomeEvaluator` analyzes $\Delta\text{metrics}$ ($\Delta\text{risk}$, $\Delta\text{gap}$, $\Delta\text{delay}$) while discounting for reported external confounders.
3. Successful empirical attribution promotes the precedent to `VALIDATED` (reliability up to $0.85 - 0.95$). Unsuccessful outcomes become validated cautionary failure precedents.

### 7. Strict Epistemic Hierarchy
> **Authoritative current ground-truth evidence strictly overrides historical precedent.**
Precedent memory informs hypothesis generation and tool prioritizing, but can never outvote contradictory current facts or official ground-truth records.

---

## 10. Disciplined Causal Reasoning & Empirical Mechanism Verification Engine

```
Observation
   ↓
Association (Correlation)
   ↓
Temporal Precedence Verification
   ↓
Candidate Mechanism Instantiation (Domain Ontology)
   ↓
Intermediate Link Verification (Multi-Step Transmission)
   ↓
Confounder Analysis & Common Cause Penalties
   ↓
Counterfactual & Natural Comparison Group Analysis
   ↓
Causal Falsification Checks
   ↓
Qualified Causal Level Assignment (Level 0 – 5)
   ↓
Calibrated Recommendation Engine (Gate 6 Bound)
```

The investigation layer guarantees that the system never confuses statistical correlation with real-world causal transmission. Moving from **“identifying correlated symptoms and attaching a likely cause”** to **“disciplined causal mechanism verification”**, the engine enforces rigorous causal standards.

### 1. The Core Causal Contract
> **The system must never convert correlation into causal language merely because two variables move together.**
> Root cause claims are strictly prohibited unless the evidence satisfies explicit causal criteria: verified temporal precedence, intermediate transmission links, confounder accounting, and absence of active falsifiers.

### 2. 6-Tier Causal Claim Levels
Every causal assertion is explicitly typed with a formal `CausalClaimLevel`:
- **`LEVEL_0_OBSERVATION`**: Two or more anomalies are present in project records (e.g. expenditure variance and schedule lag).
- **`LEVEL_1_ASSOCIATION`**: Statistical co-occurrence or correlation detected; no temporal precedence or transmission mechanism established.
- **`LEVEL_2_TEMPORAL_ASSOCIATION`**: Cause verified to strictly precede the effect in time ($\Delta t > 0$), but intermediate mechanisms remain unverified.
- **`LEVEL_3_MECHANISTIC_SUPPORT`**: At least one intermediate physical or administrative transmission step verified; plausible domain mechanism confirmed.
- **`LEVEL_4_STRONG_CAUSAL_SUPPORT`**: Multi-step mechanism verified across $\ge 2$ independent evidence sources, temporal sequence confirmed, no unresolved common confounders, counterfactual proxy supports causality.
- **`LEVEL_5_INTERVENTION_SUPPORTED`**: Targeted empirical intervention on the identified cause verified to alter or resolve the observed effect in real-world project history.

### 3. First-Class Causal Objects (`paimana_agent.causal`)
1. **`CausalClaim`**: Represents an explicit causal proposition with source, target, support score ($[0, 1]$), confidence bracket, epistemic status (`SUPPORTED`, `PLAUSIBLE`, `WEAKENED`, `REJECTED`), falsification notes, and unresolved confounders.
2. **`CausalMechanism`**: Represents the concrete multi-step transmission chain linking cause to effect through explicit intermediate nodes ($A \to X \to Y \to B$).
3. **`TemporalRelation`**: Encapsulates timestamp precedence ($\Delta t$), sequence monotonicity, and temporal consistency.
4. **`Confounder`**: Identifies common external causes ($Z \to X$ and $Z \to Y$) that induce spurious correlations, along with evidence required to resolve them.
5. **`CounterfactualProxy`**: Natural comparison evaluations (“What would have occurred without this cause?”) contrasting unaffected workfronts or peer packages.
6. **`CausalGraph`**: Directed acyclic causal graph containing `CausalGraphNode` and `CausalGraphEdge` objects with weights, mechanism IDs, and empirical statuses.

### 4. Canonical Infrastructure Mechanism Ontology (`CausalOntology`)
The ontology library codifies 5 canonical infrastructure mechanism templates with explicit predicted and falsifying observations:
- **`M_CONTRACTOR_EXECUTION`**: Cashflow/resource distress $\to$ Plant/labor demobilization $\to$ Low burn rate on unencumbered fronts $\to$ Milestone slippage.
  - *Falsifier*: Site muster rolls and equipment telemetry verify full or surplus plant mobilization.
- **`M_APPROVAL_DEPENDENCY`**: Statutory proposal pending $\to$ Clearance turnaround SLA exceeded $\to$ Workfront unavailable $\to$ Physical execution stalled.
  - *Falsifier*: Statutory authority issues formal clearance or handover notice predating the delay.
- **`M_FUNDING_CONSTRAINT`**: Letter of Credit / Escrow depleted $\to$ Contractor running bills unpaid $>60$ days $\to$ Vendor credit lines frozen $\to$ Site work halts.
  - *Falsifier*: Financial escrow audit confirms uninterrupted on-time invoice settlements.
- **`M_LAND_ROW_DEFICIT`**: Land acquisition litigation $\to$ Linear corridor unencumbered length $<70\%$ $\to$ Contractor cannot achieve continuous paving $\to$ Cumulative schedule stall.
  - *Falsifier*: District revenue records confirm complete unencumbered physical possession granted at contract signing.
- **`M_DESIGN_VARIATION`**: Site geological surprise $\to$ Structural design change order submitted $\to$ Technical committee approval pending $\to$ Foundation works suspended.
  - *Falsifier*: As-built drawings and geological baseline confirm standard conditions with no variation claims.

### 5. Multi-Step Intermediate Chain Verification (`CausalEngine`)
The engine rejects single-hop leaps. When evaluating a claim, each intermediate step in the transmission chain must be evaluated against ground-truth evidence:
$$\text{Mechanism Support} = \frac{\sum_{i=1}^N w_i \cdot \text{verified}_i}{\sum_{i=1}^N w_i}$$
Missing intermediate links penalize mechanism support and generate explicit evidence gaps.

### 6. Temporal Precedence & Inversion Detection (`TemporalReasoner`)
A cause must strictly precede its effect:
- **Temporal Inversion**: If an alleged cause occurred *after* the effect had already commenced, causality is mathematically impossible. The claim is downgraded to `LEVEL_1_ASSOCIATION`, marked `REJECTED`, and penalized.
- **Precedence Monotonicity**: Verifies that cause severity growth preceded or coincided with effect escalation.

### 7. Common Cause Confounder Analysis (`ConfounderDetector`)
Identifies hidden common drivers that simultaneously influence both cause and effect (e.g., systemic state treasury cashflow freeze delaying statutory deposit payments while simultaneously starving contractor working capital).
- Active unresolved confounders apply a penalty ($P_{\text{conf}} \ge 0.15$) to the causal composite score.
- Generates targeted evidence needs to isolate or rule out the confounder.

### 8. Counterfactual Comparison Proxies (`CounterfactualAnalyzer`)
Because controlled A/B testing is impossible on mega infrastructure projects, the system utilizes natural comparison groups:
- **Spatial / Workfront Comparison**: Compares encumbered versus unencumbered packages under the same contractor.
- **Contractor Comparison**: Compares the same contractor on other projects with timely funding to determine whether distress is contractor-intrinsic or project-specific.

### 9. ML/SHAP Attribution Safety Boundary
Machine learning feature importances and SHAP values are strictly classified as:
$$\text{evidence\_type} = \text{"MODEL\_DERIVED"}$$
The system enforces a hard architectural boundary: **SHAP values reflect statistical permutations inside the ML model, never empirical causal proof in the physical world.** A claim substantiated solely by SHAP feature attribution is capped at `LEVEL_1_ASSOCIATION` and can never reach Level 4 or 5 without physical corroboration.

### 10. Calibrated Recommendation Boundary (Gate 6)
Recommendation aggressiveness is strictly calibrated against the verified causal claim level:
- Under **Level 0–2 (`OBSERVATION`, `ASSOCIATION`, `TEMPORAL_ASSOCIATION`)**: Punitive contractual measures (e.g. liquidated damages, contract termination, show-cause notices) are strictly **VETOED** by Gate 6 in `RecommendationValidator`. The system permits only non-punitive, diagnostic, or collaborative actions (e.g., joint reconciliation audits, milestone reviews).
- **Level 3 (`MECHANISTIC_SUPPORT`)**: Permits moderate corrective actions (e.g., catch-up schedules, escrow re-allocation).
- **Level 4–5 (`STRONG_CAUSAL_SUPPORT`, `INTERVENTION_SUPPORTED`)**: Permits full escalations, including punitive contractual enforcement and ministerial taskforces.

### 11. Auditable Causal Decision Trace (`CausalDecisionTrace`)
Every investigation emits a structured causal trace logging:
- Evaluated competing explanations and why each was accepted, retained, or rejected.
- Mechanism link-by-link verification breakdown.
- Confounders detected, penalties applied, and resolution status.
- Temporal sequence analysis results.
- Retained plausible alternatives (preserving uncertainty under ambiguous data).


## 11. Multidimensional Investigation Convergence & Stopping Management

### 1. Paradigm Shift: Convergence vs. Resource Control
In traditional agentic systems, stopping conditions are commonly implemented as simple loop boundaries:
$$\text{iteration} \ge 8 \implies \text{STOP}$$
This conflates **resource safety boundaries** with **investigation convergence**. An agent that halts simply because an arbitrary counter reached 8 has not concluded an investigation; conversely, an agent that continues executing simply because the iteration count is under 8 wastes computational budget and external tool calls when the core uncertainty has already been resolved.

PAIMANA V3 separates these concerns through an explicit, two-stage convergence engine:
1. **Stage 1 (Hard Resource Limits)**: Tool invocation ceilings (`max_tool_calls`), total latency deadlines, and run-away cost guards act strictly as safety limits. When reached, they yield `ConvergenceStatus.BUDGET_EXHAUSTED` with reason `TOOL_LIMIT_REACHED`.
2. **Stage 2 (Multidimensional Convergence Evaluation)**: The agent continuously asks:
   > *"Has additional investigation stopped producing enough useful new information to justify another step?"*

```text
                               +----------------------------+
                               |     Investigation Step     |
                               +----------------------------+
                                             |
                                             v
                      +---------------------------------------------+
                      | Stage 1: Resource & Safety Boundary Check   |
                      +---------------------------------------------+
                                       /           \
                                      /             \
                             Exhausted               Budget Available
                                   /                   \
                                  v                     v
                 +-----------------------+   +------------------------------------+
                 |   BUDGET_EXHAUSTED    |   | Stage 2: Multidimensional Eval     |
                 | (TOOL_LIMIT_REACHED)  |   +------------------------------------+
                 +-----------------------+              /          \
                                                       /            \
                                              Converged              Active Gaps / Needs
                                                     /                \
                                                    v                  v
                               +-------------------------+    +------------------------------------+
                               |       CONVERGED         |    | Information-Theoretic Gate         |
                               |  (SUFFICIENT_EVIDENCE)  |    +------------------------------------+
                               +-------------------------+              /          \
                                                                       /            \
                                                   EV(T) >= Threshold                EV(T) < Threshold
                                                                     /                \
                                                                    v                  v
                                                        +-------------------+   +------------------------------------+
                                                        |    PROGRESSING    |   | NO_HIGH_VALUE_EVIDENCE_AVAILABLE   |
                                                        |  (Next Best Tool) |   | (Diminishing / Saturated / None)   |
                                                        +-------------------+   +------------------------------------+
```

### 2. Distinct Terminal States
The convergence engine classifies investigation outcomes into 5 mutually exclusive, semantically precise terminal states:
- **`CONVERGED`**: All evidentiary, separation, stability, contradiction, causal, and decision readiness criteria are met simultaneously.
- **`INSUFFICIENT_EVIDENCE`**: Critical evidence needs remain unfulfilled, but the tool registry contains no eligible tools capable of acquiring the necessary data.
- **`NO_HIGH_VALUE_EVIDENCE_AVAILABLE`**: Evidence gaps remain, but all remaining candidate tools yield an expected information gain or net utility below the worthwhile threshold ($EV(T) < \text{threshold}$), or evidence saturation / diminishing returns has been reached.
- **`CONTRADICTORY`**: High or critical contradictions remain unresolved across authoritative data sources, and no available diagnostic tool can distinguish between them.
- **`BUDGET_EXHAUSTED`**: The hard maximum tool execution limit or latency ceiling was reached before convergence.

### 3. The 6 Evaluation Dimensions
Investigation maturity is evaluated continuously across six orthogonal dimensions:
1. **Evidence Coverage (`EvidenceCoverageEvaluator`)**: Measures resolution of open `EvidenceNeed`s, weighted by need priority. Critically, multiple tools querying the exact same source snapshot do not satisfy distinct needs, preventing pseudo-completeness.
2. **Hypothesis Separation (`HypothesisSeparationEvaluator`)**: Evaluates the statistical margin between the leading hypothesis score and runner-up:
   $$\Delta_{\text{sep}} = S_{\text{lead}} - S_{\text{runner-up}}$$
   Classifies the state as `CLEARLY_SEPARATED` ($\ge 0.20$), `PARTIALLY_SEPARATED`, or `HIGHLY_COMPETITIVE` ($< 0.10$).
3. **Hypothesis Stability (`HypothesisStabilityEvaluator`)**: Evaluates the stability of hypothesis distributions over consecutive steps:
   $$\Delta_{\text{stab}} = 1.0 - \frac{1}{|H|} \sum_{h \in H} |S_{h, t} - S_{h, t-1}|$$
   Demands $\ge 2$ consecutive steps of stable rankings without leader flipping.
4. **Contradiction Resolution (`ContradictionResolutionEvaluator`)**: Severity-weighted evaluation (`CRITICAL: 4.0`, `HIGH: 3.0`, `MEDIUM: 2.0`, `LOW: 1.0`). Any unresolved `CRITICAL` or `HIGH` contradiction acts as an absolute blocker to `CONVERGED`. Minor `LOW` discrepancies (e.g., minor portal submission latency) do not block convergence when underlying evidence is solid.
5. **Causal Support (`CausalConvergenceEvaluator`)**: Maps verified causal reasoning levels (Levels 0 through 5) into the composite score, requiring minimum Level 3 (`MECHANISTIC_SUPPORT`) for standard severity and Level 4+ for high/critical severity.
6. **Decision Readiness (`DecisionReadinessEvaluator`)**: Verifies operational prerequisites for downstream recommendation synthesis: causal understanding, identified responsible authorities, action feasibility, and financial cost awareness.

### 4. Dynamic Information Trajectory & Detection Subsystems
To prevent wasteful execution and detect unproductive loops, the engine deploys three specialized detectors:
- **Diminishing Returns Detector (`DiminishingReturnsDetector`)**: Analyzes a sliding window ($W=3$) of realized information gains:
  $$\Delta_{\text{gain}, t} = \frac{1}{|H|} \sum_{h \in H} |S_{h, t} - S_{h, t-1}|$$
  Detects when information gain has flattened below $\tau = 0.03$.
- **Evidence Saturation Detector (`EvidenceSaturationDetector`)**: Detects when consecutive tools query identical data lineages without altering confidence scores or introducing new source independence groups.
- **Hypothesis Oscillation Detector (`HypothesisOscillationDetector`)**: Detects unstable oscillations where leading hypothesis identities alternate under narrow margins, preventing infinite cycling between equally plausible explanations.

### 5. Hysteresis & Reopening Engine (`ReopenPolicyManager`)
Once an investigation reaches a terminal state, it is sealed. Minor data changes do not trigger repetitive re-investigations. Reopening is governed by strict, asymmetric hysteresis:
- **Spike in Material Risk**: Risk score jumps by $\ge 15$ points since the previous investigation.
- **New Authoritative Evidence**: An evidence item with $\text{authority} \ge 0.85$ and high materiality arrives.
- **Causal Contradiction**: New physical ground truth refutes the previously accepted root-cause mechanism.
- **Intervention Failure**: An empirical outcome indicates that an enacted recovery intervention failed.

### 6. Auditability: Termination Trace & Convergence Dashboard
Every concluded investigation records a full `TerminationRecord` embedded in `InvestigationState`:
- `status`: One of the 5 terminal states.
- `termination_reason`: Standardized identifier (`SUFFICIENT_EVIDENCE`, `NO_HIGH_VALUE_TOOL_REMAINING`, `CONTRADICTORY_EVIDENCE`, `INSUFFICIENT_EVIDENCE`, `TOOL_LIMIT_REACHED`).
- `dimension_scores`: Multi-dimensional metrics breakdown (`coverage`, `separation`, `stability`, `contradictions`, `causal`, `readiness`).
- `expected_gain_at_stop`: The $EV(T)$ of the best remaining tool when the agent terminated.
- `convergence_dashboard`: Renderable tabular summary of the 6 dimensions against policy thresholds.


## 12. Resource Governance, Investigation Budget & Portfolio Concurrency Architecture

### 1. Architectural Distinction: Scientific Value vs. Operational Resource Bounds
PAIMANA V3 enforces an explicit separation between scientific evaluation and resource governance:
- **Convergence Engine**: Decides whether another investigation step is *scientifically worthwhile* ($EV(T) \ge \tau$).
- **Dynamic Tool Selector**: Determines *what is the best next step* to address open evidentiary gaps.
- **Budget Governance Engine**: Decides whether the system is *permitted to spend the required operational resources* (time, tool calls, LLM tokens, external API hits, monetary cost, concurrency slots) to execute that step.

```text
                                  EVENT
                                    │
                                    ▼
                         Investigation Manager
                                    │
                         Allocate Initial Budget
                                    │
                                    ▼
                           Investigation State
                                    │
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
            Convergence       Tool Selection     Budget Manager
              Engine              Engine               │
                 │                  │                  │
                 │           Best next action          │
                 │                  │                  │
                 └──────────────────┼──────────────────┘
                                    ▼
                             Resource Check
                                    │
                      ┌─────────────┴─────────────┐
                      ▼                           ▼
                   APPROVED                    BLOCKED
                      │                           │
                      ▼                     degrade / defer /
                  Reserve                      expand / stop
                      │
                      ▼
                   Execute
                      │
                      ▼
                Record actual use
                      │
                      ▼
               Update investigation
                      │
                      ▼
                Convergence check
                      │
                ┌─────┴─────┐
                ▼           ▼
             Continue     Terminate
                │           │
                │     ┌─────┴─────────────────────┐
                │     ▼       ▼        ▼           ▼
                │  CONVERGED  NO     INSUFFICIENT  BUDGET
                │             HIGH       EVIDENCE   EXHAUSTED
                │            VALUE
                └─────────────┘
```

### 2. First-Class Multi-Resource Budget (`InvestigationBudget`)
The system manages an auditable, multi-dimensional ledger (`ResourceConsumption` and `ResourceLedger`) rather than an arbitrary loop counter:
- **Iterations**: Prevents runaway supervisor loops ($N_{\text{iter}} \le 8$).
- **Tool Invocations**: Bounds downstream tool invocations ($N_{\text{tools}} \le 5\text{--}12$).
- **LLM Calls & Tokens**: Enforces prompt and completion ceilings ($C_{\text{LLM}} \le 4\text{--}8$, $T_{\text{tokens}} \le 8,000\text{--}20,000$).
- **External API Calls**: Protects rate limits on third-party ministerial systems ($C_{\text{API}} \le 2\text{--}10$).
- **Execution & Wall-Clock Latency**: Hierarchical timeouts bounding tool calls ($t_{\text{tool}} \le t_{\text{parent}}$).
- **Monetary Cost**: Explicit operational cost ceilings in USD/INR ($C_{\text{est}} \le \$0.35\text{--}\$2.50$).
- **Concurrency Slots**: Prevents simultaneous tool execution contention.

### 3. Risk-Calibrated Budget Policy (`BudgetPolicy`)
Resource envelopes are calibrated dynamically to anomaly severity:
- **`LOW`**: 3 iterations, 4 tool calls, 2 LLM calls, 4,000 tokens, 2 external calls, 20s latency, \$0.35 cost, 10% reserve. Shallow triage.
- **`MEDIUM`**: 6 iterations, 6 tool calls, 4 LLM calls, 8,000 tokens, 4 external calls, 40s latency, \$0.80 cost, 15% reserve. Standard investigation.
- **`HIGH`**: 8 iterations, 8 tool calls, 6 LLM calls, 14,000 tokens, 6 external calls, 60s latency, \$1.50 cost, 15% reserve. Expanded investigation.
- **`CRITICAL`**: 10 iterations, 12 tool calls, 8 LLM calls, 20,000 tokens, 10 external calls, 90s latency, \$2.50 cost, 20% reserve. Full forensic investigation with mandatory independent corroboration.

### 4. Pre-Execution Budget Reservation (`ReservationManager`)
Before any tool execution, the supervisor places a formal hold (`BudgetReservation`). If the estimated resource demand exceeds available budget, the reservation is rejected immediately, preventing concurrent overdrafts. Upon completion, actual latency, cost, and tokens are settled against the ledger, recording variance ($\Delta_{\text{actual} - \text{estimated}}$).

### 5. Cost-Aware Tool Utility (`ResourceEstimator`)
Dynamic tool selection integrates operational cost and resource pressure alongside information gain:
$$\text{resource\_adjusted\_value} = \frac{\text{expected\_information\_gain} \times \text{decision\_relevance} \times \text{evidence\_quality}}{\text{estimated\_cost} + \text{latency\_penalty} + \text{resource\_pressure}}$$
Where normalized resource pressure $P_{\text{res}} = \max(r_{\text{tools}}, r_{\text{time}}, r_{\text{cost}}, r_{\text{tokens}}) \in [0.0, 1.0]$. A tool with slightly lower theoretical information gain may be selected if it is substantially cheaper and faster.

### 6. Emergency Reserve Protection
The budget reserves 15–20% of its resource envelope as an **Emergency Reserve**. Routine exploratory investigation is blocked from spending this reserve. It is unlocked exclusively when material high/critical contradictions appear or when final decisive verification is required.

### 7. Graceful Degradation & Confidence Coupling (`GracefulDegradationManager`)
As resource pressure climbs, the agent degrades gracefully across four operational tiers:
- **Level 1 (Normal, $P \le 0.50$)**: Full LLM planning, unrestricted tool registry, deep precedent search.
- **Level 2 (Cost-Aware, $0.50 < P \le 0.75$)**: Top-value tools only, standard LLM planning.
- **Level 3 (Constrained, $0.75 < P \le 0.90$)**: Deterministic gap planner, local evidence sources, reduced memory retrieval.
- **Level 4 (Safe Termination, $P > 0.90$ or Exhausted)**: Safe termination with `BUDGET_EXHAUSTED`.
**Hard Epistemic Guarantee**: Resource constraints explicitly reduce reported evidence completeness and qualify confidence (e.g. downgrading to `PRELIMINARY_QUALIFIED` with audit caveats). Resource constraints never silently produce unearned high confidence.

### 8. Auditable Budget Escalation (`BudgetEscalator`)
If an investigation encounters critical unresolved uncertainty but has exhausted its routine allowance, it may submit a formal `BudgetExpansionRequest`. Expansion is approved only if:
1. Event severity is `HIGH` or `CRITICAL`.
2. Current uncertainty is high ($\ge 0.35$) or an active material contradiction exists.
3. Expected information gain is decisive ($EV \ge 0.10$).
Trivial requests or low-severity investigations are denied, terminating strictly as `BUDGET_EXHAUSTED`.

### 9. Portfolio Concurrency & Priority Scheduling
- **Admission Control (`PortfolioAdmissionController`)**: Limits simultaneous active investigations across the national portfolio, admitting immediately if slots exist or placing requests into a priority queue.
- **Priority Scheduling (`PriorityScheduler`)**: Queued investigations are scheduled descending by composite priority score ($S_{\text{priority}} = 0.40 \cdot \text{sev} + 0.30 \cdot \text{urgency} + 0.15 \cdot \text{impact} + 0.15 \cdot \text{criticality}$). Critical corridor emergencies preempt routine scans.
- **Cascading Cancellation (`CancellationManager`)**: Superseded or preempted investigations abort running operations and release all reserved resource holds immediately.
- **Human Attention Budgeting (`HumanReviewCapacity`)**: Tracks human review capacity to prevent flooding ministerial approvers with routine notices, routing high-impact and punitive actions to priority queues.


---

## 13. Tool Reliability, Fault-Tolerant Evidence Acquisition & Recovery Architecture

```
                                      +--------------------------------+
                                      |   Dynamic Tool Selector        |
                                      |   Reliability-Weighted Utility |
                                      +----------------+---------------+
                                                       |
                                            [Preflight Health Check]
                                                       |
                                                       v
                                      +--------------------------------+
                                      |     Circuit Breaker Check      |
                                      |  (CLOSED / OPEN / HALF_OPEN)   |
                                      +----------------+---------------+
                                                       |
                                         +-------------+-------------+
                                         |                           |
                                      [CLOSED]                     [OPEN]
                                         |                           |
                                         v                           v
                      +-----------------------------------+  +---------------+
                      | Specialist Tool Execution Attempt |  | FallbackGraph |
                      +-----------------+-----------------+  | Substitution  |
                                        |                    +-------+-------+
                         +--------------+--------------+             |
                         |                             |             |
                     [Success]                      [Error]          |
                         |                             |             |
                         v                             v             |
             +-----------------------+     +-----------------------+ |
             | Result Quality Check  |     | Failure Classifier    | |
             | False-Success Check   |     | (Taxonomy + Retryable)| |
             +-----------+-----------+     +-----------+-----------+ |
                         |                             |             |
                    +----+----+               +--------+--------+    |
                    |         |               |                 |    |
                 [Valid]  [Invalid]      [Retryable]     [Non-Retry] |
                    |         |               |                 |    |
                    |         +--------+      v                 |    |
                    |                  |  Bounded Retry         |    |
                    |                  |  Backoff + Jitter      |    |
                    |                  |      |                 |    |
                    |                  |   [Exhausted]          |    |
                    |                  |      +--------+--------+    |
                    |                  |               |             |
                    v                  +-------------->v             |
           +-----------------+                 +---------------+     |
           | Evidence Graph  |                 | FallbackGraph |<----+
           | State Preserved |                 | Substitution  |
           +-----------------+                 +-------+-------+
                                                       |
                                                       v
                                            [Discounted Authority]
                                            [Shared Lineage Mark]
```

### 1. Foundational Epistemic Contract
> **A tool invocation can succeed technically while still producing unusable evidence, and a tool invocation can fail technically without meaning the investigation has failed.**

Operational reliability is treated as a first-class decision signal rather than an ad-hoc exception handler. Tool reliability is strictly separated across two orthogonal dimensions:
1. **Execution Reliability ($\mathcal{R}_{\text{exec}} \in [0.0, 1.0]$)**: Uptime, latency predictability, timeout avoidance, and technical HTTP/RPC completion rate.
2. **Evidence Reliability ($\mathcal{R}_{\text{ev}} \in [0.0, 1.0]$)**: Data completeness, recency/freshness, source authority, and absence of misattributed or false-positive records.

### 2. Standardized ToolResult Contract & Failure Taxonomy
Every tool execution yields a standardized `ToolResult` governed by a strict categorical status taxonomy:
- `SUCCESS`: High quality, complete evidence with verified domain invariants.
- `PARTIAL_SUCCESS`: Execution succeeded but only a subset of fields/records were available (`completeness_score < 1.0`).
- `EMPTY_RESULT`: Query was technically valid but returned zero matching records (`empty_reason` specified, distinct from "zero risk").
- `STALE_RESULT`: Data exceeds acceptable staleness half-life (`freshness_score` decayed).
- `TIMEOUT`: Execution exceeded hard deadline (retryable).
- `AUTH_FAILURE` / `PERMISSION_DENIED`: Credential or authorization refusal (strictly **non-retryable**).
- `RATE_LIMITED`: Upstream API throttled (retryable with exponential backoff).
- `SOURCE_UNAVAILABLE`: Upstream database or external service offline (retryable once, then fallback).
- `SCHEMA_ERROR`: Payload failed structural parsing/deserialization (quarantined, non-retryable).
- `VALIDATION_ERROR`: Domain invariants violated (e.g. false success with mismatched project ID; quarantined).
- `DEPENDENCY_FAILURE`: Prerequisite connection, database, or model missing.
- `CIRCUIT_OPEN`: Invocations temporarily blocked due to repeated upstream failures.
- `INTERNAL_ERROR`: Unhandled Python runtime exception.

### 3. Circuit Breaker Finite State Machine (`CircuitBreaker`)
Prevents catastrophic cascading failures and protects external services from hammering:
- **`CLOSED`**: Normal operation. Invocations pass through. Consecutive failures increment error counters.
- **`OPEN`**: Tripped when consecutive failures $\ge \tau_{\text{failure}}$ (default 3). Calls are rejected immediately without network dispatch (`can_execute() == False`), directly routing to fallback sources.
- **`HALF_OPEN`**: Entered when cooldown window (default 30s) elapses. A single probe invocation is permitted. If the probe succeeds, the circuit closes (`CLOSED`); if it fails, the circuit re-opens (`OPEN`) immediately for another cooldown period.

### 4. Reliability-Weighted Dynamic Tool Utility
Tool candidate ranking incorporates execution reliability:
$$\text{tool\_utility} = \frac{\text{expected\_information\_gain} \times \text{discrimination\_power} \times \text{source\_authority} \times \mathcal{R}_{\text{exec}}}{\text{resource\_cost} + \text{failure\_penalty} + \text{latency\_penalty}}$$
Where $\mathcal{R}_{\text{exec}}$ is drawn from the tool's persistent operational profile. A tool with high theoretical information gain but degraded reliability ($\mathcal{R}_{\text{exec}} \le 0.30$) is systematically down-ranked below a reliable, moderate-gain alternative.

### 5. Source Fallback Graphs & Substitution Lineage (`FallbackGraph`)
When primary specialist tools fail or their circuit breakers trip, the agent navigates a directed fallback graph:
- `approval_timeline` $\to$ `project_history` $\to$ `milestone_audit`
- `gis_satellite_validation` $\to$ `field_muster_rolls` $\to$ `milestone_audit`
- `financial_velocity` $\to$ `milestone_audit` $\to$ `project_history`
- `peer_intelligence` $\to$ `memory_retrieval`
**Anti-Hallucination Guarantees**:
- **Authority Discount**: Substituted evidence records apply an authority discount ratio $\alpha = \min(1.0, \text{auth}_{\text{fallback}} / \text{auth}_{\text{primary}})$.
- **Lineage Preservation**: If a fallback tool accesses the same underlying database snapshot as another tool, it is assigned the same `independence_group_id` (`SUB_<primary>_<snapshot>`). Fallbacks **never masquerade as independent corroboration**.

### 6. False-Success Detection & Quarantining (`ToolResultValidator`)
Technically successful tool runs (HTTP 200 / return dictionary) are rigorously scrutinized before evidence graph ingestion:
1. **Empty Payload Check**: Returns marked `EMPTY_RESULT` with `useful_evidence = False`.
2. **Project Code Misattribution**: If returned payload contains an unexpected project ID, status is set to `VALIDATION_ERROR` and quarantined.
3. **All-Null Payload**: If all primary metrics are `None`, the result is rejected as invalid.
4. **Staleness Gating**: Invocations exceeding the age threshold receive discounted freshness scores and explicit warning flags.

### 7. Recovery Budget Accounting & State Preservation
- **Recovery Ledger Charging**: Retries and fallback invocations are recorded in the `InvestigationBudget` ledger (`tool_calls_used` and latency counters incremented).
- **State Preservation Guarantee**: A tool failure operates strictly at the individual step level. It **never wipes, resets, or corrupts** previously established hypotheses, existing evidence items, or convergence detector states.
- **Useful Evidence Rate Metric**: Persistent profiles track $\text{useful\_evidence\_rate} = \frac{\text{usable evidence results}}{\text{total tool calls}}$, penalizing false successes and unusable outputs.

---

## 14. Deep Integration with Peer Intelligence Agentic System

```text
                             +----------------------------------------+
                             |         Supervisor Agent Planner       |
                             +-------------------+--------------------+
                                                 |
                                     (Dynamic Tool Dispatch)
                                                 v
                             +----------------------------------------+
                             |         PAIMANA ToolRegistry           |
                             |  (Registers 12 Peer Specialist Tools)  |
                             +-------------------+--------------------+
                                                 |
                         +-----------------------+-----------------------+
                         |                       |                       |
                         v                       v                       v
               +-------------------+   +-------------------+   +--------------------+
               |  peer_discovery   |   |  peer_benchmark   |   |   peer_deviation   |
               |  peer_trajectory  |   |   peer_outlier    |   | peer_cohort_health |
               | cohort_intellig.  |   | statistical_bench |   | detect_peer_anomal |
               | trajectory_intel  |   |  domain_context   |   |  peer_intelligence|
               +---------+---------+   +---------+---------+   +---------+----------+
                         |                       |                       |
                         +-----------------------+-----------------------+
                                                 |
                                     [Dynamic Store Resolver]
                                                 |
                                                 v
                             +----------------------------------------+
                             |       SQLiteProjectRepository          |
                             |      (Adapts Store / monitoring.db)    |
                             +-------------------+--------------------+
                                                 |
                                                 v
                             +----------------------------------------+
                             |        PeerIntelligenceService         |
                             |  - Cohort Engine   - Benchmark Engine  |
                             |  - Outlier Engine  - Trajectory Engine |
                             |  - Domain Context  - Statistical Engine|
                             +-------------------+--------------------+
                                                 |
                                     (Standardized ToolResult)
                                                 v
                             +----------------------------------------+
                             |      Evidence & State Propagation      |
                             |  - EvidenceNormalizer (PEER_COHORT)    |
                             |  - InvestigationState (Inferences)     |
                             |  - Decision Trace & Evidence Graph     |
                             |  - Legacy Backward Compatibility Data  |
                             +----------------------------------------+
```

### 1. Peer Intelligence Specialist Tool Suite
The agentic layer dynamically registers and exposes the full suite of 12 peer capabilities conforming to PAIMANA's MCP-compatible `ToolDefinition` specification:
1. **`peer_discovery`**: Multi-dimensional comparable peer identification & filtering with transparent similarity explanations.
2. **`peer_benchmark`**: Robust statistical distributions (median, IQR, p25/p75) across peer cohorts.
3. **`peer_deviation`**: Target project vs peer median divergence calculations with directional interpretations.
4. **`peer_trajectory`**: Chronological velocity and monthly change rate comparisons across historical snapshots.
5. **`peer_outlier`**: Peer-relative anomaly detection cleanly separating absolute operational risk from sector context.
6. **`peer_cohort_health`**: Cohort size, similarity strength, and data completeness evaluations.
7. **`peer_intelligence`**: Master drop-in upgraded tool providing comprehensive discovery, benchmarks, deviations, trajectory, outlier, and domain context.
8. **`cohort_intelligence`**: Evaluates multidimensional cohort quality, distribution shape, heterogeneity, and refinement recommendations.
9. **`statistical_benchmark`**: Robust reference profiles, bootstrap confidence intervals, and empirical percentiles.
10. **`detect_peer_anomalies`**: Multi-method contextual, multivariate, and temporal anomaly detection.
11. **`analyze_trajectory_intelligence`**: Rolling velocity, acceleration, stagnation, recovery, and regime-shift analysis.
12. **`analyze_domain_context`**: Domain-specific infrastructure operational realities, statutory clearances, and terrain bottlenecks.

### 2. Decoupled Storage Adapter (`SQLiteProjectRepository`)
The peer system adapts directly to PAIMANA's persistent `Store` via `SQLiteProjectRepository`:
- Directly queries live project snapshots (`snapshots` table) and historical audit records.
- Seamlessly falls back to `InMemoryProjectRepository` when running under in-memory test fixtures.
- Dynamic tool execution wrappers (`_resolve_service`) inspect invocation kwargs and dynamically attach to the active `Store` instance, guaranteeing zero cross-talk between isolated project databases.

### 3. Epistemic Evidence Ingestion & Independence Tracking
Tool outputs are normalized by `EvidenceNormalizer` into canonical `Evidence` records:
- **Authority Score**: Pre-calibrated at $0.85$ (empirical comparative database).
- **Lineage Partitioning**: Assigned explicit independence partition keys (`PEER_COHORT_<sector>`), preventing peer benchmarks from being conflated with project self-reported metrics.
- **Evidence Graph Linkage**: Relational edges (`tool:peer_* -> CONTEXTUALIZES -> hypothesis:chronic_schedule_delay`, weight $0.60$) are dynamically recorded in the investigation graph.

### 4. Rich Inferences & Decision Trace Propagation
When peer tools execute, `SupervisorAgent._process_observation`:
- Extracts natural language inferences (`state.add_inference`) derived from peer cohorts and national baselines.
- Appends structured records to `decision_trace` with metric values, thresholds, and cohort baselines.
- Resolves open evidence gaps (`state.resolve_evidence_gap("Benchmark against sector and agency peer baselines")`).

### 5. Backward Compatibility Guarantee
The master `peer_intelligence` tool automatically enriches its return payload with all legacy fields:
- `sector`, `stage_bracket`, `cost_band`, `n_peers_seen`, `n_comparable`, `same_agency_count`, `comparable_with_cost_revision`, `comparable_with_slippage`, `sector_national_baseline`, `note`, and `summary`.
- `NormalizedStatus` ensures transparent string equality across both `PARTIAL` and `PARTIAL_SUCCESS`.
- All 133 tests in `peer/tests` and all 111 behavioral tests in `paimana_agent` execute with 100% pass rates.








