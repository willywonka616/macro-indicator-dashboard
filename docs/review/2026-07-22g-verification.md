# Verification log, review round `2026-07-22g` — retiring undated manual values, de-tautologising §9

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-22f-verification.md` (round f, base
> commit `a73c4df`, equation #3's growth-term commentary). Every review
> pass gets its own new file under `docs/review/` — check STATUS.md's
> "current review-round files" note (top of file) for whichever round is
> actually current when you're reading this.
>
> **Base commit:** `c7cdbe8` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> second live `update-data.yml` run this round, documented in §2 below)
> **Written:** 2026-07-22T19:35:00Z UTC

**What this round covers:** `TASKmanualvalues.md` — the §19.2 freshness
audit found 10 of `manual.json`'s 14 values undated (11 originally; one,
the CBO 10-yr projection, was already made live by §21), several
transcribed straight from Dalio's Ch.17 table, meaning §9 calibrated those
rows against the numbers they were seeded from. This round: (1) makes the
TIC holder-shares split live from FRED, independent of the book; (2)
attempts BIS's debt-currency share live and documents honestly why it
isn't resolved yet; (3) dates every remaining manual value with its real
last-known-true date — no fabricated dates; (4) confirms the UI staleness
indicator fires for all of them; (5) marks every §9 calibration row
genuine-test vs. tautology, with before/after counts.

The full inventory table, the source research, and the honest-dating
rationale are written up in `STATUS.md` §28 (not duplicated here) — this
file's job is the live-run verification specifically.

## 1. First live run: real numbers, and a real bug the run itself caught

Triggered `workflow_dispatch` on commit `c8f2967` (the initial
implementation). Confirmed live from the actual CI log — not assumed
from the mock test:

```
FYGFDPUN: 'Federal Debt Held by the Public', units='Millions of Dollars', freq=Q, latest 2026-01-01 = 31,454,810.96
FDHBFRBN: 'Federal Debt Held by Federal Reserve Banks', units='Billions of Dollars', freq=Q, latest 2026-01-01 = 4,693.551
FDHBFIN: 'Federal Debt Held by Foreign and International Investors', units='Billions of Dollars', freq=Q, latest 2025-10-01 = 9,270.9
```

All three series fetch correctly — but the row still shipped `manual`
this run, because `FDHBFIN`'s latest observation (2025-10-01) is 294 days
old, past the generic `FRESHNESS_DAYS_BY_FREQ["Quarterly"]` (220d)
threshold, even though `FYGFDPUN`/`FDHBFRBN` were current through
2026-01-01 the same day. This is a **real, live-confirmed fact**:
`FDHBFIN` publishes a full quarter behind its two counterpart series from
the same underlying Treasury table — not a bug in the fetch, a genuine
cadence difference the freshness guard correctly (if too strictly) caught.

Also confirmed live: all three BIS `WS_NA_SEC_DSS` dimension-filter
guesses returned **0 series each**:
```
dimensions={'FREQ': ['Q'], 'ISSUER_RES': ['5J']} -> 0 series
dimensions={'FREQ': ['Q'], 'ISSUER_RES': ['3P']} -> 0 series
dimensions={'FREQ': ['Q'], 'L_REP_CTY': ['5J']} -> 0 series
```
Confirms `bis.py`'s documented uncertainty was correct, not overcautious
— none of the guessed dimension names/codes exist in this dataset as
published on DBnomics. Resolving this needs real schema research this
project's dev sandbox can't do (both `data.bis.org` and
`db.nomics.world` are blocked there); left open, not guessed.

**Claim status: VERIFIED** — read directly from the CI job log
(run `29949076336`), not assumed.

## 2. Fix + second live run: TIC holder shares now genuinely live

Added `series.py`'s `TIC_FOREIGN_FRESH_DAYS` (220d + one quarter's grace
= 310d), applied only to `FDHBFIN`'s own freshness check — same class of
fix as `COFER_FRESH_DAYS`/`TRESEGUS_FRESH_DAYS` (a generic
frequency-bucket threshold miscalibrated for one structurally
slower-published series). Re-ran `workflow_dispatch` on commit `1b7cb44`
(run `29950922488`, completed successfully) — committed as `c7cdbe8`,
this round's base commit. Read directly from the committed
`public/data.json`:

```
"— held by central bank": { "value": 14.7, "display": "14.7%", "tag": "live",
  "asOf": "2025-Q4",
  "src": "derived · FRED (FYGFDPUN, FDHBFRBN, FDHBFIN — Treasury Fiscal
          Service \"distribution of federal securities by class of investors\")" }
