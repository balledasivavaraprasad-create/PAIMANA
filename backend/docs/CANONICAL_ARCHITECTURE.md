# Canonical Agentic Architecture — PAIMANA V3 / V3+

## Phase 0: Canonical Architecture & System Freezing

This document defines the single authoritative architecture for the PAIMANA Infrastructure Project Monitoring and Agentic Investigation System. It unifies all advanced subsystems (dynamic tool selection, causal reasoning, convergence engine, resource governance, institutional precedent memory, and peer intelligence) into a coherent, linear, and auditable pipeline.

---

## 1. The Authoritative 14-Stage Lifecycle

Every project evaluation adheres strictly to the following end-to-end operational path:

```text
Monitoring
   ↓
Snapshot
   ↓
Event
   ↓
Investigation
   ↓
Evidence
   ↓
Hypothesis
   ↓
Causal reasoning
   ↓
Tool selection
   ↓
Convergence
   ↓
Recommendation
   ↓
Approval
   ↓
Execution
   ↓
Outcome
   ↓
Memory
```

### Stage Definitions

1. **Monitoring** (`MonitoringAgent.on_project_saved` / `run_scheduled_scan`):
   Continuous surveillance of infrastructure projects across additions, edits, and automated scheduled scans.
2. **Snapshot** (`Store.save_snapshot`, `compute_snapshot_hash`):
   Fast-path material change detection via cryptographic hashing. Unchanged records bypass heavy re-computation.
3. **Event** (`events.detect_events`, `worth_investigating`):
   Taxonomy-driven anomaly and escalation event detection (e.g., `COST_PROGRESS_MISMATCH`, `MILESTONE_DELAYED`, `RISK_ACCELERATING`).
4. **Investigation** (`SupervisorAgent.run_investigation`):
   Stateful supervisor instantiated with risk-calibrated budget policy and investigation accumulator.
5. **Evidence** (`EvidenceNormalizer`, `Evidence`):
   Ground-truth metrics (CUF ledger, MPR, milestone schedules) and tool outputs ingested into structured `Evidence` items with cryptographic source lineage and independence groups.
6. **Hypothesis** (`HypothesisManager`, `Hypothesis`):
   Seeding of 4 competing causal explanations (`front_loaded_billing`, `chronic_schedule_delay`, `regulatory_land_clearance`, `reporting_discrepancy`) with dynamic branching and Bayesian posterior updating.
7. **Causal Reasoning** (`CausalEngine`, `CausalClaim`):
   Disciplined verification of causal mechanisms, temporal precedence ($T_{\text{cause}} < T_{\text{effect}}$), and confounder detection, establishing explicit Causal Claim Levels (Level 0 Observation to Level 4 Counterfactual Proof).
8. **Tool Selection** (`DynamicInformationSeekingSelector`, `ToolRegistry`):
   Information-seeking tool evaluation ranking candidate tools by expected uncertainty reduction, source authority, reliability profile, and affordability under resource budget constraints.
9. **Convergence** (`ConvergenceEngine`, `ConvergenceDetector`):
   Multi-dimensional stopping evaluation checking evidence sufficiency, hypothesis separation margin, contradiction resolution, and marginal utility diminishing returns.
10. **Recommendation** (`CandidateGenerator`, `CandidateValidator`, `CandidateScorer`, `pareto_filter`, `RecommendationSelector`):
    Multi-criteria candidate generation across 5 archetypes, hard safety gating, Pareto dominance filtering, and multi-dimensional ranking.
11. **Approval** (`report["status"] = "pending_approval"`, `responsible_stakeholder`):
    Statutory authority gating ensuring high-consequence interventions are routed to appropriate executive authorities (e.g., State Chief Secretary, Apex Committee).
12. **Execution** (`record_intervention`):
    Execution of approved intervention tracked in operational store.
13. **Outcome** (`record_outcome`, `OutcomeEvaluator`):
    Empirical observation of post-intervention trajectory (risk score delta, schedule recovery, resolution).
14. **Memory** (`MemoryConsolidator`, `PrecedentMemoryStore`, `Precedent`):
    Closed-loop consolidation into persistent precedent memory with transferability scoring and failure warnings.

---

## 2. Hard Rule: Single Canonical Object Registry

To prevent competing models or conflicting representations, exactly **ONE** canonical class definition exists for each core concept:

| Concept | Canonical Class | Authoritative Module Path | Role |
| :--- | :--- | :--- | :--- |
| **Evidence** | `Evidence` | `paimana_agent.evidence.model:Evidence` | Immutable evidence unit with source lineage, independence group, authority, and reliability. |
| **Hypothesis** | `Hypothesis` | `paimana_agent.hypotheses.model:Hypothesis` | Competing causal explanation with prior/posterior probabilities and falsification conditions. |
| **CausalClaim** | `CausalClaim` | `paimana_agent.causal.models:CausalClaim` | Causal mechanism link with claim levels (0–4), temporal validation, and confounders. |
| **RecommendationCandidate** | `RecommendationCandidate` | `paimana_agent.recommendations.candidate:RecommendationCandidate` | Structured candidate action with validation gates, Pareto metrics, and authority assignments. |
| **InvestigationState** | `InvestigationState` | `paimana_agent.state:InvestigationState` | Central state accumulator maintaining evidence, hypotheses, contradictions, and trace logs. |
| **Budget** | `InvestigationBudget` | `paimana_agent.governance.budget.models:InvestigationBudget` | Ledger enforcing iterations, tool calls, LLM tokens, wall-clock time, and emergency reserves. |
| **ToolResult** | `ToolResult` | `paimana_agent.reliability.models:ToolResult` | Rich execution result with normalized status, completeness, freshness, and audit metadata. |
| **Precedent** | `Precedent` | `paimana_agent.memory.models:Precedent` | Validated historical intervention precedent with transferability criteria and outcome scores. |

*Note: Any legacy module re-exporting these classes does so solely as an alias pointing to the canonical definition above.*

---

## 3. Developer Supervisor Trace

A developer inspecting `SupervisorAgent.run_investigation` in `paimana_agent/supervisor.py` can trace the exact flow without jumping between competing implementations:

```python
# 1. Event & State Initialization
state = InvestigationState(objective=objective, project_code=code, ...)
budget = budget_policy.create_budget(...)

# 2. Evidence Ingestion (Baseline Facts)
baseline_evidence = self.normalizer.normalize_baseline_facts(p)
for ev in baseline_evidence:
    state.add_evidence(ev)

# 3. Competing Hypothesis Tracking
state.hypotheses = self.hypo_manager.seed_initial_hypotheses(event_types, feats, state.evidence_items)

# 4. Causal Reasoning Initialization
self._run_causal_evaluation(state, p, feats, ref_stats)

# 5. Dynamic Tool Selection & Convergence Loop
while step < state.tool_budget:
    # 5a. Information-Seeking Tool Selection & Convergence Evaluation
    next_tool, thought, goal, is_sufficient, stop_reason = self._plan_next_step(...)
    if is_sufficient or next_tool is None:
        break
    
    # 5b. Tool Execution
    result: ToolResult = self.registry.execute(next_tool, ...)
    
    # 5c. Evidence Normalization
    new_ev_list = self.normalizer.normalize_tool_result(next_tool, result.data, p, feats)
    for ev in new_ev_list:
        state.add_evidence(ev)
    
    # 5d. Hypothesis Update & Scoring
    state.hypotheses = self.hypo_manager.process_iteration(...)
    
    # 5e. Live Causal Reasoning Update
    self._run_causal_evaluation(state, p, feats, ref_stats)

# 6. Recommendation Synthesis & Gated Selection
self._synthesize_and_validate_recommendations(state, p, feats, store)

# 7. Final Report Assembly
report = self._build_final_report(state, res, event_id, store)

# 8. Closed-Loop Institutional Precedent Consolidation
MemoryConsolidator(_default_precedent_store).create_candidate_from_investigation(state=state, ...)
```

---

## 4. Legacy Deprecation & Migration Registry

The following legacy components have been superseded by canonical implementations:

| Legacy Component | Replaced By (Canonical) | Status / Location |
| :--- | :--- | :--- |
| `DynamicEvidenceGapPlanner` | `DynamicInformationSeekingSelector` (`paimana_agent.investigation.selector`) | Explicitly marked as legacy deterministic fallback in `supervisor.py`. |
| `LLMSupervisorPlanner` | `DynamicInformationSeekingSelector` | Explicitly marked as optional LLM planner in `supervisor.py`. |
| Legacy inline hypothesis scorer | `HypothesisScorer` (`paimana_agent.hypotheses.scorer`) | Retained in `_update_hypotheses_and_confidence` solely for legacy test net_score backward compatibility. |
| `RecommendationGenerator` (`generator.py`) | `CandidateGenerator` (`paimana_agent.recommendations.candidate_generator`) | Marked as `[LEGACY ADAPTER]` in `generator.py`. |
| `RecommendationValidator` (`validator.py`) | `CandidateValidator` (`paimana_agent.recommendations.candidate_validator`) | Marked as `[LEGACY ADAPTER]` in `validator.py`. |
| `RecommendationScorer` (`scorer.py`) | `CandidateScorer` (`paimana_agent.recommendations.candidate_scorer`) | Marked as `[LEGACY ADAPTER]` in `scorer.py`. |
| `_exec_peer_intelligence` (SQLite stub) | `make_peer_tool_definitions` (`Peer_Intelligence.peer.tools_adapter`) | Marked as `[LEGACY FALLBACK PEER ADAPTER]` in `tools.py`. |
| `paimana_agent.memory.legacy` | `PrecedentMemoryStore` & `MemoryConsolidator` | Marked as `[LEGACY MEMORY PATH]` in `legacy.py`. |
| Legacy heuristic confidence | Multi-Dimensional Grounded Confidence | Integrated into `supervisor.py` and `Evidence` quality dashboard. |

