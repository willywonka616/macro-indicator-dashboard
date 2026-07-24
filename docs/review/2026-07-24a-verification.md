# Verification log, review round `2026-07-24a` — native-first SDMX migration

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-23d-verification.md` (round d, base
> commit `9b7c850`, euro-area live sourcing attempted, all rows manual).
> Every review pass gets its own new file under `docs/review/` — check
> STATUS.md's "current review-round files" note (top of file) for
> whichever round is actually current when you're reading this.
>
> **Base commit:** `3fb9c14` (HEAD of `claude/new-session-ldotj8` when this
> file was written)
> **Written:** 2026-07-24T02:40:00Z UTC

**What this round covers:** `TASKnativesources.md` — native-first policy
+ migration. Code commits `29a3ea1` (the migration itself) and `16d4b3a`
(two bug fixes the first live run surfaced). Two `workflow_dispatch`
rounds:
- Run 1: `30061177601` (commit `29a3ea1`) → committed as `cbdaa05`.
- Run 2: `30061697837` (commit `16d4b3a`, the fixes) → committed as `3fb9c14`.

## 1. Run 1: what resolved, what a fresh threshold got wrong

Verbatim from job `89382957690`'s log:

```
[Eurostat] native + mirror fallback: gov_10q_ggdebt
  general government debt (S13) % GDP: 89.4% as of 2026-Q1 (geo=EA20, source=native, 105 pts)
    at Dalio's vintage (2025-Q1): 87.7% (book target: 85%, general-vs-central identification)
  central government debt (S1311) % GDP: 79.1% as of 2026-Q1 (geo=EA20, source=native, 105 pts)
    at Dalio's vintage (2025-Q1): 77.6% (book target: 85%, general-vs-central identification)

[Eurostat] native + mirror fallback: gov_10q_ggnfa
  central govt interest / revenue: FAILED: [...]: no native or mirror attempt resolved
    (['EA20', 'EA19']): DBnomics/Eurostat request failed after 3 tries: 404 Client Error

[Eurostat] native + mirror fallback: bop_gdp6_q
  current account % GDP: 1.7% as of 2025-Q3 (geo=EA20, source=dbnomics_mirror)

[Eurostat] native + mirror fallback: namq_10_gdp
  nominal GDP: €4,018,237M as of 2026-Q1 (geo=EA20, source=native)

[ECB] native SDMX (RAS), then DBnomics mirror fallback
  [ECB native] RAS/M.N.4F.1C.S121.S121.FC.FI.RT1.RT.F41A.TM13.EUR.X1.N.N.ALL (native attempt):
    latest (2026, 6) = 0.0, 6 pts
  [ECB native] RAS/M.U2.N.RAS0.RAS0.T.N.ALL (native attempt): FAILED: 400 Client Error: Bad Request
  computed: reserve assets €0M as of 2026-06 (key=...F41A.TM13..., source=native)

[ECB] native SDMX QSA total-debt attempt
  total_debt_pct_gdp() FAILED: 404 Client Error: Not Found

[BIS] native SDMX probe
  native probe .../WS_NA_SEC_DSS/Q.5J/all: HTTP 404
  native probe .../WS_NA_SEC_DSS/Q.3P/all: HTTP 404

Verifying IMF COFER — native first (2 structured attempts), DBnomics mirror as fallback
  IMF-native COFER USD unavailable: SDMX 3.0 (api.imf.org): HTTP 404 | SDMX 2.1 (sdmxcentral.imf.org): HTTP 501
  [cofer] USD share resolved via DBnomics mirror (native failed): 57.7% as of 2025-Q1 — freshness: 569d old, STALE
  IMF-native COFER EUR unavailable: SDMX 3.0: HTTP 404 | SDMX 2.1: HTTP 501
  [cofer] EUR share unavailable (native and mirror both failed): 404
```

**Build step (not just `--verify`) — the actual row that shipped:**

```
EUR government debt (central/general basis) unavailable: freshness guard:
  Eurostat government debt (chosen basis) latest observation is 2026-Q1
  (204d old, today 2026-07-24) — exceeds the 150d threshold for this
  series' cadence. The source is likely dead or frozen, not just running
  a normal lag.
