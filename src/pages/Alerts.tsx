import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import RiskBadge from '../components/RiskBadge';
import { fetchAlerts, acknowledgeAlert, triggerN8nRiskEvent, AlertItem, UserProfile } from '../lib/api';

interface Props {
  onNavigateToInvestigation?: (projectId: string) => void;
  currentUser?: UserProfile | null;
  pinsCount?: number;
  onOpenAddProject?: () => void;
}

export default function Alerts({ onNavigateToInvestigation, currentUser, pinsCount, onOpenAddProject }: Props) {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  // User-configurable alert threshold and n8n credentials
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

  if (pinsCount === 0) {
    return (
      <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        <GlassCard variant="hero" padding={32} className="space-y-6 text-center sm:text-left">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 pb-6 border-b border-white/10">
            <div className="space-y-2 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-400/30">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                <span>Zero Monitored Assets</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold font-display text-white">
                Early-Warning Surveillance Awaiting Projects
              </h2>
              <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
                Automated threshold breach detection, multi-factor risk escalation alerts, and automated n8n webhook notifications monitor active infrastructure corridors. Ingest an asset to initialize active monitoring.
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
      // If alert was created, refresh alerts stream
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

  return (
    <div className="space-y-4 sm:space-y-6 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Header - Clean heading without top eyebrow tag */}
      <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white">
            Algorithmic Early Warning Telemetry & Risk Surveillance
          </h2>
          <p className="text-xs sm:text-base text-white/70">
            {alerts.filter(a => a.status === 'PENDING').length} Unacknowledged Critical Anomalies · State-Transition Deduplication Protocol & Event-Driven Outbound Webhook Architecture
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={loadAlerts}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-white text-black text-xs sm:text-sm font-mono-code font-bold hover:bg-zinc-200 cursor-pointer transition-all shadow-md"
          >
            ↻ Re-Synchronize Incident Stream
          </button>
        </div>
      </GlassCard>

      {/* Executive Threshold & n8n Cloud Workflow Protocol */}
      <GlassCard variant="medium" padding={24} className="space-y-4 border border-white/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div>
            <h3 className="text-base sm:text-lg font-bold font-display text-white flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              Automated Institutional Alert & n8n Cloud Workflow Protocol
            </h3>
            <p className="text-xs sm:text-sm text-white/70">
              Surveillance engine continuously evaluates asset DPHIS against user-configured threshold (default: &gt; 75.0). Exceeding this boundary triggers automated email dispatch to user credentials via n8n Cloud.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 font-mono-code text-xs text-white/80 shrink-0">
            <span className="px-2.5 py-1 bg-white/10 rounded-lg border border-white/20">Webhook: Live</span>
            <span className="px-2.5 py-1 bg-white/10 rounded-lg border border-white/20">Recipient: balledasivavaraprasad@gmail.com</span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-mono-code text-white/80 uppercase">DPHIS Alert Threshold</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="40"
                max="95"
                step="1"
                value={userThreshold}
                onChange={e => setUserThreshold(Number(e.target.value))}
                className="w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm font-mono-code text-white focus:outline-none focus:border-white"
              />
              <span className="text-xs font-mono-code text-white/60 shrink-0">/ 100</span>
            </div>
            <p className="text-[11px] text-white/50">Default: 75.0 (Critical Tier)</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-mono-code text-white/80 uppercase">Target Recipient Email</label>
            <input
              type="email"
              value={recipientEmail}
              onChange={e => setRecipientEmail(e.target.value)}
              className="w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm font-mono-code text-white focus:outline-none focus:border-white"
              placeholder="user@paimana.gov.in"
            />
            <p className="text-[11px] text-white/50">User credential destination</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-mono-code text-white/80 uppercase">Simulated Asset DPHIS</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={simulatedDphis}
                onChange={e => setSimulatedDphis(Number(e.target.value))}
                className="w-full bg-black/40 border border-white/20 rounded-lg px-3 py-2 text-sm font-mono-code text-white focus:outline-none focus:border-white"
              />
              <span className="text-xs font-mono-code text-white/60 shrink-0">/ 100</span>
            </div>
            <p className="text-[11px] text-white/50">Test value to evaluate rule</p>
          </div>

          <div className="flex flex-col justify-end space-y-1.5">
            <button
              onClick={handleTriggerSimulation}
              disabled={isTriggering}
              className="w-full px-4 py-2.5 rounded-lg bg-white text-black font-mono-code font-bold text-xs sm:text-sm hover:bg-zinc-200 transition-all cursor-pointer disabled:opacity-50 shadow-md"
            >
              {isTriggering ? "Evaluating..." : "⚡ Execute Risk Evaluation"}
            </button>
            <p className="text-[11px] text-white/50 text-center">FastAPI → n8n Cloud Webhook</p>
          </div>
        </div>

        {simulationResult && (
          <div className={`p-3.5 rounded-lg border text-xs sm:text-sm font-mono-code flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${
            simulationResult.threshold_exceeded
              ? "bg-emerald-950/50 border-emerald-500/50 text-emerald-200"
              : "bg-amber-950/50 border-amber-500/50 text-amber-200"
          }`}>
            <div>
              <span className="font-bold">
                {simulationResult.threshold_exceeded ? "✓ ESCALATION TRIGGERED:" : "ℹ ALERT SUPPRESSED:"}
              </span>{" "}
              {simulationResult.message || (simulationResult.threshold_exceeded ? `DPHIS score ${simulatedDphis} exceeds threshold ${userThreshold}. Dispatched to n8n Cloud; notification email queued for ${simulationResult.recipient_email}.` : `DPHIS score ${simulatedDphis} is below threshold ${userThreshold}. Standard surveillance maintained.`)}
            </div>
            {simulationResult.status_code && (
              <span className="px-2.5 py-1 rounded bg-black/40 border border-white/20 text-xs shrink-0">
                HTTP {simulationResult.status_code} OK
              </span>
            )}
          </div>
        )}
      </GlassCard>

      {/* Alerts Stream */}
      <div className="space-y-4">
        {alerts.length > 0 ? (
          alerts.map(a => (
            <GlassCard key={a.alert_id} variant="medium" padding={20} className="space-y-3 sm:space-y-4 border-l-4 border-l-white">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                  <RiskBadge level={a.severity as any} />
                  <span className="font-mono-code font-bold text-sm sm:text-base text-white">{a.project_id}</span>
                  <h4 className="text-base sm:text-lg font-semibold font-display text-white">{a.project_name}</h4>
                </div>

                <div className="flex items-center gap-3 text-xs sm:text-sm font-mono-code text-white/80 shrink-0">
                  <span className="text-white font-bold">Composite DPHIS: {a.dphis}</span>
                  <span>•</span>
                  <span>{new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
              </div>

              <p className="text-sm sm:text-base text-white/90 leading-relaxed">{a.message}</p>

              <div className="pt-3 border-t border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs sm:text-sm">
                <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                  <span className="text-xs sm:text-sm font-mono-code uppercase px-2.5 py-1 rounded bg-white/10 border border-white/20 text-white">
                    Diagnostic Criterion: {a.trigger}
                  </span>
                  <span className="text-xs sm:text-sm font-mono-code font-bold text-white">
                    Protocol Lifecycle: {a.status}
                  </span>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {onNavigateToInvestigation && (
                    <button
                      onClick={() => onNavigateToInvestigation(a.project_id)}
                      className="text-xs sm:text-sm font-mono-code text-white underline hover:text-white/80 cursor-pointer font-semibold"
                    >
                      Initiate Forensic Causal Audit →
                    </button>
                  )}
                  {a.status !== 'ACKNOWLEDGED' && (
                    <button
                      onClick={() => handleAcknowledge(a.alert_id)}
                      className="px-3 sm:px-4 py-1.5 rounded-lg bg-white text-black hover:bg-zinc-200 border border-white text-xs sm:text-sm font-mono-code font-bold cursor-pointer transition-all"
                    >
                      Ratify & Confirm Receipt
                    </button>
                  )}
                </div>
              </div>
            </GlassCard>
          ))
        ) : (
          <GlassCard variant="medium" padding={32} className="text-center space-y-3">
            <div className="text-3xl text-white">✓</div>
            <div className="text-base sm:text-lg font-bold text-white">No Active Anomalous Incident Triggers</div>
            <p className="text-xs sm:text-base text-white/70">
              Sovereign asset cohort operating within calibrated confidence bands. Real-time telemetry evaluates multi-temporal divergence continuously.
            </p>
          </GlassCard>
        )}
      </div>
    </div>
  );
}
