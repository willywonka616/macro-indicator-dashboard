# Verification log, review round `2026-07-22a` — gold price, automated

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-21d-verification.md` (round d, base
> commit `2a0a072`, the CBO-projections pass). Every review pass gets its
> own new file under `docs/review/` — check STATUS.md's "current
> review-round files" note (top of file) for whichever round is actually
> current when you're reading this.
>
> **Base commit:** `8a92e75` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> second live `update-data.yml` run documented in §3 below, after the
> freshness-selector fix)
> **Written:** 2026-07-22T04:30:00Z UTC

**What this round covers:** `TASKgoldautomation.md` — eliminating the last
manual-cadence input on the dashboard, the hand-entered gold price
(`data/manual.json`'s `goldPriceManualFallback`, added in round `2026-07-21`
§18). Every source candidate in the task's own §§1-5 was retried or probed
live and the exact result recorded, not assumed from prior-round prose.

## 1. §§1-2 retried live: Nasdaq, Stooq, LBMA

Retried with full browser headers (User-Agent, Accept, Accept-Language) —
`gold.py`'s new diagnostic probes, never used as a live source, run inside
`verify()` on every CI run so the exact failure mode is always current.
Confirmed in CI (run `29890754964`):

```
[nasdaq] https://data.nasdaq.com/api/v3/datasets/LBMA/GOLD.csv?rows=5
  -> HTTP 403, Incapsula bot-challenge HTML — identical to the unheadered attempt

[stooq] https://stooq.com/q/d/l/?s=xauusd&i=d
  -> HTTP 200, but body is a client-side JS proof-of-work challenge page, not CSV

