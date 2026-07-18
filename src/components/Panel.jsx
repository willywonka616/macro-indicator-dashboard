import React from "react";
import { c } from "../theme.js";
import MetricRow from "./MetricRow.jsx";
import Tag from "./Tag.jsx";

/* A titled panel of metric rows.
 * `p` = { eyebrow, tag, note, accent?, rows[] }. */
export default function Panel({ p }) {
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
    </section>
  );
}
