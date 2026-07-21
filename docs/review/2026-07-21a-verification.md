# Verification log, review round `2026-07-21a` — manual price/value inputs, not manual outputs

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-20d-verification.md` (round d, base
> commit `a93e485`, the freshness-guard pass that first demoted gold and
> COFER to manual). Every review pass gets its own new file under
> `docs/review/` — check STATUS.md's "current review-round files" note
> (top of file) for whichever round is actually current when you're
> reading this.
>
> **Base commit:** `b0e8827` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §3 below)
> **Written:** 2026-07-21T06:35:00Z UTC

**What this round covers:** a user correction to round d's fix. (1)
Switch the gold-reserves fallback from a manual OUTPUT (a full
hand-carried percentage, equal to Dalio's own book figure by
construction) to a manual PRICE INPUT — one hand-entered number
(~$4,000/oz, dated) applied to the still-live Treasury gold-ounce count,
so the ounce count, FX-excl-gold, and GDP all stay live. Do the same for
IMF COFER: use the latest *actually published* figure instead of the
book-transcribed value. (2) Label the resulting circularity explicitly in
STATUS.md §9, so a fallback-vs-book "match" doesn't read as independent
corroboration. (3) Retry the actual World Bank Pink Sheet (distinct from
the CMO forecast table already ruled out), the ECB Data Portal, and IMF
IFS (distinct from the already-tried PCPS dataflow) — none previously
attempted.

## 1. `data/manual.json` changes

- New `goldPriceManualFallback`: `pricePerOz: 4000`, `asOf: "2026-07-20"`,
  with a `history` array recording the last live DBnomics/PCPS price
  ($3,351.86, 2025-06) and the approximate Jan-2026 peak ($5,595, context
  only). Cross-checked against tradingeconomics.com and mygoldcalc.com
  (~$4,001-4,008/oz as of 2026-07-20).
- `reservesInclGoldFallback` retained (3.0%, Dalio's book figure) but
  re-documented as a last-resort-only path, used only if the live
  Treasury ounce-count fetch itself fails — explicitly marked as not an
  independent check.
- `reserveCurrency.cbReserves` updated from 57.0%/~2024 (book-transcribed)
  to 57.13%/2026-Q1 (the latest actually-published IMF COFER figure),
  with a `history` array of the last five published quarters
  (2025-Q1 through 2026-Q1: 57.79, 56.32, 56.92, 56.42, 57.13). Sourced
  via web search against IMF's own COFER data brief, cross-checked
  against two independent secondary sources citing the same release.

## 2. A new tag, and a bug in the first implementation

Added `manual_price` as a fourth provenance tag (`Tag.jsx`, `App.jsx`) —
a hybrid: one input hand-entered (the gold price), everything else still
live. The frontend already handled an unrecognized tag safely before this
change (confirmed by reading the code first); this was a labelling
addition.

The first attempt at the fetch.py fallback logic had a real bug, caught
by a live production run:
```
Gold price unavailable/stale, using manual price input at the live oz month: freshness guard: gold price (DBnomics PCPS) latest observation is (2025, 6) (414d old, today 2026-07-20) — exceeds the 60d threshold for this series' cadence. The source is likely dead or frozen, not just running a normal lag.
Gold-inclusive reserves unavailable even with a manual price input (live ounce count itself failed), using the full manual fallback: reserves_incl_gold_pct_gdp: no overlapping quarters
```
(`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29767418637`,
job `88436912553`, commit `44d4320` — superseded.) Root cause: the
manual-price dict had exactly one entry, at the live ounce-count month.
`TRESEGUSM052N` (FX reserves excl. gold) lags the gold-ounce series by
several months in practice (2026-03 vs. 2026-06 at the time), so that
single point shared no overlapping month with `TRESEGUSM052N`'s own
history, and `series.reserves_incl_gold_pct_gdp()` — which requires
overlap to compute anything — raised `"no overlapping quarters"`. That
exception was caught by the *outer* handler, which misreported it as "the
live ounce count itself failed" (it hadn't) and fell all the way back to
the old 3.0% manual output, silently defeating the fix.

**Fix:** keep any real (if stale) historical price data the fetch attempt
actually returned, and only patch in the manual price for the months
missing from it — restoring full month coverage so the intersection with
`TRESEGUSM052N`'s own lagging history is non-empty again:
```python
gold_price_monthly = {}
try:
    gold_price_monthly = G.gold_price_usd_per_oz()
    price_asof = max(gold_price_monthly)
    S.require_fresh(...)
    price_is_live = True