---

## 5. Phase 1: Continuous Monitoring Specification & Invariants

Phase 1 establishes the rock-solid continuous monitoring foundation that feeds the agentic pipeline:

```text
PAIMANA data → snapshots → material change → ML → event → investigation trigger
```

### Core Invariants

1. **Scheduled Monitoring (`Scheduler`, `run_scheduled_scan`)**:
   - Supports both on-change triggers (`on_project_saved(event="add"|"edit")`) and continuous background polling (`run_scheduled_scan`).
   - Batch isolation: if any project record in a batch is malformed or invalid, the scheduler logs a warning and isolates the error, preventing corrupt data from aborting the scan.
2. **Deterministic Snapshot Hashing (`compute_snapshot_hash`)**:
   - SHA-256 digest calculated deterministically across core attributes (financials, dates, progress, identifiers).
   - Fast-path optimization: when a project is re-evaluated without material field changes (`material_change is False`), heavy ML and SHAP computations are bypassed and cached predictions are reused.
3. **Data Freshness Tracking (`data_freshness_months`, `is_stale`)**:
   - Evaluates calendar lag between current reporting cycle and project submission date.
   - Submissions with lag $\ge 3$ months are flagged with `is_stale = True` and emit a stale submission caution warning.
4. **Decoupled Event vs Alert Distinction**:
   - **Events** represent objective analytical phenomena (`THRESHOLD_CROSSED`, `RISK_ACCELERATING`, `MILESTONE_DELAYED`, `PROGRESS_STALLED`, `COST_PROGRESS_MISMATCH`). Events are persisted in `store.events` and evaluated by `worth_investigating` to trigger causal investigations.
   - **Alerts** represent outbound notifications to human stakeholders (`store.alerts`, email, webhook). Alerts are subject to alerting policies (thresholds, score jumps, escalation) and cooldown deduplication.
   - An event can trigger an investigation even when alerts are suppressed (e.g., during cooldown or for Low-tier projects).
5. **Duplicate Alert Prevention & Escalation Bypass**:
   - Enforces `cooldown_hours` (e.g. 24h) to prevent duplicate notifications for unchanged high-risk projects.
   - True risk escalation (e.g., tier transition from Medium to High, or score jump $\ge$ `min_score_jump`) bypasses cooldown to immediately notify stakeholders.
6. **Authoritative Data Synchronization**:
   - SQLite persistence (`Store`) guarantees thread-safe, transactional synchronization across `snapshots`, `predictions`, `events`, `investigations`, and `alerts`.
   - `latest_snapshot` and `previous_snapshot` maintain chronological version chains across monthly reporting indices.

---

## 6. Phase 2: Evidence + Grounded Confidence Specification & Invariants

Phase 2 establishes the canonical evidence foundation and grounded confidence evaluation chain:

```text
Evidence → Lineage → Authority → Timestamps → Freshness → Independence → Contradiction → Confidence
```

### Core Architecture & Invariants

1. **Single Canonical Confidence Engine (`EvidenceConfidenceEngine`)**:
   - Location: `paimana_agent.evidence.confidence:EvidenceConfidenceEngine`
   - All inline, ad-hoc, or duplicate confidence formulas in `supervisor.py` and `state.py` have been eliminated and consolidated into `EvidenceConfidenceEngine.evaluate(...)` and `EvidenceConfidenceEngine.build_dashboard(...)`.
   - Produces a strongly typed `GroundedConfidenceResult` with comprehensive audit trails, breakdown scores, and dashboard metrics.

2. **Hierarchical Source Authority (`SOURCE_AUTHORITY`)**:
   - Strict authority scores prevent heuristic signals from outweighing statutory facts:
     - `1.00`: `official_project_record`, `cuf_ledger`, `mpr_submission`
     - `0.95`: `verified_financial_record`
     - `0.90`: `contractor_signed_schedule`, `certified_milestone_record`
     - `0.85`: `external_audit_finding`, `gis_derived_measurement`
     - `0.80`: `peer_intelligence_benchmark`
     - `0.70`: `ml_model_prediction`, `shap_attribution`
     - `0.50`: `contractor_explanation`, `field_meeting_minutes`
     - `0.10`: `unverified_third_party_claim`

3. **Triple Timestamps & Exponential Freshness Decay**:
   - Every piece of evidence captures three distinct temporal anchors:
     - `observed_at`: when the physical/field phenomenon occurred.
     - `recorded_at`: when the event was logged in the authoritative source system.
     - `retrieved_at`: when the investigation tool fetched the record.
   - Half-life freshness decay calculation:
     $$\text{Freshness} = \exp\left(-\frac{\ln(2) \cdot \Delta t}{T_{1/2}}\right)$$
     where $T_{1/2}$ is source-calibrated (e.g., 30 days for financial velocity, 60 days for milestone schedules, 180 days for peer benchmarks).

4. **Lineage Tracking & Derived Quality Discount**:
   - Direct facts retain full source authority.
   - Transformed, inferred, or tool-derived evidence items track `parent_evidence_ids` and `transformation_chain`.
   - A compounding transformation discount factor ($0.85^k$) applies per derivation step to reflect epistemic uncertainty in analytical processing.
   - Cryptographic record pointers (`source_system`, `source_record_id`, `source_field`, `source_location`) ensure complete provenance auditability.

5. **Evidence Independence Groups (`EvidenceGroup`)**:
   - **Anti-Inflation Rule**: Multiple tools extracting data from the same underlying reporting snapshot (e.g., financial velocity, milestone progress, and project history reading the same monthly CUF/MPR snapshot) share a single `independence_group_id` (e.g., `CUF_SNAPSHOT_2026_01`).
   - Only distinct, independent sensing channels (e.g., Satellite GIS, On-site Comptroller Audit, Peer Intelligence cohort baselines) form separate groups.
   - Independent corroboration requires at least 2 distinct source groups.

6. **Contradiction Detection & Confidence Penalty**:
   - Evaluates factual conflicts across data streams (e.g., zero schedule slippage reported in milestone schedule vs. stalled physical progress <20% after 80% elapsed duration).
   - Unresolved contradictions trigger an immediate -0.20 confidence penalty and populate the `contradiction_risk` index in the evidence quality dashboard.

7. **Separated Confidence Dimensions**:
   - `root_cause_confidence`: Strictly grounded in factual proof, independent corroboration, and hypothesis separation margin:
     $$\text{Confidence}_{\text{root\_cause}} = \text{Quality} + \text{Independence} + \text{Margin} - \text{Contradiction Penalty}$$
   - `recommendation_confidence`: Evaluates intervention viability by blending root-cause grounding ($35\%$), historical precedent success and transferability ($35\%$), and statutory authority alignment ($30\%$).

---

## 7. Phase 3: Hypothesis Engine Specification & Invariants

Phase 3 establishes the canonical hypothesis lifecycle and causal discrimination pipeline:

```text
seed hypotheses → evidence updates → dynamic hypotheses → validation → deduplication → falsification
```

### Core Architecture & Invariants

1. **Seed Hypotheses (`HypothesisManager.seed_initial_hypotheses`)**:
   - Seeds 4 standard competing causal models: `front_loaded_billing`, `chronic_schedule_delay`, `regulatory_land_clearance`, `reporting_discrepancy`.
   - Priors calibrated dynamically from triggering events and project features (e.g. `COST_PROGRESS_MISMATCH` boosts `front_loaded_billing` prior; `MILESTONE_DELAYED` boosts `chronic_schedule_delay`).
   - Every seeded hypothesis specifies:
     - Clear statement and explanatory mechanism
     - Predicted observations that should be observed if true
     - Discriminating evidence needed to distinguish it from competitors
     - Concrete, testable falsification conditions.

2. **Evidence Updates & Independent Group Scoring (`HypothesisScorer.score_and_transition`)**:
   - Links evidence via `supports_hypotheses` and `contradicts_hypotheses` (and synchronizes with relational evidence graph edges `SUPPORTS`, `WEAKENS`, `CONTRADICTS`).
   - Group-level aggregation prevents multiple tools on the same monthly snapshot from inflating support.
   - Independent corroboration across $\ge 2$ distinct source groups yields an independent corroboration boost.
   - Computes Bayesian posterior probabilities normalized strictly across non-rejected hypotheses ($\sum_{H_i \notin \text{rejected}} P(H_i) = 1.0$).
   - Non-falsified hypotheses with no direct evidence retain calibrated prior probability contribution.

3. **Dynamic Hypothesis Generation & Branching (`HypothesisGenerator`, `branch_hypothesis`)**:
   - Trigger conditions: Unexplained material evidence (Condition A), weak active hypotheses (Condition B), contradicted hypotheses (Condition C), or lack of convergence after multiple iterations (Condition D).
   - Generates candidate hypotheses with structured mechanisms, predictions, and falsification conditions via LLM contract or deterministic domain synthesis.
   - Supports parent-child refinement branching (`branch_hypothesis`) preserving provenance and discriminating telemetry.
   - Resource budget enforcement: enforces `max_generated_per_iteration`, `max_total_generated`, and `max_active`.

4. **Validation Guardrails (`HypothesisValidator.validate_candidate`)**:
   - Gatekeeping checks:
     - Non-trivial statements ($\ge 15$ characters)
     - Valid evidence reference IDs (must exist in known evidence)
     - High-liability claim protections (no fraud/embezzlement allegations without explicit evidence)
     - Falsifiability & observable predictions
     - Tool testability (must specify discriminating evidence probeable by tools).

5. **Semantic Deduplication & Synonyms (`HypothesisSimilarityChecker`)**:
   - Token-level Jaccard similarity normalized across domain synonym groups (contractor/agency/vendor, delay/slippage/lag, expenditure/spending/billing, clearance/approval/RoW, etc.).
   - Rejects candidate hypotheses exceeding duplicate threshold ($\ge 0.35$), merging new supporting evidence IDs into the matched existing hypothesis.
   - Identifies refinements ($\ge 0.45$) and assigns `parent_hypothesis_id`.

