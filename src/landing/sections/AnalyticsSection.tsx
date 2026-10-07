import { useId } from 'react';
import { useInView } from '../motion';

/**
 * Portfolio analytics preview.
 *
 * These are deterministic, data-shaped miniatures that demonstrate what the
 * authenticated Analytics surface contains. They are not live figures and are
 * labelled as conceptual. Values are drawn from a fixed matrix so the visuals
 * never change between renders.
 */

const TREND_SERIES = {
  observed: [42, 45, 44, 51, 54, 58, 63, 61, 67, 71, 69, 74],
  predicted: [42, 45, 44, 51, 54, 58, 63, 66, 70, 73, 76, 79],
};

const RISK_MATRIX = [
  { cost: 18, schedule: 22, risk: 12 },
  { cost: 32, schedule: 28, risk: 26 },
  { cost: 44, schedule: 38, risk: 41 },
  { cost: 28, schedule: 55, risk: 47 },
  { cost: 58, schedule: 52, risk: 61 },
  { cost: 66, schedule: 71, risk: 74 },
  { cost: 74, schedule: 62, risk: 68 },
  { cost: 38, schedule: 24, risk: 22 },
  { cost: 52, schedule: 46, risk: 38 },
  { cost: 22, schedule: 66, risk: 58 },
];

const EVENT_HEATMAP = [
  [1, 2, 1, 3, 4, 2, 1, 1, 0, 2, 3, 4],
  [0, 1, 2, 2, 5, 3, 2, 1, 1, 2, 4, 3],
  [2, 1, 3, 4, 6, 5, 3, 2, 1, 3, 5, 6],
  [1, 2, 2, 3, 4, 6, 4, 3, 2, 2, 3, 5],
];

const GEO_POINTS = [
  { x: 46, y: 62, risk: 74 },
  { x: 52, y: 48, risk: 61 },
  { x: 38, y: 55, risk: 45 },
  { x: 60, y: 40, risk: 52 },
  { x: 44, y: 38, risk: 33 },
  { x: 66, y: 58, risk: 58 },
  { x: 34, y: 66, risk: 41 },
  { x: 56, y: 70, risk: 49 },
];

const DEVIATION_BARS = [
  { label: 'PRJ-04', value: 26 },
  { label: 'PRJ-17', value: 19 },
  { label: 'PRJ-09', value: 14 },
  { label: 'PRJ-22', value: 11 },
  { label: 'PRJ-02', value: 6 },
];

/**
 * Two additional panels keep the grid balanced at six data-backed visuals and
 * cover the cohort-trajectory comparison and the monitoring-health surface.
 */

const DEVIATION_TREND = [
  { cycle: 108, deviation: 2 },
  { cycle: 109, deviation: 4 },
  { cycle: 110, deviation: 3 },
  { cycle: 111, deviation: 9 },
  { cycle: 112, deviation: 15 },
  { cycle: 113, deviation: 18 },
  { cycle: 114, deviation: 21 },
  { cycle: 115, deviation: 26 },
];

const MONITORING_HEALTH = [
  { label: 'Ingest', value: 98, tone: 'healthy' },
  { label: 'Snapshot', value: 94, tone: 'healthy' },
  { label: 'Prediction', value: 91, tone: 'healthy' },
  { label: 'Peer service', value: 78, tone: 'attention' },
  { label: 'Investigation', value: 84, tone: 'neutral' },
  { label: 'Automation', value: 97, tone: 'healthy' },
];

const OUTCOME_BARS = [
  { label: 'Improved', value: 34, tone: 'healthy' },
  { label: 'Stable', value: 41, tone: 'neutral' },
  { label: 'Deteriorated', value: 19, tone: 'attention' },
  { label: 'Unknown', value: 6, tone: 'muted' },
];

