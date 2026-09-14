-- ============================================================
-- PAIMANA — Project tracking tables + sample data
-- Run against the existing database with:
--   psql -U postgres -d paimana_db -f add_projects.sql
--
-- This version is SAFE TO RE-RUN: table/trigger/index creation
-- uses IF NOT EXISTS, and all sample-data inserts use
-- ON CONFLICT DO NOTHING so re-running never errors out or
-- creates duplicate rows.
--
-- NOTE: The 5 project records below are illustrative/synthetic
-- example data for prototyping and ML pipeline testing — the
-- costs, dates, and progress figures are NOT verified real-world
-- figures. Replace with real, authorized CUF data before any
-- production or decision-making use.
-- ============================================================

\c paimana_db

-- ---------- Master project record ----------

CREATE TABLE IF NOT EXISTS projects (
  id                          BIGSERIAL PRIMARY KEY,
  project_code                TEXT NOT NULL UNIQUE,        -- e.g. 'PRJ-2024-001'
  project_name                TEXT NOT NULL,
  sector                      TEXT NOT NULL,                -- e.g. 'Transport & Logistics', 'Energy'
  department_id               INTEGER REFERENCES departments(id),
  implementing_agency         TEXT,
  state                       TEXT,
  approved_cost_cr            NUMERIC(12,2) NOT NULL,        -- ₹ crore
  revised_cost_cr             NUMERIC(12,2),
  cumulative_expenditure_cr   NUMERIC(12,2) DEFAULT 0,
  sanction_date                DATE,
  scheduled_completion_date   DATE,
  revised_completion_date     DATE,
  physical_progress_percent   NUMERIC(5,2) DEFAULT 0 CHECK (physical_progress_percent BETWEEN 0 AND 100),
  status                      TEXT NOT NULL DEFAULT 'Ongoing'
                               CHECK (status IN ('Not Started','Ongoing','Delayed','Critical Delay','On Hold','Completed')),
  is_synthetic                BOOLEAN NOT NULL DEFAULT TRUE, -- flags demo/seed data vs real CUF submissions
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_projects_updated_at ON projects;
CREATE TRIGGER trg_projects_updated_at
BEFORE UPDATE ON projects
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_projects_sector ON projects (sector);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects (status);
CREATE INDEX IF NOT EXISTS idx_projects_department ON projects (department_id);

-- ---------- Monthly progress snapshots (the real ML training signal —
-- a time series of cost/progress per project, per month) ----------

CREATE TABLE IF NOT EXISTS project_progress_updates (
  id                          BIGSERIAL PRIMARY KEY,
  project_id                  BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  report_month                DATE NOT NULL,                 -- convention: 1st of the month
  cumulative_expenditure_cr   NUMERIC(12,2),
  physical_progress_percent   NUMERIC(5,2) CHECK (physical_progress_percent BETWEEN 0 AND 100),
  status                      TEXT,
  remarks                     TEXT,
  reported_by                 UUID REFERENCES users(id),
  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, report_month)
);

CREATE INDEX IF NOT EXISTS idx_progress_project_month ON project_progress_updates (project_id, report_month);

-- ---------- AI/ML-generated risk scores (decision-support outputs,
-- not guaranteed facts) ----------

CREATE TABLE IF NOT EXISTS project_risk_scores (
  id                          BIGSERIAL PRIMARY KEY,
  project_id                  BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  cost_overrun_risk_percent   NUMERIC(5,2) CHECK (cost_overrun_risk_percent BETWEEN 0 AND 100),
  schedule_delay_risk_percent NUMERIC(5,2) CHECK (schedule_delay_risk_percent BETWEEN 0 AND 100),
  risk_level                  TEXT CHECK (risk_level IN ('Low','Medium','High','Critical')),
  model_version                TEXT NOT NULL DEFAULT 'seed-v0',
  generated_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_risk_project ON project_risk_scores (project_id);

-- ---------- One-time cleanup: this table had NO unique constraint
-- originally, so re-running the old script created duplicate rows.
-- Remove any duplicates (keep the earliest row per project+model)
-- before adding the constraint below. This is a no-op on a clean DB.
-- ----------

DELETE FROM project_risk_scores a
USING project_risk_scores b
WHERE a.id > b.id
  AND a.project_id = b.project_id
  AND a.model_version = b.model_version;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'project_risk_scores_project_model_key'
  ) THEN
    ALTER TABLE project_risk_scores
      ADD CONSTRAINT project_risk_scores_project_model_key UNIQUE (project_id, model_version);
  END IF;
