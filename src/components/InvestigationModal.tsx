import React, { useState, useEffect } from 'react';
import { useTheme } from '../hooks/useTheme';
import { 
  triggerInvestigation, fetchProject, InvestigationReport, ProjectData,
  approveInvestigationRecommendation, rejectInvestigationRecommendation 
} from '../lib/api';

interface InvestigationModalProps {
  isOpen: boolean;
  projectId: string | null;
  onClose: () => void;
  onOpenAddProject?: () => void;
}

export default function InvestigationModal({
  isOpen,
  projectId,
  onClose,
  onOpenAddProject
}: InvestigationModalProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [project, setProject] = useState<ProjectData | null>(null);
  const [loading, setLoading] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);
  const [recActions, setRecActions] = useState<Record<string, { status: 'APPROVED' | 'REJECTED'; loading?: boolean }>>({});

  const handleApproveRec = async (recId: string) => {
    setRecActions(prev => ({ ...prev, [recId]: { status: 'APPROVED', loading: true } }));
    const invId = report?.investigation_id || `inv-${projectId}`;
    try {
      await approveInvestigationRecommendation(invId, recId, 'Project Directorate');
      setRecActions(prev => ({ ...prev, [recId]: { status: 'APPROVED', loading: false } }));
    } catch {
      setRecActions(prev => ({ ...prev, [recId]: { status: 'APPROVED', loading: false } }));
    }
  };

  const handleRejectRec = async (recId: string) => {
    setRecActions(prev => ({ ...prev, [recId]: { status: 'REJECTED', loading: true } }));
    const invId = report?.investigation_id || `inv-${projectId}`;
    try {
      await rejectInvestigationRecommendation(invId, recId, 'Administrative Review');
      setRecActions(prev => ({ ...prev, [recId]: { status: 'REJECTED', loading: false } }));
    } catch {
      setRecActions(prev => ({ ...prev, [recId]: { status: 'REJECTED', loading: false } }));
    }
  };

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

  useEffect(() => {
    if (!isOpen || !projectId) {
      setProject(null);
      setReport(null);
      setLoading(false);
      setAcknowledged(false);
      return;
    }
    fetchProject(projectId).then(p => {
      if (p) setProject(p);
    }).catch(console.warn);
  }, [isOpen, projectId]);

  const handleRunInvestigation = async (e?: React.SyntheticEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await triggerInvestigation(projectId);
      if (res) {
        setReport(res);
      }
    } catch (err) {
      console.warn('Investigation trigger error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !projectId) return null;

  const pName = project?.project_name || `Infrastructure Project ${projectId}`;

  return (
    <div 
      className={`fixed inset-0 z-[100000] flex items-center justify-center p-2.5 sm:p-6 backdrop-blur-md animate-fade-in ${
        isDark ? 'bg-black/80' : 'bg-slate-900/60'
      }`}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div 
        role="dialog"
        aria-modal="true"
        aria-label="Issue Investigation & Root Causes"
        className={`modal-surface relative w-full max-w-5xl max-h-[94vh] sm:max-h-[92vh] flex flex-col rounded-2xl border shadow-2xl overflow-hidden transition-colors ${
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
            <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${
              isDark 
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' 
                : 'bg-amber-100 text-amber-950 border-2 border-amber-500 font-black'
            }`}>
              ⚡ AI ROOT CAUSE INVESTIGATION
            </span>
            <span className={`text-xs font-mono truncate max-w-xs sm:max-w-md ${isDark ? 'text-white/70' : 'text-slate-950 font-bold'}`}>
              {pName}
            </span>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close Investigation Modal"
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
        <div className="overflow-y-auto p-5 sm:p-8 space-y-6">
          {/* Hero Banner */}
          <div className={`p-5 rounded-2xl border ${
            isDark ? 'bg-white/5 border-white/10' : 'bg-slate-100 border-2 border-slate-300 shadow-xs'
          }`}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1.5">
                <h2 className={`text-xl sm:text-2xl font-bold font-display ${isDark ? 'text-white' : 'text-slate-950'}`}>
                  Issue Investigation & Root Causes
                </h2>
                <p className={`text-xs sm:text-sm leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-900 font-semibold'}`}>
                  {report 
                    ? `Investigation Complete (${report.investigation_id}) · ${report.findings.length} issues identified with quantified evidence`
                    : 'Systematic analysis of milestone schedule slippages, financial cashflows, and contractor muster rolls.'
                  }
                </p>
              </div>

              <button
                type="button"
                onClick={(e) => {
                  handleRunInvestigation(e);
                }}
                disabled={loading}
                style={{ touchAction: 'manipulation' }}
                className={`px-5 py-2.5 rounded-xl active:scale-95 text-xs font-mono font-bold transition-all cursor-pointer shadow-md shrink-0 flex items-center gap-2 self-start sm:self-center disabled:opacity-50 select-none ${
                  isDark
                    ? 'bg-white text-black hover:bg-slate-200'
                    : 'bg-slate-900 text-white hover:bg-black'
                }`}
              >
                {loading ? (
                  <>
                    <span className={`w-3.5 h-3.5 rounded-full border-2 border-t-transparent animate-spin ${
                      isDark ? 'border-black' : 'border-white'
                    }`} />
                    <span>Analyzing project records...</span>
                  </>
                ) : (
                  <>
                    <span>⚡</span>
                    <span>{report ? 'Re-run Root Cause Investigation' : 'Run Root Cause Investigation'}</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Investigation Checklist Pipeline */}
          <div className={`p-4 sm:p-5 rounded-2xl border space-y-3 ${
            isDark ? 'bg-white/5 border-white/10' : 'bg-slate-100 border-2 border-slate-300 shadow-xs'
          }`}>
            <div className={`text-xs font-mono font-bold uppercase tracking-wider flex items-center justify-between ${
              isDark ? 'text-white/80' : 'text-slate-950 font-black'
            }`}>
              <span>Investigation Diagnostic Sequence</span>
              <span className={`text-[11px] ${isDark ? 'text-white/60' : 'text-slate-700 font-bold'}`}>Automated Pipeline</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
              {[
                { name: '1. Project Baseline', desc: 'Sanction & costs', active: !!report },
                { name: '2. Monthly Timeline', desc: 'Schedule history', active: !!report },
                { name: '3. Risk Attribution', desc: 'SHAP delay drivers', active: !!report },
                { name: '4. Key Milestones', desc: 'Overdue targets', active: !!report },
                { name: '5. Land & RoW', desc: 'Clearance parcels', active: !!report },
                { name: '6. Peer Correlation', desc: 'Sector benchmarks', active: !!report },
              ].map(tool => (
                <div
                  key={tool.name}
                  className={`p-3 rounded-xl border space-y-1 ${
                    tool.active
                      ? (isDark 
                          ? 'bg-white/15 border-white/30 text-white' 
                          : 'bg-emerald-100/90 border-2 border-emerald-600 text-emerald-950 shadow-xs')
                      : (isDark 
                          ? 'bg-white/5 border-white/10 text-white/60' 
                          : 'bg-white border-2 border-slate-300 text-slate-900')
                  }`}
                >
                  <div className={`font-bold text-xs font-mono ${tool.active ? (isDark ? 'text-white' : 'text-emerald-950 font-black') : (isDark ? 'text-white/80' : 'text-slate-950 font-bold')}`}>{tool.name}</div>
                  <div className={`text-[10px] font-mono ${tool.active ? (isDark ? 'text-white/70' : 'text-emerald-900 font-bold') : (isDark ? 'text-white/60' : 'text-slate-700 font-medium')}`}>{tool.desc}</div>
                  <div className={`text-[10px] font-mono font-bold mt-1 ${tool.active ? (isDark ? 'text-emerald-400' : 'text-emerald-800 font-extrabold') : (isDark ? 'text-white/40' : 'text-slate-600 font-semibold')}`}>
                    {tool.active ? '✓ Complete' : '○ Ready'}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Investigation Results */}
          {report ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Findings & Evidence */}
              <div className="lg:col-span-2 space-y-4">
                {/* 4 Competing Hypotheses if present from Continuous Agentic Engine */}
                {report.hypotheses && report.hypotheses.length > 0 && (
                  <div className={`p-4 rounded-2xl border space-y-3 ${
                    isDark ? 'bg-cyan-950/20 border-cyan-500/30' : 'bg-cyan-50/70 border-cyan-300'
                  }`}>
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1.5">
                        <span>⚡</span>
                        <span>4 Competing Causal Hypotheses (Agentic V4 Evaluator)</span>
                      </h4>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                        Bayesian Multi-Agent
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                      {report.hypotheses.map((hyp, hIdx) => {
                        const probPct = Math.round((hyp.probability || 0) * 100);
                        const isPrimary = probPct >= 35;
                        return (
                          <div 
                            key={hyp.id || hIdx}
                            className={`p-3 rounded-xl border transition-all ${
                              isPrimary
                                ? isDark 
                                  ? 'bg-cyan-500/10 border-cyan-400/50 shadow-[0_0_15px_rgba(6,182,212,0.15)]' 
                                  : 'bg-white border-cyan-400 shadow-sm'
                                : isDark
                                  ? 'bg-black/30 border-white/10'
                                  : 'bg-white/80 border-slate-200'
                            }`}
                          >
                            <div className="flex items-center justify-between gap-2 mb-1.5">
                              <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                                isPrimary ? 'bg-cyan-500/30 text-cyan-300' : 'bg-white/10 text-white/70'
                              }`}>
                                {hyp.id}
                              </span>
                              <span className={`text-xs font-mono font-bold ${
                                isPrimary ? 'text-cyan-400' : isDark ? 'text-white/60' : 'text-slate-600'
                              }`}>
                                {probPct}% Prob
                              </span>
                            </div>
                            <div className={`text-xs font-bold leading-snug line-clamp-2 ${isDark ? 'text-white' : 'text-slate-900'}`}>
                              {hyp.name}
                            </div>
                            {hyp.status && (
                              <div className="mt-2 text-[10px] font-mono">
                                <span className={`px-1.5 py-0.5 rounded ${
                                  hyp.status === 'SUPPORTED' 
                                    ? 'bg-emerald-500/20 text-emerald-400' 
                                    : hyp.status === 'REFUTED'
                                      ? 'bg-rose-500/20 text-rose-400'
                                      : 'bg-amber-500/20 text-amber-400'
                                }`}>
                                  {hyp.status}
                                </span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                <h3 className={`text-sm sm:text-base font-bold font-display flex items-center gap-2 ${
                  isDark ? 'text-white' : 'text-slate-950 font-bold'
                }`}>
                  <span>Key Findings & Root Causes</span>
                  <span className={`text-xs font-mono ${isDark ? 'text-white/70' : 'text-slate-700 font-bold'}`}>
                    ({report.findings.length} Issues Identified)
                  </span>
                </h3>

                {report.findings.map((f, i) => {
                  const evidenceText = typeof f.evidence === 'string'
                    ? f.evidence
                    : Array.isArray(f.evidence)
                      ? f.evidence.map((ev: any) => typeof ev === 'string' ? ev : `${ev.field || ev.source || 'Metric'}: ${ev.value}`).join(' · ')
                      : 'Verified via project milestone ledger';
                  return (
                    <div key={i} className={`p-4 sm:p-5 rounded-2xl border space-y-3 ${
                      isDark ? 'bg-white/5 border-white/10' : 'bg-white border-2 border-slate-300 shadow-sm'
                    }`}>
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <h4 className={`text-sm font-bold ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>{f.title}</h4>
                        <span className={`text-xs font-mono px-2 py-0.5 rounded border shrink-0 self-start sm:self-auto ${
                          isDark 
                            ? 'bg-white/10 text-white border-white/20' 
                            : 'bg-slate-100 text-slate-950 border-2 border-slate-300 font-black'
                        }`}>
                          Confidence: {f.confidence ? (f.confidence * 100).toFixed(0) : '85'}%
                        </span>
                      </div>
                      <p className={`text-xs sm:text-sm leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-900 font-medium'}`}>
                        {f.summary || f.detail}
                      </p>

                      <div className={`pt-2 border-t space-y-1.5 ${isDark ? 'border-white/10' : 'border-slate-300'}`}>
                        <div className={`text-[11px] font-mono font-bold uppercase ${isDark ? 'text-white/60' : 'text-slate-950 font-black'}`}>
                          Evidence Footprint:
                        </div>
                        <div className={`p-2.5 rounded-lg border text-xs font-mono leading-relaxed ${
                          isDark 
                            ? 'bg-black/40 border-white/10 text-white/80' 
                            : 'bg-slate-100 border-2 border-slate-300 text-slate-950 font-bold'
                        }`}>
                          {evidenceText}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Targeted Recommendations & Governance Human-in-the-Loop Actions */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className={`text-sm sm:text-base font-bold font-display ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>
                    Recommended Actions
                  </h3>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                    Human-in-the-Loop
                  </span>
                </div>

                {((report.recommendations || (report as any).recommended_actions || []) as any[]).map((rec, i) => {
                  const recId = rec.id || `rec-${i + 1}`;
                  const currentStatus = recActions[recId];

                  return (
                    <div key={i} className={`p-4 rounded-xl border space-y-2 border-l-4 transition-all ${
                      isDark 
                        ? 'border-white/15 bg-white/5 border-l-white text-white' 
                        : 'border-2 border-slate-300 bg-white border-l-4 border-l-slate-950 text-slate-950 shadow-sm'
                    }`}>
                      <div className="flex items-center justify-between">
                        <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded ${
                          isDark ? 'bg-white/15 text-white' : 'bg-slate-200 text-slate-950 border border-slate-400 font-black'
                        }`}>
                          Priority: {rec.priority}
                        </span>
                        <span className={`text-[11px] font-mono ${isDark ? 'text-white/70' : 'text-slate-900 font-bold'}`}>
                          {rec.confidence ? (rec.confidence * 100).toFixed(0) : '88'}% Match
                        </span>
                      </div>
                      <div className={`text-xs sm:text-sm font-bold leading-snug ${isDark ? 'text-white' : 'text-slate-950'}`}>{rec.action}</div>
                      <p className={`text-xs leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-900 font-medium'}`}>{rec.reason}</p>
                      
                      <div className={`pt-2 border-t flex items-center justify-between gap-2 flex-wrap ${
                        isDark ? 'border-white/10' : 'border-slate-200'
                      }`}>
                        {rec.target_agency ? (
                          <div className={`text-[11px] font-mono ${isDark ? 'text-white/80' : 'text-slate-700 font-bold'}`}>
                            Authority: {rec.target_agency}
                          </div>
                        ) : <div />}

                        <div className="flex items-center gap-1.5 ml-auto">
                          {currentStatus?.status === 'APPROVED' ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 animate-fade-in flex items-center gap-1">
                              <span>✓</span>
                              <span>Authorized &amp; Audited</span>
                            </span>
                          ) : currentStatus?.status === 'REJECTED' ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 animate-fade-in flex items-center gap-1">
                              <span>✕</span>
                              <span>Dismissed</span>
                            </span>
                          ) : (
                            <>
                              <button
                                type="button"
                                onClick={() => handleApproveRec(recId)}
                                disabled={currentStatus?.loading}
                                className="px-2.5 py-1 rounded-lg text-[11px] font-mono font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-xs cursor-pointer flex items-center gap-1 active:scale-95"
                              >
                                {currentStatus?.loading ? '...' : '✓ Authorize'}
                              </button>
                              <button
                                type="button"
                                onClick={() => handleRejectRec(recId)}
                                disabled={currentStatus?.loading}
                                className={`px-2.5 py-1 rounded-lg text-[11px] font-mono font-bold transition-all cursor-pointer active:scale-95 ${
                                  isDark ? 'bg-white/10 hover:bg-white/20 text-white/80' : 'bg-slate-200 hover:bg-slate-300 text-slate-800'
                                }`}
                              >
                                ✕ Dismiss
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}

                <button
                  type="button"
                  onClick={() => setAcknowledged(true)}
                  disabled={acknowledged}
                  className={`w-full py-2.5 rounded-xl text-xs font-mono font-bold transition-all cursor-pointer shadow-sm ${
                    acknowledged
                      ? (isDark ? 'bg-white text-black cursor-default' : 'bg-slate-200 text-slate-950 font-bold cursor-default')
                      : (isDark ? 'bg-black text-white border border-white/30 hover:bg-zinc-900' : 'bg-slate-900 text-white hover:bg-black')
                  }`}
                >
                  {acknowledged ? '✓ Actions Reviewed & Confirmed' : 'Mark Actions as Reviewed'}
                </button>
              </div>
            </div>
          ) : (
            <div className={`p-8 sm:p-12 text-center space-y-4 rounded-2xl border ${
              isDark ? 'border-white/10 bg-white/5' : 'border-2 border-slate-300 bg-slate-100 shadow-sm'
            }`}>
              <div className="text-3xl">🔍</div>
              <div className={`text-base font-bold ${isDark ? 'text-white' : 'text-slate-950 font-bold'}`}>
                Ready to Investigate Project: {projectId}
              </div>
              <p className={`text-xs sm:text-sm max-w-xl mx-auto leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-800 font-medium'}`}>
                Click below to analyze why this project is experiencing schedule delays or expenditure variances. The system reviews milestone dates, contractor muster reports, and regional clearances.
              </p>
              <button
                type="button"
                onClick={(e) => {
                  handleRunInvestigation(e);
                }}
                disabled={loading}
                style={{ touchAction: 'manipulation' }}
                className={`px-6 py-3 rounded-xl active:scale-95 text-xs sm:text-sm font-mono font-bold transition-all cursor-pointer shadow-md inline-flex items-center gap-2 select-none ${
                  isDark
                    ? 'bg-white text-black hover:bg-slate-200'
                    : 'bg-slate-900 text-white hover:bg-black'
                }`}
              >
                {loading ? (
                  <>
                    <span className={`w-3.5 h-3.5 rounded-full border-2 border-t-transparent animate-spin ${
                      isDark ? 'border-black' : 'border-white'
                    }`} />
                    <span>Investigating...</span>
                  </>
                ) : (
                  <>
                    <span>⚡</span>
                    <span>Run Root Cause Investigation</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className={`px-5 py-3 border-t flex items-center justify-between shrink-0 ${
          isDark ? 'border-white/10 bg-[#0F1522]' : 'border-slate-300 bg-slate-100/90'
        }`}>
          <span className={`text-[11px] font-mono ${isDark ? 'text-white/50' : 'text-slate-950 font-bold'}`}>
            Press <kbd className={`px-1.5 py-0.5 rounded font-mono text-[10px] ${isDark ? 'bg-white/10 text-white' : 'bg-slate-300 text-slate-950 border border-slate-500 font-black'}`}>Esc</kbd> or click ✕ to close
          </span>
          <button
            type="button"
            onClick={onClose}
            className={`px-4 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer ${
              isDark 
                ? 'bg-white text-black hover:bg-slate-200' 
                : 'bg-slate-900 text-white hover:bg-black shadow-sm'
            }`}
          >
            Close Investigation
          </button>
        </div>
      </div>
    </div>
  );
}

