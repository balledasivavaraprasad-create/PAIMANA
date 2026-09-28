import pytest
from app.services.feature_service import engineer_features, FEATURE_COLUMNS
from app.ml.feature_engineering.financial import compute_financial_features
from app.ml.feature_engineering.schedule import compute_schedule_features, parse_date
from app.ml.feature_engineering.progress import compute_progress_features

def test_financial_features_formulas():
    project = {
        "cost": {"original": 2000.0, "revised": 2400.0}
    }
    snapshots = [
        {"snapshot_date": "2026-01-01", "cumulative_expenditure": 600.0},
        {"snapshot_date": "2026-02-01", "cumulative_expenditure": 750.0},
        {"snapshot_date": "2026-03-01", "cumulative_expenditure": 950.0},
    ]

    fin = compute_financial_features(project, snapshots)
    # cost_escalation = (2400 - 2000) / 2000 = 0.20
    assert fin["cost_escalation"] == 0.20
    # expenditure_ratio = 950 / 2400 = 0.3958
    assert fin["expenditure_ratio"] == pytest.approx(0.3958, abs=0.01)
    # monthly_burn_rate = average of delta (150 + 200) / 2 = 175.0
    assert fin["monthly_burn_rate"] == 175.0
    # cost_acceleration = 200 - 150 = 50.0
    assert fin["cost_acceleration"] == 50.0

def test_financial_features_no_snapshots():
    project = {"cost": {"original": 1000.0, "revised": 1100.0}}
    fin = compute_financial_features(project, [])
    assert fin["cost_escalation"] == 0.10
    assert fin["expenditure_ratio"] == 0.0
    assert fin["monthly_burn_rate"] == 0.0
    assert fin["cost_acceleration"] == 0.0

def test_schedule_features_formulas():
    project = {
        "schedule": {
            "original_start": "2024-01-01",
            "original_end": "2026-01-01",  # ~24.0 months
            "revised_end": "2026-07-01",   # ~6.0 months slip
        }
    }
    snapshots = [
        {"snapshot_date": "2026-03-01", "milestones": {"completed": 4, "delayed": 2, "pending": 4, "total": 10}}
    ]

    sched = compute_schedule_features(project, snapshots)
    assert sched["planned_duration_months"] > 23.0
    assert sched["deadline_slip_months"] > 5.5
    assert sched["schedule_gap_ratio"] > 0.20
    # milestone_delay_rate = 2 / 10 = 0.20
    assert sched["milestone_delay_rate"] == 0.20

def test_progress_features_stagnation():
    # 3 consecutive months with progress delta < 0.5%
    snapshots = [
        {"snapshot_date": "2026-01-01", "physical_progress": 20.0, "financial_progress": 35.0},
        {"snapshot_date": "2026-02-01", "physical_progress": 20.2, "financial_progress": 37.0},
        {"snapshot_date": "2026-03-01", "physical_progress": 20.4, "financial_progress": 40.0},
    ]

    prog = compute_progress_features(snapshots)
    assert prog["current_physical_progress"] == 20.4
    assert prog["current_financial_progress"] == 40.0
    assert prog["physical_financial_gap"] == 19.6  # 40 - 20.4
    assert prog["progress_velocity"] == 0.2  # 20.4 - 20.2
    assert prog["stagnation_months"] >= 2.0

def test_feature_engineering_full_pipeline_edge_cases():
    # 1. 100% progress project
    p_complete = {
        "project_id": "P_COMPLETED",
        "state": "Gujarat",
        "sector": "Power",
        "cost": {"original": 500.0, "revised": 500.0},
        "schedule": {"original_start": "2020-01-01", "original_end": "2023-01-01", "revised_end": "2023-01-01"}
    }
    snap_complete = [{
        "snapshot_date": "2023-01-01",
        "physical_progress": 100.0,
        "financial_progress": 100.0,
        "cumulative_expenditure": 500.0,
        "milestones": {"completed": 10, "delayed": 0, "pending": 0, "total": 10}
    }]
    feat_complete = engineer_features(p_complete, snap_complete)
    assert feat_complete["current_physical_progress"] == 100.0
    assert feat_complete["physical_financial_gap"] == 0.0
    assert feat_complete["cost_escalation"] == 0.0

    # 2. Mega project with zero expenditure (just started)
    p_mega = {
        "project_id": "P_MEGA",
        "state": "Maharashtra",
        "sector": "Urban Transit",
        "cost": {"original": 45000.0, "revised": 52000.0},
        "schedule": {"original_start": "2026-01-01", "original_end": "2031-01-01", "revised_end": "2032-06-01"}
    }
    feat_mega = engineer_features(p_mega, [])
    assert feat_mega["cost_escalation"] > 0.15
    assert feat_mega["expenditure_ratio"] == 0.0
    for col in FEATURE_COLUMNS:
        assert col in feat_mega
        assert isinstance(feat_mega[col], (int, float))
