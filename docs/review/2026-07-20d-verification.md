# Verification log, review round `2026-07-20d` — freshness guard + live production run

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-20c-verification.md` (round c, base
> commit `bf0ec51`, the gold alt-source magnitude quantification). Every
> review pass gets its own new file under `docs/review/` — check
> STATUS.md's "current review-round files" note (top of file) for whichever
> round is actually current when you're reading this.
>
> **Base commit:** `a93e485` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §3 below)
> **Written:** 2026-07-20T15:51:00Z UTC

**What this round covers:** `TASKgoldpricefreshness.md` — (1) try five
named keyless gold-price sources in the specified order, stopping at the
first current one, or documenting all five as tried-and-failed; (2) add a
freshness guard checking every fetched series' observation *date*, not
just its magnitude, since a dead source returning a plausible number
passes every existing sanity band silently; (3) re-run the full pipeline
and report what the guard catches, including the new gold price used (if
any) and the resulting `reserves_to_gdp`.

## 1. Five gold sources, in order — all fail

### 1.1 FRED — tried first, per the task's own instruction

```
=== FRED: series/search?search_text='LBMA gold' ===
0 results

=== FRED: series/search?search_text='gold fixing' ===
2 results (both irrelevant — an India M3 series, a 1931 Berlin wool price)

=== FRED: series/search?search_text='gold spot' ===
0 results

=== FRED: series/search?search_text='gold price' ===
30 results (top 30 by popularity) — none a genuine $/oz spot/fixing series.
The current, on-cadence ones are:
  GVZCLS       CBOE Gold ETF Volatility Index (an index, not a price)
  IQ12260      Export Price Index (End Use): Nonmonetary Gold (base-year index)
  NASDAQQGLDI  Credit Suisse NASDAQ Gold FLOWS103 Price Index (an index)
  IR14270      Import Price Index (End Use): Nonmonetary Gold (base-year index)
  ...plus several more base-year PPI/import/export indices, none $/oz

=== Explicitly checking the two believed-discontinued LBMA fixings ===
  GOLDAMGBD228NLBM   FAILED: 400 Client Error: Bad Request
  GOLDPMGBD228NLBM   FAILED: 400 Client Error: Bad Request
```
Both old LBMA fixing series IDs are now hard-404 at the FRED API level —
not "discontinued with history retained," genuinely gone. **FRED: no
usable current gold price.**

### 1.2 World Bank Pink Sheet via DBnomics (carried forward from round c)

```
provider WB: 14 datasets
  candidate dataset: GEM — Global Economic Monitor
  candidate dataset: commodity_prices — Commodity Prices: History and Projections

WB/commodity_prices q=gold -> 2 series
  FGOLD-1W (Gold, nominal, $/troy oz – World): 71 obs, latest 2030 = 1100.0
  KFGOLD-1W (Gold, real, $/troy oz – World): 71 obs, latest 2030 = 907.4
```
Real dataset, real gold series — but annual, with `2030` (a *projected*
out-year) as its "latest" observation. Not the monthly Pink Sheet.
**No usable current gold price.**

### 1.3 Bundesbank — direct API and DBnomics mirror

```
=== Bundesbank direct SDMX API — guessed series codes ===
  BBK01.WT5511                FAILED: 404
  BBK01.WT5510                FAILED: 404
  BBEX3.D.XAU.EUR.CA.AC.A01   FAILED: 404

=== DBnomics provider BUBA — full 50-dataset catalog ===
  ...BBEX3   ECB euro reference exchange rates, exchange rates in
             particular countries, special drawing rights, precious metals
  ...BBK01   (name: None)

=== BUBA/BBEX3 series dump (limit=300, no filter) ===
  300 series (all currency exchange rates, alphabetical by ISO code,
  cut off around "AN" — gold/XAU is much further down the alphabet)

=== BUBA/BBEX3, server-side search q='gold' ===
  7 series, 3 match gold/XAU:
    A.XAU.DEM.EA.AC.C03  Gold price, Frankfurt Stock Exchange fixing,
                          1kg fine gold = DM, up to end of 1998
    D.XAU.DEM.EA.AC.C01  (daily) same series, up to end of 1998
    M.XAU.DEM.EA.AC.C02  (monthly) same series, up to end of 1998
```
The real Bundesbank gold series exists (`BBEX3`) — but it's a pre-euro
Deutsche Mark fixing, permanently discontinued at end-1998, not a
stale-but-alive feed. **No usable current gold price.**

### 1.4 Nasdaq Data Link (ex-Quandl), LBMA/GOLD — no-key attempt

```
[CSV, no key] GET https://data.nasdaq.com/api/v3/datasets/LBMA/GOLD.csv
  status: 403, content-type: text/html
  body: '<html>...<script src="/_Incapsula_Resource?SWJIYLWA=...">...'

[JSON, no key, limit=5] GET https://data.nasdaq.com/api/v3/datasets/LBMA/GOLD.json
  status: 403, content-type: text/html
  body: (same Incapsula anti-bot challenge page)
