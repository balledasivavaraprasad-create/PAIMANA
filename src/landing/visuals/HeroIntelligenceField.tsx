import { useCallback, useEffect, useRef } from 'react';
import { useLandingTheme } from '../components/ThemeContext';
import { useReducedMotion } from '../motion';
import { createIntersectionObserver } from '../motion/env';

/**
 * Hero intelligence field.
 *
 * Concept (per 04_LANDING_PAGE_SPEC.md): an abstract analytical instrument —
 * not an architecture diagram. A project field where one node leaves the
 * expected band and the system gathers evidence around it.
 *
 * Story beats, in order:
 *   NORMAL → STATE CHANGE → RISK SIGNAL → PEER DEVIATION → INVESTIGATION
 *
 * Performance notes:
 *  - A single rAF loop drives all drawing. State is held in refs, so pointer
 *    movement never re-creates the loop or triggers a React re-render.
 *  - When reduced motion is preferred, exactly one frame is painted (the
 *    settled end state) and the loop never starts. This is the required
 *    static equivalent.
 *  - The loop pauses entirely when the canvas scrolls out of view.
 *  - No layout properties are animated; only canvas draw calls.
 */

type NodeKind = 'project' | 'peer' | 'evidence' | 'evidence-alt' | 'target' | 'investigation';
type LinkKind = 'trajectory' | 'peer' | 'signal' | 'investigation';

interface FieldNode {
  id: string;
  x: number;
  y: number;
  kind: NodeKind;
  label?: string;
}

interface FieldLink {
  from: string;
  to: string;
  kind: LinkKind;
  /** Minimum story beat index before this link is revealed. */
  appearsAt: number;
}

const STORY_BEATS = 5;

/** Phase index used for the settled / static frame. */
const SETTLED_PHASE = STORY_BEATS - 1;

const NODES: FieldNode[] = [
  { id: 'p1', x: 14, y: 26, kind: 'project', label: 'PRJ-01' },
  { id: 'p2', x: 27, y: 63, kind: 'project', label: 'PRJ-07' },
  { id: 'p3', x: 76, y: 22, kind: 'project', label: 'PRJ-12' },
  { id: 'p4', x: 87, y: 58, kind: 'project', label: 'PRJ-19' },
  { id: 'p5', x: 63, y: 82, kind: 'project', label: 'PRJ-23' },
  { id: 'target', x: 42, y: 44, kind: 'target', label: 'TARGET' },

  { id: 'peer1', x: 22, y: 80, kind: 'peer' },
  { id: 'peer2', x: 8, y: 47, kind: 'peer' },
  { id: 'peer3', x: 33, y: 11, kind: 'peer' },
  { id: 'peer4', x: 55, y: 20, kind: 'peer' },

  { id: 'ev-history', x: 60, y: 38, kind: 'evidence', label: 'HISTORY' },
  { id: 'ev-finance', x: 52, y: 66, kind: 'evidence-alt', label: 'FINANCE' },

  { id: 'investigation', x: 74, y: 44, kind: 'investigation', label: 'INVESTIGATE' },
];

const LINKS: FieldLink[] = [
  { from: 'target', to: 'peer1', kind: 'peer', appearsAt: 3 },
  { from: 'target', to: 'peer2', kind: 'peer', appearsAt: 3 },
  { from: 'target', to: 'peer3', kind: 'peer', appearsAt: 3 },
  { from: 'target', to: 'peer4', kind: 'peer', appearsAt: 3 },

  { from: 'target', to: 'ev-history', kind: 'signal', appearsAt: 2 },
  { from: 'target', to: 'ev-finance', kind: 'signal', appearsAt: 2 },

  { from: 'ev-history', to: 'investigation', kind: 'investigation', appearsAt: 4 },
  { from: 'ev-finance', to: 'investigation', kind: 'investigation', appearsAt: 4 },

  { from: 'p1', to: 'target', kind: 'trajectory', appearsAt: 0 },
  { from: 'p2', to: 'target', kind: 'trajectory', appearsAt: 0 },
  { from: 'p3', to: 'target', kind: 'trajectory', appearsAt: 0 },
  { from: 'p4', to: 'target', kind: 'trajectory', appearsAt: 0 },
  { from: 'p5', to: 'target', kind: 'trajectory', appearsAt: 0 },
];

