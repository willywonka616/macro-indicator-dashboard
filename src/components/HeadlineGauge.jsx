import React from "react";
import { c, zColor } from "../theme.js";
import ZScale from "./ZScale.jsx";

/* One of the two big headline z-score gauges (gov / central bank).
 * `g` = { z, label, verdict, source }. */
export default function HeadlineGauge({ g }) {
  return (
    <div className="rounded-lg p-4" style={{ background: c.panel2, border: `1px solid ${c.line}` }}>
      <div style={{ fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: c.muted }}>
        {g.label}
      </div>
      <div className="flex items-baseline gap-2 mt-1 mb-3">
        <span className="font-mono" style={{ fontSize: 30, fontWeight: 600, color: zColor(g.z), lineHeight: 1 }}>
          {g.z > 0 ? "+" : ""}
          {g.z.toFixed(1)}
        </span>
        <span className="font-mono" style={{ fontSize: 12, color: c.faint }}>
          z
        </span>
        <span className="ml-auto" style={{ fontSize: 12, color: zColor(g.z) }}>
          {g.verdict}
        </span>
      </div>
      <ZScale z={g.z} />
    </div>
  );
}
