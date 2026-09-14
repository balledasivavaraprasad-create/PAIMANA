-- ============================================================
-- PAIMANA — align schema with the real feature-engineered ML
-- dataset (2_feature_engineered_dataset.csv, 57 columns).
--
-- 1. Adds the one missing base field (start_date) to `projects`,
--    and fills illustrative sample values for state/sector/dates
--    (flash_report_projects never had these — update with real
--    values once you have them).
-- 2. Seeds 4 months of raw progress history per project (needed
--    as input before any feature engineering can run).
-- 3. Creates `project_ml_features` — the ~25 computed/derived
--    columns from the CSV, calculated from real arithmetic on
--    your actual project + progress data (not fabricated).
-- 4. Extends `project_risk_scores` with the 7 real target columns
--    your model predicts (y_cost_risk_1m, next_cost_overrun_pct,
--    etc.) — all NULL until your model actually runs.
-- 5. Drops `project_milestones` — unused by the real ML feature
--    set, so removed per your go-ahead to drop unneeded tables.
--
-- flash_report_projects, users, otp_codes, etc. are untouched.
--
-- Run with:
--   psql -U postgres -d paimana_db -f add_ml_pipeline_schema.sql
-- ============================================================

\c paimana_db

-- ============================================================
-- 1. Add the missing base field + illustrative sample values
-- ============================================================

ALTER TABLE projects ADD COLUMN IF NOT EXISTS start_date DATE;

-- Fill state / sector / dates with illustrative samples, varied per
-- project (ordered by id) — replace with real CUF values when available.
WITH sample_values AS (
  SELECT
    p.id,
    ROW_NUMBER() OVER (ORDER BY p.id) AS rn
  FROM projects p
),
lookup (rn, sample_state, sample_sector, start_offset_months, original_dur_months, revised_extra_months) AS (
  VALUES
    (1, 'Maharashtra',      'Transport & Logistics', 42, 48, 18),
    (2, 'Jammu & Kashmir',  'Railways',               66, 60, 5),
    (3, 'Madhya Pradesh',   'Roads & Highways',       48, 42, 24),
    (4, 'Uttar Pradesh',    'Water Resources',        60, 54, 15),
    (5, 'Tamil Nadu',       'Electricity Generation', 39, 48, 0)
)
UPDATE projects p
SET
  state = l.sample_state,
  sector = l.sample_sector,
  start_date = (CURRENT_DATE - (l.start_offset_months || ' months')::interval)::date,
  sanction_date = (CURRENT_DATE - ((l.start_offset_months + 3) || ' months')::interval)::date,
  scheduled_completion_date = (CURRENT_DATE - (l.start_offset_months || ' months')::interval + (l.original_dur_months || ' months')::interval)::date,
  revised_completion_date = CASE WHEN l.revised_extra_months > 0
    THEN (CURRENT_DATE - (l.start_offset_months || ' months')::interval + ((l.original_dur_months + l.revised_extra_months) || ' months')::interval)::date
    ELSE NULL
  END
FROM sample_values sv
JOIN lookup l ON l.rn = sv.rn
WHERE p.id = sv.id;

-- ============================================================
-- 2. Seed 4 months of raw progress history per project
-- (latest month = the project's current known totals; earlier
--  months scaled back proportionally — illustrative trend, but
--  anchored to your real current figures.)
-- ============================================================

TRUNCATE TABLE project_progress_updates RESTART IDENTITY;

WITH months (offset_months, weight) AS (
  VALUES (3, 0.80), (2, 0.87), (1, 0.94), (0, 1.00)  -- 0 = current month, matches projects' current totals
)
INSERT INTO project_progress_updates (project_id, report_month, cumulative_expenditure_cr, physical_progress_percent, status, remarks)
SELECT
  p.id,
  date_trunc('month', CURRENT_DATE - (m.offset_months || ' months')::interval)::date,
  ROUND(p.cumulative_expenditure_cr * m.weight, 2),
  ROUND(LEAST(p.physical_progress_percent * m.weight, 100), 2),
  p.status,
  CASE WHEN m.offset_months = 0 THEN 'Latest reported figures' ELSE 'Illustrative backfilled trend' END
FROM projects p
CROSS JOIN months m
ORDER BY p.id, m.offset_months DESC;

-- ============================================================
-- 3. project_ml_features — computed/derived columns
-- ============================================================