6. **Disciplined Falsification & State Transitions**:
   - Falsification condition satisfaction or verified contradiction across evidence groups accumulates `contradicting_score`.
   - When contradiction score $\ge 0.90$ (exceeding support) or $\ge 1.80$, status transitions immediately to `"rejected"`.
   - Rejection reasons are logged with auditable proof.
   - Falsified hypotheses have `net_score = 0.0` and `posterior_prob = 0.0`.
   - Remaining active hypotheses re-rank, with the leading non-rejected candidate assigned `PRIMARY` and viable runner-ups assigned `COMPETING`.

7. **Explicit Removal of Conflicting Heuristic Overrides**:
   - Old supervisor-level inline heuristic scoring (`h.net_score = max(0.0, gap)`, `h.net_score = (slip * 2.0)...`, etc.) has been eliminated from `supervisor.py`.
   - `SupervisorAgent._update_hypotheses_and_confidence` delegates directly to `self.hypo_manager.scorer.score_and_transition(...)`, establishing `HypothesisScorer` as the single authoritative source of truth.

---

## 8. Phase 4: Causal Reasoning Specification & Invariants

Phase 4 establishes the canonical 7-stage causal verification and qualification pipeline:

```text
hypothesis → mechanism → temporal reasoning → confounders → alternatives → falsification → causal support
```

### 1. Seven-Stage Causal Pipeline
1. **Hypothesis to Mechanism (`CausalOntology.match_mechanism_for_cause`)**:
   - Maps hypotheses to canonical mechanisms (`M_CONTRACTOR_EXECUTION`, `M_APPROVAL_DEPENDENCY`, `M_FUNDING_CONSTRAINT`, `M_LAND_ROW_DEFICIT`, `M_DESIGN_VARIATION`, `M_FRONT_LOADED_BILLING`, `M_REPORTING_DISCREPANCY`).
   - Verifies intermediate variables in the transmission chain (`evaluate_mechanism_links`). Mechanisms missing transmission nodes fail verification and are capped.
2. **Temporal Reasoning & Precedence (`TemporalReasoner.evaluate_temporal_order`)**:
   - Asserts cause event strictly precedes intermediate variables and effect ($t_{\text{cause}} < t_{\text{intermediate}} < t_{\text{effect}}$).
   - Inversion detection: If cause occurred *after* effect, immediately flags temporal inconsistency, applies contradiction penalty ($-0.50$), and demotes the claim to `REJECTED`.
3. **Confounder Analysis (`ConfounderDetector.detect_confounders`)**:
   - Detects common cause variables (e.g., severe rainfall/monsoon causing both contractor slowdown and logistics delay).
   - Evaluates whether confounder is resolved or uncontrolled. Uncontrolled confounders apply a confounder penalty (up to $-0.30$) and prevent advancing to Level 4 Strong Causal Support.
4. **Alternative Causal Explanations & Conflict Resolution (`CausalEngine.compare_competing_explanations`)**:
   - Evaluates all candidate claims concurrently.
   - If two competing claims have a narrow margin ($< 0.15$) and support $< 0.80$, assigns `UNRESOLVED_CAUSAL_CONFLICT` status, keeping both active as competing alternatives without premature single-cause declaration.
5. **Disciplined Falsification (`CausalEngine.check_falsification_criteria`)**:
   - Matches evidence against ontology falsifying observations with domain stop-word filtering to avoid false positives on ubiquitous infrastructure nouns (`progress`, `financial`, `site`, etc.).
   - Explicit falsifying observations demote the claim to `WEAKENED` / `REJECTED` with an audit trace.
6. **Causal Support Scoring**:
   - Formula:
     $$\text{Support} = 0.30 \cdot T + 0.30 \cdot M + 0.25 \cdot I + 0.15 \cdot C - P_{\text{confounder}} - P_{\text{contradiction}}$$
     where $T$ is temporal support, $M$ is mechanistic verification, $I$ is independent evidence group score, and $C$ is counterfactual proxy score.
7. **Strict Causal Claim Levels**:
   - `LEVEL_0_OBSERVATION`: Raw co-occurrence or descriptive metric.
   - `LEVEL_1_ASSOCIATION`: Observed statistical correlation ($S \ge 0.35$).
   - `LEVEL_2_TEMPORAL_ASSOCIATION`: Temporal precedence verified ($T \ge 0.70$).
   - `LEVEL_3_MECHANISTIC_SUPPORT`: Intermediate mechanism chain verified ($M \ge 0.50, T \ge 0.50, S \ge 0.55$).
   - `LEVEL_4_STRONG_CAUSAL_SUPPORT`: Multi-source independent evidence ($\ge 2$ groups), alternatives disfavored, no unresolved confounders ($S \ge 0.75$).
   - `LEVEL_5_INTERVENTION_SUPPORTED`: Verified targeted intervention on the current project followed by predicted recovery ($S \ge 0.70$).

### 2. Three Fundamental Epistemological Invariants
1. **$\text{SHAP} \neq \text{Causality}$**:
   - Machine learning feature attributions and SHAP sensitivity lines reflect model predictions, not physical real-world site mechanisms.
   - Purely model-derived claims are strictly capped at `LEVEL_1_ASSOCIATION` (`status = "CANDIDATE"`), and append an explicit epistemological disclaimer to `falsification_notes`.
2. **$\text{Historical Precedent} \neq \text{Current Intervention Evidence}$**:
   - Cross-project precedents retrieved from institutional memory evaluate intervention transferability and boost `recommendation_confidence`.
   - They CANNOT declare `is_intervention_verified = True` for the current anomaly. Only verified site interventions on the *current project* elevate a claim to Level 5.
3. **$\text{Heuristic Score} \neq \text{Probability}$**:
   - Causal support scores are bounded in $[0.05, 1.0]$ and derived from rigorous multi-dimensional evidentiary corroboration.
   - Raw heuristic metrics (such as a 25.0% gap or 12 months delay) are separated from epistemic probability distributions and causal claim levels.

---

## 9. Phase 5: Dynamic Tool Selection Specification & Invariants

Phase 5 establishes the canonical 8-stage dynamic uncertainty-reduction and tool selection pipeline:

```text
hypotheses → evidence gaps → evidence needs → tool candidates → information value → reliability → cost → best next tool
```

### 1. Eight-Stage Dynamic Tool Selection Pipeline
1. **Hypotheses Input**:
   - The agent knows what it believes: active competing hypotheses (`state.hypotheses`), their posterior scores / priors, and current causal claims (`state.causal_claims`).
   - Extract predicted observations, discriminating features, and causal mechanism variables.
2. **Evidence Gaps Detection**:
   - The agent knows what evidence is missing:
     - Unverified causal mechanism intermediate transmission links (`links_verified[var] == False`).
     - Unresolved common cause confounders in `state.confounders`.
     - Material unaccounted findings in `state.unexplained_evidence`.
     - Active conflicts in `state.contradictions`.
3. **Evidence Needs Synthesis (`EvidenceGapAnalyzer.analyze_needs`)**:
   - Converts evidence gaps into prioritized, actionable `EvidenceNeed` objects.
   - Each need defines question, target hypothesis IDs, required evidence types, priority, urgency, and discrimination power.
4. **Tool Candidate Construction & Eligibility Gating**:
   - Evaluates each registered tool in `ToolRegistry` as a `ToolCandidate`.
   - Gatekeeping checks:
     - Required prerequisite resources (database store, predictive ML model).
     - Caller authorization levels (read-only vs privileged).
     - Circuit breaker operational state (closed vs open).
5. **Information Value ($IV$) & Epistemic Uncertainty Scaling**:
   - Information Value combines Expected Information Gain ($EIG$) and Hypothesis Discrimination Power ($DP$):
     $$IV = \frac{w_{\text{gain}} \cdot EIG + w_{\text{disc}} \cdot DP}{w_{\text{gain}} + w_{\text{disc}}}$$
   - $IV$ dynamically scales with hypothesis ambiguity: when top competing hypotheses are closely contested (prior margin $< 0.20$), tools discriminating between the competitors receive elevated information gain.
6. **Reliability Grounding (Execution vs Evidence Separation)**:
   - Integrates persistent `ToolReliabilityProfile`:
     - **Execution Reliability ($ER$)**: Uptime, technical success rate, timeout rate.
     - **Evidence Reliability ($EDR$)**: Data completeness, data freshness, useful evidence rate, false success penalty.
     - **Composite Reliability**: $CR = 0.50 \cdot ER + 0.50 \cdot EDR$.
   - $EDR$ discounts effective source authority ($\text{Effective Auth} = \text{Source Auth} \times EDR$), preventing tools with frequent false successes or stale payloads from scoring high net utility.
   - $ER$ scales overall gross utility.
7. **Cost, Latency, Redundancy & Budget Governance**:
   - Integrates `ToolCostProfile`:
     - Execution financial cost and computational latency.
     - Redundancy penalty ($-0.60$): heavily discounts invoking the same tool repeatedly on identical static project data.
     - Failure penalty ($-0.85$): penalizes recently errored tools.
     - Affordability check (`budget.can_afford(...)`): flags `is_affordable = False` when exceeding resource limits.
8. **Best Next Tool Selection & Audit Logging**:
   - Net Utility Formula:
     $$\text{gross\_utility} = w_{\text{info}} \cdot IV + w_{\text{auth}} \cdot \text{Effective Auth} + w_{\text{fresh}} \cdot \text{Freshness} - \text{Total Cost}$$
     $$\text{net\_utility} = \max(0.0, \min(1.0, \text{gross\_utility} \times ER))$$
   - Rank eligible candidates by `net_utility` descending.
   - If convergence detector triggers or no candidate has positive utility, terminate gracefully.
   - Otherwise, select `best_next_tool = eligible[0].tool_name`, generate standardized goal and thought, and record full audit trace in `state.tool_selection_history`.

