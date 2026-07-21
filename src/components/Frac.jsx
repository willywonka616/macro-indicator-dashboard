import React from "react";
import { c } from "../theme.js";

/* Minimal fraction layout: numerator over denominator with a rule between
 * them — styled HTML, no LaTeX dependency (TASK-equation-button.md §3:
 * "enough at this complexity, and keeps the bundle small"). */
export default function Frac({ num, den }) {
  return (
    <span
      className="inline-flex flex-col items-center text-center mx-1"
      style={{ verticalAlign: "middle", lineHeight: 1.25, maxWidth: "min(85vw, 260px)" }}
    >
      <span style={{ padding: "0 2px" }}>{num}</span>
      <span style={{ borderTop: `1px solid ${c.text}`, minWidth: "100%" }} />
      <span style={{ padding: "0 2px" }}>{den}</span>
    </span>
  );
}