"— held by domestic players": { "value": 55.3, "display": "55.3%", "tag": "live", "asOf": "2025-Q4" }
"— held abroad": { "value": 30.0, "display": "30.0%", "tag": "live", "asOf": "2025-Q4" }
```

Sum: 14.7 + 55.3 + 30.0 = **100.0% exactly**. `asOf` is 2025-Q4 (not
2026-Q1) because the computation bottlenecks to the latest quarter
common to all three series — `FDHBFIN` is the limiting one, exactly as
its own longer lag predicts.

**This is a genuine, non-circular result**: 14.7% / 55.3% / 30.0% is
materially different from Dalio's book figures (13% / 57% / 29%) — a real
independent computation, not a match by construction. `provenance.fallbacksFired`
for this run contains only the pre-existing, unrelated COFER entry (frozen
since 2025-Q1, documented in earlier rounds) — **no** "Debt holders" entry,
confirming the live path shipped cleanly with no fallback firing.

**Claim status: VERIFIED** — read directly from the committed
`public/data.json` at commit `c7cdbe8`, not from memory or a mock.

## 3. Every previously-undated manual value now carries an `asOf`

Read directly from the same `public/data.json`:

```
gov_assets_minus_debt | −96% | asOf 2025-03 | note: ⚠ 508d old, past 180d threshold
share_hard_fx         | No   | asOf 2025-03 | note: ⚠ 508d old, past 180d threshold
sovereign_wealth      | None | asOf 2025-03 | note: ⚠ 508d old, past 180d threshold
world_trade_usd       | 52.6%| asOf 2025-03 | note: ⚠ 508d old, past 180d threshold
world_debt_usd        | 80.7%| asOf 2025-03 | note: ⚠ 508d old, past 180d threshold  (BIS, live attempt failed as expected)
global_equity_usd     | 65.7%| asOf 2025-03 | note: ⚠ 508d old, past 180d threshold
world_cb_reserves_usd | 57.1%| asOf 2026-Q1 | note: (none — well within its own threshold)
```

Every one of these is honestly dated: `2025-03` for figures transcribed
from Dalio's book at that vintage (a real "last known true" date, not
invented), and the pre-existing `2026-Q1` for the COFER manual snapshot
(unchanged this round). All seven show the amber `⚠` staleness note
except the COFER snapshot, which is correctly still fresh. **This
confirms the frontend needs no change**: `MetricRow.jsx`'s existing
"render any note starting with ⚠ in the warning color" logic already
covers every one of these — verified with a Playwright screenshot against
a synthetic build before this round's live run (see STATUS.md §28.4).

**Claim status: VERIFIED** — read directly from the committed
`public/data.json`.

## 4. Local + browser verification

Full existing mock-test suite extended (synthetic `FYGFDPUN`/`FDHBFRBN`/
`FDHBFIN` series proportioned ~13%/29%/58%; a stubbed-always-raising BIS
call) and re-run — all checks pass, including two new scenarios: (a) a
fully-healthy run ships all three holder rows live, summing to ~100%,
with `fallbacksFired == []`; (b) a simulated FRED outage on the TIC
series falls back cleanly to the dated manual split, correctly recorded
in `fallbacksFired` (unlike BIS, which is deliberately never routed
through that mechanism).

Browser (Playwright): built a synthetic `data.json` from the mock test's
fallback scenario (all manual rows dated `2025-03`, 508 days before
today) and screenshotted the full page at 900px width — confirmed the
amber `⚠` staleness note renders correctly on every newly-dated manual
row (Gov assets, held by central bank/domestic/abroad, Share in hard FX,
World trade/debt in USD, Global equity market cap). Original
`public/data.json` restored before committing; `npm run build` re-run
clean afterward.

## 5. Bundle size

Not separately re-measured — no new frontend component or dependency;
`MetricRow.jsx`'s existing `⚠`-note rendering already covers the new
rows. Backend-only change (`fetch.py`, `series.py`, new `bis.py`,
`data/manual.json`).