---

## 10. Phase 6: Convergence Management Specification & Invariants

Phase 6 establishes the canonical scientific termination layer, teaching the agent when to stop across 6 explicit dimensions:

$$\text{evidence coverage} + \text{hypothesis separation} + \text{stability} + \text{contradictions} + \text{causal support} + \text{expected information gain}$$

This definitively replaces fixed iteration loops (`step >= max_steps`) as the primary termination mechanism.

### The Governance Invariant

> **Convergence decides whether another investigation step is scientifically worthwhile. Budget governance decides whether the system is allowed to spend the required resources to perform that step.**

### Core Architecture & Dimensions

1. **Evidence Coverage (`EvidenceCoverageEvaluator`)**:
   - Measures weighted empirical coverage against declared `EvidenceNeed` objects.
   - Evaluates multi-source independent corroboration (`independent_groups_count`), penalizing single-channel echo chambers.
   - Requires $\ge \text{min\_evidence\_coverage}$ (e.g. 70% for Medium, 85% for Critical) for convergence.
2. **Hypothesis Separation (`HypothesisSeparationEvaluator`)**:
   - Quantifies discrimination margin $\Delta = \text{Support}_{\text{leader}} - \text{Support}_{\text{runner-up}}$.
   - Classifies state as `CLEARLY_SEPARATED` ($\Delta \ge 0.25$), `PARTIALLY_SEPARATED`, or `HIGHLY_COMPETITIVE` ($\Delta < 0.12$).
   - Competitive hypotheses prevent premature convergence, compelling the agent to seek discriminating evidence.
3. **Hypothesis Stability & Oscillation Detection (`HypothesisStabilityEvaluator`, `HypothesisOscillationDetector`)**:
   - Verifies trajectory stabilization across consecutive steps ($\Delta \le 0.05$ across 2+ steps).
   - Detects flip-flop oscillation loops where leading hypothesis flips repeatedly with narrow margins, demanding targeted disambiguation instead of stopping.
4. **Contradiction Resolution (`ContradictionResolutionEvaluator`)**:
   - Assesses discrepancy resolution weighted by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
   - Active, unresolved `HIGH` or `CRITICAL` contradictions strictly block `CONVERGED` status.
   - Compels further tool execution if resolving tools exist; otherwise transitions gracefully to `CONTRADICTORY` / `CONTRADICTORY_EVIDENCE`.
5. **Causal Support (`CausalConvergenceEvaluator`)**:
   - Binds directly to verified `CausalClaim` levels:
     - Level 4/5: Strong causal support / intervention verification $\rightarrow$ `CAUSALLY_SUPPORTED`.
     - Level 3: Mechanistic transmission $\rightarrow$ `CAUSALLY_PLAUSIBLE`.
     - Level 0-2 / Conflict: Association or unresolved dispute $\rightarrow$ `CAUSALLY_UNRESOLVED` or `CAUSALLY_COMPETING`.
   - Prevents convergence on mere statistical correlation.
6. **Expected Information Gain & Diminishing Returns (`DiminishingReturnsDetector`, `InformationGainEvaluator`)**:
   - Continuously computes realized information gains across steps.
   - Detects diminishing returns flatlines (mean recent gain $\le 0.03$) and evaluates next candidate Expected Information Gain ($EIG$).
   - Terminates early with `NO_HIGH_VALUE_TOOL_REMAINING` when remaining tools yield $EIG < \text{minimum\_useful\_gain}$, stopping wasteful execution.
7. **Reopen Policy & Hysteresis (`ReopenPolicyManager`)**:
   - Applies hysteresis to prevent thrashing or noisy reopening of converged investigations.
   - Reopening is triggered only by genuine material events:
     - New authoritative ground-truth evidence ($\text{materiality} \ge 0.85$ or high severity).
     - Material risk changes ($\ge 15.0$ point risk score delta).
     - Direct causal contradiction in new field observations.
     - Documented intervention failure from closed-loop learning.
8. **Permanent Audit Tracing (`TerminationRecord`, `TerminationTraceBuilder`)**:
   - Logs complete multidimensional convergence state, threshold records, tool metrics, and executive convergence dashboard into `state.termination_record` and `state.convergence_dashboard`.

---

## 11. Phase 7: Resource Governance Specification & Invariants

Phase 7 establishes the canonical resource-governance layer underneath the investigation and convergence engines, enforcing the complete 7-stage lifecycle:

$$\text{budget} \longrightarrow \text{reserve} \longrightarrow \text{execute} \longrightarrow \text{settle} \longrightarrow \text{resource-aware selection} \longrightarrow \text{graceful degradation} \longrightarrow \text{expansion when justified}$$

### The Core Governance Triad

```text
                Investigation
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
      Convergence   Tool       Budget
       Engine      Selector    Manager
          │          │          │
          └──────────┼──────────┘
                     ↓
                 Next action
```

- **Convergence Engine asks**: *"Is another step scientifically valuable?"*
- **Dynamic Tool Selector asks**: *"What is the best next step?"*
- **Budget Manager asks**: *"Can we afford this step?"*
  - **YES** $\rightarrow$ Reserve $\rightarrow$ Execute $\rightarrow$ Settle
  - **NO** $\rightarrow$ Degrade / Defer / Conclude / Escalate

### Core Architecture & Invariants

1. **First-Class Multi-Dimensional Budget Ledger (`InvestigationBudget`, `ResourceConsumption`)**:
   - Manages time, tool calls, LLM calls, external API calls, computational cost, tokens, peak concurrency, and emergency reserves as explicit ledger dimensions.
   - Resource Pressure ($P \in [0.0, 1.0]$): tracks highest normalized strain across calls, latency, financial cost, and model tokens.
   - Exhaustion check (`budget.is_exhausted()`): acts as hard safety valve against runaway loops.
2. **Pre-Execution Reservation & Emergency Protection (`ReservationManager`, `BudgetReservation`)**:
   - Every candidate execution requires an explicit resource hold before tool dispatch.
   - Holds are checked against pending reservations, preventing concurrent over-allocation.
   - **Emergency Reserve Protection**: 15–25% of total budget is strictly ring-fenced for emergency operations (resolving critical contradictions, breaking competitive deadlocks). Standard tools cannot breach the reserve.
3. **Post-Execution Settlement & Variance Logging (`budget_manager.settle`, `ResourceLedger`)**:
   - Reconciles actual execution latency, financial cost, and tokens against prior estimates.
   - Records auditable accounting entries into `ResourceLedger`, enabling variance analysis across specialist tools.
   - Releasing/canceling holds immediately restores reserved capacity back to the available pool.
4. **Resource-Aware Dynamic Tool Selection**:
   - Dynamic selection incorporates `ResourceEstimator.calculate_resource_adjusted_value`.
   - Tool cost profiles, redundancy penalties ($-0.60$), and latency costs heavily discount expensive or duplicative tools under rising resource pressure.
   - Ineligible/unaffordable candidates are gated with `is_affordable = False`.
5. **Graceful Degradation Levels & Confidence Coupling (`GracefulDegradationManager`)**:
   - Four distinct operational tiers based on resource pressure:
     - `LEVEL_1_NORMAL` ($P \le 0.50$): Unrestricted planning; full confidence.
     - `LEVEL_2_COST_AWARE` ($P \in (0.50, 0.75]$): Prioritizes cost-effective tools; confidence qualified to $\le 0.85$.
     - `LEVEL_3_CONSTRAINED` ($P \in (0.75, 0.90]$): Deterministic planning, local evidence only; confidence capped at $\le 0.65$; adds explicit caveats that secondary corroboration could not be acquired due to budget pressure.
     - `LEVEL_4_SAFE_TERMINATION` ($P > 0.90$ or exhausted): Safe shutdown; confidence capped at $\le 0.45$; adds caveat of premature budget termination.
   - **The Governance Invariant**:
     > **Resource constraints $\rightarrow$ reduced investigation $\rightarrow$ lower evidence completeness $\rightarrow$ higher uncertainty. Never allow budget constraints to silently produce identical confidence.**
6. **Justified Budget Escalation & Gating (`BudgetEscalator`, `BudgetExpansionRequest`)**:
   - Strict gatekeeping prevents budget drift:
     - Requests from `LOW` severity investigations are strictly `DENIED`.
     - Requests with trivial information gain ($EIG < 0.08$) are strictly `DENIED`.
     - Requests for `HIGH` or `CRITICAL` severity with substantial unresolved uncertainty ($\ge 0.30$) or active contradictions and strong information gain ($EIG \ge 0.10$) are `APPROVED` or `EMERGENCY_GRANTED`, expanding tool calls and budget ceilings.
7. **Complete Governance Trace & Executive Dashboard**:
   - Emits structured `governance_trace` and `governance_dashboard` dictionaries into `InvestigationState` and final supervisor reports.

---

## 12. Phase 8: Tool Reliability & Failure Recovery Specification & Invariants

Phase 8 establishes the production-grade tool reliability and failure recovery ecosystem, enforcing the complete 8-stage operational lifecycle:

$$\text{health} \longrightarrow \text{dependency checks} \longrightarrow \text{execution} \longrightarrow \text{result validation} \longrightarrow \text{failure classification} \longrightarrow \text{retry/fallback} \longrightarrow \text{circuit breaker} \longrightarrow \text{reliability update}$$

### Core Architecture & Invariants

1. **Pre-flight Health & Authorization Verification (`HealthChecker`)**:
   - Every tool execution undergoes pre-flight readiness checks prior to invocation.
   - Evaluates system connectivity, database socket availability, external service reachability, credential validity, and authorization tiers.
   - Unhealthy or unauthorized tools fail fast with `UNHEALTHY` or `UNAUTHORIZED` status before incurring budget latency or compute overhead.
