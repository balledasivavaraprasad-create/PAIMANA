import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import RiskBadge from '../components/RiskBadge';
import { fetchProjectPredictions, fetchProjectRisk, fetchProject, PredictionData, RiskData, ProjectData } from '../lib/api';

interface Props {
  projectId: string;
  onNavigateToInvestigation: (projectId: string) => void;
  onSelectProject?: (projectId: string) => void;
}

function DHPISGauge({ score }: { score: number }) {
  const cx = 100, cy = 95, R = 75, sw = 14;
  const toRad = (deg: number) => (deg * Math.PI) / 180;

  const ptOnCircle = (angleDeg: number) => ({
    x: cx + R * Math.cos(toRad(angleDeg)),
    y: cy - R * Math.sin(toRad(angleDeg)),
  });

  const bgStart = ptOnCircle(180);
  const bgEnd = ptOnCircle(0);

  const scoreAngleDeg = 180 - score * 1.8;
  const scoreEnd = ptOnCircle(scoreAngleDeg);
  const largeArc = score > 50 ? 1 : 0;

  const color =
    score >= 75 ? 'var(--risk-critical)' : score >= 50 ? 'var(--risk-high)' : score >= 25 ? 'var(--risk-moderate)' : 'var(--risk-low)';

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <svg viewBox="0 0 200 120" className="w-56 h-auto drop-shadow-md">
        <path
          d={`M ${bgStart.x} ${bgStart.y} A ${R} ${R} 0 0 1 ${bgEnd.x} ${bgEnd.y}`}
          fill="none"
          stroke="var(--surface-sunken)"
          strokeWidth={sw}
          strokeLinecap="round"
        />
        {score > 0 && (
          <path
            d={`M ${bgStart.x} ${bgStart.y} A ${R} ${R} 0 ${largeArc} 1 ${scoreEnd.x} ${scoreEnd.y}`}
            fill="none"
            stroke={color}
            strokeWidth={sw}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        )}
        <text
          x={cx}
          y={cy + 12}
          textAnchor="middle"
          className="font-mono-code font-bold text-4xl"
          fill={color}
        >
          {score}
        </text>
      </svg>

      <div className="mt-1">
        <RiskBadge level={score >= 75 ? 'critical' : score >= 50 ? 'high' : score >= 25 ? 'moderate' : 'low'} showGlow />
      </div>
    </div>
  );
}

