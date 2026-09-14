import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import { triggerInvestigation, fetchProject, InvestigationReport, ProjectData } from '../lib/api';

interface Props {
  projectId?: string;
  onOpenAddProject?: () => void;
}

export default function Investigation({ projectId, onOpenAddProject }: Props) {
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

  const handleRunInvestigation = async () => {
    if (!projectId) return;
    setLoading(true);
    const res = await triggerInvestigation(projectId);
    if (res) {
      setReport(res);
    }
    setLoading(false);
  };

  if (!projectId) {
    return (
      <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        <GlassCard variant="hero" padding={32} className="space-y-6 text-center sm:text-left">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 pb-6 border-b border-white/10">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-400/30">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                <span>No Project Selected</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold font-display text-white">
                Multi-Agent Causal Diagnosis Requires a Capital Asset
              </h2>
              <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
                Autonomous causal diagnosis synthesizes forensic evidence across 57 feature covariates, contractor historical execution velocity, and milestone buffers. Ingest a project to run causal investigations.
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

  const pName = project?.project_name || "NH-48 Varanasi-Ranchi Expressway";

  return (
    <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Header - Clean heading without top eyebrow tags */}
      <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 sm:gap-6">
        <div className="space-y-2">
          <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white">
            Empirical Multi-Agent Causal Diagnosis: Asset {projectId}
          </h2>
          <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
            {pName} · {report ? `Diagnostic Dossier Finalized (${report.investigation_id})` : 'Autonomous algorithmic evidence synthesis across longitudinal snapshot matrices, Shapley factor attributions & critical path milestones'}
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={handleRunInvestigation}
            disabled={loading}
            className="w-full sm:w-auto px-5 sm:px-6 py-2.5 sm:py-3 rounded-xl bg-black text-white text-xs sm:text-sm font-mono-code font-bold border border-white/30 shadow-[0_0_16px_rgba(255,255,255,0.25)] hover:bg-zinc-900 transition-all cursor-pointer flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                <span>Executing Controlled Algorithmic Pipeline...</span>
              </>
            ) : (
              <span>⚡ Initiate Causal Diagnosis Protocol</span>
            )}
          </button>
        </div>
      </GlassCard>

      {/* Tool Execution Sequence - Responsive grid for split-screen and mobile */}
      <GlassCard variant="medium" padding={20} className="space-y-4">
        <div className="text-xs sm:text-sm font-mono-code font-bold uppercase text-white/80 flex flex-wrap items-center justify-between gap-2">
          <span>Autonomous Causal Diagnostic Sequence (Controlled FastAPI Service Layer)</span>
          <span className="text-white font-semibold">Deterministic Execution</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { name: '1. Baseline Corpus', desc: 'tool_get_project', active: !!report },
            { name: '2. Trajectory Sequence', desc: 'tool_get_history', active: !!report },
            { name: '3. Shapley Vectors', desc: 'tool_get_shap', active: !!report },
            { name: '4. Critical Milestones', desc: 'tool_get_milestones', active: !!report },
            { name: '5. Geospatial Topology', desc: 'tool_get_environment', active: !!report },
            { name: '6. Peer Benchmarks', desc: 'tool_compare_peers', active: !!report },
          ].map(tool => (
            <div
              key={tool.name}
              className={`p-3 sm:p-4 rounded-xl border space-y-1.5 ${
                tool.active
                  ? 'bg-white/15 border-white/40 text-white'
                  : 'bg-white/5 border-white/10 text-white/60'
              }`}
            >
              <div className="font-bold text-xs sm:text-sm font-mono-code text-white">{tool.name}</div>
              <div className="text-[10px] sm:text-xs font-mono-code text-white/70">{tool.desc}</div>
              <div className="text-[10px] sm:text-xs font-bold text-white mt-1">
                {tool.active ? '✓ Finalized' : '○ Standby Mode'}
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
            <h3 className="text-base sm:text-lg font-bold font-display text-white flex items-center gap-2">
              <span>Empirically Grounded Causal Findings</span>
              <span className="text-xs sm:text-sm font-mono-code text-white/80">
                ({report.findings.length} Isolated Pathways)
              </span>
            </h3>

            {report.findings.map((f, i) => (
              <GlassCard key={i} variant="medium" padding={22} className="space-y-3 sm:space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <h4 className="text-sm sm:text-base font-bold text-white">{f.title}</h4>
                  <span className="text-xs font-mono-code px-2.5 sm:px-3 py-1 rounded bg-white/10 text-white border border-white/20 shrink-0">
                    Confidence: {(f.confidence * 100).toFixed(0)}% (CI: 95%)
                  </span>
                </div>
                <p className="text-xs sm:text-sm md:text-base text-white/85 leading-relaxed">{f.summary}</p>

                {/* Evidence citations */}
                <div className="pt-3 border-t border-white/15 space-y-2">
                  <div className="text-xs font-mono-code font-bold uppercase text-white/70">
                    Empirical Footprint Audit Traces:
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 sm:gap-3">
                    {f.evidence.map((ev, ei) => (
                      <div key={ei} className="p-2.5 sm:p-3 rounded-xl bg-white/5 border border-white/15 text-xs sm:text-sm font-mono-code">
                        <span className="text-white/70">{ev.source}.{ev.field}: </span>
                        <span className="font-bold text-white">{ev.value}</span>
                        {ev.context && <div className="text-xs text-white/60 mt-1">{ev.context}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>

          {/* Targeted Recommendations */}
          <div className="space-y-4 sm:space-y-5">
            <h3 className="text-base sm:text-lg font-bold font-display text-white">
              Executive Intervention Directives
            </h3>

            {report.recommendations.map((rec, i) => (
              <GlassCard key={i} variant="medium" padding={20} className="space-y-3 border-l-4 border-l-white">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono-code font-bold px-2 py-0.5 rounded bg-white/15 text-white">
                    Statutory Priority: {rec.priority}
                  </span>
                  <span className="text-xs font-mono-code text-white/70">
                    {(rec.confidence * 100).toFixed(0)}% Empirical Congruence
                  </span>
                </div>

                <div className="text-xs sm:text-sm md:text-base font-bold text-white leading-snug">{rec.action}</div>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed">{rec.reason}</p>

                {rec.target_agency && (
                  <div className="pt-2 border-t border-white/15 text-xs font-mono-code text-white/90">
                    Statutory Sponsoring Authority: {rec.target_agency}
                  </div>
                )}
              </GlassCard>
            ))}

            <button
              onClick={() => setAcknowledged(true)}
              disabled={acknowledged}
              className={`w-full py-3 rounded-xl text-xs sm:text-sm font-mono-code font-bold transition-all cursor-pointer ${
                acknowledged
                  ? 'bg-white text-black cursor-default'
                  : 'bg-black text-white border border-white/30 hover:bg-zinc-900 shadow-xl'
              }`}
            >
              {acknowledged ? '✓ Executive Dossier Ratified & Logged to Sovereign Audit Ledger' : 'Ratify & Sign Statutory Directives'}
            </button>
          </div>
        </div>
      ) : (
        <GlassCard variant="medium" padding={36} className="text-center space-y-4">
          <div className="text-3xl sm:text-4xl text-white">🔍</div>
          <div className="text-base sm:text-xl font-bold text-white">
            Algorithmic Causal Investigation Engine Primed: Asset {projectId}
          </div>
          <p className="text-xs sm:text-sm md:text-base text-white/80 max-w-xl mx-auto leading-relaxed">
            Initiating the protocol activates an autonomous diagnostic graph querying multi-temporal snapshot matrices, evaluating additive Shapley decompositions, auditing critical path milestone buffers, and synthesizing deterministic evidence footprints.
          </p>
          <button
            onClick={handleRunInvestigation}
            className="w-full sm:w-auto px-6 sm:px-7 py-3 rounded-xl bg-black text-white text-xs sm:text-sm font-mono-code font-bold border border-white/30 shadow-[0_0_16px_rgba(255,255,255,0.2)] hover:bg-zinc-900 cursor-pointer"
          >
            ⚡ Initiate Causal Diagnosis Protocol
          </button>
        </GlassCard>
      )}
    </div>
  );
}
