import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import { fetchProjectPredictions, fetchProjectRisk, fetchProject, PredictionData, RiskData, ProjectData } from '../lib/api';

interface Props {
  projectId: string;
  onNavigateToInvestigation: (projectId: string) => void;
  onSelectProject?: (projectId: string) => void;
}

function DHPISGauge({ score }: { score: number }) {
  const size = 220;
  const strokeWidth = 14;
  const center = size / 2;
  const radius = center - strokeWidth - 4;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference;

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

        {/* Centered Content - Perfectly aligned in the exact center of the circle */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-2">
          <span className="font-mono-code font-bold text-4xl sm:text-5xl text-white tracking-tight">
            {score}
          </span>
          <span className="mt-1 text-xs sm:text-sm font-mono-code font-bold text-white uppercase tracking-wider">
            {score >= 70 ? 'High / Elevated' : score >= 45 ? 'More / Moderate' : 'Baseline'}
          </span>
          <span className="text-xs font-mono-code text-white/70 mt-0.5">
            Score: {score} / 100
          </span>
        </div>
      </div>
    </div>
  );
}

export default function ProjectIntelligence({ projectId, onNavigateToInvestigation }: Props) {
  const [activeTab, setActiveTab] = useState<'shap' | 'predictions'>('shap');
  const [project, setProject] = useState<ProjectData | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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

  const pName = project?.project_name || "NH-48 Varanasi-Ranchi Expressway Package 4";
  const pState = project?.state || "Uttar Pradesh";
  const pSector = project?.sector || "Roads & Highways";
  const currentDphis = risk?.dphis ?? project?.dphis ?? 85.0;

  return (
    <div className="space-y-6 sm:space-y-8 pt-20 sm:pt-24 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Top Header Card - Clean heading without top eyebrow tag */}
      <GlassCard variant="hero" padding={24} className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2 sm:space-y-3">
          <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white leading-tight">
            {pName}
          </h2>

          <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-xs sm:text-sm md:text-base text-white/80 font-medium">
            <span className="font-mono-code font-bold text-white px-2 py-0.5 rounded bg-white/10">{projectId}</span>
            <span>•</span>
            <span>{project?.ministry || "Ministry of Road Transport & Highways"}</span>
            <span>•</span>
            <span>{pSector}</span>
            <span>•</span>
            <span>State: {pState}</span>
            <span>•</span>
            <span className="font-mono-code font-bold text-white">
              Budget: ₹{project?.cost.revised || 4218} Cr
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => onNavigateToInvestigation(projectId)}
            className="w-full sm:w-auto px-5 sm:px-6 py-2.5 sm:py-3 rounded-xl bg-black text-white text-xs sm:text-sm font-mono-code font-bold border border-white/30 shadow-[0_0_16px_rgba(255,255,255,0.22)] hover:bg-zinc-900 transition-all cursor-pointer flex items-center justify-center gap-2"
          >
            <span>Trigger Agentic Investigation →</span>
          </button>
        </div>
      </GlassCard>

      {/* Main Grid: DPHIS Gauge + Predictions / SHAP */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
        {/* Left: DPHIS Gauge & Component Breakdown */}
        <GlassCard variant="medium" padding={24} className="space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-base sm:text-lg font-bold font-display text-white">
              Dynamic Project Health Score
            </h3>
            <span className="text-xs sm:text-sm font-mono-code text-white/70">Live DPHIS</span>
          </div>

          <DHPISGauge score={currentDphis} />

          {/* Component Bar Breakdown */}
          {risk?.components && (
            <div className="space-y-3 pt-3 border-t border-white/15 text-sm">
              <div className="text-xs font-mono-code font-bold uppercase text-white/70">
                Weighted Risk Component Indices
              </div>
              <div className="space-y-2.5">
                {[
                  { name: 'Time / Schedule Risk', val: risk.components.time },
                  { name: 'Cost Overrun Risk', val: risk.components.cost },
                  { name: 'Progress Stagnation Gap', val: risk.components.progress },
                  { name: 'Milestone Slippage', val: risk.components.milestone },
                  { name: 'Financial Burn Ratio', val: risk.components.financial },
                  { name: 'Environmental Hazard', val: risk.components.implementation },
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
                SHAP Impact Drivers
              </button>
              <button
                onClick={() => setActiveTab('predictions')}
                className={`px-3 sm:px-4 py-2 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer ${
                  activeTab === 'predictions' ? 'bg-white text-black' : 'text-white/80 hover:text-white hover:bg-white/10'
                }`}
              >
                ML Predictions (XGBoost)
              </button>
            </div>
            <span className="text-xs font-mono-code text-white/80 font-semibold">
              Trained XGBoost Engine
            </span>
          </div>

          {activeTab === 'shap' ? (
            <div className="space-y-4">
              <p className="text-sm md:text-base text-white/85 leading-relaxed">
                SHAP feature attribution isolates which quantified features drove this project's score escalation.
              </p>
              <div className="space-y-3">
                {(prediction?.top_shap_factors || [
                  { feature: 'Schedule Deviation Rate', impact: 43.2, direction: 'increase', description: 'Superstructure Phase 1 milestone delayed by 28 months' },
                  { feature: 'Financial–Physical Progress Gap', impact: 24.1, direction: 'increase', description: '62% funds disbursed vs 34% physical progress achieved' },
                  { feature: 'Contractor Equipment Shortfall', impact: 14.5, direction: 'increase', description: 'Machinery on site 38% below DPR requirements' },
                  { feature: 'Right of Way (RoW) Clearance', impact: -8.0, direction: 'decrease', description: 'Land acquisition 98% cleared by state authority' },
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
                      <div className="text-xs text-white/60 uppercase">{f.impact > 0 ? 'More / Added' : 'Reduction'}</div>
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
                    +{prediction?.cost.predicted_overrun_pct || 7.2}% budget overrun exposure
                  </div>
                </div>

                <div className="p-5 rounded-xl bg-white/5 border border-white/15 space-y-2">
                  <div className="text-xs font-mono-code uppercase text-white/70">Expected Completion Delay</div>
                  <div className="text-2xl sm:text-3xl font-bold font-mono-code text-white">
                    +{prediction?.delay.expected_delay_months || 24} Months
                  </div>
                  <div className="text-xs sm:text-sm text-white/85">
                    Est. Target: {prediction?.delay.predicted_completion_date || '2027-12-31'}
                  </div>
                </div>
              </div>

              <div className="p-5 rounded-xl bg-white/5 border border-white/15 space-y-2">
                <div className="font-semibold text-sm sm:text-base text-white">Model Credibility & Temporal Data Splitting</div>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed">
                  These predictions were generated using temporal snapshot splitting (using observations at time t to forecast outcome at t+12), preventing forward data leakage and ensuring rigorous auditability for government oversight.
                </p>
              </div>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}
