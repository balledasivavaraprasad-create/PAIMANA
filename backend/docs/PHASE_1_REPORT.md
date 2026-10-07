# PHASE 1 — CONTINUOUS MONITORING HARDENING REPORT
**InfraBuild-AI / PAIMANA Agentic Layer**  
*Part 2: Production-Correct Snapshot-Driven Monitoring*

---

## 1. Executive Summary

Phase 1 hardens the continuous monitoring subsystem of the PAIMANA Agent into an authoritative, snapshot-driven monitoring engine. Prior to Phase 1, project checks conflated risk evaluation with alert generation, re-ran expensive ML and SHAP models on unmutated records, lacked cryptographic provenance and discrete data freshness states, and did not maintain an explicit boundary with external authoritative data providers.

With this release:
- Continuous monitoring strictly follows canonical snapshot lifecycle and material change detection.
- Unchanged project snapshots bypass compute-intensive ML and SHAP models, reusing validated state and recording project health checks.
- Risk state, risk change, material data change, operational events, and outbound alerts are formally decoupled into distinct concepts.
- Data freshness is classified into explicit states (`FRESH`, `AGING`, `STALE`, `UNAVAILABLE`) and propagated downstream.
- Authoritative boundary providers (`AuthoritativeDataProvider`, `FileDataProvider`, `ApiDataProvider`, `MemoryDataProvider`) guard against fake data fabrication upon provider downtime.
- Alert deduplication ensures persistent high-risk projects remain visible without triggering duplicate alerts unless genuine risk transitions occur.

---

## 2. Files Changed & Created

| File | Type | Changes / Purpose |
|---|---|---|
| `paimana_agent/snapshot.py` | **New** | Implemented `CanonicalSnapshot` dataclass, `SnapshotSource` enum (`PAIMANA_SYNC`, `USER_EDIT`, `IMPORT`, `SYSTEM_UPDATE`, `SCHEDULED_SCAN`), `FreshnessState` enum (`FRESH`, `AGING`, `STALE`, `UNAVAILABLE`), and `compute_freshness()` calculation. |
| `paimana_agent/store.py` | **Refactored** | Added schema migration for canonical snapshot attributes (`snapshot_id`, `source`, `source_record_id`, `snapshot_hash`, `schema_version`, `observed_at`, `recorded_at`, `retrieved_at`, `reporting_period`, `freshness_state`), created `project_checks` table for verification audit logs, enhanced `save_snapshot()`, `latest_snapshot()`, and `previous_snapshot()`, and added `record_project_check()` / `last_project_check()`. |
| `paimana_agent/agent.py` | **Refactored** | Integrated canonical snapshot construction via `CanonicalSnapshot.create()`, implemented hash-based fast-path material change detection before ML inference, recorded project checks, cleanly decoupled `current_risk_state`, `risk_change`, `material_data_change`, `events`, and `alert`, and refactored `_decide()` to suppress repeated alerts for persistent risk without material changes. Updated `on_project_saved()` and `run_scheduled_scan()` signatures. |
| `paimana_agent/sync.py` | **Refactored** | Created abstract `AuthoritativeDataProvider` boundary interface with concrete implementations (`FileDataProvider`, `ApiDataProvider`, `MemoryDataProvider`), defined `ProviderUnavailableError`, and updated `PaimanaDataSync` to construct canonical snapshots and guard against fake data fabrication. |
| `paimana_agent/scheduler.py` | **Refactored** | Enhanced `Scheduler` to directly support `AuthoritativeDataProvider` objects and callable providers, handled `ProviderUnavailableError` gracefully with error logging, and passed `source="SCHEDULED_SCAN"` to `agent.run_scheduled_scan()`. |
| `tests/test_phase1_monitoring.py` | **Updated / Expanded** | Replaced preliminary tests with 12 comprehensive unit and integration tests strictly addressing all Phase 1 acceptance criteria. |
| `Reports/PHASE_1_REPORT.md` | **New** | Comprehensive technical report documenting architectural changes, flow, test results, limitations, and integration roadmap. |

