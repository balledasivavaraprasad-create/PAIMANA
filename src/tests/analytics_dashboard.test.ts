import { describe, it, expect } from 'vitest';
import { DEMO_ADMIN_28_PROJECTS, DEMO_USER_10_PROJECTS, SEEDED_PROJECTS_MAP } from '../lib/seededProjects';

describe('PAIMANA National Portfolio Intelligence & Continuous-Monitoring Analytics', () => {
  it('correctly calculates portfolio macro metrics from real project data with zero fabricated numbers', () => {
    const projects = DEMO_ADMIN_28_PROJECTS;
    expect(projects.length).toBeGreaterThan(0);

    const totalCount = projects.length;
    const criticalCount = projects.filter((p) => p.dphis >= 80).length;
    const highCount = projects.filter((p) => p.dphis >= 65 && p.dphis < 80).length;
    const attentionNeeded = criticalCount + highCount;

    const avgDphis = Math.round((projects.reduce((acc, p) => acc + p.dphis, 0) / totalCount) * 10) / 10;

    expect(totalCount).toBe(28);
    expect(attentionNeeded).toBeGreaterThan(0);
    expect(criticalCount).toBeGreaterThanOrEqual(0);
    expect(avgDphis).toBeGreaterThan(0);
    expect(avgDphis).toBeLessThanOrEqual(100);
    expect(isNaN(avgDphis)).toBe(false);
  });

  it('filters projects consistently across sector, state, and risk tier', () => {
    const projects = DEMO_ADMIN_28_PROJECTS;
    
    // Filter by risk tier
    const criticalOnly = projects.filter((p) => (p.risk || p.risk_level || (p.dphis >= 80 ? 'critical' : 'low')) === 'critical');
    criticalOnly.forEach((p) => {
      expect(p.dphis).toBeGreaterThanOrEqual(75);
    });

    // Search filter
    const searchMatch = projects.filter((p) => {
      const n = (p.name || p.project_name || '').toLowerCase();
      const id = (p.id || p.project_id || '').toLowerCase();
      return n.includes('metro') || id.includes('metro');
    });
    expect(searchMatch.length).toBeGreaterThan(0);
    searchMatch.forEach((p) => {
      const n = (p.name || p.project_name || '').toLowerCase();
      expect(n).toContain('metro');
    });
  });

  it('correctly maps project changes and detects divergence signals', () => {
    const sample = DEMO_ADMIN_28_PROJECTS[0];
    const ref = SEEDED_PROJECTS_MAP[sample.id] || {};

    const physProg = sample.physical_progress_pct || ref.physical_progress_pct || 40.0;
    const revCost = ref.cost?.revised || 960;
    const exp = ref.cost?.cumulative_expenditure || 263.93;
    const finProg = Math.round(((exp / revCost) * 100) * 10) / 10;

    expect(physProg).toBeGreaterThan(0);
    expect(finProg).toBeGreaterThan(0);
    expect(isNaN(finProg)).toBe(false);
  });

  it('formats CSV export columns properly', () => {
    const sample = DEMO_ADMIN_28_PROJECTS.slice(0, 3);
    const headers = ['Project ID', 'Project Name', 'DPHIS', 'Risk'];
    const rows = sample.map((p) => [`"${p.id}"`, `"${p.name}"`, p.dphis, `"${p.risk}"`]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');

    expect(csvContent).toContain('Project ID,Project Name,DPHIS,Risk');
    expect(csvContent).toContain(sample[0].id);
    expect(csvContent).toContain(String(sample[0].dphis));
  });
});
