-- ============================================================
-- PAIMANA — Project milestones (planned vs. actual dates)
-- Run AFTER add_projects.sql, against the same database:
--   psql -U postgres -d paimana_db -f add_milestones.sql
--
-- This version is SAFE TO RE-RUN (IF NOT EXISTS / ON CONFLICT),
-- and casts every date literal to ::date so PostgreSQL doesn't
-- resolve them as text through the UNION ALL chains below.
--
-- This is usually the single strongest predictor for a schedule-
-- delay model: how far behind (or ahead) each milestone actually
-- landed versus its planned date. The seed data below is synthetic,
-- same caveat as add_projects.sql — not real CUF submissions.
-- ============================================================

\c paimana_db

CREATE TABLE IF NOT EXISTS project_milestones (
  id                  BIGSERIAL PRIMARY KEY,
  project_id          BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  milestone_name      TEXT NOT NULL,             -- e.g. 'Foundation completion', 'Land acquisition'
  sequence_no         INTEGER NOT NULL,          -- order within the project, 1, 2, 3...
  planned_date        DATE NOT NULL,
  actual_date         DATE,                      -- NULL until the milestone is actually reached
  status              TEXT NOT NULL DEFAULT 'Pending'
                       CHECK (status IN ('Pending','In Progress','Achieved','Delayed')),
  delay_days          INTEGER GENERATED ALWAYS AS (
                         CASE WHEN actual_date IS NOT NULL
                              THEN (actual_date - planned_date)
                              ELSE NULL END
                       ) STORED,                 -- positive = late, negative = early, computed automatically
  remarks             TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, sequence_no)
);

DROP TRIGGER IF EXISTS trg_milestones_updated_at ON project_milestones;
CREATE TRIGGER trg_milestones_updated_at
BEFORE UPDATE ON project_milestones
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_milestones_project ON project_milestones (project_id);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON project_milestones (status);

-- ============================================================
-- Sample milestones — 4-5 per project, mixing on-time, early,
-- delayed, and still-pending milestones so a model sees both
-- healthy and at-risk patterns.
--
-- NOTE: every date literal is explicitly cast with ::date. Without
-- this, PostgreSQL resolves the UNION ALL column type as text
-- (since bare string literals are "unknown" type until matched
-- against a single INSERT ... VALUES target — which doesn't apply
-- here), and text -> date is not an implicit/assignment cast.
-- ============================================================

-- Sea Link Coastal Connector Phase 2 (Delayed overall)
INSERT INTO project_milestones (project_id, milestone_name, sequence_no, planned_date, actual_date, status, remarks)
SELECT id, 'Land acquisition & clearances', 1, '2019-09-30'::date, '2019-10-20'::date, 'Achieved', 'Minor delay in coastal clearance approval'
FROM projects WHERE project_code = 'PRJ-2019-014'
UNION ALL
SELECT id, 'Foundation & pier works', 2, '2020-12-31'::date, '2021-03-15'::date, 'Achieved', 'Marine construction window lost to monsoon'
FROM projects WHERE project_code = 'PRJ-2019-014'
UNION ALL
SELECT id, 'Main span erection', 3, '2022-06-30'::date, '2022-11-10'::date, 'Achieved', 'Steel girder supply chain delay'
FROM projects WHERE project_code = 'PRJ-2019-014'
UNION ALL
SELECT id, 'Approach road connectivity', 4, '2023-09-30'::date, '2024-02-28'::date, 'Achieved', 'Land acquisition dispute in one package'
FROM projects WHERE project_code = 'PRJ-2019-014'
UNION ALL
SELECT id, 'Toll systems & commissioning', 5, '2025-06-30'::date, NULL, 'In Progress', 'Final testing underway'
FROM projects WHERE project_code = 'PRJ-2019-014'
ON CONFLICT (project_id, sequence_no) DO NOTHING;

-- Himalayan Rail Arch Bridge (Completed, mostly on time)
INSERT INTO project_milestones (project_id, milestone_name, sequence_no, planned_date, actual_date, status, remarks)
SELECT id, 'Foundation works', 1, '2018-12-31'::date, '2018-12-20'::date, 'Achieved', 'Completed ahead of schedule'
FROM projects WHERE project_code = 'PRJ-2018-031'
UNION ALL
SELECT id, 'Pier construction', 2, '2020-06-30'::date, '2020-07-10'::date, 'Achieved', 'Negligible slippage'
FROM projects WHERE project_code = 'PRJ-2018-031'
UNION ALL
SELECT id, 'Arch closure', 3, '2021-12-31'::date, '2022-01-05'::date, 'Achieved', 'Weather-related short delay'
FROM projects WHERE project_code = 'PRJ-2018-031'
UNION ALL
SELECT id, 'Track laying & electrification', 4, '2023-03-31'::date, '2023-04-15'::date, 'Achieved', 'On schedule'
FROM projects WHERE project_code = 'PRJ-2018-031'
UNION ALL
SELECT id, 'Safety certification & inauguration', 5, '2023-08-31'::date, '2024-01-25'::date, 'Achieved', 'Extended safety trial runs'
FROM projects WHERE project_code = 'PRJ-2018-031'
ON CONFLICT (project_id, sequence_no) DO NOTHING;