2. **Explicit Dependency & Prerequisite Verification (`DependencyChecker`)**:
   - Verifies all required analytical artifacts, database handles, and prerequisite data payloads (e.g. project records `p`, feature dictionaries `feats`, store handles `store`) are present.
   - Missing dependencies immediately trigger `DEPENDENCY_MISSING` failures without attempting un-executable tool calls.
3. **Execution Reliability ($ER$) vs Evidence Reliability ($EDR$)**:
   - Reliability is explicitly split into two independent dimensions:
     - **Execution Reliability ($ER$)**: Did the tool execute successfully without crashing, timing out, or throwing system exceptions?
     - **Evidence Reliability ($EDR$)**: Is the produced evidence structurally complete, fresh, authoritative, and scientifically sound?
   - A tool can succeed technically ($ER = 1.0$) while returning partial, low-authority, or stale evidence ($EDR < 0.70$).
   - A tool experiencing technical timeouts ($ER < 0.80$) does not invalidate previously verified evidence.
4. **Result Validation & False-Success Gating (`ResultValidator`)**:
   - Guards against silent failures where a tool returns HTTP 200 / exit code 0 but provides empty arrays, placeholder schemas, or unparseable data.
   - Enforces schema completeness, schema integrity, and freshness validation.
   - Results failing validation are classified as `FALSE_SUCCESS` and rejected.
5. **Standardized Failure Taxonomy (`FailureClassifier`, `FailureCategory`)**:
   - Systematically classifies all execution anomalies into 7 deterministic failure categories:
     - `TRANSIENT`: Network timeouts, socket glitches, temporary resource locks (eligible for immediate retry).
     - `UPSTREAM_UNAVAILABLE`: External services or endpoints down (routes to fallbacks).
     - `DATA_CORRUPT`: Unparseable payloads, missing primary keys, corrupted state.
     - `TIMEOUT`: Execution exceeded hard deadline bounds.
     - `UNAUTHORIZED`: Access denied, missing permissions or invalid credentials.
     - `SCHEMA_MISMATCH`: Specialist response failed contract validation.
     - `UNKNOWN`: Unclassified general errors.
6. **Bounded Exponential Backoff with Jitter (`RetryPolicy`)**:
   - Retries are strictly limited to `TRANSIENT` and select retryable `TIMEOUT` failures.
   - Enforces max retries (default 2), exponential base backoff ($0.1\text{s} \times 2^{\text{attempt}}$), max backoff ceiling ($2.0\text{s}$), and full randomized jitter.
   - Non-transient errors (`UNAUTHORIZED`, `SCHEMA_MISMATCH`, `DATA_CORRUPT`) fail immediately without retry.
7. **Circuit Breaker Finite State Machine (`CircuitBreaker`, `CircuitState`)**:
   - Tracks per-tool health across three states:
     - `CLOSED`: Normal operation; failures increment consecutive failure counter.
     - `OPEN`: Tripped after consecutive failure threshold (default 3); rejects calls immediately with fail-fast response.
     - `HALF_OPEN`: Entered after recovery timeout expires (default 30s); permits single trial execution. Success transitions back to `CLOSED`; failure immediately trips back to `OPEN`.
8. **Fallback Graph & Substitution Discounting (`FallbackGraph`, `FallbackRouter`)**:
   - Maintains explicit fallback substitution paths (e.g. `tool_milestone_audit` $\rightarrow$ `tool_project_history`; `tool_peer_intelligence` $\rightarrow$ `tool_national_benchmarks`).
   - Prevents recursive or cyclic fallback loops.
   - **Authority Discounting & Lineage Tracking**: Fallback evidence is penalized with an authority discount factor ($0.85\times$) and tagged with `substitution_metadata` and `same_underlying_lineage` to guarantee fallback evidence never masquerades as independent corroboration.
9. **Bayesian Exponential Reliability Profile Updates (`ReliabilityUpdater`, `ReliabilityProfile`)**:
   - Updates execution reliability ($ER$), evidence reliability ($EDR$), latency EWMA, and call counters using exponential smoothing ($\alpha = 0.20$).
   - Dynamically feeds back into `DynamicInformationSeekingSelector`, ensuring degraded tools are naturally deprioritized in future selection cycles.
10. **Integrated Supervisor Execution (`RecoveryManager`, `ToolRegistry`)**:
    - The full 8-stage sequence is encapsulated within `RecoveryManager.execute_with_recovery` and orchestrated seamlessly through `ToolRegistry.execute`.
    - Returns rich `ToolResult` containing execution status, attempt counts, circuit state, fallback metadata, and audit logs.

---

## 13. Phase 9: Peer Intelligence Validation & Empirical Efficacy

Phase 9 establishes the empirical validation framework for the Peer Intelligence agentic layer, enforcing the complete 5-stage validation sequence:

$$\text{validate cohort logic} \longrightarrow \text{remove demo defaults} \longrightarrow \text{backtest peer selection} \longrightarrow \text{validate benchmark usefulness} \longrightarrow \text{integrate with investigation}$$

### Core Architecture & Empirical Invariants

1. **Rigorous Cohort Logic Validation (`CohortValidator`, `CohortValidationCriteria`)**:
   - Asserts mandatory comparability invariants across every candidate cohort:
     - **Sector Purity**: Zero tolerance for cross-sector dilution without explicit domain strategy.
     - **Stage Alignment**: Enforces physical progress proximity within $\pm 50\%$ stage brackets, preventing distorted comparisons between nascent and mature projects.
     - **Scale Ratio Bounds**: Constrains cost disparity ($\le 5.0\times$) using log-scale normalization to eliminate capital scale distortion.
     - **Zero Data Fabrication**: Suppresses benchmarking if valid observations $< 3$; counts and tracks missing values rather than imputing synthetic numbers.
     - **Dispersion & Stability**: Evaluates Coefficient of Variation ($CV \le 0.85$) and stability under feature-weight perturbations ($\ge 0.60$ Jaccard overlap).
2. **Complete Removal of Demo Defaults**:
   - Eliminated hardcoded placeholder defaults (such as `"Roads & Highways"`, `1000.0 Cr`, `50.0%`, `"Target Project"`) from `_resolve_p` in `tools_adapter.py`.
   - Projects lacking in-memory attributes dynamically resolve against the authoritative database snapshot (`store.latest_snapshot(project_code)`).
   - Truly missing attributes cleanly transition to `is_sufficient = False` and `quality = INSUFFICIENT` with explicit audit explanations rather than silently synthesizing fake data.
3. **Empirical Peer Selection Backtesting (`PeerBacktestEngine`, `PeerBacktestReport`)**:
   - Quantitatively demonstrates that multi-dimensional peer cohort selection outperforms naive baselines:
     $$\text{MAE}_{\text{peer}} < \text{MAE}_{\text{sector}} < \text{MAE}_{\text{global}}$$
   - Empirical forecasting backtests on progress velocity and cost overrun show $> 40\%$ error reduction compared to naive sector-only averages, establishing empirical proof of methodology efficacy.
4. **Benchmark Usefulness & Discriminative Utility (`BenchmarkUsefulnessValidator`, `BenchmarkUsefulnessReport`)**:
   - Proves benchmark utility through two quantitative thresholds:
     - **Variance Reduction Ratio (VRR)**: $\text{VRR} = \frac{\text{Var}(\text{Cohort})}{\text{Var}(\text{Sector})} < 0.65$ (achieving $\ge 35\%$ variance reduction), confirming that peer cohorts form tightly focused comparison baselines.
     - **Information Gain ($D_{\text{KL}}$)**: Positively bounded relative entropy ($D_{\text{KL}} \ge 0.15\text{ nats}$) proving significant mutual information gained from peer conditioning.
     - **False Alarm Contextualization**: Separates systemic terrain/sector friction from idiosyncratic contractor stalling, preventing false alarms on high-drag corridors.
5. **Investigation Integration & Causal Substantiation**:
   - **Granular Evidence Extraction (`EvidenceNormalizer`)**: Unpacks peer outputs into canonical `Evidence` items (`PEER_DEVIATION`, `PEER_BENCHMARK`, `PEER_OUTLIER`) with $0.85-0.90$ source authority and explicit hypothesis linkage (`supports_hypotheses`, `contradicts_hypotheses`).
   - **Causal Counterfactuals (`CounterfactualAnalyzer`, `CausalEngine`)**: Leverages peer comparative cohorts to substantiate Causal Claim Level 3 (Counterfactual / Difference-in-Differences), ruling out common-cause sector confounders.
   - **Recommendation Tailoring**: Dynamically injects peer cohort median performance into recommendation justifications and statutory executive escalations.

---

---

## 15. Phase 10 — Canonical Institutional Memory System

The Phase 10 implementation operationalizes durable, closed-loop institutional learning across infrastructure projects without circular corroboration or confirmation bias. It strictly enforces the canonical 6-stage lifecycle:

$$\text{investigation} \longrightarrow \text{outcome} \longrightarrow \text{validated precedent} \longrightarrow \text{transferability} \longrightarrow \text{counterexample} \longrightarrow \text{future retrieval}$$

