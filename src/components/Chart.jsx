import React, { useEffect, useRef, useState } from "react";
import { c, CRISES } from "../theme.js";

/* Full-width time-series chart: real x/y axes with units, tick marks and
 * labels, vertical crisis/regime markers, and a hover crosshair + tooltip.
 * `data` = [{ y: decimalYear, v: value }]. Values are percentages. */

function niceDomain(min, max) {
  if (min === max) return [min - 1, max + 1];
  const span = max - min;
  const pad = span * 0.08;
  let lo = min - pad;
  const hi = max + pad;
  if (min >= 0 && lo < 0) lo = 0; // don't invent negative territory
  return [lo, hi];
}

// ~`count` "nice" tick values across [lo, hi].
function niceTicks(lo, hi, count) {
  const raw = (hi - lo) / count;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const norm = raw / mag;
  const step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag;
  const out = [];
  for (let t = Math.ceil(lo / step) * step; t <= hi + 1e-9; t += step) {
    out.push(Math.round(t * 1e6) / 1e6);
  }
  return out;
}

function yearTicks(minY, maxY) {
  const span = maxY - minY;
  const step = span > 80 ? 20 : span > 40 ? 10 : span > 16 ? 5 : span > 6 ? 2 : 1;
  const out = [];
  for (let t = Math.ceil(minY / step) * step; t <= maxY + 1e-9; t += step) out.push(t);
  return out;
}

const fmtPct = (v) => `${Number.isInteger(v) ? v : v.toFixed(1)}%`;