---

## 3. Architecture & Conceptual Decoupling

### 3.1 Canonical Snapshot Model
Every snapshot ingested into the monitoring engine is assigned an immutable cryptographic fingerprint and provenance metadata:
- `project_id`: Unique project identifier (e.g., `NHAI-DEL-MUM-01`).
- `snapshot_id`: Deterministic ID formatted as `SNAP-{project_id}-{hash[:8]}`.
- `reporting_period`: Official reporting cycle (`YYYY-MM`).
- `observed_at`: Epoch timestamp when metrics were observed in the field.
- `recorded_at`: Epoch timestamp when snapshot was written to the store.
- `retrieved_at`: Epoch timestamp when data was fetched from provider.
- `source`: Explicit provenance (`PAIMANA_SYNC`, `USER_EDIT`, `IMPORT`, `SYSTEM_UPDATE`, `SCHEDULED_SCAN`).
- `source_record_id`: External primary key or sync cursor.
- `snapshot_hash`: Deterministic SHA-256 hash computed over normalized project payload.
- `schema_version`: Model versioning string (`1.0`).
- `freshness_state`: Discrete data freshness classification.
- `freshness_lag_months`: Calendar lag relative to evaluation timestamp.
- `payload`: Full raw project attributes.

### 3.2 Discrete Data Freshness Model
- **`FRESH`**: 0–1 month calendar lag between report period and current evaluation cycle.
- **`AGING`**: 2 months calendar lag; project is flagged for potential submission delay.
- **`STALE`**: $\ge 3$ months calendar lag; system issues explicit stale submission warning.
- **`UNAVAILABLE`**: Missing, invalid, or unparseable reporting date; freshness cannot be guaranteed.

### 3.3 Formal Separation of Core Monitoring Concepts
Phase 1 formally decouples monitoring concepts into separate data structures returned by `evaluate_project`:

1. **Current Risk State (`current_risk_state`)**:
   Captures current point-in-time risk:
   ```json
   {
     "risk_score": 78.4,
     "tier": "High",
     "cost_overrun_pct": 24.5,
     "slippage_months": 18.0,
     "combined_score": 75.0
   }
   ```
2. **Risk Change (`risk_change`)**:
   Tracks movement across successive evaluations:
   ```json
   {
     "prev_score": 62.1,
     "current_score": 78.4,
     "delta_score": 16.3,
     "prev_tier": "Medium",
     "current_tier": "High",
     "is_escalation": true,
     "is_jump": true,
     "is_transition": true
   }
   ```
3. **Material Data Change (`material_data_change`)**:
   Boolean flag indicating whether project core parameters mutated compared to previous snapshot.
4. **Operational Events (`events`)**:
   Discrete anomalies detected by rules (e.g., `COST_PROGRESS_MISMATCH`, `SCHEDULE_SLIPPAGE`). When `material_data_change` is `False`, `events` is empty (`[]`), preventing duplicate event churn.
5. **Outbound Alert (`alert`)**:
   Stakeholder notification decision. A project remaining at High risk with no material data change suppresses outbound alerts while remaining prominently visible in the risk registry.

---

## 4. Monitoring Flow

```
[PAIMANA Portal / MoSPI DB / User Edit / Batch Feed]
                     │
                     ▼
       AuthoritativeDataProvider (File / API / Memory)
                     │
                     ▼
       Canonical Snapshot Construction & SHA-256 Hashing
                     │
                     ▼
         Check Previous Snapshot in Store
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
  [Material Change]        [Unchanged Data]
         │                       │
         │ (Yes)                 │ (No)
         ▼                       ▼
  Run Expensive ML          Bypass ML & SHAP
  & SHAP Attribution        Reuse Validated Scores
  Record Change Check       Record Unmutated Check
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
          Detect Risk Transitions
       (prev_tier -> current_tier)
                     │
                     ▼
         Operational Event Engine
         (Suppressed if Unmutated)
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
  [Event Detected]         [Alert Decision]
         │                       │
         ▼                       ▼
  Trigger Agentic           Check Alert Escalation,
  Investigation             Jump, & Deduplication
  (Supervisor Loop)         (Suppress if Persistent)
                     │
                     ▼
    Persist Canonical Snapshot & Prediction State
                     │
                     ▼
      Continue Scheduled / Event Monitoring
```

