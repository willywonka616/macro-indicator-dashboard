# Verification log, review round `2026-07-23d` — euro area (aggregate)

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-23c-verification.md` (round c, base
> commit `6613635`, MSPD parsing closed). Every review pass gets its own
> new file under `docs/review/` — check STATUS.md's "current review-round
> files" note (top of file) for whichever round is actually current when
> you're reading this.
>
> **Base commit:** `9b7c850` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §1 below)
> **Written:** 2026-07-23T20:15:00Z UTC

**What this round covers:** `TASKeuroarea.md` — the euro area
(aggregate), first non-US country. Shared central-bank data model,
three-state own-currency field, and live sourcing attempts for every
computable row via Eurostat/ECB/IMF (DBnomics). Code commit `eeb68bd`,
triggered via `workflow_dispatch` on `claude/new-session-ldotj8`, run id
`30040181332`, job id `89317911960` — completed successfully (`verify`
step green, `build` step green), committed as `9b7c850`.

## 1. What actually resolved live — read directly from the job log

Verbatim excerpts (timestamps trimmed), not reconstructed from memory:

```
[Eurostat] https://api.db.nomics.world/v22/series/Eurostat/gov_10q_ggdebt
  general government debt (S13) % GDP: 88.2% as of 2025-Q2 (geo=EA20, 102 pts)
    at Dalio's vintage (2025-Q1): 87.7% (book target: 85%, general-vs-central identification)
  central government debt (S1311) % GDP: 78.1% as of 2025-Q2 (geo=EA20, 102 pts)
    at Dalio's vintage (2025-Q1): 77.6% (book target: 85%, general-vs-central identification)

[Eurostat] https://api.db.nomics.world/v22/series/Eurostat/gov_10q_ggnfa
  central govt interest / revenue: FAILED: ['Q.D41.S1311.MIO_EUR.{geo}', 'Q.S1311.D41.MIO_EUR.{geo}']:
    no attempt resolved (['EA20', 'EA19']): DBnomics/Eurostat request failed after 3 tries:
    404 Client Error: NOT FOUND for url: .../gov_10q_ggnfa/Q.S1311.D41.MIO_EUR.EA19?observations=1

[Eurostat] https://api.db.nomics.world/v22/series/Eurostat/bop_gdp6_q
  current account % GDP: 1.7% as of 2025-Q3 (geo=EA20)

[Eurostat] https://api.db.nomics.world/v22/series/Eurostat/namq_10_gdp
  nominal GDP: €3,969,578M as of 2025-Q3 (geo=EA20)

[ECB] https://api.db.nomics.world/v22/series/ECB/RAS
  key=M.U2.S1.S1._Z.RES.T._Z.LE.EUR -> FAILED: 404
  key=M.U2.N.RAS.RAS0.TOT.RAS0 -> FAILED: 404
  key=M.U2.S121.RES.RAS0.TOT -> FAILED: 404
  reserve_assets_eur() FAILED (see key attempts above)
  fallback dataset-root dump (20 series, no filter):
    ['M.N.4F.1C.S121.S121.FC.FI.RT1.RT.F41A.TM13.EUR.X1.N.N.ALL',
     'M.N.4F.1C.S121.S121.FC.FI.RT1.RT.F41A.TM3C.EUR.X1.N.N.ALL', ...]

[cofer] computed USD share: 57.7% as of 2025-Q1 (105 pts) — freshness: 568d old, 270d threshold, STALE
[cofer] EUR share unavailable — build will use the manual value: DBnomics/COFER request failed
  after 3 tries: 404 Client Error: NOT FOUND for url: .../COFER/Q.W00.RAXGFXAREURRT_PT?observations=1
