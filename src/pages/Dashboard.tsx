import React from 'react';
import type { Page } from '../App';
import GlassCard from '../components/GlassCard';
import MetricCard from '../components/MetricCard';
import RiskBadge, { RiskLevel } from '../components/RiskBadge';
import DataTable, { Column } from '../components/DataTable';

interface Props {
  onNavigate: (page: Page, projectId?: string) => void;
}

interface AttentionProject {
  id: string;
  name: string;
  ministry: string;
  state: string;
  dphis: number;
  risk: RiskLevel;
  change: string;
  cost: string;
  delay: string;
}

const attentionProjects: AttentionProject[] = [
  { id: 'P1024', name: 'NH-48 Expansion, Agra-Lucknow', ministry: 'Road Transport & Highways', state: 'Uttar Pradesh', dphis: 91, risk: 'critical', change: '+9', cost: '₹4,218 Cr', delay: '28 mo' },
  { id: 'P0847', name: 'Metro Rail Phase III', ministry: 'Housing & Urban Affairs', state: 'Tamil Nadu', dphis: 84, risk: 'critical', change: '+6', cost: '₹12,450 Cr', delay: '14 mo' },
  { id: 'P1156', name: 'Solar Energy Grid, Jaisalmer', ministry: 'New & Renewable Energy', state: 'Rajasthan', dphis: 78, risk: 'high', change: '+4', cost: '₹6,820 Cr', delay: '11 mo' },
  { id: 'P0392', name: 'Port Modernisation Project', ministry: 'Ports, Shipping & Waterways', state: 'Andhra Pradesh', dphis: 76, risk: 'high', change: '+3', cost: '₹3,190 Cr', delay: '9 mo' },
  { id: 'P0771', name: 'Broad Gauge Conversion, NE', ministry: 'Railways', state: 'Bihar', dphis: 74, risk: 'high', change: '+5', cost: '₹2,870 Cr', delay: '18 mo' },
];

const stateRiskSummary = [
  { state: 'Uttar Pradesh', projects: 67, dphis: 91, risk: 'critical' as RiskLevel, cost: '₹42,180 Cr' },
  { state: 'Tamil Nadu', projects: 28, dphis: 84, risk: 'critical' as RiskLevel, cost: '₹38,450 Cr' },
  { state: 'Rajasthan', projects: 38, dphis: 78, risk: 'high' as RiskLevel, cost: '₹26,820 Cr' },
  { state: 'Andhra Pradesh', projects: 24, dphis: 76, risk: 'high' as RiskLevel, cost: '₹18,190 Cr' },
  { state: 'Bihar', projects: 23, dphis: 74, risk: 'high' as RiskLevel, cost: '₹14,870 Cr' },
  { state: 'Maharashtra', projects: 52, dphis: 45, risk: 'low' as RiskLevel, cost: '₹57,840 Cr' },
  { state: 'Gujarat', projects: 22, dphis: 32, risk: 'low' as RiskLevel, cost: '₹28,120 Cr' },
  { state: 'Assam & NE', projects: 15, dphis: 55, risk: 'moderate' as RiskLevel, cost: '₹15,410 Cr' },
];