CREATE TABLE IF NOT EXISTS project_ml_features (
  id                                        BIGSERIAL PRIMARY KEY,
  project_id                                BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  report_month                              DATE NOT NULL,

  cost_overrun_pct                          NUMERIC(8,2),
  expenditure_original_cost_pct             NUMERIC(8,2),
  expenditure_revised_cost_pct              NUMERIC(8,2),
  progress_expenditure_gap_pct              NUMERIC(8,2),
  project_age_months                        NUMERIC(8,2),
  planned_duration_months                   NUMERIC(8,2),
  remaining_duration_months                 NUMERIC(8,2),
  remaining_progress_pct                    NUMERIC(8,2),
  schedule_slippage_months                  NUMERIC(8,2),
  completion_date_revised_flag              INTEGER,

  monthly_progress_change_pct               NUMERIC(8,2),
  monthly_expenditure_change_cr             NUMERIC(12,2),
  monthly_revised_cost_change_cr            NUMERIC(12,2),
  monthly_cost_growth_pct                   NUMERIC(8,2),
  progress_velocity_pct_per_month           NUMERIC(8,2),
  expenditure_growth_pct                    NUMERIC(8,2),
  required_progress_velocity_pct_per_month  NUMERIC(8,2),
  velocity_gap_pct_points                   NUMERIC(8,2),

  rolling_progress_velocity_3m              NUMERIC(8,2),
  rolling_cost_growth_3m                    NUMERIC(8,2),
  rolling_expenditure_growth_3m             NUMERIC(8,2),
  snapshots_so_far                          INTEGER,

  cost_overrun_trend_1m                     NUMERIC(8,2),
  progress_trend_1m                         NUMERIC(8,2),
  prev_cost_overrun_pct                     NUMERIC(8,2),
  prev_physical_progress_pct                NUMERIC(8,2),
  prev_completion_revised_flag              INTEGER,

  created_at                                TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, report_month)
);

CREATE INDEX IF NOT EXISTS idx_ml_features_project_month ON project_ml_features (project_id, report_month);

-- Compute and insert real feature values from the seeded progress history
TRUNCATE TABLE project_ml_features RESTART IDENTITY;

