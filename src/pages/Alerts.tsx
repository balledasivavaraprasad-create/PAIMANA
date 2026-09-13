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
    <div className="space-y-6 pt-20 pb-12 px-6 md:px-16 max-w-7xl mx-auto">
      {/* Header */}
      <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--accent)] font-mono-code">
              Automated Alert Engine
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-red-500/10 text-red-400 font-semibold border border-red-500/20">
              {alerts.filter(a => a.status === 'PENDING').length} Active Alerts
            </span>
          </div>
          <h2 className="text-2xl font-bold font-display text-[var(--text-primary)]">
            Risk Alerts & Automated Early Warnings
          </h2>
          <p className="text-xs text-[var(--text-muted)]">
            State-transition deduplication & n8n webhook notification bus
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadAlerts}
            className="px-4 py-2 rounded-xl bg-black text-white text-xs font-mono-code font-bold border border-white/20 hover:bg-zinc-900 cursor-pointer"
          >
            ↻ Refresh Stream
          </button>
        </div>
      </GlassCard>

      {/* Alerts Stream */}
      <div className="space-y-4">
        {alerts.length > 0 ? (
          alerts.map(a => (
            <GlassCard key={a.alert_id} variant="medium" padding={20} className="space-y-3 border-l-4 border-l-red-500">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-3">
                  <RiskBadge level={a.severity as any} showGlow />
                  <span className="font-mono-code font-bold text-xs text-[var(--accent)]">{a.project_id}</span>
                  <h4 className="text-sm font-semibold font-display text-[var(--text-primary)]">{a.project_name}</h4>
                </div>

                <div className="flex items-center gap-2 text-xs font-mono-code text-[var(--text-muted)]">
                  <span className="text-red-500 font-bold">DPHIS {a.dphis}</span>
                  <span>•</span>
                  <span>{new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
              </div>

              <p className="text-xs text-[var(--text-secondary)]">{a.message}</p>

              <div className="pt-2 border-t border-[var(--border-hairline)] flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono-code uppercase px-2 py-0.5 rounded bg-[var(--surface-sunken)] border border-[var(--border-hairline)] text-[var(--text-muted)]">
                    Trigger: {a.trigger}
                  </span>
                  <span className={`text-[10px] font-mono-code font-bold ${a.status === 'ACKNOWLEDGED' ? 'text-emerald-500' : 'text-amber-400'}`}>
                    Status: {a.status}
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  {onNavigateToInvestigation && (
                    <button
                      onClick={() => onNavigateToInvestigation(a.project_id)}
                      className="text-xs font-mono-code text-[var(--accent)] hover:underline cursor-pointer"
                    >
                      Investigate Project →
                    </button>
                  )}
                  {a.status !== 'ACKNOWLEDGED' && (
                    <button
                      onClick={() => handleAcknowledge(a.alert_id)}
                      className="px-3 py-1 rounded-lg bg-[var(--surface-sunken)] hover:bg-[var(--surface-card)] border border-[var(--border-hairline)] text-[11px] font-mono-code text-[var(--text-primary)] cursor-pointer"
                    >
                      Acknowledge
                    </button>
                  )}
                </div>
              </div>
            </GlassCard>
          ))
        ) : (
          <GlassCard variant="medium" padding={32} className="text-center space-y-2">
            <div className="text-2xl">✓</div>
            <div className="text-sm font-bold text-[var(--text-primary)]">No Active Alerts Escalated</div>
            <p className="text-xs text-[var(--text-muted)]">
              All 1,500 projects are operating within standard threshold limits. Alerts will automatically fire upon critical transition.
            </p>
          </GlassCard>
        )}
      </div>
    </div>
  );
}
