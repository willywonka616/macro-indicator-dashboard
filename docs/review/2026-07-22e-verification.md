# Verification log, review round `2026-07-22e` — total debt reconciliation, closed

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-22d-verification.md` (round d, base
> commit `174f680`, the quarter-bucketing bug fix). Every review pass gets
> its own new file under `docs/review/` — check STATUS.md's "current
> review-round files" note (top of file) for whichever round is actually
> current when you're reading this.
>
> **Base commit:** `7de91cc` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §§2-3 below)
> **Written:** 2026-07-22T11:45:00Z UTC

**What this round covers:** `TASKtotaldebtreconcile.md` — a hard,
explicitly time-boxed (two iterations, then stop regardless) attempt to
reconcile this pipeline's total-debt figure (`TCMDO`, 362.6% of GDP)
against Dalio's Ch.17 "Total Debt · OTHER" row (340%, US, March 2025).
The task's own brief pre-eliminated two hypotheses from an earlier round
(§14.4: total-minus-government, 263.9%; `TCMDODNS` nonfinancial-only,
256.7%) and explicitly forbade re-testing them. What remained: whether
isolating the financial sector specifically (not conflated with the
foreign-debt exclusion `TCMDODNS` also applies) or vintage timing could
close the gap.

## 1. Iteration 1 — composition, isolating ONLY the financial sector

`TCMDODNS`'s own FRED title is "Domestic Nonfinancial Sectors" — it
excludes BOTH the financial sector AND rest-of-world debt, so it never
cleanly tested "is double-counted financial-sector debt the cause,"
which is what the task specifically asked about. Researched and found a
genuinely different FRED series: `DODFS` — "Domestic Financial Sectors;
Debt Securities and Loans; Liability, Level" — which isolates *only* the
financial sector, keeping foreign debt in.

Added a live diagnostic to `fetch.py --verify` (not previously present)
computing `TCMDO − DODFS`. Live CI (run `29916180176`, commit `8224069`):
```
TCMDO: 362.6% of GDP as of 2026-01-01
TCMDODNS: 256.7% of GDP as of 2026-01-01 (excludes BOTH financial AND foreign — already eliminated, §14.4)
DODFS: 81.9% of GDP as of 2026-01-01 (financial sector ONLY)
TCMDO minus DODFS (excl. ONLY financial, foreign still in): 280.7% of GDP
```
**Eliminated.** 280.7% is 59.3pt short of 340% — *worse* than TCMDO's own
22.6pt gap, not better. Financial-sector double-counting is not the
source of the discrepancy.

**Claim status: VERIFIED** — `DODFS` confirmed to exist and resolve via a
live FRED fetch, not assumed from the series ID alone.

## 2. Iteration 2 — vintage, including a self-caught mistake

Dalio's snapshot is March 2025 (~2025-Q1). First attempt at this check
(same commit `8224069`) divided 2025-Q1 `TCMDO` by the CURRENT (2026-Q1)
GDP observation — a mismatched-vintage pairing. Live CI showed:
```
TCMDO at 2025-Q1 (Dalio's snapshot vintage), current GDP: 341.8% of GDP as of 2025-01-01
```
**This number is wrong and was not reported anywhere as a finding** —
recognized immediately as an apples-to-oranges comparison (older, smaller
debt level divided by a newer, larger GDP figure produces an artificially
lower, misleadingly-341.8%-looking ratio, not a genuine vintage
reconciliation). Fixed (commit `b5305b7`) to pair both series at the same
quarter. Live CI (run `29916494182`, commit `b5305b7`):
```
TCMDO at 2025-Q1, GDP ALSO at 2025-Q1 (same-quarter pairing): 362.5% of GDP as of 2025-01-01
```
**Eliminated.** 362.5% (March 2025) vs. 362.6% (today) — a 0.1pt
difference. Vintage explains essentially none of the 22.6pt gap.
Independently cross-checked against the already-shipped "Total debt (all
sectors)" row's own chart history, read directly from `public/data.json`
without any new fetch: `{"y": 2025.0, "v": 362.514}` — matches the
corrected live figure to within rounding.

**Claim status: VERIFIED**, with the flawed first draft disclosed
explicitly rather than quietly discarded — both the wrong (341.8%) and
corrected (362.5%) figures are part of this record.

## 3. Production runs

- Run 1 (financial-sector + first vintage draft): `https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29916180176`, job `88910455452`, committed as `e0b61db`.
- Run 2 (vintage-pairing fix): `https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29916494182`, job `88911485537`, committed as `7de91cc` (this round's base commit).

Both non-fatal diagnostic additions to `--verify` only — no change to what
`fetch.py --force` ships; `public/data.json`'s "Total debt (all sectors)"
row is unchanged by this round (still live `TCMDO`, 362.6%).

## 4. Closed: known difference, ~23pts, unreconciled — no third iteration

Per the task's own acceptance criteria. Full hypothesis table:

| Hypothesis | Result | Verdict |
|---|---|---|
| Total debt minus government's own debt | 263.9% (−76.1pt) | Eliminated, §14.4 (prior round) |
| Nonfinancial-sectors-only (`TCMDODNS`) | 256.7% (−83.3pt) | Eliminated, §14.4 (prior round) |
| Isolated financial-sector-only (`TCMDO − DODFS`) | 280.7% (−59.3pt) | Eliminated, this round |
| Vintage (same-quarter TCMDO/GDP at 2025-Q1) | 362.5% (+22.5pt) | Eliminated, this round |

Most probable residual cause, unchanged from the task's own framing and
nothing found here to contradict it: Dalio's 340% is most likely
Bridgewater's own internal debt aggregate, on a basis public FRED/Z.1
series don't reproduce by construction.

`STATUS.md` §9's calibration table row relabeled to
"known difference, unreconciled after bounded investigation" (not left
looking like an untriaged mismatch); §14.4's own text and the "three rows
needed more" bullet list both updated with forward pointers to this
closure. `TCMDO` (362.6%) continues to ship unchanged — this round is a
labelling correction, not a source change, per the task's explicit
instruction.

## 5. Local verification

No code paths that ship in `data.json` were touched — only diagnostic
`print()` statements inside `verify()`. Full existing mock-test suite
re-run to confirm no regression:
```
ALL CHECKS PASSED (incl. freshness guard, 3-tier fallback, provenance assertions, CBO projections)
quarterly_last() regression: correctly picked the true latest month (March) for 2026-Q1
```