```

**This is the bug**: native `gov_10q_ggdebt` resolved REAL, CURRENT
(2026-Q1) data — not stale, not dead — and the freshness guard rejected
it anyway. `EUROSTAT_FRESH_DAYS` (150d) didn't account for Eurostat
dating a quarterly observation to the quarter's START, adding up to ~90
more days on top of the real ~113d publication lag before "today" even
sees it — the same reasoning FRED's own 220d quarterly threshold already
encodes (see `series.py`). A second, independent bug in the same run:
ECB RAS's first key resolves syntactically (HTTP 200, 6 real
observations) but every value is exactly 0.0 — not aggregate reserve
assets, some irrelevant instrument/maturity slice of the underlying BOP
DSD. Both `EUR government debt (% of GDP)` in `public/data.json`'s
`fallbacksFired` confirms the first; the `€0M` figure in the log confirms
the second (this round it was gated behind the ALSO-broken GDP freshness
check so it never actually shipped — but fixing bug 1 alone would have
let it through, which is exactly why both needed catching in the same
pass).

**Claim status: VERIFIED** — read directly from job `89382957690`'s log.

## 2. Fixes applied

- `series.py`: `EUROSTAT_FRESH_DAYS` 150 → 230 (t+113d real lag + up to
  ~90d quarter-start dating + headroom, same reasoning as FRED's 220d).
- `ecb.py`: new `_plausible_reserves(hist)` — rejects a resolved series
  whose values are all ≤1000 (real reserves are hundreds of billions of
  EUR, in millions) before accepting it, applied to both native attempts
  and both mirror fallback attempts.

Committed as `16d4b3a`, tested locally first (`test_fetch.py`'s
regression test reproduces the exact live bug shape — an all-zero
history — and confirms the guard rejects it; full suite re-run, exit 0).

## 3. Run 2: fixes confirmed against real live data

Verbatim from job `89384460058`'s log (commit `16d4b3a`, run
`30061697837`):

```
[Eurostat] native + mirror fallback: gov_10q_ggdebt
  general government debt (S13) % GDP: 89.4% as of 2026-Q1 (geo=EA20, source=native, 105 pts)
  central government debt (S1311) % GDP: 79.1% as of 2026-Q1 (geo=EA20, source=native, 105 pts)

[ECB] native SDMX (RAS), then DBnomics mirror fallback
  [ECB native] RAS/M.N.4F.1C.S121.S121.FC.FI.RT1.RT.F41A.TM13.EUR.X1.N.N.ALL: latest (2026, 6) = 0.0, 6 pts
  [ECB native] RAS/M.U2.N.RAS0.RAS0.T.N.ALL: FAILED: 400 Client Error
  reserve_assets_eur() FAILED (native and mirror both failed): ECB RAS: no native or mirror
    attempt resolved to a plausible value ([...]): 404 Client Error
```

No more `EUR government debt ... unavailable: freshness guard` message —
confirmed directly by inspecting the committed `public/data.json` at
`3fb9c14`:

```python
gov_panel["rows"]:
  debt_to_gdp             | live   | 89%   | Eurostat gov_10q_ggdebt (native SDMX), general government (S13...)
  debt_to_gdp_other_basis | live   | 79.1% | Eurostat gov_10q_ggdebt (native SDMX), central government...
```

And ECB RAS: `no native or mirror attempt resolved to a plausible value`
— the `€0M` bad value is gone, replaced by a clean failure that correctly
falls through to the manual book figure (`FX reserves`, `tag: "manual"`,
`"9%"`, confirmed in the same file).

**Claim status: VERIFIED** — both the "bug reproduced" (run 1) and "bug
fixed" (run 2) states are read directly from job logs and the committed
data file, not asserted from the code alone.

## 4. Mirror-vs-native cross-check (TASKnativesources.md §2's requirement)

| Basis | Mirror reading (round c/d, frozen 2025-Q2) | Native reading (this round, 2026-Q1) |
|---|---|---|
| General government | 88.2% | 89.4% |
| Central government | 78.1% | 79.1% |

Both bases moved by the same ~1.0-1.2pt, consistent with roughly three
quarters of real debt growth between 2025-Q2 and 2026-Q1 — not a
disagreement in construction. At Dalio's own vintage (2025-Q1), BOTH
mirror and native agree exactly: general 87.7%, central 77.6% (this is
expected — 2025-Q1 is now historical data both transports have settled
on identically). **Claim status: VERIFIED** — no addressing error; same
series, new transport, as intended.

## 5. "Migrate both or neither" — COFER

Not exercised live this round (both USD and EUR failed identically on
both native attempts, so there was nothing to arbitrate between). Tested
locally instead: `test_fetch.py` mocks one currency `source: "native"`
and the other `source: "dbnomics_mirror"`, confirms the natively-resolved
one is force-downgraded to manual with a `fallbacksFired` entry recorded,
and a second scenario mocks both native and confirms both ship live.
Both scenarios pass. **Claim status: VERIFIED locally; not yet exercised
live** — recorded honestly as such, not overclaimed.

## 6. Z-score wall

Unaffected — this round touched no Z-scored row's construction, only
transport for already-non-Z raw values (EUR debt/GDP/current-account,
US's COFER `src` label). `data/manual.json`'s `US` block diff for this
round: zero lines (confirmed via `git diff`).

**Claim status: VERIFIED.**

## 7. Local + browser verification

Full `test_fetch.py` suite (now including: `sdmx.py`'s JSON-stat/CSV
parsers against synthetic realistic fixtures, the native/mirror
resolution order, the "migrate both or neither" coordination in both
directions, the ECB RAS plausibility-guard regression test reproducing
the exact live bug shape, and a golden-path ECB QSA total-debt mock) —
all pass, exit 0. `npm run build` clean. No frontend changes this round
(pure backend/sourcing migration) — no new screenshot needed; the
existing EUR screenshot from round c already covers the rendering path
for a `live`-tagged government-debt row via the pre-existing MetricRow
component, unchanged by this round.

## 8. Bundle size

Unchanged — no frontend files touched this round.
