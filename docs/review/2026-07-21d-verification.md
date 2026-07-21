# Verification log, review round `2026-07-21d` — CBO 10-year projections (Dalio's forward-looking equations)

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-21c-verification.md` (round c, base
> commit `0873732`, the equation-button pass). Every review pass gets its
> own new file under `docs/review/` — check STATUS.md's "current
> review-round files" note (top of file) for whichever round is actually
> current when you're reading this.
>
> **Base commit:** `2a0a072` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §3 below)
> **Written:** 2026-07-21T18:15:00Z UTC

**What this round covers:** `TASKprojections.md` — a projection layer
from CBO's published baseline (the same source Dalio himself uses, per
his book's footnote 20), deliberately run after the equation-button pass
(round c) since the projection rows are exactly what its "Dalio's
formula" blocks describe. Three built items: (1) live 10-year debt/GDP
and debt/revenue projections, extending the dashboard's existing
sparklines forward; (2) Dalio's equation #3 (the interest rate that
would keep debt flat), computed from CBO's baseline and compared against
the actual average effective rate (Treasury, live); (3) replacing the
hand-carried, undated 122% debt projection with a live CBO fetch.

## 1. A better source than the task assumed

The task's brief assumed downloadable xlsx files from cbo.gov, with the
explicit instruction to "verify the current URLs and file formats rather
than assuming." Doing so found CBO's own machine-readable data mirror on
GitHub, `US-CBO/cbo-data` — an official CBO product ("for use by
programmers, AI agents, and automated systems," per its README) — instead
of scraping xlsx. It publishes exactly the needed dataset
(`ten_year_budget`, publication #51118) as clean, versioned CSVs, one per
vintage.

cbo.gov itself is not reachable from this project's dev sandbox (proxy
policy denial — confirmed live: `curl` to `www.cbo.gov` returns
`CONNECT tunnel failed, response 403`, and the proxy's own status
endpoint logs `"connect_rejected ... policy denial"` for the host), same
as `github.io` was blocked earlier this session. `raw.githubusercontent.com`
and `api.github.com` ARE reachable from a normal CI runner's unrestricted
network — the same "not reachable from dev, but CI works fine"
asymmetry every other source in this project has (Treasury's own module
docstring states this explicitly).

**Verified against three independently-known facts before trusting the
new source:**
```
vintage 2024-06, FY2034 debt/GDP: 122.4%   (Dalio's own stated 122%)
vintage 2025-01, FY2035 debt/GDP: 118.5%   (task file's own stated 118%)
vintage 2026-02, FY2026 debt/GDP: 100.6%   (~101%, independently reported)
vintage 2026-02, FY2036 debt/GDP: 120.2%   (~120%, independently reported)
```
All four fetched live via `raw.githubusercontent.com/US-CBO/cbo-data/main/data/budget/ten_year_budget/annual_fy_<vintage>.csv`.

## 2. What's built

Three rows in the Government debt panel (`scripts/fetch.py`,
`scripts/series.py`, `scripts/cbo.py`, `scripts/treasury.py`):

1. **"Debt, 10-yr projection"** — was `manual` (hand-carried 122%, no
   date, one of the 11 dateless `manual.json` values §19.2 found), now
   `tag: "projection"`, live from CBO's current vintage. Its own
   dedicated chart extends the existing live debt/GDP history with CBO's
   projected annual tail.
2. **"Debt vs revenue"** (existing live row) — chart gains the same kind
   of projected tail (debt held by the public ÷ total revenue, both from
   CBO); the row's headline value/`asOf` are unchanged, still the live
   current figure.
3. **"Interest rate to keep debt flat (Dalio eq. #3)"** — new,
   `tag: "projection"`, computed entirely from CBO's own baseline
   (`series.py`'s `interest_rate_to_keep_debt_flat()`):
   ```
   i_required = Revenue Growth − (Future Expenses Excl. Interest − Future Revenue) / Starting Debt Level
   ```
   Every term is a CBO-published field: Revenue Growth (`proj_rev_total`
   year-over-year), the primary-deficit term (`proj_primary_deficit`,
   sign-flipped — verified live to equal `outlays_total −
   outlays_net_interest − rev_total` exactly, to the dollar), Starting
   Debt Level (`proj_debt_held_by_public_begin`). Compared against
   `treasury.py`'s new `avg_interest_rate_marketable()` — Treasury's own
   published average rate on marketable debt, live.

**Deliberately not extended:** "Net interest (to the public)"'s chart —
CBO's own "net interest" concept doesn't cleanly match this row's
precise net-to-public, GAS-excluded definition; extending it would
misrepresent both. Recorded as a deliberate scope decision.

## 3. Full production run: `update-data.yml`, `workflow_dispatch`

`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29855636492`,
job `88719132639`, 2026-07-21 18:04-18:06 UTC, committed as `2a0a072`.
No CBO-fallback warning appeared in the log — confirming `api.github.com`
(needed for the vintage-listing call) IS reachable from CI's network,
unlike this project's dev sandbox. Values read directly from the
committed `public/data.json`:

```
provenance.cboVintage: "CBO 10-Year Budget Projections, February 2026 baseline (FY2025–FY2036, current law)"

debt_to_revenue        | 576% | live       | 2026-Q1 | 52 history pts (11 of them projected)
debt_10yr_projection   | 120% | projection | FY2036  | 236 history pts (live quarterly + CBO annual tail)
interest_rate_to_keep_debt_flat | 4.2% | projection | FY2026 | 11 history pts (fully projected)
```

`interest_rate_to_keep_debt_flat`'s full note (the equation-#3 diagnostic
comparison, "the single most useful thing this feature can show" per the
task):
```
CBO 10-Year Budget Projections, February 2026 baseline (FY2025–FY2036,
current law). Actual average effective rate on marketable debt held by
the public (Treasury, live, 2026-06): 3.41% — gap vs. the rate required
to keep debt flat: -0.8pt (debt burden trending down at the actual rate,
all else equal).
```

`debt_to_revenue`'s projected tail, first and last points (matches the
values independently computed during local research, to the basis
point):
```
{'y': 2026.667, 'v': 573.55, 'projected': True}
...
{'y': 2036.667, 'v': 676.47, 'projected': True}
```

**Claim status: VERIFIED** — live `workflow_dispatch` run, not a mock;
`public/data.json` at commit `2a0a072` reflects exactly this, including
a genuine current comparison (CBO's required rate vs. Treasury's actual
rate) neither side of which was known in advance.

## 4. Local + browser verification

Local: extended the scratchpad mock test with real CBO data (fetched via
`raw.githubusercontent.com`, reachable from this sandbox; stubbed as
`current_vintage_data()`'s return value, since only the vintage-*listing*
call needs `api.github.com`). Confirmed all three rows appear correctly
on a healthy run, and a simulated CBO outage correctly falls the
projection row back to `manual`, omits the equation-#3 row entirely,
strips the projected tail from `debt_to_revenue`, and records the
mismatch in `provenance.fallbacksFired` (reusing round b's mechanism
unchanged — confirms it generalises to a new fallback-capable row).

Browser (Playwright, same approach as round c): screenshots confirmed
the dashed projected tail, shaded forward region, "PROJECTED" label, and
hollow end-marker all render correctly on both "Debt vs revenue" and
"Debt, 10-yr projection"; the equation-#3 row's fully-projected chart
(no historical portion) renders as an all-dashed line with the label at
the chart's left edge. Re-ran round c's 390px overflow check against all
three new rows and their equation-button panels — zero overflow, zero
console errors.

## 5. Bundle size

```
                JS (gzip)   CSS (gzip)
before          56.08 kB    2.87 kB
after           57.04 kB    2.87 kB
Δ               +0.96 kB    +0 kB
```
No new runtime dependency — `Chart.jsx`'s projected-segment rendering is
pure SVG, reusing the existing polyline/polygon primitives.

**Claim status: VERIFIED** — `npm run build` output compared directly,
before/after, via `git stash` isolation of the frontend-only diff.
