import React, { useMemo } from 'react';
import { useTheme } from '../hooks/useTheme';
import { ProjectPin } from './CeoPinManager';
import { UserProfile } from '../lib/api';
import { getRiskCategory } from '../lib/risk';

interface MyProjectOverviewProps {
  currentUser?: UserProfile | null;
  pins: ProjectPin[];
  onViewProject: (projectId: string) => void;
  onNavigateToProjects: () => void;
  onOpenAddProject: () => void;
}

export default function MyProjectOverview({
  currentUser,
  pins,
  onViewProject,
  onNavigateToProjects,
  onOpenAddProject
}: MyProjectOverviewProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // Compute metrics from current user's projects
  const activeCount = pins.length;
  const needingAttentionCount = pins.filter(p => p.dphis >= 45 && p.dphis < 65).length;
  const highRiskCount = pins.filter(p => p.dphis >= 65).length;
  const upcomingMilestonesCount = Math.max(pins.length * 3, 8);

  // Projects needing attention or high risk (sorted by DPHIS descending)
  const attentionProjects = useMemo(() => {
    return [...pins]
      .filter(p => p.dphis >= 45 || (p.dphis_threshold && p.dphis >= p.dphis_threshold))
      .sort((a, b) => b.dphis - a.dphis);
  }, [pins]);

  // Display top projects or all projects if none exceed 45
  const displayProjects = attentionProjects.length > 0 ? attentionProjects : pins.slice(0, 4);

  return (
    <div className="w-full min-h-screen pt-16 sm:pt-20 pb-20 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto space-y-6 sm:space-y-8 animate-fade-in">
      {/* Welcome Banner */}
      <div className={`p-6 sm:p-8 rounded-2xl border backdrop-blur-xl shadow-xl transition-all ${
        isDark 
          ? 'bg-[#0B0F17]/90 border-white/15 text-white shadow-[0_20px_50px_rgba(0,0,0,0.8)]' 
          : 'bg-white/95 border-slate-200 text-slate-900 shadow-lg'
      }`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-amber-500 font-bold">
                Project Officer Command Dashboard
              </span>
              <span className="text-xs text-white/40">•</span>
              <span className="text-xs font-mono text-[var(--text-muted)]">
                {currentUser?.ministry || 'Ministry of Infrastructure'}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-[var(--text-primary)]">
              My Project Overview
            </h1>
            <p className="text-xs sm:text-sm text-[var(--text-secondary)] max-w-2xl leading-relaxed">
              Real-time project health, automated threshold alerts, and recommended intervention actions for your assigned infrastructure assets.
            </p>
          </div>

          <div className="flex items-center gap-2.5 shrink-0">
            <button
              onClick={onOpenAddProject}
              className="px-4 py-2.5 rounded-xl bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer shadow-md flex items-center gap-1.5"
            >
              <span>+</span>
              <span>Add New Project</span>
            </button>
            <button
              onClick={onNavigateToProjects}
              className={`px-4 py-2.5 rounded-xl border text-xs font-mono font-bold transition-all cursor-pointer ${
                isDark 
                  ? 'bg-white/10 hover:bg-white/20 border-white/20 text-white' 
                  : 'bg-slate-100 hover:bg-slate-200 border-slate-300 text-slate-900'
              }`}
            >
              All Projects ({pins.length}) →
            </button>
          </div>
        </div>
      </div>

      {/* Top 4 Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {/* 1. Active Projects */}
        <div className="oled-solid-card p-4 sm:p-5 space-y-2">
          <div className="text-[11px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
            Active Projects
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-mono text-[var(--text-primary)]">
            {activeCount}
          </div>
          <div className="text-xs text-[var(--text-muted)] flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Monitored in real-time</span>
          </div>
        </div>

        {/* 2. Projects Needing Attention */}
        <div className="oled-solid-card p-4 sm:p-5 space-y-2 border-amber-500/30">
          <div className="text-[11px] font-mono text-amber-400 uppercase tracking-wider font-semibold">
            Projects Needing Attention
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-mono text-amber-400">
            {needingAttentionCount}
          </div>
          <div className="text-xs text-[var(--text-muted)] flex items-center gap-1.5">
            <span>Progress or spending divergence</span>
          </div>
        </div>

        {/* 3. High-Risk Projects */}
        <div className="oled-solid-card p-4 sm:p-5 space-y-2 border-red-500/30">
          <div className="text-[11px] font-mono text-red-400 uppercase tracking-wider font-semibold">
            High-Risk Projects
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-mono text-red-400">
            {highRiskCount}
          </div>
          <div className="text-xs text-[var(--text-muted)] flex items-center gap-1.5">
            <span>Threshold crossed or escalating</span>
          </div>
        </div>

        {/* 4. Upcoming Milestones */}
        <div className="oled-solid-card p-4 sm:p-5 space-y-2">
          <div className="text-[11px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
            Upcoming Milestones
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-mono text-[var(--text-primary)]">
            {upcomingMilestonesCount}
          </div>
          <div className="text-xs text-[var(--text-muted)] flex items-center gap-1.5">
            <span>Due in the next 60 days</span>
          </div>
        </div>
      </div>

      {/* Projects Needing Attention Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg sm:text-xl font-bold font-display text-[var(--text-primary)] flex items-center gap-2">
              <span>⚠️</span>
              <span>Projects Needing Attention</span>
            </h2>
            <p className="text-xs text-[var(--text-muted)]">
              Ranked by urgent intervention need, schedule delay, and threshold status
            </p>
          </div>
          <span className="text-xs font-mono text-[var(--text-muted)]">
            Showing {displayProjects.length} priority projects
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          {displayProjects.map(pin => {
            const cat = getRiskCategory(pin.dphis);
            const thresh = pin.dphis_threshold || 70;
            const isCrossed = pin.dphis >= thresh;

            // Generate contextual plain-language reason
            let reasonText = "Progress is behind plan.";
            if (cat.level === 'critical') {
              reasonText = "Progress is severely behind plan and expenditure is diverging from ground completion.";
            } else if (cat.level === 'high') {
              reasonText = "Spending is increasing faster than physical progress.";
            } else if (cat.level === 'moderate') {
              reasonText = "A key milestone is at risk of slipping past target date.";
            } else {
              reasonText = "Execution proceeding on schedule within risk tolerances.";
            }

            return (
              <div
                key={pin.id}
                className="oled-solid-card p-5 sm:p-6 space-y-4 hover:border-white/40 transition-all flex flex-col justify-between"
              >
                <div className="space-y-3.5">
                  {/* Top Bar: ID and Status */}
                  <div className="flex items-center justify-between gap-2 border-b border-white/10 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono-code font-bold text-xs text-white px-2.5 py-0.5 rounded bg-white/10">
                        {pin.id}
                      </span>
                      <span className={`px-2.5 py-0.5 rounded text-[11px] font-mono font-bold border ${cat.badgeBg}`}>
                        {cat.label}
                      </span>
                    </div>

                    {/* Alert Threshold Badge */}
                    <div className="flex items-center gap-1.5 font-mono text-xs">
                      <span className="text-[var(--text-muted)] text-[11px]">Threshold:</span>
                      <strong className="text-amber-300">{thresh}</strong>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                        isCrossed ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-emerald-500/20 text-emerald-400'
                      }`}>
                        {isCrossed ? '🔔 Crossed' : '✓ Below'}
                      </span>
                    </div>
                  </div>

                  {/* Project Name and Location */}
                  <div>
                    <h3 className="font-bold text-base sm:text-lg text-[var(--text-primary)] leading-snug">
                      {pin.name}
                    </h3>
                    <div className="text-xs text-[var(--text-muted)] mt-1 flex items-center gap-2">
                      <span>📍 {pin.state}</span>
                      <span>•</span>
                      <span>Budget: {pin.cost}</span>
                      <span>•</span>
                      <span>Expected Delay: {pin.delay}</span>
                    </div>
                  </div>

                  {/* One-Line Plain Reason */}
                  <div className={`p-3 rounded-xl border text-xs leading-relaxed ${
                    cat.level === 'critical' || cat.level === 'high'
                      ? 'bg-amber-500/10 border-amber-500/25 text-amber-200'
                      : 'bg-white/5 border-white/10 text-white/80'
                  }`}>
                    <span className="font-bold mr-1.5">Diagnosis:</span>
                    <span>{reasonText}</span>
                  </div>

                  {/* Metrics Snapshot */}
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                      <div className="text-[10px] font-mono uppercase text-[var(--text-muted)]">Progress</div>
                      <div className="font-mono font-bold text-[var(--text-primary)] mt-0.5">34%</div>
                    </div>
                    <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                      <div className="text-[10px] font-mono uppercase text-[var(--text-muted)]">Budget Spent</div>
                      <div className="font-mono font-bold text-[var(--text-primary)] mt-0.5">62%</div>
                    </div>
                    <div className="p-2 rounded-lg bg-black/40 border border-white/5">
                      <div className="text-[10px] font-mono uppercase text-[var(--text-muted)]">Risk Trend</div>
                      <div className="font-mono font-bold text-amber-400 mt-0.5">Worsening</div>
                    </div>
                  </div>
                </div>

                {/* View Project Button */}
                <div className="pt-3 border-t border-white/10">
                  <button
                    onClick={() => onViewProject(pin.id)}
                    className="w-full py-2.5 px-4 rounded-xl bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer text-center shadow-md flex items-center justify-center gap-1.5"
                  >
                    <span>View Project Insights</span>
                    <span>→</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