function GeographicRiskOverview({ onNavigate }: { onNavigate: (page: Page, id?: string) => void }) {
  const dotColor = (risk: RiskLevel) => {
    if (risk === 'critical') return 'var(--risk-critical)';
    if (risk === 'high') return 'var(--risk-high)';
    if (risk === 'moderate') return 'var(--risk-moderate)';
    return 'var(--risk-low)';
  };

  return (
    <GlassCard variant="medium" padding={20} className="flex flex-col h-full space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold font-display text-[var(--text-primary)]">Geographic Risk Telemetry</h3>
          <p className="text-xs text-[var(--text-muted)]">State-wise project density & predictive DPHIS levels</p>
        </div>
        <div className="flex items-center gap-3">
          {(['critical', 'high', 'moderate', 'low'] as RiskLevel[]).map(r => (
            <div key={r} className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full" style={{ background: dotColor(r) }} />
              <span className="text-[10px] capitalize text-[var(--text-muted)]">{r}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 flex-1 overflow-y-auto max-h-[340px] pr-1">
        {stateRiskSummary.map(s => (
          <div
            key={s.state}
            onClick={() => onNavigate('projects')}
            className="p-3 rounded-xl bg-[var(--surface-sunken)] border border-[var(--border-hairline)] hover:border-[var(--accent)] transition-all cursor-pointer space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-[var(--text-primary)]">{s.state}</span>
              <RiskBadge level={s.risk} />
            </div>
            <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] font-mono-data">
              <span>{s.projects} Projects</span>
              <span className="font-bold text-[var(--text-primary)]">DPHIS {s.dphis}</span>
            </div>
            <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${s.dphis}%`, background: dotColor(s.risk) }}
              />
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  );
}

export default function Dashboard({ onNavigate }: Props) {
  const riskData = [
    { label: 'Critical', count: 142, pct: 16.8, color: 'var(--risk-critical)' },
    { label: 'High Risk', count: 203, pct: 24.0, color: 'var(--risk-high)' },
    { label: 'Moderate', count: 287, pct: 33.9, color: 'var(--risk-moderate)' },
    { label: 'Low Risk', count: 215, pct: 25.4, color: 'var(--risk-low)' },
  ];

  const columns: Column<AttentionProject>[] = [
    { key: 'id', header: 'Project ID', render: row => <span className="font-mono-data font-bold text-[var(--accent)]">{row.id}</span> },
    { key: 'name', header: 'Project Name', render: row => <span className="font-semibold text-[var(--text-primary)]">{row.name}</span> },
    { key: 'ministry', header: 'Ministry', render: row => <span className="text-[var(--text-secondary)]">{row.ministry}</span> },
    { key: 'state', header: 'State', render: row => <span className="text-[var(--text-secondary)]">{row.state}</span> },
    {
      key: 'dphis',
      header: 'DPHIS Score',
      render: row => <span className="font-mono-data font-bold text-sm text-[var(--risk-critical)]">{row.dphis}</span>,
    },
    { key: 'risk', header: 'Risk Level', render: row => <RiskBadge level={row.risk} /> },
    { key: 'change', header: '30d Trend', render: row => <span className="text-red-500 font-semibold">{row.change}</span> },
    { key: 'cost', header: 'Est Cost', render: row => <span className="font-mono-data text-[var(--text-primary)]">{row.cost}</span> },
    { key: 'delay', header: 'Schedule Slip', render: row => <span className="text-amber-500 font-medium">{row.delay}</span> },
  ];

  return (
    <div className="space-y-6">
      {/* Top Welcome Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold font-display tracking-tight text-[var(--text-primary)]">
            Executive Portfolio Overview
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            Central Sector Infrastructure Projects · Automated Predictive Assessment
          </p>
        </div>

        <button
          onClick={() => onNavigate('analytics')}
          className="px-4 py-2 rounded-xl bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white text-xs font-semibold shadow-md transition-all cursor-pointer self-start sm:self-auto"
        >
          View Risk Analytics →
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        <MetricCard label="Total Monitored" value="1,842" sub="Active infrastructure" />
        <MetricCard label="Portfolio Value" value="₹14.8L Cr" sub="Revised outlay" />
        <MetricCard label="Critical Risk" value="42" accent="var(--risk-critical)" sub="+6 this month" trend="up" />
        <MetricCard label="High Risk" value="118" accent="var(--risk-high)" sub="+14 this month" trend="up" />
        <MetricCard label="Interventions" value="28" accent="var(--risk-critical)" sub="Action required" trend="up" />
        <MetricCard label="Portfolio Health" value="73/100" sub="-3 pts last month" trend="up" />
        <MetricCard label="Cost Exposure" value="₹1.84L Cr" accent="var(--risk-high)" sub="12.4% total budget" trend="up" />
        <MetricCard label="Avg Schedule Slip" value="14.2 mo" accent="var(--risk-moderate)" sub="Across active delay" />
      </div>

      {/* Hero AI Portfolio Insight Banner */}
      <GlassCard variant="hero" padding={24} className="relative overflow-hidden border-[var(--accent-soft)]">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-[var(--accent-soft)] border border-[var(--accent)] text-[var(--accent)] flex items-center justify-center flex-shrink-0">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--accent)] font-mono-data">
                PAIMANA AI · Portfolio Insight
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-sunken)] text-[var(--text-muted)] border border-[var(--border-hairline)]">
                Live Evidence Digest
              </span>
            </div>

            <p className="text-sm text-[var(--text-primary)] leading-relaxed">
              <strong className="font-semibold text-[var(--accent)]">17 projects</strong> show rapidly increasing risk velocity this month, primarily driven by schedule slippage and expenditure-progress divergence. NH-48 Expansion (<strong className="underline decoration-red-500 cursor-pointer" onClick={() => onNavigate('projects', 'P1024')}>P1024</strong>) has reached a critical DPHIS score of <strong className="text-red-500 font-mono-data">91</strong> requiring immediate ministry intervention.
            </p>

            <div className="flex items-center gap-4 mt-3">
              <button
                onClick={() => onNavigate('investigation', 'P1024')}
                className="text-xs font-semibold text-[var(--accent)] hover:underline cursor-pointer flex items-center gap-1"
              >
                Launch Investigation on P1024 →
              </button>
              <button
                onClick={() => onNavigate('alerts')}
                className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:underline cursor-pointer"
              >
                View all 14 elevated alerts
              </button>
            </div>
          </div>

          <div className="hidden lg:flex flex-col gap-1.5 border-l border-[var(--border-hairline)] pl-6 flex-shrink-0 text-right">
            <div className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">Core Workflow</div>
            <div className="text-xs font-mono-data text-[var(--text-secondary)]">Predict → Explain</div>
            <div className="text-xs font-mono-data text-[var(--accent)] font-bold">Investigate → Intervene</div>
          </div>
        </div>
      </GlassCard>

      {/* Main Grid: Telemetry & Risk Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <GeographicRiskOverview onNavigate={onNavigate} />
        </div>

        <GlassCard variant="medium" padding={20} className="flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-sm font-semibold font-display text-[var(--text-primary)] mb-1">Portfolio Risk Breakdown</h3>
            <p className="text-xs text-[var(--text-muted)]">Percentage share by DPHIS category</p>
          </div>

          {/* Stacked Risk Bar */}
          <div className="h-3 rounded-full overflow-hidden flex bg-[var(--surface-sunken)] p-0.5 border border-[var(--border-hairline)]">
            {riskData.map(r => (
              <div key={r.label} style={{ width: `${r.pct}%`, background: r.color }} className="h-full first:rounded-l-full last:rounded-r-full" />
            ))}
          </div>

          <div className="space-y-2.5">
            {riskData.map(r => (
              <div key={r.label} className="flex items-center justify-between text-xs p-2 rounded-lg bg-[var(--surface-sunken)] border border-[var(--border-hairline)]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: r.color }} />
                  <span className="font-medium text-[var(--text-primary)]">{r.label}</span>
                </div>
                <div className="flex items-center gap-3 font-mono-data">
                  <span className="font-bold text-[var(--text-primary)]">{r.count}</span>
                  <span className="text-[10px] text-[var(--text-muted)]">{r.pct}%</span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Projects Requiring Immediate Attention Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold font-display text-[var(--text-primary)]">Projects Requiring Immediate Attention</h3>
            <p className="text-xs text-[var(--text-muted)]">Ranked by DPHIS risk severity & acceleration</p>
          </div>
          <button
            onClick={() => onNavigate('projects')}
            className="text-xs font-semibold text-[var(--accent)] hover:underline cursor-pointer"
          >
            View full portfolio (1,842) →
          </button>
        </div>

        <DataTable
          columns={columns}
          data={attentionProjects}
          keyExtractor={row => row.id}
          onRowClick={row => onNavigate('projects', row.id)}
        />
      </div>
    </div>
  );
}
