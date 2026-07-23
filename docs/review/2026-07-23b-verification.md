# Verification log, review round `2026-07-23b` — government borrowing need, live

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-23a-verification.md` (round a, base
> commit `9b7b11d`, central bank panel raw values). Every review pass
> gets its own new file under `docs/review/` — check STATUS.md's
> "current review-round files" note (top of file) for whichever round is
> actually current when you're reading this.
>
> **Base commit:** `5d8826a` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> fourth and final live `update-data.yml` run this round, documented in
> §1-2 below)
> **Written:** 2026-07-23T05:45:00Z UTC

**What this round covers:** `TASKborrowingneed.md` — the MSPD maturity
endpoint resolved in the prior round; this task uses it (plus Treasury
deficit/revenue data) to make the government gauge's borrowing-need rows
live, the last big book-transcribed numbers on the dashboard. **The
Z-score wall is completely unchanged** (verified by direct diff, §3).

## 1. Four live exploratory rounds — real bugs found and fixed before anything shipped

This dev sandbox cannot reach `api.fiscaldata.treasury.gov`, so the
construction had to be verified live in CI, per the task's own §1
("verify, don't assume"). Four round trips, each fixing a real,
previously-unknown issue:

**Round 1** (`workflow_dispatch` on `32193b3`) — confirmed
`mspd_table_3_market`'s real schema live:
```
record_date used: 2026-06-30
fields: ['record_date', 'security_type_desc', 'security_class1_desc',
         'security_class2_desc', ..., 'issue_date', 'maturity_date',
         'outstanding_amt', ...]
distinct security_class1_desc: ['Bills Maturity Value', 'Notes', 'Bonds',
  'Inflation-Protected Securities', 'Floating Rate Notes',
  'Federal Financing Bank', 'Total Marketable']
```
and found `government_deficit_monthly()`'s original field-matching
against `mts_table_1` resolved **zero** rows.

**Round 2** (`1aa0a3b`) — dumped `mts_table_1`'s real schema:
```
fields: record_date, ..., classification_desc, current_month_gross_rcpt_amt,
        current_month_gross_outly_amt, current_month_dfct_sur_amt, ...
distinct classification_desc: ['March', 'April', 'May', 'June',
  'Year-to-Date', 'FY 2026', ...]
```
Revealed the real structure: one row PER PERIOD, receipts/outlays/deficit
as columns on that row — not separate receipts-vs-outlays rows, which
the original function assumed. Also found the MSPD individual-rows sum
($90,379,008 raw units) vs. the table's own "Total Marketable" row
($31,085,831 raw units, confirming outstanding_amt is in **millions of
dollars**) — a **2.9x discrepancy**, same date, same table.

**Round 3** (`d548c70`) — found the actual bugs:
```
last 6 months (current_month_dfct_sur_amt, before the sign fix):
  ...(all positive, before an incorrect flip made the TTM total negative)
resolved: 136 months, latest 2026-06 = $-344.8B
TTM deficit, latest 2026-06 = $-1829.2B   <- a "surplus," contradicting known reality
```
and found the concrete shape of the MSPD gap: CUSIP `912797RF6` appears
across 4 rows (issue_dates 2025-07-10, 2026-01-08, 2026-04-09,
2026-05-28), all sharing `maturity_date: 2026-07-09` — a Treasury
reopening pattern, the leading hypothesis for the ~2.9x gap.

**Round 4** (`6775e83`, committed as `5d8826a`) — fixed the deficit sign
(removed an incorrect flip) and tested CUSIP deduplication directly:
```
last 6 months (after the fix, positive = deficit): all positive
TTM deficit, latest 2026-06 = $1829.2B   <- matches the task's own "~$1.9T" almost exactly
TTM revenue, same month = $5377.8B -> current borrowing need = 34.0% of revenue (book: 39%)

