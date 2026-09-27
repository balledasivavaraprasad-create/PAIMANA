import React from 'react';
import GlassCard from '../components/GlassCard';

export default function DataModels() {
  const models = [
    {
      id: 'schedule_risk_1m_v2.1',
      name: 'Schedule Risk Regressor (1-Month Horizon)',
      type: 'LightGBM Gradient Boosting',
      accuracy: '94.2% ROC-AUC',
      lastTrained: '2026-03-15',
      status: 'Active · Production',
      features: 57,
      loss: 'Quantile Loss (α=0.75)'
    },
    {
      id: 'cost_risk_1m_v1.8',
      name: 'Cost Escalation Predictor',
      type: 'XGBoost Robust Regressor',
      accuracy: '91.8% R²',
      lastTrained: '2026-03-12',
      status: 'Active · Production',
      features: 57,
      loss: 'Huber M-Estimator'
    },
    {
      id: 'combined_dphis_engine_v3.0',
      name: 'Composite DPHIS Risk Index Synthesizer',
      type: 'Ensemble Multi-Factor Heuristic',
      accuracy: '96.4% Concordance',
      lastTrained: '2026-03-20',
      status: 'Active · Production',
      features: 57,
      loss: 'Weighted Hysteresis'
    }
  ];

  const dataQualityMetrics = [
    { label: 'Total Tracked Features', value: '57 Features', status: 'Optimal' },
    { label: 'Data Freshness', value: '< 15 mins', status: 'Live Sync' },
    { label: 'Missing Fields Across Portfolio', value: '0.4%', status: 'Within Tolerance' },
    { label: 'GIS & Spatial Coordinates Health', value: '99.8%', status: 'Verified' },
    { label: 'Financial Telemetry Alignment', value: '98.6%', status: 'Audited' },
    { label: 'Model Feature Drift Score', value: '0.04 (Low)', status: 'Stable' },
  ];

  return (
    <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Header */}
      <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white">
              Data Quality &amp; Machine Learning Models
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
              ADMIN ONLY
            </span>
          </div>
          <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
            Telemetry ingestion pipelines, model performance benchmarks, feature drift tracking, and retraining status
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="px-3 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-mono font-bold">
            ✓ Ingestion Engine Healthy
          </span>
        </div>
      </GlassCard>

      {/* Data Quality & Pipeline Health */}
      <div className="space-y-3">
        <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white/70">
          Portfolio Data Quality &amp; Pipeline Telemetry
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
          {dataQualityMetrics.map(m => (
            <div key={m.label} className="oled-solid-card p-4 space-y-1">
              <div className="text-[10px] font-mono uppercase text-white/60 truncate">{m.label}</div>
              <div className="text-base sm:text-lg font-bold font-mono text-white">{m.value}</div>
              <div className="text-[11px] font-mono text-emerald-400 font-semibold">{m.status}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Active Predictive Models */}
      <div className="space-y-3">
        <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white/70">
          Active Machine Learning Models &amp; Manifest
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
          {models.map(m => (
            <div key={m.id} className="oled-solid-card p-5 sm:p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <span className="font-mono text-xs text-white/80 px-2 py-0.5 rounded bg-white/10">{m.id}</span>
                <span className="text-[11px] font-mono text-emerald-400 font-bold">{m.status}</span>
              </div>

              <div>
                <h4 className="font-bold text-base text-white">{m.name}</h4>
                <div className="text-xs text-white/70 font-mono mt-1">{m.type}</div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
                <div className="p-2 rounded bg-black/40 border border-white/10">
                  <div className="text-white/50 text-[10px] uppercase">Benchmark</div>
                  <div className="font-bold text-white mt-0.5">{m.accuracy}</div>
                </div>
                <div className="p-2 rounded bg-black/40 border border-white/10">
                  <div className="text-white/50 text-[10px] uppercase">Features</div>
                  <div className="font-bold text-white mt-0.5">{m.features} cols</div>
                </div>
              </div>

              <div className="text-xs text-white/70 space-y-1 pt-1 border-t border-white/10 font-mono text-[11px]">
                <div>Objective: {m.loss}</div>
                <div>Last Retrained: {m.lastTrained}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Feature Ingestion Status */}
      <GlassCard variant="medium" padding={24} className="space-y-3">
        <h4 className="text-sm sm:text-base font-bold text-white font-display">
          57 Feature Engineering Pipeline Status
        </h4>
        <p className="text-xs sm:text-sm text-white/80 leading-relaxed">
          The InfraBuild AI pipeline ingests 8 standard report attributes from project officers and computes 49 synthetic early-warning features including expenditure disparity ratio, milestone hysteresis coefficients, and seasonal monsoon delay indices.
        </p>
      </GlassCard>
    </div>
  );
}
