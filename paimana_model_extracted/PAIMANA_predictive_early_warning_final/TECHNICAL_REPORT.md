# PAIMANA Predictive Early Warning — Technical Report

## 1. Scope
This prototype reuses the existing one-month-ahead cost, schedule and combined risk targets, while adding stage-aware progress and financial-health indicators. Milestone (M) and implementation (I) risk are intentionally omitted.

## 2. Leakage and generalization controls
- Model inputs exclude all `y_*` and `next_*` fields.
- Chronological holdout: later report months are held out from training.
- Early stopping uses a validation period only.
- Probability calibration uses validation predictions only.
- Stronger regularization and minimum leaf size reduce memorization.

## 3. Models
### cost_risk_1m
- Best iteration: 70
- Train ROC-AUC: 0.9955
- Validation ROC-AUC: 0.9964
- Test ROC-AUC: 0.9811
- Test F1: 0.9782
- Test PR-AUC: 0.9689
- Test Brier: 0.0115
- Train-test AUC gap: 0.0144

### schedule_risk_1m
- Best iteration: 9
- Train ROC-AUC: 0.9210
- Validation ROC-AUC: 0.7855
- Test ROC-AUC: 0.7861
- Test F1: 0.4293
- Test PR-AUC: 0.4634
- Test Brier: 0.1720
- Train-test AUC gap: 0.1349

### combined_risk_1m
- Best iteration: 45
- Train ROC-AUC: 0.9801
- Validation ROC-AUC: 0.9131
- Test ROC-AUC: 0.9224
- Test F1: 0.7919
- Test PR-AUC: 0.9109
- Test Brier: 0.1078
- Train-test AUC gap: 0.0577

## 4. DPHIS
Current risk uses T/C/P/F plus a small combined-model consistency signal. Emerging risk is derived from project-level risk velocity and acceleration and is bounded before being blended. Final DPHIS is 78% current risk + 22% emerging risk. Tiers: Low, Watch, Medium, High, Critical.

## 5. Interpretation
The score is an early-warning indicator. Officers should inspect the component risks, trend, confidence, and driver fields before taking action.