END $$;

-- ============================================================
-- Sample data — 5 illustrative infrastructure projects
-- (synthetic figures, for prototyping / ML pipeline testing only)
-- ============================================================

INSERT INTO projects
  (project_code, project_name, sector, department_id, implementing_agency, state,
   approved_cost_cr, revised_cost_cr, cumulative_expenditure_cr,
   sanction_date, scheduled_completion_date, revised_completion_date,
   physical_progress_percent, status)
VALUES
  ('PRJ-2019-014', 'Sea Link Coastal Connector Phase 2', 'Transport & Logistics',
   (SELECT id FROM departments WHERE name = 'Road Transport & Highways'),
   'Metropolitan Region Development Authority', 'Maharashtra',
   17800.00, 21430.00, 19875.50,
   '2019-03-15', '2023-12-31', '2025-06-30',
   92.50, 'Delayed'),

  ('PRJ-2018-031', 'Himalayan Rail Arch Bridge', 'Transport & Logistics',
   (SELECT id FROM departments WHERE name = 'Railways'),
   'Northern Railway Construction Wing', 'Jammu & Kashmir',
   1486.00, 1652.00, 1652.00,
   '2018-01-10', '2023-08-31', '2024-01-25',
   100.00, 'Completed'),

  ('PRJ-2021-007', 'National Expressway Corridor — Segment C', 'Transport & Logistics',
   (SELECT id FROM departments WHERE name = 'Road Transport & Highways'),
   'National Highways Authority', 'Madhya Pradesh',
   9450.00, 11120.00, 6230.75,
   '2021-06-01', '2025-03-31', '2026-09-30',
   54.00, 'Critical Delay'),

  ('PRJ-2020-022', 'Interbasin Water Transfer Link — Stage 1', 'Water & Sanitation',
   (SELECT id FROM departments WHERE name = 'Jal Shakti'),
   'National Water Development Agency', 'Madhya Pradesh / Uttar Pradesh',
   4400.00, 5980.00, 3105.20,
   '2020-02-20', '2024-12-31', '2026-03-31',
   48.75, 'Delayed'),

  ('PRJ-2022-019', 'Thermal Power Capacity Expansion Unit 5', 'Energy',
   (SELECT id FROM departments WHERE name = 'Power'),
   'State Power Generation Corporation', 'Tamil Nadu',
   6200.00, 6200.00, 3560.00,
   '2022-04-01', '2026-03-31', NULL,
   57.00, 'Ongoing')
ON CONFLICT (project_code) DO NOTHING;

-- ---------- Sample monthly progress history (last 4 months, per project) ----------
-- Illustrates the time-series shape an ML model would train on.

INSERT INTO project_progress_updates (project_id, report_month, cumulative_expenditure_cr, physical_progress_percent, status, remarks)
SELECT id, '2026-03-01'::date, 18900.00, 88.00, 'Delayed', 'Approach road land acquisition delay in one package'
FROM projects WHERE project_code = 'PRJ-2019-014'
UNION ALL
SELECT id, '2026-04-01'::date, 19200.00, 89.50, 'Delayed', 'Marine works progressing; monsoon slowdown expected'
FROM projects WHERE project_code = 'PRJ-2019-014'
UNION ALL
SELECT id, '2026-05-01'::date, 19560.00, 91.00, 'Delayed', 'Toll plaza civil works nearing completion'
FROM projects WHERE project_code = 'PRJ-2019-014'
UNION ALL
SELECT id, '2026-06-01'::date, 19875.50, 92.50, 'Delayed', 'Final commissioning tests scheduled'
FROM projects WHERE project_code = 'PRJ-2019-014'

UNION ALL
SELECT id, '2026-03-01'::date, 5820.00, 46.00, 'Delayed', 'Tunnel boring behind schedule due to geology'
FROM projects WHERE project_code = 'PRJ-2021-007'
UNION ALL
SELECT id, '2026-04-01'::date, 5975.00, 48.50, 'Critical Delay', 'Contractor mobilisation dispute on Package 3'
FROM projects WHERE project_code = 'PRJ-2021-007'
UNION ALL
SELECT id, '2026-05-01'::date, 6080.00, 51.00, 'Critical Delay', 'Revised contractor deployment plan submitted'
FROM projects WHERE project_code = 'PRJ-2021-007'
UNION ALL
SELECT id, '2026-06-01'::date, 6230.75, 54.00, 'Critical Delay', 'Land acquisition for 2 remaining stretches pending'
FROM projects WHERE project_code = 'PRJ-2021-007'

