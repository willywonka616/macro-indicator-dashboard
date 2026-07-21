import React from "react";
import { c } from "../theme.js";

/* Provenance tag. The brief wants provenance visible everywhere, so
 * every metric/panel carries one of: live | model | manual | manual_price |
 * projection. `manual_price` is a hybrid: every other input (e.g. gold
 * ounce count) is still live, but one input (e.g. the gold price) is a
 * hand-entered manual value — not fully live, but not a fully manual
 * output either. `projection` (TASKprojections.md) is CBO's own baseline,
 * not this pipeline's forecast and not a current measurement — dashed,
 * not solid, matching the dashed forward segment on its chart (Chart.jsx),
 * so "this is a projection" reads the same way in both places. */
const KINDS = {
  live: { label: "Live data", color: c.calm },
  model: { label: "Dalio model", color: c.mitig },
  manual: { label: "Manual", color: c.caution },
  manual_price: { label: "Manual price input", color: c.caution },
  projection: { label: "Projection (CBO)", color: c.mitig, dashed: true },
};

export default function Tag({ kind }) {
  const k = KINDS[kind] || KINDS.manual;
  return (
    <span
      className="rounded px-1.5 py-0.5"
      style={{
        fontSize: 9,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        color: k.color,
        border: `1px ${k.dashed ? "dashed" : "solid"} ${k.color}66`,
        background: `${k.color}12`,
        whiteSpace: "nowrap",
      }}
    >
      {k.label}
    </span>
  );
}
