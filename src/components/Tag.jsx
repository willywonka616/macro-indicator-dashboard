import React from "react";
import { c } from "../theme.js";

/* Provenance tag. The brief wants provenance visible everywhere, so
 * every metric/panel carries one of: live | model | manual. */
const KINDS = {
  live: { label: "Live data", color: c.calm },
  model: { label: "Dalio model", color: c.mitig },
  manual: { label: "Manual", color: c.caution },
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
        border: `1px solid ${k.color}44`,
        background: `${k.color}12`,
        whiteSpace: "nowrap",
      }}
    >
      {k.label}
    </span>
  );
}
