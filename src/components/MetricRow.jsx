import React from "react";
import { c, toneColor } from "../theme.js";
import Chart from "./Chart.jsx";

/* One metric line inside a Panel.
 * `r` = { label, value, display?, unit, tone, src, asOf?, history?, note? }.
 * Renders `display` (pre-formatted string) when present, else `value`.
 * `note`, if present, is a short framing caption shown under label/src —
 * for a row that means little without context (e.g. "net" vs "gross"
 * interest), not a full explanation (that's Panel.jsx's longNote).
 * When there's history, a full-width chart is drawn below the row. */
export default function MetricRow({ r }) {
  const shown = r.display ?? r.value;
  const hasChart = r.history && r.history.length > 1;
  return (
    <div className="py-3" style={{ borderBottom: `1px solid ${c.lineSoft}` }}>
      <div className="flex items-center justify-between">
        <div className="min-w-0">
          <div style={{ fontSize: 13, color: c.text }}>{r.label}</div>
          {r.note && (
            <div style={{ fontSize: 11, color: c.muted, marginTop: 1 }}>{r.note}</div>
          )}
          {r.src && r.src !== "—" && (
            <div style={{ fontSize: 10, color: c.faint }}>
              {r.src}
              {r.asOf ? ` · ${r.asOf}` : ""}
            </div>
          )}
        </div>
        <div className="text-right shrink-0 pl-3">
          <span className="font-mono" style={{ fontSize: 16, fontWeight: 600, color: toneColor(r.tone) }}>
            {shown}
          </span>
          {r.unit && (
            <span className="font-mono ml-1" style={{ fontSize: 11, color: c.faint }}>
              {r.unit}
            </span>
          )}
        </div>
      </div>
      {hasChart && (
        <div className="mt-2">
          <Chart data={r.history} color={toneColor(r.tone)} unit={r.unit} />
        </div>
      )}
    </div>
  );
}