UNION ALL
SELECT id, '2026-03-01'::date, 2850.00, 44.00, 'Delayed', 'Canal lining work slowed by monsoon forecast prep'
FROM projects WHERE project_code = 'PRJ-2020-022'
UNION ALL
SELECT id, '2026-04-01'::date, 2960.00, 45.75, 'Delayed', 'Environmental clearance amendment under review'
FROM projects WHERE project_code = 'PRJ-2020-022'
UNION ALL
SELECT id, '2026-05-01'::date, 3040.00, 47.25, 'Delayed', 'Pumping station equipment procurement in progress'
FROM projects WHERE project_code = 'PRJ-2020-022'
UNION ALL
SELECT id, '2026-06-01'::date, 3105.20, 48.75, 'Delayed', 'Resettlement compensation disbursal ongoing'
FROM projects WHERE project_code = 'PRJ-2020-022'

UNION ALL
SELECT id, '2026-03-01'::date, 3120.00, 51.00, 'Ongoing', 'Boiler erection on schedule'
FROM projects WHERE project_code = 'PRJ-2022-019'
UNION ALL
SELECT id, '2026-04-01'::date, 3280.00, 53.00, 'Ongoing', 'Turbine delivery received'
FROM projects WHERE project_code = 'PRJ-2022-019'
UNION ALL
SELECT id, '2026-05-01'::date, 3420.00, 55.25, 'Ongoing', 'Cooling tower civil works progressing'
FROM projects WHERE project_code = 'PRJ-2022-019'
UNION ALL
SELECT id, '2026-06-01'::date, 3560.00, 57.00, 'Ongoing', 'On track for scheduled milestones'
FROM projects WHERE project_code = 'PRJ-2022-019'
ON CONFLICT (project_id, report_month) DO NOTHING;

-- ---------- Sample seed risk scores (would normally be written by your ML pipeline) ----------

INSERT INTO project_risk_scores (project_id, cost_overrun_risk_percent, schedule_delay_risk_percent, risk_level, model_version)
SELECT id, 62.00, 71.00, 'High', 'seed-v0' FROM projects WHERE project_code = 'PRJ-2019-014'
UNION ALL
SELECT id, 8.00, 5.00, 'Low', 'seed-v0' FROM projects WHERE project_code = 'PRJ-2018-031'
UNION ALL
SELECT id, 87.00, 91.00, 'Critical', 'seed-v0' FROM projects WHERE project_code = 'PRJ-2021-007'
UNION ALL
SELECT id, 74.00, 68.00, 'High', 'seed-v0' FROM projects WHERE project_code = 'PRJ-2020-022'
UNION ALL
SELECT id, 22.00, 18.00, 'Low', 'seed-v0' FROM projects WHERE project_code = 'PRJ-2022-019'
ON CONFLICT (project_id, model_version) DO NOTHING;

-- ============================================================
-- Handy queries
-- ============================================================

-- Full project overview with department name
-- SELECT p.project_code, p.project_name, d.name AS ministry, p.sector, p.status,
--        p.approved_cost_cr, p.revised_cost_cr,
--        ROUND((p.revised_cost_cr - p.approved_cost_cr) / p.approved_cost_cr * 100, 1) AS cost_overrun_pct
-- FROM projects p LEFT JOIN departments d ON d.id = p.department_id
-- ORDER BY p.created_at DESC;

-- Time series for one project (what an ML model would train on)
-- SELECT report_month, cumulative_expenditure_cr, physical_progress_percent, status
-- FROM project_progress_updates
-- WHERE project_id = (SELECT id FROM projects WHERE project_code = 'PRJ-2021-007')
-- ORDER BY report_month;

-- Highest-risk projects right now
-- SELECT p.project_name, r.cost_overrun_risk_percent, r.schedule_delay_risk_percent, r.risk_level
-- FROM project_risk_scores r
-- JOIN projects p ON p.id = r.project_id
-- ORDER BY r.cost_overrun_risk_percent DESC;
