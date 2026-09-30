import React, { useEffect, useRef, useState } from 'react';

interface PlotlyChartProps {
  data: any[];
  layout: any;
  config?: any;
  className?: string;
  onPlotClick?: (eventData: any) => void;
  style?: React.CSSProperties;
}

let cachedPlotly: any = null;

export default function PlotlyChart({
  data,
  layout,
  config = { responsive: true, displayModeBar: false },
  className = '',
  onPlotClick,
  style
}: PlotlyChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [plotlyLoaded, setPlotlyLoaded] = useState<boolean>(!!cachedPlotly);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    if (!cachedPlotly) {
      import('plotly.js-dist-min')
        .then((mod) => {
          if (isMounted) {
            cachedPlotly = mod.default || mod;
            setPlotlyLoaded(true);
          }
        })
        .catch((err) => {
          if (isMounted) {
            console.error('Error loading Plotly bundle:', err);
            setError('Failed to load chart engine');
          }
        });
    } else {
      setPlotlyLoaded(true);
    }
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!plotlyLoaded || !cachedPlotly || !containerRef.current) return;

    const el = containerRef.current;
    const finalConfig = {
      responsive: true,
      displayModeBar: false,
      ...config,
    };

    try {
      cachedPlotly.react(el, data, layout, finalConfig).then(() => {
        if (onPlotClick && (el as any).on) {
          (el as any).removeAllListeners?.('plotly_click');
          (el as any).on('plotly_click', (d: any) => {
            onPlotClick(d);
          });
        }
      });
    } catch (e) {
      console.warn('Plotly render error:', e);
    }

    const handleResize = () => {
      if (el && cachedPlotly?.Plots?.resize) {
        cachedPlotly.Plots.resize(el);
      }
    };

    window.addEventListener('resize', handleResize);

    const resizeObserver = new ResizeObserver(() => {
      handleResize();
    });
    resizeObserver.observe(el);

    return () => {
      window.removeEventListener('resize', handleResize);
      resizeObserver.disconnect();
      if (el && cachedPlotly?.purge) {
        cachedPlotly.purge(el);
      }
    };
  }, [plotlyLoaded, data, layout, config, onPlotClick]);

  if (error) {
    return (
      <div className={`flex items-center justify-center p-6 text-xs text-rose-400 font-mono-code ${className}`} style={style}>
        {error}
      </div>
    );
  }

  return (
    <div className={`relative w-full ${className}`} style={style}>
      {!plotlyLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/5 backdrop-blur-sm rounded-xl">
          <div className="flex items-center gap-2 text-xs font-mono-code opacity-70">
            <span className="w-3.5 h-3.5 rounded-full border-2 border-current border-t-transparent animate-spin" />
            <span>Rendering visualization...</span>
          </div>
        </div>
      )}
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
}
