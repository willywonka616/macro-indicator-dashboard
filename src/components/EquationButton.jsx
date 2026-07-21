import React, { useId, useState } from "react";
import { c } from "../theme.js";
import { equations } from "../content/equations.js";
import EquationLine from "./EquationLine.jsx";
import Tag from "./Tag.jsx";

/* Small "ƒx" disclosure control revealing the maths behind a metric, in
 * Dalio's own notation (How Countries Go Broke, Ch. 3 — see
 * TASK-equation-button.md). Renders nothing if src/content/equations.js
 * has no entry for `row.key` — that's the "row without an entry simply
 * shows no button" rule from that file's §4, not a bug.
 *
 * The mapping table ("what fills each term") is built from `row` itself
 * at render time — `row.terms` when fetch.py provided a per-term
 * breakdown (compound rows like reserves-incl-gold), otherwise a single
 * fallback row built from the row's own src/asOf/tag. Nothing here is
 * hardcoded: a tag that doesn't exist yet in Tag.jsx's KINDS map still
 * renders (falls through to the caution/manual styling), so a future
 * pipeline change that adds another tag needs no change in this file. */
export default function EquationButton({ row }) {
  const entry = row?.key ? equations[row.key] : null;
  const [open, setOpen] = useState(false);
  const panelId = useId();

  if (!entry) return null;

  const terms =
    row.terms && row.terms.length > 0
      ? row.terms
      : [{ label: row.label || "This figure", src: row.src, asOf: row.asOf, tag: row.tag }];

  return (
    // display:contents so the button and (when open) the panel become
    // direct children of the caller's flex row, letting flex-wrap put the
    // panel on its own full-width line below the label instead of
    // squeezing sideways next to it.
    <span style={{ display: "contents" }}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={`${open ? "Hide" : "Show"} the maths behind ${row.label || "this figure"}`}
        onClick={() => setOpen((o) => !o)}
        className="rounded"
        style={{
          fontFamily: "ui-serif, Georgia, serif",
          fontStyle: "italic",
          fontSize: 10.5,
          width: 17,
          height: 17,
          lineHeight: "16px",
          textAlign: "center",
          color: open ? c.bg : c.faint,
          background: open ? c.calm : "transparent",
          border: `1px solid ${open ? c.calm : c.line}`,
          cursor: "pointer",
          padding: 0,
        }}
      >
        ƒx
      </button>

      {open && (
        <div
          id={panelId}
          role="region"
          aria-label={`Maths behind ${row.label || "this figure"}`}
          className="eq-panel mt-2 rounded-lg p-3"
          style={{ background: c.panel2, border: `1px solid ${c.line}`, fontSize: 12, width: "100%" }}
        >
          {/* 1. Definition */}
          <SectionLabel color={c.muted}>
            {entry.kind === "observed" ? "Directly observed — no derivation" : "Definition"}
          </SectionLabel>
          {typeof entry.definition === "string" ? (
            <p style={{ color: c.text, lineHeight: 1.5 }}>{entry.definition}</p>
          ) : (
            <EquationLine parts={entry.definition} />
          )}

          {/* 2. Dalio's forward-looking formula, only where one exists */}
          {entry.formula && (
            <div className="mt-3 pt-3" style={{ borderTop: `1px solid ${c.lineSoft}` }}>
              <SectionLabel color={c.mitig}>{entry.formula.label}</SectionLabel>
              {entry.formula.lines.map((line, i) => (
                <div key={i} className={i ? "mt-2" : ""}>
                  <EquationLine parts={line} />
                </div>
              ))}
              {entry.formula.prose && (
                <p className="mt-2" style={{ fontSize: 11, color: c.muted, lineHeight: 1.5 }}>
                  {entry.formula.prose}
                </p>
              )}
            </div>
          )}
          {entry.formulaNote && (
            <p className="mt-2" style={{ fontSize: 11, color: c.muted, lineHeight: 1.5 }}>
              {entry.formulaNote}
            </p>
          )}

          {/* 3. What fills each term — src/asOf/tag read from data.json, not
             this file. Stacked (label, then src/tag below), not side by
             side — a long src string (e.g. "Treasury (MTS mts_table_4,
             total receipts net of refunds, TTM)") has no natural break
             point, so trying to fit it beside the label overflows narrow
             viewports; stacking avoids that at any width. */}
          <div className="mt-3 pt-3" style={{ borderTop: `1px solid ${c.lineSoft}` }}>
            <SectionLabel color={c.muted}>What fills each term</SectionLabel>
            <div style={{ display: "flex", flexDirection: "column" }}>
              {terms.map((t, i) => (
                <div
                  key={i}
                  className="py-1.5"
                  style={{ borderTop: i ? `1px solid ${c.lineSoft}` : "none", minWidth: 0 }}
                >
                  <div style={{ color: c.text, fontSize: 11 }}>{t.label}</div>
                  <div className="flex flex-wrap items-center gap-1.5 mt-0.5">
                    <span style={{ color: c.faint, fontSize: 10, wordBreak: "break-word" }}>
                      {t.src || "—"}
                      {t.asOf ? ` · ${t.asOf}` : ""}
                    </span>
                    {t.tag && <Tag kind={t.tag} />}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 4. Caveats */}
          {entry.caveats && entry.caveats.length > 0 && (
            <div className="mt-3 pt-3" style={{ borderTop: `1px solid ${c.lineSoft}` }}>
              <SectionLabel color={c.caution}>Caveats</SectionLabel>
              {entry.caveats.map((cv, i) => (
                <p key={i} style={{ fontSize: 11, color: c.muted, lineHeight: 1.5, marginTop: i ? 4 : 0 }}>
                  {cv}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </span>
  );
}

function SectionLabel({ children, color }) {
  return (
    <div
      style={{
        fontSize: 9.5,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        color,
        fontWeight: 600,
        marginBottom: 5,
      }}
    >
      {children}
    </div>
  );
}