/** Node kinds only exist from this beat onward. */
const NODES_APPEAR_AT = 0;
/** Target node crosses the risk boundary at this beat. */
const RISK_BEAT = 2;
/** Peer cohort responds at this beat. */
const PEER_BEAT = 3;
/** Investigation activates at this beat. */
const INVESTIGATION_BEAT = 4;

const BEAT_LABELS = [
  'PROJECT FIELD OBSERVED',
  'STATE CHANGE DETECTED',
  'RISK SIGNAL RAISED',
  'PEER DEVIATION MEASURED',
  'INVESTIGATION ACTIVE',
];

interface Palette {
  grid: string;
  linkIdle: string;
  project: string;
  target: string;
  risk: string;
  peer: string;
  evidence: string;
  investigation: string;
  label: string;
  boundary: string;
  wash: string;
}

function readPalette(element: HTMLElement): Palette {
  const styles = getComputedStyle(element);
  const read = (name: string, fallback: string) => {
    const value = styles.getPropertyValue(name).trim();
    return value || fallback;
  };

  return {
    grid: read('--lp-border-subtle', 'rgba(148,163,184,0.07)'),
    linkIdle: read('--lp-neutral', '#94A3B8'),
    project: read('--lp-informational', '#60A5FA'),
    target: read('--lp-accent', '#38BDF8'),
    risk: read('--lp-high-risk', '#FB923C'),
    peer: read('--lp-neutral', '#94A3B8'),
    evidence: read('--lp-attention', '#FBBF24'),
    investigation: read('--lp-agentic', '#A78BFA'),
    label: read('--lp-text-muted', '#94A3B8'),
    boundary: read('--lp-high-risk', '#FB923C'),
    wash: read('--lp-bg-inset', '#0D1320'),
  };
}

function withAlpha(color: string, alpha: number): string {
  const trimmed = color.trim();

  // Support the hex forms used by the token set as well as rgb()/rgba().
  if (trimmed.startsWith('#')) {
    const hex = trimmed.slice(1);
    const full =
      hex.length === 3
        ? hex
            .split('')
            .map((c) => c + c)
            .join('')
        : hex;
    const r = parseInt(full.slice(0, 2), 16);
    const g = parseInt(full.slice(2, 4), 16);
    const b = parseInt(full.slice(4, 6), 16);
    if (Number.isNaN(r) || Number.isNaN(g) || Number.isNaN(b)) {
      return `rgba(148,163,184,${alpha})`;
    }
    return `rgba(${r},${g},${b},${alpha})`;
  }

  const match = trimmed.match(/rgba?\(([^)]+)\)/);
  if (match) {
    const [r, g, b] = match[1].split(',').map((p) => p.trim());
    return `rgba(${r},${g},${b},${alpha})`;
  }

  return `rgba(148,163,184,${alpha})`;
}