[lbma] https://prices.lbma.org.uk/json/gold_pm.json
  -> HTTP 200, real JSON, history from 1968 — a genuine surprise (the prior
     round's docstring said this had moved fully behind a licensed portal).
     Its actual freshness is NOT established by this probe (only a 200-char
     preview of the chronologically-earliest records was captured) — left
     as an explicit open item rather than asserted either way.
```

**Claim status: VERIFIED** (reachability/failure mode of each), with LBMA's
freshness explicitly flagged NOT VERIFIED — see STATUS.md §22.2 for why
this wasn't chased further given a working source was already in hand.

## 2. §3: World Bank Pink Sheet direct download — a real bug caught live

`scripts/gold.py`'s `_worldbank_pink_sheet_gold_monthly()` downloads and
defensively parses the actual monthly "CMO Historical Data" spreadsheet
from `thedocs.worldbank.org`.

**First `workflow_dispatch` (run `29890496801`, commit `a828d32`):**
```
[gold-price] World Bank Pink Sheet, direct download
  https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/CMO-Historical-Data-Monthly.xlsx
  parsed 792 months; latest: 2025-12 = 4309.23 USD/oz
  freshness: 233d old, 60d threshold, STALE

[gold-price] GitHub mirror (datasets/gold-prices), fallback leg
  parsed 2322 months; latest: 2026-06 = 4228.0 USD/oz
  freshness: 51d old, 60d threshold, ok

  active leg this run: direct download   <-- BUG: chose the stale leg
                                              because it parsed without
                                              raising an exception
```
`fetch.py`'s independent freshness guard on the *combined* price correctly
caught this 233 days old and forced the whole row to `manual_price` instead
of `live` — the system degraded safely, but for the wrong reason (two
layers downstream of where the mistake was made), and skipped a perfectly
good, current source that was right there.

**Root cause, confirmed via web research:** the World Bank had quietly
rotated its live spreadsheet to a new document hash
(`.../74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/...`, in place since
2026-02-03) while the *old* hash kept resolving HTTP 200 and parsing
cleanly forever — just with data frozen at whatever point the rotation
happened. A successful parse was not proof of freshness for this source.

**Fix** (commit `ce6c4d6`): `gold_price_usd_per_oz_labeled()` now checks the
direct leg's own latest observation against the Monthly freshness threshold
before preferring it over the mirror, and the hardcoded URL was updated to
the current hash.

**Second `workflow_dispatch` (run `29890754964`, commit `ce6c4d6`, this
round's base commit `8a92e75`):**
```
[gold-price] World Bank Pink Sheet, direct download
  https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx
  parsed 798 months; latest: 2026-06 = 4228.0 USD/oz
  freshness: 51d old, 60d threshold, ok

[gold-price] GitHub mirror (datasets/gold-prices), fallback leg
  parsed 2322 months; latest: 2026-06 = 4228.0 USD/oz
  freshness: 51d old, 60d threshold, ok

  active leg this run: World Bank (Pink Sheet, direct)   <-- fixed
```

**Claim status: VERIFIED** — two live `workflow_dispatch` runs, not mocks;
the bug, its root cause, and the fix are all confirmed against real CI
output, not inferred.

## 3. Production run details

- Run 1 (bug): `https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29890496801`, job `88829818663`, committed as `6ea75ec` (shipped `manual_price` for gold, correctly degraded despite the source-selection bug).
- Run 2 (fix): `https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29890754964`, job `88830573939`, committed as `8a92e75` (this round's base commit — shipped `live`).

`public/data.json` at `8a92e75`, "Reserves incl. gold (market)" row:
```
tag: "live"
value: 4.9 ("4.9%")
src: "derived · Treasury (gold) + World Bank (Pink Sheet, direct), both 2026-06 + FRED"
asOf: "2026-Q1"
terms: [
  {"label": "Gold holdings (troy oz)", "src": "Treasury (fiscal_service, gold_reserve)", "asOf": "2026-06", "tag": "live"},
  {"label": "Gold price ($/oz)", "src": "World Bank (Pink Sheet, direct)", "asOf": "2026-06", "tag": "live"},
  {"label": "FX reserves excl. gold", "src": "FRED: TRESEGUSM052N", "asOf": "2026-03", "tag": "live"},
  {"label": "GDP", "src": "FRED: GDP", "asOf": "2026-Q1", "tag": "live"}
]
```
No `provenance.fallbacksFired` entry for "Reserves incl. gold (market)" in
this run (only a pre-existing, unrelated COFER mismatch appears — see
STATUS.md §18 for that fallback, unaffected by this round).

**Claim status: VERIFIED** — read directly from the committed
`public/data.json`, not from memory.

## 4. Local verification

Unit-level tests of the new freshness-aware selector
(`gold_price_usd_per_oz_labeled()`), run against the real module with a
stubbed direct-download function:

```
stale-direct-falls-to-mirror test passed: World Bank (Pink Sheet, GitHub mirror: datasets/gold-prices) (2026, 6)
fresh-direct-preferred test passed: World Bank (Pink Sheet, direct)
```

Full scratchpad mock-test suite (`test_fetch.py`, all prior rounds'
scenarios plus the updated gold stubs) re-run end to end:
```
reserves incl. gold: 4.8% | excl. gold: 1.6%
reserves incl. gold src: derived · Treasury (gold) + World Bank (Pink Sheet, direct), both 2026-07 + FRED
...
freshness guard on stale gold price: fell back to manual PRICE INPUT (oz still live), as expected
freshness guard with both oz and price stale: fell back to full manual output, as expected
ALL CHECKS PASSED (incl. freshness guard, 3-tier fallback, provenance assertions, CBO projections)
```
(Mock-test values differ slightly from the live production values above —
expected, synthetic fixture data vs. real fetched data — the point of this
suite is exercising every code path, not reproducing exact numbers.)

## 5. UI staleness indicator (§7)

`MetricRow.jsx` now renders any `note` starting with "⚠" (the existing
convention every fallback-staleness note in this codebase already follows)
in the theme's warning color (`c.caution`) and bold, instead of the same
muted gray as an ordinary caption. Verified visually: patched a local
`public/data.json` to simulate the `manual_price` fallback (the same shape
this row shipped as in production before this round's fix), screenshotted
via Playwright at 500px width, confirmed via `getComputedStyle`:
```
color: rgb(224, 169, 59)   (= #E0A93B = c.caution)
font-weight: 600
```
clearly distinct from the muted gray `src`/`asOf` line beneath it. The
patched `data.json` was reverted before committing — not part of this
round's shipped changes.

## 6. Bundle size

No frontend dependency change — `MetricRow.jsx`'s change is a conditional
inline style, no new imports. `openpyxl` was added to
`scripts/requirements.txt` (Python, CI-only) to parse the World Bank xlsx —
does not affect the frontend bundle.

**Claim status: VERIFIED** — reviewed the diff directly; no new frontend
import.
