import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import { useTheme } from '../hooks/useTheme';
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
  const { theme } = useTheme();
  const isDark = theme === 'dark';
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
      <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto animate-fade-in">
        {/* Header Flashcard */}
        <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="text-[11px] font-mono uppercase tracking-wider text-amber-500 font-bold">
              Project Early-Warning System
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className={`text-xl sm:text-2xl md:text-3xl font-bold font-display ${isDark ? 'text-white' : 'text-slate-900'}`}>
                My Project Alerts
              </h1>
              <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${
                isDark 
                  ? 'bg-white/10 text-white/90 border-white/20' 
                  : 'bg-slate-200 text-slate-800 border-slate-300'
              }`}>
                {pendingCount} Pending Review
              </span>
            </div>
            <p className={`text-xs sm:text-sm md:text-base leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-600'}`}>
              When a project's risk score reaches or crosses its configured alert threshold, an automated alert is generated here and sent to your email.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              type="button"
              onClick={loadAlerts}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all cursor-pointer shadow-md flex items-center gap-1.5 ${
                isDark
                  ? 'bg-white text-black hover:bg-slate-200'
                  : 'bg-slate-900 text-white hover:bg-black'
              }`}
            >
              <span>↻</span>
              <span>Refresh</span>
            </button>
          </div>
        </GlassCard>

        {/* Alerts List */}
        {loading ? (
          <div className={`p-12 text-center text-xs font-mono ${isDark ? 'text-white/60' : 'text-slate-500'}`}>
            Loading your project alerts...
          </div>
        ) : alerts.length === 0 ? (
          <div className="oled-solid-card p-12 text-center space-y-3">
            <div className={`text-base font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>All Clear · No Project Alerts</div>
            <p className={`text-xs sm:text-sm max-w-md mx-auto ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
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
                  <div className={`flex flex-wrap items-center justify-between gap-2 border-b pb-3 ${
                    isDark ? 'border-white/10' : 'border-slate-200'
                  }`}>
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${cat.badgeBg}`}>
                        {cat.label} ALERT
                      </span>
                      <span className={`font-mono-code font-bold text-xs px-2 py-0.5 rounded ${
                        isDark ? 'text-white bg-white/10' : 'text-slate-900 bg-slate-200'
                      }`}>
                        {a.project_id}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className={isDark ? 'text-white/60' : 'text-slate-600'}>Status:</span>
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        isAcknowledged 
                          ? (isDark ? 'bg-white/10 text-white/70' : 'bg-slate-200 text-slate-700')
                          : 'bg-red-500/20 text-red-500 border border-red-500/30'
                      }`}>
                        {isAcknowledged ? 'ACKNOWLEDGED' : 'THRESHOLD CROSSED 🔔'}
                      </span>
                    </div>
                  </div>

                  {/* Project Info & Threshold Comparison */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-start">
                    <div className="md:col-span-2 space-y-1">
                      <div className={`text-[11px] font-mono uppercase ${isDark ? 'text-white/60' : 'text-slate-500'}`}>Project</div>
                      <h3 className={`text-base sm:text-lg font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        {a.project_name || `Project ${a.project_id}`}
                      </h3>
                      <div className={`text-xs pt-1 leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-700'}`}>
                        <strong className={isDark ? 'text-white' : 'text-slate-900'}>Why:</strong> {whyReason}
                      </div>
                    </div>

                    <div className={`p-3 rounded-xl border space-y-1 font-mono text-xs ${
                      isDark ? 'bg-black/40 border-white/10' : 'bg-slate-100 border-slate-200'
                    }`}>
                      <div className={`text-[10px] uppercase ${isDark ? 'text-white/60' : 'text-slate-500'}`}>Current DPHIS</div>
                      <div className={`text-lg font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{score} / 100</div>
                      <div className="text-[10px] text-amber-500 font-semibold">Risk Severity: {cat.label}</div>
                    </div>

                    <div className={`p-3 rounded-xl border space-y-1 font-mono text-xs ${
                      isDark ? 'bg-black/40 border-white/10' : 'bg-slate-100 border-slate-200'
                    }`}>
                      <div className={`text-[10px] uppercase ${isDark ? 'text-white/60' : 'text-slate-500'}`}>Project Threshold</div>
                      <div className="text-lg font-bold text-amber-500">{thresh} / 100</div>
                      <div className="text-[10px] text-red-500 font-semibold flex items-center gap-1">
                        <CurvedGrowthArrow className="w-3 h-3 text-red-500" />
                        <span>Crossed by +{Math.max(0, (score - thresh)).toFixed(1)} pts</span>
                      </div>
                    </div>
                  </div>

                  {/* Recommended Action Box */}
                  <div className={`p-3 rounded-xl border space-y-1 text-xs ${
                    isDark ? 'bg-white/5 border-white/10 text-white/85' : 'bg-slate-50 border-slate-200 text-slate-700'
                  }`}>
                    <span className={`font-mono font-bold uppercase text-[10px] ${isDark ? 'text-white' : 'text-slate-900'}`}>Recommended Action</span>
                    <p className="leading-relaxed">
                      Review delayed milestones and contractor resource muster with the executing department. Verify ongoing disbursements against physical measurement books.
                    </p>
                  </div>

                  {/* Footer Buttons */}
                  <div className={`pt-2 border-t flex flex-wrap items-center justify-between gap-3 ${
                    isDark ? 'border-white/10' : 'border-slate-200'
                  }`}>
                    <div className={`text-[11px] font-mono ${isDark ? 'text-white/50' : 'text-slate-500'}`}>
                      Dispatched: {a.created_at ? new Date(a.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Recent'}
                    </div>

                    <div className="flex items-center gap-2">
                      {!isAcknowledged && (
                        <button
                          type="button"
                          onClick={() => handleAcknowledge(a.alert_id)}
                          className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold border transition-all cursor-pointer ${
                            isDark 
                              ? 'bg-white/10 hover:bg-white/20 text-white border-white/20' 
                              : 'bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-300'
                          }`}
                        >
                          ✓ Acknowledge
                        </button>
                      )}

                      {onNavigateToInvestigation && (
                        <button
                          type="button"
                          onClick={() => onNavigateToInvestigation(a.project_id)}
                          className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold border transition-all cursor-pointer ${
                            isDark 
                              ? 'bg-white/10 hover:bg-white/20 text-white border-white/20' 
                              : 'bg-amber-100 hover:bg-amber-200 text-amber-900 border-amber-300'
                          }`}
                        >
                          Investigate ⚡
                        </button>
                      )}

                      {onNavigateToProject && (
                        <button
                          type="button"
                          onClick={() => onNavigateToProject(a.project_id)}
                          className={`px-4 py-1.5 rounded-lg text-xs font-mono font-bold transition-all cursor-pointer shadow-sm ${
                            isDark 
                              ? 'bg-white text-black hover:bg-slate-200' 
                              : 'bg-slate-900 text-white hover:bg-black'
                          }`}
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
    <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto animate-fade-in">
      {/* Header — Alerts & Automation Command Center Flashcard */}
      <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className={`text-xl sm:text-2xl md:text-3xl font-bold font-display ${isDark ? 'text-white' : 'text-slate-900'}`}>
              Alerts &amp; Automation Command Center
            </h1>
            <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-500 border border-amber-500/30">
              ADMIN
            </span>
            <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${
              isDark 
                ? 'bg-white/10 text-white/90 border-white/20' 
                : 'bg-slate-200 text-slate-800 border-slate-300'
            }`}>
              {alerts.length} {alerts.length === 1 ? 'Event' : 'Events'} Logged
            </span>
          </div>
          <p className={`text-xs sm:text-sm md:text-base leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-600'}`}>
            Multi-ministry risk threshold evaluation, automated n8n webhook pipelines, email dispatch telemetry, and crossing event audit logs.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            type="button"
            onClick={loadAlerts}
            className={`px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all cursor-pointer shadow-md flex items-center gap-1.5 ${
              isDark
                ? 'bg-white text-black hover:bg-slate-200'
                : 'bg-slate-900 text-white hover:bg-black'
            }`}
          >
            <span>↻</span>
            <span>Refresh All</span>
          </button>
        </div>
      </GlassCard>


      {/* n8n Webhook & Event Trigger Panel */}
      <div className="oled-solid-card p-5 sm:p-6 space-y-4">
        <div className={`flex flex-col md:flex-row md:items-center justify-between gap-3 border-b pb-3 ${
          isDark ? 'border-white/10' : 'border-slate-200'
        }`}>
          <div>
            <h3 className={`text-sm sm:text-base font-bold flex items-center gap-2 ${
              isDark ? 'text-white' : 'text-slate-900'
            }`}>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              Automated n8n Webhook Pipeline
            </h3>
            <p className={`text-xs mt-0.5 font-mono ${isDark ? 'text-white/60' : 'text-slate-600'}`}>
              Target: <code className="text-amber-500 font-bold">https://hrishikesh1.app.n8n.cloud/webhook/project-risk-threshold</code>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-500 text-xs font-mono font-bold border border-emerald-500/30">
              Active · Connected
            </span>
          </div>
        </div>

        {/* Test Event Simulator */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end pt-1">
          <div>
            <label className={`block text-[11px] font-mono uppercase mb-1 ${isDark ? 'text-white/70' : 'text-slate-700 font-semibold'}`}>Project ID</label>
            <input
              type="text"
              value={simulatedProjectId}
              onChange={e => setSimulatedProjectId(e.target.value)}
              className={`w-full px-3 py-1.5 rounded-lg font-mono text-xs outline-none border transition-colors ${
                isDark
                  ? 'bg-black/50 border-white/20 text-white focus:border-white/50'
                  : 'bg-white border-slate-300 text-slate-900 focus:border-slate-500'
              }`}
            />
          </div>

          <div>
            <label className={`block text-[11px] font-mono uppercase mb-1 ${isDark ? 'text-white/70' : 'text-slate-700 font-semibold'}`}>DPHIS Score</label>
            <input
              type="number"
              min="1"
              max="100"
              step="0.5"
              value={simulatedDphis}
              onChange={e => setSimulatedDphis(Number(e.target.value))}
              className={`w-full px-3 py-1.5 rounded-lg font-mono text-xs outline-none border transition-colors ${
                isDark
                  ? 'bg-black/50 border-white/20 text-white focus:border-white/50'
                  : 'bg-white border-slate-300 text-slate-900 focus:border-slate-500'
              }`}
            />
          </div>

          <div>
            <label className={`block text-[11px] font-mono uppercase mb-1 ${isDark ? 'text-white/70' : 'text-slate-700 font-semibold'}`}>Project Threshold</label>
            <input
              type="number"
              min="1"
              max="100"
              value={simulatedThreshold}
              onChange={e => setSimulatedThreshold(Number(e.target.value))}
              className={`w-full px-3 py-1.5 rounded-lg font-mono text-xs outline-none border transition-colors ${
                isDark
                  ? 'bg-black/50 border-white/20 text-white focus:border-white/50'
                  : 'bg-white border-slate-300 text-slate-900 focus:border-slate-500'
              }`}
            />
          </div>

          <div>
            <button
              type="button"
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
              ? 'bg-red-500/15 border-red-500/30 text-red-500 font-semibold'
              : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-600 font-semibold'
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
          <h3 className={`text-sm font-mono font-bold uppercase tracking-wider ${isDark ? 'text-white/70' : 'text-slate-700'}`}>
            System Alert Events ({alerts.length})
          </h3>
          <span className={`text-xs font-mono ${isDark ? 'text-white/50' : 'text-slate-500'}`}>Stored in MongoDB · Persisted before webhook</span>
        </div>

        {alerts.length === 0 ? (
          <div className={`oled-solid-card p-12 text-center text-xs font-mono ${isDark ? 'text-white/60' : 'text-slate-500'}`}>
            No alert events recorded in database.
          </div>
        ) : (
          <div className={`overflow-x-auto rounded-xl border backdrop-blur-md ${
            isDark ? 'border-white/15 bg-black/40' : 'border-slate-300 bg-white shadow-sm'
          }`}>
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className={`border-b font-mono text-[10px] uppercase font-bold ${
                  isDark ? 'border-white/15 bg-[#0B0F17] text-white/70' : 'border-slate-200 bg-slate-100 text-slate-700'
                }`}>
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
              <tbody className={`divide-y font-mono text-xs ${isDark ? 'divide-white/5' : 'divide-slate-200'}`}>
                {alerts.map(a => {
                  const score = a.current_dphis ?? a.dphis ?? 70.0;
                  const thresh = a.threshold ?? 70.0;
                  const cat = getRiskCategory(score);
                  const isAck = a.status === 'ACKNOWLEDGED';

                  return (
                    <tr key={a.alert_id} className={`transition-colors ${isDark ? 'hover:bg-white/5' : 'hover:bg-slate-50'}`}>
                      <td className={`p-3.5 font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{a.alert_id}</td>
                      <td className="p-3.5 font-sans">
                        <div className={`font-semibold ${isDark ? 'text-white' : 'text-slate-900'}`}>{a.project_name || a.project_id}</div>
                        <div className={`text-[11px] font-mono ${isDark ? 'text-white/50' : 'text-slate-500'}`}>{a.project_id}</div>
                      </td>
                      <td className="p-3.5">
                        <span className={`font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{score}</span>
                        <span className={isDark ? 'text-white/40' : 'text-slate-500'}> / {thresh}</span>
                      </td>
                      <td className="p-3.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${cat.badgeBg}`}>
                          {cat.label}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          a.notification_status === 'sent'
                            ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/30'
                            : a.notification_status === 'failed'
                            ? 'bg-red-500/20 text-red-500 border border-red-500/30'
                            : 'bg-amber-500/20 text-amber-500 border border-amber-500/30'
                        }`}>
                          {a.notification_status || 'sent'}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span className={isAck ? (isDark ? 'text-white/50' : 'text-slate-500') : 'text-amber-500 font-bold'}>
                          {a.status}
                        </span>
                      </td>
                      <td className={`p-3.5 text-[11px] ${isDark ? 'text-white/50' : 'text-slate-500'}`}>
                        {a.created_at ? new Date(a.created_at).toLocaleDateString() : 'Recent'}
                      </td>
                      <td className="p-3.5">
                        <div className="flex items-center gap-1.5">
                          {!isAck && (
                            <button
                              type="button"
                              onClick={() => handleAcknowledge(a.alert_id)}
                              className={`px-2 py-1 rounded text-[11px] font-bold transition-all cursor-pointer ${
                                isDark 
                                  ? 'bg-white/10 hover:bg-white/20 text-white' 
                                  : 'bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300'
                              }`}
                            >
                              ✓ Ack
                            </button>
                          )}
                          {onNavigateToProject && (
                            <button
                              type="button"
                              onClick={() => onNavigateToProject(a.project_id)}
                              className={`px-2 py-1 rounded text-[11px] font-bold transition-all cursor-pointer shadow-sm ${
                                isDark 
                                  ? 'bg-white text-black hover:bg-slate-200' 
                                  : 'bg-slate-900 text-white hover:bg-black'
                              }`}
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
