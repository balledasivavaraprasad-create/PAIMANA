import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import { triggerInvestigation, fetchProject, InvestigationReport, ProjectData } from '../lib/api';
import { useTheme } from '../hooks/useTheme';

interface Props {
  projectId?: string;
  onOpenAddProject?: () => void;
}

export default function Investigation({ projectId, onOpenAddProject }: Props) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [project, setProject] = useState<ProjectData | null>(null);
  const [loading, setLoading] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);

  useEffect(() => {
    if (!projectId) {
      setProject(null);
      setReport(null);
      return;
    }
    fetchProject(projectId).then(p => {
      if (p) setProject(p);
    });
  }, [projectId]);

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
    } finally {
      setLoading(false);
    }
  };

  if (!projectId) {
    return (
      <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        <GlassCard variant="hero" padding={32} className="space-y-6 text-center sm:text-left">
          <div className={`flex flex-col sm:flex-row items-center justify-between gap-6 pb-6 border-b ${isDark ? 'border-white/10' : 'border-slate-200'}`}>
            <div className="space-y-2 max-w-2xl">
              <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-mono font-bold ${
                isDark ? 'bg-amber-500/20 text-amber-300 border border-amber-400/30' : 'bg-amber-100 text-amber-900 border border-amber-300'
              }`}>
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <span>No Project Selected</span>
              </div>
              <h2 className={`text-2xl sm:text-3xl font-bold font-display ${isDark ? 'text-white' : 'text-slate-900'}`}>
                Select a Project to Start Investigation
              </h2>
              <p className={`text-xs sm:text-sm md:text-base leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-600'}`}>
                To investigate delay causes and budget issues, please add or select a project from your dashboard first.
              </p>
            </div>

            {onOpenAddProject && (
              <button
                onClick={onOpenAddProject}
                style={!isDark ? { color: '#ffffff' } : undefined}
                className={`px-6 py-3.5 rounded-xl text-sm font-mono-code font-bold transition-all cursor-pointer shadow-md flex items-center gap-2 shrink-0 ${
                  isDark ? 'bg-white text-black hover:bg-slate-200' : 'bg-slate-900 text-white hover:bg-black shadow-slate-300'
                }`}
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

  const pName = project?.project_name || "NH-48 Varanasi-Ranchi Expressway";

  return (
    <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Header - Clean heading without top eyebrow tags */}
      <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 sm:gap-6">
        <div className="space-y-2">
          <h2 className={`text-xl sm:text-2xl md:text-3xl font-bold font-display ${isDark ? 'text-white' : 'text-slate-900'}`}>
            Project Investigation &amp; Root Causes: {projectId}
          </h2>
          <p className={`text-xs sm:text-sm md:text-base leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-600'}`}>
            {pName} · {report ? `Investigation Complete (${report.investigation_id})` : 'Analyzing milestone delays, monthly spending, and contractor progress to find clear solutions.'}
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={(e) => {
              handleRunInvestigation(e);
            }}
            disabled={loading}
            style={{ touchAction: 'manipulation', ...(!isDark ? { color: '#ffffff' } : undefined) }}
            className={`w-full sm:w-auto px-5 sm:px-6 py-2.5 sm:py-3 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer flex items-center justify-center gap-2 select-none shadow-md disabled:opacity-50 ${
              isDark 
                ? 'bg-black text-white border border-white/30 hover:bg-zinc-900 shadow-[0_0_16px_rgba(255,255,255,0.25)]' 
                : 'bg-slate-900 text-white hover:bg-black shadow-slate-300'
            }`}
          >
            {loading ? (
              <>
                <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                <span style={!isDark ? { color: '#ffffff' } : undefined}>Analyzing project records...</span>
              </>
            ) : (
              <span style={!isDark ? { color: '#ffffff' } : undefined}>
                ⚡ {report ? 'Re-run Root Cause Investigation' : 'Run Root Cause Investigation'}
              </span>
            )}
          </button>
        </div>
      </GlassCard>

      {/* Tool Execution Sequence - Responsive grid for split-screen and mobile */}
      <GlassCard variant="medium" padding={20} className="space-y-4">
        <div className={`text-xs sm:text-sm font-mono-code font-bold uppercase flex flex-wrap items-center justify-between gap-2 ${
          isDark ? 'text-white/80' : 'text-slate-700'
        }`}>
          <span>Investigation Checklist</span>
          <span className={`font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>Automated Checks</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { name: '1. Project Baseline', desc: 'Project details & costs', active: !!report },
            { name: '2. Monthly Timeline', desc: 'Past monthly reports', active: !!report },
            { name: '3. Key Risk Factors', desc: 'Delay drivers & impacts', active: !!report },
            { name: '4. Key Milestones', desc: 'Target completion dates', active: !!report },
            { name: '5. Land & Clearances', desc: 'Site status & permits', active: !!report },
            { name: '6. Peer Comparison', desc: 'Similar project records', active: !!report },
          ].map(tool => (
            <div
              key={tool.name}
              className={`p-3 sm:p-4 rounded-xl border space-y-1.5 transition-all ${
                tool.active
                  ? (isDark ? 'bg-white/15 border-white/40 text-white' : 'bg-slate-900 text-white border-slate-900 shadow-sm')
                  : (isDark ? 'bg-white/5 border-white/10 text-white/60' : 'bg-white border-slate-200 text-slate-700 shadow-xs')
              }`}
            >
              <div 
                style={tool.active && !isDark ? { color: '#ffffff' } : undefined}
                className={`font-bold text-xs sm:text-sm font-mono-code ${
                  tool.active ? 'text-white' : (isDark ? 'text-white' : 'text-slate-900')
                }`}
              >
                {tool.name}
              </div>
              <div 
                style={tool.active && !isDark ? { color: '#cbd5e1' } : undefined}
                className={`text-[10px] sm:text-xs font-mono-code ${
                  tool.active ? (isDark ? 'text-white/80' : 'text-slate-300') : (isDark ? 'text-white/70' : 'text-slate-500')
                }`}
              >
                {tool.desc}
              </div>
              <div 
                style={tool.active && !isDark ? { color: '#34d399' } : undefined}
                className={`text-[10px] sm:text-xs font-bold mt-1 ${
                  tool.active ? 'text-emerald-400' : (isDark ? 'text-white/50' : 'text-slate-400')
                }`}
              >
                {tool.active ? '✓ Done' : '○ Ready'}
              </div>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Investigation Results */}
      {report ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
          {/* Findings & Grounded Evidence */}
          <div className="lg:col-span-2 space-y-4 sm:space-y-5">
            <h3 className={`text-base sm:text-lg font-bold font-display flex items-center gap-2 ${
              isDark ? 'text-white' : 'text-slate-900'
            }`}>
              <span>Key Findings &amp; Root Causes</span>
              <span className={`text-xs sm:text-sm font-mono-code ${isDark ? 'text-white/80' : 'text-slate-600'}`}>
                ({report.findings.length} Issues Identified)
              </span>
            </h3>

            {report.findings.map((f, i) => (
              <GlassCard key={i} variant="medium" padding={22} className="space-y-3 sm:space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <h4 className={`text-sm sm:text-base font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{f.title}</h4>
                  <span className={`text-xs font-mono-code px-2.5 sm:px-3 py-1 rounded border shrink-0 ${
                    isDark ? 'bg-white/10 text-white border-white/20' : 'bg-slate-100 text-slate-800 font-bold border-slate-300'
                  }`}>
                    Confidence: {(((f.confidence ?? 0.85)) * 100).toFixed(0)}%
                  </span>
                </div>
                <p className={`text-xs sm:text-sm md:text-base leading-relaxed ${isDark ? 'text-white/85' : 'text-slate-700'}`}>{f.summary}</p>

                {/* Evidence citations */}
                <div className={`pt-3 border-t space-y-2 ${isDark ? 'border-white/15' : 'border-slate-200'}`}>
                  <div className={`text-xs font-mono-code font-bold uppercase ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
                    Evidence &amp; Verified Data:
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 sm:gap-3">
                    {Array.isArray(f.evidence) ? f.evidence.map((ev: any, ei: number) => (
                      <div key={ei} className={`p-2.5 sm:p-3 rounded-xl border text-xs sm:text-sm font-mono-code ${
                        isDark ? 'bg-white/5 border-white/15' : 'bg-slate-50 border-slate-200 text-slate-800'
                      }`}>
                        <span className={isDark ? 'text-white/70' : 'text-slate-600'}>{ev?.source || 'Source'}.{ev?.field || 'Metric'}: </span>
                        <span className={`font-bold ${isDark ? 'text-white' : 'text-slate-950'}`}>{String(ev?.value ?? '')}</span>
                        {ev?.context && <div className={`text-xs mt-1 ${isDark ? 'text-white/60' : 'text-slate-500'}`}>{ev.context}</div>}
                      </div>
                    )) : (
                      <div className={`p-2.5 sm:p-3 rounded-xl border text-xs sm:text-sm font-mono-code ${
                        isDark ? 'bg-white/5 border-white/15 text-white/80' : 'bg-slate-50 border-slate-200 text-slate-800'
                      }`}>
                        {String(f.evidence || '')}
                      </div>
                    )}
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>

          {/* Targeted Recommendations */}
          <div className="space-y-4 sm:space-y-5">
            <h3 className={`text-base sm:text-lg font-bold font-display ${isDark ? 'text-white' : 'text-slate-900'}`}>
              Recommended Actions
            </h3>

            {(report.recommendations || []).map((rec, i) => (
              <GlassCard key={i} variant="medium" padding={20} className={`space-y-3 border-l-4 ${
                isDark ? 'border-l-white' : 'border-l-slate-900 border border-slate-200'
              }`}>
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-mono-code font-bold px-2 py-0.5 rounded border ${
                    isDark ? 'bg-white/15 text-white border-transparent' : 'bg-slate-100 text-slate-800 border-slate-300'
                  }`}>
                    Priority: {rec.priority}
                  </span>
                  <span className={`text-xs font-mono-code ${isDark ? 'text-white/70' : 'text-slate-500'}`}>
                    {(((rec.confidence ?? 0.88)) * 100).toFixed(0)}% Match
                  </span>
                </div>

                <div className={`text-xs sm:text-sm md:text-base font-bold leading-snug ${isDark ? 'text-white' : 'text-slate-900'}`}>{rec.action}</div>
                <p className={`text-xs sm:text-sm leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-600'}`}>{rec.reason}</p>

                {rec.target_agency && (
                  <div className={`pt-2 border-t text-xs font-mono-code ${
                    isDark ? 'border-white/15 text-white/90' : 'border-slate-200 text-slate-700'
                  }`}>
                    Responsible Authority: {rec.target_agency}
                  </div>
                )}
              </GlassCard>
            ))}

            <button
              onClick={() => setAcknowledged(true)}
              disabled={acknowledged}
              style={!isDark ? { color: '#ffffff' } : undefined}
              className={`w-full py-3 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer shadow-md ${
                acknowledged
                  ? (isDark ? 'bg-white text-black cursor-default' : 'bg-emerald-600 text-white cursor-default')
                  : (isDark ? 'bg-black text-white border border-white/30 hover:bg-zinc-900 shadow-xl' : 'bg-slate-900 text-white hover:bg-black shadow-slate-300')
              }`}
            >
              <span style={!isDark ? { color: '#ffffff' } : undefined}>
                {acknowledged ? '✓ Actions Reviewed & Confirmed' : 'Mark Actions as Reviewed'}
              </span>
            </button>
          </div>
        </div>
      ) : (
        <GlassCard variant="medium" padding={36} className="text-center space-y-4">
          <div className="text-3xl sm:text-4xl">🔍</div>
          <div className={`text-base sm:text-xl font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
            Ready to Investigate Project: {projectId}
          </div>
          <p className={`text-xs sm:text-sm md:text-base max-w-xl mx-auto leading-relaxed ${
            isDark ? 'text-white/80' : 'text-slate-600'
          }`}>
            Click below to analyze why this project is delayed or over budget. The system will review milestone dates, monthly spending, and contractor progress to find clear solutions.
          </p>
          <button
            type="button"
            onClick={handleRunInvestigation}
            onTouchEnd={(e) => {
              e.stopPropagation();
            }}
            disabled={loading}
            style={{ touchAction: 'manipulation', ...(!isDark ? { color: '#ffffff' } : undefined) }}
            className={`w-full sm:w-auto px-6 sm:px-7 py-3 rounded-xl text-xs sm:text-sm font-mono-code font-bold active:scale-95 cursor-pointer select-none shadow-md ${
              isDark ? 'bg-black text-white border border-white/30 hover:bg-zinc-900 shadow-[0_0_16px_rgba(255,255,255,0.2)]' : 'bg-slate-900 text-white hover:bg-black shadow-slate-300'
            }`}
          >
            <span style={!isDark ? { color: '#ffffff' } : undefined}>⚡ Investigate the Issue</span>
          </button>
        </GlassCard>
      )}
    </div>
  );
}
