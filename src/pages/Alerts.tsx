import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import { fetchAlerts, acknowledgeAlert, triggerN8nRiskEvent, AlertItem, UserProfile } from '../lib/api';
import { getRiskCategory } from '../lib/risk';

interface Props {
  onNavigateToInvestigation?: (projectId: string) => void;
  onNavigateToProject?: (projectId: string) => void;
  currentUser?: UserProfile | null;
  pinsCount?: number;
  onOpenAddProject?: () => void;
}

export default function Alerts({ 
  onNavigateToInvestigation, 
  onNavigateToProject,
  currentUser, 
  pinsCount, 
  onOpenAddProject 
}: Props) {
  const isAdmin = currentUser?.role === 'ADMIN' || currentUser?.role === 'ANALYST';
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Admin-only configurable alert threshold and n8n credentials
  const [userThreshold, setUserThreshold] = useState<number>(currentUser?.dphis_alert_threshold ?? 75.0);
  const [recipientEmail, setRecipientEmail] = useState<string>(currentUser?.alert_email || currentUser?.email || 'balledasivavaraprasad@gmail.com');
  const [simulatedDphis, setSimulatedDphis] = useState<number>(84.5);
  const [isTriggering, setIsTriggering] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<any | null>(null);

  useEffect(() => {
    if (currentUser?.dphis_alert_threshold) {
      setUserThreshold(currentUser.dphis_alert_threshold);
    }
    if (currentUser?.alert_email || currentUser?.email) {
      setRecipientEmail(currentUser.alert_email || currentUser.email);
    }
  }, [currentUser]);

  const loadAlerts = () => {
    fetchAlerts().then(items => {
      setAlerts(items);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleAcknowledge = async (alertId: string) => {
    const ok = await acknowledgeAlert(alertId);
    if (ok) {
      setAlerts(prev => prev.map(a => a.alert_id === alertId ? { ...a, status: 'ACKNOWLEDGED' } : a));
    }
  };

  const handleTriggerSimulation = async () => {
    setIsTriggering(true);
    setSimulationResult(null);
    try {
      const res = await triggerN8nRiskEvent({
        projectId: 'P1024',
        dphis: simulatedDphis,
        threshold: userThreshold,
        recipientEmail: recipientEmail,
        recipientName: currentUser?.full_name || 'Executive Officer'
      });
      setSimulationResult(res);
      if (res.threshold_exceeded) {
        setTimeout(loadAlerts, 1500);
      }
    } catch (err: any) {
      setSimulationResult({
        success: false,
        threshold_exceeded: false,
        message: err.message || 'Dispatch failed'
      });
    } finally {
      setIsTriggering(false);
    }
  };

  if (pinsCount === 0) {
    return (
      <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        <GlassCard variant="hero" padding={32} className="space-y-6 text-center sm:text-left">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 pb-6 border-b border-white/10">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-400/30">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span>No Alerts Yet</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold font-display text-white">
                All Clear · No Projects Flagged
              </h2>
              <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
                When you add projects, any critical cost increases or milestone delays will automatically appear here as alerts.
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

  const pendingCount = alerts.filter(a => a.status === 'PENDING').length;

  /* =========================================================================
     NORMAL USER VIEW — "Your Project Alerts"
     No technical config, no webhooks, no test buttons.
     Clean, actionable project warnings.
     ========================================================================= */
  if (!isAdmin) {
    return (
      <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        {/* Header */}
        <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white">
              Your Project Alerts
            </h2>
            <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
              {pendingCount > 0 
                ? `${pendingCount} alerts require your review for projects in your department.`
                : 'All projects are currently progressing within approved parameters.'
              }
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={loadAlerts}
              className="px-4 py-2 rounded-xl bg-white text-black text-xs font-mono font-bold hover:bg-zinc-200 cursor-pointer transition-all shadow-md"
            >
              ↻ Refresh
            </button>
          </div>
        </GlassCard>

        {/* Normal User Alert Cards */}
        {alerts.length === 0 ? (
          <GlassCard variant="medium" padding={32} className="text-center space-y-3">
            <div className="text-base font-bold text-white">No Active Alerts</div>
            <p className="text-xs sm:text-sm text-white/70">
              There are no pending alerts for your projects at this time.
            </p>
          </GlassCard>
        ) : (
          <div className="space-y-4">
            {alerts.map(a => {
              const cat = getRiskCategory(a.dphis);
              const isAcknowledged = a.status === 'ACKNOWLEDGED';

              return (
                <div
                  key={a.alert_id}
                  className={`oled-solid-card p-5 sm:p-6 space-y-4 transition-all ${
                    isAcknowledged ? 'opacity-65 border-white/10' : 'border-white/25 hover:border-white/40'
                  }`}
                >
                  {/* Top Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 pb-3">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${cat.badgeBg}`}>
                        {cat.label} ALERT
                      </span>
                      <span className="font-mono-code font-bold text-xs text-white px-2 py-0.5 rounded bg-white/10">
                        {a.project_id}
                      </span>
                    </div>

                    <div className="text-[11px] font-mono text-white/60">
                      {a.created_at ? new Date(a.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Recent'}
                    </div>
                  </div>

                  {/* Project Name & What Changed */}
                  <div className="space-y-1">
                    <h3 className="text-base sm:text-lg font-bold text-white">
                      {a.project_name || `Project ${a.project_id}`}
                    </h3>
                    <div className="text-xs sm:text-sm text-white/90 font-medium">
                      <strong>What changed:</strong> Physical progress has fallen significantly below the planned milestone target.
                    </div>
                  </div>

                  {/* Why it Matters & Recommended Action */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1">
                      <div className="text-white/60 font-mono uppercase text-[10px]">Why It Matters</div>
                      <p className="text-white/85 leading-relaxed">
                        Risk indicator increased to <strong>{cat.label}</strong> due to slippage in major construction milestones. Continued delay puts scheduled delivery at risk.
                      </p>
                    </div>

                    <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1">
                      <div className="text-white/60 font-mono uppercase text-[10px]">Recommended Action</div>
                      <p className="text-white/85 leading-relaxed">
                        Review the contractor schedule and delayed milestone with the executing agency. Align upcoming financial releases with verified work.
                      </p>
                    </div>
                  </div>

                  {/* Actions Row */}
                  <div className="pt-2 border-t border-white/10 flex flex-wrap items-center justify-between gap-3">
                    <div className="text-xs font-mono text-white/60">
                      Status: <strong className={isAcknowledged ? 'text-emerald-400' : 'text-amber-400'}>{a.status}</strong>
                    </div>

                    <div className="flex items-center gap-2">
                      {!isAcknowledged && (
                        <button
                          onClick={() => handleAcknowledge(a.alert_id)}
                          className="px-3.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-mono font-bold border border-white/20 transition-all cursor-pointer"
                        >
                          ✓ Acknowledge
                        </button>
                      )}

                      {onNavigateToProject && (
                        <button
                          onClick={() => onNavigateToProject(a.project_id)}
                          className="px-4 py-1.5 rounded-lg bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer"
                        >
                          View Project →
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  /* =========================================================================
     ADMIN VIEW — "Alerts & Automation Command Center"
     Full control: threshold sliders, email config, test triggers, n8n webhook monitoring.
     ========================================================================= */
  return (
    <div className="space-y-4 sm:space-y-6 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Header */}
      <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white">
              Alerts &amp; Automation Command Center
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
              ADMIN
            </span>
          </div>
          <p className="text-xs sm:text-base text-white/70">
            {pendingCount} Pending Alerts · n8n Automation Workflows &amp; Multi-Channel Early-Warning System
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={loadAlerts}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-white text-black text-xs sm:text-sm font-mono-code font-bold hover:bg-zinc-200 cursor-pointer transition-all shadow-md"
          >
            ↻ Refresh Alerts
          </button>
        </div>
      </GlassCard>

      {/* Admin Executive Threshold & n8n Cloud Workflow Protocol */}
      <GlassCard variant="medium" padding={24} className="space-y-4 border border-white/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div>
            <h3 className="text-base sm:text-lg font-bold font-display text-white flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              Automated Alert Dispatch &amp; Threshold Calibration
            </h3>
            <p className="text-xs text-white/70 mt-0.5">
              Configure risk criteria, notification recipient address, and test webhook pipelines.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <span className="text-[11px] font-mono-code text-white/60">n8n Workflow Engine:</span>
            <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 text-xs font-mono-code font-bold border border-emerald-500/30">
              Active · Connected
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
          {/* Threshold Config */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-mono-code">
              <span className="text-white/80 uppercase">Risk Alert Threshold</span>
              <span className="font-bold text-white px-2 py-0.5 rounded bg-white/10">{userThreshold}</span>
            </div>
            <input
              type="range"
              min="50"
              max="95"
              step="1"
              value={userThreshold}
              onChange={e => setUserThreshold(parseFloat(e.target.value))}
              className="w-full accent-white cursor-pointer"
            />
            <p className="text-[11px] text-white/50">Triggers alert when project risk exceeds this score</p>
          </div>

          {/* Recipient Email Config */}
          <div className="space-y-1.5">
            <label className="text-xs font-mono-code text-white/80 uppercase">Recipient Email</label>
            <input
              type="email"
              value={recipientEmail}
              onChange={e => setRecipientEmail(e.target.value)}
              className="w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm font-mono-code text-white focus:outline-none focus:border-white"
              placeholder="user@infrabuild.gov.in"
            />
            <p className="text-[11px] text-white/50">Where notification alerts are delivered</p>
          </div>

          {/* Test Risk Score Simulator */}
          <div className="space-y-1.5">
            <label className="text-xs font-mono-code text-white/80 uppercase">Test Risk Score</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0"
                max="100"
                step="0.5"
                value={simulatedDphis}
                onChange={e => setSimulatedDphis(parseFloat(e.target.value) || 0)}
                className="w-24 bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm font-mono-code text-white focus:outline-none focus:border-white"
              />
              <button
                onClick={handleTriggerSimulation}
                disabled={isTriggering}
                className="flex-1 px-4 py-2 rounded-lg bg-white text-black hover:bg-slate-200 text-xs font-mono-code font-bold cursor-pointer transition-all shadow-md disabled:opacity-40"
              >
                {isTriggering ? 'Triggering...' : 'Test Alert Email ⚡'}
              </button>
            </div>
            <p className="text-[11px] text-white/50">Simulates real-time project risk breach</p>
          </div>
        </div>

        {/* Simulation Feedback Alert Box */}
        {simulationResult && (
          <div className={`p-3.5 rounded-xl border text-xs font-mono-code transition-all ${
            simulationResult.threshold_exceeded
              ? 'bg-red-500/15 border-red-500/30 text-red-200'
              : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-200'
          }`}>
            <div className="font-bold mb-1">
              {simulationResult.threshold_exceeded
                ? `🚨 Alert Triggered: Risk ${simulatedDphis} exceeded threshold ${userThreshold}!`
                : `✓ Under Threshold: Risk ${simulatedDphis} did not trigger alert (threshold is ${userThreshold}).`}
            </div>
            <div className="opacity-80 text-[11px]">
              {simulationResult.message}
            </div>
          </div>
        )}
      </GlassCard>

      {/* Stream of Live Alerts */}
      <div className="space-y-3">
        <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white/70">
          Portfolio Alert Stream ({alerts.length})
        </h3>

        {alerts.length === 0 ? (
          <GlassCard variant="medium" padding={32} className="text-center space-y-3">
            <div className="text-base font-bold text-white">No Alerts Found</div>
            <p className="text-xs sm:text-sm text-white/70">
              No alert items logged in the database.
            </p>
          </GlassCard>
        ) : (
          alerts.map(a => {
            const cat = getRiskCategory(a.dphis);
            const isAck = a.status === 'ACKNOWLEDGED';

            return (
              <div
                key={a.alert_id}
                className={`oled-solid-card p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all ${
                  isAck ? 'opacity-60 border-white/10' : 'border-white/20 hover:border-white/35'
                }`}
              >
                <div className="space-y-1.5 max-w-2xl">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${cat.badgeBg}`}>
                      {cat.label}
                    </span>
                    <span className="font-mono-code font-bold text-xs text-white px-2 py-0.5 rounded bg-white/10">
                      {a.project_id}
                    </span>
                    <span className="text-[11px] font-mono text-white/50">
                      {a.created_at ? new Date(a.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Recent'}
                    </span>
                  </div>

                  <h4 className="font-bold text-sm sm:text-base text-white">
                    {a.project_name || `Corridor ${a.project_id}`}
                  </h4>

                  <p className="text-xs text-white/80 leading-relaxed">
                    {a.explanation || a.trigger_reason || 'Risk threshold exceeded. Milestone and physical progress divergence detected.'}
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {!isAck && (
                    <button
                      onClick={() => handleAcknowledge(a.alert_id)}
                      className="px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-mono font-bold border border-white/20 transition-all cursor-pointer"
                    >
                      Acknowledge
                    </button>
                  )}

                  {onNavigateToInvestigation && (
                    <button
                      onClick={() => onNavigateToInvestigation(a.project_id)}
                      className="px-3.5 py-1.5 rounded-lg bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer"
                    >
                      Investigate →
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
