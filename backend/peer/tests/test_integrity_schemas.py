"""Unit tests for PAIMANA Data Integrity & Reliability Schemas & Contracts (Phase DIR-A)."""
import time
import pytest

from peer.integrity.schemas import (
    CanonicalProjectIdentity,
    DataProvenanceRecord,
    DuplicateCandidate,
    DuplicateMatchLevel,
    FieldQualityReport,
    FieldQualityStatus,
    IdentityStatus,
    IntegrityEvaluationReport,
    NormalizationUnit,
    ProjectSnapshot,
    TemporalEligibility,
    ValidationResult,
    ValidationSeverity,
    ValidationStatus,
)


class TestCanonicalProjectIdentity:
    def test_canonical_identity_lifecycle_and_serialization(self):
        identity = CanonicalProjectIdentity(
            canonical_project_id="CAN-PRJ-001",
            source_project_id="NHAI-DL-001",
            project_name="Delhi-Amritsar Expressway Package 1",
            aliases=["NHAI-PKG1", "DA-EXP-01"],
            sector="Road Transport and Highways",
            project_type="Expressway",
            implementing_agency="NHAI",
            identity_status=IdentityStatus.VERIFIED,
            confidence_score=0.98,
        )

        d = identity.to_dict()
        assert d["canonical_project_id"] == "CAN-PRJ-001"
        assert d["source_project_id"] == "NHAI-DL-001"
        assert d["identity_status"] == "VERIFIED"
        assert len(d["aliases"]) == 2
        assert d["confidence_score"] == 0.98

        # Roundtrip
        reconstructed = CanonicalProjectIdentity.from_dict(d)
        assert reconstructed.canonical_project_id == identity.canonical_project_id
        assert reconstructed.identity_status == IdentityStatus.VERIFIED
        assert reconstructed.aliases == ["NHAI-PKG1", "DA-EXP-01"]
        assert reconstructed.implementing_agency == "NHAI"

    def test_canonical_identity_fallback_for_unknown_status(self):
        data = {
            "canonical_project_id": "CAN-002",
            "source_project_id": "RAW-002",
            "project_name": "Test Port",
            "identity_status": "NON_EXISTENT_STATUS",
        }
        reconstructed = CanonicalProjectIdentity.from_dict(data)
        assert reconstructed.identity_status == IdentityStatus.PROVISIONAL


class TestProjectSnapshot:
    def test_snapshot_distinct_timestamps_and_hashing(self):
        now_ts = time.time()
        snap = ProjectSnapshot(
            snapshot_id="SNAP-202403-001",
            canonical_project_id="CAN-PRJ-001",
            observation_date="2024-03-31",
            recorded_at=now_ts,
            source_updated_at="2024-04-05T10:00:00Z",
            ingested_at=now_ts - 100,
            original_cost=1500.0,
            revised_cost=1650.0,
            expenditure=800.0,
            physical_progress=55.0,
            financial_progress=48.5,
            cost_overrun_pct=10.0,
            time_overrun_pct=15.0,
            schedule_delay_months=6.0,
            planned_start_date="2020-01-01",
            planned_completion_date="2024-01-01",
            data_source="MOSPI",
        )

        # Check distinct timestamps
        assert snap.observation_date == "2024-03-31"
        assert snap.source_updated_at == "2024-04-05T10:00:00Z"
        assert snap.ingested_at < snap.recorded_at

        # Check hash calculation and verification
        assert len(snap.data_hash) == 64
        assert snap.verify_hash() is True

        # Check tampering detection
        snap.revised_cost = 9999.0
        assert snap.verify_hash() is False

    def test_snapshot_to_peer_record_interop(self):
        snap = ProjectSnapshot(
            snapshot_id="SNAP-002",
            canonical_project_id="CAN-002",
            observation_date="2023-12-31",
            original_cost=2000.0,
            revised_cost=2200.0,
            expenditure=1100.0,
            physical_progress=60.0,
            cost_overrun_pct=10.0,
            time_overrun_pct=5.0,
            schedule_delay_months=3.0,
        )
        identity = CanonicalProjectIdentity(
            canonical_project_id="CAN-002",
            source_project_id="SRC-002",
            project_name="Metro Line 3",
            sector="Urban Transport",
            project_type="Metro",
            implementing_agency="MMRC",
        )

        peer_rec = snap.to_peer_record(identity)
        assert peer_rec["project_code"] == "CAN-002"
        assert peer_rec["project_name"] == "Metro Line 3"
        assert peer_rec["sector"] == "Urban Transport"
        assert peer_rec["physical_progress"] == 60.0
        assert peer_rec["snapshot_date"] == "2023-12-31"

    def test_snapshot_dict_roundtrip(self):
        snap = ProjectSnapshot(
            snapshot_id="SNAP-003",
            canonical_project_id="CAN-003",
            observation_date="2024-01-31",
            original_cost=500.0,
            revised_cost=550.0,
            physical_progress=75.0,
        )
        d = snap.to_dict()
        reconstructed = ProjectSnapshot.from_dict(d)
        assert reconstructed.snapshot_id == snap.snapshot_id
        assert reconstructed.data_hash == snap.data_hash
        assert reconstructed.verify_hash() is True


