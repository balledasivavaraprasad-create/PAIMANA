import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import RiskBadge from '../components/RiskBadge';
import { fetchAlerts, acknowledgeAlert, AlertItem } from '../lib/api';

interface Props {
  onNavigateToInvestigation?: (projectId: string) => void;
}

export default function Alerts({ onNavigateToInvestigation }: Props) {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

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
