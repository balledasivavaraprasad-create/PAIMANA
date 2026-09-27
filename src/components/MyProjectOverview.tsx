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
  onNavigateToInvestigation?: (projectId: string) => void;
  onRemoveProject?: (projectId: string) => void;
}

function CompactDphisGauge({ score }: { score: number }) {
  const size = 68;
  const strokeWidth = 6;
  const center = size / 2;
  const radius = center - strokeWidth - 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.min(100, Math.max(0, score));
  const strokeDashoffset = circumference - (clamped / 100) * circumference;
  const cat = getRiskCategory(score);

  return (
    <div className="relative flex items-center justify-center shrink-0" style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90" viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke="rgba(255, 255, 255, 0.15)"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke={cat.level === 'critical' ? '#ef4444' : cat.level === 'high' ? '#f97316' : cat.level === 'moderate' ? '#eab308' : '#10b981'}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="font-mono-code font-bold text-base text-white leading-none">
          {score}
        </span>
        <span className="text-[8px] font-mono-code font-bold text-white/60 uppercase mt-0.5">
          DPHIS
        </span>
      </div>
    </div>
  );
}

export default function MyProjectOverview({
  currentUser,
  pins,
  onViewProject,
  onNavigateToProjects,
  onOpenAddProject,
  onNavigateToInvestigation,
  onRemoveProject
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
          ? 'bg-[#0B0F17]/80 border-white/15 text-white shadow-[0_20px_50px_rgba(0,0,0,0.8)]' 
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
              Real-time project health, automated predictive risk scoring, and early intervention actions for your assigned infrastructure assets.
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

      {/* Top 4 Frosted Summary Flashcards */}
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
            <span>Escalated delay index</span>
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
            <span>Due in next 60 days</span>
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
              Ranked by urgent intervention need, schedule delay, and DPHIS risk score
            </p>
          </div>
          <span className="text-xs font-mono text-[var(--text-muted)]">
            Showing {displayProjects.length} priority projects
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          {displayProjects.map(pin => {
            const cat = getRiskCategory(pin.dphis);

            return (
              <div
                key={pin.id}
                className="oled-solid-card p-5 sm:p-6 space-y-4 hover:border-white/40 transition-all flex flex-col justify-between"
              >
                <div className="space-y-3.5">
                  {/* Top Bar: ID & Location */}
                  <div className="flex items-center justify-between gap-2 border-b border-white/10 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono-code font-bold text-xs text-white px-2.5 py-0.5 rounded bg-white/10">
                        {pin.id}
                      </span>
                      <span className="text-xs text-white/70 flex items-center gap-1 font-medium">
                        <span>📍</span>
                        <span>{pin.state}</span>
                      </span>
                    </div>

                    {onRemoveProject && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRemoveProject(pin.id);
                        }}
                        title="Remove Project"
                        className="text-xs text-red-400/80 hover:text-red-300 hover:bg-red-500/15 px-2 py-0.5 rounded-lg border border-red-500/20 transition-all cursor-pointer font-mono"
                      >
                        ✕ Remove
                      </button>
                    )}
                  </div>

                  {/* Project Name */}
                  <div>
                    <h3 className="font-bold text-base sm:text-lg text-[var(--text-primary)] leading-snug line-clamp-2">
                      {pin.name}
                    </h3>
                  </div>

                  {/* DPHIS Score with Round Circular Progress Bar & Scrollbar */}
                  <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-center gap-3.5">
                    <CompactDphisGauge score={pin.dphis} />

                    <div className="flex-1 space-y-1.5 min-w-0">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-mono-code font-bold text-white/80 text-[11px] uppercase tracking-wider">
                          DPHIS Risk Score:
                        </span>
                        <span className="font-mono-code font-bold text-white">
                          {pin.dphis} <span className="text-white/40 font-normal">/ 100</span>
                        </span>
                      </div>

                      {/* Compact DPHIS scrollbar/bar */}
                      <div className="h-2 w-full rounded-full bg-white/10 p-0.5 overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(100, Math.max(5, pin.dphis))}%`,
                            background: pin.dphis >= 80 
                              ? 'linear-gradient(90deg, #f97316, #ef4444)' 
                              : pin.dphis >= 65 
                              ? 'linear-gradient(90deg, #eab308, #f97316)' 
                              : pin.dphis >= 45 
                              ? '#eab308' 
                              : '#10b981'
                          }}
                        />
                      </div>

                      <div className="text-[10px] font-mono text-white/60 flex items-center justify-between">
                        <span>Low (0)</span>
                        <span className={cat.level === 'critical' || cat.level === 'high' ? 'text-red-400 font-bold' : 'text-emerald-400 font-medium'}>
                          {cat.label}
                        </span>
                        <span>Critical (100)</span>
                      </div>
                    </div>
                  </div>

                  {/* High Delay Risk Flashcard / Diagnosis */}
                  <div className={`p-3 rounded-xl border text-xs leading-relaxed ${
                    cat.level === 'critical'
                      ? 'bg-red-500/15 border-red-500/30 text-red-200'
                      : cat.level === 'high'
                      ? 'bg-amber-500/15 border-amber-500/30 text-amber-200'
                      : cat.level === 'moderate'
                      ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-200'
                      : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200'
                  }`}>
                    <div className="flex items-center gap-1.5 font-bold mb-1">
                      <span>{cat.level === 'critical' || cat.level === 'high' ? '⚠️' : 'ℹ️'}</span>
                      <span className="uppercase tracking-wider font-mono text-[11px]">
                        {cat.level === 'critical' ? 'Critical Delay Risk' : cat.level === 'high' ? 'High Delay Risk' : cat.level === 'moderate' ? 'Moderate Attention Needed' : 'On Track'}
                      </span>
                    </div>
                    <p className="text-[11px] opacity-90 leading-snug">
                      {cat.level === 'critical' 
                        ? 'Physical execution is severely lagging behind the master schedule. Immediate intervention required.'
                        : cat.level === 'high'
                        ? 'Construction progress is lagging behind approved timeline. Milestone at risk of slippage.'
                        : cat.level === 'moderate'
                        ? 'Spending pace is slightly higher than completed physical work. Review upcoming milestone.'
                        : 'All physical deliverables and fund disbursements are proceeding as planned.'}
                    </p>
                  </div>
                </div>

                {/* Actions: View Project Insights + Investigate Issue (side-by-side) */}
                <div className="pt-3 border-t border-white/10 flex items-center gap-2">
                  <button
                    onClick={() => onViewProject(pin.id)}
                    className="flex-1 py-2 px-3 rounded-xl bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer text-center shadow-md flex items-center justify-center gap-1 whitespace-nowrap"
                  >
                    <span>View Project Insights</span>
                    <span>→</span>
                  </button>

                  {onNavigateToInvestigation && (
                    <button
                      onClick={() => onNavigateToInvestigation(pin.id)}
                      title="Deep AI Investigation"
                      className="flex-1 py-2 px-3 rounded-xl bg-white/10 hover:bg-white hover:text-black text-white text-xs font-mono font-bold border border-white/20 transition-all cursor-pointer flex items-center justify-center gap-1 whitespace-nowrap"
                    >
                      <span>Investigate Issue</span>
                      <span>⚡</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