```

**Claim status: VERIFIED** — read directly from the CI job log
(`mcp__github__get_job_logs`, job id `89317911960`), not assumed.

**What this means, source by source:**

1. **`gov_10q_ggdebt` (government debt, both bases): resolved correctly.**
   The `Q.GD.<sector>.PC_GDP.EA20` shape guessed in `scripts/eurostat.py`
   was right for both `S13` (general) and `S1311` (central) — real,
   sane values came back for both. See §2 below for what this means for
   the central-vs-general identification.
2. **`gov_10q_ggnfa` (interest/revenue): did not resolve.** Both
   dimension-order guesses (`D41.S1311` and `S1311.D41`) 404'd for both
   `EA20` and `EA19`. Since the DEBT dataset in the same "gov_10q_*"
   family resolved sector `S1311` correctly, the gap is specific to this
   dataset's own na_item/unit codes for interest paid and total revenue,
   not sector `S1311` itself. Left unresolved and documented plainly —
   same treatment `scripts/bis.py` already established for its own
   still-unresolved BIS integration.
3. **`bop_gdp6_q` (current account): resolved correctly.** 1.7% as of
   2025-Q3 — a real, sane value, close to Dalio's +2% book figure.
4. **`namq_10_gdp` (GDP): resolved correctly.** €3,969,578M for ONE
   quarter (2025-Q3) — this confirms `namq_10_gdp` is a per-quarter
   level, not an annualized rate (the euro area's known annual GDP is
   ~€15-16T, and 4×€3.97T ≈ €15.9T lines up). This finding drove §3's bug
   fix below.
5. **`ECB/RAS` (reserves): dataset confirmed real, key did not resolve.**
   All 3 guessed keys 404'd. The dataset-root fallback dump (no filter)
   proves `ECB/RAS` itself is a real, populated dataset (DBnomics
   describes it as "official reserve assets of the euro area... BPM6"),
   but its actual SDMX key has far more fields (16, per the example
   pulled live above) than the 9-10 guessed. Documented in
   `scripts/ecb.py`'s docstring with the real example key, for a future
   session to build on rather than guess blind again.
6. **IMF COFER, EUR share: did not resolve** — the naming-convention
   substitution (`RAXGFXARUSDRT_PT` → `RAXGFXAREURRT_PT`) that works for
   every other currency-keyed field in `imf.py` isn't this series' real
   code. Separately and importantly: **the USD share this SAME run read
   57.7% at 2025-Q1, 568 days stale** — proving COFER's DBnomics mirror
   is currently frozen for the pre-existing US integration too, not
   something this round's EUR work caused. This is the exact failure
   mode STATUS.md §17/§18 already documented for COFER, recurring.

## 2. The central-vs-general basis finding (TASKeuroarea.md §3)

`fetch.py`'s `build_eur()` fetches both bases and adopts whichever is
closer to Dalio's 85% **at his own March-2025 vintage** (2025-Q1), not
today's reading — the same "identify at vintage, not today" discipline
already established for the US's TCMDO/GDP total-debt check. This run:

| Basis | Reading at 2025-Q1 (his vintage) | Distance from 85% |
|---|---|---|
| General government (S13) | 87.7% | 2.7pt |
| Central government (S1311) | 77.6% | 7.4pt, further away |

**General government is the closer match** — `debt_basis_adopted` in
`public/data.json`'s `countries.EUR.provenance` reads `"general"`,
confirmed by direct inspection of the committed file, not just the code
path. This is the **opposite** of `TASKeuroarea.md` §3's own stated
expectation ("expected to be the central-government subsector series").
Reported exactly as found — the code doesn't hardcode either assumption,
so this isn't a result that could have been tuned toward the expectation
even by accident.

**Claim status: VERIFIED** — read directly from both the job log and the
committed `public/data.json`'s `provenance.debtBasisAdopted` field.

## 3. Why every EUR-side row still ships `manual` this round

Two distinct reasons, confirmed by direct inspection of
`public/data.json`'s `countries.EUR.panels` (every row's `tag` reads
`"manual"`) and the job log's freshness-guard output:

```
EUR government debt (central/general basis) unavailable: freshness guard:
  Eurostat government debt (chosen basis) latest observation is 2025-Q2
  (478d old, today 2026-07-23) — exceeds the 280d threshold for this
  series' cadence. The source is likely dead or frozen, not just running
  a normal lag.

EUR current account unavailable: freshness guard: Eurostat current
  account latest observation is 2025-Q3 (387d old, today 2026-07-23) —
  exceeds the 280d threshold for this series' cadence.
