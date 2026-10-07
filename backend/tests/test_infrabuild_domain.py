from datetime import datetime, timezone, timedelta

from app.domain.availability import metric_payload, optional_metric
from app.services.data_quality_service import classify_freshness
from app.services.peer_intelligence_service import classify_peer_context, cohort_quality
from app.domain.enums import CohortQuality, DataFreshness, PeerClassification
from app.services.rbac import has_permission, product_roles_for
from app.services.snapshot_identity import compute_snapshot_hash, is_material_change


def test_zero_is_not_unknown():
    assert optional_metric(0) == 0.0
    assert optional_metric(None) is None
    missing = metric_payload(None, "insufficient_peer_data")
    assert missing["availability"] is False
    assert missing["value"] is None
    assert missing["reason"] == "insufficient_peer_data"


def test_snapshot_hash_stable_and_sensitive():
    project = {"project_id": "P1", "cost": {"original": 10, "revised": 12}}
    snap_a = {"physical_progress": 40.0, "financial_progress": 55.0, "report_period": "2026-09"}
    snap_b = {"physical_progress": 41.0, "financial_progress": 55.0, "report_period": "2026-09"}
    h1 = compute_snapshot_hash(project, snap_a)
    h2 = compute_snapshot_hash(project, snap_a)
    h3 = compute_snapshot_hash(project, snap_b)
    assert h1 == h2
    assert h1 != h3


def test_material_change_skips_identical_hash():
    prev = {"snapshot_hash": "abc", "report_period": "2026-09", "physical_progress": 40}
    curr = {"snapshot_hash": "abc", "report_period": "2026-09", "physical_progress": 40}
    changed, reason = is_material_change(prev, curr)
    assert changed is False
    assert reason == "no_material_change"


def test_material_change_new_period():
    prev = {"snapshot_hash": "abc", "report_period": "2026-08"}
    curr = {"snapshot_hash": "abc", "report_period": "2026-09"}
    changed, reason = is_material_change(prev, curr)
    assert changed is True
    assert reason == "new_report_period"


def test_freshness_null_is_unavailable():
    assert classify_freshness(None) == DataFreshness.UNAVAILABLE
    now = datetime.now(timezone.utc)
    assert classify_freshness(now - timedelta(days=2), now) == DataFreshness.FRESH
    assert classify_freshness(now - timedelta(days=20), now) == DataFreshness.STALE


def test_peer_quality_insufficient_not_zero_median():
    quality = cohort_quality(2, 8.0)
    assert quality == CohortQuality.INSUFFICIENT
    classification = classify_peer_context(72.0, [40.0, 42.0], quality)
    assert classification == PeerClassification.INSUFFICIENT_PEER_EVIDENCE


def test_peer_outlier_classification():
    quality = CohortQuality.HIGH_QUALITY
    classification = classify_peer_context(72.0, [40.0] * 12, quality)
    assert classification == PeerClassification.PROJECT_SPECIFIC_OUTLIER


def test_rbac_viewer_cannot_approve():
    user = {"role": "VIEWER", "username": "v"}
    roles = product_roles_for(user)
    assert has_permission(user, "projects:read")
    assert not has_permission(user, "investigations:approve")
    assert not has_permission(user, "thresholds:write")
    assert "viewer" in {r.value for r in roles}


def test_rbac_admin_can_approve():
    user = {"role": "ADMIN", "username": "admin"}
    assert has_permission(user, "investigations:approve")
    assert has_permission(user, "system:admin")