export default function Chart({ data, color, unit = "", height = 300 }) {
  // TASKprojections.md §6: a projection must never be mistaken for a
  // measurement. Points carrying `projected: true` (CBO baseline, not a
  // fetched observation) get their own dashed polyline plus a shaded
  // background region, both starting at the last historical point so the
  // line reads as continuous, not disconnected. Charts with no projected
  // points behave exactly as before — this is purely additive.
  const wrap = useRef(null);
  const [w, setW] = useState(720);
  const [hoverI, setHoverI] = useState(null);

  useEffect(() => {
    if (!wrap.current) return;
    const ro = new ResizeObserver((entries) => {
      const cw = entries[0].contentRect.width;
      if (cw) setW(cw);
    });
    ro.observe(wrap.current);
    return () => ro.disconnect();
  }, []);

  if (!data || data.length < 2) return null;

  const H = height;
  const m = { top: 20, right: 24, bottom: 36, left: 56 };
  const iw = Math.max(10, w - m.left - m.right);
  const ih = H - m.top - m.bottom;

  const xs = data.map((d) => d.y);
  const vs = data.map((d) => d.v);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const [loY, hiY] = niceDomain(Math.min(...vs), Math.max(...vs));

  const px = (x) => m.left + ((x - minX) / (maxX - minX || 1)) * iw;
  const py = (v) => m.top + ((hiY - v) / (hiY - loY || 1)) * ih;

  const yT = niceTicks(loY, hiY, 5);
  const xT = yearTicks(minX, maxX);

  // Historical (solid) vs. projected (dashed) split — see the note above
  // the component. projPoints repeats the last historical point so the
  // dashed segment starts exactly where the solid one ends.
  const firstProjIdx = data.findIndex((d) => d.projected);
  const hasProjection = firstProjIdx > -1;
  const histPoints = hasProjection ? data.slice(0, firstProjIdx) : data;
  const projPoints = hasProjection ? data.slice(Math.max(firstProjIdx - 1, 0)) : [];
  const transitionX = hasProjection && histPoints.length ? px(histPoints[histPoints.length - 1].y) : null;

  const line = histPoints.map((d) => `${px(d.y).toFixed(1)},${py(d.v).toFixed(1)}`).join(" ");
  const area = histPoints.length > 1
    ? `${px(histPoints[0].y).toFixed(1)},${py(loY).toFixed(1)} ${line} ` +
      `${px(histPoints[histPoints.length - 1].y).toFixed(1)},${py(loY).toFixed(1)}`
    : "";
  const projLine = projPoints.map((d) => `${px(d.y).toFixed(1)},${py(d.v).toFixed(1)}`).join(" ");

  const last = data[data.length - 1];
  const lastIsProjected = !!last.projected;
  const zeroInRange = loY < 0 && hiY > 0;
  // Cascade crisis labels left-to-right with a guaranteed minimum gap so
  // clusters of 2+ close markers (e.g. 1973/1979/1980 on a narrow phone
  // chart) fan out instead of stacking on top of each other. Each label's
  // TEXT position is pushed right only as far as needed to clear the
  // previous one; the dashed reference line always stays at the marker's
  // true year. Computed from actual on-screen spacing, so it holds at any
  // chart width.
  const LABEL_MIN_GAP = 16;
  let lastTx = -Infinity;
  const crises = CRISES.filter((cr) => cr.year >= minX && cr.year <= maxX).map((cr) => {
    const cx = px(cr.year);
    const tx = Math.max(cx - 3, lastTx + LABEL_MIN_GAP);
    lastTx = tx;
    return { ...cr, cx, tx };
  });

  const onMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clientX = e.clientX ?? (e.touches && e.touches[0] && e.touches[0].clientX);
    if (clientX == null) return;
    const sx = (clientX - rect.left) * (w / rect.width);
    const xv = minX + ((sx - m.left) / iw) * (maxX - minX || 1);
    let idx = 0, best = Infinity;
    data.forEach((d, i) => {
      const dd = Math.abs(d.y - xv);
      if (dd < best) { best = dd; idx = i; }
    });
    setHoverI(idx);
  };

  const hp = hoverI != null ? data[hoverI] : null;

  return (
    <div ref={wrap} style={{ position: "relative", width: "100%" }}>
      <svg
        width={w}
        height={H}
        style={{ display: "block", touchAction: "pan-y" }}
        onMouseMove={onMove}
        onMouseLeave={() => setHoverI(null)}
        onTouchStart={onMove}
        onTouchMove={onMove}
        onTouchEnd={() => setHoverI(null)}
      >
        {/* y gridlines + labels */}
        {yT.map((t, i) => (
          <g key={`y${i}`}>
            <line x1={m.left} x2={m.left + iw} y1={py(t)} y2={py(t)} stroke={c.lineSoft} strokeWidth={1} />
            <text x={m.left - 8} y={py(t)} textAnchor="end" dominantBaseline="middle" fontSize={11} fill={c.faint}>
              {fmtPct(t)}
            </text>
          </g>
        ))}
        {zeroInRange && (
          <line x1={m.left} x2={m.left + iw} y1={py(0)} y2={py(0)} stroke={c.line} strokeWidth={1} />
        )}

        {/* shaded forward region (TASKprojections.md §6) — drawn first, as a
            background layer, so the observed-to-projected transition is
            obvious even before noticing the dashed line itself */}
        {hasProjection && transitionX != null && (
          <rect
            x={transitionX} y={m.top} width={Math.max(0, m.left + iw - transitionX)} height={ih}
            fill={c.mitig} opacity={0.06}
          />
        )}

        {/* x axis ticks + labels */}
        <line x1={m.left} x2={m.left + iw} y1={m.top + ih} y2={m.top + ih} stroke={c.line} strokeWidth={1} />
        {xT.map((t, i) => (
          <g key={`x${i}`}>
            <line x1={px(t)} x2={px(t)} y1={m.top + ih} y2={m.top + ih + 5} stroke={c.line} strokeWidth={1} />
            <text x={px(t)} y={m.top + ih + 18} textAnchor="middle" fontSize={11} fill={c.faint}>
              {Math.round(t)}
            </text>
          </g>
        ))}

        {/* crisis / regime markers */}
        {crises.map((cr, i) => {
          const { cx, tx } = cr;
          const ly = m.top + 3;
          return (
            <g key={`c${i}`}>
              <line x1={cx} x2={cx} y1={m.top} y2={m.top + ih} stroke={c.faint} strokeWidth={1} strokeDasharray="3 3" opacity={0.55} />
              <text
                x={tx}
                y={ly}
                transform={`rotate(-90 ${tx} ${ly})`}
                textAnchor="end"
                fontSize={9}
                fill={c.faint}
              >
                {cr.short}
              </text>
            </g>
          );
        })}

        {/* series: solid historical, dashed projected tail (TASKprojections.md
            §6 — "a reader must never mistake a projection for a
            measurement") */}
        {area && <polygon points={area} fill={color} opacity={0.1} />}
        {line && (
          <polyline points={line} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        )}
        {hasProjection && (
          <>
            <polyline
              points={projLine} fill="none" stroke={color} strokeWidth={2}
              strokeDasharray="6 4" strokeLinejoin="round" strokeLinecap="round" opacity={0.85}
            />
            {transitionX != null && (
              <line
                x1={transitionX} x2={transitionX} y1={m.top} y2={m.top + ih}
                stroke={c.mitig} strokeWidth={1} strokeDasharray="2 3" opacity={0.6}
              />
            )}
            <text
              x={Math.min(transitionX ?? m.left, m.left + iw) + 4} y={m.top + 11}
              fontSize={9} letterSpacing="0.06em" fill={c.mitig}
            >
              PROJECTED
            </text>
          </>
        )}
        {lastIsProjected ? (
          <circle cx={px(last.y)} cy={py(last.v)} r={3.5} fill={c.bg} stroke={color} strokeWidth={2} />
        ) : (
          <circle cx={px(last.y)} cy={py(last.v)} r={3} fill={color} />
        )}

        {/* y-axis caption (unit) */}
        <text x={m.left - 8} y={m.top - 8} textAnchor="start" fontSize={10} fill={c.muted}>
          % {unit}
        </text>

        {/* hover crosshair */}
        {hp && (
          <g>
            <line x1={px(hp.y)} x2={px(hp.y)} y1={m.top} y2={m.top + ih} stroke={c.muted} strokeWidth={1} opacity={0.6} />
            <circle cx={px(hp.y)} cy={py(hp.v)} r={4} fill={color} stroke={c.bg} strokeWidth={2} />
          </g>
        )}
      </svg>

      {hp && (
        <div
          style={{
            position: "absolute",
            left: Math.min(Math.max(px(hp.y) + 8, 4), w - 96),
            top: 4,
            pointerEvents: "none",
            background: c.panel2,
            border: `1px solid ${c.line}`,
            borderRadius: 6,
            padding: "4px 8px",
            fontSize: 11,
            color: c.text,
            whiteSpace: "nowrap",
          }}
        >
          <span style={{ color: c.faint }}>{Math.round(hp.y)}</span>{" "}
          <span className="font-mono" style={{ color, fontWeight: 600 }}>{fmtPct(hp.v)}</span>
        </div>
      )}
    </div>
  );
}
