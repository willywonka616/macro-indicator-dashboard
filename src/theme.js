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

// Vertical crisis / regime markers drawn on every time-series chart.
// `year` is a decimal year; `short` is the on-chart label. Tunable in one place.
export const CRISES = [
  { year: 1973, short: "'73 oil shock", label: "1973 oil shock (OPEC embargo)" },
  { year: 1979, short: "'79 oil shock", label: "1979 oil shock (Iranian revolution)" },
  { year: 1980, short: "1980", label: "Volcker shock / early-80s recession (1980)" },
  { year: 1987, short: "Black Monday", label: "Black Monday crash (1987)" },
  { year: 2000, short: "Dot-com", label: "Dot-com peak (2000)" },
  { year: 2008, short: "GFC", label: "Global financial crisis (2007–08)" },
  { year: 2020, short: "COVID", label: "COVID crash (2020)" },
];
