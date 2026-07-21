import React from "react";
import { c } from "../theme.js";
import MetricRow from "./MetricRow.jsx";
import Tag from "./Tag.jsx";

const commentaryTone = (t) => (t === "alarm" ? c.alarm : t === "calm" ? c.calm : t === "mitig" ? c.mitig : c.text);

/* A titled panel of metric rows.
 * `p` = { eyebrow, tag, note, accent?, rows[] }.
 * `longNote` (optional) = paragraphs of hand-written explanation, same
 * segment shape as commentary.js's `reads` — rendered right under the
 * panel's own rows, not several screens away, for cases (like the net/gross
 * debt-service split) where a reader seeing two numbers side by side needs
 * the reason there. Each paragraph is [{ t, tone? }, ...]. */
export default function Panel({ p, longNote }) {
  return (
    <section
      className="rounded-lg p-4"
      style={{
        background: c.panel,
        border: `1px solid ${c.line}`,
        borderLeft: p.accent ? `2px solid ${p.accent}` : `1px solid ${c.line}`,
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <h3
          style={{
            fontSize: 11,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: p.accent || c.muted,
            fontWeight: 600,
          }}
        >
          {p.eyebrow}
        </h3>
        <Tag kind={p.tag} />
      </div>
      <div>
        {p.rows.map((r, j) => (
          <MetricRow key={j} r={r} />
        ))}
      </div>
      {p.note && (
        <p className="mt-3" style={{ fontSize: 11.5, lineHeight: 1.5, color: c.muted }}>
          {p.note}
        </p>
      )}
      {longNote && longNote.length > 0 && (
        <div className="mt-3 pt-3" style={{ borderTop: `1px solid ${c.lineSoft}` }}>
          {longNote.map((para, i) => (
            <p key={i} style={{ fontSize: 12, lineHeight: 1.6, color: c.muted, marginTop: i === 0 ? 0 : 8 }}>
              {para.map((seg, j) => <span key={j} style={{ color: commentaryTone(seg.tone) }}>{seg.t}</span>)}
            </p>
          ))}
        </div>
      )}
    </section>
  );
}
