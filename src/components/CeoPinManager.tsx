import React, { useState } from 'react';
import { useTheme } from '../hooks/useTheme';

export interface ProjectPin {
  id: string;
  name: string;
  state: string;
  latPct: number;
  lngPct: number;
  dphis: number;
  risk: 'critical' | 'high' | 'moderate' | 'low';
  cost: string;
  delay: string;
  dphis_threshold?: number;
  threshold_status?: string;
}

interface CeoPinManagerProps {
  onAddPin: (newPin: ProjectPin) => void;
  onClose: () => void;
}

export function CeoPinManager({ onAddPin, onClose }: CeoPinManagerProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const [id, setId] = useState(`P${Math.floor(1000 + Math.random() * 9000)}`);
  const [name, setName] = useState('');
  const [state, setState] = useState('Uttar Pradesh');
  const [dphis, setDphis] = useState(85);
  const [risk, setRisk] = useState<'critical' | 'high' | 'moderate' | 'low'>('critical');
  const [cost, setCost] = useState('₹3,500 Cr');
  const [delay, setDelay] = useState('12 mo');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    onAddPin({
      id,
      name,
      state,
      dphis,
      risk,
      cost,
      delay,
      latPct: 50,
      lngPct: 50,
    });
    onClose();
  };

  return (
    <div className={`fixed inset-0 z-[100000] backdrop-blur-md flex items-center justify-center p-4 animate-fade-in ${
      isDark ? 'bg-black/80' : 'bg-slate-900/60'
    }`}>
      <div 
        role="dialog"
        aria-modal="true"
        aria-label="Add New Project"
        className={`modal-surface w-full max-w-md p-6 space-y-4 rounded-2xl border-2 shadow-2xl transition-all ${
          isDark ? 'bg-[#0B0F17] border-white/20 text-white' : 'bg-white border-slate-300 text-slate-950'
        }`}
      >
        <div className={`flex items-center justify-between border-b pb-3 ${
          isDark ? 'border-white/10' : 'border-slate-200'
        }`}>
          <h3 className={`text-base font-bold font-display ${isDark ? 'text-white' : 'text-slate-950'}`}>
            Add New Project
          </h3>
          <button 
            onClick={onClose} 
            aria-label="Close"
            className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-sm cursor-pointer transition-colors modal-close-btn ${
              isDark ? 'text-white/60 hover:text-white bg-white/5' : 'text-slate-800 hover:text-black bg-slate-200 hover:bg-slate-300 border border-slate-300'
            }`}
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`block mb-1 font-mono-code text-[10px] uppercase font-bold ${
                isDark ? 'text-white/60' : 'text-slate-600'
              }`}>Project ID</label>
              <input
                type="text"
                value={id}
                onChange={e => setId(e.target.value)}
                className={`w-full px-3 py-2 rounded-lg border font-mono-code outline-none ${
                  isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-slate-900 focus:border-slate-900'
                }`}
              />
            </div>
            <div>
              <label className={`block mb-1 font-mono-code text-[10px] uppercase font-bold ${
                isDark ? 'text-white/60' : 'text-slate-600'
              }`}>State / Location</label>
              <select
                value={state}
                onChange={e => setState(e.target.value)}
                className={`w-full px-3 py-2 rounded-lg border outline-none cursor-pointer ${
                  isDark ? 'bg-[#0E1524] border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-slate-900 focus:border-slate-900'
                }`}
              >
                <option value="Uttar Pradesh">Uttar Pradesh</option>
                <option value="Maharashtra">Maharashtra</option>
                <option value="Tamil Nadu">Tamil Nadu</option>
                <option value="Rajasthan">Rajasthan</option>
                <option value="Gujarat">Gujarat</option>
                <option value="Bihar">Bihar</option>
                <option value="West Bengal">West Bengal</option>
                <option value="Andhra Pradesh">Andhra Pradesh</option>
              </select>
            </div>
          </div>

          <div>
            <label className={`block mb-1 font-mono-code text-[10px] uppercase font-bold ${
              isDark ? 'text-white/60' : 'text-slate-600'
            }`}>Project Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Western Dedicated Freight Corridor Package 4"
              className={`w-full px-3 py-2 rounded-lg border outline-none ${
                isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-slate-900 focus:border-slate-900'
              }`}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`block mb-1 font-mono-code text-[10px] uppercase font-bold ${
                isDark ? 'text-white/60' : 'text-slate-600'
              }`}>Risk Level</label>
              <select
                value={risk}
                onChange={e => setRisk(e.target.value as any)}
                className={`w-full px-3 py-2 rounded-lg border outline-none cursor-pointer ${
                  isDark ? 'bg-[#0E1524] border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-slate-900 focus:border-slate-900'
                }`}
              >
                <option value="critical">Critical Risk (75–100)</option>
                <option value="high">High Risk (50–74)</option>
                <option value="moderate">Moderate Risk (25–49)</option>
                <option value="low">Low Risk (0–24)</option>
              </select>
            </div>

            <div>
              <label className={`block mb-1 font-mono-code text-[10px] uppercase font-bold ${
                isDark ? 'text-white/60' : 'text-slate-600'
              }`}>Risk Score ({dphis} / 100)</label>
              <input
                type="range"
                min="1"
                max="99"
                value={dphis}
                onChange={e => setDphis(Number(e.target.value))}
                className="w-full mt-2 accent-amber-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`block mb-1 font-mono-code text-[10px] uppercase font-bold ${
                isDark ? 'text-white/60' : 'text-slate-600'
              }`}>Approved Cost</label>
              <input
                type="text"
                value={cost}
                onChange={e => setCost(e.target.value)}
                className={`w-full px-3 py-2 rounded-lg border font-mono-code outline-none ${
                  isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-slate-900 focus:border-slate-900'
                }`}
              />
            </div>

            <div>
              <label className={`block mb-1 font-mono-code text-[10px] uppercase font-bold ${
                isDark ? 'text-white/60' : 'text-slate-600'
              }`}>Estimated Delay</label>
              <input
                type="text"
                value={delay}
                onChange={e => setDelay(e.target.value)}
                className={`w-full px-3 py-2 rounded-lg border font-mono-code outline-none ${
                  isDark ? 'bg-black/50 border-white/20 text-white focus:border-white' : 'bg-white border-slate-300 text-slate-900 focus:border-slate-900'
                }`}
              />
            </div>
          </div>

          <div className={`pt-3 border-t flex items-center gap-3 ${isDark ? 'border-white/10' : 'border-slate-200'}`}>
            <button
              type="button"
              onClick={onClose}
              className={`flex-1 py-2.5 rounded-xl border font-semibold text-xs transition-colors cursor-pointer ${
                isDark ? 'border-white/20 text-white/80 hover:bg-white/10' : 'border-slate-300 text-slate-700 hover:bg-slate-100'
              }`}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={`flex-1 py-2.5 rounded-xl font-semibold text-xs transition-all duration-200 cursor-pointer shadow-md ${
                isDark 
                  ? 'bg-white text-black hover:bg-slate-200' 
                  : 'bg-slate-900 text-white hover:bg-black shadow-slate-300'
              }`}
            >
              Save Project
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CeoPinManager;