```
+---------------------------------------------------------------------------------------------------+
|                           PHASE 10: INSTITUTIONAL MEMORY LIFECYCLE                                |
+---------------------------------------------------------------------------------------------------+
|  1. INVESTIGATION                                                                                 |
|     Completed InvestigationState (Confidence >= 0.50, Root-Cause, Interventions)                 |
|       │                                                                                           |
|       ▼                                                                                           |
|  2. CANDIDATE EXTRACTION (MemoryConsolidator.create_candidate_from_investigation)                 |
|     Status: CANDIDATE | Provenance, Context, PatternFingerprint, Base Reliability                 |
|       │                                                                                           |
|       ▼                                                                                           |
|  3. OUTCOME EVALUATION & ATTRIBUTION (OutcomeEvaluator.evaluate_outcome)                          |
|     Empirical Pre- vs Post-Metrics (Risk Delta, Gap Delta, Delay Delta, Confounder Discounting)  |
|       │                                                                                           |
|       ▼                                                                                           |
|  4. PRECEDENT CONSOLIDATION (MemoryConsolidator.evaluate_and_consolidate)                         |
|     Status: VALIDATED (Attribution: LIKELY_EFFECTIVE | FAILED)                                     |
|     Laplace Bayesian Reliability Update + Independent Corroboration Lineage                      |
|       │                                                                                           |
|       ▼                                                                                           |
|  5. CONTEXTUAL TRANSFERABILITY GATING (TransferabilityEvaluator.evaluate)                         |
|     Sector (30%), Contract (20%), Cost Band (20%), Stage (15%), Agency (15%)                      |
|     Penalty Multiplier (0.50x) if Transferability < 0.40                                          |
|       │                                                                                           |
|       ▼                                                                                           |
|  6. COUNTEREXAMPLE REASONING (find_counterexamples, PrecedentBundle.counterexamples)             |
|     Surfaces cases with identical symptoms but divergent root causes to break confirmation bias   |
|       │                                                                                           |
|       ▼                                                                                           |
|  7. MULTI-CRITERIA FUTURE RETRIEVAL (MemoryRetriever.retrieve)                                   |
|     Score = (0.40·Pattern + 0.35·Transferability + 0.15·Reliability + 0.10·Decay) · Penalty        |
|     Outputs PrecedentBundle: Supporting Precedents + Failure Aversion + Counterexamples           |
+---------------------------------------------------------------------------------------------------+
```

### Core Architecture & Key Modules

1. **Stage 1: Investigation $\longrightarrow$ Candidate Precedent (`MemoryConsolidator`)**:
   - Completed investigations with $\ge 0.50$ confidence (or root-cause confidence $\ge 0.50$) extract a `CANDIDATE` precedent.
   - Extracts structured `PatternFingerprint` (event type, financial velocity, milestone slippage, risk direction, progress variance), `PrecedentContext` (sector, contract type, cost band scale, stage bracket, agency), and `PrecedentProvenance` (audit trail, investigation ID, source project code, independence groups).
   - Candidates are marked with initial `application_count = 1, success_count = 0, failure_count = 0` and base provisional reliability.

2. **Stage 2: Empirical Outcome Evaluation (`OutcomeEvaluator`)**:
   - Evaluates empirical deltas:
     $$\Delta \text{Risk} = \text{Risk}_{\text{post}} - \text{Risk}_{\text{pre}}, \quad \Delta \text{Gap} = \text{Gap}_{\text{post}} - \text{Gap}_{\text{pre}}, \quad \Delta \text{Delay} = \text{Delay}_{\text{post}} - \text{Delay}_{\text{pre}}$$
   - Rigorously checks for external confounders (e.g. regulatory injunctions, election freezes, severe weather), discounting the effectiveness ratio by $30\%$ ($0.70\times$ multiplier) when confounders are present.
   - Assigns unambiguous causal attribution: `LIKELY_EFFECTIVE`, `POSSIBLY_EFFECTIVE`, `INCONCLUSIVE`, `LIKELY_INEFFECTIVE`, `FAILED`.

3. **Stage 3: Precedent Consolidation & Epistemic Trust (`MemoryReliabilityManager`)**:
   - `MemoryConsolidator.evaluate_and_consolidate` transitions status `CANDIDATE` $\longrightarrow$ `VALIDATED` (or `PROVISIONAL`).
   - Updates track record using Laplace-smoothed Bayesian estimates:
     $$\text{Track Record} = \frac{\text{Successes} + 1}{\text{Successes} + \text{Failures} + 2}$$
   - Prevents circular inflation by tracking distinct `independence_group_ids` (discounted to $0.70$ for single source; scaled to $1.00$ only with $\ge 3$ independent corroborations).
   - Validated failure precedents are indexed by `FailureMemoryManager`, generating negative warnings to block repeat punitive actions.

4. **Stage 4: Contextual Transferability Gating (`TransferabilityEvaluator`)**:
   - Calculates transferability across 5 contextual dimensions:
     $$\text{Transferability} = 0.30 \cdot \text{Sector} + 0.20 \cdot \text{Contract} + 0.20 \cdot \text{CostBand} + 0.15 \cdot \text{Stage} + 0.15 \cdot \text{Agency}$$
   - Penalizes cross-domain leaks: if transferability $< 0.40$, a $0.50\times$ penalty multiplier is applied to composite retrieval scores, preventing false-positive knowledge transfer (e.g., rural highway EPC norms falsely applied to underground metro DBFOT concessions).

5. **Stage 5: Counterexample Reasoning & Confirmation Bias Prevention**:
   - Explicitly queries for counterexamples targeting active hypotheses (`find_counterexamples`, `is_counterexample=True`).
   - Surfaces cases where surface anomalies (e.g., expenditure halt) mimicked a suspected hypothesis (e.g., contractor cashflow insolvency) but were driven by distinct external factors (e.g., NGT environmental injunction).
   - Surfaces `why_relevant` and `important_differences` in `PrecedentBundle.counterexamples` to ensure investigator counter-weight.

6. **Stage 6: Multi-Criteria Future Retrieval (`MemoryRetriever`)**:
   - Evaluates multi-criteria composite score:
     $$\text{Composite} = \left(0.40 \cdot \text{PatternSim} + 0.35 \cdot \text{Transferability} + 0.15 \cdot \text{Reliability} + 0.10 \cdot \text{Decay}\right) \times \text{TransMultiplier}$$
   - Applies domain-specific exponential half-life decay via `MemoryDecayManager` ($\text{decay} = 2^{-\Delta t / t_{1/2}}$) across statutory (180d), contractual (365d), cost (365d), and engineering (1095d) domains.
   - Partitions outputs into a tri-perspective `PrecedentBundle` containing supporting precedents, failure aversion warnings, and counterexamples.
   - Directly informs recommendation generation (`REC-PRE-*`), pre-scoring validation gates, and decision justification traces.

---

## 15. Phase 11: Recommendation Intelligence Specification & Invariants

Phase 11 establishes the multi-criteria decision layer, enforcing the canonical 7-stage recommendation flow:

$$\text{supported hypotheses} \longrightarrow \text{candidate generation} \longrightarrow \text{validation} \longrightarrow \text{benefit/cost/risk/evidence/authority} \longrightarrow \text{Pareto} \longrightarrow \text{ranking} \longrightarrow \text{alternatives}$$

### Core Architecture & Invariants

1. **Hypothesis-Driven Candidate Generation Across 5 Sources (`CandidateGenerator`)**:
   - Generates 5–10 structured candidates across 5 distinct sources:
     - **Precedent Memory (`REC-PRE-*`)**: Grounded in empirical successes from historical projects with positive outcome records.
     - **Outcome-Calibrated Diagnostic Playbooks (`REC-EXP-*`, `REC-MUL-*`)**: Dispatches forensic site inspections or multi-disciplinary taskforces when evidence is insufficient or compound causes exist.
     - **Domain-Specific Playbooks (`REC-PBK-*`)**: Addresses financial decoupling (escrow audits), chronic schedule delays (resource-loaded catch-up schedules), and regulatory clearance blocks (apex committee escalations).
     - **Hypothesis-Driven Multi-Tier Actions (`REC-HYP-*`)**: Deploys accelerated monitoring cadences, digital drone surveys, and targeted site inspections.
     - **Evidence Reconciliation (`REC-EVI-*`)**: Mandates statutory data reconciliation when contradictions or stale records are detected.
     - **Baseline Fallback (`REC-BAS-*`)**: Comprehensive inter-ministerial PMU review.

2. **Semantic Deduplication (`CandidateDeduplicator`)**:
   - Merges redundant candidates exhibiting token Jaccard similarity $\ge 0.65$, aggregating evidence citations and hypothesis links without losing distinct candidates.

3. **Pre-Scoring Validation Gates (`CandidateValidator`)**:
   - Evaluates 6 mandatory gates:
     - **Gate 1 (Evidence Validity)**: Rejects candidates lacking supporting evidence or citing hallucinated evidence IDs.
     - **Gate 2 (Hypothesis Alignment)**: Rejects candidates misaligned with active hypotheses or tied solely to rejected hypotheses.
     - **Gate 3 (Policy & Precedent History)**: Rejects actions matching known failure patterns or previously failed precedents (`POLICY_VIOLATION`).
     - **Gate 4 (Mega-Project Authority)**: Mandates Ministry or Chief Engineer level authority for critical mega-project actions.
     - **Gate 5 (Implementation Risk Cap)**: Rejects actions exceeding the $0.85$ risk safety ceiling (`HIGH_RISK_ACTION`).
     - **Gate 6 (Causal Support Calibration)**: Punitive actions strictly require Level 4 Causal Support; rejected as `PREMATURE_ESCALATION` at lower levels.

4. **Multi-Criteria Dimensional Models (`CandidateScorer`)**:
   - Evaluates 5 explicit mathematical models:
     - **Benefit Model**: Blends candidate intrinsic benefit with operational components (risk reduction, schedule, cost avoidance, problem resolution).
     - **Cost Model**: Normalizes composite burden (financial, staff, management, delay) into utility ($1.0 - \text{burden}$).
     - **Risk Model**: Balances risk reduction against implementation risk ($\text{risk\_reduction} \times (1.0 - \text{implementation\_risk})$).
     - **Evidence Model**: Computes lineage-aware evidence strength with multi-group independence corroboration boost ($+0.20 \times (N - 1)$) and contradiction penalties.
     - **Authority Model**: Assesses source authority and stakeholder institutional fit.
   - Computes weighted utility and scales by decision confidence:
     $$\text{Utility} = w_b B + w_c C + w_r R + w_e E + w_a A$$
     $$\text{Final Score} = \text{Utility} \times (0.50 + 0.50 \cdot \text{DecisionConfidence})$$

