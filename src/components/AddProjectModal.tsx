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
        username: currentUser?.username
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
              <span className="w-2.5 h-2.5 rounded-full bg-sky-400 animate-pulse" />
              <h2 className="text-xl font-serif font-bold tracking-wide">
                Ingest Infrastructure Asset
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Standard Flash Report Baseline (8 Columns) → Automated Gemini Flash 2.5 (57 Features) → LightGBM DPHIS Scoring
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
              <div className="w-16 h-16 rounded-full border-4 border-sky-400/20 border-t-sky-400 animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center font-mono font-bold text-sky-400 text-xs">
                AI
              </div>
            </div>
            <div className="space-y-1">
              <h4 className="font-mono font-bold text-sm text-sky-400 animate-pulse">
                {statusStep || 'Processing Ingestion Pipeline...'}
              </h4>
              <p className="text-[11px] text-slate-400 font-mono">
                Gemini Flash 2.5 is synthesizing 57 domain features for LightGBM inference
              </p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Autofill helper */}
            <div className="flex justify-between items-center bg-sky-500/10 border border-sky-500/20 p-2.5 rounded-lg text-xs font-mono">
              <span className="text-sky-300">Prefill sample values from Flash Report:</span>
              <button
                type="button"
                onClick={handleAutofillSample}
                className="px-2.5 py-1 rounded bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-400/40 text-[11px] font-bold cursor-pointer"
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
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-sky-400' : 'bg-white border-slate-300 text-black focus:border-sky-600'
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
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-sky-400' : 'bg-white border-slate-300 text-black focus:border-sky-600'
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
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-sky-400' : 'bg-white border-slate-300 text-black focus:border-sky-600'
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
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-sky-400' : 'bg-white border-slate-300 text-black focus:border-sky-600'
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
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-sky-400' : 'bg-white border-slate-300 text-black focus:border-sky-600'
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
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-sky-400' : 'bg-white border-slate-300 text-black focus:border-sky-600'
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
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-sky-400' : 'bg-white border-slate-300 text-black focus:border-sky-600'
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
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-sky-400' : 'bg-white border-slate-300 text-black focus:border-sky-600'
                  }`}
                />
              </div>
            </div>

            {/* Row 4: Jurisdiction context */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  Jurisdiction Ministry
                </label>
                <input
                  type="text"
                  value={ministry}
                  onChange={e => setMinistry(e.target.value)}
                  placeholder="e.g. Ministry of Road Transport & Highways"
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-sky-400' : 'bg-white border-slate-300 text-black focus:border-sky-600'
                  }`}
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono font-semibold text-slate-300 mb-1">
                  Jurisdiction State / Territory
                </label>
                <input
                  type="text"
                  value={state}
                  onChange={e => setState(e.target.value)}
                  placeholder="e.g. Maharashtra, Uttar Pradesh"
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono outline-none ${
                    isDark ? 'bg-black/50 border-white/20 text-white focus:border-sky-400' : 'bg-white border-slate-300 text-black focus:border-sky-600'
                  }`}
                />
              </div>
            </div>

            {/* Footer Buttons */}
            <div className="pt-4 border-t border-white/10 flex items-center justify-between gap-3">
              <span className="text-[10px] font-mono text-slate-400">
                ⚡ Automatically engineers 57 columns via Gemini Flash 2.5
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
                  className="px-5 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-black font-mono font-bold text-xs shadow-lg shadow-sky-500/20 cursor-pointer transition-all disabled:opacity-50"
                >
                  {loading ? 'Ingesting Asset...' : 'Ingest & Compute DPHIS →'}
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
