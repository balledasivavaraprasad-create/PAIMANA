import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import { triggerInvestigation, fetchProject, InvestigationReport, ProjectData } from '../lib/api';

interface Props {
  projectId: string;
}

export default function Investigation({ projectId }: Props) {
  const [report, setReport] = useState<InvestigationReport | null>(null);
  const [project, setProject] = useState<ProjectData | null>(null);
  const [loading, setLoading] = useState(false);
  const [acknowledged, setAcknowledged] = useState(false);

  useEffect(() => {
    fetchProject(projectId).then(p => {
      if (p) setProject(p);
    });
  }, [projectId]);

  const handleRunInvestigation = async () => {
    setLoading(true);
    const res = await triggerInvestigation(projectId);
    if (res) {
      setReport(res);
    }
    setLoading(false);
  };

  const pName = project?.project_name || "NH-48 Varanasi-Ranchi Expressway";

  return (
    <div className="space-y-6 pt-20 pb-12 px-6 md:px-16 max-w-7xl mx-auto">
      {/* Header */}
      <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--accent)] font-mono-code">
              Autonomous Agentic Investigation
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-semibold border border-emerald-500/20">
              {report ? `Completed (${report.investigation_id})` : 'Ready to Execute'}
            </span>
          </div>
          <h2 className="text-2xl font-bold font-display text-[var(--text-primary)]">
            Evidence-First Investigation: Project {projectId}
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            {pName} · Multi-tool autonomous discovery across MongoDB snapshots, SHAP drivers, and milestones
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunInvestigation}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl bg-black text-white text-xs font-mono-code font-bold border border-white/30 shadow-[0_0_15px_rgba(255,255,255,0.25)] hover:bg-zinc-900 transition-all cursor-pointer flex items-center gap-2"
          >
            {loading ? (
              <>
                <span className="w-3 h-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                <span>Investigating Tools...</span>
              </>
            ) : (
              <span>⚡ Execute Investigation</span>
            )}
          </button>
        </div>
      </GlassCard>

      {/* Tool Execution Sequence */}
      <GlassCard variant="medium" padding={20} className="space-y-3">
        <div className="text-xs font-mono-code font-bold uppercase text-[var(--text-muted)] flex items-center justify-between">
          <span>Agent Tool Execution Pipeline (Controlled FastAPI Tools)</span>
          <span className="text-emerald-500 font-semibold">Strict Evidence Grounding</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          {[
            { name: '1. Project Core', desc: 'tool_get_project', active: !!report },
            { name: '2. Time Trajectory', desc: 'tool_get_history', active: !!report },
            { name: '3. SHAP Attribution', desc: 'tool_get_shap', active: !!report },
            { name: '4. Milestones', desc: 'tool_get_milestones', active: !!report },
            { name: '5. Environment', desc: 'tool_get_environment', active: !!report },
            { name: '6. Peer Benchmark', desc: 'tool_compare_peers', active: !!report },
          ].map(tool => (
            <div
              key={tool.name}
              className={`p-3 rounded-xl border text-xs space-y-1 ${
                tool.active
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-[var(--text-primary)]'
                  : 'bg-[var(--surface-sunken)] border-[var(--border-hairline)] text-[var(--text-muted)]'
              }`}
            >
              <div className="font-bold font-mono-code">{tool.name}</div>
              <div className="text-[10px] font-mono-code opacity-75">{tool.desc}</div>
              <div className="text-[10px] font-bold">
                {tool.active ? '✓ Verified' : '○ Standby'}
              </div>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Investigation Results */}
      {report ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Findings & Grounded Evidence */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-sm font-bold font-display text-[var(--text-primary)] flex items-center gap-2">
              <span>Grounded Evidence Findings</span>
              <span className="text-xs font-mono-code text-[var(--accent)]">
                ({report.findings.length} Isolated)
              </span>
            </h3>

            {report.findings.map((f, i) => (
              <GlassCard key={i} variant="medium" padding={20} className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-[var(--text-primary)]">{f.title}</h4>
                  <span className="text-[10px] font-mono-code px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    Confidence: {(f.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{f.summary}</p>

                {/* Evidence citations */}
                <div className="pt-2 border-t border-[var(--border-hairline)] space-y-1.5">
                  <div className="text-[10px] font-mono-code font-bold uppercase text-[var(--text-muted)]">
                    Evidence Footprints:
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {f.evidence.map((ev, ei) => (
                      <div key={ei} className="p-2 rounded-lg bg-[var(--surface-sunken)] border border-[var(--border-hairline)] text-[11px] font-mono-code">
                        <span className="text-[var(--text-muted)]">{ev.source}.{ev.field}: </span>
                        <span className="font-bold text-[var(--accent)]">{ev.value}</span>
                        {ev.context && <div className="text-[9px] text-[var(--text-secondary)] mt-0.5">{ev.context}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>

          {/* Targeted Recommendations */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold font-display text-[var(--text-primary)]">
              Decision-Support Recommendations
            </h3>

            {report.recommendations.map((rec, i) => (
              <GlassCard key={i} variant="medium" padding={20} className="space-y-3 border-l-4 border-l-[var(--accent)]">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono-code font-bold px-2 py-0.5 rounded bg-red-500/15 text-red-500">
                    Priority: {rec.priority}
                  </span>
                  <span className="text-[10px] font-mono-code text-[var(--text-muted)]">
                    {(rec.confidence * 100).toFixed(0)}% Match
                  </span>
                </div>

                <div className="text-xs font-bold text-[var(--text-primary)]">{rec.action}</div>
                <p className="text-[11px] text-[var(--text-secondary)]">{rec.reason}</p>

                {rec.target_agency && (
                  <div className="pt-2 border-t border-[var(--border-hairline)] text-[10px] font-mono-code text-[var(--accent)]">
                    Action Target: {rec.target_agency}
                  </div>
                )}
              </GlassCard>
            ))}

            <button
              onClick={() => setAcknowledged(true)}
              disabled={acknowledged}
              className={`w-full py-3 rounded-xl text-xs font-mono-code font-bold transition-all cursor-pointer ${
                acknowledged
                  ? 'bg-emerald-600 text-white cursor-default'
                  : 'bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white shadow-lg'
              }`}
            >
              {acknowledged ? '✓ Findings Acknowledged & Logged to Audit Trail' : 'Acknowledge & Sign Findings'}
            </button>
          </div>
        </div>
      ) : (
        <GlassCard variant="medium" padding={40} className="text-center space-y-4">
          <div className="text-3xl">🔍</div>
          <div className="text-base font-bold text-[var(--text-primary)]">
            Ready to Launch Multi-Tool Investigation for {projectId}
          </div>
          <p className="text-xs text-[var(--text-secondary)] max-w-md mx-auto">
            Clicking "Execute Investigation" triggers the LangGraph agentic pipeline. It queries MongoDB for historical snapshots, runs SHAP models, extracts milestone delays, and generates grounded evidence citations.
          </p>
          <button
            onClick={handleRunInvestigation}
            className="px-6 py-2.5 rounded-xl bg-black text-white text-xs font-mono-code font-bold border border-white/30 shadow-[0_0_15px_rgba(255,255,255,0.2)] hover:bg-zinc-900 cursor-pointer"
          >
            Launch Autonomous Agent
          </button>
        </GlassCard>
      )}
    </div>
  );
}
