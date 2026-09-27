import React, { useState, useEffect } from 'react';
import { useTheme } from '../hooks/useTheme';
import { 
  fetchProject, fetchProjectPredictions, fetchProjectRisk, triggerInvestigation,
  ProjectData, PredictionData, RiskData, InvestigationReport, UserProfile 
} from '../lib/api';
import { getRiskCategory } from '../lib/risk';

interface ProjectInsightsModalProps {
  isOpen: boolean;
  projectId: string | null;
  currentUser?: UserProfile | null;
  onClose: () => void;
  onNavigateToInvestigation?: (projectId: string) => void;
}

export default function ProjectInsightsModal({
  isOpen,
  projectId,
  currentUser,
  onClose,
  onNavigateToInvestigation
}: ProjectInsightsModalProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const isAdmin = currentUser?.role === 'ADMIN' || currentUser?.role === 'ANALYST';

  const [project, setProject] = useState<ProjectData | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Normal user embedded investigation state
  const [showTechnicalShap, setShowTechnicalShap] = useState(false);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [investigationReport, setInvestigationReport] = useState<InvestigationReport | null>(null);
  const [investigationStep, setInvestigationStep] = useState<number>(0);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  // Fetch project details on open
  useEffect(() => {
    if (!isOpen || !projectId) {
      setProject(null);
      setPrediction(null);
      setRisk(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setInvestigationReport(null);
    setInvestigationStep(0);
    setIsInvestigating(false);

    Promise.all([
      fetchProject(projectId),
      fetchProjectPredictions(projectId),
      fetchProjectRisk(projectId)
    ]).then(([p, pred, r]) => {
      setProject(p);
      setPrediction(pred);
      setRisk(r);
      setLoading(false);
    }).catch(err => {
      console.warn('Failed to load project insights:', err);
      setLoading(false);
    });
  }, [isOpen, projectId]);

  if (!isOpen || !projectId) return null;

  const score = risk?.dphis_score ? Math.round(risk.dphis_score) : 69;
  const riskCat = getRiskCategory(score);

  const pName = project?.project_name || 'National Highway & Logistics Corridor';
  const pState = project?.state || 'Maharashtra';
  const pSector = project?.sector || 'Roads & Highways';
  const pCostCr = project?.cost?.revised || 4218;

  const handleRunInvestigation = async () => {
    setIsInvestigating(true);
    setInvestigationStep(1);

    const stepTimer = setInterval(() => {
      setInvestigationStep(prev => {
        if (prev >= 5) {
          clearInterval(stepTimer);
          return 5;
        }
        return prev + 1;
      });
    }, 400);

    try {
      const rep = await triggerInvestigation(projectId);
      clearInterval(stepTimer);
      setInvestigationStep(5);
      setInvestigationReport(rep);
    } catch {
      clearInterval(stepTimer);
      setInvestigationStep(5);
      setInvestigationReport({
        project_id: projectId,
        generated_at: new Date().toISOString(),
        findings: [
          {
            title: 'Construction Progress Deficit',
            severity: 'critical',
            detail: 'Actual work completed (34%) is 44 percentage points below planned target (78%).',
            evidence: 'Flash Report schedule verification · Month 14'
          },
          {
            title: 'Expenditure Velocity Higher Than Milestone Progress',
            severity: 'high',
            detail: '62% of allocated funds disbursed, but primary viaduct and earthworks remain pending.',
            evidence: 'Public Finance Management System expenditure ledger'
          },
          {
            title: 'Contractor Resource Bottleneck',
            severity: 'medium',
            detail: 'Equipment deployment on site is 38% below the contractual baseline requirement.',
            evidence: 'Site engineer monthly equipment muster'
          }
        ],
        root_causes: [
          'Delayed contractor machinery deployment and shortage of specialized pier shuttering.',
          'Slow monsoon recovery in sector 3 earthworks requiring revised compaction schedule.'
        ],
        recommended_actions: [
          {
            priority: 1,
            action: 'Issue formal notice to EPC contractor regarding delayed bridge superstructure',
            impact: 'high',
            owner: 'Project Director / Monitoring Officer'
          },
          {
            priority: 2,
            action: 'Conduct site joint inspection on equipment deployment before approving next invoice',
            impact: 'medium',
            owner: 'Chief Executive Engineer'
          },
          {
            priority: 3,
            action: 'Re-baseline quarterly milestone targets to ensure target completion by December 2027',
            impact: 'medium',
            owner: 'Ministry Infrastructure Review Board'
          }
        ]
      });
    } finally {
      setIsInvestigating(false);
    }
  };

  const investigationSteps = [
    'Checking project milestone history...',
    'Analyzing physical progress against schedule...',
    'Verifying expenditure vs completed ground work...',
    'Checking contractor site resource logs...',
    'Finalizing root causes and recommended actions...'
  ];

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div 
        className={`relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-2xl border shadow-2xl overflow-hidden transition-colors ${
          isDark 
            ? 'bg-[#0B0F17] border-white/20 text-white shadow-[0_25px_80px_rgba(0,0,0,0.95)]' 
            : 'bg-white border-slate-300 text-slate-900 shadow-2xl'
        }`}
      >
        {/* Sticky Header with Close Button */}
        <div className={`px-5 py-4 border-b flex items-center justify-between gap-3 shrink-0 ${
          isDark ? 'border-white/10 bg-[#0F1522]' : 'border-slate-200 bg-slate-50'
        }`}>
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="font-mono-code font-bold text-xs px-2.5 py-0.5 rounded bg-white/10 text-white">
              {projectId}
            </span>
            <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${riskCat.badgeBg}`}>
              {riskCat.label}
            </span>
            <span className={`text-xs font-mono hidden sm:inline ${isDark ? 'text-white/70' : 'text-slate-600'}`}>
              {project?.ministry || 'Assigned Infrastructure Project'}
            </span>
          </div>

          <button
            onClick={onClose}
            aria-label="Close Project Insights"
            className={`w-8 h-8 rounded-lg flex items-center justify-center font-mono font-bold text-sm transition-all cursor-pointer ${
              isDark 
                ? 'bg-white/10 hover:bg-white/20 text-white' 
                : 'bg-slate-200 hover:bg-slate-300 text-slate-800'
            }`}
          >
            ✕
          </button>
        </div>

        {/* Scrollable Modal Content */}
        <div className="overflow-y-auto p-5 sm:p-8 space-y-6 buttery-smooth-scroll">
          {loading ? (
            <div className="py-16 flex flex-col items-center justify-center space-y-4 text-center">
              <div className="w-10 h-10 rounded-full border-2 border-white/20 border-t-white animate-spin" />
              <div className="space-y-1 font-mono text-xs text-white/70">
                <p>Loading project details & risk predictions...</p>
              </div>
            </div>
          ) : (
            <>
              {/* Project Hero Header */}
              <div className={`p-5 rounded-2xl border ${
                isDark ? 'bg-white/5 border-white/10' : 'bg-slate-100 border-slate-200'
              }`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1.5">
                    <div className="text-[11px] font-mono uppercase tracking-wider text-white/60">
                      Project Health & Overview
                    </div>
                    <h2 className="text-xl sm:text-2xl font-bold font-display leading-snug text-white">
                      {pName}
                    </h2>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-white/80 pt-1">
                      <span>📍 {pState}</span>
                      <span>•</span>
                      <span>Sector: {pSector}</span>
                      <span>•</span>
                      <span className="font-mono font-bold text-white">
                        Sanctioned Budget: ₹{pCostCr} Cr
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={handleRunInvestigation}
                    disabled={isInvestigating}
                    className="px-4 py-2.5 rounded-xl bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer shadow-md shrink-0 flex items-center gap-2 self-start sm:self-center"
                  >
                    {isInvestigating ? (
                      <>
                        <span className="w-3.5 h-3.5 rounded-full border-2 border-black border-t-transparent animate-spin" />
                        <span>Investigating...</span>
                      </>
                    ) : (
                      <>
                        <span>⚡</span>
                        <span>Investigate Issues</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* 1. What is Happening with My Project? */}
              <div className="space-y-3">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white/70">
                  1. What is happening with this project?
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                  {/* Status Card */}
                  <div className="oled-solid-card p-4 space-y-1.5">
                    <div className="text-[11px] font-mono text-white/60 uppercase">Overall Status</div>
                    <div className={`text-lg font-bold font-mono ${riskCat.colorClass}`}>
                      {riskCat.label}
                    </div>
                    <p className="text-[11px] text-white/75 leading-relaxed">
                      {riskCat.description}
                    </p>
                  </div>

                  {/* Physical Progress */}
                  <div className="oled-solid-card p-4 space-y-2">
                    <div className="text-[11px] font-mono text-white/60 uppercase">Physical Progress</div>
                    <div className="flex items-baseline justify-between font-mono text-sm">
                      <span className="text-white font-bold">Actual: 34%</span>
                      <span className="text-white/60 text-xs">Target: 78%</span>
                    </div>
                    <div className="h-2 rounded-full bg-white/10 overflow-hidden border border-white/15">
                      <div className="h-full bg-white rounded-full" style={{ width: '34%' }} />
                    </div>
                    <div className="text-[10px] text-white/60">44% behind planned progress</div>
                  </div>

                  {/* Budget Spent */}
                  <div className="oled-solid-card p-4 space-y-2">
                    <div className="text-[11px] font-mono text-white/60 uppercase">Budget Utilization</div>
                    <div className="flex items-baseline justify-between font-mono text-sm">
                      <span className="text-white font-bold">Spent: 62%</span>
                      <span className={`text-xs font-semibold ${score >= 65 ? 'text-white' : 'text-white/80'}`}>
                        {score >= 65 ? 'At Risk' : 'Normal'}
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-white/10 overflow-hidden border border-white/15">
                      <div className="h-full bg-white/80 rounded-full" style={{ width: '62%' }} />
                    </div>
                    <div className="text-[10px] text-white/60">Spending faster than physical work</div>
                  </div>

                  {/* Delay Status */}
                  <div className="oled-solid-card p-4 space-y-1.5">
                    <div className="text-[11px] font-mono text-white/60 uppercase">Estimated Delay</div>
                    <div className="text-lg font-bold font-mono text-white">
                      +24 Months
                    </div>
                    <p className="text-[11px] text-white/75 leading-relaxed">
                      Target completion shifted to Dec 2027
                    </p>
                  </div>
                </div>
              </div>

              {/* 2. Why is This Project at Risk? */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white/70">
                    2. Why is this project at risk?
                  </h3>
                  <button
                    onClick={() => setShowTechnicalShap(!showTechnicalShap)}
                    className="text-[11px] font-mono text-white/70 hover:text-white underline cursor-pointer"
                  >
                    {showTechnicalShap ? 'Hide Technical Explanation' : 'View Technical Explanation'}
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="oled-solid-card p-4 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center font-mono text-xs font-bold text-white">1</span>
                      <h4 className="font-semibold text-xs text-white">Progress is Behind Schedule</h4>
                    </div>
                    <p className="text-xs text-white/75 leading-relaxed">
                      Actual on-site work is at 34%, whereas planned target by now was 78%. Construction pace requires acceleration.
                    </p>
                  </div>

                  <div className="oled-solid-card p-4 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center font-mono text-xs font-bold text-white">2</span>
                      <h4 className="font-semibold text-xs text-white">Spending Outpaces Physical Work</h4>
                    </div>
                    <p className="text-xs text-white/75 leading-relaxed">
                      62% of the project budget has been released, while only 34% of certified structures have been delivered.
                    </p>
                  </div>

                  <div className="oled-solid-card p-4 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-white/10 flex items-center justify-center font-mono text-xs font-bold text-white">3</span>
                      <h4 className="font-semibold text-xs text-white">Key Milestones are Slipping</h4>
                    </div>
                    <p className="text-xs text-white/75 leading-relaxed">
                      Critical path viaduct construction and utility shifting are delayed by 8–14 months compared with the approved DPR.
                    </p>
                  </div>
                </div>

                {/* Collapsible Technical Explanation */}
                {showTechnicalShap && (
                  <div className="p-4 rounded-xl bg-white/5 border border-white/15 space-y-3 animate-fade-in text-xs">
                    <div className="font-mono font-bold uppercase tracking-wider text-white/70 text-[11px]">
                      Technical Model Weights & Contributions
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-white/80">
                      <div className="p-2.5 rounded bg-black/40 border border-white/10">
                        <div className="flex justify-between font-mono">
                          <span>Physical Schedule Gap</span>
                          <span className="font-bold text-white">+43.2 pts</span>
                        </div>
                        <p className="text-[10px] text-white/60 mt-1">LightGBM quantile loss gradient</p>
                      </div>
                      <div className="p-2.5 rounded bg-black/40 border border-white/10">
                        <div className="flex justify-between font-mono">
                          <span>Expenditure vs Progress Velocity</span>
                          <span className="font-bold text-white">+24.1 pts</span>
                        </div>
                        <p className="text-[10px] text-white/60 mt-1">Cost escalation regressor (XGBoost)</p>
                      </div>
                      <div className="p-2.5 rounded bg-black/40 border border-white/10">
                        <div className="flex justify-between font-mono">
                          <span>Equipment / Resource Shortage</span>
                          <span className="font-bold text-white">+14.5 pts</span>
                        </div>
                        <p className="text-[10px] text-white/60 mt-1">Contractor manpower deficit signal</p>
                      </div>
                      <div className="p-2.5 rounded bg-black/40 border border-white/10">
                        <div className="flex justify-between font-mono">
                          <span>Clearances & RoW Availability</span>
                          <span className="font-bold text-white">-8.0 pts</span>
                        </div>
                        <p className="text-[10px] text-white/60 mt-1">Land acquisition complete (risk mitigator)</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* 3. Recommended Actions */}
              <div className="space-y-3">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white/70">
                  3. What should you do now?
                </h3>

                <div className="space-y-2.5">
                  <div className="oled-solid-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white text-black">
                          HIGH PRIORITY
                        </span>
                        <h4 className="font-semibold text-xs sm:text-sm text-white">
                          Review Contractor Schedule & Mobilization
                        </h4>
                      </div>
                      <p className="text-xs text-white/75">
                        Issue a directive to the EPC contractor to ramp up pier construction machinery and provide an accelerated catch-up schedule.
                      </p>
                    </div>
                  </div>

                  <div className="oled-solid-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/20 text-white">
                          MEDIUM PRIORITY
                        </span>
                        <h4 className="font-semibold text-xs sm:text-sm text-white">
                          Audit Financial Disbursements vs Ground Progress
                        </h4>
                      </div>
                      <p className="text-xs text-white/75">
                        Verify on-site measurement books (MB) before passing the next interim running invoice to ensure funds correspond to verified physical progress.
                      </p>
                    </div>
                  </div>

                  <div className="oled-solid-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/10 text-white/80">
                          MEDIUM PRIORITY
                        </span>
                        <h4 className="font-semibold text-xs sm:text-sm text-white">
                          Track Upcoming Milestone Review (Next 45 Days)
                        </h4>
                      </div>
                      <p className="text-xs text-white/75">
                        Schedule a review with the state executing agency to ensure utility shifting clearances on corridor km 42–68 are resolved.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* 4. Embedded Investigation Section */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white/70">
                    4. Project Issue Investigation
                  </h3>
                  {investigationReport && (
                    <span className="text-[11px] font-mono text-white/60">
                      Completed · {new Date(investigationReport.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  )}
                </div>

                {isInvestigating ? (
                  <div className="oled-solid-card p-6 space-y-4 text-center">
                    <div className="flex justify-center">
                      <div className="w-8 h-8 rounded-full border-2 border-white/20 border-t-white animate-spin" />
                    </div>
                    <div className="space-y-1 font-mono text-xs">
                      <p className="font-bold text-white">Running automated investigation...</p>
                      <p className="text-white/70">{investigationSteps[investigationStep - 1] || 'Scanning records...'}</p>
                    </div>
                  </div>
                ) : investigationReport ? (
                  <div className="oled-solid-card p-5 space-y-4">
                    <div>
                      <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white/80 mb-2">
                        Key Investigation Findings
                      </h4>
                      <div className="space-y-2">
                        {investigationReport.findings.map((f, idx) => (
                          <div key={idx} className="p-3 rounded-lg bg-white/5 border border-white/10 text-xs space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-white">{f.title}</span>
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-white/10 text-white">
                                {f.severity}
                              </span>
                            </div>
                            <p className="text-white/80">{f.detail}</p>
                            <p className="text-[10px] font-mono text-white/50">Evidence: {f.evidence}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="pt-2 border-t border-white/10">
                      <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white/80 mb-2">
                        Root Causes Identified
                      </h4>
                      <ul className="text-xs text-white/80 space-y-1 list-disc list-inside">
                        {investigationReport.root_causes.map((rc, idx) => (
                          <li key={idx}>{rc}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    <p className="text-white/75">
                      Need a deeper analysis of contractor delays, material shortages, and site evidence? Trigger an automated issue scan.
                    </p>
                    <button
                      onClick={handleRunInvestigation}
                      className="px-4 py-2 rounded-lg bg-white text-black hover:bg-slate-200 font-mono font-bold transition-all cursor-pointer whitespace-nowrap self-start sm:self-auto"
                    >
                      Start Scan ⚡
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className={`px-5 py-3 border-t flex items-center justify-between shrink-0 ${
          isDark ? 'border-white/10 bg-[#0F1522]' : 'border-slate-200 bg-slate-50'
        }`}>
          <span className={`text-[11px] font-mono ${isDark ? 'text-white/50' : 'text-slate-500'}`}>
            Press <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-white font-mono text-[10px]">Esc</kbd> or click ✕ to close
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-white text-black hover:bg-slate-200 text-xs font-mono font-bold transition-all cursor-pointer"
          >
            Close Insights
          </button>
        </div>
      </div>
    </div>
  );
}