```

- **Government debt and current account**: real, correctly-computed
  values were fetched, but DBnomics' own mirror of both datasets is
  frozen well past `series.py`'s new `EUROSTAT_FRESH_DAYS` (280d)
  threshold — the freshness guard did exactly its job (refuse to ship a
  live-tagged figure built on stale-mirror data), the same mechanism
  that already caught COFER frozen for over a year (§17/§18). This is a
  DBnomics-mirror problem, not a construction problem in this round's
  new code.
- **Interest/revenue, FX reserves, world CB reserves in EUR**: genuinely
  did not resolve (404s) — wrong series-level guesses, documented
  honestly in each row's own `note` field and in the relevant module's
  docstring, not chased indefinitely (same bounded-effort precedent as
  BIS's still-unresolved integration).

**Claim status: VERIFIED** — read directly from the CI log and the
committed `public/data.json`.

## 4. A bug the live run surfaced: GDP annualization

`namq_10_gdp` resolving to €3,969,578M for ONE quarter (confirmed §1.4
above) exposed a latent unit error in `build_eurosystem()`'s FX-reserves
construction: it originally divided the reserves figure (a stock) by a
SINGLE quarter of GDP (a flow), which would overstate the %-of-ANNUAL-GDP
ratio roughly 4x the moment ECB RAS ever starts resolving. Fixed to sum
the trailing four quarters before dividing — the same annualization
convention `series.py`'s `current_account_pct_gdp_3yr` already uses for
the US. This path never actually executes in production yet (ECB RAS
fails before reaching it), so the fix is verified locally only:

```
Eurosystem shared entity: FX reserves 5.3% (live) [before the fix, on the mock fixture]
Eurosystem shared entity: FX reserves 5.1% (live) [after the fix, same mock fixture]
```

**Claim status: VERIFIED locally** (the code path itself, via the mock
test) — **NOT YET verified against real reserves data**, since ECB RAS
still doesn't resolve live. This is the code being correct and ready for
when it does, not a live-confirmed number. Recorded honestly as such,
not overclaimed.

## 5. Shared-CB data model + three-state currency field: no regression to US

```
US output: byte-identical across two back-to-back build_us() calls, as required
```

- `git diff` on `scripts/fetch.py` shows the only removed lines are
  inside `main()` (wiring in the new `build_eur()`/`build_eurosystem()`
  calls) — zero lines changed inside `build_us()` itself.
- `git diff` on `data/manual.json` shows the entire diff is pure
  addition (`git diff data/manual.json | grep '^-'` returns nothing
  beyond the diff header) — the existing `US` block, including every
  Z-score, is untouched.
- Local test asserts `json.dumps(build_us(...), sort_keys=True)` is
  identical across two back-to-back calls with the same mocks.
- `src/components/MetricRow.jsx`'s new `currencyStatus` badge is
  additive-only (renders nothing when the field is absent) — confirmed
  both by the byte-identical US output above and by a Playwright
  screenshot showing the badge appears only on the EUR own-currency row.

**Claim status: VERIFIED** — `git diff` inspection, local test, and
screenshot, not merely asserted.

## 6. Z-score wall

N/A for the EUR entry — no Z-scores exist for it at all (§5's own
instruction; `"govGauge"`/`"cbGauge"`/`"headline"` are absent from
`build_eur()`'s output entirely, confirmed by direct inspection of
`public/data.json`). For the US entry, the same diff method as every
prior round (`(label, z)` tuples, in order, both gauges, against the
pre-round `data/manual.json`) — unchanged; this round's `manual.json`
diff touches only the new `centralBanks`/`EUR` keys, never the existing
`US` block.

**Claim status: VERIFIED.**

## 7. Local + browser verification

Local mock test suite (`test_fetch.py`) extended with: the byte-identical
US-output check (§5), central/general basis identification with a
realistic vintage-anchored fixture, the three-state currency field, the
"no Z anywhere" assertion, live/manual row-split assertions, the shared
Eurosystem entity's FX-reserves and COFER-EUR live paths (with a
dedicated outage-degrades-to-manual test), and the GDP-annualization fix
verified via before/after ratio comparison on the same fixture. All
checks pass, exit 0. `npm run build` clean. Playwright screenshots of
both the US view (unchanged) and the EUR view (all panels, the
three-state currency badge, and the explicit "not published for this
entity" no-Z-model banner) confirmed correct rendering;
`public/data.json` restored to its committed state afterward,
`git status --short public/data.json` clean before proceeding.

## 8. Bundle size

```
dist/index.html                   1.38 kB │ gzip:  0.61 kB
dist/assets/index-C-I-yLJI.css   11.71 kB │ gzip:  3.12 kB
dist/assets/index-CRHQMhjC.js   184.82 kB │ gzip: 59.17 kB
```
No meaningful change from round c (new frontend code is a handful of
conditionals and one small badge component).
