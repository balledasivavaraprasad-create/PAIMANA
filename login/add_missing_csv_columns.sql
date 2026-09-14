-- ============================================================
-- PAIMANA — Add columns found in the CSVs but missing from the schema
-- Run with:  psql -U postgres -d paimana_db -f add_missing_csv_columns.sql
--
-- Cross-checked every column in FlashReport_July_2026.csv and
-- 2_feature_engineered_dataset.csv against the current schema.
-- These did not exist anywhere:
--
--   FlashReport CSV:            page, s_no
--   Feature-engineered CSV:     max_available_horizon, gap_to_next_snapshot,
--                                next_cost_overrun_pct,
--                                next_completion_revised_flag,
--                                next_schedule_slippage_months
--
-- NO new tables are created. page and s_no/sl_no both represent a
-- report row's serial position in a given monthly report, so they're
-- unified into one column (report_page, report_serial_no) on
-- project_progress_updates, since that's the table that's already
-- one-row-per-project-per-month. The 5 "next_*" / horizon columns are
-- per-snapshot engineered features, so they go on ml_predictions
-- alongside the rest.
--
-- ADD COLUMN with no DEFAULT automatically sets every existing row
-- to NULL, which also satisfies "only the 6 FlashReport columns get
-- sample values, everything else NULL" for these new columns too —
-- no separate UPDATE needed.
--
-- Safe to re-run (IF NOT EXISTS throughout).
-- ============================================================

\c paimana_db

ALTER TABLE project_progress_updates
  ADD COLUMN IF NOT EXISTS report_page      INTEGER,  -- from FlashReport CSV: page
  ADD COLUMN IF NOT EXISTS report_serial_no INTEGER;  -- from FlashReport CSV: s_no / feature CSV: sl_no

ALTER TABLE ml_predictions
  ADD COLUMN IF NOT EXISTS max_available_horizon         INTEGER,
  ADD COLUMN IF NOT EXISTS gap_to_next_snapshot           INTEGER,
  ADD COLUMN IF NOT EXISTS next_cost_overrun_pct          NUMERIC(10,4),
  ADD COLUMN IF NOT EXISTS next_completion_revised_flag   SMALLINT,
  ADD COLUMN IF NOT EXISTS next_schedule_slippage_months  NUMERIC(10,2);

-- ---------- Verify ----------
-- \d project_progress_updates
-- \d ml_predictions
-- SELECT report_page, report_serial_no FROM project_progress_updates
--   WHERE project_id IN (SELECT id FROM projects WHERE project_code LIKE 'PRJ-2026-4%');
