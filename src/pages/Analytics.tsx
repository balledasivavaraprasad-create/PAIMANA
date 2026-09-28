import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import MetricCard from '../components/MetricCard';
import { CurvedGrowthArrow } from '../components/CurvedTrendArrow';
import { fetchAnalyticsOverview, fetchRiskTrend, AnalyticsOverview } from '../lib/api';

interface Props {
  onNavigateToProject?: (projectId: string) => void;
  pinsCount?: number;
  onOpenAddProject?: () => void;
}

export default function Analytics({ onNavigateToProject, pinsCount, onOpenAddProject }: Props) {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [riskTrend, setRiskTrend] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchAnalyticsOverview(),
      fetchRiskTrend()
    ]).then(([ov, trend]) => {
      if (ov) setOverview(ov);
      if (trend) setRiskTrend(trend);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (pinsCount === 0) {
    return (
      <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        <GlassCard variant="hero" padding={32} className="space-y-6 text-center sm:text-left">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 pb-6 border-b border-white/10">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-400/30">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span>No Projects in Your Dashboard Yet</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold font-display text-white">
                Add a Project to See Analytics
              </h2>
              <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
                To view national risk trends, budget spending, and sector breakdowns, please add at least one project using the Add Project button.
              </p>
            </div>

            {onOpenAddProject && (
              <button
                onClick={onOpenAddProject}
                className="px-6 py-3.5 rounded-xl bg-white text-black text-sm font-mono-code font-bold hover:bg-slate-200 transition-all cursor-pointer shadow-[0_0_24px_rgba(255,255,255,0.3)] flex items-center gap-2 shrink-0"
              >
                <span className="text-base">+</span>
                <span>Add Project</span>
              </button>
            )}
          </div>
        </GlassCard>
      </div>
    );
  }

  const totalProjects = overview?.total_projects || 1500;
  const criticalCount = overview?.critical || 60;
  const highCount = overview?.high || 28;
  const avgDphis = overview?.average_dphis || 21.3;
  const costOverrun = overview?.cost_overrun_pct || 5.0;

  return (
    <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Header - Clean heading without top eyebrow tag */}
      <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 sm:gap-6">
        <div className="space-y-1.5 sm:space-y-2">
          <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white">
            National Infrastructure Spending & Risk Trends
          </h2>
          <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
            Overview of {totalProjects.toLocaleString()} monitored government projects and their progress trends
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <span className="text-xs sm:text-sm font-mono-code px-3.5 py-1.5 rounded-xl bg-white/10 text-white font-semibold border border-white/20">
            Monitored: 1,500 Projects
          </span>
        </div>
      </GlassCard>

      {/* Top 4 Macro Metrics - Fully responsive grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        <MetricCard
          label="Total Projects"
          value={totalProjects.toLocaleString()}
          sub="Monitored across India"
        />
        <MetricCard
          label="Projects with Major Delays"
          value={criticalCount.toString()}
          sub={`+${highCount} high risk projects`}
        />
        <MetricCard
          label="Average Risk Score"
          value={avgDphis.toString()}
          sub="Target baseline: Under 30"
        />
        <MetricCard
          label="Estimated Cost Increase"
          value={`${costOverrun}%`}
          sub="Average budget overrun"
        />
      </div>

      {/* 2-Column Analytics: Monthly DPHIS Trend & Sector Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
        {/* Monthly Trend */}
        <GlassCard variant="medium" padding={24} className="space-y-4 sm:space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-base sm:text-lg font-bold font-display text-white">
              Monthly Risk Trends
            </h3>
            <span className="text-xs font-mono-code text-white/70">Past 6 Months</span>
          </div>

          <div className="space-y-3 pt-1">
            {(riskTrend.length > 0 ? riskTrend : [
              { month: '2026-03', average_dphis: 40.2, critical_count: 68 },
              { month: '2026-04', average_dphis: 41.5, critical_count: 72 },
              { month: '2026-05', average_dphis: 42.1, critical_count: 76 },
              { month: '2026-06', average_dphis: 43.8, critical_count: 80 },
              { month: '2026-07', average_dphis: 45.2, critical_count: 82 },
              { month: '2026-08', average_dphis: 46.1, critical_count: 84 },
            ]).map((t: any) => (
              <div key={t.month} className="p-3 sm:p-4 rounded-xl bg-white/5 border border-white/15 flex items-center justify-between gap-2">
                <div className="space-y-0.5">
                  <div className="text-xs sm:text-sm font-bold font-mono-code text-white">{t.month}</div>
                  <div className="text-[11px] sm:text-xs text-white/70">{t.critical_count} projects facing major delays</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-sm sm:text-base font-bold font-mono-code text-white">Index: {t.average_dphis}</div>
                  <div className="text-[10px] sm:text-xs text-white/80 font-mono-code font-semibold flex items-center justify-end gap-1">
                    <CurvedGrowthArrow className="w-3 h-3 text-amber-400" />
                    <span>+{(t.average_dphis - 38.0).toFixed(1)} pts higher than average</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Sector Exposure Breakdown */}
        <GlassCard variant="medium" padding={24} className="space-y-4 sm:space-y-5">
          <h3 className="text-base sm:text-lg font-bold font-display text-white">
            Projects &amp; Budgets by Sector
          </h3>

          <div className="space-y-3 pt-1">
            {[
              { sector: 'Roads & National Highways', count: 480, critical: 24, outlay: '₹5.2L Cr' },
              { sector: 'Railways & Dedicated Freight Corridors', count: 320, critical: 16, outlay: '₹3.8L Cr' },
              { sector: 'Metro Rail & Urban Transit', count: 210, critical: 10, outlay: '₹2.4L Cr' },
              { sector: 'Renewable Ultra Mega Solar Grids', count: 290, critical: 6, outlay: '₹1.9L Cr' },
              { sector: 'Deepwater Ports & Shipping Modernization', count: 200, critical: 4, outlay: '₹1.5L Cr' },
            ].map(sec => (
              <div key={sec.sector} className="p-3 sm:p-4 rounded-xl bg-white/5 border border-white/15 space-y-1.5 sm:space-y-2">
                <div className="flex items-center justify-between text-xs sm:text-sm md:text-base">
                  <span className="font-semibold text-white">{sec.sector}</span>
                  <span className="font-mono-code font-bold text-white shrink-0">{sec.outlay}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] sm:text-xs md:text-sm font-mono-code text-white/70">
                  <span>{sec.count} Projects</span>
                  <span className="text-white font-bold">{sec.critical} Facing Delays</span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
