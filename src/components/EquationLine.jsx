import React from "react";
import { c } from "../theme.js";
import Frac from "./Frac.jsx";

/* One line of an equation: a sequence of plain-text parts and fractions,
 * laid out left to right and wrapping naturally at narrow widths (e.g.
 * 390px, TASK-equation-button.md §5's accessibility acceptance bar).
 * `parts` = Array<string | {num, den}>. */
export default function EquationLine({ parts }) {
  return (
    <div
      className="flex flex-wrap items-center gap-x-1 gap-y-1.5"
      style={{ fontFamily: "ui-serif, Georgia, 'Times New Roman', serif", fontSize: 12.5, color: c.text }}
    >
      {parts.map((p, i) =>
        typeof p === "string" ? <span key={i}>{p}</span> : <Frac key={i} num={p.num} den={p.den} />
      )}
    </div>
  );
}
