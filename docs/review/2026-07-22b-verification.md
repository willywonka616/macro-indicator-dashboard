# Verification log, review round `2026-07-22b` — LBMA over Pink Sheet, and a bottleneck found

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-22a-verification.md` (round a, base
> commit `8a92e75`, gold automation via World Bank Pink Sheet). Every
> review pass gets its own new file under `docs/review/` — check
> STATUS.md's "current review-round files" note (top of file) for
> whichever round is actually current when you're reading this.
>
> **Base commit:** `89bffc1` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §2 below)
> **Written:** 2026-07-22T04:50:00Z UTC

**What prompted this round:** a manual check on round a's shipped figure
(4.9% of GDP, off a $4,228/oz "June 2026" World Bank Pink Sheet price)
found actual spot gold running $4,070-4,083/oz around the time it was
checked — a real gap. Two explicit questions to answer with evidence, not
assumption: (1) what price/date did the run actually ship, confirming or
correcting the "~2 months stale" claim; (2) is a lagged monthly average
even the right source for this row, with LBMA and XAU-as-currency FX APIs
re-probed as candidates.

## 1. What round a actually shipped, and whether "~2 months stale" holds

Read directly from `public/data.json` at commit `8a92e75`:
```
value: 4228.00 USD/oz
asOf (of the price term): 2026-06
src: "... World Bank (Pink Sheet, direct), both 2026-06 ..."
```

**Cross-referenced actual daily 2026 gold prices (web research):**
```
2026-06-01: ~$4,460    2026-06-10: ~$4,152    2026-06-25: ~$4,005
2026-06-30: ~$4,015    2026-07-21: ~$4,070-4,083 (spot at time of check)
```
A $4,228 whole-month June average is **consistent with this real
trajectory** (opening high, declining through the month) — not a
mislabeled May figure as originally guessed. The precise "~2 month" claim
doesn't hold exactly, but the underlying complaint is correct: an average
over a declining month represents gold's price as of roughly the middle
of the window, materially different from spot by the time it's checked
weeks later.

**Claim status: VERIFIED** (the actual shipped price/date, and the
research reconciling it against real daily prices), with the original
"~2-month/May" framing explicitly corrected rather than accepted.

## 2. LBMA re-probed properly — and it works

The prior round's diagnostic probe only logged a 200-character preview,
which for `gold_pm.json`'s array (ascending from 1968) showed only the
earliest records — no claim about freshness was actually possible from
that evidence, though the round's prose assumed "still blocked." This
round implemented the feed for real and let a live CI run settle it:

```
[lbma] https://prices.lbma.org.uk/json/gold_pm.json
  parsed 700 months; latest observation: 2026-07-21 = 4052.3 USD/oz
  freshness: 1d old, 20d threshold, ok
  active leg this run: LBMA (PM fix, direct)
```
Run: `https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29891818128`,
job `88833594271`, committed as `89bffc1` (this round's base commit).

The World Bank Pink Sheet (both direct and mirror) is still probed every
run and remains the fallback tier:
```
[gold-price] World Bank Pink Sheet, direct download — fallback leg
  parsed 798 months; latest: 2026-06 = 4228.0 USD/oz
  freshness: 51d old, 60d threshold, ok
[gold-price] GitHub mirror (datasets/gold-prices), fallback leg
  parsed 2322 months; latest: 2026-06 = 4228.0 USD/oz
  freshness: 51d old, 60d threshold, ok
```

**Claim status: VERIFIED** — live CI, not a mock; the same run also
confirmed the fallback tier still resolves correctly.

## 3. XAU-as-currency FX APIs, re-probed with a real body search

Fixed `_probe()` to optionally search the *full* response body for a
substring, not just the 200-char preview (the same limitation that made
round a's LBMA claim unverifiable). Probed exchangerate-api.com's
genuinely keyless endpoint:
```
[open.er-api.com] https://open.er-api.com/v6/latest/USD -> HTTP 200, real JSON
[open.er-api.com] '"XAU"' present anywhere in full body: False
```
**Claim status: VERIFIED** — XAU confirmed absent from the truly-open
(keyless) tier, contradicting third-party summaries that describe it as
included. This is checked against the real response, not a marketing page.

## 4. The reserves value moved to 5.1%, not toward 4.1-4.3% — and why

This is the substantive finding of this round. Compared the shipped
`public/data.json` before (`8a92e75`, World Bank leg) and after
(`89bffc1`, LBMA leg):

| | `asOf` | `value` | Q1-2026 history point (`y: 2026.0`) |
|---|---|---|---|
| Before | `2026-Q1` | 4.9% | `4.888` |
| After | `2026-Q1` | 5.1% | `5.054` |

**`asOf` is identical: `2026-Q1` in both runs.**
`reserves_incl_gold_pct_gdp()` (`scripts/series.py`) takes the most
recent quarter where reserves-excl-gold (`TRESEGUSM052N`), the gold
value, and GDP *all* have data. `TRESEGUSM052N` (IMF/BOP-sourced, its own
documented longer lag since STATUS.md §17) currently tops out at
2026-03 — so the headline ratio's "latest" point uses gold's price for
**March 2026**, regardless of which leg is active or how fresh that
leg's own most recent fetch is. The `src` string's "price 2026-07" is the
leg's own latest fetched observation (shown for transparency), not
necessarily what feeds the headline `value`.

The 4.888 → 5.054 shift is real, but it's the difference between the
World Bank's March-2026 whole-month average and LBMA's March-2026
last-trading-day price — two legitimate but different ways of
characterizing the same month — not a "the row is now more current"
effect. Confirmed by direct inspection of the `history[]` array in both
commits, not inferred from code reading alone.

**Claim status: VERIFIED** — both commits' `public/data.json` read
directly and compared point-by-point.

## 5. What this round did NOT do

Did not change `reserves_incl_gold_pct_gdp()`'s quarterly-bottleneck
design (e.g., splitting out a "gold value at current price" figure
decoupled from `TRESEGUSM052N`'s lag). That changes what the headline
number means, not just which source feeds it — flagged to the user as an
open question rather than decided unilaterally.
