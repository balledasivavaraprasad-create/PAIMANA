import React, { useState } from 'react';

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
}

interface CeoPinManagerProps {
  onAddPin: (newPin: ProjectPin) => void;
  onClose: () => void;
}

export function CeoPinManager({ onAddPin, onClose }: CeoPinManagerProps) {
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
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="oled-solid-card w-full max-w-md p-6 space-y-4 shadow-2xl">
        <div className="flex items-center justify-between border-b border-[var(--border-hairline)] pb-3">
          <h3 className="text-base font-bold font-display text-[var(--text-primary)]">
            Institutional Capital Asset Ingestion Protocol
          </h3>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-lg cursor-pointer">
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3 text-xs text-[var(--text-secondary)]">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block mb-1 font-mono-code text-[10px] uppercase text-[var(--text-muted)]">Asset Identification Token</label>
              <input
                type="text"
                value={id}
                onChange={e => setId(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[var(--surface-sunken)] border border-[var(--border-hairline)] text-[var(--text-primary)] font-mono-code outline-none focus:border-[var(--accent)]"
              />
            </div>
            <div>
              <label className="block mb-1 font-mono-code text-[10px] uppercase text-[var(--text-muted)]">Sub-National Jurisdiction</label>
              <select
                value={state}
                onChange={e => setState(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[var(--surface-sunken)] border border-[var(--border-hairline)] text-[var(--text-primary)] outline-none"
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
            <label className="block mb-1 font-mono-code text-[10px] uppercase text-[var(--text-muted)]">Infrastructure Nomenclature</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Western Dedicated Freight Corridor Package 4"
              className="w-full px-3 py-2 rounded-lg bg-[var(--surface-sunken)] border border-[var(--border-hairline)] text-[var(--text-primary)] outline-none focus:border-[var(--accent)]"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block mb-1 font-mono-code text-[10px] uppercase text-[var(--text-muted)]">Risk Classification</label>
              <select
                value={risk}
                onChange={e => setRisk(e.target.value as any)}
                className="w-full px-3 py-2 rounded-lg bg-[var(--surface-sunken)] border border-[var(--border-hairline)] text-[var(--text-primary)] outline-none"
              >
                <option value="critical">Critical Risk Cohort (75+ DPHIS)</option>
                <option value="high">Elevated Variance Tier (50-74)</option>
                <option value="moderate">Moderate Exposure (25-49)</option>
                <option value="low">Nominal Baseline (0-24)</option>
              </select>
            </div>

            <div>
              <label className="block mb-1 font-mono-code text-[10px] uppercase text-[var(--text-muted)]">Calibrated DPHIS Index ({dphis} / 100)</label>
              <input
                type="range"
                min="1"
                max="99"
                value={dphis}
                onChange={e => setDphis(Number(e.target.value))}
                className="w-full mt-2"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block mb-1 font-mono-code text-[10px] uppercase text-[var(--text-muted)]">Sanctioned Capital Outlay</label>
              <input
                type="text"
                value={cost}
                onChange={e => setCost(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[var(--surface-sunken)] border border-[var(--border-hairline)] text-[var(--text-primary)] font-mono-code outline-none"
              />
            </div>

            <div>
              <label className="block mb-1 font-mono-code text-[10px] uppercase text-[var(--text-muted)]">Critical Path Delay (Δt)</label>
              <input
                type="text"
                value={delay}
                onChange={e => setDelay(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[var(--surface-sunken)] border border-[var(--border-hairline)] text-[var(--text-primary)] font-mono-code outline-none"
              />
            </div>
          </div>

          <div className="pt-3 flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl border border-[var(--border-hairline)] text-[var(--text-secondary)] font-semibold text-xs hover:bg-[var(--surface-sunken)] cursor-pointer"
            >
              Abort Protocol
            </button>
            <button
              type="submit"
              className="flex-1 py-2.5 rounded-xl bg-black text-white font-semibold text-xs border border-white/30 shadow-[0_0_12px_rgba(255,255,255,0.22)] hover:bg-zinc-900 hover:border-white/60 cursor-pointer transition-all duration-200"
            >
              Ingest & Commit to Ledger
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CeoPinManager;
