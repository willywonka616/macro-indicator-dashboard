import React from "react";
import { c, zColor } from "../theme.js";
import ZScale from "./ZScale.jsx";

/* One component line inside a risk gauge (gov / central bank).
 * `r` = { label, z, extra?, mitig? }. */
export default function GaugeRow({ r }) {
  return (
    <div className="py-2.5" style={{ borderBottom: `1px solid ${c.lineSoft}` }}>
      <div className="flex items-center justify-between mb-1.5">
        <span style={{ fontSize: 13, color: r.mitig ? c.mitig : c.text }}>{r.label}</span>
        <span className="flex items-baseline gap-2">
          {r.extra && (
            <span className="font-mono" style={{ fontSize: 11, color: c.faint }}>
              {r.extra}
            </span>
          )}
          <span
            className="font-mono"
            style={{
              fontSize: 14,
              fontWeight: 600,
              color: zColor(r.z),
              minWidth: 44,
              textAlign: "right",
              display: "inline-block",
            }}
          >
            {r.z > 0 ? "+" : ""}
            {r.z.toFixed(1)}z
          </span>
        </span>
      </div>
      <ZScale z={r.z} height={5} />
    </div>
  );
}