-- National Expressway Corridor — Segment C (Critical Delay)
INSERT INTO project_milestones (project_id, milestone_name, sequence_no, planned_date, actual_date, status, remarks)
SELECT id, 'Land acquisition', 1, '2021-12-31'::date, '2022-05-20'::date, 'Achieved', 'Compensation disputes across 3 villages'
FROM projects WHERE project_code = 'PRJ-2021-007'
UNION ALL
SELECT id, 'Earthwork & embankment', 2, '2022-12-31'::date, '2023-08-15'::date, 'Achieved', 'Contractor mobilisation delay'
FROM projects WHERE project_code = 'PRJ-2021-007'
UNION ALL
SELECT id, 'Tunnel boring', 3, '2024-06-30'::date, NULL, 'Delayed', 'Unexpected geology, boring progress behind plan'
FROM projects WHERE project_code = 'PRJ-2021-007'
UNION ALL
SELECT id, 'Pavement & structures', 4, '2025-06-30'::date, NULL, 'Pending', 'Not yet started, dependent on tunnel completion'
FROM projects WHERE project_code = 'PRJ-2021-007'
UNION ALL
SELECT id, 'Commissioning', 5, '2025-03-31'::date, NULL, 'Pending', 'Original date now unachievable'
FROM projects WHERE project_code = 'PRJ-2021-007'
ON CONFLICT (project_id, sequence_no) DO NOTHING;

-- Interbasin Water Transfer Link — Stage 1 (Delayed)
INSERT INTO project_milestones (project_id, milestone_name, sequence_no, planned_date, actual_date, status, remarks)
SELECT id, 'Environmental clearance', 1, '2020-08-31'::date, '2020-11-30'::date, 'Achieved', 'Amendment required after initial review'
FROM projects WHERE project_code = 'PRJ-2020-022'
UNION ALL
SELECT id, 'Resettlement & rehabilitation', 2, '2021-12-31'::date, '2022-09-10'::date, 'Achieved', 'Compensation disbursal slower than planned'
FROM projects WHERE project_code = 'PRJ-2020-022'
UNION ALL
SELECT id, 'Canal lining — Reach 1', 3, '2023-12-31'::date, '2024-06-30'::date, 'Achieved', 'Monsoon working-season loss'
FROM projects WHERE project_code = 'PRJ-2020-022'
UNION ALL
SELECT id, 'Pumping station construction', 4, '2025-03-31'::date, NULL, 'In Progress', 'Equipment procurement ongoing'
FROM projects WHERE project_code = 'PRJ-2020-022'
UNION ALL
SELECT id, 'Canal lining — Reach 2 & commissioning', 5, '2026-12-31'::date, NULL, 'Pending', 'Not yet started'
FROM projects WHERE project_code = 'PRJ-2020-022'
ON CONFLICT (project_id, sequence_no) DO NOTHING;

-- Thermal Power Capacity Expansion Unit 5 (Ongoing, on track)
INSERT INTO project_milestones (project_id, milestone_name, sequence_no, planned_date, actual_date, status, remarks)
SELECT id, 'Civil works & foundation', 1, '2022-12-31'::date, '2022-12-18'::date, 'Achieved', 'Ahead of schedule'
FROM projects WHERE project_code = 'PRJ-2022-019'
UNION ALL
SELECT id, 'Boiler erection', 2, '2024-03-31'::date, '2024-04-05'::date, 'Achieved', 'Negligible slippage'
FROM projects WHERE project_code = 'PRJ-2022-019'
UNION ALL
SELECT id, 'Turbine installation', 3, '2025-06-30'::date, NULL, 'In Progress', 'Equipment delivered, installation underway'
FROM projects WHERE project_code = 'PRJ-2022-019'
UNION ALL
SELECT id, 'Cooling tower & auxiliary systems', 4, '2025-12-31'::date, NULL, 'Pending', 'Scheduled to start after turbine installation'
FROM projects WHERE project_code = 'PRJ-2022-019'
UNION ALL
SELECT id, 'Trial run & commissioning', 5, '2026-03-31'::date, NULL, 'Pending', 'On track per current plan'
FROM projects WHERE project_code = 'PRJ-2022-019'
ON CONFLICT (project_id, sequence_no) DO NOTHING;

-- ============================================================
-- Handy queries
-- ============================================================

-- Every milestone for one project, with delay in days
-- SELECT milestone_name, planned_date, actual_date, status, delay_days
-- FROM project_milestones
-- WHERE project_id = (SELECT id FROM projects WHERE project_code = 'PRJ-2021-007')
-- ORDER BY sequence_no;

-- Average milestone delay per project — a strong ML feature
-- SELECT p.project_name, ROUND(AVG(m.delay_days), 1) AS avg_delay_days, COUNT(*) AS milestones_achieved
-- FROM project_milestones m
-- JOIN projects p ON p.id = m.project_id
-- WHERE m.actual_date IS NOT NULL
-- GROUP BY p.project_name
-- ORDER BY avg_delay_days DESC;

-- Projects with an overdue pending/in-progress milestone right now
-- SELECT p.project_name, m.milestone_name, m.planned_date
-- FROM project_milestones m
-- JOIN projects p ON p.id = m.project_id
-- WHERE m.status IN ('Pending','In Progress') AND m.planned_date < CURRENT_DATE
-- ORDER BY m.planned_date;