class TestIntegrityEvaluationAndValidationResults:
    def test_validation_result_serialization(self):
        val = ValidationResult(
            rule_id="RULE-COST-01",
            field="expenditure",
            status=ValidationStatus.FAILED,
            severity=ValidationSeverity.ERROR,
            observed_value=2500.0,
            expected="expenditure <= revised_cost (2000.0)",
            message="Reported expenditure exceeds authorized revised cost",
        )
        d = val.to_dict()
        assert d["rule_id"] == "RULE-COST-01"
        assert d["status"] == "FAILED"
        assert d["severity"] == "ERROR"
        assert d["observed_value"] == 2500.0

    def test_field_quality_report(self):
        fqr = FieldQualityReport(
            field_name="physical_progress",
            status=FieldQualityStatus.VALID,
            score=1.0,
            details="Progress value is monotonically consistent and within [0, 100]",
        )
        d = fqr.to_dict()
        assert d["field_name"] == "physical_progress"
        assert d["status"] == "VALID"
        assert d["score"] == 1.0

    def test_duplicate_candidate(self):
        dc = DuplicateCandidate(
            canonical_project_id="CAN-001",
            candidate_project_id="NHAI-001-ALT",
            match_level=DuplicateMatchLevel.EXACT_MATCH,
            confidence_score=0.96,
            matching_criteria=["normalized_name", "sector", "agency", "location"],
            differing_criteria=[],
            recommended_action="MERGE_UNDER_CANONICAL_ID",
        )
        d = dc.to_dict()
        assert d["match_level"] == "EXACT_MATCH"
        assert d["confidence_score"] == 0.96
        assert len(d["matching_criteria"]) == 4

    def test_provenance_record(self):
        prov = DataProvenanceRecord(
            record_id="PROV-001",
            entity_type="ProjectSnapshot",
            entity_id="SNAP-001",
            source_system="MOSPI_OCR_INGEST",
            raw_payload_hash="a1b2c3d4e5f6",
            transformations=[
                {"step": "unit_normalization", "from": "LAKHS", "to": "CRORES"},
                {"step": "date_formatting", "output": "ISO8601"},
            ],
        )
        d = prov.to_dict()
        assert d["source_system"] == "MOSPI_OCR_INGEST"
        assert len(d["transformations"]) == 2

    def test_integrity_evaluation_report_aggregation(self):
        val = ValidationResult(
            rule_id="RULE-TEMP-01",
            field="observation_date",
            status=ValidationStatus.PASSED,
            severity=ValidationSeverity.INFO,
            observed_value="2024-03-31",
            expected="<= 2024-04-01",
            message="Observation date is within valid observation horizon",
        )
        fqr = FieldQualityReport(
            field_name="observation_date",
            status=FieldQualityStatus.VALID,
            score=1.0,
            details="Valid ISO date",
        )
        report = IntegrityEvaluationReport(
            canonical_project_id="CAN-001",
            snapshot_id="SNAP-001",
            is_valid=True,
            overall_score=0.99,
            temporal_eligibility=TemporalEligibility.ELIGIBLE,
            validation_results=[val],
            field_qualities={"observation_date": fqr},
            summary="All integrity checks passed successfully.",
        )
        d = report.to_dict()
        assert d["is_valid"] is True
        assert d["temporal_eligibility"] == "ELIGIBLE"
        assert len(d["validation_results"]) == 1
        assert d["field_qualities"]["observation_date"]["status"] == "VALID"
