-- ============================================================
-- PAIMANA — Strip ALL derived/computed values, keep only the
-- 6 raw FlashReport CSV fields, for the 5 live projects.
-- Run with:  psql -U postgres -d paimana_db -f cleanup_strict_csv_only.sql
--
-- FlashReport_July_2026.csv's 6 real data columns:
--   project_id, project_name, original_cost_crores,
--   revised_cost_crores, expenditure_crores, physical_progress_percent
--
-- After this script, across projects / project_progress_updates /
-- ml_predictions for PRJ-2026-401..405, the ONLY non-null,
-- non-key values anywhere are:
--   projects.project_name, .approved_cost_cr, .revised_cost_cr,
--            .cumulative_expenditure_cr, .physical_progress_percent
--   project_progress_updates.cumulative_expenditure_cr,
--            .physical_progress_percent
--
-- ml_predictions rows for these 5 projects are nulled out entirely
-- (id / project_id / report_month / created_at are structural keys,
-- not data values, so they're left as-is).
--
-- This previously stopped at the projects/progress_updates level;
-- this version additionally nulls the ml_predictions columns that
-- were still arithmetic derivations (cost_overrun_pct,
-- expenditure_original_cost_pct, expenditure_revised_cost_pct,
-- progress_expenditure_gap_pct, remaining_progress_pct) — those
-- are computed, not raw CSV values, so per this instruction they
-- go to NULL too, to be filled only once your actual pipeline
-- computes/predicts them.
--
-- SCOPE: only the 5 live projects (PRJ-2026-401..405). Your 55
-- bulk training-data projects are untouched — say the word if you
-- want those nulled the same way too.
--
-- Safe to re-run.
-- ============================================================

\c paimana_db

UPDATE ml_predictions m
SET cost_overrun_pct               = NULL,
    expenditure_original_cost_pct  = NULL,
    expenditure_revised_cost_pct   = NULL,
    progress_expenditure_gap_pct   = NULL,
    remaining_progress_pct         = NULL
FROM projects p
WHERE m.project_id = p.id
  AND p.project_code IN ('PRJ-2026-401','PRJ-2026-402','PRJ-2026-403','PRJ-2026-404','PRJ-2026-405');

-- ---------- Verify ----------
-- SELECT p.project_code, p.project_name, p.approved_cost_cr, p.revised_cost_cr,
--        p.cumulative_expenditure_cr, p.physical_progress_percent
-- FROM projects p WHERE p.project_code LIKE 'PRJ-2026-4%' ORDER BY p.project_code;
--
-- SELECT * FROM ml_predictions m
-- JOIN projects p ON p.id = m.project_id
-- WHERE p.project_code LIKE 'PRJ-2026-4%';
