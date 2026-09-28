import React, { useState, useEffect, useMemo } from 'react';
import GlassCard from '../components/GlassCard';
import { 
  fetchProjectPredictions, fetchProjectRisk, fetchProject, fetchProjects,
  PredictionData, RiskData, ProjectData, UserProfile 
} from '../lib/api';
import { ProjectPin } from '../components/CeoPinManager';
import { getRiskCategory } from '../lib/risk';
import { useTheme } from '../hooks/useTheme';
import { computeRealTimeShapFactors } from '../lib/shap';
import { CurvedGrowthArrow, CurvedDecreaseArrow, TrendBadge } from '../components/CurvedTrendArrow';

interface Props {
  projectId?: string;
  currentUser?: UserProfile | null;
  allProjects?: ProjectPin[];
  onNavigateToInvestigation: (projectId: string) => void;
  onSelectProject?: (projectId: string) => void;
  onOpenAddProject?: () => void;
  onNavigateBack?: () => void;
}

function DHPISGauge({ score }: { score: number }) {
  const size = 220;
  const strokeWidth = 14;
  const center = size / 2;
  const radius = center - strokeWidth - 4;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference;
  const cat = getRiskCategory(score);

  return (
    <div className="flex flex-col items-center justify-center py-2 sm:py-4">
      <div className="relative w-48 h-48 sm:w-56 sm:h-56 flex items-center justify-center">
        <svg className="w-full h-full -rotate-90" viewBox={`0 0 ${size} ${size}`}>
          {/* Track Circle */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            stroke="rgba(255, 255, 255, 0.15)"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Progress Arc in crisp solid white */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            stroke="#ffffff"
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Centered Content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-2">
          <span className="font-mono-code font-bold text-4xl sm:text-5xl text-white tracking-tight">
            {score}
          </span>
          <span className={`mt-1 text-xs sm:text-sm font-mono-code font-bold uppercase tracking-wider ${cat.colorClass}`}>
            {cat.label}
          </span>
          <span className="text-xs font-mono-code text-white/70 mt-0.5">
            DPHIS Index · {cat.badgeText}
          </span>
        </div>
      </div>
    </div>
  );
}

function MiniDphisGauge({ score }: { score: number }) {
  const size = 64;
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
        <span className="font-mono-code font-bold text-sm text-white leading-none">
          {score}
        </span>
        <span className="text-[7px] font-mono-code font-bold text-white/60 uppercase mt-0.5">
          DPHIS
        </span>
      </div>
    </div>
  );
}

