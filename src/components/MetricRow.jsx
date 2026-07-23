import React from "react";
import { c, toneColor } from "../theme.js";
import Chart from "./Chart.jsx";
import EquationButton from "./EquationButton.jsx";

/* One metric line inside a Panel.
 * `r` = { label, value, display?, unit, tone, src, asOf?, history?, note?,
 * key?, terms?, currencyStatus? }. Renders `display` (pre-formatted string)
 * when present, else `value`. `note`, if present, is a short framing
 * caption shown under label/src — for a row that means little without
 * context (e.g. "net" vs "gross" interest), not a full explanation (that's
 * Panel.jsx's longNote). When there's history, a full-width chart is drawn
 * below the row. `key`/`terms` (if present) drive the "ƒx" equation-maths
 * button — see EquationButton.jsx.
 *
 * `currencyStatus` (TASKeuroarea.md §2) is the three-state own-currency
 * semantic: "own" (this entity can unilaterally print what it borrows in —
 * the US, or the euro area as a whole) / "shared" (uses a currency it
 * cannot unilaterally issue — a future euro-area MEMBER STATE) / "foreign"
 * (borrows in someone else's currency outright). Optional — a row with no
 * currencyStatus renders exactly as before this field existed. */
const CURRENCY_STATUS = {
  own: { label: "Own currency — can print what it borrows in", color: (c) => c.mitig },
  shared: { label: "Shared currency — no unilateral issuer", color: (c) => c.caution },
  foreign: { label: "Foreign currency — cannot print at all", color: (c) => c.alarm },
};

export default function MetricRow({ r }) {
  const shown = r.display ?? r.value;
  const hasChart = r.history && r.history.length > 1;
  return (
    <div className="py-3" style={{ borderBottom: `1px solid ${c.lineSoft}` }}>
      <div className="flex items-center justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-1.5">
            <span style={{ fontSize: 13, color: c.text }}>{r.label}</span>
            <EquationButton row={r} />
          </div>
          {r.note && (
            // TASKgoldautomation.md §7: a fallback firing must be visible to
            // a reader of the page, not only to someone reading build logs
            // or a GitHub Actions annotation. Every fallback-staleness note
            // in this codebase is written starting with "⚠" (fetch.py's
            // gold/COFER/manual-freshness notes) — that convention is reused
            // here as the signal to render in the warning color instead of
            // the neutral muted one, rather than adding a second, parallel
            // "is this stale" field that could drift out of sync with it.
            <div
              style={{
                fontSize: 11,
                color: r.note.startsWith("⚠") ? c.caution : c.muted,
                fontWeight: r.note.startsWith("⚠") ? 600 : 400,
                marginTop: 1,
              }}
            >
              {r.note}
            </div>
          )}
          {r.src && r.src !== "—" && (
            <div style={{ fontSize: 10, color: c.faint }}>
              {r.src}
              {r.asOf ? ` · ${r.asOf}` : ""}
            </div>
          )}
          {r.currencyStatus && CURRENCY_STATUS[r.currencyStatus] && (
            <div
              className="inline-block mt-1 rounded px-1.5 py-0.5"
              style={{
                fontSize: 9.5,
                color: CURRENCY_STATUS[r.currencyStatus].color(c),
                border: `1px solid ${CURRENCY_STATUS[r.currencyStatus].color(c)}66`,
                background: `${CURRENCY_STATUS[r.currencyStatus].color(c)}12`,
              }}
            >
              {CURRENCY_STATUS[r.currencyStatus].label}
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
