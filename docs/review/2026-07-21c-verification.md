# Verification log, review round `2026-07-21c` — equation button (Dalio's notation)

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-21b-verification.md` (round b, base
> commit `3335451`, the manual-value freshness guard + provenance
> assertion pass). Every review pass gets its own new file under
> `docs/review/` — check STATUS.md's "current review-round files" note
> (top of file) for whichever round is actually current when you're
> reading this.
>
> **Base commit:** `0873732` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §2 below, on top of the
> equation-button commit `a7af9bb`)
> **Written:** 2026-07-21T08:25:00Z UTC

**What this round covers:** `TASK-equation-button.md` — a small "ƒx"
disclosure control on every metric row revealing the formula behind it in
Ray Dalio's own variable names (*How Countries Go Broke*, Ch. 3), with
current-value definitions kept visibly separate from his forward-looking
projection formulas, and source identifiers demoted to a mapping table
whose src/asOf/tag are read from `data.json` at render time — never
hardcoded in `src/content/`, per the task's addendum.

## 1. Backend: `key` and `terms`

`scripts/fetch.py` now attaches a stable `key` to every panel row and a
`terms` array (each term carrying its own `{label, src, asOf, tag}`) to
the five compound rows: net interest ÷ revenue, gross interest ÷ revenue,
debt ÷ revenue, real 10-year rate, and reserves incl. gold. `_series_asof()`
formats a raw FRED series' latest date consistent with the rest of the
pipeline; `_term()` is a plain constructor. `reserves_incl_gold_terms` is
only populated inside the try branch that actually succeeds (live or
manual_price tier) — the full-manual fallback has nothing to break down
and falls back to a single row built from the parent row's own src/asOf/tag,
same as every non-compound row.

## 2. Full production run: `update-data.yml`, `workflow_dispatch`

`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29813823905`,
job on `claude/new-session-ldotj8` at commit `a7af9bb`, 2026-07-21
08:19-08:21 UTC, committed as `0873732`. Read directly from the committed
`public/data.json`:

```
debt_to_gdp                 | terms: False   (observed, no formula)
debt_service_to_revenue     | terms: True
real_rates                  | terms: True
reserves_to_gdp             | terms: True
... (15 more panel rows, key present on all 19)
```

The `reserves_to_gdp` vital's real `terms` array, produced against actual
live/fallback data this run (the gold-price fallback happened to be
active, giving a genuine mixed-tag example — exactly the case the
mapping table exists to make visible):

```json
[
  {"label": "Gold holdings (troy oz)", "src": "Treasury (fiscal_service, gold_reserve)", "asOf": "2026-06", "tag": "live"},
  {"label": "Gold price ($/oz)", "src": "manual (data/manual.json goldPriceManualFallback, $4,000/oz)", "asOf": "2026-06", "tag": "manual_price"},
  {"label": "FX reserves excl. gold", "src": "FRED: TRESEGUSM052N", "asOf": "2026-03", "tag": "live"},
  {"label": "GDP", "src": "FRED: GDP", "asOf": "2026-Q1", "tag": "live"}
]
```
Three terms `live`, one `manual_price` — read straight from this run's
actual fetch results, not asserted or hardcoded anywhere in
`src/content/equations.js`.

**Claim status: VERIFIED** — live `workflow_dispatch` run, not a mock;
`public/data.json` at commit `0873732` reflects exactly this.

## 3. Browser verification (Playwright)

`chromium-cli` wasn't available in this environment; used the
`playwright` package already present in `node_modules` directly (Node
script, `chromium.launch()` against `/opt/pw-browsers/chromium-1194`).
Driven against the Vite dev server with a full-featured local `data.json`
(generated from the scratchpad mock test — production `data.json` was
temporarily swapped in for the browser session only, then restored
byte-for-byte before anything was committed, confirmed via `git status`
showing no diff on `public/data.json`).

**Golden path:** clicked a `ƒx` button on "Debt service vs income" —
panel opened showing Definition (a `Frac`-rendered ratio), Dalio's
projection formula (three equation lines, fraction layout rendering
correctly), the mapping table (real src/asOf/tag + a live `Tag` pill),
and the interest-only-vs-principal caveat. Screenshots inspected
directly, not assumed from code.

**Keyboard + ARIA**, checked programmatically (not just visually):
```
before click, aria-expanded = false
after 1st click, aria-expanded = true
panel visible after 1st click: true
after Enter (should close), aria-expanded = false
```

**Observed-only row** ("Share in hard (foreign) FX"): renders "DIRECTLY
OBSERVED — NO DERIVATION" plus its own definition and a single-row
mapping table pulled from the row's own src ("—") and `MANUAL` tag.

**390px width — a real bug found and fixed:** first pass measured
`document.documentElement.scrollWidth` at 481px against a 390px
viewport, live in the browser. Root cause: the mapping table's term rows
tried to fit a label and a long, unbroken `src` string side by side in a
`shrink-0` flex row, which refuses to shrink below its content's natural
width instead of wrapping. Fixed by stacking each term (label, then
src/asOf/tag below it) — a block-level stack wraps at any width. Also
added a `max-width` guard to `Frac`'s numerator/denominator spans for
the identical failure mode with long formula terms. Re-tested: opened
all 24 `ƒx` buttons on the page one at a time at 390px, checked
`scrollWidth` after each —
```
total buttons: 24
any overflow across all buttons: false
```

**Console:** zero console/page errors across every check in this section.

**Claim status: VERIFIED** — live Playwright browser session against the
actual dev server and built React components; every claim above is a
programmatic assertion or a directly-inspected screenshot, not inferred
from source reading alone.

## 4. Bundle size

Isolated via `git stash` of only the frontend diff, rebuilt, compared:

```
                Before        After         Δ
JS (raw)      163.47 kB     174.47 kB    +11.00 kB
JS (gzip)      52.84 kB      56.08 kB     +3.24 kB
CSS (raw)       9.47 kB       9.97 kB     +0.50 kB
CSS (gzip)      2.71 kB       2.86 kB     +0.15 kB
```
**+3.39 kB gzip total.** No new runtime dependency — `package.json` is
unchanged this round; fraction rendering is ~15 lines of styled HTML
(`Frac.jsx`), per the task's own "if you disagree after trying it, say
so rather than pulling in KaTeX silently" — it was tried, and plain HTML
was sufficient.

**Claim status: VERIFIED** — `npm run build` output compared directly,
before/after, same working tree modulo the frontend diff.
