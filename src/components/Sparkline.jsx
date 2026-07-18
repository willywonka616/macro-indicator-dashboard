import React from "react";
import { c } from "../theme.js";

/* Real historical trace. `data` = [{ y: decimalYear, v: value }].
 * Carried over unchanged from the legacy dashboard so full-resolution
 * history from data.json renders without any changes here. */
export default function Sparkline({ data, color, w = 116, h = 30 }) {
  if (!data || data.length < 2) return null;
  const xs = data.map((d) => d.y),
    vs = data.map((d) => d.v);
  const minX = Math.min(...xs),
    maxX = Math.max(...xs);
  const minY = Math.min(...vs),
    maxY = Math.max(...vs);
  const rY = maxY - minY || 1,
    rX = maxX - minX || 1;
  const px = (x) => ((x - minX) / rX) * (w - 3) + 1.5;
  const py = (v) => h - 3 - ((v - minY) / rY) * (h - 6);
  const line = data.map((d) => `${px(d.y).toFixed(1)},${py(d.v).toFixed(1)}`).join(" ");
  const area = `${px(minX).toFixed(1)},${h} ${line} ${px(maxX).toFixed(1)},${h}`;
  const last = data[data.length - 1];
  const zeroInRange = minY < 0 && maxY > 0;
  return (
    <div className="flex items-center gap-2">
      <svg width={w} height={h} style={{ display: "block", overflow: "visible" }}>
        {zeroInRange && (
          <line x1={0} x2={w} y1={py(0)} y2={py(0)} stroke={c.line} strokeWidth={1} strokeDasharray="2 2" />
        )}
        <polygon points={area} fill={color} opacity={0.09} />
        <polyline points={line} fill="none" stroke={color} strokeWidth={1.4} opacity={0.9} strokeLinejoin="round" />
        <circle cx={px(last.y)} cy={py(last.v)} r={2.1} fill={color} />
      </svg>
      <span className="font-mono" style={{ fontSize: 9, color: c.faint, whiteSpace: "nowrap" }}>
        {Math.round(minX)}–{String(Math.round(maxX)).slice(2)}
      </span>
    </div>
  );
}
