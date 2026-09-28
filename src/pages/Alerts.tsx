import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import { fetchAlerts, acknowledgeAlert, UserProfile, AlertItem } from '../lib/api';
import { getRiskCategory } from '../lib/risk';
import { CurvedGrowthArrow } from '../components/CurvedTrendArrow';

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

  // Admin test trigger state
  const [simulatedProjectId, setSimulatedProjectId] = useState<string>('P1024');
  const [simulatedDphis, setSimulatedDphis] = useState<number>(74.0);
  const [simulatedThreshold, setSimulatedThreshold] = useState<number>(70.0);
  const [isTriggering, setIsTriggering] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<any | null>(null);

  const loadAlerts = () => {
    setLoading(true);
    // Normal user: fetch their project alerts; Admin: fetch system alerts
    fetchAlerts(isAdmin ? undefined : currentUser?.username)
      .then(items => {
        setAlerts(items);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    loadAlerts();
  }, [currentUser, isAdmin]);

  const handleAcknowledge = async (alertId: string) => {
    const ok = await acknowledgeAlert(alertId);
    if (ok) {
      setAlerts(prev => prev.map(a => a.alert_id === alertId ? { ...a, status: 'ACKNOWLEDGED' } : a));
    }
  };

  const handleTriggerTest = async () => {
    setIsTriggering(true);
    setSimulationResult(null);
    try {
      const res = await fetch(`http://localhost:8001/api/v1/project-risk-events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: simulatedProjectId,
          current_dphis: simulatedDphis,
          threshold: simulatedThreshold
        })
      });
      const data = await res.json();
      setSimulationResult(data);
      if (data.triggered) {
        setTimeout(loadAlerts, 1000);
      }
    } catch (err: any) {
      setSimulationResult({
        success: false,
        triggered: false,
        message: err.message || 'Trigger event failed'
      });
    } finally {
      setIsTriggering(false);
    }
  };

  const pendingCount = alerts.filter(a => a.status === 'PENDING').length;

  /* =========================================================================
     NORMAL USER VIEW — "My Project Alerts"
     Focused, non-technical, outcome-oriented
     ========================================================================= */
  if (!isAdmin) {
    return (
      <div className="space-y-6 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto animate-fade-in">
        {/* Header */}
        <div className="p-6 rounded-2xl border bg-[#0B0F17]/90 border-white/15 text-white shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="text-[11px] font-mono uppercase tracking-wider text-amber-400 font-bold">
              Project Early-Warning System
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold font-display text-white">
              My Project Alerts
            </h1>
            <p className="text-xs sm:text-sm text-white/70 max-w-2xl leading-relaxed">
              When a project's risk score reaches or crosses its configured alert threshold, an automated alert is generated here and sent to your email.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <span className="px-3 py-1.5 rounded-xl bg-white/10 text-white font-mono text-xs font-bold border border-white/15">
              {pendingCount} Pending Review
            </span>
            <button
              onClick={loadAlerts}
              className="px-4 py-2 rounded-xl bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer shadow-md"
            >
              ↻ Refresh
            </button>
          </div>
        </div>

        {/* Alerts List */}
        {loading ? (
          <div className="p-12 text-center text-xs font-mono text-white/60">
            Loading your project alerts...
          </div>
        ) : alerts.length === 0 ? (
          <div className="oled-solid-card p-12 text-center space-y-3">
            <div className="text-base font-bold text-white">All Clear · No Project Alerts</div>
            <p className="text-xs sm:text-sm text-white/70 max-w-md mx-auto">
              None of your assigned infrastructure projects have breached their configured alert thresholds.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {alerts.map(a => {
              const score = a.current_dphis ?? a.dphis ?? 72.0;
              const thresh = a.threshold ?? 70.0;
              const cat = getRiskCategory(score);
              const isAcknowledged = a.status === 'ACKNOWLEDGED';
              const whyReason = (a.top_risk_reasons && a.top_risk_reasons.length > 0)
                ? a.top_risk_reasons[0]
                : "Progress is behind plan and schedule risk has increased.";

              return (
                <div
                  key={a.alert_id}
                  className={`oled-solid-card p-5 sm:p-6 space-y-4 transition-all ${
                    isAcknowledged ? 'opacity-65 border-white/10' : 'border-white/20 hover:border-white/40'
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

                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="text-white/60">Status:</span>
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        isAcknowledged ? 'bg-white/10 text-white/70' : 'bg-red-500/20 text-red-400 border border-red-500/30'
                      }`}>
                        {isAcknowledged ? 'ACKNOWLEDGED' : 'THRESHOLD CROSSED 🔔'}
                      </span>
                    </div>
                  </div>

                  {/* Project Info & Threshold Comparison */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-start">
                    <div className="md:col-span-2 space-y-1">
                      <div className="text-[11px] font-mono text-white/60 uppercase">Project</div>
                      <h3 className="text-base sm:text-lg font-bold text-white">
                        {a.project_name || `Project ${a.project_id}`}
                      </h3>
                      <div className="text-xs text-white/80 pt-1 leading-relaxed">
                        <strong className="text-white">Why:</strong> {whyReason}
                      </div>
                    </div>

                    <div className="p-3 rounded-xl bg-black/40 border border-white/10 space-y-1 font-mono text-xs">
                      <div className="text-[10px] text-white/60 uppercase">Current DPHIS</div>
                      <div className="text-lg font-bold text-white">{score} / 100</div>
                      <div className="text-[10px] text-amber-400">Risk Severity: {cat.label}</div>
                    </div>

                    <div className="p-3 rounded-xl bg-black/40 border border-white/10 space-y-1 font-mono text-xs">
                      <div className="text-[10px] text-white/60 uppercase">Project Threshold</div>
                      <div className="text-lg font-bold text-amber-300">{thresh} / 100</div>
                      <div className="text-[10px] text-red-400 font-semibold flex items-center gap-1">
                        <CurvedGrowthArrow className="w-3 h-3 text-red-400" />
                        <span>Crossed by +{Math.max(0, (score - thresh)).toFixed(1)} pts</span>
                      </div>
                    </div>
                  </div>

                  {/* Recommended Action Box */}
                  <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-1 text-xs">
                    <span className="font-mono font-bold text-white uppercase text-[10px]">Recommended Action</span>
                    <p className="text-white/85 leading-relaxed">
                      Review delayed milestones and contractor resource muster with the executing department. Verify ongoing disbursements against physical measurement books.
                    </p>
                  </div>

                  {/* Footer Buttons */}
                  <div className="pt-2 border-t border-white/10 flex flex-wrap items-center justify-between gap-3">
                    <div className="text-[11px] font-mono text-white/50">
                      Dispatched: {a.created_at ? new Date(a.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Recent'}
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

                      {onNavigateToInvestigation && (
                        <button
                          onClick={() => onNavigateToInvestigation(a.project_id)}
                          className="px-3.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-mono font-bold border border-white/20 transition-all cursor-pointer"
                        >
                          Investigate ⚡
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
     Full telemetry, n8n webhook status, notification logs, test triggers
     ========================================================================= */
  return (
    <div className="space-y-6 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="p-6 rounded-2xl border bg-[#0B0F17]/90 border-white/15 text-white shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <h1 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white">
              Alerts &amp; Automation Command Center
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
              ADMIN
            </span>
          </div>
          <p className="text-xs sm:text-sm text-white/70 max-w-2xl leading-relaxed">
            Multi-ministry risk threshold evaluation, automated n8n webhook pipelines, email dispatch telemetry, and crossing event audit logs.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={loadAlerts}
            className="px-4 py-2 rounded-xl bg-white text-black text-xs font-mono font-bold hover:bg-slate-200 cursor-pointer transition-all shadow-md"
          >
            ↻ Refresh All
          </button>
        </div>
      </div>

      {/* n8n Webhook & Event Trigger Panel */}
      <div className="oled-solid-card p-5 sm:p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div>
            <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
              Automated n8n Webhook Pipeline
            </h3>
            <p className="text-xs text-white/60 mt-0.5 font-mono">
              Target: <code className="text-amber-300">https://hrishikesh1.app.n8n.cloud/webhook/project-risk-threshold</code>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-300 text-xs font-mono font-bold border border-emerald-500/30">
              Active · Connected
            </span>
          </div>
        </div>

        {/* Test Event Simulator */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end pt-1">
          <div>
            <label className="block text-[11px] font-mono uppercase text-white/70 mb-1">Project ID</label>
            <input
              type="text"
              value={simulatedProjectId}
              onChange={e => setSimulatedProjectId(e.target.value)}
              className="w-full px-3 py-1.5 rounded-lg bg-black/50 border border-white/20 text-white font-mono text-xs outline-none"
            />
          </div>

          <div>
            <label className="block text-[11px] font-mono uppercase text-white/70 mb-1">DPHIS Score</label>
            <input
              type="number"
              min="1"
              max="100"
              step="0.5"
              value={simulatedDphis}
              onChange={e => setSimulatedDphis(Number(e.target.value))}
              className="w-full px-3 py-1.5 rounded-lg bg-black/50 border border-white/20 text-white font-mono text-xs outline-none"
            />
          </div>

          <div>
            <label className="block text-[11px] font-mono uppercase text-white/70 mb-1">Project Threshold</label>
            <input
              type="number"
              min="1"
              max="100"
              value={simulatedThreshold}
              onChange={e => setSimulatedThreshold(Number(e.target.value))}
              className="w-full px-3 py-1.5 rounded-lg bg-black/50 border border-white/20 text-white font-mono text-xs outline-none"
            />
          </div>

          <div>
            <button
              onClick={handleTriggerTest}
              disabled={isTriggering}
              className="w-full py-2 px-3 rounded-lg bg-amber-400 hover:bg-amber-300 text-black text-xs font-mono font-bold transition-all cursor-pointer shadow-md disabled:opacity-50"
            >
              {isTriggering ? 'Evaluating...' : 'Simulate Crossing Event ⚡'}
            </button>
          </div>
        </div>

        {/* Simulation Feedback */}
        {simulationResult && (
          <div className={`p-3 rounded-xl border text-xs font-mono ${
            simulationResult.triggered
              ? 'bg-red-500/15 border-red-500/30 text-red-200'
              : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-200'
          }`}>
            <div className="font-bold">
              {simulationResult.triggered
                ? `🚨 THRESHOLD CROSSED: Alert ${simulationResult.alert_id} generated & dispatched to n8n!`
                : `✓ NO ALERT: ${simulationResult.message}`}
            </div>
            {simulationResult.notification_status && (
              <div className="text-[11px] opacity-80 mt-1">
                Notification Status: <strong>{simulationResult.notification_status}</strong> (Ref: {simulationResult.n8n_execution_reference || 'N/A'})
              </div>
            )}
          </div>
        )}
      </div>

      {/* Admin Alert Stream Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white/70">
            System Alert Events ({alerts.length})
          </h3>
          <span className="text-xs font-mono text-white/50">Stored in MongoDB · Persisted before webhook</span>
        </div>

        {alerts.length === 0 ? (
          <div className="oled-solid-card p-12 text-center text-xs font-mono text-white/60">
            No alert events recorded in database.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-white/15 bg-black/40">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-white/15 bg-[#0B0F17] font-mono text-[10px] text-white/70 uppercase">
                  <th className="p-3.5">Alert ID</th>
                  <th className="p-3.5">Project</th>
                  <th className="p-3.5">DPHIS / Threshold</th>
                  <th className="p-3.5">Severity</th>
                  <th className="p-3.5">Notification</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Timestamp</th>
                  <th className="p-3.5">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono text-xs">
                {alerts.map(a => {
                  const score = a.current_dphis ?? a.dphis ?? 70.0;
                  const thresh = a.threshold ?? 70.0;
                  const cat = getRiskCategory(score);
                  const isAck = a.status === 'ACKNOWLEDGED';

                  return (
                    <tr key={a.alert_id} className="hover:bg-white/5 transition-colors">
                      <td className="p-3.5 font-bold text-white">{a.alert_id}</td>
                      <td className="p-3.5 font-sans">
                        <div className="font-semibold text-white">{a.project_name || a.project_id}</div>
                        <div className="text-[11px] text-white/50 font-mono">{a.project_id}</div>
                      </td>
                      <td className="p-3.5">
                        <span className="font-bold text-white">{score}</span>
                        <span className="text-white/40"> / {thresh}</span>
                      </td>
                      <td className="p-3.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${cat.badgeBg}`}>
                          {cat.label}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          a.notification_status === 'sent'
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : a.notification_status === 'failed'
                            ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        }`}>
                          {a.notification_status || 'sent'}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span className={isAck ? 'text-white/50' : 'text-amber-400 font-bold'}>
                          {a.status}
                        </span>
                      </td>
                      <td className="p-3.5 text-white/50 text-[11px]">
                        {a.created_at ? new Date(a.created_at).toLocaleDateString() : 'Recent'}
                      </td>
                      <td className="p-3.5">
                        <div className="flex items-center gap-1.5">
                          {!isAck && (
                            <button
                              onClick={() => handleAcknowledge(a.alert_id)}
                              className="px-2 py-1 rounded bg-white/10 hover:bg-white/20 text-white text-[11px] font-bold transition-all cursor-pointer"
                            >
                              ✓ Ack
                            </button>
                          )}
                          {onNavigateToProject && (
                            <button
                              onClick={() => onNavigateToProject(a.project_id)}
                              className="px-2 py-1 rounded bg-white text-black hover:bg-slate-200 text-[11px] font-bold transition-all cursor-pointer"
                            >
                              View →
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
