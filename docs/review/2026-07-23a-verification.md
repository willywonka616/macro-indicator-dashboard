# Verification log, review round `2026-07-23a` — central bank panel raw values

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-22g-verification.md` (round g, base
> commit `c7cdbe8`, retiring the undated manual values). Every review
> pass gets its own new file under `docs/review/` — check STATUS.md's
> "current review-round files" note (top of file) for whichever round is
> actually current when you're reading this.
>
> **Base commit:** `9b7b11d` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §1 below)
> **Written:** 2026-07-23T04:30:00Z UTC

**What this round covers:** `TASKcbrawvalues.md` — re-reading Dalio's
Ch.17 central bank gauge table found the dashboard under-using it: a
"Reading Today" raw-value column sits next to every Z-score, four of
which weren't carried at all, and most leaf inputs are ordinary
measurable statistics, not model output. This round adds live raw values
alongside the frozen (March 2025) book figures — **the Z-score wall
itself is completely untouched** (verified by direct diff, §3 below).

## 1. Live CI run: every new FRED series confirmed, one real endpoint resolved

Triggered `workflow_dispatch` on commit `d3c15cc`. Read directly from the
CI job log (run `29979098020`), not assumed:

```
M2SL: 'M2', units='Billions of Dollars', freq=M, latest 2026-05-01 = 23052.3
BOGMBASE: 'Monetary Base: Total', units='Billions of Dollars', freq=M, latest 2026-05-01 = 5538.6
GDPC1: 'Real Gross Domestic Product', units='Billions of Chained 2017 Dollars', freq=Q, latest 2026-01-01 = 24180.419
A939RX0Q048SBEA: 'Real gross domestic product per capita', units='Chained 2017 Dollars', freq=Q, latest 2026-01-01 = 70583.0
FEDFUNDS: 'Federal Funds Effective Rate', units='Percent', freq=M, latest 2026-06-01 = 3.63
RESPPLLOPNWW: 'Liabilities and Capital: Liabilities: Earnings Remittances Due to the U.S. Treasury: Wednesday Level', units='Millions of U.S. Dollars', freq=W
  last 6 observations: 2026-06-10: -237738.0 | 2026-06-17: -236697.0 | 2026-06-24: -236241.0
                        2026-07-01: -235615.0 | 2026-07-08: -235052.0 | 2026-07-15: -234254.0
```

All five new FRED series resolve cleanly with sane values and units — no
schema surprises. `RESPPLLOPNWW` also resolves: negative and shrinking in
magnitude over the last 6 weeks (a real, live-confirmed trend — see
STATUS.md §29.2 for the interpretation and why it isn't shipped as a live
row this round).

**Treasury's MSPD maturity-profile probe (§21, never previously confirmed
live from this dev sandbox) also resolved** — the first candidate,
`mspd_table_3_market`, returns individual-security rows with both
`maturity_date` and `outstanding_amt`:
```
fields: ['record_date', 'security_type_desc', 'security_class1_desc', 'security_class2_desc',
         'series_cd', 'interest_rate_pct', 'yield_pct', 'issue_date', 'maturity_date',
         'interest_pay_date_1..4', 'issued_amt', 'inflation_adj_amt', 'redeemed_amt',
         'outstanding_amt', 'src_line_nbr', 'record_fiscal_year', ...]
