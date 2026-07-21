# Verification log, review round `2026-07-21b` — manual-value freshness guard + provenance assertion

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-21a-verification.md` (round a, base
> commit `b0e8827`, the manual-INPUT-not-OUTPUT fallback pass). Every
> review pass gets its own new file under `docs/review/` — check
> STATUS.md's "current review-round files" note (top of file) for
> whichever round is actually current when you're reading this.
>
> **Base commit:** `3335451` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §2 below)
> **Written:** 2026-07-21T07:15:00Z UTC

**What this round covers:** two more classes of silently-wrong-data,
distinct from the frozen-SOURCE class §17's freshness guard already
covers. (1) A hand-entered manual value with a date is exactly as capable
of going stale as a fetched one — `data/manual.json`'s `goldPriceManualFallback`
(added in round a) had no threshold at all. Extend the freshness guard to
manual inputs, and check whether any other manual value lacks a date
entirely. (2) A fallback firing (live → manual/manual_price) was only
ever visible as an incidental `print()` line — nothing asserted the
shipped tag matched what a healthy run should have produced. Add a
per-row provenance assertion that fails or logs loudly when a fallback
fires.

## 1. Manual-value freshness thresholds (series.py)

Three new thresholds, each reasoned from what the value stands in for:
```python
GOLD_MANUAL_PRICE_FRESH_DAYS = FRESHNESS_DAYS_BY_FREQ["Monthly"]  # 60d
CBRESERVES_MANUAL_FRESH_DAYS = COFER_FRESH_DAYS                   # 270d
MANUAL_FRESH_DAYS = 180                                            # catch-all
```
Checked with the non-raising `S.freshness()`, not `require_fresh()` —
deliberately non-fatal (see STATUS.md §19.1 for the full reasoning: these
are already the fallback of last resort, so failing the build over their
own staleness would defeat the "degrade rather than break" point of
having a fallback at all). Staleness triggers `fetch.py`'s new
`loud_warn()`:
```python
def loud_warn(msg: str):
    print(f"\n{'!' * 70}\nWARNING: {msg}\n{'!' * 70}\n")
    print(f"::warning::{msg}")
```
— a console banner AND a GitHub Actions `::warning::` annotation, which
renders as a real Annotation on the run's Checks page. Wired in at all
three places a manual value can actually ship (gold-price manual input,
full-manual gold output via `lastChecked`, COFER manual fallback) and
unconditionally during `--verify` via a new `audit_manual_values()`, so
drift is visible during routine health checks too, not only when a
fallback actually fires.

## 2. Dateless-value audit

```
Manual-value freshness audit (data/manual.json):
  goldPriceManualFallback.asOf                            2026-07-20      1d old   60d threshold  ok
  reserveCurrency.cbReserves.asOf                         2026-Q1       201d old  270d threshold  ok
  lastChecked (governs every dateless value below)        2026-07-18      3d old  180d threshold  ok
  11 manual values have NO individual date, relying solely on lastChecked above:
    govAssetsMinusDebt
    cboProjection
    holders.centralBank
    holders.domestic
    holders.abroad
    shareHardFX
    sovereignWealth
    reserveCurrency.trade
    reserveCurrency.equity
    reserveCurrency.debt
    reservesInclGoldFallback (no own asOf; last-resort only — see its own note)
```
**Finding: 11 of 14 manual.json values have no date of their own**, and
rely solely on the single top-level `lastChecked` for any notion of "how
old is this" — real gap for the ones with an actual natural update
cadence (TIC holder data, CBO baselines), currently indistinguishable in
age from static facts like `sovereignWealth: "None"`. Recorded, not
fixed this round (would require sourcing 11 new independently-tracked
dates — out of scope for a freshness-guard pass). See STATUS.md §19.2.

## 3. Per-row provenance assertion (fetch.py)

```python
def assert_provenance(fallbacks_fired, row_label, expected_tag, actual_tag, reason):
    if actual_tag == expected_tag:
        return
    entry = {"row": row_label, "expectedTag": expected_tag, "actualTag": actual_tag, "reason": reason}
    fallbacks_fired.append(entry)
    loud_warn(f"provenance mismatch on '{row_label}': expected tag "
              f"'{expected_tag}', shipped '{actual_tag}' — a fallback fired. "
              f"Reason: {reason}")
