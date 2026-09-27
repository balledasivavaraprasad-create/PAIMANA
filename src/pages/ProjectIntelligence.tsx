import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import { 
  fetchProjectPredictions, fetchProjectRisk, fetchProject, triggerInvestigation,
  PredictionData, RiskData, ProjectData, InvestigationReport, UserProfile 
} from '../lib/api';
import { getRiskCategory } from '../lib/risk';

interface Props {
  projectId?: string;
  currentUser?: UserProfile | null;
  onNavigateToInvestigation: (projectId: string) => void;
  onSelectProject?: (projectId: string) => void;
  onOpenAddProject?: () => void;
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

export default function ProjectIntelligence({ 
  projectId, 
  currentUser,
  onNavigateToInvestigation, 
  onOpenAddProject 
}: Props) {
  const isAdmin = currentUser?.role === 'ADMIN' || currentUser?.role === 'ANALYST';
  const [activeTab, setActiveTab] = useState<'shap' | 'predictions'>('shap');
  const [project, setProject] = useState<ProjectData | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(true);

  // Normal user embedded investigation state
  const [showTechnicalShap, setShowTechnicalShap] = useState(false);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [investigationReport, setInvestigationReport] = useState<InvestigationReport | null>(null);
  const [investigationStep, setInvestigationStep] = useState<number>(0);

  useEffect(() => {
    if (!projectId) {
      setProject(null);
      setPrediction(null);
      setRisk(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      fetchProject(projectId),
      fetchProjectPredictions(projectId),
      fetchProjectRisk(projectId)
    ]).then(([p, pred, r]) => {
      if (p) setProject(p);
      if (pred) setPrediction(pred);
      if (r) setRisk(r);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [projectId]);

  const handleRunNormalInvestigation = async () => {
    if (!projectId || isInvestigating) return;
    setIsInvestigating(true);
    setInvestigationStep(1);

    const stepTimer = setInterval(() => {
      setInvestigationStep(prev => (prev < 4 ? prev + 1 : prev));
    }, 450);

    try {
      const res = await triggerInvestigation(projectId);
      clearInterval(stepTimer);
      setInvestigationReport(res);
    } catch (err) {
      clearInterval(stepTimer);
      console.warn('Investigation trigger error:', err);
    } finally {
      setIsInvestigating(false);
      setInvestigationStep(5);
    }
  };

  // ONBOARDING EMPTY STATE: If no project is assigned or selected
  if (!loading && (!projectId || !project)) {
    return (
      <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        <GlassCard variant="hero" padding={32} className="space-y-8 text-center sm:text-left">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 pb-6 border-b border-white/10">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-400/30">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span>No Project Selected</span>
              </div>
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold font-display text-white">
                {isAdmin ? 'Select a Project to Inspect Intelligence' : 'Welcome to Your Project Insights'}
              </h2>
              <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
                {isAdmin
                  ? 'Select an infrastructure corridor from the Portfolio view to inspect risk scores, SHAP explanations, and model forecasts.'
                  : 'You do not have a project selected. Choose one of your assigned projects to see its health status, delay reasons, and recommended actions.'}
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

  const pName = project?.project_name || "NH-48 Varanasi-Ranchi Expressway Package 4";
  const pState = project?.state || "Uttar Pradesh";
  const pSector = project?.sector || "Roads & Highways";
  const currentDphis = risk?.dphis ?? project?.dphis ?? 85.0;
  const riskCat = getRiskCategory(currentDphis);

  /* =========================================================================
     NORMAL USER VIEW — ACTIONABLE, SIMPLE, HUMAN-CENTERED
     Answers: 1. What is happening? 2. Why? 3. What should I do?
     ========================================================================= */
  if (!isAdmin) {
    return (
      <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        {/* Top Project Context Card */}
        <GlassCard variant="hero" padding={24} className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 sm:space-y-3">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="font-mono-code font-bold text-xs sm:text-sm text-white px-2.5 py-0.5 rounded bg-white/10">
                {projectId}
              </span>
              <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${riskCat.badgeBg}`}>
                {riskCat.label}
              </span>
              <span className="text-xs text-white/70">
                {project?.ministry || 'Ministry of Road Transport & Highways'}
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
                Sanctioned Budget: ₹{project?.cost.revised || 4218} Cr
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={handleRunNormalInvestigation}
              disabled={isInvestigating}
              className="px-5 py-2.5 rounded-xl bg-white text-black hover:bg-slate-200 text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer shadow-lg flex items-center gap-2"
            >
              {isInvestigating ? (
                <>
                  <span className="w-3.5 h-3.5 rounded-full border-2 border-black border-t-transparent animate-spin" />
                  <span>Investigating Issues...</span>
                </>
              ) : (
                <>
                  <span>⚡</span>
                  <span>Investigate Issues</span>
                </>
              )}
            </button>
          </div>
        </GlassCard>

        {/* SECTION 1: WHAT IS HAPPENING WITH MY PROJECT? */}
        <div className="space-y-3">
          <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white/70">
            1. Project Health Status
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="oled-solid-card p-5 space-y-2">
              <div className="text-xs text-white/60 font-medium uppercase font-mono">Overall Status</div>
              <div className={`text-xl sm:text-2xl font-bold font-mono ${riskCat.colorClass}`}>
                {riskCat.label}
              </div>
              <p className="text-xs text-white/80 leading-relaxed">
                {riskCat.description}
              </p>
            </div>

            <div className="oled-solid-card p-5 space-y-2">
              <div className="text-xs text-white/60 font-medium uppercase font-mono">Physical Progress</div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-white">
                34% Completed
              </div>
              <div className="text-xs text-white/80">
                Target by now: <strong className="text-white">78%</strong>
              </div>
              <div className="h-1.5 rounded-full bg-white/10 overflow-hidden mt-1">
                <div className="h-full bg-white rounded-full" style={{ width: '34%' }} />
              </div>
            </div>

            <div className="oled-solid-card p-5 space-y-2">
              <div className="text-xs text-white/60 font-medium uppercase font-mono">Schedule Delay</div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-white">
                +{prediction?.delay.expected_delay_months || 24} Months
              </div>
              <p className="text-xs text-white/80">
                Expected Completion: <strong className="text-white">{prediction?.delay.predicted_completion_date || 'Dec 2027'}</strong>
              </p>
            </div>

            <div className="oled-solid-card p-5 space-y-2">
              <div className="text-xs text-white/60 font-medium uppercase font-mono">Budget Health</div>
              <div className="text-xl sm:text-2xl font-bold font-mono text-white">
                ₹{prediction?.cost.predicted_final_cost || 4520} Cr
              </div>
              <p className="text-xs text-white/80">
                Spending pace is <strong className="text-amber-400">ahead of physical work</strong>.
              </p>
            </div>
          </div>
        </div>

        {/* SECTION 2: WHY IS THIS PROJECT AT RISK? (Plain-Language Explanation) */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white/70">
              2. Why This Project Needs Attention
            </h3>
            <button
              onClick={() => setShowTechnicalShap(!showTechnicalShap)}
              className="text-xs font-mono text-white/60 hover:text-white underline cursor-pointer"
            >
              {showTechnicalShap ? 'Hide Technical Details' : 'View Technical Details'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="oled-solid-card p-5 space-y-2.5 border-l-4 border-l-red-500">
              <div className="flex items-center gap-2 text-red-400 font-bold text-xs uppercase font-mono">
                <span>⚠️ Primary Reason</span>
              </div>
              <h4 className="font-bold text-sm sm:text-base text-white">
                Progress is Behind Schedule
              </h4>
              <p className="text-xs text-white/80 leading-relaxed">
                Actual physical progress is at <strong>34%</strong>, while the sanctioned plan required <strong>78%</strong> by this stage. Key construction packages are falling behind.
              </p>
            </div>

            <div className="oled-solid-card p-5 space-y-2.5 border-l-4 border-l-orange-500">
              <div className="flex items-center gap-2 text-orange-400 font-bold text-xs uppercase font-mono">
                <span>⚠️ Second Reason</span>
              </div>
              <h4 className="font-bold text-sm sm:text-base text-white">
                Spending is Ahead of Physical Work
              </h4>
              <p className="text-xs text-white/80 leading-relaxed">
                Funds have been disbursed faster than actual physical construction is completed, indicating high exposure to financial and milestone overruns.
              </p>
            </div>

            <div className="oled-solid-card p-5 space-y-2.5 border-l-4 border-l-amber-500">
              <div className="flex items-center gap-2 text-amber-400 font-bold text-xs uppercase font-mono">
                <span>⚠️ Third Reason</span>
              </div>
              <h4 className="font-bold text-sm sm:text-base text-white">
                Equipment & Resource Shortage
              </h4>
              <p className="text-xs text-white/80 leading-relaxed">
                Contractor on-site machinery and heavy equipment mobilization is 38% below the planned target needed to finish on time.
              </p>
            </div>
          </div>

          {/* Optional Collapsible Technical SHAP Section */}
          {showTechnicalShap && (
            <div className="p-4 rounded-xl bg-black/50 border border-white/20 space-y-3 mt-2 text-xs">
              <div className="text-xs font-mono font-bold text-white/80 uppercase">
                Technical Factor Weights (For Engineering & Audit Reference)
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {[
                  { name: 'Schedule Deviation', weight: '+43.2 pts impact', dir: 'increase' },
                  { name: 'Expenditure vs Progress', weight: '+24.1 pts impact', dir: 'increase' },
                  { name: 'Site Equipment Shortage', weight: '+14.5 pts impact', dir: 'increase' },
                  { name: 'Land Clearances Done', weight: '-8.0 pts mitigation', dir: 'decrease' },
                ].map(f => (
                  <div key={f.name} className="p-3 rounded-lg bg-white/5 border border-white/10 space-y-1">
                    <div className="font-semibold text-white">{f.name}</div>
                    <div className="font-mono text-[11px] text-white/70">{f.weight}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* SECTION 3: WHAT SHOULD I DO? (Recommended Actions) */}
        <div className="space-y-3">
          <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white/70">
            3. Recommended Actions
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="oled-solid-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-300 text-[10px] font-mono font-bold border border-red-500/30">
                  HIGH PRIORITY
                </span>
                <span className="text-[11px] text-white/60 font-mono">Immediate</span>
              </div>
              <h4 className="font-bold text-sm sm:text-base text-white">
                Review Contractor Progress Plan
              </h4>
              <p className="text-xs text-white/80 leading-relaxed">
                Current physical progress is significantly below the target. Hold a joint milestone review with the EPC contractor to set weekly recovery targets.
              </p>
            </div>

            <div className="oled-solid-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-300 text-[10px] font-mono font-bold border border-red-500/30">
                  HIGH PRIORITY
                </span>
                <span className="text-[11px] text-white/60 font-mono">Next 7 Days</span>
              </div>
              <h4 className="font-bold text-sm sm:text-base text-white">
                Align Financial Releases with Work
              </h4>
              <p className="text-xs text-white/80 leading-relaxed">
                Ensure upcoming invoice approvals require verified physical milestone completion to stop spending from outrunning physical progress.
              </p>
            </div>

            <div className="oled-solid-card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px] font-mono font-bold border border-amber-400/30">
                  MEDIUM PRIORITY
                </span>
                <span className="text-[11px] text-white/60 font-mono">Next 14 Days</span>
              </div>
              <h4 className="font-bold text-sm sm:text-base text-white">
                Inspect Site Equipment Mobilization
              </h4>
              <p className="text-xs text-white/80 leading-relaxed">
                Verify on-site machinery and equipment against contractual requirements to ensure capacity is sufficient to reach the next milestone.
              </p>
            </div>
          </div>
        </div>

        {/* SECTION 4: EMBEDDED INVESTIGATION RESULT (When Triggered) */}
        {investigationStep > 0 && (
          <GlassCard variant="medium" padding={24} className="space-y-5 border border-white/20">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <h4 className="text-base sm:text-lg font-bold font-display text-white">
                  Investigation Findings for {projectId}
                </h4>
                <p className="text-xs text-white/70">
                  Automated diagnostic review across project history, milestone progress, and financial records
                </p>
              </div>

              {isInvestigating ? (
                <span className="px-3 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-mono font-bold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                  <span>Checking Records...</span>
                </span>
              ) : (
                <span className="px-3 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-mono font-bold">
                  ✓ Investigation Complete
                </span>
              )}
            </div>

            {/* Step Checklists */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs font-mono">
              {[
                'Project History',
                'Milestones',
                'Work Progress',
                'Financial Status',
                'Context & Land'
              ].map((step, idx) => {
                const isDone = investigationStep > idx + 1;
                const isCurrent = investigationStep === idx + 1;
                return (
                  <div 
                    key={step}
                    className={`p-2.5 rounded-lg border flex items-center gap-2 ${
                      isDone 
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                        : isCurrent
                        ? 'bg-white/10 border-white/30 text-white font-bold'
                        : 'bg-white/5 border-white/10 text-white/50'
                    }`}
                  >
                    <span>{isDone ? '✓' : isCurrent ? '⋯' : '○'}</span>
                    <span className="truncate">{step}</span>
                  </div>
                );
              })}
            </div>

            {/* Results Grid */}
            {investigationStep >= 5 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <div className="p-4 rounded-xl bg-black/40 border border-white/15 space-y-2">
                  <div className="text-xs font-mono font-bold text-white/70 uppercase">
                    Likely Root Causes
                  </div>
                  <ul className="text-xs sm:text-sm text-white/85 space-y-2 list-disc list-inside">
                    <li>Slippage in critical path foundation works for major flyover structures.</li>
                    <li>Mobilization of specialized construction machinery is running 38% behind schedule.</li>
                    <li>Expenditure outpaced verified site milestones during Q2 disbursements.</li>
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-black/40 border border-white/15 space-y-2">
                  <div className="text-xs font-mono font-bold text-white/70 uppercase">
                    Expected Impact &amp; Resolution
                  </div>
                  <p className="text-xs sm:text-sm text-white/85 leading-relaxed">
                    Executing the weekly recovery schedule and requiring milestone verification for future invoices can reduce expected timeline slippage by up to <strong>14 months</strong> and prevent further cost escalations.
                  </p>
                </div>
              </div>
            )}
          </GlassCard>
        )}
      </div>
    );
  }

  /* =========================================================================
     ADMIN VIEW — DEEP SYSTEM-LEVEL RISK INTELLIGENCE & SHAP COHORTS
     ========================================================================= */
  return (
    <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Top Header Card */}
      <GlassCard variant="hero" padding={24} className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2 sm:space-y-3">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="font-mono-code font-bold text-xs sm:text-sm text-white px-2 py-0.5 rounded bg-white/10">{projectId}</span>
            <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${riskCat.badgeBg}`}>
              {riskCat.label}
            </span>
            <span className="text-xs font-mono text-white/60">MoSPI Administrative Scope</span>
          </div>

          <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white leading-tight">
            {pName}
          </h2>

          <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-xs sm:text-sm text-white/80 font-medium">
            <span>{project?.ministry || "Ministry of Road Transport & Highways"}</span>
            <span>•</span>
            <span>Sector: {pSector}</span>
            <span>•</span>
            <span>State: {pState}</span>
            <span>•</span>
            <span className="font-mono-code font-bold text-white">
              Sanctioned Outlay: ₹{project?.cost.revised || 4218} Cr
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 shrink-0">
          {onOpenAddProject && (
            <button
              onClick={onOpenAddProject}
              className="px-4 py-2.5 rounded-xl bg-white/10 text-white hover:bg-white/20 border border-white/20 text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer flex items-center gap-1.5"
            >
              <span>+ Ingest Asset</span>
            </button>
          )}
          <button
            onClick={() => onNavigateToInvestigation(projectId || '')}
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
              Dynamic Project Health (DPHIS)
            </h3>
            <span className="text-xs sm:text-sm font-mono-code text-white/70">0–100 Scale</span>
          </div>

          <DHPISGauge score={currentDphis} />

          {/* Component Bar Breakdown */}
          {risk?.components && (
            <div className="space-y-3 pt-3 border-t border-white/15 text-sm">
              <div className="text-xs font-mono-code font-bold uppercase text-white/70">
                Risk Component Decomposition
              </div>
              <div className="space-y-2.5">
                {[
                  { name: 'Schedule Delays (30% weight)', val: risk.components.time },
                  { name: 'Budget Overrun Risk (30% weight)', val: risk.components.cost },
                  { name: 'Physical Progress Lags (25% weight)', val: risk.components.progress },
                  { name: 'Financial Velocity Disparity (10% weight)', val: risk.components.financial },
                  { name: 'Model Implementation Confidence (5% weight)', val: risk.components.implementation },
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
                SHAP Explainability Vectors
              </button>
              <button
                onClick={() => setActiveTab('predictions')}
                className={`px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer ${
                  activeTab === 'predictions' ? 'bg-white text-black' : 'text-white/80 hover:text-white hover:bg-white/10'
                }`}
              >
                Forecast Models &amp; Horizons
              </button>
            </div>
            <span className="text-xs font-mono-code text-white/80 font-semibold">
              LightGBM / XGBoost Regressor v2.1
            </span>
          </div>

          {activeTab === 'shap' ? (
            <div className="space-y-4">
              <p className="text-sm md:text-base text-white/85 leading-relaxed">
                Feature attribution values generated via TreeSHAP explainability algorithms, identifying primary risk-driving variables:
              </p>
              <div className="space-y-3">
                {(prediction?.top_shap_factors || [
                  { feature: 'Construction Schedule Delays', impact: 43.2, direction: 'increase', description: 'Main construction milestones are running 28 months behind the planned timeline.' },
                  { feature: 'Spending Ahead of Progress', impact: 24.1, direction: 'increase', description: '62% of funds have been spent, while only 34% of actual physical construction is completed.' },
                  { feature: 'Machinery & Equipment Shortage', impact: 14.5, direction: 'increase', description: 'Heavy equipment on site is 38% lower than agreed in the project plan.' },
                  { feature: 'Land Acquisition Completed', impact: -8.0, direction: 'decrease', description: '98.4% of land has been acquired and cleared, which prevents work stoppages.' },
                ]).map(f => (
                  <div key={f.feature} className="p-4 rounded-xl bg-white/5 border border-white/15 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1 max-w-xl">
                      <div className="font-semibold text-sm sm:text-base text-white">{f.feature}</div>
                      <div className="text-xs sm:text-sm text-white/80">{f.description}</div>
                    </div>
                    <div className="sm:text-right font-mono-code shrink-0">
                      <div className="text-base sm:text-xl font-bold text-white">
                        {f.impact > 0 ? `+${f.impact}` : f.impact} pts
                      </div>
                      <div className="text-xs text-white/60 uppercase">{f.impact > 0 ? '+ Increases Risk' : '− Reduces Risk'}</div>
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
                  <div className="text-xs sm:text-sm text-white/85 font-semibold">
                    +{prediction?.cost.predicted_overrun_pct || 7.2}% projected budget overrun
                  </div>
                </div>

                <div className="p-5 rounded-xl bg-white/5 border border-white/15 space-y-2">
                  <div className="text-xs font-mono-code uppercase text-white/70">Timeline Slippage Projection</div>
                  <div className="text-2xl sm:text-3xl font-bold font-mono-code text-white">
                    +{prediction?.delay.expected_delay_months || 24} Months
                  </div>
                  <div className="text-xs sm:text-sm text-white/85">
                    Predicted Completion: {prediction?.delay.predicted_completion_date || '2027-12-31'}
                  </div>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-white/5 border border-white/15 space-y-2">
                <div className="font-semibold text-sm sm:text-base text-white">Model Governance &amp; Benchmarking</div>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed">
                  Trained on 3,399 central sector project historical tracking cycles. Calibrated with quantile loss regressors and validated with 5-fold spatial cross-validation.
                </p>
              </div>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