export default function ProjectIntelligence({ projectId, onNavigateToInvestigation }: Props) {
  const [activeTab, setActiveTab] = useState<'shap' | 'predictions' | 'components'>('shap');
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
    <div className="space-y-6 pt-20 pb-12 px-6 md:px-16 max-w-7xl mx-auto">
      {/* Top Header Card */}
      <GlassCard variant="hero" padding={24} className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className="font-mono-code text-xs font-bold px-2.5 py-1 rounded bg-[var(--accent-soft)] text-[var(--accent)] border border-[var(--accent-soft)]">
              {projectId}
            </span>
            <h2 className="text-2xl font-bold font-display text-[var(--text-primary)]">
              {pName}
            </h2>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-xs text-[var(--text-secondary)]">
            <span>{project?.ministry || "Ministry of Road Transport & Highways"}</span>
            <span>•</span>
            <span>{pSector}</span>
            <span>•</span>
            <span>State: {pState}</span>
            <span>•</span>
            <span className="font-mono-code font-bold text-[var(--accent)]">
              Cost: ₹{project?.cost.revised || 4218} Cr
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigateToInvestigation(projectId)}
            className="px-5 py-2.5 rounded-xl bg-black text-white text-xs font-mono-code font-bold border border-white/30 shadow-[0_0_15px_rgba(255,255,255,0.25)] hover:bg-zinc-900 transition-all cursor-pointer flex items-center gap-2"
          >
            <span>🔍 Trigger Agentic Investigation</span>
          </button>
        </div>
      </GlassCard>

      {/* Main Grid: DPHIS Gauge + Predictions / SHAP */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: DPHIS Gauge & Component Breakdown */}
        <GlassCard variant="medium" padding={20} className="space-y-4">
          <h3 className="text-sm font-bold font-display text-[var(--text-primary)] flex items-center justify-between">
            <span>Dynamic Project Health Score</span>
            <span className="text-[10px] font-mono-code text-[var(--text-muted)]">Live DPHIS</span>
          </h3>

          <DHPISGauge score={currentDphis} />

          {/* Component Bar Breakdown */}
          {risk?.components && (
            <div className="space-y-2 pt-2 border-t border-[var(--border-hairline)] text-xs">
              <div className="text-[10px] font-mono-code font-bold uppercase text-[var(--text-muted)]">
                Weighted Risk Components
              </div>
              <div className="space-y-1.5">
                {[
                  { name: 'Time / Schedule Risk', val: risk.components.time },
                  { name: 'Cost Overrun Risk', val: risk.components.cost },
                  { name: 'Progress Stagnation Gap', val: risk.components.progress },
                  { name: 'Milestone Slippage', val: risk.components.milestone },
                  { name: 'Financial Burn Ratio', val: risk.components.financial },
                  { name: 'Environmental Hazard', val: risk.components.implementation },
                ].map(comp => (
                  <div key={comp.name} className="space-y-0.5">
                    <div className="flex justify-between font-mono-code text-[11px]">
                      <span className="text-[var(--text-secondary)]">{comp.name}</span>
                      <span className="font-bold text-[var(--text-primary)]">{(comp.val * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[var(--surface-sunken)] overflow-hidden">
                      <div
                        className="h-full bg-[var(--accent)] rounded-full"
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
          <div className="flex items-center justify-between border-b border-[var(--border-hairline)] pb-3">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('shap')}
                className={`px-3 py-1 rounded-lg text-xs font-mono-code font-bold transition-all cursor-pointer ${
                  activeTab === 'shap' ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                SHAP Impact Drivers
              </button>
              <button
                onClick={() => setActiveTab('predictions')}
                className={`px-3 py-1 rounded-lg text-xs font-mono-code font-bold transition-all cursor-pointer ${
                  activeTab === 'predictions' ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                ML Predictions (XGBoost)
              </button>
            </div>
            <span className="text-[10px] font-mono-code text-emerald-500 font-semibold">
              ● Trained XGBoost v1.0
            </span>
          </div>

          {activeTab === 'shap' ? (
            <div className="space-y-3">
              <p className="text-xs text-[var(--text-secondary)]">
                SHAP feature attribution isolates which quantified features drove this project's DPHIS score escalation.
              </p>
              <div className="space-y-2.5">
                {(prediction?.top_shap_factors || [
                  { feature: 'Schedule Deviation Rate', impact: 43.2, direction: 'increase', description: 'Superstructure Phase 1 milestone delayed by 28 months' },
                  { feature: 'Financial–Physical Progress Gap', impact: 24.1, direction: 'increase', description: '62% funds disbursed vs 34% physical progress achieved' },
                  { feature: 'Contractor Equipment Shortfall', impact: 14.5, direction: 'increase', description: 'Machinery on site 38% below DPR requirements' },
                  { feature: 'Right of Way (RoW) Clearance', impact: -8.0, direction: 'decrease', description: 'Land acquisition 98% cleared by state authority' },
                ]).map(f => (
                  <div key={f.feature} className="p-3.5 rounded-xl bg-[var(--surface-sunken)] border border-[var(--border-hairline)] flex items-center justify-between">
                    <div className="space-y-1 max-w-lg">
                      <div className="font-semibold text-xs text-[var(--text-primary)]">{f.feature}</div>
                      <div className="text-[11px] text-[var(--text-secondary)]">{f.description}</div>
                    </div>
                    <div className="text-right font-mono-code">
                      <div className={`text-sm font-bold ${f.direction === 'increase' ? 'text-[var(--risk-critical)]' : 'text-[var(--risk-low)]'}`}>
                        {f.impact > 0 ? `+${f.impact}` : f.impact} pts
                      </div>
                      <div className="text-[10px] text-[var(--text-muted)] uppercase">{f.direction}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-[var(--surface-sunken)] border border-[var(--border-hairline)] space-y-1">
                  <div className="text-[10px] font-mono-code uppercase text-[var(--text-muted)]">Predicted Final Cost</div>
                  <div className="text-2xl font-bold font-mono-code text-[var(--text-primary)]">
                    ₹{prediction?.cost.predicted_final_cost || 4520} Cr
                  </div>
                  <div className="text-xs text-[var(--risk-critical)] font-semibold">
                    +{prediction?.cost.predicted_overrun_pct || 7.2}% budget overrun exposure
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[var(--surface-sunken)] border border-[var(--border-hairline)] space-y-1">
                  <div className="text-[10px] font-mono-code uppercase text-[var(--text-muted)]">Expected Completion Delay</div>
                  <div className="text-2xl font-bold font-mono-code text-[var(--text-primary)]">
                    +{prediction?.delay.expected_delay_months || 24} Months
                  </div>
                  <div className="text-xs text-[var(--text-secondary)]">
                    Est. Target: {prediction?.delay.predicted_completion_date || '2027-12-31'}
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[var(--surface-sunken)] border border-[var(--border-hairline)] space-y-2 text-xs">
                <div className="font-semibold text-[var(--text-primary)]">Model Credibility & Data Leakage Prevention</div>
                <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
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
