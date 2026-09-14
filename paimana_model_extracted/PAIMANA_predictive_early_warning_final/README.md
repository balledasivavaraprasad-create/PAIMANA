# PAIMANA Predictive Early Warning — Prototype Final

This package upgrades the previous feature-selection pipeline into a project-level predictive early-warning prototype. M (milestone risk) and I (implementation risk) are intentionally excluded because the current dataset does not contain sufficiently reliable milestone/management fields.

## Main outputs
- `data/3_final_project_health_scores.csv`: compact dashboard-ready project snapshot scores.
- `data/3_final_project_health_scores_all_columns.csv`: full analytical table with model outputs and engineered fields.
- `data/model_performance.csv`: temporal train/validation/test metrics.
- `data/model_manifest.json`: exact model features and scoring design.
- `models/`: LightGBM models and validation-only Platt probability calibrators.

## Risk design
T = 1-month schedule risk probability from the schedule ML model.
C = 1-month cost risk probability from the cost ML model.
P = progress health risk from expected-vs-actual progress, required-vs-actual velocity, and velocity deterioration.
F = stage-aware expenditure-vs-physical-progress efficiency risk plus deterioration and expenditure acceleration.

Current risk = 30% T + 30% C + 25% P + 10% F + 5% combined-model consistency signal.
Emerging risk captures risk velocity and acceleration. DPHIS = 78% current risk + 22% emerging risk.

The design deliberately uses bounded/robust transformations so extreme PAIMANA values do not dominate the score.

## Model validation
The labeled history is split chronologically: earliest months for training, following two months for validation, and latest three labeled months for a completely later holdout. LightGBM is regularized and uses early stopping. Probability calibration is fitted only on validation predictions.

## Why this is not simply a weighted average
The dashboard can show current risk, emerging risk, risk velocity, acceleration, confidence, data quality, risk transition, and the underlying T/C/P/F drivers. This is intended as decision support rather than a single opaque number.
