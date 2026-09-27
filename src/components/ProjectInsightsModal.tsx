import React, { useState, useEffect } from 'react';
import { useTheme } from '../hooks/useTheme';
import { 
  fetchProject, fetchProjectPredictions, fetchProjectRisk, updateProjectThreshold,
  ProjectData, PredictionData, RiskData, UserProfile 
} from '../lib/api';
import { getRiskCategory } from '../lib/risk';

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

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div 
        className={`relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl border shadow-2xl overflow-hidden transition-colors ${
          isDark 
            ? 'bg-[#0B0F17] border-white/20 text-white shadow-[0_25px_80px_rgba(0,0,0,0.95)]' 
            : 'bg-white border-slate-300 text-slate-900 shadow-2xl'
        }`}
      >
        {/* Sticky Header with Close Button */}
        <div className={`px-5 py-4 border-b flex items-center justify-between gap-3 shrink-0 ${
          isDark ? 'border-white/10 bg-[#0F1522]' : 'border-slate-200 bg-slate-50'
        }`}>
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="font-mono-code font-bold text-xs px-2.5 py-0.5 rounded bg-white/10 text-white">
              {projectId}
            </span>
            <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${riskCat.badgeBg}`}>
              {riskCat.label}
            </span>
            <span className={`text-xs font-mono hidden sm:inline ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
              {project?.ministry || 'Assigned Infrastructure Project'}
            </span>
          </div>

          <button
            onClick={onClose}
            aria-label="Close Project Insights"
            className={`w-8 h-8 rounded-lg flex items-center justify-center font-mono font-bold text-sm transition-all cursor-pointer ${
              isDark 
                ? 'bg-white/10 hover:bg-white/20 text-white' 
                : 'bg-slate-200 hover:bg-slate-300 text-slate-800'
            }`}
          >
            ✕
          </button>
        </div>

        {/* Scrollable Modal Content */}
        <div className="overflow-y-auto p-5 sm:p-8 space-y-6 buttery-smooth-scroll">
          {loading ? (
            <div className="py-16 flex flex-col items-center justify-center space-y-4 text-center">
              <div className="w-10 h-10 rounded-full border-2 border-white/20 border-t-white animate-spin" />
              <div className="space-y-1 font-mono text-xs text-white/70">
                <p>Loading project details & risk predictions...</p>
              </div>
            </div>
          ) : (
            <>
              {/* Project Hero Header */}
              <div className={`p-5 rounded-2xl border ${
                isDark ? 'bg-white/5 border-white/10' : 'bg-slate-100 border-slate-200'
              }`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className="text-[11px] font-mono uppercase tracking-wider text-white/60">
                      Project Health & Overview
                    </div>
                    <h2 className="text-xl sm:text-2xl font-bold font-display leading-snug text-white">
                      {pName}
                    </h2>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-white/80 pt-1">
                      <span>📍 {pState}</span>
                      <span>•</span>
                      <span>Sector: {pSector}</span>
                      <span>•</span>
                      <span className="font-mono font-bold text-white">
                        Sanctioned Budget: ₹{pCostCr} Cr
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Project Health & DPHIS Alert Threshold Banner */}
              <div className={`p-4 sm:p-5 rounded-2xl border transition-all ${
                isThresholdCrossed 
                  ? 'bg-amber-500/10 border-amber-500/30' 
                  : (isDark ? 'bg-white/5 border-white/10' : 'bg-slate-100 border-slate-200')
              }`}>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="text-[11px] font-mono uppercase tracking-wider text-white/60 flex items-center gap-2">
                      <span>PROJECT HEALTH</span>
                      <span>•</span>
                      <span className="font-bold text-white">DPHIS {score} / 100</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-2.5 pt-0.5">
                      <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${riskCat.badgeBg}`}>
                        {riskCat.label}
                      </span>
                      <span className="text-xs sm:text-sm font-semibold text-white">
                        Alert Threshold: <strong className="font-mono text-amber-400">{threshold}</strong> / 100
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                        isThresholdCrossed 
                          ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse' 
                          : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                      }`}>
                        {isThresholdCrossed ? '🔔 THRESHOLD CROSSED' : '✓ BELOW THRESHOLD'}
                      </span>
                    </div>
                    <p className="text-xs text-white/70 pt-1">
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
                            ? 'bg-amber-400 text-black border-amber-300' 
                            : 'bg-white/10 hover:bg-white/20 text-white border-white/20'
                        }`}
                      >
                        ⚙️ {isEditingThreshold ? 'Close Edit' : 'Edit Threshold'}
                      </button>
                    </div>
                  )}
                </div>

                {/* Admin Threshold Editor Drawer */}
                {isAdmin && isEditingThreshold && (
                  <div className="mt-4 pt-4 border-t border-white/10 space-y-4 animate-fade-in">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <h4 className="text-xs font-mono font-bold text-white uppercase">
                          Configure Project Alert Threshold
                        </h4>
                        <p className="text-[11px] text-white/60">
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
                          className="w-20 px-3 py-1.5 rounded-lg bg-black/60 border border-amber-500/50 text-amber-300 text-sm font-mono font-bold text-center outline-none"
                        />
                        <button
                          onClick={handleSaveThreshold}
                          disabled={isSavingThreshold}
                          className="px-4 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-black text-xs font-mono font-bold transition-all cursor-pointer disabled:opacity-50"
                        >
                          {isSavingThreshold ? 'Saving...' : 'Save Threshold'}
                        </button>
                      </div>
                    </div>

                    {thresholdSaveSuccess && (
                      <div className="text-xs text-emerald-400 font-mono font-medium">
                        ✓ {thresholdSaveSuccess}
                      </div>
                    )}

                    {/* Threshold History Table */}
                    {project?.threshold_history && project.threshold_history.length > 0 && (
                      <div className="space-y-1.5">
                        <div className="text-[10px] font-mono uppercase text-white/50">Threshold Change History</div>
                        <div className="max-h-28 overflow-y-auto space-y-1 font-mono text-[11px] text-white/70">
                          {project.threshold_history.slice().reverse().map((h, i) => (
                            <div key={i} className="flex items-center justify-between p-1.5 rounded bg-black/30 border border-white/5">
                              <span>
                                {h.old_value !== null ? `${h.old_value} → ` : 'Initial: '}
                                <strong className="text-amber-300">{h.new_value}</strong>
                              </span>
                              <span>By: {h.changed_by}</span>
                              <span className="text-white/40">{new Date(h.timestamp).toLocaleDateString()}</span>
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
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white/70">
                  1. What is happening with this project?
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                  {/* Status Card */}
                  <div className="oled-solid-card p-4 space-y-1.5">
                    <div className="text-[11px] font-mono text-white/60 uppercase">Overall Status</div>
                    <div className={`text-lg font-bold font-mono ${riskCat.colorClass}`}>
                      {riskCat.label}
                    </div>
                    <p className="text-[11px] text-white/75 leading-relaxed">
                      {riskCat.description}
                    </p>
                  </div>

                  {/* Physical Progress */}
                  <div className="oled-solid-card p-4 space-y-2">
                    <div className="text-[11px] font-mono text-white/60 uppercase">Physical Progress</div>
                    <div className="flex items-baseline justify-between font-mono text-sm">
                      <span className="text-white font-bold">Actual: 34%</span>
                      <span className="text-white/60 text-xs">Target: 78%</span>
                    </div>
                    <div className="h-2 rounded-full bg-white/10 overflow-hidden border border-white/15">
                      <div className="h-full bg-white rounded-full" style={{ width: '34%' }} />
                    </div>
                    <div className="text-[10px] text-white/60">44% behind planned progress</div>
                  </div>

                  {/* Budget Spent */}
                  <div className="oled-solid-card p-4 space-y-2">
                    <div className="text-[11px] font-mono text-white/60 uppercase">Budget Utilization</div>
                    <div className="flex items-baseline justify-between font-mono text-sm">
                      <span className="text-white font-bold">Spent: 62%</span>
                      <span className={`text-xs font-semibold ${score >= 65 ? 'text-white' : 'text-white/80'}`}>
                        {score >= 65 ? 'At Risk' : 'Normal'}
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-white/10 overflow-hidden border border-white/15">
                      <div className="h-full bg-white/80 rounded-full" style={{ width: '62%' }} />
                    </div>
                    <div className="text-[10px] text-white/60">Spending faster than physical work</div>
                  </div>

                  {/* Delay Status */}
                  <div className="oled-solid-card p-4 space-y-1.5">
                    <div className="text-[11px] font-mono text-white/60 uppercase">Estimated Delay</div>
                    <div className="text-lg font-bold font-mono text-white">
                      +24 Months
                    </div>
                    <p className="text-[11px] text-white/75 leading-relaxed">
                      Target completion shifted to Dec 2027
                    </p>
                  </div>
                </div>
              </div>

              {/* 2. Why is This Project at Risk? */}
              {/* 2. Recommended Actions */}
              <div className="space-y-3">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white/70">
                  2. Recommended Actions
                </h3>

                <div className="space-y-2.5">
                  <div className="oled-solid-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white text-black">
                          HIGH PRIORITY
                        </span>
                        <h4 className="font-semibold text-xs sm:text-sm text-white">
                          Review Contractor Schedule & Mobilization
                        </h4>
                      </div>
                      <p className="text-xs text-white/75">
                        Issue a directive to the EPC contractor to ramp up pier construction machinery and provide an accelerated catch-up schedule.
                      </p>
                    </div>
                  </div>

                  <div className="oled-solid-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/20 text-white">
                          MEDIUM PRIORITY
                        </span>
                        <h4 className="font-semibold text-xs sm:text-sm text-white">
                          Audit Financial Disbursements vs Ground Progress
                        </h4>
                      </div>
                      <p className="text-xs text-white/75">
                        Verify on-site measurement books (MB) before passing the next interim running invoice to ensure funds correspond to verified physical progress.
                      </p>
                    </div>
                  </div>

                  <div className="oled-solid-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/10 text-white/80">
                          MEDIUM PRIORITY
                        </span>
                        <h4 className="font-semibold text-xs sm:text-sm text-white">
                          Track Upcoming Milestone Review (Next 45 Days)
                        </h4>
                      </div>
                      <p className="text-xs text-white/75">
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
          isDark ? 'border-white/10 bg-[#0F1522]' : 'border-slate-200 bg-slate-50'
        }`}>
          <span className={`text-[11px] font-mono ${isDark ? 'text-white/50' : 'text-slate-500'}`}>
            Press <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-white font-mono text-[10px]">Esc</kbd> or click ✕ to close
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer"
          >
            Close Insights
          </button>
        </div>
      </div>
    </div>
  );
}
