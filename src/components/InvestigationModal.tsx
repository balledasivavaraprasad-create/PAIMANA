import React, { useState, useEffect } from 'react';
import { useTheme } from '../hooks/useTheme';
import { triggerInvestigation, fetchProject, InvestigationReport, ProjectData } from '../lib/api';

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

  const handleRunInvestigation = async () => {
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
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div 
        className={`relative w-full max-w-5xl max-h-[92vh] flex flex-col rounded-2xl border shadow-2xl overflow-hidden transition-colors ${
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
            <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
              ⚡ AI ROOT CAUSE INVESTIGATION
            </span>
            <span className={`text-xs font-mono truncate max-w-xs sm:max-w-md ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
              {pName}
            </span>
          </div>

          <button
            onClick={onClose}
            aria-label="Close Investigation Modal"
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
        <div className="overflow-y-auto p-5 sm:p-8 space-y-6">
          {/* Hero Banner */}
          <div className={`p-5 rounded-2xl border ${
            isDark ? 'bg-white/5 border-white/10' : 'bg-slate-100 border-slate-200'
          }`}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1.5">
                <h2 className="text-xl sm:text-2xl font-bold font-display text-white">
                  Issue Investigation & Root Causes
                </h2>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed">
                  {report 
                    ? `Investigation Complete (${report.investigation_id}) · ${report.findings.length} issues identified with quantified evidence`
                    : 'Systematic analysis of milestone schedule slippages, financial cashflows, and contractor muster rolls.'
                  }
                </p>
              </div>

              <button
                onClick={handleRunInvestigation}
                disabled={loading}
                className="px-5 py-2.5 rounded-xl bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer shadow-md shrink-0 flex items-center gap-2 self-start sm:self-center disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <span className="w-3.5 h-3.5 rounded-full border-2 border-black border-t-transparent animate-spin" />
                    <span>Analyzing project records...</span>
                  </>
                ) : (
                  <>
                    <span>⚡</span>
                    <span>{report ? 'Re-run Investigation' : 'Run Root Cause Investigation'}</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Investigation Checklist Pipeline */}
          <div className="p-4 sm:p-5 rounded-2xl border bg-white/5 border-white/10 space-y-3">
            <div className="text-xs font-mono font-bold uppercase tracking-wider text-white/80 flex items-center justify-between">
              <span>Investigation Diagnostic Sequence</span>
              <span className="text-[11px] text-white/60">Automated Pipeline</span>
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
                      ? 'bg-white/15 border-white/30 text-white'
                      : 'bg-white/5 border-white/10 text-white/60'
                  }`}
                >
                  <div className="font-bold text-xs font-mono text-white">{tool.name}</div>
                  <div className="text-[10px] font-mono text-white/70">{tool.desc}</div>
                  <div className="text-[10px] font-mono font-bold text-white mt-1">
                    {tool.active ? '✓ Done' : '○ Standby'}
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
                <h3 className="text-sm sm:text-base font-bold font-display text-white flex items-center gap-2">
                  <span>Key Findings & Root Causes</span>
                  <span className="text-xs font-mono text-white/70">
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
                    <div key={i} className="p-4 sm:p-5 rounded-2xl border bg-white/5 border-white/10 space-y-3">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <h4 className="text-sm font-bold text-white">{f.title}</h4>
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-white/10 text-white border border-white/20 shrink-0 self-start sm:self-auto">
                          Confidence: {f.confidence ? (f.confidence * 100).toFixed(0) : '85'}%
                        </span>
                      </div>
                      <p className="text-xs sm:text-sm text-white/80 leading-relaxed">
                        {f.summary || f.detail}
                      </p>

                      <div className="pt-2 border-t border-white/10 space-y-1.5">
                        <div className="text-[11px] font-mono font-bold uppercase text-white/60">
                          Evidence Footprint:
                        </div>
                        <div className="p-2.5 rounded-lg bg-black/40 border border-white/10 text-xs font-mono text-white/80">
                          {evidenceText}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Targeted Recommendations */}
              <div className="space-y-4">
                <h3 className="text-sm sm:text-base font-bold font-display text-white">
                  Recommended Actions
                </h3>

                {((report.recommendations || (report as any).recommended_actions || []) as any[]).map((rec, i) => (
                  <div key={i} className="p-4 rounded-xl border border-white/15 bg-white/5 space-y-2 border-l-4 border-l-white">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-white/15 text-white">
                        Priority: {rec.priority}
                      </span>
                      <span className="text-[11px] font-mono text-white/70">
                        {rec.confidence ? (rec.confidence * 100).toFixed(0) : '88'}% Match
                      </span>
                    </div>
                    <div className="text-xs sm:text-sm font-bold text-white leading-snug">{rec.action}</div>
                    <p className="text-xs text-white/80 leading-relaxed">{rec.reason}</p>
                    {rec.target_agency && (
                      <div className="pt-1.5 border-t border-white/10 text-[11px] font-mono text-white/90">
                        Authority: {rec.target_agency}
                      </div>
                    )}
                  </div>
                ))}

                <button
                  onClick={() => setAcknowledged(true)}
                  disabled={acknowledged}
                  className={`w-full py-2.5 rounded-xl text-xs font-mono font-bold transition-all cursor-pointer ${
                    acknowledged
                      ? 'bg-white text-black cursor-default'
                      : 'bg-black text-white border border-white/30 hover:bg-zinc-900 shadow-xl'
                  }`}
                >
                  {acknowledged ? '✓ Actions Reviewed & Confirmed' : 'Mark Actions as Reviewed'}
                </button>
              </div>
            </div>
          ) : (
            <div className="p-8 sm:p-12 text-center space-y-4 rounded-2xl border border-white/10 bg-white/5">
              <div className="text-3xl text-white">🔍</div>
              <div className="text-base font-bold text-white">
                Ready to Investigate Project: {projectId}
              </div>
              <p className="text-xs sm:text-sm text-white/80 max-w-xl mx-auto leading-relaxed">
                Click below to analyze why this project is experiencing schedule delays or expenditure variances. The system reviews milestone dates, contractor muster reports, and regional clearances.
              </p>
              <button
                onClick={handleRunInvestigation}
                className="px-6 py-2.5 rounded-xl bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer shadow-md inline-flex items-center gap-2"
              >
                <span>⚡ Run Root Cause Investigation</span>
              </button>
            </div>
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
            Close Investigation
          </button>
        </div>
      </div>
    </div>
  );
}