function panelPath(values: number[], width: number, height: number, pad: number) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return values
    .map((value, index) => {
      const x = pad + (index / (values.length - 1)) * (width - pad * 2);
      const y = pad + (1 - (value - min) / span) * (height - pad * 2);
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');
}

export default function AnalyticsSection() {
  const { ref, isInView } = useInView<HTMLElement>();
  const headingId = useId();

  return (
    <section className="lp-section lp-analytics" id="analytics" ref={ref} aria-labelledby={headingId}>
      <div className="landing-container">
        <div className="lp-section__header">
          <span className="lp-section__eyebrow">Analytics</span>
          <h2 className="lp-section__title" id={headingId}>
            See the portfolio, not just the project.
          </h2>
          <p className="lp-section__description">
            Project-level signals do not aggregate neatly on their own. The portfolio surface exists to
            show where deterioration is concentrated, which cohorts are moving together, and whether
            previous interventions actually produced a measured change.
          </p>
        </div>

        <p className="lp-conceptual-note" role="note">
          <span className="lp-conceptual-note-tag">Conceptual preview</span>
          Charts below illustrate the shape of the authenticated analytics surface. Figures are
          illustrative placeholders, not live portfolio data.
        </p>

        <div className="lp-analytics__grid" data-visible={isInView ? 'true' : 'false'}>
          <ChartFrame
            title="Portfolio risk trend"
            caption="Observed composite risk against model projection over twelve monitoring cycles."
          >
            <TrendChart />
          </ChartFrame>

          <ChartFrame
            title="Cost vs schedule risk"
            caption="Each point is one project, positioned by cost risk against schedule risk."
          >
            <RiskMatrix />
          </ChartFrame>

          <ChartFrame
            title="Event heatmap"
            caption="Detected event volume by month and category."
          >
            <EventHeatmap />
          </ChartFrame>

          <ChartFrame
            title="Geographic risk concentration"
            caption="Portfolio risk aggregated by region. Boundaries are indicative only."
          >
            <GeoRisk />
          </ChartFrame>

          <ChartFrame
            title="Peer deviation"
            caption="Largest gap between project DPHIS and its peer cohort median."
          >
            <DeviationBars />
          </ChartFrame>

          <ChartFrame
            title="Intervention outcomes"
            caption="Measured result of approved interventions after follow-up monitoring."
          >
            <OutcomeBars />
          </ChartFrame>

          <ChartFrame
            title="Deviation trajectory"
            caption="Peer deviation widening across the last eight monitoring cycles."
          >
            <DeviationTrend />
          </ChartFrame>

          <ChartFrame
            title="Monitoring health"
            caption="Component availability. Degraded services stay visible rather than blanking the page."
          >
            <MonitoringHealth />
          </ChartFrame>
        </div>
      </div>
    </section>
  );
}

function ChartFrame({
  title,
  caption,
  children,
}: {
  title: string;
  caption: string;
  children: React.ReactNode;
}) {
  return (
    <figure className="lp-chart">
      <figcaption className="lp-chart__header">
        <span className="lp-chart__title">{title}</span>
        <span className="lp-chart__badge">Preview</span>
      </figcaption>
      <div className="lp-chart__body">{children}</div>
      <p className="lp-chart__caption">{caption}</p>
    </figure>
  );
}

function TrendChart() {
  const w = 300;
  const h = 140;
  return (
    <svg className="lp-chart__svg" viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Line chart comparing observed portfolio risk with predicted risk; both trend upward across twelve cycles.">
      <g className="lp-chart__grid">
        {[0, 1, 2, 3].map((i) => (
          <line key={i} x1="8" y1={20 + i * 32} x2={w - 8} y2={20 + i * 32} />
        ))}
      </g>
      <path
        className="lp-chart__line lp-chart__line--observed"
        d={panelPath(TREND_SERIES.observed, w, h, 12)}
      />
      <path
        className="lp-chart__line lp-chart__line--predicted"
        d={panelPath(TREND_SERIES.predicted, w, h, 12)}
      />
      <g className="lp-chart__legend">
        <text x="12" y={h - 2}>Observed</text>
        <text x="74" y={h - 2}>Predicted</text>
      </g>
    </svg>
  );
}

function RiskMatrix() {
  return (
    <svg className="lp-chart__svg" viewBox="0 0 300 140" role="img" aria-label="Scatter plot of ten projects by cost risk against schedule risk, with the highest-risk project in the upper right.">
      <g className="lp-chart__grid">
        <line x1="150" y1="10" x2="150" y2="124" />
        <line x1="14" y1="67" x2="286" y2="67" />
      </g>
      {RISK_MATRIX.map((point, i) => {
        const x = 14 + (point.cost / 100) * 272;
        const y = 124 - (point.schedule / 100) * 114;
        const isExtreme = point.risk >= 68;
        return (
          <circle
            key={i}
            cx={x}
            cy={y}
            r={isExtreme ? 4.5 : 3}
            className={isExtreme ? 'lp-chart__point lp-chart__point--critical' : 'lp-chart__point'}
          />
        );
      })}
      <text x="286" y="136" textAnchor="end" className="lp-chart__axis-label">
        Cost risk →
      </text>
      <text x="16" y="16" className="lp-chart__axis-label">
        Schedule risk
      </text>
    </svg>
  );
}

function EventHeatmap() {
  const max = 6;
  const cols = EVENT_HEATMAP[0].length;
  const cell = 300 / cols;
  return (
    <svg className="lp-chart__svg" viewBox="0 0 300 140" role="img" aria-label="Heatmap of detected event volume by month and category, peaking in the middle months.">
      {EVENT_HEATMAP.map((row, r) =>
        row.map((value, c) => (
          <rect
            key={`${r}-${c}`}
            x={c * cell}
            y={r * 26}
            width={cell - 2}
            height={22}
            rx="2"
            className="lp-chart__cell"
            opacity={0.15 + (value / max) * 0.85}
          />
        )),
      )}
      <text x="4" y="130" className="lp-chart__axis-label">
        Jan → Dec, four event categories
      </text>
    </svg>
  );
}

function GeoRisk() {
  return (
    <svg className="lp-chart__svg" viewBox="0 0 300 140" role="img" aria-label="Stylised regional map with eight circular risk markers, largest in the south-central region.">
      <path
        className="lp-chart__outline"
        d="M40 26 C 86 10, 150 14, 196 30 C 246 46, 268 74, 250 106 C 226 132, 150 134, 96 122 C 52 112, 20 84, 30 52 Z"
      />
      {GEO_POINTS.map((point, i) => {
        const x = 30 + (point.x / 100) * 230;
        const y = 20 + (point.y / 100) * 100;
        return (
          <circle
            key={i}
            cx={x}
            cy={y}
            r={3 + (point.risk / 100) * 8}
            className={
              point.risk >= 60
                ? 'lp-chart__point lp-chart__point--critical'
                : point.risk >= 45
                  ? 'lp-chart__point lp-chart__point--attention'
                  : 'lp-chart__point'
            }
          />
        );
      })}
      <text x="4" y="130" className="lp-chart__axis-label">
        Indicative boundaries — not administrative regions
      </text>
    </svg>
  );
}

function DeviationTrend() {
  const w = 300;
  const h = 140;
  return (
    <svg className="lp-chart__svg" viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Line chart of peer deviation rising from 2 at cycle 108 to 26 at cycle 115, with the sharpest increase in the final three cycles.">
      <g className="lp-chart__grid">
        {[0, 1, 2, 3].map((i) => (
          <line key={i} x1="8" y1={20 + i * 32} x2={w - 8} y2={20 + i * 32} />
        ))}
      </g>
      <path className="lp-chart__line lp-chart__line--observed" d={panelPath(
        DEVIATION_TREND.map((point) => point.deviation),
        w,
        h,
        12,
      )} />
      {DEVIATION_TREND.map((point, index) => {
        const min = 2;
        const max = 26;
        const x = 12 + (index / (DEVIATION_TREND.length - 1)) * (w - 24);
        const y = 12 + (1 - (point.deviation - min) / (max - min)) * (h - 24);
        return <circle key={point.cycle} cx={x} cy={y} r="2" className="lp-chart__point lp-chart__point--critical" />;
      })}
      <text x="12" y={h - 2} className="lp-chart__axis-label">
        Cycle {DEVIATION_TREND[0].cycle} → {DEVIATION_TREND[DEVIATION_TREND.length - 1].cycle}
      </text>
    </svg>
  );
}

function MonitoringHealth() {
  return (
    <div className="lp-chart__bars">
      {MONITORING_HEALTH.map((item) => (
        <div key={item.label} className="lp-chart__bar-row" style={{ gridTemplateColumns: '7rem minmax(0,1fr) 2.5rem' }}>
          <span className="lp-chart__bar-label">{item.label}</span>
          <span className="lp-chart__bar-track">
            <span
              className={`lp-chart__bar-fill lp-chart__bar-fill--${item.tone}`}
              style={{ width: `${item.value}%` }}
            />
          </span>
          <span className="lp-chart__bar-value">{item.value}%</span>
        </div>
      ))}
      <p className="lp-chart__note">A degraded component surfaces a warning, not a blank panel.</p>
    </div>
  );
}

function DeviationBars() {
  const max = Math.max(...DEVIATION_BARS.map((d) => d.value));
  return (
    <div className="lp-chart__bars">
      {DEVIATION_BARS.map((bar) => (
        <div key={bar.label} className="lp-chart__bar-row">
          <span className="lp-chart__bar-label">{bar.label}</span>
          <span className="lp-chart__bar-track">
            <span
              className="lp-chart__bar-fill lp-chart__bar-fill--risk"
              style={{ width: `${(bar.value / max) * 100}%` }}
            />
          </span>
          <span className="lp-chart__bar-value">+{bar.value}</span>
        </div>
      ))}
    </div>
  );
}

function OutcomeBars() {
  const total = OUTCOME_BARS.reduce((sum, bar) => sum + bar.value, 0);
  return (
    <div className="lp-chart__bars">
      {OUTCOME_BARS.map((bar) => (
        <div key={bar.label} className="lp-chart__bar-row">
          <span className="lp-chart__bar-label">{bar.label}</span>
          <span className="lp-chart__bar-track">
            <span
              className={`lp-chart__bar-fill lp-chart__bar-fill--${bar.tone}`}
              style={{ width: `${(bar.value / total) * 100}%` }}
            />
          </span>
          <span className="lp-chart__bar-value">{bar.value}%</span>
        </div>
      ))}
      <p className="lp-chart__note">Measured after follow-up monitoring. Unknown stays visible.</p>
    </div>
  );
}