```
Called at both fallback-capable rows (gold reserves, COFER); results
collected in a new `country.provenance.fallbacksFired` array, empty on a
fully-healthy run. Deliberately non-fatal — same reasoning as §1: these
two rows exist specifically so a dead source degrades the site rather
than takes it down, and failing the build on every mismatch would defeat
that. The assertion's job is to make a fallback firing undeniable
(structured field + loud warning), not to treat it as itself an error.
See STATUS.md §19.3.

## 4. Verified locally

Extended the scratchpad mock test with three assertions: a fully-live run
produces `provenance.fallbacksFired == []`; the manual-price scenario
records a `manual_price` mismatch entry; the full-manual scenario records
a `manual` mismatch entry. All three pass; loud-warning banners and
`::warning::` annotations print correctly in each case.

## 5. Full production run: `update-data.yml`, `workflow_dispatch`

Two runs were needed (same race pattern as round a: a `workflow_dispatch`'s
own `git push` losing against a STATUS.md commit pushed moments later
from this session). The clean run
(`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29809275699`,
job `88566499233`, 2026-07-21 07:07-07:09 UTC) pushed as `3335451`.
Verbatim `--verify` output (manual-value audit, unconditional):
```
Manual-value freshness audit (data/manual.json):
  goldPriceManualFallback.asOf                            2026-07-20      1d old   60d threshold  ok
  reserveCurrency.cbReserves.asOf                         2026-Q1       201d old  270d threshold  ok
  lastChecked (governs every dateless value below)        2026-07-18      3d old  180d threshold  ok
  11 manual values have NO individual date, relying solely on lastChecked above: ...
```
Verbatim build-step output (both known fallbacks correctly produce loud
warnings, unchanged headline values):
```
Gold price unavailable/stale, patching a manual price input across the gap: freshness guard: gold price (DBnomics PCPS) latest observation is (2025, 6) (415d old, today 2026-07-21) — exceeds the 60d threshold for this series' cadence. The source is likely dead or frozen, not just running a normal lag.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
WARNING: provenance mismatch on 'Reserves incl. gold (market)': expected tag 'live', shipped 'manual_price' — a fallback fired. Reason: live gold price and/or holdings fetch failed or exceeded its freshness threshold
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

##[warning]provenance mismatch on 'Reserves incl. gold (market)': expected tag 'live', shipped 'manual_price' — a fallback fired. Reason: live gold price and/or holdings fetch failed or exceeded its freshness threshold
IMF COFER unavailable, using manual value: freshness guard: IMF COFER USD share latest observation is 2025-Q1 (566d old, today 2026-07-21) — exceeds the 270d threshold for this series' cadence. The source is likely dead or frozen, not just running a normal lag.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
WARNING: provenance mismatch on 'World CB reserves in USD': expected tag 'live', shipped 'manual' — a fallback fired. Reason: live IMF COFER fetch failed or exceeded its freshness threshold
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

##[warning]provenance mismatch on 'World CB reserves in USD': expected tag 'live', shipped 'manual' — a fallback fired. Reason: live IMF COFER fetch failed or exceeded its freshness threshold
Wrote public/data.json — generatedAt 2026-07-21T07:09:57Z
```
The `##[warning]` lines are GitHub's own rendering of the `::warning::`
annotations — real Annotations on the Checks page, not just log text.

**Claim status: VERIFIED** — live `workflow_dispatch` run, not a mock;
`public/data.json` at commit `3335451` reflects exactly this, including
the new `provenance.fallbacksFired` field. See
`docs/review/2026-07-21b-values.md` for the extracted headline values.
