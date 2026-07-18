/* ------------------------------------------------------------------ *
 *  Theme tokens + shared scales.
 *
 *  Everything colour/threshold related lives here so it is tunable in
 *  one place (per the brief). Carried over verbatim from the legacy
 *  single-file dashboard.
 *
 *  Z-score convention (Dalio's): UP = MORE VULNERABLE.
 *  Negative = protective. +2 and above is "quite bad".
 * ------------------------------------------------------------------ */

export const c = {
  bg: "#0E1418",
  panel: "#161D23",
  panel2: "#1B242B",
  line: "#263039",
  lineSoft: "#1F282F",
  text: "#E7EEF3",
  muted: "#8A9AA6",
  faint: "#5E6B75",
  calm: "#3FB6A8",
  caution: "#E0A93B",
  alarm: "#E5533B",
  mitig: "#5B8DD6",
};

// Z-score scale bounds and the "quite bad" threshold marker.
export const MIN = -3;
export const MAX = 3;
export const THRESH = 2;

// Position (0–100%) of a z-score on the MIN..MAX scale.
export const pct = (v) => Math.max(0, Math.min(100, ((v - MIN) / (MAX - MIN)) * 100));

// tone -> colour. `tone` in data.json drives metric colour.
export const toneColor = (t) =>
  ({ risk: c.alarm, caution: c.caution, neutral: c.muted, mitig: c.mitig }[t] || c.muted);

// z-score -> colour, with the same break points the legacy used.
export const zColor = (z) =>
  z >= THRESH ? c.alarm : z >= 0.75 ? c.caution : z <= -0.75 ? c.mitig : c.muted;
