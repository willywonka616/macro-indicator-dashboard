import React from "react";
import { c, zColor } from "../theme.js";
import ZScale from "./ZScale.jsx";
import Tag from "./Tag.jsx";

/* One line inside a risk gauge (gov / central bank), or a Z-less context
 * line underneath one (TASKcbrawvalues.md).
 *
 * `r` = {
 *   label, z?, mitig?, extra?, constant?, note?,
 *   book?:  { display, asOf? },   // Dalio's frozen March-2025 book figure
 *   live?:  { display, asOf, src?, note? },  // this pipeline's live reading
 *   components?: [ { label, book?, live? }, ... ],  // sub-items, no own z
 * }
 *
 * `z` is OPTIONAL: rows with no z (the "context" list — book-table figures
 * Dalio doesn't score separately in our simplified model) render without
 * the Z badge / scale bar, just label + book/live. */

function ValueLine({ book, live, extra, constant }) {
  const parts = [];
  if (live) {
    parts.push(
      <span key="live" className="inline-flex items-baseline gap-1">
        <span className="font-mono" style={{ fontSize: 12, fontWeight: 600, color: c.calm }}>
          {live.display}
        </span>
        {live.asOf && (
          <span style={{ fontSize: 9.5, color: c.faint }}>({live.asOf})</span>
        )}
      </span>
    );
  }
  if (book) {
    parts.push(
      <span key="book" className="inline-flex items-baseline gap-1">
        <span className="font-mono" style={{ fontSize: live ? 11 : 12, color: live ? c.faint : c.muted }}>
          {book.display}
        </span>
        <span style={{ fontSize: 9.5, color: c.faint }}>
          (book{book.asOf ? `, ${book.asOf}` : ""})
        </span>
      </span>
    );
  }
  if (!parts.length && extra) {
    parts.push(
      <span key="extra" className="font-mono" style={{ fontSize: 11, color: c.faint }}>
        {extra}{constant ? " (constant)" : ""}
      </span>
    );
  }
  if (!parts.length) return null;
  return <div className="flex flex-wrap items-baseline gap-2 mt-0.5">{parts}</div>;
}

function NoteLine({ text }) {
  if (!text) return null;
  return (
    <div style={{ fontSize: 10.5, color: c.faint, lineHeight: 1.4, marginTop: 2 }}>
      {text}
    </div>
  );
}

export default function GaugeRow({ r }) {
  const hasZ = r.z !== undefined && r.z !== null;
  return (
    <div className="py-2.5" style={{ borderBottom: `1px solid ${c.lineSoft}` }}>
      <div className="flex items-center justify-between mb-1">
        <span className="flex items-center gap-1.5">
          <span style={{ fontSize: 13, color: r.mitig ? c.mitig : c.text }}>{r.label}</span>
          {r.live && <Tag kind="live" />}
        </span>
        {hasZ && (
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
        )}
      </div>
      <ValueLine book={r.book} live={r.live} extra={r.extra} constant={r.constant} />
      {hasZ && (
        <div className="mt-1.5">
          <ZScale z={r.z} height={5} />
        </div>
      )}
      <NoteLine text={r.note} />
      {r.live?.note && <NoteLine text={r.live.note} />}
      {r.components && r.components.length > 0 && (
        <div className="mt-2 pl-3" style={{ borderLeft: `2px solid ${c.lineSoft}` }}>
          {r.components.map((comp, i) => (
            <div key={i} className={i > 0 ? "mt-2" : ""}>
              <span className="flex items-center gap-1.5">
                <span style={{ fontSize: 11.5, color: c.muted }}>{comp.label}</span>
                {comp.live && <Tag kind="live" />}
              </span>
              <ValueLine book={comp.book} live={comp.live} />
              <NoteLine text={comp.live?.note} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
