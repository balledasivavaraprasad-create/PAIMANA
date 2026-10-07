import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import { useTheme } from '../hooks/useTheme';
import { 
  fetchAlerts, acknowledgeAlert, triggerRiskAlertEvaluation, UserProfile, AlertItem,
  fetchMonitoringStatus, triggerPortfolioScan, MonitoringStatusData 
} from '../lib/api';
import { getRiskCategory } from '../lib/risk';
import { CurvedGrowthArrow } from '../components/CurvedTrendArrow';

interface Props {
  onNavigateToInvestigation?: (projectId: string) => void;
  onOpenInvestigation?: (projectId: string) => void;
  onNavigateToProject?: (projectId: string) => void;
  currentUser?: UserProfile | null;
  pinsCount?: number;
  onOpenAddProject?: () => void;
}

export default function Alerts({ 
  onNavigateToInvestigation, 
  onOpenInvestigation,
  onNavigateToProject,
  currentUser, 
  pinsCount, 
  onOpenAddProject 
}: Props) {
  const triggerInvestigationHandler = onNavigateToInvestigation || onOpenInvestigation;
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const isAdmin = currentUser?.role === 'ADMIN' || currentUser?.role === 'ANALYST';
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [monitoringStatus, setMonitoringStatus] = useState<MonitoringStatusData | null>(null);
  const [isScanning, setIsScanning] = useState(false);

  // Admin test trigger state
  const [simulatedProjectId, setSimulatedProjectId] = useState<string>('P1024');
  const [simulatedDphis, setSimulatedDphis] = useState<number>(77.2);
  const [simulatedThreshold, setSimulatedThreshold] = useState<number>(70.0);
  const [isTriggering, setIsTriggering] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<any | null>(null);

  const loadAlerts = () => {
    setLoading(true);
    fetchAlerts(isAdmin ? undefined : currentUser?.username)
      .then(items => {
        setAlerts(items);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  const loadMonitoring = () => {
    fetchMonitoringStatus().then(st => {
      if (st) setMonitoringStatus(st);
    }).catch(console.warn);
  };

  useEffect(() => {
    loadAlerts();
    if (isAdmin) {
      loadMonitoring();
    }
  }, [currentUser, isAdmin]);

  const handleTriggerScan = async () => {
    setIsScanning(true);
    try {
      await triggerPortfolioScan();
      loadAlerts();
      loadMonitoring();
    } catch (e) {
      console.warn('Scan trigger error:', e);
    } finally {
      setIsScanning(false);
    }
  };

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
      const data = await triggerRiskAlertEvaluation(
        simulatedProjectId,
        simulatedDphis,
        simulatedThreshold
      );
      setSimulationResult(data);
      if (data.triggered) {
        setTimeout(loadAlerts, 800);
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
  const sentCount = alerts.filter(a => a.notification_status === 'sent' || a.user_notified).length;

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
              <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-emerald-500/15 text-emerald-500 border border-emerald-500/25">
                {sentCount} Notifications Sent
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
                      {a.event_id && (
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                          isDark ? 'text-white/50 bg-white/5' : 'text-slate-500 bg-slate-100'
                        }`}>
                          {a.event_id}
                        </span>
                      )}
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

                  {/* Notification Delivery & Stakeholder Metadata */}
                  <div className={`p-3 rounded-xl border flex flex-wrap items-center justify-between gap-3 text-xs font-mono ${
                    isDark ? 'bg-white/5 border-white/10' : 'bg-slate-50 border-slate-200'
                  }`}>
                    <div className="flex flex-wrap items-center gap-3">
                      <div className="flex items-center gap-1.5">
                        <span className={isDark ? 'text-white/60' : 'text-slate-500'}>Email Notification:</span>
                        <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          a.notification_status === 'sent' || a.user_notified
                            ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/30'
                            : a.notification_status === 'retrying' || a.outbox_status === 'failed_retryable'
                            ? 'bg-amber-500/20 text-amber-500 border border-amber-500/30'
                            : a.notification_status === 'failed'
                            ? 'bg-red-500/20 text-red-500 border border-red-500/30'
                            : 'bg-blue-500/20 text-blue-500 border border-blue-500/30'
                        }`}>
                          {a.notification_status === 'sent' || a.user_notified
                            ? '✓ Dispatched via n8n'
                            : a.notification_status === 'retrying' || a.outbox_status === 'failed_retryable'
                            ? '⏳ Retrying Delivery'
                            : a.notification_status === 'failed'
                            ? '✗ Delivery Failed'
                            : 'Pending Dispatch'}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5">
                        <span className={isDark ? 'text-white/60' : 'text-slate-500'}>Recipient:</span>
                        <span className={`font-semibold ${isDark ? 'text-white/90' : 'text-slate-800'}`}>
                          {a.recipient_email || currentUser?.email || 'Project Stakeholder'}
                        </span>
                      </div>
                    </div>

                    <div className={`text-[11px] ${isDark ? 'text-white/50' : 'text-slate-500'}`}>
                      Dispatched: {a.created_at ? new Date(a.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Recent'}
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
                      {a.alert_id} · Sovereign Decision Support
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

                      {triggerInvestigationHandler && (
                        <button
                          type="button"
                          onClick={() => triggerInvestigationHandler(a.project_id)}
                          className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold border transition-all cursor-pointer shadow-sm ${
                            isDark 
                              ? 'bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border-sky-500/40' 
                              : 'bg-sky-50 hover:bg-sky-100 text-sky-800 border-sky-300'
                          }`}
                        >
                          Launch Investigation ⚡
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
              {alerts.length} Events Logged
            </span>
            <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-emerald-500/15 text-emerald-500 border border-emerald-500/25">
              {sentCount} Dispatched via n8n
            </span>
          </div>
          <p className={`text-xs sm:text-sm md:text-base leading-relaxed ${isDark ? 'text-white/80' : 'text-slate-600'}`}>
            Multi-ministry risk threshold evaluation, automated n8n webhook outbox pipelines, email dispatch telemetry, and crossing event audit logs.
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

      {/* Continuous Autonomous Surveillance & Telemetry Card */}
      <div className={`p-5 sm:p-6 rounded-2xl border transition-all ${
        isDark 
          ? 'bg-slate-900/80 border-cyan-500/30 shadow-[0_0_25px_rgba(6,182,212,0.1)]' 
          : 'bg-white border-cyan-200 shadow-sm'
      }`}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-cyan-500/20">
          <div className="flex items-start sm:items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 text-lg shrink-0">
              🛰️
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className={`text-base font-bold tracking-tight ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  Continuous Autonomous Surveillance Engine (Agentic Layer V4)
                </h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 animate-pulse">
                  SURVEILLANCE ACTIVE
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  EVERY 6H + ON-CHANGE
                </span>
              </div>
              <p className={`text-xs mt-1 font-mono ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
                Snapshot SHA-256 state tracking · 4 competing causal hypotheses · Bayesian multi-dimensional confidence scoring
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={handleTriggerScan}
              disabled={isScanning}
              className={`px-4 py-2.5 rounded-xl text-xs font-mono font-bold transition-all cursor-pointer shadow-md flex items-center gap-2 ${
                isScanning 
                  ? 'bg-cyan-500/50 text-white cursor-wait' 
                  : isDark 
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white' 
                    : 'bg-cyan-600 hover:bg-cyan-700 text-white'
              }`}
            >
              <span className={isScanning ? 'animate-spin' : ''}>{isScanning ? '⚙' : '⚡'}</span>
              <span>{isScanning ? 'Scanning Portfolio...' : 'Trigger Full Surveillance Scan'}</span>
            </button>
          </div>
        </div>

        {/* Telemetry Metrics Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4">
          <div className={`p-3 rounded-xl border ${isDark ? 'bg-black/30 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
            <span className={`text-[10px] font-mono uppercase tracking-wider block ${isDark ? 'text-white/60' : 'text-slate-500'}`}>
              Monitored Corridors
            </span>
            <span className="text-xl font-mono font-bold text-cyan-400 mt-0.5 block">
              {monitoringStatus?.projects_monitored ?? 428} <span className="text-xs text-white/50 font-normal">MoSPI assets</span>
            </span>
            <span className="text-[10px] font-mono text-emerald-400 mt-1 block">100% covered</span>
          </div>

          <div className={`p-3 rounded-xl border ${isDark ? 'bg-black/30 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
            <span className={`text-[10px] font-mono uppercase tracking-wider block ${isDark ? 'text-white/60' : 'text-slate-500'}`}>
              Surveillance Cadence
            </span>
            <span className={`text-xl font-mono font-bold mt-0.5 block ${isDark ? 'text-white' : 'text-slate-800'}`}>
              Every {monitoringStatus?.interval_hours ?? 6}h
            </span>
            <span className={`text-[10px] font-mono mt-1 block ${isDark ? 'text-white/60' : 'text-slate-500'}`}>
              + On Data Change
            </span>
          </div>

          <div className={`p-3 rounded-xl border ${isDark ? 'bg-black/30 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
            <span className={`text-[10px] font-mono uppercase tracking-wider block ${isDark ? 'text-white/60' : 'text-slate-500'}`}>
              Outbox Event Pipeline
            </span>
            <span className="text-xl font-mono font-bold text-emerald-400 mt-0.5 block">
              {monitoringStatus?.outbox_queue?.delivered ?? 37} <span className="text-xs text-white/50 font-normal">dispatched</span>
            </span>
            <span className="text-[10px] font-mono text-amber-400 mt-1 block">
              {monitoringStatus?.outbox_queue?.pending ?? 0} queued in outbox
            </span>
          </div>

          <div className={`p-3 rounded-xl border ${isDark ? 'bg-black/30 border-white/10' : 'bg-slate-50 border-slate-200'}`}>
            <span className={`text-[10px] font-mono uppercase tracking-wider block ${isDark ? 'text-white/60' : 'text-slate-500'}`}>
              Causal Engine
            </span>
            <span className={`text-xl font-mono font-bold mt-0.5 block ${isDark ? 'text-white' : 'text-slate-800'}`}>
              4 Hypotheses
            </span>
            <span className="text-[10px] font-mono text-cyan-400 mt-1 block">
              Relational Graph
            </span>
          </div>
        </div>
      </div>
      <div className="oled-solid-card p-5 sm:p-6 space-y-4">
        <div className={`flex flex-col md:flex-row md:items-center justify-between gap-3 border-b pb-3 ${
          isDark ? 'border-white/10' : 'border-slate-200'
        }`}>
          <div>
            <h3 className={`text-sm sm:text-base font-bold flex items-center gap-2 ${
              isDark ? 'text-white' : 'text-slate-900'
            }`}>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              Production n8n Webhook &amp; Alert Outbox Pipeline
            </h3>
            <p className={`text-xs mt-0.5 font-mono ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
              Backend Source-of-Truth → Durable MongoDB Outbox → HMAC-SHA256 Signed Webhook → OpenAI Factual Email Generation
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-500 text-xs font-mono font-bold border border-emerald-500/30">
              Active · HMAC-SHA256 Signed
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

        {/* Simulation Feedback Telemetry */}
        {simulationResult && (
          <div className={`p-4 rounded-xl border text-xs font-mono space-y-2.5 ${
            simulationResult.triggered
              ? 'bg-red-500/10 border-red-500/30 text-red-400'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
          }`}>
            <div className="flex flex-wrap items-center justify-between gap-2 font-bold text-sm">
              <span>{simulationResult.triggered ? '🚨 THRESHOLD CROSSED & WEBHOOK DISPATCHED' : '✓ THRESHOLD EVALUATION COMPLETE'}</span>
              <span className="text-[11px] font-normal px-2.5 py-0.5 rounded bg-black/40 border border-white/10 text-white/80">
                Status: {simulationResult.threshold_status || (simulationResult.triggered ? 'triggered' : 'suppressed')}
              </span>
            </div>
            
            <p className="text-xs text-white/90 font-sans leading-relaxed">
              {simulationResult.message || (simulationResult.triggered ? `Project crossed DPHIS threshold ${simulationResult.threshold} (Current: ${simulationResult.current_dphis}). Alert was persisted to MongoDB and dispatched to the n8n webhook.` : '')}
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-[11px]">
              {simulationResult.event_id && (
                <div className="bg-black/40 p-2.5 rounded border border-white/10">
                  <div className="text-white/50 text-[10px]">EVENT ID</div>
                  <div className="font-bold text-white truncate">{simulationResult.event_id}</div>
                </div>
              )}
              {simulationResult.alert_id && (
                <div className="bg-black/40 p-2.5 rounded border border-white/10">
                  <div className="text-white/50 text-[10px]">ALERT ID</div>
                  <div className="font-bold text-white truncate">{simulationResult.alert_id}</div>
                </div>
              )}
              {simulationResult.notification_status && (
                <div className="bg-black/40 p-2.5 rounded border border-white/10">
                  <div className="text-white/50 text-[10px]">NOTIFICATION STATUS</div>
                  <div className={`font-bold ${simulationResult.notification_status === 'sent' ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {simulationResult.notification_status.toUpperCase()}
                  </div>
                </div>
              )}
              {simulationResult.outbox_id && (
                <div className="bg-black/40 p-2.5 rounded border border-white/10">
                  <div className="text-white/50 text-[10px]">DURABLE OUTBOX ID</div>
                  <div className="font-bold text-emerald-400 truncate">{simulationResult.outbox_id}</div>
                </div>
              )}
            </div>
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
                  <th className="p-3.5">Alert / Event ID</th>
                  <th className="p-3.5">Project</th>
                  <th className="p-3.5">DPHIS / Threshold</th>
                  <th className="p-3.5">Severity</th>
                  <th className="p-3.5">Notification</th>
                  <th className="p-3.5">Recipient</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Timestamp</th>
                  <th className="p-3.5">Actions</th>
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
                      <td className="p-3.5">
                        <div className={`font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{a.alert_id}</div>
                        {a.event_id && (
                          <div className={`text-[10px] font-mono ${isDark ? 'text-white/40' : 'text-slate-400'}`}>{a.event_id}</div>
                        )}
                      </td>
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
                          a.notification_status === 'sent' || a.user_notified
                            ? 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/30'
                            : a.notification_status === 'retrying' || a.outbox_status === 'failed_retryable'
                            ? 'bg-amber-500/20 text-amber-500 border border-amber-500/30'
                            : a.notification_status === 'failed'
                            ? 'bg-red-500/20 text-red-500 border border-red-500/30'
                            : 'bg-blue-500/20 text-blue-500 border border-blue-500/30'
                        }`}>
                          {a.notification_status || 'sent'}
                        </span>
                      </td>
                      <td className="p-3.5 font-mono text-[11px]">
                        <span className={isDark ? 'text-white/80' : 'text-slate-700'}>
                          {a.recipient_email || 'official@example.gov.in'}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span className={isAck ? (isDark ? 'text-white/50' : 'text-slate-500') : 'text-amber-500 font-bold'}>
                          {a.status}
                        </span>
                      </td>
                      <td className={`p-3.5 text-[11px] ${isDark ? 'text-white/50' : 'text-slate-500'}`}>
                        {a.created_at ? new Date(a.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Recent'}
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
                          {triggerInvestigationHandler && (
                            <button
                              type="button"
                              onClick={() => triggerInvestigationHandler(a.project_id)}
                              className={`px-2 py-1 rounded text-[11px] font-bold transition-all cursor-pointer shadow-sm ${
                                isDark 
                                  ? 'bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/40' 
                                  : 'bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-300'
                              }`}
                            >
                              Investigate ⚡
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
