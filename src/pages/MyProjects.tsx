import React, { useState, useMemo } from 'react';
import GlassCard from '../components/GlassCard';
import ProjectInsightsModal from '../components/ProjectInsightsModal';
import { ProjectPin } from '../components/CeoPinManager';
import { UserProfile } from '../lib/api';
import { getRiskCategory } from '../lib/risk';
import { useTheme } from '../hooks/useTheme';

interface Props {
  currentUser?: UserProfile | null;
  pins: ProjectPin[];
  onSelectProject: (projectId: string) => void;
  onNavigateToInsights?: (projectId: string) => void;
  onNavigateToRiskIntelligence?: (projectId: string) => void;
  onNavigateToInvestigation?: (projectId: string) => void;
  onOpenAddProject: () => void;
  onRemoveProject?: (projectId: string) => void;
}

const getPinSector = (p: ProjectPin): string => {
  if ((p as any).sector) return (p as any).sector;
  const n = p.name.toLowerCase();
  if (n.includes('rail') || n.includes('gauge') || n.includes('metro') || n.includes('station')) return 'Railways';
  if (n.includes('solar') || n.includes('power') || n.includes('energy') || n.includes('transmission')) return 'Power & Energy';
  if (n.includes('port') || n.includes('shipping') || n.includes('dock') || n.includes('terminal')) return 'Ports & Shipping';
  if (n.includes('gas') || n.includes('petroleum') || n.includes('pipeline')) return 'Petroleum & Natural Gas';
  if (n.includes('water') || n.includes('irrigation') || n.includes('river')) return 'Water Resources';
  return 'Roads & Highways';
};

const parseCost = (costStr: string): number => parseInt(costStr.replace(/[^\d]/g, '') || '0', 10);
const parseDelay = (delayStr: string): number => parseInt(delayStr.replace(/[^\d]/g, '') || '0', 10);

