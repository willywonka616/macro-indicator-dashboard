# Verification log, review round `2026-07-22c` — a decoupled gold-at-current-price row

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-22b-verification.md` (round b, base
> commit `89bffc1`, LBMA switch + the quarterly-bottleneck finding). Every
> review pass gets its own new file under `docs/review/` — check
> STATUS.md's "current review-round files" note (top of file) for
> whichever round is actually current when you're reading this.
>
> **Base commit:** `46c168a` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §2 below)
> **Written:** 2026-07-22T05:55:00Z UTC

**What prompted this round:** round b found that "Reserves incl. gold
(market)" is bottlenecked to `TRESEGUSM052N`/GDP's own latest common
quarter (2026-Q1) regardless of which gold-price leg is active, so LBMA's
fresher price never actually reaches that row's headline. Rather than
redesign that row unilaterally, this was flagged to the user, who asked
for a second, explicitly-labelled figure using the live gold price
directly, alongside the existing (correctly-lagged) headline.

## 1. Confirming GDP itself is the binding constraint

Before designing the fix, checked whether `TRESEGUSM052N` alone was the
bottleneck (as round b's prose implied) or whether GDP itself also caps
at 2026-Q1 — this matters because it determines whether a %-of-GDP
framing could ever be "live." Read directly from the "Verify FRED series"
step of run `29891818128`'s log:
```
GDP    yes Q    Billions of Dollars    1947-01-01   2026-01-01   202d   220d ok    Gross Domestic Product
```
**GDP's own latest FRED observation is dated 2026-01-01 (Q1 2026),
202 days old** — Q2 2026 GDP hasn't been published yet. This is
independent of `TRESEGUSM052N`. Confirms a %-of-GDP redesign would have
hit the same wall from the other side — the new row is deliberately a
plain dollar figure instead.

**Claim status: VERIFIED** — read directly from a live CI run's own log,
not inferred from code alone.

## 2. Implementation and production verification

`scripts/fetch.py`: new `gold_value_row` (key `gold_value_current`) built
from the same `gold_value_monthly` dict the existing headline row already
computes (live oz × live price), using its own latest overlapping month
rather than intersecting with `TRESEGUSM052N`/GDP at all. Tag mirrors
`reserves_incl_gold_tag`; omitted entirely if the live ounce count itself
fails (no manual dollar fallback exists, same precedent as
`interest_rate_to_keep_debt_flat`).

Live `workflow_dispatch` run:
`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29894871465`,
job `88842789540`, all steps green, committed as `46c168a` (this round's
base commit). Read directly from the resulting `public/data.json`:
```json
{
  "label": "Gold holdings, at current price",
  "value": 1052.8,
  "display": "$1,052.8B",
  "unit": "",
  "tone": "neutral",
  "tag": "live",
  "key": "gold_value_current",
  "src": "derived · Treasury (gold oz 2026-06) + LBMA (PM fix, direct) (price 2026-07)",
  "asOf": "2026-06",
  "history": []
}
```
Directly above it in the same panel, "Reserves incl. gold (market)"
still ships `asOf: "2026-Q1"` — the vintage gap between the two rows is
now visible in the shipped data, not just described in prose.
`provenance.fallbacksFired` contains only the pre-existing, unrelated
COFER entry — no gold-related fallback fired this run.

**Claim status: VERIFIED** — live production run, not a mock;
`public/data.json` at commit `46c168a` inspected directly.

## 3. Local verification

Extended the scratchpad mock-test suite (`test_fetch.py`) with three
assertions:
- **Golden path**: `gold_value_current` row present, `tag: "live"`,
  `display` starts with `$` and ends with `B`, `value` matches
  `round(oz × price / 1e9, 1)` computed independently in the test.
- **Manual-price-input scenario** (§18's fallback path — live oz, stale
  price): row survives, tagged `manual_price`, matching the row above it.
- **Full-manual-fallback scenario** (live ounce count itself
  unavailable): row is **absent** from the panel entirely — asserted via
  `not any(r["key"] == "gold_value_current" ...)`.

All three pass; full existing suite (every prior round's assertions,
including the CBO-outage and gold-freshness-guard scenarios) still passes
unchanged.

```
gold holdings, at current price: $650.2B | 2026-07  (golden path, synthetic fixture)
gold holdings, at current price (manual_price case): $1,046.0B
gold holdings, at current price: correctly omitted when oz itself is unavailable
ALL CHECKS PASSED (incl. freshness guard, 3-tier fallback, provenance assertions, CBO projections)
```

## 4. Browser verification

Patched a local `public/data.json` (and the built `dist/data.json` — vite
preview serves the build output, not `public/` directly; this tripped up
the first screenshot attempt, which found nothing until the build
artifact was refreshed too) with the new row, served via `vite preview`,
screenshotted with Playwright:
- Row renders directly below "Reserves incl. gold (market)", `$1,052.8B`
  display, `ƒx` equation button present.
- Equation panel opens correctly: definition line ("Gold holdings, at
  current price = Gold holdings in troy oz × Gold price"), "what fills
  each term" section with a LIVE DATA tag, and the new caveat explaining
  why this is a dollar figure rather than a ratio.
- Zero console errors.

Patched files (`public/data.json`, `dist/data.json`) discarded before
committing — confirmed via `git status` showing no diff on
`public/data.json`, and `dist/` removed (build artifact, not tracked).

**Claim status: VERIFIED** — Playwright screenshots inspected directly.

## 5. Bundle size

No new dependency — `equations.js`'s new entry is plain data, `fetch.py`
reuses existing helpers. Not re-measured numerically this round (the
change is data/backend-only; the only frontend diff is a content-only
addition to `equations.js`, well within the noise floor of prior
gzip-size measurements).