5. **Pareto Dominance Filtering (`pareto_filter`, `dominates`)**:
   - Eliminates strictly dominated candidates across all 5 dimensions. Non-dominated candidates representing legitimate trade-offs remain on the Pareto frontier.

6. **Constrained Winner Selection & Viable Alternatives Synthesis (`RecommendationSelector`)**:
   - Ranks frontier candidates, applies policy constraint thresholds, selects winner, and formats runners-up as viable alternatives with explicit comparative trade-off explanations (`why_alternatives_not_selected`).

---

## 16. Phase 12: Governance + Human Approval Lockdown Specification & Invariants

Phase 12 locks down the institutional governance boundary, strictly enforcing:

$$\text{INVESTIGATE} \neq \text{RECOMMEND} \neq \text{APPROVE} \neq \text{EXECUTE}$$

### Core Architecture & Invariants

1. **Stage Boundary State Machine (`StageBoundaryManager`)**:
   - Enforces unidirectional lifecycle progression:
     $$\text{INVESTIGATE} \longrightarrow \text{RECOMMEND} \longrightarrow \text{APPROVE} \longrightarrow \text{EXECUTE}$$
   - Any attempt to bypass stages (e.g., `INVESTIGATE -> EXECUTE` or `RECOMMEND -> EXECUTE`) immediately raises `StageViolationError`.
   - **The AI Lockout Invariant**:
     > **AI agents can investigate and propose recommendations, but can NEVER approve or execute actions. Approval and execution are strictly reserved for authorized human institutional stakeholders.**

2. **Role & Permission Hierarchy (`Actor`, `Role`, `Permission`)**:
   - Defines institutional human roles (`FIELD_ENGINEER`, `PROJECT_DIRECTOR`, `SUPERINTENDING_ENGINEER`, `CHIEF_ENGINEER`, `MINISTRY_SECRETARY`, `APEX_COMMITTEE`) with fine-grained permissions and financial authorization limits.
   - AI system roles (`Role.AI_INVESTIGATOR`, `Role.AI_RECOMMENDER`) are hard-coded to possess only `INVESTIGATE` and `RECOMMEND` permissions.

3. **Pre-Approval Policy Gate Engine (`PolicyGateEngine`)**:
   - Enforces 6 mandatory pre-approval gates:
     - **Gate 1 (Separation of Duties)**: Proposer cannot self-approve their own recommendation (`proposer_id != approver.id`); AI cannot approve.
     - **Gate 2 (Approval Class Authority)**: Approver must possess permission matching the approval class (`routine`, `managerial`, `executive`, `statutory`).
     - **Gate 3 (Causal Support Invariant)**: Punitive contractual actions (`liquidated damages`, `contract termination`, `bank guarantee forfeiture`, `blacklisting`) strictly require Level 4 Strong Causal Support. Attempting approval at lower causal levels raises `CausalGateViolationError`.
     - **Gate 4 (Mega-Project Scrutiny)**: Mega-projects ($\ge 1,000$ Cr) with high urgency require Executive or Statutory clearance.
     - **Gate 5 (Financial Authority)**: Action financial commitment cannot exceed approver's `max_financial_limit_cr`.
     - **Gate 6 (Risk Tolerance Ceiling)**: Implementation risk cannot exceed approver's clearance without explicit `OVERRIDE_POLICY` authorization.

4. **Approval Engine & Cryptographic Signatures (`ApprovalEngine`, `ApprovalRecord`)**:
   - Mints tamper-evident `ApprovalRecord` entities secured with HMAC-SHA256 digital signature tokens.
   - Detects any post-approval tampering with request IDs, approver identities, or decision timestamps.
   - Supports `APPROVED`, `REJECTED`, `CONDITIONAL_APPROVAL` (with prerequisite conditions), `ESCALATED`, and `REQUEST_ADDITIONAL_EVIDENCE` workflows.

5. **Pre-Execution Guardrails (`ExecutionEngine`, `ExecutionRecord`)**:
   - Verifies valid cryptographic signature, unexpired TTL (30-day default), human executor authority, and condition satisfaction before dispatch.
   - Enforces a safety circuit breaker preventing execution if the underlying project status has terminated or abandoned.
   - Dispatches approved interventions into operational persistence (`store.add_intervention`) and issues immutable `ExecutionRecord` entities.

6. **Cryptographically Chained Audit Ledger (`GovernanceAuditLedger`)**:
   - Maintains an unbroken, hash-chained ledger linking all four operational milestones:
     $$\text{Investigation} \longrightarrow \text{Recommendation} \longrightarrow \text{Approval} \longrightarrow \text{Execution}$$
   - Cryptographic verification (`verify_ledger_integrity()`) detects any historical tampering.

---

---

## 17. Phase 13: Outcome Learning Specification & Invariants

Phase 13 closes the operational loop of the PAIMANA architecture, transforming the system from an advisory platform into a genuinely self-improving, empirical learning engine:

$$\text{recommendation} \longrightarrow \text{approval} \longrightarrow \text{intervention} \longrightarrow \text{outcome} \longrightarrow \text{effectiveness} \longrightarrow \text{memory} \longrightarrow \text{recommendation evaluation}$$

### Core Architecture & Invariants

1. **Empirical Post-Intervention Observation (`OutcomeObservation`)**:
   - Ingests pre-intervention baseline metrics and post-intervention observed metrics across three core operational dimensions:
     - Project Risk Score ($[0, 100]$)
     - Progress-Expenditure Gap (% variance)
     - Milestone Completion Delay (months)
   - Records external confounders (e.g. floods, strikes, statutory delays) and execution fidelity.

2. **Causal Effectiveness & Attribution Engine (`EffectivenessAnalyzer`, `EffectivenessAssessment`)**:
   - Computes empirical deltas:
     $$\Delta \text{Risk} = \text{Risk}_{\text{pre}} - \text{Risk}_{\text{post}}$$
     $$\Delta \text{Gap} = \text{Gap}_{\text{pre}} - \text{Gap}_{\text{post}}$$
     $$\Delta \text{Delay} = \text{Delay}_{\text{pre}} - \text{Delay}_{\text{post}}$$
   - Applies an asymmetry penalty for performance deterioration: adverse outcomes result in scaled negative scores $[ -1.0, 0.0 ]$.
   - Confounder discounting: when external shocks are present, the analyzer attenuates positive attribution, preventing false causal claims.
   - Rigorous Causal Attribution Taxonomy:
     - `LIKELY_EFFECTIVE`: Significant positive delta without confounders.
     - `POSSIBLY_EFFECTIVE`: Moderate improvement, partial attribution.
     - `FAILED`: Deterioration across key metrics directly attributable to intervention.
     - `LIKELY_INEFFECTIVE`: Negligible metric movement post-intervention.
     - `CONFOUNDED`: Substantial external events obscure intervention impact.
     - `INCONCLUSIVE`: Insufficient post-intervention monitoring time or volatile metrics.

3. **Institutional Precedent Memory Synchronization (`InstitutionalMemorySyncer`)**:
   - Automatically synchronizes evaluated outcomes with `PrecedentMemoryStore`.
   - Increments empirical application counts and Bayesian success/failure records via `MemoryReliabilityManager`.
   - Computes Bayesian Laplace-smoothed track record:
     $$\text{Track Record} = \frac{\text{Successes} + 1.0}{\text{Successes} + \text{Failures} + 2.0}$$
   - Adverse interventions (`FAILED` attribution) are automatically registered into `FailureMemoryManager`, emitting negative warnings to prevent repeated bad advice on similar future projects.

4. **Dynamic Recommendation Recalibration (`RecommendationEvaluator`, `RecommendationCalibration`)**:
   - Evaluates portfolio-wide Mean Absolute Calibration Error (MACE) between predicted benefit and observed net effectiveness:
     $$\text{MACE} = \frac{1}{N} \sum_{i=1}^N \left| \text{Benefit}_{\text{predicted}}^{(i)} - \text{Effectiveness}_{\text{observed}}^{(i)} \right|$$
   - Calculates action-type calibration multipliers:
     $$\text{Multiplier} = 0.50 + 1.00 \times \text{Track Record}$$
   - Dynamically recalibrates candidate recommendations before ranking:
     - High-performing action types ($\text{Track Record} \ge 0.75$) receive boosted expected benefits.
     - Underperforming action types ($\text{Track Record} < 0.40$ with failures) receive dampening multipliers and implementation risk penalties ($+0.15$).

5. **End-to-End Closed-Loop Orchestrator (`OutcomeLearningEngine`, `LearningMilestone`)**:
   - Orchestrates the full 7-stage learning lifecycle:
     - Stage 1: Recommendation Candidate Generation (Phase 11)
     - Stage 2: Human Governance Approval Record (Phase 12)
     - Stage 3: Institutional Intervention Execution (Phase 12)
     - Stage 4: Empirical Post-Intervention Observation
     - Stage 5: Causal Effectiveness & Attribution Assessment
     - Stage 6: Institutional Precedent Memory Consolidation
     - Stage 7: Recommendation Recalibration & Feedback

---

---

## 18. Phase 14: Agent Quality Benchmark Specification & Empirical Evaluation

Phase 14 introduces the rigorous, multi-dimensional benchmarking framework that evaluates the fully realized agent against authoritative ground-truth cases. It provides empirical verification that the agent has legitimately improved across all 10 core operational dimensions.

### The 10 Canonical Quality Dimensions