maturity field: maturity_date -> ['2026-07-28', '2026-07-02', ... 30 distinct dates shown]
```
A real, actionable finding — see STATUS.md §29.3 for why this wasn't
built into a shipped "Current borrowing need" row this round (a
substantial follow-up in its own right, recommended as a focused future
task).

**Claim status: VERIFIED** — read directly from the CI job log, not
assumed from documentation research alone.

## 2. Shipped values (committed `public/data.json` at `9b7b11d`)

| Row | Book (Mar 2025) | Live (2026) | asOf |
|---|---|---|---|
| Unbacked money | 71% of GDP | **71.2%** | 2026-Q1 |
| — monetary base comparison (note, not primary) | — | 17.1% of GDP | 2026-Q1 |
| Reserves / money | (Z only) | **6.4%** | 2026-03 |
| Real cash return (long-term, ann) | −1.4%/yr | **+1.0%** | avg 1954-07–2026-06 |
| Real gold return (long-term, ann) | +9.8%/yr | **+8.3%** | CAGR 1968-04–2026-07 |
| Inflation volatility | 1.4% ann | **2.0%** | trailing 10y to 2026-06 |
| Volatility of growth (ann), context | 2.2% | **2.5%** | trailing 10y to 2026-Q1 |
| GDP per capita growth, context | 1.5% | **2.0%** | CAGR 1947-Q1–2026-Q1 |
| Months of reserve sales, context | (Z only) | **n/a — no sustained sales** | 2026-03 |
| Reserve FX / financial center | 57.0% | *(manual this run — COFER's own live fetch is currently frozen, pre-existing)* | — |
| Central bank profitability | −0.2% of GDP | *(not shipped live — see STATUS.md §29.2)* | — |

**Real cash return flips sign** (book −1.4%, live +1.0%) — a genuine,
unforced divergence, not a rounding difference. Not investigated further
by design: TASKcbrawvalues.md's explicit instruction is to report a
defensible method's actual reading, not to search for a window that
reproduces his figure. Every other row lands within a few points.

**Claim status: VERIFIED** — read directly from the committed
`public/data.json`, not from memory or a mock.

## 3. Z-score wall: verified byte-identical

```python
def collect_z(gauge):
    return [(r['label'], r['z']) for r in gauge['rows']]
# before (commit 95b59b2) vs after (this round): identical, in order, both gauges
```
`govGauge`: `[('Current borrowing need', 2.4), ('— if rollover problems', 2.5),
('Projected borrowing need', 2.8), ('— if rollover problems', 2.9), ('Debt in own currency', -2.0)]`
`cbGauge`: `[('Central bank profitability', 0.1), ('— if rates rise', 0.2),
('Unbacked money', 0.3), ('Reserves / money', 1.5), ('Currency as storehold', -2.0),
('Reserve FX / financial center', -3.3), ('Rule of law', -1.1), ('Inflation volatility', -2.1)]`

Zero Z-scores added, removed, or recomputed. The two new `components`
(real cash/gold return) carry no `z` of their own by design — see
STATUS.md §29.4 for why two book-cited Z-scores ("History of Losses for
Savers: 1.1z," "Months of reserve sales: 0.0z") were deliberately NOT
added: neither is independently verifiable against the book from this
session, so both raw-value sets ship as unscored context instead.

**Claim status: VERIFIED** — direct diff of the actual committed files,
not a description of intent.

## 4. Local + browser verification

Mock test suite extended with synthetic (but trending, not flat) FRED
series for `M2SL`/`BOGMBASE`/`GDPC1`/`A939RX0Q048SBEA`/`FEDFUNDS` — a
key-naming bug (`cb_live["reserve_fx_share"]` vs. the row's actual key
`reserve_fx_financial_center`) was caught immediately by the new
assertions and fixed before any live run. Full suite passes, including
new checks: Z-scores unchanged, live values populated with sane
magnitudes, the Reserve-FX row's live value matches the reserve-currency
panel's own COFER row exactly (not a second fetch), storehold components
carry no `z`, reserve runway correctly reads "no sustained sales" against
monotonically-rising synthetic reserves, and CB profitability stays
book-only.

Browser (Playwright): screenshotted the CB and government gauge panels
twice — once against a synthetic build (fully-populated live values, all
computed from realistic trending mock data) and once against the real
production `data.json` after the live CI run. Both render book vs. live
vs. Z distinctly, the new "supporting context" section appears under the
main rows, and components render as an indented sub-list under "Currency
as storehold." No overflow, no console errors at 900–1400px width.

## 5. Bundle size

Not separately re-measured — no new dependency; `GaugeRow.jsx` grew from
a ~35-line to a ~110-line component (still no new imports beyond the
already-present `Tag.jsx`), well within the noise floor of prior
gzip-size measurements this session.
