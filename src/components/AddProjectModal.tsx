import React, { useState } from 'react';
import { useTheme } from '../hooks/useTheme';
import { ingestNormalAsset, ProjectData, UserProfile } from '../lib/api';

interface AddProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserProfile | null;
  onProjectAdded: (newProject: ProjectData) => void;
}

export default function AddProjectModal({
  isOpen,
  onClose,
  currentUser,
  onProjectAdded
}: AddProjectModalProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // The 8 Standard Normal File Columns from FlashReport_July_2026.csv
  const [page, setPage] = useState<number>(1);
  const [sNo, setSNo] = useState<number>(1);
  const [projectId, setProjectId] = useState<string>('');
  const [projectName, setProjectName] = useState<string>('');
  const [originalCost, setOriginalCost] = useState<string>('');
  const [revisedCost, setRevisedCost] = useState<string>('');
  const [expenditure, setExpenditure] = useState<string>('');
  const [physicalProgress, setPhysicalProgress] = useState<string>('');

  // Contextual metadata
  const [state, setState] = useState<string>('Maharashtra');
  const [ministry, setMinistry] = useState<string>(currentUser?.ministry || 'Ministry of Road Transport & Highways');
  const [dphisThreshold, setDphisThreshold] = useState<number>(70);

  // Submission State
  const [loading, setLoading] = useState(false);
  const [statusStep, setStatusStep] = useState<string>('');
  const [error, setError] = useState<string>('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!projectId.trim() || !projectName.trim()) {
      setError('Project ID and Project Name are required.');
      return;
    }
    const origCostNum = parseFloat(originalCost);
    const revCostNum = parseFloat(revisedCost || originalCost);
    const expNum = parseFloat(expenditure || '0');
    const progNum = parseFloat(physicalProgress);

    if (isNaN(origCostNum) || origCostNum <= 0) {
      setError('Original Cost must be a positive number in ₹ Crores.');
      return;
    }
    if (isNaN(progNum) || progNum < 0 || progNum > 100) {
      setError('Physical Progress must be between 0% and 100%.');
      return;
    }

    setLoading(true);
    try {
      setStatusStep('Invoking Gemini Flash 2.5 AI for 57-Feature Engineering...');
      await new Promise(r => setTimeout(r, 600));

      setStatusStep('Synthesizing Risk Dimensions & Progress-Expenditure Velocity...');
      const createdProject = await ingestNormalAsset({
        page: Number(page) || 1,
        s_no: Number(sNo) || 1,
        project_id: projectId.trim().toUpperCase(),
        project_name: projectName.trim(),
        original_cost_crores: origCostNum,
        revised_cost_crores: revCostNum,
        expenditure_crores: expNum,
        physical_progress_percent: progNum,
        ministry: ministry.trim(),
        state: state.trim(),
        username: currentUser?.username,
        dphis_threshold: Number(dphisThreshold) || 70
      });

      setStatusStep('LightGBM Models Calibrated · DPHIS Index Calculated!');
      await new Promise(r => setTimeout(r, 400));

      onProjectAdded(createdProject);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to ingest project. Please check backend connection.');
    } finally {
      setLoading(false);
      setStatusStep('');
    }
  };

  const handleAutofillSample = () => {
    setProjectId(`PRJ_${Math.floor(1000 + Math.random() * 9000)}`);
    setProjectName('Varanasi-Kolkata Greenfield Economic Corridor Package 3');
    setOriginalCost('4250.0');
    setRevisedCost('4890.0');
    setExpenditure('2890.0');
    setPhysicalProgress('62.5');
    setSNo(1);
    setPage(1);
    setState('Uttar Pradesh');
    if (currentUser?.ministry) {
      setMinistry(currentUser.ministry);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className={`w-full max-w-2xl rounded-2xl border p-6 sm:p-8 backdrop-blur-2xl shadow-2xl transition-all max-h-[92vh] overflow-y-auto ${
        isDark ? 'bg-[#0A1222]/95 border-white/20 text-white shadow-black/80' : 'bg-white/95 border-slate-300 text-slate-900 shadow-xl'
      }`}>
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-5">
          <div>
            <div className="flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${isDark ? 'bg-white' : 'bg-black'}`} />
              <h2 className="text-xl font-serif font-bold tracking-wide">
                Add New Project
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Enter the 8 basic project details from the monthly report to compute risk scores and delay forecasts.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="text-slate-400 hover:text-white text-2xl font-mono cursor-pointer"
          >
            ×
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-400 text-xs font-mono font-medium">
            ⚠️ {error}
          </div>
        )}

        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center space-y-4 text-center">
            <div className="relative w-16 h-16">
              <div className={`w-16 h-16 rounded-full border-4 animate-spin ${
                isDark ? 'border-white/20 border-t-white' : 'border-black/20 border-t-black'
              }`} />
              <div className={`absolute inset-0 flex items-center justify-center font-mono font-bold text-xs ${
                isDark ? 'text-white' : 'text-black'
              }`}>
                AI
              </div>
            </div>
            <div className="space-y-1">
              <h4 className={`font-mono font-bold text-sm ${isDark ? 'text-white' : 'text-black'}`}>
                {statusStep || 'Saving project & analyzing...'}
              </h4>
              <p className="text-[11px] text-slate-400 font-mono">
                Calculating cost trends, delay projections, and risk scores.
              </p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Autofill helper */}
            <div className={`flex justify-between items-center p-2.5 rounded-lg text-xs font-mono border ${
              isDark ? 'bg-white/5 border-white/15 text-white' : 'bg-black/5 border-black/15 text-black'
            }`}>
              <span className={isDark ? 'text-white/80' : 'text-black/80'}>Prefill sample values from Flash Report:</span>
              <button
                type="button"
                onClick={handleAutofillSample}
                className={`px-2.5 py-1 rounded border text-[11px] font-bold cursor-pointer transition-colors ${
                  isDark ? 'bg-white/10 hover:bg-white/20 text-white border-white/20' : 'bg-black/10 hover:bg-black/20 text-black border-black/20'
                }`}
              >
                ⚡ Populate Sample Corridor
              </button>
            </div>

            {/* Row 1: Identification */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  1. Project ID (project_id) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. NH-48-PKG3 or 060100093"
                  value={projectId}
                  onChange={e => setProjectId(e.target.value)}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-black focus:border-black'
                  }`}
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  2. Infrastructure Nomenclature (project_name) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Chenab Superstructure Rail Bridge"
                  value={projectName}
                  onChange={e => setProjectName(e.target.value)}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-black focus:border-black'
                  }`}
                />
              </div>
            </div>

            {/* Row 2: Financial Capital Outlay */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  3. Original Cost (₹ Cr) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="e.g. 4200.00"
                  value={originalCost}
                  onChange={e => setOriginalCost(e.target.value)}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-black focus:border-black'
                  }`}
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  4. Revised Cost (₹ Cr) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="e.g. 4850.00"
                  value={revisedCost}
                  onChange={e => setRevisedCost(e.target.value)}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-black focus:border-black'
                  }`}
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  5. Cumulative Exp. (₹ Cr) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="e.g. 2950.00"
                  value={expenditure}
                  onChange={e => setExpenditure(e.target.value)}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-black focus:border-black'
                  }`}
                />
              </div>
            </div>

            {/* Row 3: Physical Progress and Tokens */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  6. Physical Progress (%) *
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  required
                  placeholder="e.g. 64.5"
                  value={physicalProgress}
                  onChange={e => setPhysicalProgress(e.target.value)}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-black focus:border-black'
                  }`}
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  7. Serial No (s_no)
                </label>
                <input
                  type="number"
                  min="1"
                  value={sNo}
                  onChange={e => setSNo(Number(e.target.value))}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-black focus:border-black'
                  }`}
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  8. Flash Report Page
                </label>
                <input
                  type="number"
                  min="1"
                  value={page}
                  onChange={e => setPage(Number(e.target.value))}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-black focus:border-black'
                  }`}
                />
              </div>
            </div>

            {/* Row 4: Jurisdiction context */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  Ministry / Department
                </label>
                <input
                  type="text"
                  value={ministry}
                  onChange={e => setMinistry(e.target.value)}
                  placeholder="e.g. Ministry of Road Transport & Highways"
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-black focus:border-black'
                  }`}
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  State / Location
                </label>
                <input
                  type="text"
                  value={state}
                  onChange={e => setState(e.target.value)}
                  placeholder="e.g. Maharashtra, Uttar Pradesh"
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-black focus:border-black'
                  }`}
                />
              </div>
            </div>

            {/* Project-Specific DPHIS Alert Threshold */}
            <div className={`p-4 rounded-xl border ${
              isDark ? 'bg-amber-500/10 border-amber-500/30' : 'bg-amber-50/80 border-amber-300'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-bold text-amber-500 dark:text-amber-400 tracking-wider flex items-center gap-1.5 font-display">
                  <span>🔔</span> RISK ALERT THRESHOLD *
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="1"
                    max="100"
                    required
                    value={dphisThreshold}
                    onChange={e => setDphisThreshold(Number(e.target.value))}
                    className={`w-20 px-3 py-1.5 rounded-lg border text-sm font-mono font-bold text-center outline-none ${
                      isDark ? 'bg-black/60 border-amber-500/50 text-amber-300 focus:border-amber-400' : 'bg-white border-amber-400 text-amber-900 focus:border-amber-600'
                    }`}
                  />
                  <span className="text-xs font-mono text-slate-400">/ 100</span>
                </div>
              </div>
              <p className="text-[11.5px] text-[var(--text-secondary)] leading-relaxed">
                Set the DPHIS score at which this project should automatically trigger an alert.
              </p>
              <p className="text-[11px] text-amber-600 dark:text-amber-400/90 font-medium mt-1">
                When this project's DPHIS reaches or crosses this value, an alert will automatically be sent to you and the responsible administrator.
              </p>
            </div>

            {/* Footer Buttons */}
            <div className="pt-4 border-t border-white/10 flex items-center justify-between gap-3">
              <span className="text-[10px] font-mono text-slate-400">
                ⚡ Automatically calculates delay risk &amp; cost trends
              </span>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-xs font-mono cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className={`px-5 py-2 rounded-lg font-mono font-bold text-xs shadow-lg cursor-pointer transition-all disabled:opacity-50 ${
                    isDark ? 'bg-white hover:bg-slate-200 text-black' : 'bg-black hover:bg-zinc-800 text-white'
                  }`}
                >
                  {loading ? 'Saving Project...' : 'Save Project & Calculate Risk →'}
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