```
Blocked by an Incapsula WAF on both formats. Would require a paid API key
(a new GitHub secret) to test meaningfully — not added without an
explicit request to do so. **No usable current gold price.**

### 1.5 Stooq daily XAUUSD CSV (carried forward from round c)

```
[no UA, base url] FAILED: 404
[with UA, base url] GET https://stooq.com/q/d/l/?s=xauusd&i=d
  status: 200, content-type: text/html
  body: '<html>...This site requires JavaScript to verify your browser...
  crypto.subtle.digest("SHA-256", ...) ... fetch("/__verify", ...)...'
```
A `200` that is not the CSV — a client-side proof-of-work anti-bot
challenge. Not retrievable via a plain HTTP client. **No usable current
gold price.**

**Result: all five sources tried, all five fail, for five distinct and
specifically-evidenced reasons.** No source switch. See STATUS.md §17.1.

## 2. Freshness guard: first live `--verify` run

Full FRED table (after threshold recalibration — the first attempt used
Quarterly=150d/generic Monthly=60d for `TRESEGUSM052N` and produced 5
false positives; see STATUS.md §17.2 for the before/after):

```
ID                 OK  FREQ       UNITS                        START        LATEST OBS      AGE    MAX FRESH   TITLE
--------------------------------------------------------------------------------------------------------------------
FYGFGDQ188S        yes Q          Percent of GDP               1970-01-01   2026-01-01     200d   220d ok      Federal Debt Held by the Public as Perce
GDP                yes Q          Billions of Dollars          1947-01-01   2026-01-01     200d   220d ok      Gross Domestic Product
TCMDO              yes Q          Millions of U.S. Dollars     1945-10-01   2026-01-01     200d   220d ok      All Sectors; Debt Securities and Loans;
IEABC              yes Q          Millions of Dollars          1999-01-01   2026-01-01     200d   220d ok      Balance on current account
TRESEGUSM052N      yes M          Millions of Dollars          1950-12-01   2026-03-01     141d   180d ok      Total Reserves excluding Gold for United
DGS10              yes D          Percent                      1962-01-02   2026-07-16       4d    20d ok      Market Yield on U.S. Treasury Securities
CPIAUCSL           yes M          Index 1982-1984=100          1947-01-01   2026-06-01      49d    60d ok      Consumer Price Index for All Urban Consu

All FRED series resolved. Review units/frequency above.
```

Treasury debt-service ratios:
```
LIVE headline debt-service ratio (net interest to the public / total
  receipts, net of refunds): 19.6% as of 2026-06 (42 history pts) —
  freshness: 49d old, 60d threshold, ok
LIVE second-row debt-service ratio (gross interest incl. GAS / total
  receipts, net of refunds): 25.1% as of 2026-06 (42 history pts) —
  freshness: 49d old, 60d threshold, ok
```

**IMF COFER — a genuinely new catch:**
```
Verifying IMF COFER via DBnomics (non-fatal — manual fallback on failure)
  23 series; codes: [...RAXGFXARUSDRT_PT...]
  computed USD share: 57.7% as of 2025-Q1 (105 pts) — freshness: 565d old,
  270d threshold, STALE
```

**Gold — the previously-known catch, now formally caught by the guard:**
```
[gold-holdings] ...
  freshness: 20d old, 60d threshold, ok

[gold-price] https://api.db.nomics.world/v22/series/IMF/PCPS (bare dump)
  selected series_code: M.W00.PGOLD.USD
  426 observations; latest: 2025-06 = 3351.85857142857 USD/oz
  freshness: 414d old, 60d threshold, STALE — this is the frozen series,
  see STATUS.md §16

  computed gold market value: $876.5B as of 2025-06 (162 months)
```

## 3. Full production run: `update-data.yml`, `workflow_dispatch`

`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29756605271`,
job `88400445209`, 2026-07-20 15:45-15:47 UTC, committed as `a93e485`.
Verbatim build-step output:

```
Gold-inclusive reserves unavailable, using manual value: freshness guard:
  gold price (DBnomics PCPS) latest observation is (2025, 6) (414d old,
  today 2026-07-20) — exceeds the 60d threshold for this series' cadence.
  The source is likely dead or frozen, not just running a normal lag.
IMF COFER unavailable, using manual value: freshness guard: IMF COFER USD
  share latest observation is 2025-Q1 (565d old, today 2026-07-20) —
  exceeds the 270d threshold for this series' cadence. The source is
  likely dead or frozen, not just running a normal lag.
Wrote public/data.json — generatedAt 2026-07-20T15:47:15Z
  debt_to_gdp                     99%  (2026-Q1, 225 pts)
  debt_service_to_revenue         20%  (2026-06, 42 pts)
  real_rates                     0.6%  (2026-Q2, 258 pts)
```
```
[claude/new-session-ldotj8 a93e485] data: monthly refresh (2026-07-20)
 1 file changed, 89 insertions(+), 923 deletions(-)
```

**Claim status: VERIFIED** — the run succeeded (exit 0), both known-stale
sources correctly fell back to manual rather than failing the build or
shipping as falsely live, and every other live row's own freshness check
passed. See STATUS.md §17.3 for the resulting values (`reserves_to_gdp`
3.0% manual, `World CB reserves in USD` 57.0% manual) and §9's updated
table.
