# Verification log, review round `2026-07-20b` — follow-up diagnostics, run output

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-20a-verification.md` (round a, base
> commit `9bace30`, the fifth-pass close-out). Every review pass gets its
> own new file under `docs/review/` — check STATUS.md's "current
> review-round files" note (top of file) for whichever round is actually
> current when you're reading this.
>
> **Base commit:** `8c5d3bb` (HEAD of `claude/new-session-ldotj8` when this
> file was written)
> **Written:** 2026-07-20T07:25:00Z UTC
>
> **No companion `-values.md` this round.** Nothing in `public/data.json`
> changed — the only shipped code change is a cosmetic fix to
> `treasury.py`'s `verify()` print header (see below); everything else was
> diagnostic scripts, run once via a temporary push-triggered workflow,
> then deleted per this project's "diagnostic, not a feature" convention
> (`git rm`, commit `8c5d3bb`). Round a's `2026-07-20a-values.md` is still
> current for headline values.

**What this round answers (a direct follow-up on round a, not new scope):**
a reviewer flagged two loose ends in round a's own writeup — (1) `treasury.py`'s
matrix header said "Mar 2025" above cells that were actually latest-TTM
(2026-06) values, and asked for the header fixed plus a live, unambiguous
re-run showing both a genuinely-dated Mar-2025 grid and a today grid side
by side; (2) round a's §14.3 cited only *dataflow-level* metadata
(`lastUpdatedAt: 2025-06-16`) as suggestive evidence that IMF PCPS itself,
not just DBnomics' mirror, was stale — and asked for an actual direct query
of IMF's PCPS API for the PGOLD series' own latest observation date.

## 1. Header fix

`scripts/treasury.py`'s `verify()` previously printed:
```
Debt-service calibration matrix (Dalio Ch.17 US target: 22%, Mar 2025):
```
above a grid whose cells were latest-TTM (2026-06) values, not Mar-2025
values — misleading. Fixed (commit `95dd7c1`) to read:
```
Debt-service calibration matrix, LATEST TTM values (each cell is a
trailing-12-month ratio ending at its own most recent overlapping month,
NOT dated to Mar-2025 — compare against Dalio's Ch.17 US target, 22% at
his March-2025 vintage; see --verify's dated Mar-2025-vs-today section,
or docs/review/, for values actually AT that date):
```
**Claim status: VERIFIED** — code change, `scripts/treasury.py` around the
`verify()` function.

## 2. Dated debt-service matrix, both grids, live re-run

`scripts/dated_matrix_check.py` reused round c's (`TASKdrifttest.md`)
`ttm_series_full()`/CBO-projection logic, restructured into two explicit,
separately-labeled grids — one pinned to `at_month=(2025, 3)`, one to
`at_month="latest"` — so neither grid's header could misdescribe the
other's dates. Run via the temporary `followup-check.yml` workflow
(`push` trigger, since the workflow was not yet on the default branch for
`workflow_dispatch` to see it), against the same live Treasury/CBO data as
round a. Output, copied verbatim from the run log:

```
GRID 1 of 2 — AT MARCH 2025 (Dalio's stated vintage), TTM ending 2025-03:
  numerator                             total receipts    on-budget receipts     tax receipts onlyCBO Jan-2025 projected
  gross (incl. GAS)                              23.9%                 32.2%                 37.6%                 22.5%
  net-to-public (excl. GAS)                      19.0%                 25.6%                 29.9%                 17.9%
  net interest, fn900                            18.9%                 25.4%                 29.7%                 17.7%

GRID 2 of 2 — AT TODAY (latest available TTM):
  numerator                             total receipts    on-budget receipts     tax receipts onlyCBO Jan-2025 projected
  gross (incl. GAS)                              25.1%                 33.3%                 35.0%                 24.9%
  net-to-public (excl. GAS)                      19.6%                 25.9%                 27.8%                 19.4%
  net interest, fn900                            19.5%                 25.8%                 27.8%                 19.3%

  'today' = 2026-06 (TTM window ending that month)
```

**Claim status: VERIFIED** — every cell in Grid 1 (Mar-2025) and Grid 2
(today) matches §13.2's and §14.1's previously-reported numbers exactly
(gross/total: 23.9%→25.1%; net-to-public/total: 19.0%→19.6%; net
interest/total: 18.9%→19.5%; same pattern across all four denominators).
This is an independent re-derivation, not a re-assertion — it went
through freshly-fetched live Treasury/CBO data via a separate script, and
landed on the identical figures. **§13's conclusion is CONFIRMED, not
revised: no realised-data cell reproduces Dalio's 22% at his Mar-2025
vintage** — closest is gross/total at 23.9% (~1.9pt off), same as before.
See STATUS.md §15.1 for the disposition.

## 3. IMF PCPS direct gold query — three attempts, all HTTP 200 / zero series

**Attempt 1 — `gold_imf_codelist_check.py`:** recursive keyword search for
"gold" across every codelist returned by
`/structure/datastructure/IMF.RES/DSD_PCPS/~?references=all` (31
codelists). Found 49 gold-related *entries*, almost all from unrelated
codelists (BOP statistics like `F11`/`F1G`, and even company tickers —
`GLDMN` = "Goldman Sachs Group, Inc."). Correctly identified the two
PCPS-specific codelists by name — `CL_PCPS_INDICATOR` (v3.0.0) and
`CL_PCPS_COMMODITY` (v1.0.0) — but this attempt queried data using the
keyword-matched candidates directly (`GOLD`, `GOLDH`, `F11`, `GMP`, `OGP`,
`PGOLD`, `PGOLDF`, `XAU`, etc., each as `W00.<code>.USD.M`) rather than
first confirming those two codelists' actual contents. Every query:
```
status=200 obs=0 latest=None
```

**Attempt 2 — `gold_imf_codelist_check2.py`:** fetched `CL_PCPS_INDICATOR`
(v3.0.0) and `CL_PCPS_COMMODITY` (v1.0.0) directly via
`/structure/codelist/IMF.RES/{cl_id}/{version}`. `CL_PCPS_COMMODITY`
confirmed to contain:
```
PGOLD  -> "Gold"
PGOLDF -> "Gold: Fixing Committee of the London Bullion Market Association"
```
`PGOLD` is an exact match to the indicator code DBnomics itself uses.
Queried `W00.PGOLD.USD.M` and `W00.PGOLDF.USD.M` with this confirmed-correct
code — still:
```
status=200 obs=0 latest=None
```

**Attempt 3 — `gold_imf_wildcard_check.py`:** ruled out "wrong dimension
order" and "wrong COUNTRY/DATA_TRANSFORMATION guess" as explanations by
wildcarding those two dimension positions (SDMX-REST: a blank
dot-separated position means "all values"):
```
query ".PGOLD..M"      (wildcard country + transformation, monthly PGOLD)
  -> status: 200, series dim order: ['COUNTRY', 'INDICATOR', 'DATA_TRANSFORMATION', 'FREQUENCY'], series count: 0
query "W00.PGOLD..M"   (pin country=W00, wildcard transformation)
  -> status: 200, series dim order: ['COUNTRY', 'INDICATOR', 'DATA_TRANSFORMATION', 'FREQUENCY'], series count: 0
query ".PGOLD.USD.M"   (wildcard country, pin transformation=USD)
  -> status: 200, series dim order: ['COUNTRY', 'INDICATOR', 'DATA_TRANSFORMATION', 'FREQUENCY'], series count: 0
```
The returned series-dimension order matches the DSD's own declared order
exactly (confirming that part of the query was never the problem). Even
fully wildcarding COUNTRY and DATA_TRANSFORMATION — i.e. "give me *any*
monthly PGOLD series, regardless of country or price-transformation
code" — returns zero series.

**Claim status: VERIFIED (as a negative result)** — across three
independent attempts (8+ code guesses, the two confirmed-correct PCPS
codelists, and full wildcarding of the two uncertain dimensions), the
IMF PCPS `PGOLD` indicator returns genuinely zero retrievable observations
via `api.imf.org`'s SDMX 3.0 REST API, `IMF.RES/PCPS` dataflow, as tested.
This is not a code-guessing or dimension-order problem — both were
independently ruled out. The root cause (wrong dataflow version behind
`~`, a missing content-negotiation header, an access/entitlement
restriction on observation data despite public structure/metadata, or the
series being served under a different agency/dataflow) was not identified;
not pursued further given the effort already spent. See STATUS.md §15.2
for the disposition against the task's two-way conditional.
