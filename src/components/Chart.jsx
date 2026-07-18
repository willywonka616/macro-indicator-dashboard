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
  const line = data.map((d) => `${px(d.y).toFixed(1)},${py(d.v).toFixed(1)}`).join(" ");
  const area = `${px(minX).toFixed(1)},${py(loY).toFixed(1)} ${line} ${px(maxX).toFixed(1)},${py(loY).toFixed(1)}`;
  const last = data[data.length - 1];
  const zeroInRange = loY < 0 && hiY > 0;
  const crises = CRISES.filter((cr) => cr.year >= minX && cr.year <= maxX);

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
          const cx = px(cr.year);
          return (
            <g key={`c${i}`}>
              <line x1={cx} x2={cx} y1={m.top} y2={m.top + ih} stroke={c.faint} strokeWidth={1} strokeDasharray="3 3" opacity={0.55} />
              <text
                x={cx - 3}
                y={m.top + 3}
                transform={`rotate(-90 ${cx - 3} ${m.top + 3})`}
                textAnchor="end"
                fontSize={9}
                fill={c.faint}
              >
                {cr.short}
              </text>
            </g>
          );
        })}

        {/* series */}
        <polygon points={area} fill={color} opacity={0.1} />
        <polyline points={line} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={px(last.y)} cy={py(last.v)} r={3} fill={color} />

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