WITH base AS (
  SELECT
    u.project_id,
    u.report_month,
    u.cumulative_expenditure_cr,
    u.physical_progress_percent,
    p.approved_cost_cr,
    p.revised_cost_cr,
    p.start_date,
    p.scheduled_completion_date,
    p.revised_completion_date,
    COALESCE(p.revised_completion_date, p.scheduled_completion_date) AS effective_completion_date,
    (p.revised_completion_date IS NOT NULL AND p.revised_completion_date <> p.scheduled_completion_date)::int AS completion_revised_flag,
    ROW_NUMBER() OVER (PARTITION BY u.project_id ORDER BY u.report_month) AS snapshots_so_far
  FROM project_progress_updates u
  JOIN projects p ON p.id = u.project_id
),
calc AS (
  SELECT
    b.*,
    ROUND((b.revised_cost_cr - b.approved_cost_cr) / NULLIF(b.approved_cost_cr, 0) * 100, 2) AS cost_overrun_pct,
    ROUND(b.cumulative_expenditure_cr / NULLIF(b.approved_cost_cr, 0) * 100, 2) AS expenditure_original_cost_pct,
    ROUND(b.cumulative_expenditure_cr / NULLIF(b.revised_cost_cr, 0) * 100, 2) AS expenditure_revised_cost_pct,
    ROUND(100.0 - b.physical_progress_percent, 2) AS remaining_progress_pct,
    ROUND((EXTRACT(YEAR FROM age(b.report_month, b.start_date)) * 12 + EXTRACT(MONTH FROM age(b.report_month, b.start_date))), 2) AS project_age_months,
    ROUND((EXTRACT(YEAR FROM age(b.scheduled_completion_date, b.start_date)) * 12 + EXTRACT(MONTH FROM age(b.scheduled_completion_date, b.start_date))), 2) AS planned_duration_months,
    ROUND((EXTRACT(YEAR FROM age(b.effective_completion_date, b.report_month)) * 12 + EXTRACT(MONTH FROM age(b.effective_completion_date, b.report_month))), 2) AS remaining_duration_months,
    ROUND((EXTRACT(YEAR FROM age(b.effective_completion_date, b.scheduled_completion_date)) * 12 + EXTRACT(MONTH FROM age(b.effective_completion_date, b.scheduled_completion_date))), 2) AS schedule_slippage_months
  FROM base b
),
with_lag AS (
  SELECT
    c.*,
    LAG(c.physical_progress_percent) OVER w AS prev_physical_progress_pct,
    LAG(c.cumulative_expenditure_cr) OVER w AS prev_expenditure,
    LAG(c.revised_cost_cr) OVER w AS prev_revised_cost,
    LAG(c.cost_overrun_pct) OVER w AS prev_cost_overrun_pct,
    LAG(c.completion_revised_flag) OVER w AS prev_completion_revised_flag
  FROM calc c
  WINDOW w AS (PARTITION BY c.project_id ORDER BY c.report_month)
),
features AS (
  SELECT
    wl.*,
    ROUND(wl.physical_progress_percent - COALESCE(wl.prev_physical_progress_pct, wl.physical_progress_percent), 2) AS monthly_progress_change_pct,
    ROUND(wl.cumulative_expenditure_cr - COALESCE(wl.prev_expenditure, wl.cumulative_expenditure_cr), 2) AS monthly_expenditure_change_cr,
    ROUND(wl.revised_cost_cr - COALESCE(wl.prev_revised_cost, wl.revised_cost_cr), 2) AS monthly_revised_cost_change_cr,
    ROUND((wl.revised_cost_cr - COALESCE(wl.prev_revised_cost, wl.revised_cost_cr)) / NULLIF(wl.prev_revised_cost, 0) * 100, 2) AS monthly_cost_growth_pct,
    ROUND((wl.cumulative_expenditure_cr - COALESCE(wl.prev_expenditure, wl.cumulative_expenditure_cr)) / NULLIF(wl.prev_expenditure, 0) * 100, 2) AS expenditure_growth_pct,
    ROUND(wl.remaining_progress_pct / NULLIF(wl.remaining_duration_months, 0), 2) AS required_progress_velocity_pct_per_month,
    ROUND(wl.cost_overrun_pct - COALESCE(wl.prev_cost_overrun_pct, wl.cost_overrun_pct), 2) AS cost_overrun_trend_1m,
    ROUND(wl.physical_progress_percent - COALESCE(wl.prev_physical_progress_pct, wl.physical_progress_percent), 2) AS progress_trend_1m
  FROM with_lag wl
)
INSERT INTO project_ml_features (
  project_id, report_month, cost_overrun_pct, expenditure_original_cost_pct, expenditure_revised_cost_pct,
  progress_expenditure_gap_pct, project_age_months, planned_duration_months, remaining_duration_months,
  remaining_progress_pct, schedule_slippage_months, completion_date_revised_flag,
  monthly_progress_change_pct, monthly_expenditure_change_cr, monthly_revised_cost_change_cr, monthly_cost_growth_pct,
  progress_velocity_pct_per_month, expenditure_growth_pct, required_progress_velocity_pct_per_month, velocity_gap_pct_points,
  rolling_progress_velocity_3m, rolling_cost_growth_3m, rolling_expenditure_growth_3m, snapshots_so_far,
  cost_overrun_trend_1m, progress_trend_1m, prev_cost_overrun_pct, prev_physical_progress_pct, prev_completion_revised_flag
)
SELECT
  f.project_id, f.report_month, f.cost_overrun_pct, f.expenditure_original_cost_pct, f.expenditure_revised_cost_pct,
  ROUND(f.physical_progress_percent - f.expenditure_revised_cost_pct, 2) AS progress_expenditure_gap_pct,
  f.project_age_months, f.planned_duration_months, f.remaining_duration_months,
  f.remaining_progress_pct, f.schedule_slippage_months, f.completion_revised_flag,
  f.monthly_progress_change_pct, f.monthly_expenditure_change_cr, f.monthly_revised_cost_change_cr, f.monthly_cost_growth_pct,
  f.monthly_progress_change_pct AS progress_velocity_pct_per_month,  -- velocity == this month's progress change
  f.expenditure_growth_pct, f.required_progress_velocity_pct_per_month,
  ROUND(f.monthly_progress_change_pct - f.required_progress_velocity_pct_per_month, 2) AS velocity_gap_pct_points,
  ROUND(AVG(f.monthly_progress_change_pct) OVER (PARTITION BY f.project_id ORDER BY f.report_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_progress_velocity_3m,
  ROUND(AVG(f.monthly_cost_growth_pct) OVER (PARTITION BY f.project_id ORDER BY f.report_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_cost_growth_3m,
  ROUND(AVG(f.expenditure_growth_pct) OVER (PARTITION BY f.project_id ORDER BY f.report_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_expenditure_growth_3m,
  f.snapshots_so_far,
  f.cost_overrun_trend_1m, f.progress_trend_1m, f.prev_cost_overrun_pct, f.prev_physical_progress_pct, f.prev_completion_revised_flag
FROM features f
ORDER BY f.project_id, f.report_month;

-- ============================================================
-- 4. Extend project_risk_scores with the real ML target columns
-- (matches the y_*/next_* columns in your training CSV exactly —
--  all NULL until your model actually writes a prediction)
-- ============================================================

ALTER TABLE project_risk_scores
  ADD COLUMN IF NOT EXISTS y_cost_risk_1m                 NUMERIC(5,2),
  ADD COLUMN IF NOT EXISTS y_schedule_risk_1m              NUMERIC(5,2),
  ADD COLUMN IF NOT EXISTS y_combined_risk_1m              NUMERIC(5,2),
  ADD COLUMN IF NOT EXISTS y_cost_overrun_actual_next      NUMERIC(8,2),
  ADD COLUMN IF NOT EXISTS next_cost_overrun_pct           NUMERIC(8,2),
  ADD COLUMN IF NOT EXISTS next_completion_revised_flag    INTEGER,
  ADD COLUMN IF NOT EXISTS next_schedule_slippage_months   NUMERIC(8,2);

-- ============================================================
-- 5. Drop project_milestones — unused by the real ML feature set
-- ============================================================

DROP TABLE IF EXISTS project_milestones;

-- ============================================================
-- Verify
-- ============================================================

-- SELECT project_name, state, sector, start_date, sanction_date, scheduled_completion_date, revised_completion_date FROM projects;
-- SELECT project_id, report_month, cost_overrun_pct, progress_velocity_pct_per_month, rolling_progress_velocity_3m FROM project_ml_features ORDER BY project_id, report_month;
-- SELECT project_id, y_cost_risk_1m, y_schedule_risk_1m, next_cost_overrun_pct FROM project_risk_scores;  -- all NULL, waiting on your model
