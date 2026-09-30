export interface PlotlyThemeOptions {
  title?: string;
  xAxisTitle?: string;
  yAxisTitle?: string;
  height?: number;
  showLegend?: boolean;
  barmode?: 'stack' | 'group' | 'overlay' | 'relative';
  margin?: { l?: number; r?: number; t?: number; b?: number; pad?: number };
}

export function getPlotlyTheme(isDark: boolean, options: PlotlyThemeOptions = {}): any {
  const fontColor = isDark ? '#E2E8F0' : '#1E293B';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)';
  const zeroLineColor = isDark ? 'rgba(255, 255, 255, 0.16)' : 'rgba(0, 0, 0, 0.16)';
  const hoverBg = isDark ? '#0F172A' : '#FFFFFF';
  const hoverBorder = isDark ? '#334155' : '#CBD5E1';

  return {
    title: options.title ? {
      text: options.title,
      font: { family: 'Inter, system-ui, sans-serif', size: 14, color: fontColor, weight: 600 },
      x: 0.02,
      xanchor: 'left',
    } : undefined,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: {
      family: 'Inter, system-ui, sans-serif',
      size: 11,
      color: fontColor,
    },
    autosize: true,
    height: options.height || 320,
    margin: options.margin || { l: 45, r: 25, t: options.title ? 35 : 20, b: 40, pad: 4 },
    showlegend: options.showLegend ?? true,
    legend: {
      orientation: 'h',
      x: 0,
      y: 1.12,
      font: { color: fontColor, size: 10 },
      bgcolor: 'transparent',
    },
    barmode: options.barmode,
    hoverlabel: {
      bgcolor: hoverBg,
      bordercolor: hoverBorder,
      font: { family: 'Inter, monospace, sans-serif', size: 11, color: fontColor },
    },
    xaxis: {
      title: options.xAxisTitle ? { text: options.xAxisTitle, font: { size: 11, color: fontColor } } : undefined,
      color: fontColor,
      gridcolor: gridColor,
      zerolinecolor: zeroLineColor,
      tickfont: { size: 10, color: fontColor },
    },
    yaxis: {
      title: options.yAxisTitle ? { text: options.yAxisTitle, font: { size: 11, color: fontColor } } : undefined,
      color: fontColor,
      gridcolor: gridColor,
      zerolinecolor: zeroLineColor,
      tickfont: { size: 10, color: fontColor },
    },
  };
}

export const CHART_COLORS = {
  blue: '#3B82F6',
  green: '#10B981',
  amber: '#F59E0B',
  red: '#EF4444',
  purple: '#8B5CF6',
  cyan: '#06B6D4',
  rose: '#F43F5E',
  slate: '#64748B',
};