export default function HeroIntelligenceField() {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const reducedMotion = useReducedMotion();
  const { theme } = useLandingTheme();

  // Animation state lives in refs so pointer input and the story clock never
  // trigger React re-renders or restart the animation loop.
  const phaseRef = useRef(reducedMotion ? SETTLED_PHASE : 0);
  const pointerRef = useRef<{ x: number; y: number } | null>(null);
  const lastFrameRef = useRef<number>(0);

  const paint = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = container.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    // Cap DPR: a 3x retina buffer buys nothing on a 1px-line drawing.
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const pixelWidth = Math.round(rect.width * dpr);
    const pixelHeight = Math.round(rect.height * dpr);

    if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const w = rect.width;
    const h = rect.height;
    const palette = readPalette(container);
    const phase = phaseRef.current;

    // Pointer proximity is expressed in viewBox percentage space.
    const pointer = pointerRef.current;
    const px = pointer ? (pointer.x / 100) * w : null;
    const py = pointer ? (pointer.y / 100) * h : null;
    const proximity = (x: number, y: number, radius: number) => {
      if (px === null || py === null) return 0;
      const distance = Math.hypot(px - x, py - y);
      if (distance > radius) return 0;
      return 1 - distance / radius;
    };

    ctx.clearRect(0, 0, w, h);

    // ── Infrastructure field grid ──
    const gridSize = Math.max(28, Math.round(w / 14));
    ctx.strokeStyle = palette.grid;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = gridSize; x < w; x += gridSize) {
      ctx.moveTo(Math.round(x) + 0.5, 0);
      ctx.lineTo(Math.round(x) + 0.5, h);
    }
    for (let y = gridSize; y < h; y += gridSize) {
      ctx.moveTo(0, Math.round(y) + 0.5);
      ctx.lineTo(w, Math.round(y) + 0.5);
    }
    ctx.stroke();

    const toX = (n: FieldNode) => (n.x / 100) * w;
    const toY = (n: FieldNode) => (n.y / 100) * h;
    const nodeById = new Map(NODES.map((n) => [n.id, n]));

    // ── Expected-progress band (peer-informed corridor) ──
    if (phase >= 1) {
      const bandTop = h * 0.2;
      const bandHeight = h * 0.34;
      ctx.strokeStyle = withAlpha(palette.grid, 0.9);
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 6]);
      ctx.strokeRect(w * 0.04, bandTop, w * 0.92, bandHeight);
      ctx.setLineDash([]);
    }

    // ── Risk boundary: target crosses it at RISK_BEAT ──
    if (phase >= RISK_BEAT) {
      const boundaryX = Math.round(w * 0.56) + 0.5;

      const wash = ctx.createLinearGradient(boundaryX - w * 0.12, 0, boundaryX, 0);
      wash.addColorStop(0, withAlpha(palette.boundary, 0));
      wash.addColorStop(1, withAlpha(palette.boundary, 0.09));
      ctx.fillStyle = wash;
      ctx.fillRect(boundaryX - w * 0.12, 0, w * 0.12, h);

      ctx.strokeStyle = withAlpha(palette.boundary, 0.32);
      ctx.lineWidth = 1;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(boundaryX, 0);
      ctx.lineTo(boundaryX, h);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.font = '9px var(--lp-font-mono, monospace)';
      ctx.fillStyle = withAlpha(palette.boundary, 0.7);
      ctx.textAlign = 'left';
      ctx.fillText('RISK BOUNDARY', boundaryX + 6, 14);
    }

    // ── Connections ──
    if (phase >= NODES_APPEAR_AT) {
      for (const link of LINKS) {
        if (phase < link.appearsAt) continue;

        const from = nodeById.get(link.from);
        const to = nodeById.get(link.to);
        if (!from || !to) continue;

        const x1 = toX(from);
        const y1 = toY(from);
        const x2 = toX(to);
        const y2 = toY(to);

        let color = palette.linkIdle;
        let baseAlpha = 0.16;

        if (link.kind === 'signal') {
          color = palette.risk;
          baseAlpha = 0.4;
        } else if (link.kind === 'investigation') {
          color = palette.investigation;
          baseAlpha = 0.34;
        } else if (link.kind === 'peer') {
          color = palette.peer;
          baseAlpha = 0.26;
        }

        // Nearby relationships brighten in response to the pointer.
        const near = Math.max(proximity(x1, y1, 110), proximity(x2, y2, 110));
        const alpha = Math.min(baseAlpha + near * 0.34, 0.78);

        ctx.strokeStyle = withAlpha(color, alpha);
        ctx.lineWidth = 1 + near * 0.5;

        ctx.beginPath();
        if (link.kind === 'trajectory') {
          // Gentle arc so trajectories read as motion, not as spokes.
          const midX = (x1 + x2) / 2;
          const midY = (y1 + y2) / 2;
          const dx = x2 - x1;
          const dy = y2 - y1;
          const length = Math.hypot(dx, dy) || 1;
          const curve = Math.min(length * 0.16, 26);
          const cpx = midX - (dy / length) * curve;
          const cpy = midY + (dx / length) * curve;
          ctx.moveTo(x1, y1);
          ctx.quadraticCurveTo(cpx, cpy, x2, y2);
        } else {
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
        }
        ctx.stroke();

        // Signal pulses travel the evidence links once risk is raised.
        if (link.kind === 'signal' && phase >= RISK_BEAT) {
          const travel = reducedMotion ? 0.5 : (lastFrameRef.current % 2600) / 2600;
          const t = travel;
          const cx = x1 + (x2 - x1) * t;
          const cy = y1 + (y2 - y1) * t;
          ctx.fillStyle = withAlpha(palette.risk, 0.75);
          ctx.beginPath();
          ctx.arc(cx, cy, 2, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    // ── Nodes ──
    if (phase >= NODES_APPEAR_AT) {
      for (const node of NODES) {
        if (node.kind === 'peer' && phase < PEER_BEAT) continue;
        if (node.kind === 'evidence' && phase < 2) continue;
        if (node.kind === 'evidence-alt' && phase < 3) continue;
        if (node.kind === 'investigation' && phase < INVESTIGATION_BEAT) continue;

        const x = toX(node);
        const y = toY(node);

        let radius = 3;
        let color = palette.linkIdle;
        let alpha = 0.55;
        let halo = 0;

        switch (node.kind) {
          case 'project':
            radius = 3.5;
            color = palette.project;
            alpha = 0.62;
            break;
          case 'peer':
            radius = 3;
            color = palette.peer;
            alpha = 0.55;
            break;
          case 'evidence':
            radius = 3.5;
            color = palette.evidence;
            alpha = 0.7;
            break;
          case 'evidence-alt':
            radius = 3.5;
            color = palette.evidence;
            alpha = 0.7;
            break;
          case 'investigation':
            radius = 5.5;
            color = palette.investigation;
            alpha = 0.95;
            halo = 12;
            break;
          case 'target':
            radius = 6;
            color = phase >= RISK_BEAT ? palette.risk : palette.target;
            alpha = 1;
            halo = phase >= RISK_BEAT ? 14 : 9;
            break;
        }

        const near = proximity(x, y, 90);
        const drawRadius = radius + near * 1.6;
        const drawAlpha = Math.min(alpha + near * 0.35, 1);

        if (halo > 0) {
          const pulse = reducedMotion ? 0 : (Math.sin(lastFrameRef.current / 520) + 1) / 2;
          const glow = ctx.createRadialGradient(x, y, 0, x, y, drawRadius + halo + pulse * 6);
          glow.addColorStop(0, withAlpha(color, 0.26 * drawAlpha));
          glow.addColorStop(1, withAlpha(color, 0));
          ctx.fillStyle = glow;
          ctx.beginPath();
          ctx.arc(x, y, drawRadius + halo + pulse * 6, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.fillStyle = withAlpha(color, drawAlpha);
        ctx.beginPath();
        ctx.arc(x, y, drawRadius, 0, Math.PI * 2);
        ctx.fill();

        // The target carries a ring once it is in a risk state, so the state
        // change is legible without relying on colour alone.
        if (node.kind === 'target' && phase >= RISK_BEAT) {
          ctx.strokeStyle = withAlpha(palette.risk, 0.5);
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(x, y, drawRadius + 6, 0, Math.PI * 2);
          ctx.stroke();
        }

        // Labels reveal only once the node is meaningful in the story.
        if (node.label) {
          const revealed =
            node.kind === 'peer'
              ? phase >= PEER_BEAT
              : node.kind === 'investigation'
                ? phase >= INVESTIGATION_BEAT
                : node.kind === 'evidence' || node.kind === 'evidence-alt'
                  ? phase >= 2
                  : phase >= 1;
          if (revealed) {
            ctx.font = '9px var(--lp-font-mono, monospace)';
            ctx.fillStyle = withAlpha(color, 0.85);
            ctx.textAlign = 'center';
            ctx.fillText(node.label, x, y - drawRadius - 7);
          }
        }
      }
    }

    // ── Investigation pulse ring ──
    if (phase >= INVESTIGATION_BEAT) {
      const node = nodeById.get('investigation');
      if (node) {
        const x = toX(node);
        const y = toY(node);
        const cycle = reducedMotion ? 0 : (lastFrameRef.current % 2200) / 2200;
        const ringRadius = 8 + cycle * 22;
        ctx.strokeStyle = withAlpha(palette.investigation, 0.34 * (1 - cycle));
        ctx.lineWidth = 1.25;
        ctx.beginPath();
        ctx.arc(x, y, ringRadius, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    // ── Story beat caption ──
    ctx.font = '9px var(--lp-font-mono, monospace)';
    ctx.fillStyle = withAlpha(palette.label, 0.72);
    ctx.textAlign = 'left';
    ctx.fillText(BEAT_LABELS[Math.min(phase, BEAT_LABELS.length - 1)], 4, h - 4);
  }, [reducedMotion]);

  // Repaint on theme change so colours are re-read from the new token set.
  useEffect(() => {
    paint();
  }, [theme, paint]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    if (reducedMotion) {
      // Static equivalent: paint the settled state exactly once, no loop.
      phaseRef.current = SETTLED_PHASE;
      paint();
      return;
    }

    let frame = 0;
    let visible = true;

    const BEAT_MS = 1500;
    const HOLD_MS = 2600;
    let elapsed = 0;
    let last = performance.now();

    // Stop drawing entirely while the hero is off-screen.
    const observer = createIntersectionObserver(
      ([entry]) => {
        visible = entry.isIntersecting;
        if (visible) {
          last = performance.now();
          paint();
        }
      },
      { threshold: 0 },
    );
    observer?.observe(container);

    const tick = (now: number) => {
      frame = requestAnimationFrame(tick);
      if (!visible) return;

      const delta = Math.min(now - last, 64);
      last = now;
      elapsed += delta;
      lastFrameRef.current = now;

      // Story clock: advance through beats, then hold on the settled state.
      const total = BEAT_MS * STORY_BEATS + HOLD_MS;
      const beat = Math.min(Math.floor(elapsed / BEAT_MS), SETTLED_PHASE);
      if (phaseRef.current !== beat) {
        phaseRef.current = beat;
      }

      paint();

      if (elapsed > total) {
        elapsed = 0;
        phaseRef.current = 0;
      }
    };

    frame = requestAnimationFrame(tick);

    const onResize = () => paint();
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(frame);
      observer?.disconnect();
      window.removeEventListener('resize', onResize);
    };
  }, [paint, reducedMotion]);

  const handlePointerMove = useCallback((event: React.PointerEvent<HTMLCanvasElement>) => {
    const container = containerRef.current;
    if (!container) return;
    if (event.pointerType === 'touch') return;
    const rect = container.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    pointerRef.current = {
      x: ((event.clientX - rect.left) / rect.width) * 100,
      y: ((event.clientY - rect.top) / rect.height) * 100,
    };
  }, []);

  const handlePointerLeave = useCallback(() => {
    pointerRef.current = null;
    paint();
  }, [paint]);

  return (
    <div className="lp-hero__visual">
      <canvas
        ref={canvasRef}
        className="lp-hero__canvas"
        onPointerMove={handlePointerMove}
        onPointerLeave={handlePointerLeave}
        role="img"
        aria-label="Abstract project intelligence field: project nodes on an infrastructure grid, one highlighted project crossing a risk boundary, a peer cohort forming around it, and an investigation signal activating on the right."
      />
      <p className="lp-sr-only">
        Illustrative visualisation of the monitoring sequence: the project field is observed, a
        state change is detected, a risk signal is raised, peer deviation is measured, and an
        investigation becomes active. Values shown are conceptual, not live project data.
      </p>
      <span className="lp-hero__visual-tag" aria-hidden="true">
        Conceptual visualisation
      </span>
    </div>
  );
}