except Exception as price_e:
    gpf = mu["goldPriceManualFallback"]
    for ym in gold_oz_monthly.keys() - gold_price_monthly.keys():
        gold_price_monthly[ym] = gpf["pricePerOz"]
    price_asof = oz_asof
    price_is_live = False
```
Verified locally against a strengthened mock test that simulates the real
lag (`TRESEGUSM052N` stub cut off 3 months before "today"; gold-price
stub whose real history also stops short of the gap) — reproduces the
exact "no overlapping quarters" failure pre-fix, resolves correctly to
`manual_price` post-fix.

## 3. Full production run: `update-data.yml`, `workflow_dispatch`

Two runs were needed. The first re-run after the fetch.py fix
(`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29806735725`,
job `88558737649`) computed correctly (no more "no overlapping
quarters"), but its `git push` lost a race against an unrelated STATUS.md
commit pushed moments earlier from this session, so its `data.json` was
never actually saved. A second `workflow_dispatch`
(`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29806949328`,
job `88559389516`, 2026-07-21 06:25-06:27 UTC) ran clean and pushed as
`b0e8827`. Verbatim build-step output:

```
Gold price unavailable/stale, patching a manual price input across the gap: freshness guard: gold price (DBnomics PCPS) latest observation is (2025, 6) (415d old, today 2026-07-21) — exceeds the 60d threshold for this series' cadence. The source is likely dead or frozen, not just running a normal lag.
IMF COFER unavailable, using manual value: freshness guard: IMF COFER USD share latest observation is 2025-Q1 (566d old, today 2026-07-21) — exceeds the 270d threshold for this series' cadence. The source is likely dead or frozen, not just running a normal lag.
Wrote public/data.json — generatedAt 2026-07-21T06:26:59Z
  debt_to_gdp                     99%  (2026-Q1, 225 pts)
  debt_service_to_revenue         20%  (2026-06, 42 pts)
  real_rates                     0.6%  (2026-Q2, 258 pts)
```
```
[claude/new-session-ldotj8 b0e8827] data: monthly refresh (2026-07-21)
 1 file changed, 473 insertions(+), 15 deletions(-)
```

**Claim status: VERIFIED** — the run succeeded (exit 0); the gold price
and COFER both correctly fell back per the new 3-tier chain (gold to
`manual_price`, COFER to `manual` with the real figure), and every other
live row's own freshness check passed. See §4 of `docs/review/2026-07-21a-values.md`
for the resulting values and STATUS.md §18 for the full writeup.

## 4. World Bank Pink Sheet, ECB Data Portal, IMF IFS — retried, all ruled out

Run via a temporary `scripts/gold_source_retry.py` (deleted after
findings captured, commit `f0d7209`, per this project's
diagnostic-not-a-feature convention).

```
provider WB: 14 datasets
  ... all 14 enumerated by name/description; none is the monthly Pink
  Sheet. GEM = CPI/inflation series per country. commodity_prices =
  the same annual Commodity Markets Outlook table already ruled out in
  round c (latest value is a 2030 projection).

ECB Data Portal:
  correct dataset category found (FM, confirmed via other commodities
  like Brent crude present) — 4 keyword variants (gold/XAU/bullion/
  precious) + a raw naming-convention sample: 0 gold/XAU series found.
  2 guessed direct-API series keys: both 404.

IMF IFS (distinct dataset from PCPS, not previously tried):
  gold-related series exist, but all are per-country reserve HOLDINGS
  valued at market price (a stock/quantity measure) — not a $/oz price
  benchmark. Not usable as a price source for this pipeline.
```

**Result: all three tried, all three ruled out for specific, evidenced
reasons.** No source switch. See STATUS.md §18.5.