after deduping by CUSIP (keep max outstanding_amt per CUSIP): 473 rows,
sum 90,379,008 RAW units   <- IDENTICAL to the pre-dedup sum
```
The dedup sum being byte-identical to the naive sum **disconfirms** CUSIP
reopening as the (sole) cause of the 2.9x gap — a real negative result,
not a wasted round: it stops this project from shipping a "fix" that
doesn't actually fix anything.

**Claim status: VERIFIED** — every figure above read directly from CI job
logs, not assumed or reconstructed from documentation.

## 2. What shipped, and what stayed manual

Committed `public/data.json` at `5d8826a`:

```json
"borrowing_need": {"z": 2.4, "book": {"display": "39% of revenue", "asOf": "2025-03"},
  "live": {"display": "34%", "value": 34.0, "asOf": "2026-06", ...}}
"borrowing_need_stress": {"z": 2.5, "book": {"display": "239% of revenue", "asOf": "2025-03"}}
  # no "live" key — stays manual
"borrowing_need_projected": {"z": 2.8, "book": {"display": "44% of revenue", "asOf": "2025-03"},
  "live": {"display": "38%", "value": 37.5, "asOf": "FY2036", ...}}
"borrowing_need_projected_stress": {"z": 2.9, "book": {"display": "254% of revenue", "asOf": "2025-03"}}
  # no "live" key — stays manual
```

`provenance.fallbacksFired` contains only the pre-existing, unrelated
COFER entry — **no** fallback recorded for either borrowing-need row,
confirming both shipped live cleanly with no error.

**Why the two roll-problems rows stay manual**: they need debt maturing
within 12 months from the same MSPD table whose individual-rows sum has
the unresolved ~2.9x discrepancy (§1). The maturing-share computed from
that same (still-unexplained) data was ~11%, implausibly low against the
well-known fact that US Treasury Bills alone (~$6-7T, entirely maturing
within a year) should already put the true maturing share well above
that — a second, independent signal something in the individual-row
reading isn't right yet. Per the task's own "cap it... document the
residual" instruction (TASKborrowingneed.md §1), this is not resolved
further this round — see STATUS.md §30.2/§30.3 for the full trail.

**Claim status: VERIFIED** — read directly from the committed
`public/data.json`, not from memory or a mock.

## 3. Z-score wall: verified byte-identical

```python
def collect_z(gauge):
    return [(r['label'], r['z']) for r in gauge['rows']]
# before (commit e570944) vs. after (this round): identical, in order, both gauges
```
`govGauge`: `[('Current borrowing need', 2.4), ('— if rollover problems', 2.5),
('Projected borrowing need', 2.8), ('— if rollover problems', 2.9), ('Debt in own currency', -2.0)]`
— unchanged. `cbGauge` — also unchanged (this round didn't touch it, but
re-verified anyway since the same diff script checks both).
`govGauge.overall`: `2.4` → `2.4`, unchanged.

**Claim status: VERIFIED** — direct diff of the actual committed files.

## 4. Local + browser verification

Mock test suite extended: `T.deficit_ttm_dollars` stubbed proportioned
to ~35% of the existing revenue stub (book target 39%); asserts both
live rows' values, both roll-problems rows correctly having no `"live"`
key, and Z-scores unchanged. A dedicated sanity-band test re-stubbed the
deficit at 500% of revenue (an absurd, clearly-wrong figure) and
confirmed the row correctly fell back to manual and was recorded in
`fallbacksFired` — the guard actually fires, not just exists in code.

Browser (Playwright): screenshotted the government gauge panel against
both a synthetic build and the real production `data.json` — book/live/Z
render distinctly, the roll-problems rows show their residual note in
place of a live value, and clicking the new "ƒx" button on "Current
borrowing need" opens a full definition panel (Dalio's Ch.3 "indicator
#1" framing, the deficit/revenue formula, both terms' live sources, and
the March-2025 vintage caveat) — `GaugeRow.jsx` did not render this
button at all before this round.

## 5. Bundle size

Not separately re-measured — the only new frontend logic is
`EquationButton` (already existed, reused as-is) now also rendered from
`GaugeRow.jsx`, plus two new `equations.js` entries (plain data, no new
component). Well within the noise floor of prior gzip-size measurements
this session.
