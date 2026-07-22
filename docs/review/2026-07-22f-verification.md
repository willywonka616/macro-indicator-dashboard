# Verification log, review round `2026-07-22f` — equation #3's growth term, confirmed correct

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-22e-verification.md` (round e, base
> commit `7de91cc`, the total-debt reconciliation closure). Every review
> pass gets its own new file under `docs/review/` — check STATUS.md's
> "current review-round files" note (top of file) for whichever round is
> actually current when you're reading this.
>
> **Base commit:** `a73c4df` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §3 below)
> **Written:** 2026-07-22T16:10:00Z UTC

**What this round covers:** `TASKequation3growth.md` — before any
commentary shipped on the equation-#3 row ("Interest rate to keep debt
flat," 4.21% required vs. 3.41% actual, a −0.8pt gap), confirm which
growth rate the calculation actually uses. Dalio's Ch.3 definition is
REVENUE growth; the task's stated concern was that a default
implementation might use GDP growth instead, and that under CBO's
current-law baseline (expiring tax provisions assumed to lapse) the two
diverge by roughly the size of the observed gap — using the wrong one
would produce a plausible-looking but wrong required rate.

## 1. The growth term: verified live, not re-derived from the pipeline's own output

Read `series.py`'s `interest_rate_to_keep_debt_flat()` directly: `growth
= (rev[fy] / rev[fy - 1] - 1.0) * 100.0` where `rev =
cbo_data["rev_total"]`. Traced `rev_total` through `cbo.py`'s `FIELDS`
mapping to CBO's own `proj_rev_total` — the field name alone suggested
revenue, but this was confirmed rather than trusted on the label:

**Magnitude check** — fetched a live CBO vintage directly
(`raw.githubusercontent.com`, reachable from this sandbox without needing
`api.github.com`):
```python
data = cbo.fetch_vintage('2026-02')
# FY2025: rev_total=5,234.6   FY2026: rev_total=5,595.9   rev_gdp_share=17.541
# FY2027: rev_total=5,885.2   rev_gdp_share=17.665
```
`rev_total` runs $5.2-6.6T across the window — revenue-scale, not
GDP-scale. Backing out GDP from `rev_total / rev_gdp_share` for FY2026:
`5,595.9 / 0.17541 ≈ $31,904B ≈ $31.9T` — matching FRED's own GDP figure
for the same period (~$31.9T, independently confirmed in an earlier
round), confirming `rev_total` and GDP are two distinct, correctly-scaled
fields, not the same field mislabeled.

**Full independent recomputation** — using the raw fetched fields
directly (not calling `interest_rate_to_keep_debt_flat()` and trusting
its own output circularly):
```
growth = 5,595.9 / 5,234.6 - 1 = 6.90%
primary_deficit[2026] = -813.7  ->  gap = 813.7 / 30,172.4 * 100 = 2.696%
required = 6.90 - 2.696 = 4.204%  ≈  4.21% (matches the shipped figure to 2 decimals)
```

**No GDP-growth code path exists to have been used by mistake, either**:
`cbo.py`'s `FIELDS` dict has no raw GDP-level entry at all — only
`debt_held_by_public_gdp_share`, `rev_total_gdp_share`, and
`outlays_net_interest_gdp_share`, all *ratios*, never a GDP dollar level.
Building a GDP-growth version of this row would require fetching GDP
from an entirely different source (FRED) and was never attempted in the
existing code.

**Claim status: VERIFIED** — two independent live checks, both against
freshly-fetched CBO data, not the pipeline's own output.

## 2. Primary-deficit and starting-debt basis: re-verified, not re-cited

The existing docstring already claimed `proj_primary_deficit` (sign-
flipped) equals `outlays_total - outlays_net_interest - rev_total`
exactly — re-checked live against the same 2026-02 vintage rather than
trusting the prior round's claim:
```
outlays_total[2026] - outlays_net_interest[2026] - rev_total[2026]
  = 7,448.6 - 1,039.0 - 5,595.9 = 813.7
-primary_deficit[2026] = -(-813.7) = 813.7   <- matches exactly
```
Confirms interest is excluded from the expenses side before comparing to
revenue — Dalio's specified primary-balance basis. "Starting Debt Level"
uses `proj_debt_held_by_public_begin` directly (CBO's own field designed
for this), not a derived prior-year lookup that could introduce an
off-by-one.

**Claim status: VERIFIED** — recomputed live this round.

## 3. What was actually missing: commentary, not a fix

No calculation changed anywhere in this round. Added:
- `fetch.py`: the equation-3 row's `note` now explains that a
  required-above-actual gap (today's case) isn't a settled cushion — the
  actual rate is an average across the whole debt stock including old
  low-coupon issues, and drifts up toward the required rate as the stock
  rolls over. The reverse case (actual above required) is also handled
  explicitly.
- `equations.js`: two new caveats on the ƒx panel — one stating plainly
  that the growth term is revenue, not GDP, and why the distinction
  matters under CBO's current-law baseline; one with the fuller
  average-vs-marginal explanation.

**Live production confirmation** — run
`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29936313846`,
committed as `a73c4df` (this round's base commit). Read directly from
`public/data.json`:
```
display: "4.2%"   (unchanged, as expected — only documentation changed)
note: "... gap vs. the rate required to keep debt flat: -0.8pt: the actual
rate sits BELOW the stabilising threshold today — read carefully: not a
settled cushion. The actual figure is an AVERAGE across all outstanding
debt, including old low-coupon issues; new issuance costs more, so the
average rate drifts up as the stock rolls over, closing this gap (or
crossing it) over time even with no change in the required rate itself."
```

**Claim status: VERIFIED** — read directly from the committed
`public/data.json`, not assumed from the code diff alone.

## 4. Local + browser verification

Full existing mock-test suite re-run, no regression (confirmed via the
existing `equation #3 row` assertion, which checks `"Actual average
effective rate" in eq3_row["note"]` — still passes with the longer note).

Browser (Playwright): patched the local built `dist/data.json`, opened
the equation-#3 row's ƒx panel, screenshotted both the formula/definition
section and the caveats section — both new caveats (revenue-vs-GDP
growth, average-vs-marginal) render correctly at 500px width, no overflow,
zero console errors. Patched files discarded before committing.

## 5. Bundle size

Not separately re-measured — the only frontend change is two additional
plain-text strings in `equations.js`'s existing caveats array (no new
component, no new dependency); well within the noise floor of prior
gzip-size measurements this session.