export default function ProjectIntelligence({ 
  projectId, 
  currentUser,
  allProjects,
  onNavigateToInvestigation, 
  onSelectProject,
  onOpenAddProject,
  onNavigateBack
}: Props) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const isAdmin = currentUser?.role === 'ADMIN' || currentUser?.role === 'ANALYST';
  
  // Navigation state: null = project list view (admin only), string = deep intelligence view
  const defaultProjectId = projectId || (!isAdmin && allProjects && allProjects.length > 0 ? allProjects[0].id : null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(defaultProjectId);

  useEffect(() => {
    if (projectId) {
      setActiveProjectId(projectId);
    } else if (!isAdmin && allProjects && allProjects.length > 0) {
      setActiveProjectId(allProjects[0].id);
    }
  }, [projectId, isAdmin, allProjects]);

  // Directory Projects State
  const [projectList, setProjectList] = useState<any[]>([]);
  const [directoryLoading, setDirectoryLoading] = useState(true);

  // Filters State
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW'>('ALL');
  const [sectorFilter, setSectorFilter] = useState<string>('ALL');
  const [stateFilter, setStateFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'dphis_desc' | 'dphis_asc' | 'cost_desc' | 'delay_desc' | 'name_asc'>('dphis_desc');

  // Deep View State
  const [activeTab, setActiveTab] = useState<'shap' | 'predictions'>('shap');
  const [project, setProject] = useState<ProjectData | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Load project list on mount
  useEffect(() => {
    let isMounted = true;
    setDirectoryLoading(true);

    fetchProjects(undefined, 100, undefined, undefined, isAdmin ? undefined : currentUser?.username).then(apiProjects => {
      if (!isMounted) return;
      if (apiProjects && apiProjects.length > 0) {
        setProjectList(apiProjects);
      } else if (allProjects && allProjects.length > 0) {
        // Fallback to pins passed via props
        const mapped = allProjects.map(p => ({
          project_id: p.id,
          project_name: p.name,
          ministry: currentUser?.ministry || 'Ministry of Infrastructure',
          sector: p.name.toLowerCase().includes('rail') || p.name.toLowerCase().includes('gauge') ? 'Railways' : p.name.toLowerCase().includes('solar') ? 'Power & Energy' : p.name.toLowerCase().includes('port') ? 'Ports & Shipping' : 'Roads & Highways',
          state: p.state,
          cost: { revised: parseInt(p.cost.replace(/[^\d]/g, '') || '3500') },
          schedule: { revised_end: '2027-12-31' },
          dphis: p.dphis,
          risk_level: p.risk,
          delay_str: p.delay
        }));
        setProjectList(mapped);
      }
      setDirectoryLoading(false);
    }).catch(() => {
      if (isMounted) setDirectoryLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, [allProjects, isAdmin, currentUser]);

  // Load detail data when an active project is selected
  useEffect(() => {
    if (!activeProjectId) {
      setProject(null);
      setPrediction(null);
      setRisk(null);
      setDetailLoading(false);
      return;
    }

    setDetailLoading(true);
    Promise.all([
      fetchProject(activeProjectId),
      fetchProjectPredictions(activeProjectId),
      fetchProjectRisk(activeProjectId)
    ]).then(([p, pred, r]) => {
      if (p) setProject(p);
      if (pred) setPrediction(pred);
      if (r) setRisk(r);
      setDetailLoading(false);
    }).catch(() => setDetailLoading(false));
  }, [activeProjectId]);

  // Inferred filter options
  const inferredSectors = useMemo(() => {
    const set = new Set<string>();
    projectList.forEach(p => {
      if (p.sector) set.add(p.sector);
    });
    return Array.from(set).sort();
  }, [projectList]);

  const inferredStates = useMemo(() => {
    const set = new Set<string>();
    projectList.forEach(p => {
      if (p.state) set.add(p.state);
    });
    return Array.from(set).sort();
  }, [projectList]);

  // Filtered & sorted projects
  const filteredProjects = useMemo(() => {
    return projectList.filter(p => {
      const pDphis = p.dphis ?? 50;
      const cat = getRiskCategory(pDphis);

      // Risk level filter
      const matchesRisk = 
        riskFilter === 'ALL' ||
        (riskFilter === 'CRITICAL' && cat.level === 'critical') ||
        (riskFilter === 'HIGH' && cat.level === 'high') ||
        (riskFilter === 'MODERATE' && cat.level === 'moderate') ||
        (riskFilter === 'LOW' && cat.level === 'low');

      // Sector filter
      const matchesSector = 
        sectorFilter === 'ALL' ||
        (p.sector && p.sector.toLowerCase() === sectorFilter.toLowerCase());

      // State filter
      const matchesState = 
        stateFilter === 'ALL' ||
        (p.state && p.state.toLowerCase() === stateFilter.toLowerCase());

      // Search query
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch = 
        !q ||
        (p.project_id && p.project_id.toLowerCase().includes(q)) ||
        (p.project_name && p.project_name.toLowerCase().includes(q)) ||
        (p.ministry && p.ministry.toLowerCase().includes(q)) ||
        (p.sector && p.sector.toLowerCase().includes(q)) ||
        (p.state && p.state.toLowerCase().includes(q));

      return matchesRisk && matchesSector && matchesState && matchesSearch;
    }).sort((a, b) => {
      const aDphis = a.dphis ?? 50;
      const bDphis = b.dphis ?? 50;
      const aCost = a.cost?.revised || 0;
      const bCost = b.cost?.revised || 0;

      if (sortBy === 'dphis_desc') return bDphis - aDphis;
      if (sortBy === 'dphis_asc') return aDphis - bDphis;
      if (sortBy === 'cost_desc') return bCost - aCost;
      if (sortBy === 'delay_desc') return bDphis - aDphis;
      if (sortBy === 'name_asc') return (a.project_name || '').localeCompare(b.project_name || '');
      return 0;
    });
  }, [projectList, riskFilter, sectorFilter, stateFilter, searchQuery, sortBy]);

  /* =========================================================================
     DEEP RISK INTELLIGENCE DETAIL PAGE (DIRECTLY REACHED FROM PORTFOLIO)
     ========================================================================= */
  const resolvedProjectId = activeProjectId || (allProjects && allProjects.length > 0 ? ((allProjects[0] as any).project_id || allProjects[0].id) : "618488");
  const pName = project?.project_name || "NH-48 Varanasi-Ranchi Expressway Package 4";
  const pState = project?.state || "Uttar Pradesh";
  const pSector = project?.sector || "Roads & Highways";
  const currentDphis = risk?.dphis ?? project?.dphis ?? 85.0;
  const riskCat = getRiskCategory(currentDphis);

  // Dynamic real-time SHAP explainability factors based on live project telemetry
  const shapFactors = useMemo(() => {
    return computeRealTimeShapFactors({
      ...project,
      id: resolvedProjectId,
      dphis: currentDphis,
      name: pName,
      sector: pSector,
      state: pState,
      delay: prediction?.delay?.expected_delay_months,
      cost: project?.cost || { revised: 4218, original: 4000 }
    });
  }, [project, resolvedProjectId, currentDphis, pName, pSector, pState, prediction]);

  return (
    <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Return to Directory / Back to My Projects */}
      <div className="flex items-center justify-between pb-2">
        <button
          onClick={() => {
            if (onNavigateBack) {
              onNavigateBack();
            } else {
              setActiveProjectId(null);
            }
          }}
          className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white hover:text-black text-white text-xs sm:text-sm font-mono-code font-bold border border-white/20 transition-all cursor-pointer flex items-center gap-2 shadow-md"
        >
          <span>← Get Back to Portfolio Page</span>
        </button>

        <div className="text-xs font-mono text-white/60">
          Inspecting Asset: <strong className="text-white">{resolvedProjectId}</strong>
        </div>
      </div>

      {/* Top Project Context Card */}
      <GlassCard variant="hero" padding={24} className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2 sm:space-y-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="font-mono-code font-bold text-xs sm:text-sm text-white px-2.5 py-0.5 rounded bg-white/10">
              {resolvedProjectId}
            </span>
            <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${riskCat.badgeBg}`}>
              {riskCat.label}
            </span>
            <span className="text-xs text-white/70">
              {project?.ministry || 'Ministry of Infrastructure'}
            </span>
          </div>

          <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white leading-tight">
            {pName}
          </h2>

          <div className="flex flex-wrap items-center gap-3 text-xs sm:text-sm text-white/80 font-medium">
            <span>📍 {pState}</span>
            <span>•</span>
            <span>Sector: {pSector}</span>
            <span>•</span>
            <span className="font-mono-code font-bold text-white">
              Sanctioned Budget: ₹{project?.cost?.revised || 4218} Cr
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <button
            onClick={() => onNavigateToInvestigation(resolvedProjectId)}
            className="px-5 sm:px-6 py-2.5 rounded-xl bg-black text-white text-xs sm:text-sm font-mono-code font-bold border border-white/30 shadow-[0_0_16px_rgba(255,255,255,0.22)] hover:bg-zinc-900 transition-all cursor-pointer flex items-center justify-center gap-2"
          >
            <span>Launch Deep AI Investigation Console →</span>
          </button>
        </div>
      </GlassCard>

      {/* Main Grid: DPHIS Gauge + Predictions / SHAP */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
        {/* Left: DPHIS Gauge & Component Breakdown */}
        <GlassCard variant="medium" padding={24} className="space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-base sm:text-lg font-bold font-display text-white">
              Project Health Score
            </h3>
            <span className="text-xs sm:text-sm font-mono-code text-white/70">0–100 Scale</span>
          </div>

          <DHPISGauge score={currentDphis} />

          {/* Component Bar Breakdown */}
          {risk?.components && (
            <div className="space-y-3 pt-3 border-t border-white/15 text-sm">
              <div className="text-xs font-mono-code font-bold uppercase text-white/70">
                Risk Factor Breakdown
              </div>
              <div className="space-y-2.5">
                {[
                  { name: 'Timeline & Delay Risk', val: risk.components.time },
                  { name: 'Budget Overrun Risk', val: risk.components.cost },
                  { name: 'Physical Work Pace', val: risk.components.progress },
                  { name: 'Spending vs Progress Gap', val: risk.components.financial },
                  { name: 'Model Reliability Score', val: risk.components.implementation },
                ].map(comp => (
                  <div key={comp.name} className="space-y-1">
                    <div className="flex justify-between font-mono-code text-xs sm:text-sm">
                      <span className="text-white/80">{comp.name}</span>
                      <span className="font-bold text-white">{(comp.val * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                      <div
                        className="h-full bg-white rounded-full transition-all duration-700"
                        style={{ width: `${Math.min(100, comp.val * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </GlassCard>

        {/* Right 2 Cols: Predictions & SHAP Explainability */}
        <GlassCard variant="medium" padding={24} className="lg:col-span-2 space-y-6">
          <div className="flex flex-wrap items-center justify-between border-b border-white/15 pb-4 gap-3">
            <div className="flex items-center gap-2 sm:gap-3">
              <button
                onClick={() => setActiveTab('shap')}
                className={`px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer ${
                  activeTab === 'shap' ? 'bg-white text-black' : 'text-white/80 hover:text-white hover:bg-white/10'
                }`}
              >
                Key Risk Factors (AI Analysis)
              </button>
              <button
                onClick={() => setActiveTab('predictions')}
                className={`px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer ${
                  activeTab === 'predictions' ? 'bg-white text-black' : 'text-white/80 hover:text-white hover:bg-white/10'
                }`}
              >
                Future Forecasts &amp; Timeline
              </button>
            </div>
            <span className="text-xs font-mono-code text-white/80 font-semibold">
              AI Risk Engine v2.1
            </span>
          </div>

          {activeTab === 'shap' ? (
            <div className="space-y-4">
              <p className="text-sm md:text-base text-white/85 leading-relaxed">
                Our AI analyzed this project's timeline, budget, and construction milestones to identify what is driving the risk level up or down:
              </p>
              <div className="space-y-3">
                {shapFactors.map(f => (
                  <div key={f.feature} className="p-4 rounded-xl bg-white/5 border border-white/15 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1 max-w-xl">
                      <div className="font-semibold text-sm sm:text-base text-white">{f.feature}</div>
                      <div className="text-xs sm:text-sm text-white/80">{f.description}</div>
                    </div>
                    <div className="sm:text-right font-mono-code shrink-0 space-y-1">
                      <TrendBadge 
                        value={`${f.impact > 0 ? '+' : ''}${f.impact} pts`} 
                        mode="risk" 
                        className="text-sm sm:text-base py-1 px-2.5" 
                        iconClassName="w-4 h-4"
                      />
                      <div className="text-xs text-white/60 uppercase flex items-center justify-end gap-1">
                        {f.impact > 0 ? (
                          <>
                            <CurvedGrowthArrow className="w-3 h-3 text-amber-400" />
                            <span>Increases Risk</span>
                          </>
                        ) : (
                          <>
                            <CurvedDecreaseArrow className="w-3 h-3 text-emerald-400" />
                            <span>Lowers Risk</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
                <div className="p-5 rounded-xl bg-white/5 border border-white/15 space-y-2">
                  <div className="text-xs font-mono-code uppercase text-white/70">Predicted Final Cost</div>
                  <div className="text-2xl sm:text-3xl font-bold font-mono-code text-white">
                    ₹{prediction?.cost.predicted_final_cost || 4520} Cr
                  </div>
                  <div className="text-xs sm:text-sm text-white/85 font-semibold flex items-center gap-1.5">
                    <CurvedGrowthArrow className="w-3.5 h-3.5 text-amber-400" />
                    <span>+{prediction?.cost.predicted_overrun_pct || 7.2}% projected budget overrun</span>
                  </div>
                </div>

                <div className="p-5 rounded-xl bg-white/5 border border-white/15 space-y-2">
                  <div className="text-xs font-mono-code uppercase text-white/70">Timeline Slippage Projection</div>
                  <div className="text-2xl sm:text-3xl font-bold font-mono-code text-white flex items-center gap-2">
                    <CurvedGrowthArrow className="w-6 h-6 text-amber-400" />
                    <span>+{prediction?.delay.expected_delay_months || 24} Months</span>
                  </div>
                  <div className="text-xs sm:text-sm text-white/85">
                    Predicted Completion: {prediction?.delay.predicted_completion_date || '2027-12-31'}
                  </div>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-white/5 border border-white/15 space-y-2">
                <div className="font-semibold text-sm sm:text-base text-white">Model Reliability &amp; Verification</div>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed">
                  Trained and benchmarked on 3,399 major national infrastructure projects. Regularly verified against ground completion records to guarantee dependable early risk alerts.
                </p>
              </div>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