---

## 5. Verification & Test Suite

The comprehensive unit test suite in `tests/test_phase1_monitoring.py` explicitly validates all 12 Phase 1 requirements:

| # | Test Function | Purpose / Validation | Result |
|---|---|---|---|
| 1 | `test_first_snapshot` | Verifies canonical fields, deterministic SHA-256 hash, FRESH state, and database persistence. | **PASSED** |
| 2 | `test_unchanged_snapshot` | Verifies identical submissions bypass ML/SHAP, log unmutated checks, and emit no duplicate events. | **PASSED** |
| 3 | `test_material_snapshot_change` | Verifies that financial or physical mutations trigger evaluation and update snapshot hashes. | **PASSED** |
| 4 | `test_stale_data` | Verifies reporting dates $\ge 3$ months behind are classified as STALE with warnings. | **PASSED** |
| 5 | `test_unavailable_data` | Verifies missing/unparseable reporting periods are classified as UNAVAILABLE with lag 999. | **PASSED** |
| 6 | `test_user_edit` | Verifies `on_project_saved()` correctly sets provenance source to `USER_EDIT`. | **PASSED** |
| 7 | `test_scheduled_scan` | Verifies `run_scheduled_scan()` sets `SCHEDULED_SCAN` provenance and provides batch error isolation. | **PASSED** |
| 8 | `test_duplicate_alert_suppression` | Verifies persistent high-risk projects do not generate repeated duplicate alerts. | **PASSED** |
| 9 | `test_genuine_risk_transition` | Verifies genuine risk escalations (Medium $\rightarrow$ High) immediately trigger outbound alerts. | **PASSED** |
| 10 | `test_event_triggering` | Verifies operational mismatches emit events and trigger investigations decoupled from alerts. | **PASSED** |
| 11 | `test_process_restart` | Verifies all snapshot metadata, checks, and prediction histories survive SQLite restarts. | **PASSED** |
| 12 | `test_provider_failure` | Verifies `ProviderUnavailableError` is raised on offline sources without fabricating fake data. | **PASSED** |

### Regression Testing Across All Phases
- **Phase 1 Test Suite**: 12/12 PASSED (11.14s)
- **All Phase Suites (`test_phase*.py`, Phases 1–15)**: 129/129 PASSED (13.40s)
- **Behavioral Test Suite (`test_agent_behavior.py`)**: 111/111 PASSED (18.90s)
- **Legacy Test Scripts (`test_agent.py`, `test_agent_v2.py`, `test_agent_v3.py`)**: ALL PASSED

---

## 6. Known Limitations & Remaining Integration Gaps

1. **Static Cadence in Continuous Polling**:
   - The scheduler polls on fixed intervals (e.g., 6 hours). Dynamic, adaptive polling frequencies based on project volatility or risk tiers can be explored in future scheduling optimizations.
2. **MoSPI PAIMANA API Authentication Standard**:
   - The `ApiDataProvider` supports Bearer tokens and standard REST headers. In production, enterprise OAuth2 token exchange with automatic token refreshes should be wired when the actual PAIMANA portal endpoint credentials are provided.
3. **Multi-Region Replica Synchronization**:
   - SQLite WAL mode handles local process concurrency cleanly, but large-scale enterprise deployments syncing thousands of concurrent projects will eventually benefit from a PostgreSQL/TimescaleDB backend for snapshots.

---

## 7. Conclusion

Phase 1 (Continuous Monitoring Hardening) is complete, robust, and verified. The monitoring engine is now snapshot-driven, computationally efficient, resistant to alert fatigue, resilient to provider failures, and strictly compliant with production-grade data integrity standards.