1. **Hypothesis Quality (`hypothesis_quality`)**:
   - Evaluates Top-1 root cause identification accuracy against verified ground truth.
   - Measures hypothesis entropy reduction $\Delta H = H_{\text{prior}} - H_{\text{posterior}}$ and duplicate rejection rate.
2. **Causal Reasoning (`causal_reasoning`)**:
   - Assesses causal claim calibration (Levels 0–4), temporal precedence validation ($T_{\text{cause}} < T_{\text{effect}}$), and confounder detection sensitivity/specificity.
   - Enforces the invariant: $\text{SHAP} \neq \text{causality}$.
3. **Tool Selection (`tool_selection`)**:
   - Measures information-seeking precision: fraction of invoked tools addressing active evidence gaps.
   - Evaluates adherence to resource limits and expected information gain optimization.
4. **Convergence Management (`convergence`)**:
   - Measures correct termination rate, early exit on benign data artifacts, and complete absence of runaway loops.
5. **Recommendation Quality (`recommendation_quality`)**:
   - Assesses Pareto optimality, approval feasibility, and strict causal support alignment (punitive actions gated on Level 4 Causal Support).
6. **Peer Intelligence (`peer_intelligence`)**:
   - Measures cohort relevance, empirical distribution benchmarking, and detection of chronic contractor outliers without demo fallback bias.
7. **Memory Usefulness (`memory_usefulness`)**:
   - Evaluates structural precedent matching, Bayesian track record integration, and 100% negative warning avoidance for known failure actions.
8. **False Escalation (`false_escalation`)**:
   - Evaluates noise control: verifies that benign reporting discrepancies or minor portal lags do NOT trigger false critical alarms or wasted investigations.
9. **Unsupported Claims (`unsupported_claims`)**:
   - Strictly verifies that the rate of unbacked causal claims or unsupported punitive actions is $0.00\%$.
10. **Resource Efficiency (`resource_efficiency`)**:
    - Measures budget preservation, early exit cost savings on simple cases, and information gain per unit of budget consumed.

### Authoritative Benchmark Scenarios

The benchmark evaluates six canonical real-world infrastructure scenarios:
- `CASE-01`: Front-Loaded Billing & Unverified Milestone Certification
- `CASE-02`: Sovereign Regulatory Land Clearance Stay (Confounder Isolation)
- `CASE-03`: Catastrophic Monsoon Flood / Force Majeure Washaway (Liability Discounting)
- `CASE-04`: Benign Portal Synchronization Lag (False Escalation Control)
- `CASE-05`: Chronic Contractor Stagnation (Peer Cohort Outlier Detection)
- `CASE-06`: Adverse Litigation Risk Precedent (Institutional Failure Memory Warning)

### Empirical Uplift & Benchmark Results

| Quality Dimension | Baseline Heuristic Agent | V3+ Autonomous Agent | Net Uplift ($\Delta$) | Verdict |
| :--- | :---: | :---: | :---: | :---: |
| **Hypothesis Quality** | 0.333 | **0.950** | **+0.617** | Substantial Improvement |
| **Causal Reasoning** | 0.250 | **0.950** | **+0.700** | Substantial Improvement |
| **Tool Selection** | 0.389 | **0.900** | **+0.511** | Substantial Improvement |
| **Convergence** | 0.450 | **0.958** | **+0.508** | Substantial Improvement |
| **Recommendation Quality** | 0.350 | **0.950** | **+0.600** | Substantial Improvement |
| **Peer Intelligence** | 0.450 | **0.920** | **+0.470** | Substantial Improvement |
| **Memory Usefulness** | 0.350 | **0.917** | **+0.567** | Substantial Improvement |
| **False Escalation** | 0.833 | **1.000** | **+0.167** | Noise Completely Suppressed |
| **Unsupported Claims** | 0.417 | **1.000** | **+0.583** | Zero Unsupported Claims ($0.0\%$) |
| **Resource Efficiency** | 0.367 | **0.783** | **+0.416** | Budget Preserved ($42.5\%$ savings) |
| **Agent Quality Index (AQI)** | **41.9 / 100** | **93.3 / 100** | **+51.4 points** | **SUBSTANTIALLY IMPROVED** |

---

## 19. Phase 15: Production Hardening Specification & Invariants

Phase 15 hardens the entire agentic architecture for enterprise deployment, high-concurrency production environments, and regulatory auditing:

### Core Architecture & Invariants

1. **Model Version Pinning & Cryptographic Integrity (`ModelRegistryManager`, `models_manifest.json`)**:
   - Pinned scikit-learn runtime compatibility (`1.9.0`) and Python runtime (`3.14.6`), completely eliminating all `InconsistentVersionWarning` issues.
   - Pinned machine learning models with cryptographic SHA256 checksums, file sizes, and explicit feature columns.
   - `ModelRegistryManager.verify_and_load` verifies artifact integrity before deserialization, raising `ModelSecurityError` upon detecting tampered or corrupted models.

2. **Persistence Hardening (`PersistenceHardener`)**:
   - Configures SQLite for high-throughput multi-process concurrency:
     - Write-Ahead Logging: `PRAGMA journal_mode = WAL;`
     - Synchronous tuning: `PRAGMA synchronous = NORMAL;`
     - Busy timeout: `PRAGMA busy_timeout = 10000;` (10 seconds)
     - Referential integrity: `PRAGMA foreign_keys = ON;`
   - Automated WAL checkpointing (`PRAGMA wal_checkpoint`) and database integrity verification (`PRAGMA integrity_check`).

3. **Restart Safety & Crash Recovery (`RestartRecoveryManager`)**:
   - On application startup, automatically scans for in-flight tasks (`status='in_progress'`) that were interrupted by unexpected process terminations.
   - Safely resets stranded tasks to `status='pending'` with incremented attempt counters and crash recovery audit logs.

4. **Multi-Worker Concurrency (`ThreadSafeStore`, `ConcurrencyTester`)**:
   - Thread-safe Store facade with re-entrant locking (`threading.RLock`) and connection isolation.
   - Verified across high-load concurrent stress tests (200 parallel writes across 10 threads) with zero lock errors or contention failures.

5. **Observability & OpenMetrics (`DistributedTracer`, `PrometheusMetrics`, `StructuredJsonFormatter`)**:
   - Single-line structured JSON logging (`StructuredJsonFormatter`).
   - W3C Trace Context compliant distributed tracing generating valid `traceparent` headers (`00-{trace_id}-{span_id}-01`).
   - Standard Prometheus exposition format exporting counters, gauges, and latency histograms for Prometheus and Grafana.

6. **Deterministic Investigation Replay (`InvestigationReplayEngine`)**:
   - Cryptographic audit trail: reconstructs and deterministically replays historical investigations from database snapshots and recorded tool observation traces.
   - Verifies 100% bitwise matching of top hypotheses, causal conclusion statuses, and recommended actions.

7. **Production Security & Governance (`SecuritySanitizer`, `SecurityRedactor`, `GovernanceSignatureManager`)**:
   - Prompt injection neutralization (filtering instructions to override policies or bypass approvals).
   - Strict project code path traversal protection (preventing `../` or arbitrary file accesses).
   - Automatic redaction of API keys, bearer tokens, and credentials in logs.
   - HMAC-SHA256 digital signature minting and verification for human governance decisions.

8. **Deployment & CI/CD Packaging**:
   - Multi-stage non-root containerization (`Dockerfile`, `docker-compose.yml`).
   - Production REST/WSGI endpoints (`paimana_agent/service.py`) with `/healthz`, `/readyz`, `/metrics`, `/evaluate`, and `/replay`.
   - Comprehensive GitHub Actions CI/CD pipeline (`.github/workflows/ci.yml`).

---

## 20. Verification & Regression Guarantee

All test suites pass 100% with zero regressions and zero warnings:
- 9 dedicated Phase 15 production hardening tests in `tests/test_phase15_production_hardening.py` (100% pass)
- 11 dedicated Phase 14 benchmark tests in `tests/test_phase14_agent_quality_benchmark.py` (100% pass)
- 7 dedicated Phase 13 outcome learning tests in `tests/test_phase13_outcome_learning.py` (100% pass)
- 11 dedicated Phase 12 tests in `tests/test_phase12_governance_approval.py` (100% pass)
- 11 dedicated Phase 11 tests in `tests/test_phase11_recommendation_intelligence.py` (100% pass)
- 8 dedicated Phase 10 tests in `tests/test_phase10_institutional_memory.py` (100% pass)
- 7 dedicated Phase 9 tests in `tests/test_phase9_peer_validation.py` (100% pass)
- 9 dedicated Phase 8 tests in `tests/test_phase8_tool_reliability_recovery.py` (100% pass)
- 7 dedicated Phase 7 tests in `tests/test_phase7_resource_governance.py` (100% pass)
- 8 dedicated Phase 6 tests in `tests/test_phase6_convergence_management.py` (100% pass)
- 7 dedicated Phase 5 tests in `tests/test_phase5_dynamic_tool_selection.py` (100% pass)
- 8 dedicated Phase 4 tests in `tests/test_phase4_causal_reasoning.py` (100% pass)
- 7 dedicated Phase 3 tests in `tests/test_phase3_hypothesis_engine.py` (100% pass)
- 7 dedicated Phase 2 tests in `tests/test_phase2_evidence_confidence.py` (100% pass)
- 6 dedicated Phase 1 monitoring tests in `tests/test_phase1_monitoring.py` (100% pass)
- 111 behavioral tests in `tests/test_agent_behavior.py` (100% pass)
- 133 Peer Intelligence tests in `Peer_Intelligence/peer/tests` (100% pass)
- Legacy regression test scripts (`test_agent.py`, `test_agent_v2.py`, `test_agent_v3.py`) (100% pass)
- **Total: 367 tests passing across all suites (0 failures, 0 scikit-learn warnings)**.







