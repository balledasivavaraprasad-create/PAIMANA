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
}

export default function MyProjects({
  currentUser,
  pins,
  onSelectProject,
  onNavigateToInsights,
  onNavigateToInvestigation,
  onOpenAddProject
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

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={onOpenAddProject}
            className="px-5 py-2.5 rounded-xl bg-white text-black text-xs sm:text-sm font-mono-code font-bold hover:bg-slate-200 transition-all cursor-pointer shadow-md flex items-center gap-1.5"
          >
            <span>+</span>
            <span>Add Project</span>
          </button>
        </div>
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
              : "You do not have any projects listed yet. Click 'Add Project' to get started."
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
        /* Cards View (Default for Normal Users) */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {filteredPins.map(pin => {
            const cat = getRiskCategory(pin.dphis);
            return (
              <div
                key={pin.id}
                className="oled-solid-card p-5 sm:p-6 space-y-4 hover:border-white/40 transition-all flex flex-col justify-between"
              >
                <div className="space-y-3">
                  {/* Top Bar: ID and Status */}
                  <div className="flex items-center justify-between gap-2 border-b border-white/10 pb-3">
                    <span className="font-mono-code font-bold text-xs sm:text-sm text-white px-2 py-0.5 rounded bg-white/10">
                      {pin.id}
                    </span>
                    <span className={`px-2.5 py-0.5 rounded text-[11px] font-mono font-bold border ${cat.badgeBg}`}>
                      {cat.label}
                    </span>
                  </div>

                  {/* Project Name & State */}
                  <div>
                    <h3 className="font-bold text-sm sm:text-base text-white leading-snug">
                      {pin.name}
                    </h3>
                    <div className="text-xs text-white/70 mt-1 flex items-center gap-1.5">
                      <span>📍</span>
                      <span>{pin.state}</span>
                    </div>
                  </div>

                  {/* Plain Language Summary */}
                  <div className="p-3 rounded-xl bg-white/5 border border-white/10 text-xs text-white/80 leading-relaxed">
                    {cat.level === 'critical' ? (
                      <p>⚠️ <strong>Urgent:</strong> Physical work is running significantly behind schedule. Review milestones.</p>
                    ) : cat.level === 'high' ? (
                      <p>⚠️ <strong>High Delay Risk:</strong> Construction progress is lagging behind approved timeline.</p>
                    ) : cat.level === 'moderate' ? (
                      <p>ℹ️ <strong>Needs Attention:</strong> Spending pace is slightly higher than completed physical work.</p>
                    ) : (
                      <p>✅ <strong>On Track:</strong> Milestone achievements and fund disbursements are proceeding as planned.</p>
                    )}
                  </div>

                  {/* Metrics Row */}
                  <div className="grid grid-cols-2 gap-2 pt-1 text-xs">
                    <div className="p-2.5 rounded-lg bg-black/40 border border-white/10">
                      <div className="text-white/60 font-mono text-[10px] uppercase">Approved Outlay</div>
                      <div className="font-mono font-bold text-white text-sm mt-0.5">{pin.cost}</div>
                    </div>
                    <div className="p-2.5 rounded-lg bg-black/40 border border-white/10">
                      <div className="text-white/60 font-mono text-[10px] uppercase">Schedule Status</div>
                      <div className="font-mono font-bold text-white text-sm mt-0.5">{pin.delay} delay</div>
                    </div>
                  </div>

                  {/* Project-Specific Alert Threshold */}
                  <div className="flex items-center justify-between text-[11px] font-mono px-3 py-1.5 rounded-lg bg-black/40 border border-white/5">
                    <span className="text-white/60">Alert Threshold: <strong className="text-amber-300">{pin.dphis_threshold || 70}</strong> / 100</span>
                    <span className={pin.dphis >= (pin.dphis_threshold || 70) ? 'text-red-400 font-bold' : 'text-emerald-400 font-medium'}>
                      {pin.dphis >= (pin.dphis_threshold || 70) ? '🔔 Crossed' : '✓ Below'}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-3 border-t border-white/10 flex items-center justify-between gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectProject(pin.id);
                      setInsightsModalProjectId(pin.id);
                    }}
                    className="flex-1 py-2 px-3 rounded-lg bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer text-center"
                  >
                    View Project Insights →
                  </button>

                  {isAdmin && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectProject(pin.id);
                        onNavigateToInvestigation(pin.id);
                      }}
                      title="Deep AI Investigation"
                      className="py-2 px-3 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-mono font-bold border border-white/20 transition-all cursor-pointer"
                    >
                      Investigate ⚡
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
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Status</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Alert Threshold</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Approved Outlay</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Delay</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredPins.map(pin => {
                const cat = getRiskCategory(pin.dphis);
                const thresh = pin.dphis_threshold || 70;
                const isCrossed = pin.dphis >= thresh;
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
                    <td className="p-4">
                      <span className={`px-2.5 py-0.5 rounded text-[11px] font-mono font-bold border ${cat.badgeBg}`}>
                        {cat.label}
                      </span>
                    </td>
                    <td className="p-4 font-mono text-xs">
                      <div className="flex items-center gap-1.5">
                        <span className="text-amber-300 font-bold">{thresh}</span>
                        <span className="text-white/40">/ 100</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                          isCrossed ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'
                        }`}>
                          {isCrossed ? '🔔 Crossed' : '✓ Below'}
                        </span>
                      </div>
                    </td>
                    <td className="p-4 font-mono font-bold text-white">{pin.cost}</td>
                    <td className="p-4 font-mono text-white/90">{pin.delay}</td>
                    <td className="p-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectProject(pin.id);
                          setInsightsModalProjectId(pin.id);
                        }}
                        className="px-3 py-1 rounded bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer whitespace-nowrap"
                      >
                        View Project Insights →
                      </button>
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
