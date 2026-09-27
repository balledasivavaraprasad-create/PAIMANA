import React, { useState, useMemo } from 'react';
import GlassCard from '../components/GlassCard';
import ProjectInsightsModal from '../components/ProjectInsightsModal';
import { ProjectPin } from '../components/CeoPinManager';
import { UserProfile } from '../lib/api';
import { getRiskCategory } from '../lib/risk';

interface Props {
  currentUser?: UserProfile | null;
  pins: ProjectPin[];
  onSelectProject: (projectId: string) => void;
  onNavigateToInsights?: (projectId: string) => void;
  onNavigateToInvestigation: (projectId: string) => void;
  onOpenAddProject: () => void;
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

export default function MyProjects({
  currentUser,
  pins,
  onSelectProject,
  onNavigateToInsights,
  onNavigateToInvestigation,
  onOpenAddProject,
  onRemoveProject
}: Props) {
  const isAdmin = currentUser?.role === 'ADMIN' || currentUser?.role === 'ANALYST';
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW'>('ALL');
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');
  const [insightsModalProjectId, setInsightsModalProjectId] = useState<string | null>(null);

  // Filter projects by search and status
  const filteredPins = useMemo(() => {
    return pins.filter(p => {
      const cat = getRiskCategory(p.dphis);
      const matchesStatus = 
        statusFilter === 'ALL' ||
        (statusFilter === 'CRITICAL' && cat.level === 'critical') ||
        (statusFilter === 'HIGH' && cat.level === 'high') ||
        (statusFilter === 'MODERATE' && cat.level === 'moderate') ||
        (statusFilter === 'LOW' && cat.level === 'low');

      const q = searchQuery.toLowerCase().trim();
      const matchesSearch = 
        !q ||
        p.id.toLowerCase().includes(q) ||
        p.name.toLowerCase().includes(q) ||
        p.state.toLowerCase().includes(q);

      return matchesStatus && matchesSearch;
    });
  }, [pins, searchQuery, statusFilter]);

  return (
    <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Header Banner */}
      <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white">
              {isAdmin ? 'National Project Portfolio' : 'My Assigned Projects'}
            </h2>
            <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-white/10 text-white/90 border border-white/20">
              {pins.length} {pins.length === 1 ? 'Project' : 'Projects'} Monitored
            </span>
          </div>
          <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
            {isAdmin 
              ? 'Complete multi-ministry infrastructure asset registry and risk monitoring' 
              : `Projects actively tracked under ${currentUser?.ministry || 'your department'} (${currentUser?.full_name || 'Project Officer'})`
            }
          </p>
        </div>

        {/* Add Project is strictly for non-admin users */}
        {!isAdmin && (
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={onOpenAddProject}
              className="px-5 py-2.5 rounded-xl bg-white text-black text-xs sm:text-sm font-mono-code font-bold hover:bg-slate-200 transition-all cursor-pointer shadow-md flex items-center gap-1.5"
            >
              <span>+</span>
              <span>Add Project</span>
            </button>
          </div>
        )}
      </GlassCard>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search by project name, ID, or state..."
            className="w-full bg-[#0B0F17]/80 border border-white/20 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-white placeholder:text-white/40 focus:outline-none focus:border-white/50"
          />
        </div>

        {/* Status Filter Buttons */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {(['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'] as const).map(st => {
            const labelMap = {
              ALL: 'All Status',
              CRITICAL: 'Critical',
              HIGH: 'High Risk',
              MODERATE: 'Needs Attention',
              LOW: 'On Track'
            };
            const active = statusFilter === st;
            return (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer whitespace-nowrap border ${
                  active
                    ? 'bg-white text-black font-bold border-white shadow-sm'
                    : 'bg-white/5 hover:bg-white/10 text-white/80 border-white/15'
                }`}
              >
                {labelMap[st]}
              </button>
            );
          })}

          {/* View Mode Toggle */}
          <div className="ml-2 hidden sm:flex items-center bg-white/5 border border-white/15 rounded-lg p-0.5">
            <button
              onClick={() => setViewMode('cards')}
              title="Card view"
              className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
                viewMode === 'cards' ? 'bg-white text-black font-bold' : 'text-white/70 hover:text-white'
              }`}
            >
              Cards
            </button>
            <button
              onClick={() => setViewMode('table')}
              title="Table view"
              className={`px-2.5 py-1 rounded text-xs transition-colors cursor-pointer ${
                viewMode === 'table' ? 'bg-white text-black font-bold' : 'text-white/70 hover:text-white'
              }`}
            >
              Table
            </button>
          </div>
        </div>
      </div>

      {/* Projects List: Cards or Table */}
      {filteredPins.length === 0 ? (
        <GlassCard variant="medium" padding={32} className="text-center space-y-4">
          <div className="text-base font-bold text-white">No Matching Projects Found</div>
          <p className="text-xs sm:text-sm text-white/70 max-w-md mx-auto">
            {searchQuery || statusFilter !== 'ALL'
              ? 'No projects match your current filter criteria. Try clearing filters or search query.'
              : !isAdmin 
                ? "You do not have any projects listed yet. Click 'Add Project' to get started."
                : "No projects registered in the portfolio database."
            }
          </p>
          {(searchQuery || statusFilter !== 'ALL') && (
            <button
              onClick={() => { setSearchQuery(''); setStatusFilter('ALL'); }}
              className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-mono font-bold border border-white/20 transition-all cursor-pointer"
            >
              Clear Filters
            </button>
          )}
        </GlassCard>
      ) : viewMode === 'cards' ? (
        /* Cards View */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {filteredPins.map(pin => {
            const cat = getRiskCategory(pin.dphis);

            return (
              <div
                key={pin.id}
                className="oled-solid-card p-5 sm:p-6 space-y-4 hover:border-white/40 transition-all flex flex-col justify-between"
              >
                <div className="space-y-3.5">
                  {/* Top Bar: ID, Location & Remove Action */}
                  <div className="flex items-center justify-between gap-2 border-b border-white/10 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono-code font-bold text-xs sm:text-sm text-white px-2 py-0.5 rounded bg-white/10">
                        {pin.id}
                      </span>
                      <span className="text-xs text-white/70 flex items-center gap-1 font-medium">
                        <span>📍</span>
                        <span>{pin.state}</span>
                      </span>
                    </div>

                    {/* Remove Project Option */}
                    {onRemoveProject && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRemoveProject(pin.id);
                        }}
                        title="Remove Project"
                        className="text-xs text-red-400/80 hover:text-red-300 hover:bg-red-500/15 px-2 py-1 rounded-lg border border-red-500/20 transition-all cursor-pointer font-mono flex items-center gap-1"
                      >
                        <span>✕</span>
                        <span>Remove</span>
                      </button>
                    )}
                  </div>

                  {/* Project Name */}
                  <div>
                    <h3 className="font-bold text-sm sm:text-base text-white leading-snug line-clamp-2">
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
                        {cat.level === 'critical' 
                          ? 'Critical Delay Risk' 
                          : cat.level === 'high' 
                          ? 'High Delay Risk' 
                          : cat.level === 'moderate' 
                          ? 'Moderate Attention Needed' 
                          : 'On Track'}
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
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectProject(pin.id);
                      if (onNavigateToInsights) {
                        onNavigateToInsights(pin.id);
                      } else {
                        setInsightsModalProjectId(pin.id);
                      }
                    }}
                    className="flex-1 py-2 px-3 rounded-xl bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer text-center shadow-md flex items-center justify-center gap-1 whitespace-nowrap"
                  >
                    <span>View Project Insights</span>
                    <span>→</span>
                  </button>

                  {/* Investigate Issue for Normal User (opens InvestigationModal pop-up) */}
                  {!isAdmin && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectProject(pin.id);
                        onNavigateToInvestigation(pin.id);
                      }}
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
      ) : (
        /* Table View */
        <div className="overflow-x-auto rounded-xl border border-white/15 bg-black/40 backdrop-blur-md">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-white/15 bg-[#0B0F17]">
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Project ID</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Project Name</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Location</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">DPHIS Score</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Risk Tier</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredPins.map(pin => {
                const cat = getRiskCategory(pin.dphis);
                return (
                  <tr 
                    key={pin.id} 
                    onClick={() => {
                      onSelectProject(pin.id);
                      setInsightsModalProjectId(pin.id);
                    }}
                    className="hover:bg-white/5 transition-colors cursor-pointer"
                  >
                    <td className="p-4 font-mono font-bold text-white">{pin.id}</td>
                    <td className="p-4 font-semibold text-white">{pin.name}</td>
                    <td className="p-4 text-white/80">{pin.state}</td>
                    <td className="p-4 font-mono font-bold text-white">
                      <div className="flex items-center gap-2">
                        <span className="text-sm">{pin.dphis}</span>
                        <div className="w-16 h-1.5 rounded-full bg-white/10 overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${pin.dphis}%`,
                              background: pin.dphis >= 80 ? '#ef4444' : pin.dphis >= 65 ? '#f97316' : '#10b981'
                            }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="p-4">
                      <span className={`px-2.5 py-0.5 rounded text-[11px] font-mono font-bold border ${cat.badgeBg}`}>
                        {cat.label}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectProject(pin.id);
                            if (onNavigateToInsights) {
                              onNavigateToInsights(pin.id);
                            } else {
                              setInsightsModalProjectId(pin.id);
                            }
                          }}
                          className="px-3 py-1.5 rounded-lg bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer whitespace-nowrap"
                        >
                          View Project Insights →
                        </button>
                        {!isAdmin && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectProject(pin.id);
                              onNavigateToInvestigation(pin.id);
                            }}
                            className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white hover:text-black text-white text-xs font-mono font-bold border border-white/20 transition-all cursor-pointer whitespace-nowrap"
                          >
                            Investigate ⚡
                          </button>
                        )}
                        {onRemoveProject && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onRemoveProject(pin.id);
                            }}
                            title="Remove project"
                            className="px-2 py-1.5 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-500/10 border border-red-500/20 text-xs font-mono transition-all cursor-pointer"
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Floating Project Insights Pop-Up Modal */}
      <ProjectInsightsModal
        isOpen={!!insightsModalProjectId}
        projectId={insightsModalProjectId}
        currentUser={currentUser}
        onClose={() => setInsightsModalProjectId(null)}
        onNavigateToInvestigation={onNavigateToInvestigation}
      />
    </div>
  );
}