function CompactDphisGauge({ score, isDark = true }: { score: number; isDark?: boolean }) {
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
          stroke={isDark ? "rgba(255, 255, 255, 0.15)" : "rgba(0, 0, 0, 0.12)"}
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
        <span className={`font-mono-code font-bold text-base leading-none ${isDark ? 'text-white' : 'text-slate-900'}`}>
          {score}
        </span>
        <span className={`text-[8px] font-mono-code font-bold uppercase mt-0.5 ${isDark ? 'text-white/60' : 'text-slate-600'}`}>
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
  onNavigateToRiskIntelligence,
  onNavigateToInvestigation,
  onOpenAddProject,
  onRemoveProject
}: Props) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const isAdmin = currentUser?.role === 'ADMIN' || currentUser?.role === 'ANALYST';
  
  // Filters State
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW'>('ALL');
  const [sectorFilter, setSectorFilter] = useState<string>('ALL');
  const [stateFilter, setStateFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'dphis_desc' | 'dphis_asc' | 'cost_desc' | 'delay_desc' | 'name_asc'>('dphis_desc');
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');
  const [insightsModalProjectId, setInsightsModalProjectId] = useState<string | null>(null);

  // Inferred options for dropdowns
  const inferredSectors = useMemo(() => {
    const set = new Set<string>();
    pins.forEach(p => set.add(getPinSector(p)));
    return Array.from(set).sort();
  }, [pins]);

  const inferredStates = useMemo(() => {
    const set = new Set<string>();
    pins.forEach(p => {
      if (p.state) set.add(p.state);
    });
    return Array.from(set).sort();
  }, [pins]);

  // Filter & sort projects
  const filteredPins = useMemo(() => {
    let list = pins.filter(p => {
      const cat = getRiskCategory(p.dphis);
      const matchesStatus = 
        statusFilter === 'ALL' ||
        (statusFilter === 'CRITICAL' && cat.level === 'critical') ||
        (statusFilter === 'HIGH' && cat.level === 'high') ||
        (statusFilter === 'MODERATE' && cat.level === 'moderate') ||
        (statusFilter === 'LOW' && cat.level === 'low');

      const matchesSector = 
        sectorFilter === 'ALL' ||
        getPinSector(p).toLowerCase() === sectorFilter.toLowerCase();

      const matchesState = 
        stateFilter === 'ALL' ||
        p.state.toLowerCase() === stateFilter.toLowerCase();

      const q = searchQuery.toLowerCase().trim();
      const matchesSearch = 
        !q ||
        p.id.toLowerCase().includes(q) ||
        p.name.toLowerCase().includes(q) ||
        p.state.toLowerCase().includes(q) ||
        getPinSector(p).toLowerCase().includes(q);

      return matchesStatus && matchesSector && matchesState && matchesSearch;
    });

    list = [...list].sort((a, b) => {
      if (sortBy === 'dphis_desc') return b.dphis - a.dphis;
      if (sortBy === 'dphis_asc') return a.dphis - b.dphis;
      if (sortBy === 'cost_desc') return parseCost(b.cost) - parseCost(a.cost);
      if (sortBy === 'delay_desc') return parseDelay(b.delay) - parseDelay(a.delay);
      if (sortBy === 'name_asc') return a.name.localeCompare(b.name);
      return 0;
    });

    return list;
  }, [pins, searchQuery, statusFilter, sectorFilter, stateFilter, sortBy]);

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

      {/* Filter and Search Bar with 3-Tier Layout */}
      <div className="space-y-3.5">
        {/* LINE 1: Search Bar (Left) + View Mode Toggle (Right) */}
        <div className="flex items-center justify-between gap-3">
          <div className="relative w-full max-w-lg">
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search by project name, ID, sector, or state..."
              className={`w-full rounded-xl px-4 py-2.5 text-xs sm:text-sm focus:outline-none transition-all border ${
                isDark
                  ? 'bg-[#0B0F17]/85 border-white/20 text-white placeholder:text-white/40 focus:border-white/50 shadow-sm'
                  : 'bg-white border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-slate-500 shadow-sm'
              }`}
            />
          </div>

          {/* View Mode Toggle */}
          <div className={`flex items-center rounded-xl p-0.5 shrink-0 border ${
            isDark ? 'bg-white/5 border-white/15' : 'bg-slate-100 border-slate-300'
          }`}>
            <button
              onClick={() => setViewMode('cards')}
              title="Card view"
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                viewMode === 'cards' 
                  ? (isDark ? 'bg-white text-black shadow-sm' : 'bg-black text-white shadow-sm')
                  : (isDark ? 'text-white/70 hover:text-white' : 'text-slate-600 hover:text-slate-900')
              }`}
            >
              Cards
            </button>
            <button
              onClick={() => setViewMode('table')}
              title="Table view"
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                viewMode === 'table' 
                  ? (isDark ? 'bg-white text-black shadow-sm' : 'bg-black text-white shadow-sm')
                  : (isDark ? 'text-white/70 hover:text-white' : 'text-slate-600 hover:text-slate-900')
              }`}
            >
              Table
            </button>
          </div>
        </div>

        {/* LINE 2: Status Filter Buttons */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          {(['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'] as const).map(st => {
            const labelMap = {
              ALL: 'All Status',
              CRITICAL: 'Critical',
              HIGH: 'High Risk',
              MODERATE: 'Need Attention',
              LOW: 'On Track'
            };
            const active = statusFilter === st;
            return (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-mono transition-all cursor-pointer whitespace-nowrap border ${
                  active
                    ? (isDark ? 'bg-white text-black font-bold border-white shadow-md' : 'bg-black text-white font-bold border-black shadow-md')
                    : (isDark ? 'bg-white/5 hover:bg-white/10 text-white/80 border-white/15' : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-300 shadow-sm')
                }`}
              >
                {labelMap[st]}
              </button>
            );
          })}
        </div>

        {/* LINE 3: Secondary Filter Toolbar: Sector, State, Sort By */}
        <div className="flex flex-wrap items-center gap-3 pt-0.5">
          {/* Sector Filter */}
          <div className="flex items-center gap-1.5">
            <span className={`text-[11px] font-mono ${isDark ? 'text-white/60' : 'text-slate-600'}`}>Sector:</span>
            <select
              value={sectorFilter}
              onChange={e => setSectorFilter(e.target.value)}
              className={`border rounded-xl px-3 py-1.5 text-xs focus:outline-none cursor-pointer shadow-sm ${
                isDark 
                  ? 'bg-[#0B0F17] border-white/20 text-white focus:border-white/50' 
                  : 'bg-white border-slate-300 text-slate-900 focus:border-slate-500'
              }`}
            >
              <option value="ALL">All Sectors ({inferredSectors.length})</option>
              {inferredSectors.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* State Filter */}
          <div className="flex items-center gap-1.5">
            <span className={`text-[11px] font-mono ${isDark ? 'text-white/60' : 'text-slate-600'}`}>State:</span>
            <select
              value={stateFilter}
              onChange={e => setStateFilter(e.target.value)}
              className={`border rounded-xl px-3 py-1.5 text-xs focus:outline-none cursor-pointer shadow-sm ${
                isDark 
                  ? 'bg-[#0B0F17] border-white/20 text-white focus:border-white/50' 
                  : 'bg-white border-slate-300 text-slate-900 focus:border-slate-500'
              }`}
            >
              <option value="ALL">All States ({inferredStates.length})</option>
              {inferredStates.map(st => (
                <option key={st} value={st}>{st}</option>
              ))}
            </select>
          </div>

          {/* Sort By */}
          <div className="flex items-center gap-1.5 sm:ml-auto">
            <span className={`text-[11px] font-mono ${isDark ? 'text-white/60' : 'text-slate-600'}`}>Sort:</span>
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as any)}
              className={`border rounded-xl px-3 py-1.5 text-xs focus:outline-none cursor-pointer shadow-sm ${
                isDark 
                  ? 'bg-[#0B0F17] border-white/20 text-white focus:border-white/50' 
                  : 'bg-white border-slate-300 text-slate-900 focus:border-slate-500'
              }`}
            >
              <option value="dphis_desc">Highest Risk (Score)</option>
              <option value="dphis_asc">Lowest Risk (Score)</option>
              <option value="cost_desc">Approved Budget (High to Low)</option>
              <option value="delay_desc">Project Delay (Longest First)</option>
              <option value="name_asc">Project Name (A–Z)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Projects List: Cards or Table */}
      {filteredPins.length === 0 ? (
        <GlassCard variant="medium" padding={32} className="text-center space-y-4">
          <div className="text-base font-bold text-white">No Matching Projects Found</div>
          <p className="text-xs sm:text-sm text-white/70 max-w-md mx-auto">
            {searchQuery || statusFilter !== 'ALL' || sectorFilter !== 'ALL' || stateFilter !== 'ALL'
              ? 'No projects match your current filter criteria. Try clearing filters or search query.'
              : !isAdmin 
                ? "You do not have any projects listed yet. Click 'Add Project' to get started."
                : "No projects registered in the portfolio database."
            }
          </p>
          {(searchQuery || statusFilter !== 'ALL' || sectorFilter !== 'ALL' || stateFilter !== 'ALL') && (
            <button
              onClick={() => { 
                setSearchQuery(''); 
                setStatusFilter('ALL'); 
                setSectorFilter('ALL'); 
                setStateFilter('ALL'); 
              }}
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
            const pinSector = getPinSector(pin);

            return (
              <div
                key={pin.id}
                className="oled-solid-card frosted-glass-card p-5 sm:p-6 space-y-4 hover:border-white/40 transition-all flex flex-col justify-between"
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

                  {/* Project Name and Sector */}
                  <div>
                    <span className="text-[10px] font-mono uppercase text-white/60 tracking-wider">
                      {pinSector}
                    </span>
                    <h3 className="font-bold text-base sm:text-lg text-[var(--text-primary)] leading-snug line-clamp-2 mt-0.5">
                      {pin.name}
                    </h3>
                  </div>

                  {/* DPHIS / Risk Score Display without progress bar */}
                  <div className={`p-3.5 rounded-xl border flex items-center gap-3.5 ${
                    isDark ? 'bg-white/5 border-white/10' : 'bg-white/80 border-slate-200'
                  }`}>
                    <CompactDphisGauge score={pin.dphis} isDark={isDark} />

                    <div className="flex-1 space-y-1.5 min-w-0">
                      <div className="flex items-center justify-between text-xs">
                        <span className={`font-mono-code font-bold text-[11px] uppercase tracking-wider ${
                          isDark ? 'text-white/80' : 'text-slate-700'
                        }`}>
                          DPHIS / Risk Score
                        </span>
                        <span className={`font-mono-code font-bold text-sm ${isDark ? 'text-white' : 'text-slate-950'}`}>
                          {pin.dphis} <span className={`text-xs font-normal ${isDark ? 'text-white/40' : 'text-slate-500'}`}>/ 100</span>
                        </span>
                      </div>

                      {/* Risk Tier Badge beneath DPHIS / Risk Score */}
                      <div>
                        <span className={`inline-block px-2.5 py-0.5 rounded text-[11px] font-mono font-bold uppercase tracking-wider border ${
                          cat.level === 'critical'
                            ? (isDark ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-red-100 text-red-700 border-red-300')
                            : cat.level === 'high'
                            ? (isDark ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-amber-100 text-amber-900 border-amber-300')
                            : cat.level === 'moderate'
                            ? (isDark ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' : 'bg-yellow-100 text-yellow-900 border-yellow-300')
                            : (isDark ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-emerald-100 text-emerald-800 border-emerald-300')
                        }`}>
                          {cat.level === 'critical' ? 'Critical Risk' : cat.level === 'high' ? 'High Risk' : cat.level === 'moderate' ? 'Moderate Risk' : 'Low Risk'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Delay Risk Diagnosis - Black text in light mode for readability */}
                  <div className={`p-3 rounded-xl border text-xs leading-relaxed ${
                    isDark
                      ? (cat.level === 'critical'
                          ? 'bg-red-500/15 border-red-500/30 text-red-200'
                          : cat.level === 'high'
                          ? 'bg-amber-500/15 border-amber-500/30 text-amber-200'
                          : cat.level === 'moderate'
                          ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-200'
                          : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200')
                      : (cat.level === 'critical'
                          ? 'bg-red-50 border-red-200 text-black'
                          : cat.level === 'high'
                          ? 'bg-amber-50 border-amber-300 text-black'
                          : cat.level === 'moderate'
                          ? 'bg-yellow-50 border-yellow-300 text-black'
                          : 'bg-emerald-50 border-emerald-300 text-black')
                  }`}>
                    <div className="flex items-center gap-1.5 font-bold mb-1">
                      <span>{cat.level === 'critical' || cat.level === 'high' ? '⚠️' : 'ℹ️'}</span>
                      <span className={`uppercase tracking-wider font-mono text-[11px] ${isDark ? '' : 'text-black font-bold'}`}>
                        {cat.level === 'critical' ? 'Critical Delay Risk' : cat.level === 'high' ? 'High Delay Risk' : cat.level === 'moderate' ? 'Moderate Attention Needed' : 'On Track'}
                      </span>
                    </div>
                    <p className={`text-[11px] leading-snug ${isDark ? 'opacity-90' : 'text-black font-medium'}`}>
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

                {/* Actions: View Project Insights + Risk Intelligence (side-by-side) */}
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

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectProject(pin.id);
                      if (onNavigateToRiskIntelligence) {
                        onNavigateToRiskIntelligence(pin.id);
                      }
                    }}
                    title="Deep Risk Intelligence & Model Forecasts"
                    className="flex-1 py-2 px-3 rounded-xl bg-white/10 hover:bg-white hover:text-black text-white text-xs font-mono font-bold border border-white/20 transition-all cursor-pointer flex items-center justify-center gap-1 whitespace-nowrap shadow-sm"
                  >
                    <span>Risk Intelligence</span>
                    <span>⚡</span>
                  </button>
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
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Sector</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Location</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">DPHIS Score</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Risk Tier</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filteredPins.map(pin => {
                const cat = getRiskCategory(pin.dphis);
                const pinSector = getPinSector(pin);
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
                    <td className="p-4 text-white/70 font-mono text-xs">{pinSector}</td>
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
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectProject(pin.id);
                            if (onNavigateToRiskIntelligence) {
                              onNavigateToRiskIntelligence(pin.id);
                            }
                          }}
                          className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white hover:text-black text-white text-xs font-mono font-bold border border-white/20 transition-all cursor-pointer whitespace-nowrap"
                        >
                          Risk Intelligence ⚡
                        </button>
                        {onNavigateToInvestigation && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectProject(pin.id);
                              onNavigateToInvestigation(pin.id);
                            }}
                            title="Launch AI Root Cause Investigation Console"
                            className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-mono font-bold border border-amber-500/40 transition-all cursor-pointer whitespace-nowrap"
                          >
                            Investigate 🔍
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

      {/* Embedded Project Insights Modal */}
      <ProjectInsightsModal
        isOpen={Boolean(insightsModalProjectId)}
        projectId={insightsModalProjectId}
        currentUser={currentUser}
        isAdmin={isAdmin}
        onClose={() => setInsightsModalProjectId(null)}
      />
    </div>
  );
}
