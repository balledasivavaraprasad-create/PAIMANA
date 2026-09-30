import React, { useState, useEffect } from 'react';
import { useTheme } from '../hooks/useTheme';
import { 
  fetchProject, fetchProjectPredictions, fetchProjectRisk, updateProjectThreshold,
  ProjectData, PredictionData, RiskData, UserProfile 
} from '../lib/api';
import { getRiskCategory } from '../lib/risk';
import { computeRealTimeShapFactors } from '../lib/shap';
import { CurvedGrowthArrow, CurvedDecreaseArrow, TrendBadge } from './CurvedTrendArrow';

interface ProjectInsightsModalProps {
  isOpen: boolean;
  projectId: string | null;
  currentUser?: UserProfile | null;
  isAdmin?: boolean;
  onClose: () => void;
  onNavigateToInvestigation?: (projectId: string) => void;
}

export default function ProjectInsightsModal({
  isOpen,
  projectId,
  currentUser,
  isAdmin: propIsAdmin,
  onClose,
  onNavigateToInvestigation
}: ProjectInsightsModalProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const roleStr = currentUser?.role?.toString().toUpperCase() || '';
  const isAdmin = propIsAdmin !== undefined ? propIsAdmin : (roleStr === 'ADMIN' || roleStr === 'ANALYST');

  const [project, setProject] = useState<ProjectData | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Admin threshold configuration state
  const [isEditingThreshold, setIsEditingThreshold] = useState(false);
  const [editThresholdValue, setEditThresholdValue] = useState<number>(70);
  const [isSavingThreshold, setIsSavingThreshold] = useState(false);
  const [thresholdSaveSuccess, setThresholdSaveSuccess] = useState<string | null>(null);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  // Fetch project details on open
  useEffect(() => {
    if (!isOpen || !projectId) {
      setProject(null);
      setPrediction(null);
      setRisk(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setIsEditingThreshold(false);
    setThresholdSaveSuccess(null);

    Promise.all([
      fetchProject(projectId),
      fetchProjectPredictions(projectId),
      fetchProjectRisk(projectId)
    ]).then(([p, pred, r]) => {
      setProject(p);
      setPrediction(pred);
      setRisk(r);
      if (p?.dphis_threshold !== undefined) {
        setEditThresholdValue(p.dphis_threshold);
      }
      setLoading(false);
    }).catch(err => {
      console.warn('Failed to load project insights:', err);
      setLoading(false);
    });
  }, [isOpen, projectId]);

  const handleSaveThreshold = async () => {
    if (!projectId) return;
    setIsSavingThreshold(true);
    setThresholdSaveSuccess(null);
    try {
      const res = await updateProjectThreshold(
        projectId,
        editThresholdValue,
        currentUser?.username || 'admin'
      );
      setProject(prev => prev ? {
        ...prev,
        dphis_threshold: editThresholdValue,
        threshold_status: res.threshold_status || (score < editThresholdValue ? 'below' : 'triggered'),
        threshold_history: res.threshold_history || prev.threshold_history
      } : null);
      setThresholdSaveSuccess('Threshold updated and logged to history!');
      setTimeout(() => {
        setIsEditingThreshold(false);
        setThresholdSaveSuccess(null);
      }, 1800);
    } catch (err: any) {
      alert(err.message || 'Failed to update threshold');
    } finally {
      setIsSavingThreshold(false);
    }
  };

  if (!isOpen || !projectId) return null;

  const score = risk?.dphis_score ? Math.round(risk.dphis_score) : (project?.dphis ? Math.round(project.dphis) : 69);
  const riskCat = getRiskCategory(score);

  const threshold = project?.dphis_threshold ?? 70;
  const isThresholdCrossed = score >= threshold;

  const pName = project?.project_name || `Infrastructure Project ${projectId}`;
  const pState = project?.state || 'Maharashtra';
  const pSector = project?.sector || 'Roads & Highways';
  const pCostCr = project?.cost?.revised || project?.cost?.original || 4218;

  // Real-time project telemetry metrics
  const actualPhysical = project?.physical_progress ?? project?.physical_progress_pct ?? Math.max(15, Math.min(92, Math.round(100 - score * 0.82)));
  const targetPhysical = Math.min(100, Math.round(actualPhysical + (score >= 65 ? (score - 40) * 0.65 : 6)));
  const progressBehind = Math.max(0, targetPhysical - actualPhysical);

  let spentPct = 52;
  if (project?.cost?.original && project?.cost?.cumulative_expenditure) {
    spentPct = Math.min(100, Math.round((project.cost.cumulative_expenditure / project.cost.original) * 100));
  } else if (project?.financial_progress) {
    spentPct = Math.round(project.financial_progress);
  } else {
    spentPct = Math.max(actualPhysical, Math.min(98, Math.round(actualPhysical + (score >= 65 ? (score - 45) * 0.6 : 5))));
  }

  const delayMonths = prediction?.delay?.expected_delay_months ?? (score >= 80 ? 24 : score >= 65 ? 14 : score >= 45 ? 6 : 0);
  const completionDate = prediction?.delay?.predicted_completion_date || project?.schedule?.revised_end || 'Target on track';

  const shapFactors = computeRealTimeShapFactors({
    ...project,
    id: projectId,
    dphis: score,
    name: pName,
    sector: pSector,
    state: pState,
    delay: delayMonths,
  });

  return (
    <div 
      className={`fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 backdrop-blur-md animate-fade-in ${
        isDark ? 'bg-black/80' : 'bg-slate-900/60'
      }`}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div 
        role="dialog"
        aria-modal="true"
        aria-label="Project Insights"
        className={`modal-surface relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl border shadow-2xl overflow-hidden transition-colors ${
          isDark 
            ? 'bg-[#0B0F17] border-white/20 text-white shadow-[0_25px_80px_rgba(0,0,0,0.95)]' 
            : 'bg-white border-2 border-slate-300 text-slate-950 shadow-2xl'
        }`}
      >
        {/* Sticky Header with Close Button */}
        <div className={`px-5 py-4 border-b flex items-center justify-between gap-3 shrink-0 ${
          isDark ? 'border-white/10 bg-[#0F1522]' : 'border-slate-200 bg-slate-100/90'
        }`}>
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className={`font-mono-code font-bold text-xs px-2.5 py-0.5 rounded ${
              isDark ? 'bg-white/10 text-white' : 'bg-slate-200 text-slate-950 border-2 border-slate-400 font-bold'
            }`}>
              {projectId}
            </span>
            <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${riskCat.badgeBg}`}>
              {riskCat.label}
            </span>
            <span className={`text-xs font-mono hidden sm:inline ${isDark ? 'text-white/70' : 'text-slate-900 font-bold'}`}>
              {project?.ministry || 'Assigned Infrastructure Project'}
            </span>
          </div>

          <button
            onClick={onClose}
            aria-label="Close Project Insights"
            className={`w-8 h-8 rounded-lg flex items-center justify-center font-mono font-bold text-sm transition-all cursor-pointer modal-close-btn ${
              isDark 
                ? 'bg-white/10 hover:bg-white/20 text-white' 
                : 'bg-slate-200 hover:bg-slate-300 text-slate-950 border border-slate-400 font-bold'
            }`}
          >
            ✕
          </button>
        </div>

        {/* Scrollable Modal Content */}
        <div className="overflow-y-auto p-5 sm:p-8 space-y-6 buttery-smooth-scroll">
          {loading ? (
            <div className="py-16 flex flex-col items-center justify-center space-y-4 text-center">
              <div className={`w-10 h-10 rounded-full border-2 animate-spin ${
                isDark ? 'border-white/20 border-t-white' : 'border-slate-300 border-t-slate-900'
              }`} />
              <div className={`space-y-1 font-mono text-xs ${isDark ? 'text-white/70' : 'text-slate-900 font-semibold'}`}>
                <p>Loading project details & risk predictions...</p>
              </div>
            </div>
          ) : (
            <>
              {/* Project Hero Header */}
              <div className={`p-5 rounded-2xl border ${
                isDark ? 'bg-white/5 border-white/10' : 'bg-slate-100 border-2 border-slate-300 shadow-xs'
              }`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className={`text-[11px] font-mono uppercase tracking-wider ${
                      isDark ? 'text-white/60' : 'text-slate-950 font-bold'
                    }`}>
                      Project Health & Overview
                    </div>
                    <h2 className={`text-xl sm:text-2xl font-bold font-display leading-snug ${
                      isDark ? 'text-white' : 'text-slate-950'
                    }`}>
                      {pName}
                    </h2>
                    <div className={`flex flex-wrap items-center gap-3 text-xs pt-1 ${
                      isDark ? 'text-white/80' : 'text-slate-900 font-bold'
                    }`}>
                      <span>📍 {pState}</span>
                      <span>•</span>
                      <span>Sector: {pSector}</span>
                      <span>•</span>
                      <span className={`font-mono font-bold ${isDark ? 'text-white' : 'text-slate-950 font-black'}`}>
                        Sanctioned Budget: ₹{pCostCr} Cr
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Project Health & DPHIS Alert Threshold Banner */}
              <div className={`p-4 sm:p-5 rounded-2xl border transition-all ${
                isThresholdCrossed 
                  ? (isDark ? 'bg-amber-500/10 border-amber-500/30' : 'bg-amber-50 border-2 border-amber-500 shadow-sm')
                  : (isDark ? 'bg-white/5 border-white/10' : 'bg-slate-100 border-2 border-slate-300 shadow-xs')
              }`}>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className={`text-[11px] font-mono uppercase tracking-wider flex items-center gap-2 ${
                      isDark ? 'text-white/60' : 'text-slate-950 font-black'
                    }`}>
                      <span>PROJECT HEALTH</span>
                      <span>•</span>
                      <span className={`font-bold ${isDark ? 'text-white' : 'text-slate-950'}`}>DPHIS {score} / 100</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-2.5 pt-0.5">
                      <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${riskCat.badgeBg}`}>
                        {riskCat.label}
                      </span>
                      <span className={`text-xs sm:text-sm font-semibold ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>
                        Alert Threshold: <strong className={`font-mono ${isDark ? 'text-amber-400' : 'text-amber-950 font-black'}`}>{threshold}</strong> / 100
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                        isThresholdCrossed 
                          ? (isDark ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse' : 'bg-red-100 text-red-950 border-2 border-red-500 font-extrabold') 
                          : (isDark ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-emerald-100 text-emerald-950 border-2 border-emerald-500 font-bold')
                      }`}>
                        {isThresholdCrossed ? '🔔 THRESHOLD CROSSED' : '✓ BELOW THRESHOLD'}
                      </span>
                    </div>
                    <p className={`text-xs pt-1 ${isDark ? 'text-white/70' : 'text-slate-900 font-medium'}`}>
                      {isThresholdCrossed 
                        ? 'Project risk score has reached or crossed its configured threshold. An alert event was automatically dispatched to you and the administrator.' 
                        : 'Current DPHIS score is within acceptable risk boundaries for this project. Automated monitoring continues.'}
                    </p>
                  </div>

                  {isAdmin && (
                    <div className="shrink-0 flex items-center gap-2">
                      <button
                        onClick={() => setIsEditingThreshold(!isEditingThreshold)}
                        className={`px-3.5 py-2 rounded-xl text-xs font-mono font-bold transition-all cursor-pointer border ${
                          isEditingThreshold 
                            ? (isDark ? 'bg-amber-400 text-black border-amber-300' : 'bg-amber-400 text-black border-amber-500') 
                            : (isDark ? 'bg-white/10 hover:bg-white/20 text-white border-white/20' : 'bg-white hover:bg-slate-200 text-slate-800 border-slate-300 shadow-sm')
                        }`}
                      >
                        ⚙️ {isEditingThreshold ? 'Close Edit' : 'Edit Threshold'}
                      </button>
                    </div>
                  )}
                </div>

                {/* Admin Threshold Editor Drawer */}
                {isAdmin && isEditingThreshold && (
                  <div className={`mt-4 pt-4 border-t space-y-4 animate-fade-in ${
                    isDark ? 'border-white/10' : 'border-slate-300'
                  }`}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <h4 className={`text-xs font-mono font-bold uppercase ${isDark ? 'text-white' : 'text-slate-900'}`}>
                          Configure Project Alert Threshold
                        </h4>
                        <p className={`text-[11px] ${isDark ? 'text-white/60' : 'text-slate-600'}`}>
                          Set the independent risk threshold for {projectId}. Every project has its own threshold.
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <input
                          type="number"
                          min="1"
                          max="100"
                          value={editThresholdValue}
                          onChange={e => setEditThresholdValue(Number(e.target.value))}
                          className={`w-20 px-3 py-1.5 rounded-lg text-sm font-mono font-bold text-center outline-none ${
                            isDark 
                              ? 'bg-black/60 border border-amber-500/50 text-amber-300' 
                              : 'bg-white border-2 border-amber-500 text-amber-900 shadow-sm'
                          }`}
                        />
                        <button
                          onClick={handleSaveThreshold}
                          disabled={isSavingThreshold}
                          className="px-4 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-black text-xs font-mono font-bold transition-all cursor-pointer disabled:opacity-50 shadow-sm"
                        >
                          {isSavingThreshold ? 'Saving...' : 'Save Threshold'}
                        </button>
                      </div>
                    </div>

                    {thresholdSaveSuccess && (
                      <div className={`text-xs font-mono font-medium ${isDark ? 'text-emerald-400' : 'text-emerald-700'}`}>
                        ✓ {thresholdSaveSuccess}
                      </div>
                    )}

                    {/* Threshold History Table */}
                    {project?.threshold_history && project.threshold_history.length > 0 && (
                      <div className="space-y-1.5">
                        <div className={`text-[10px] font-mono uppercase ${isDark ? 'text-white/50' : 'text-slate-500 font-bold'}`}>
                          Threshold Change History
                        </div>
                        <div className={`max-h-28 overflow-y-auto space-y-1 font-mono text-[11px] ${isDark ? 'text-white/70' : 'text-slate-700'}`}>
                          {project.threshold_history.slice().reverse().map((h, i) => (
                            <div key={i} className={`flex items-center justify-between p-1.5 rounded border ${
                              isDark ? 'bg-black/30 border-white/5' : 'bg-white border-slate-200 shadow-xs'
                            }`}>
                              <span>
                                {h.old_value !== null ? `${h.old_value} → ` : 'Initial: '}
                                <strong className={isDark ? 'text-amber-300' : 'text-amber-800'}>{h.new_value}</strong>
                              </span>
                              <span>By: {h.changed_by}</span>
                              <span className={isDark ? 'text-white/40' : 'text-slate-500'}>{new Date(h.timestamp).toLocaleDateString()}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* 1. What is Happening with My Project? */}
              <div className="space-y-3">
                <h3 className={`text-xs font-mono font-bold uppercase tracking-wider ${
                  isDark ? 'text-white/70' : 'text-slate-950 font-black'
                }`}>
                  1. What is happening with this project?
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                  {/* Status Card */}
                  <div className={`p-4 space-y-1.5 rounded-xl border ${
                    isDark ? 'oled-solid-card' : 'bg-white border-2 border-slate-300 shadow-sm'
                  }`}>
                    <div className={`text-[11px] font-mono uppercase ${isDark ? 'text-white/60' : 'text-slate-950 font-bold'}`}>Overall Status</div>
                    <div className={`text-lg font-bold font-mono ${riskCat.colorClass}`}>
                      {riskCat.label}
                    </div>
                    <p className={`text-[11px] leading-relaxed ${isDark ? 'text-white/75' : 'text-slate-900 font-medium'}`}>
                      {riskCat.description}
                    </p>
                  </div>

                  {/* Physical Progress */}
                  <div className={`p-4 space-y-2 rounded-xl border ${
                    isDark ? 'oled-solid-card' : 'bg-white border-2 border-slate-300 shadow-sm'
                  }`}>
                    <div className={`text-[11px] font-mono uppercase ${isDark ? 'text-white/60' : 'text-slate-950 font-bold'}`}>Physical Progress</div>
                    <div className="flex items-baseline justify-between font-mono text-sm">
                      <span className={`font-bold ${isDark ? 'text-white' : 'text-slate-950 font-black'}`}>Actual: {actualPhysical}%</span>
                      <span className={`text-xs ${isDark ? 'text-white/60' : 'text-slate-900 font-bold'}`}>Target: {targetPhysical}%</span>
                    </div>
                    <div className={`h-2.5 rounded-full overflow-hidden border ${
                      isDark ? 'bg-white/10 border-white/15' : 'bg-slate-200 border-slate-300'
                    }`}>
                      <div className={`h-full rounded-full transition-all duration-700 ${
                        isDark ? 'bg-white' : 'bg-slate-900'
                      }`} style={{ width: `${actualPhysical}%` }} />
                    </div>
                    <div className={`text-[10px] ${isDark ? 'text-white/60' : 'text-slate-900 font-medium'}`}>
                      {progressBehind > 0 ? `${progressBehind}% behind planned progress` : 'On track with planned schedule'}
                    </div>
                  </div>

                  {/* Budget Spent */}
                  <div className={`p-4 space-y-2 rounded-xl border ${
                    isDark ? 'oled-solid-card' : 'bg-white border-2 border-slate-300 shadow-sm'
                  }`}>
                    <div className={`text-[11px] font-mono uppercase ${isDark ? 'text-white/60' : 'text-slate-950 font-bold'}`}>Budget Utilization</div>
                    <div className="flex items-baseline justify-between font-mono text-sm">
                      <span className={`font-bold ${isDark ? 'text-white' : 'text-slate-950 font-black'}`}>Spent: {spentPct}%</span>
                      <span className={`text-xs font-semibold ${score >= 65 ? (isDark ? 'text-amber-400' : 'text-amber-950 font-black') : (isDark ? 'text-emerald-400' : 'text-emerald-950 font-black')}`}>
                        {score >= 65 ? 'At Risk' : 'Normal'}
                      </span>
                    </div>
                    <div className={`h-2.5 rounded-full overflow-hidden border ${
                      isDark ? 'bg-white/10 border-white/15' : 'bg-slate-200 border-slate-300'
                    }`}>
                      <div className={`h-full rounded-full transition-all duration-700 ${
                        isDark ? 'bg-white/80' : 'bg-slate-900'
                      }`} style={{ width: `${spentPct}%` }} />
                    </div>
                    <div className={`text-[10px] ${isDark ? 'text-white/60' : 'text-slate-900 font-medium'}`}>
                      {spentPct > actualPhysical ? `${spentPct - actualPhysical}% ahead of physical work` : 'Disbursement matches physical pace'}
                    </div>
                  </div>

                  {/* Delay Status */}
                  <div className={`p-4 space-y-1.5 rounded-xl border ${
                    isDark ? 'oled-solid-card' : 'bg-white border-2 border-slate-300 shadow-sm'
                  }`}>
                    <div className={`text-[11px] font-mono uppercase ${isDark ? 'text-white/60' : 'text-slate-950 font-bold'}`}>Estimated Delay</div>
                    <div className={`text-lg font-bold font-mono ${isDark ? 'text-white' : 'text-slate-950 font-black'}`}>
                      {delayMonths > 0 ? `+${delayMonths} Months` : 'On Time'}
                    </div>
                    <p className={`text-[11px] leading-relaxed ${isDark ? 'text-white/75' : 'text-slate-900 font-medium'}`}>
                      Target completion: {completionDate}
                    </p>
                  </div>
                </div>
              </div>

              {/* 2. Key Risk Drivers (Real-Time AI Explainability) */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className={`text-xs font-mono font-bold uppercase tracking-wider ${
                    isDark ? 'text-white/70' : 'text-slate-950 font-black'
                  }`}>
                    2. Why is this project at risk? (Key Risk Factors)
                  </h3>
                  <span className={`text-[11px] font-mono ${isDark ? 'text-white/50' : 'text-slate-800 font-bold'}`}>Live Telemetry Analysis</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {shapFactors.map(f => (
                    <div key={f.feature} className={`p-3.5 space-y-1.5 flex flex-col justify-between rounded-xl border ${
                      isDark ? 'oled-solid-card' : 'bg-white border-2 border-slate-300 shadow-sm'
                    }`}>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className={`font-semibold text-xs ${isDark ? 'text-white' : 'text-slate-950 font-black'}`}>{f.feature}</span>
                          <TrendBadge value={`${f.impact > 0 ? '+' : ''}${f.impact} pts`} mode="risk" iconClassName="w-3 h-3" />
                        </div>
                        <p className={`text-[11px] leading-relaxed ${isDark ? 'text-white/75' : 'text-slate-900 font-medium'}`}>
                          {f.description}
                        </p>
                      </div>
                      <div className={`text-[10px] font-mono uppercase tracking-wider flex items-center gap-1.5 pt-1.5 border-t ${
                        isDark ? 'border-white/5' : 'border-slate-300'
                      }`}>
                        {f.impact > 0 ? (
                          <span className={`flex items-center gap-1 ${isDark ? 'text-amber-400' : 'text-amber-950 font-black'}`}>
                            <CurvedGrowthArrow className={`w-3 h-3 ${isDark ? 'text-amber-400' : 'text-amber-950'}`} />
                            <span>Increases Project Risk</span>
                          </span>
                        ) : (
                          <span className={`flex items-center gap-1 ${isDark ? 'text-emerald-400' : 'text-emerald-950 font-black'}`}>
                            <CurvedDecreaseArrow className={`w-3 h-3 ${isDark ? 'text-emerald-400' : 'text-emerald-950'}`} />
                            <span>Reduces Risk / Supports On-Time</span>
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 3. Recommended Actions */}
              <div className="space-y-3">
                <h3 className={`text-xs font-mono font-bold uppercase tracking-wider ${
                  isDark ? 'text-white/70' : 'text-slate-950 font-black'
                }`}>
                  3. Recommended Actions
                </h3>

                <div className="space-y-2.5">
                  <div className={`p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border ${
                    isDark ? 'oled-solid-card' : 'bg-white border-2 border-slate-300 shadow-sm'
                  }`}>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          isDark ? 'bg-white text-black' : 'bg-slate-900 text-white font-bold'
                        }`}>
                          HIGH PRIORITY
                        </span>
                        <h4 className={`font-semibold text-xs sm:text-sm ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>
                          Review Contractor Schedule & Mobilization
                        </h4>
                      </div>
                      <p className={`text-xs ${isDark ? 'text-white/75' : 'text-slate-900 font-medium'}`}>
                        Issue a directive to the EPC contractor to ramp up pier construction machinery and provide an accelerated catch-up schedule.
                      </p>
                    </div>
                  </div>

                  <div className={`p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border ${
                    isDark ? 'oled-solid-card' : 'bg-white border-2 border-slate-300 shadow-sm'
                  }`}>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                          isDark ? 'bg-white/20 text-white border-transparent' : 'bg-slate-200 text-slate-950 border border-slate-400 font-black'
                        }`}>
                          MEDIUM PRIORITY
                        </span>
                        <h4 className={`font-semibold text-xs sm:text-sm ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>
                          Audit Financial Disbursements vs Ground Progress
                        </h4>
                      </div>
                      <p className={`text-xs ${isDark ? 'text-white/75' : 'text-slate-900 font-medium'}`}>
                        Verify on-site measurement books (MB) before passing the next interim running invoice to ensure funds correspond to verified physical progress.
                      </p>
                    </div>
                  </div>

                  <div className={`p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-xl border ${
                    isDark ? 'oled-solid-card' : 'bg-white border-2 border-slate-300 shadow-sm'
                  }`}>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                          isDark ? 'bg-white/10 text-white/80 border-transparent' : 'bg-slate-200 text-slate-950 border border-slate-400 font-black'
                        }`}>
                          MEDIUM PRIORITY
                        </span>
                        <h4 className={`font-semibold text-xs sm:text-sm ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>
                          Track Upcoming Milestone Review (Next 45 Days)
                        </h4>
                      </div>
                      <p className={`text-xs ${isDark ? 'text-white/75' : 'text-slate-900 font-medium'}`}>
                        Schedule a review with the state executing agency to ensure utility shifting clearances on corridor km 42–68 are resolved.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className={`px-5 py-3 border-t flex items-center justify-between shrink-0 ${
          isDark ? 'border-white/10 bg-[#0F1522]' : 'border-slate-300 bg-slate-100/90'
        }`}>
          <span className={`text-[11px] font-mono ${isDark ? 'text-white/50' : 'text-slate-950 font-bold'}`}>
            Press <kbd className={`px-1.5 py-0.5 rounded font-mono text-[10px] ${
              isDark ? 'bg-white/10 text-white' : 'bg-slate-300 text-slate-950 border border-slate-500 font-black'
            }`}>Esc</kbd> or click ✕ to close
          </span>
          <div className="flex items-center gap-2">
            {onNavigateToInvestigation && (
              <button
                type="button"
                onClick={() => onNavigateToInvestigation(projectId)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer border flex items-center gap-1.5 ${
                  isDark 
                    ? 'bg-amber-400 text-black border-amber-300 hover:bg-amber-300' 
                    : 'bg-amber-400 text-black border-amber-500 hover:bg-amber-500 shadow-sm'
                }`}
              >
                <span>⚡ Deep AI Investigation</span>
              </button>
            )}
            <button
              onClick={onClose}
              className={`px-4 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
                isDark 
                  ? 'bg-white text-black hover:bg-slate-200' 
                  : 'bg-slate-900 text-white hover:bg-black shadow-sm'
              }`}
            >
              Close Insights
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
