# STATUS

Living document. **Update this at the end of every session** — that's the
instruction this file was created under, and it stands going forward. Written
for another AI assistant (or human) picking this up cold, with no memory of
prior sessions and no access to this repo's chat history.

Last updated: **2026-07-19** (later the same day, following an external
review of §10's review package), by Claude (Sonnet 5). This pass: split
debt-service into net (headline, to the public) and gross (incl.
intragovernmental) rows, both now denominated in on-budget receipts instead
of total receipts (extending the calibration matrix to 3×3 — see §3);
added a debt/revenue row alongside debt/GDP (§3); **explicitly retracted**
a wrong timing-drift claim from §10.2 rather than quietly editing it (see
the retraction block inside §10.2); tried and **refuted** a hypothesis
about Dalio's "other debt" figure (switching total-debt series to
TCMDODNS made the gap worse, not better — reverted to TCMDO, see §9);
corrected an overclaimed "confirmed" about IMF PCPS's gold-price staleness
(only DBnomics' mirror was actually checked, not IMF itself — see §3); and
made the gold-price/holdings date mismatch visible in the reserves row's
`src`, not only in `asOf`. §9 now covers every Ch.17 book row with a
published figure, not just the two from the first pass. See §10 for the
review package itself (`docs/verification-log.md`,
`docs/current-values.md`, regenerated this pass with a fresh commit SHA).

---

## 1. What's built and working

A live, auto-refreshing dashboard of Ray Dalio's sovereign debt-risk
indicators (*How Countries Go Broke*, Ch. 17), US only so far.

- **Live site:** https://willywonka616.github.io/macro-indicator-dashboard/
- **Repo:** `willywonka616/macro-indicator-dashboard`, public, default branch
  `main`. Most sessions have landed work on `main` directly; this session
  was explicitly scoped to a feature branch (`claude/new-session-ldotj8`,
  not yet merged — see §4/§8) rather than that being the project's normal
  convention.
- **Stack:** Vite + React + Tailwind v4 (via `@tailwindcss/vite`) for utility
  classes, mixed with inline styles for colour tokens (matches the legacy
  single-file dashboard's own mix — the brief said either approach was fine
  as long as it's consistent), Python 3 fetcher, two GitHub Actions
  workflows, GitHub Pages hosting.
- **Installable as a PWA** — manifest + custom icon, "Add to Home screen" on
  Android/iOS opens it fullscreen like a native app.

**End-to-end pipeline confirmed working on live infrastructure** (not just
locally): FRED/Treasury/IMF → `scripts/fetch.py` → commit `public/data.json`
→ triggers Pages deploy → live site updates. This has round-tripped
successfully multiple times over the session (see §4).

### Repo layout (as of last commit)
```
public/
  data.json              generated — the only source of numbers on the page
  manifest.webmanifest   PWA manifest
  icon-192.png, icon-512.png, apple-touch-icon.png
src/
  App.jsx                reads data.json, no hardcoded figures
  components/            ZScale, Chart, Tag, MetricRow, GaugeRow, Panel, HeadlineGauge
  content/commentary.js  hand-written interpretation prose (no LLM, not auto-generated)
  theme.js                colour tokens, z/tone scales, CRISES marker config
scripts/
  fetch.py                orchestrator: --verify / build / atomic write
  series.py               FRED ID registry + derived-metric math
  treasury.py             Treasury Fiscal Data client (debt service, budget basis)
  imf.py                  IMF COFER via DBnomics (reserve-currency USD share)
  gold.py                  Treasury gold holdings + DBnomics/IMF PCPS gold price (reserves incl. gold)
  requirements.txt
data/manual.json          Dalio's Z-scores + non-automatable figures, with dates
.github/workflows/
  update-data.yml          monthly cron (5th, 06:00 UTC) + workflow_dispatch
  deploy.yml               build + publish to Pages
README.md                 architecture/setup docs for a human user
STATUS.md                 this file
```

There is **no `legacy/` directory** — the user rejected committing the
original single-file dashboard verbatim; its logic was split into
`src/components/*` instead and nothing of it survives as a standalone file.

---

## 2. FRED series: verified vs failed vs substituted

The brief supplied 13 candidate IDs "from memory," explicitly unverified, and
asked for them to be checked against live FRED before trusting them. The
sandbox this was built in **cannot reach `api.stlouisfed.org`** (blocked by
egress policy) — all verification happened in GitHub Actions
(`update-data.yml`'s `--verify` step), not locally, and not by me reading
FRED's docs.

### Brief's original 13 IDs — outcome
All 13 resolved successfully on FRED (confirmed in the first live Actions
run). Of those, **9 are unused in the final build** — either superseded by a
better ID, or simply not needed yet:

| ID | Resolved? | Used today? | Note |
|---|---|---|---|
| `GFDEGDQ188S` | ✅ | ❌ replaced | Gross federal debt. User asked to switch to debt *held by the public* to match Dalio's framing → `FYGFGDQ188S` |
| `GFDEBTN` | ✅ | ❌ unused | Available for a future "total debt $" metric if wanted |
| `A091RC1Q027SBEA` | ✅ | ❌ replaced | Interest payments (NIPA basis) — replaced by Treasury Fiscal Data (budget basis), see §3 |
| `W006RC1Q027SBEA` | ✅ | ❌ replaced | **This was a real bug**: it's tax receipts *only*, narrower than total receipts. Using it as the denominator overstated debt-service-to-revenue at 33% instead of the correct ~18%. Caught by inspection, not by FRED — it resolved fine, it was just the wrong scope. |
| `GDP` | ✅ | ✅ used | Denominator for several ratios |
| `GDPC1` | ✅ | ❌ unused | Real GDP, available if wanted later |
| `TCMDO` | ✅ | ✅ used | Total debt, all sectors |
| `BOPBCA` | ✅ resolved, but **DISCONTINUED** | ❌ replaced | FRED accepted the ID and returned history, but the series has stopped receiving new observations. Would have silently frozen. Replaced with `IEABC` (active). |
| `TRESEGUSM052N` | ✅ | ✅ used | Total reserves excl. gold |
| `WALCL` | ✅ | ❌ unused | Fed total assets, available if wanted later |
| `CPIAUCSL` | ✅ | ✅ used | Real-rate calc (10y − trailing CPI inflation) |
| `FEDFUNDS` | ✅ | ❌ unused | Available if wanted later |
| `DGS10` | ✅ | ✅ used | Real-rate calc |

### IDs added later, not in the brief's original table
| ID | Status | Why |
|---|---|---|
| `FYGFGDQ188S` (Federal debt held by public, % GDP) | ✅ **verified live** — fetch succeeded on a real Actions run, 225 quarterly history points, current value 99% (matches Dalio's book figure) | User explicitly requested "held by public" over gross debt |
| `IEABC` (Balance on current account) | ✅ verified live, active/updating, history from ~1999 in current chart data | Replacement for discontinued `BOPBCA` |

**Currently active registry** (`scripts/series.py`, `FRED_SERIES` dict):
`FYGFGDQ188S`, `GDP`, `TCMDO`, `IEABC`, `TRESEGUSM052N`, `DGS10`, `CPIAUCSL` —
7 series, all confirmed resolving on live FRED as of the last successful run.

**If you're picking this up cold: don't trust this table indefinitely.**
FRED does occasionally discontinue or rename series (as `BOPBCA` proved). The
`--verify` step re-checks every ID on every run and will fail loudly if one
breaks — check the Actions tab for the latest run's outcome before assuming
any of the above is still good.

---

## 3. Non-FRED live sources — what they are, and where they broke

Two more automated sources exist beyond the brief's original FRED-only plan,
added mid-session at the user's request. Both took multiple iterations to get
right because **the dev sandbox cannot reach either host** — every fix had to
be inferred from a `--verify` schema dump captured from a real CI run, then
shipped blind and re-verified on the next run. If you're continuing this
work, expect the same constraint unless the sandbox's egress policy has
changed.

### Treasury Fiscal Data API (`scripts/treasury.py`) — debt service ratio
No API key. Computes trailing-12-month interest on debt held by the public ÷
trailing-12-month total federal receipts (budget/cash basis — this is the
basis Dalio and CBO use for "interest as a share of revenue," not FRED's NIPA
basis, which is why it replaced `A091.../W006...`).

Bugs found and fixed, in order:
1. **Wrong receipts table.** First attempt read `mts_table_1`, which has no
   "Total Receipts" row (its `classification_desc` values are month names).
   Fixed by switching to `mts_table_4` (falls back to `mts_table_1`).
2. **Transient network failure.** A `RemoteDisconnected` mid-run failed an
   otherwise-correct build. Fixed by adding 4-try exponential backoff to both
   the Treasury and FRED HTTP clients.
3. **Wrong interest scope (real bug, not flakiness).** The first working
   version filtered interest rows to `expense_group_desc` containing
   "interest," which excluded `AMORTIZED DISCOUNT` (~$20B/month) — a real
   interest component, just recognized differently for T-bills. This
   undercounted interest and produced a **debt-service ratio of 13%**,
   clearly too low. Fixed to sum every component under
   `expense_catg_desc == "INTEREST EXPENSE ON PUBLIC ISSUES"` (accrued +
   amortized discount/premium + savings + misc), explicitly excluding
   `INTEREST EXPENSE ON GOVT ACCOUNT SERIES` (intragovernmental, paid to
   trust funds — not part of net interest to the public).

**RESOLVED 2026-07-19, revised again same day** after an external review of
this exact write-up caught a real error in it — see §10.2 for the retraction
and §9 for the full calibration comparison. Two rounds happened on the same
day:

**Round 1** adopted gross interest / total receipts (23.0%), closest of six
candidates in a 3×2 matrix, and attributed the ~1pt residual vs. Dalio's 22%
to a March-2025-vs-rolling-window timing difference. **That attribution was
wrong** — the review pointed out the GAO/CBO cross-check itself used FY2024
data (ending September 2024, *before* Dalio's snapshot) and *also* got
23.0%, so the ratio was flat at 23% on both sides of March 2025; drift can't
explain a gap that isn't drifting. See §10.2.

**Round 2** re-examined the definition itself instead of the timing, and
found a real numerator/denominator mismatch: `debt_to_gdp` measures debt
*held by the public*, but gross interest also includes intragovernmental
Government Account Series interest — a scope `debt_to_gdp` excludes. The
matrix was extended to 3×3 by adding **on-budget receipts** (total receipts
minus OASI+DI trust fund receipts, the statutory off-budget definition,
2 U.S.C. 622(7)) as a third denominator, computed from `mts_table_4`'s own
unambiguous trust-fund grand-total lines
(`on_budget_receipts_monthly()`) — not from `mts_table_5`'s "Total
On-Budget"/"Total Off-Budget" rows, which a live probe confirmed are outlay/
deficit figures, not receipts (only `current_month_net_outly_amt` is
populated on those rows, and it's negative — a monthly on-budget deficit).
Live result (2026-07-19, second run of the day):

```
numerator                          on-budget receipts   tax receipts only   total receipts
gross (incl. GAS)                          29.7%              35.0%              23.0%
net-to-public (excl. GAS)                  23.1%              27.8%              17.9%
net interest, function 900                 23.0%              27.8%              17.8%
```

**Net-to-public / on-budget receipts (23.1%) is now the live headline basis**
— it's the economically consistent pairing (net interest to the public,
same "to the public" scope as the debt stock it's compared against), and it
happens to also match Dalio's 22% about as closely as gross/total-receipts
did (~1pt), so the switch cost nothing on fit while fixing the scope
mismatch. **Gross interest / on-budget receipts (29.7%) ships as an
explicit second row** ("Gross interest (incl. intragovernmental)"), not
folded into the headline — GAS interest is a real future claim (credited to
trust funds as bonds, not paid in cash) but isn't cash leaving the
government today.

The **residual vs. Dalio's 22% is still ~1pt and still not fully
explained** — see §10.2's retraction for what evidence does and doesn't
support here. Stated plainly: this is *closer to* Dalio's figure on
defensible definitional grounds, not a fully reconciled match.

The chosen basis is recorded in `data.json`'s `provenance.debtServiceBasis`,
`grossDebtServiceBasis`, and a new shared `revenueDefinition` string (the
on-budget-receipts definition, referenced by both debt-service rows and the
new debt/revenue row — see below), and in each row's own `src`.

**Two separate sanity bands**, re-set for the new bases rather than reusing
the old shared one: net interest 10–40% (23.1% comfortably inside), gross
interest 15–50% (29.7% comfortably inside).

### Debt / revenue (new row, alongside debt / GDP)
Dalio's Ch.17 table reports debt/GDP, but Ch.3 argues debt/revenue is the
more meaningful figure (GDP isn't the government's to spend; receipts are).
Added as a second row in the "Government debt" panel, not a replacement for
the headline `debt_to_gdp` vital (which stays, since it's the figure the
§9 calibration is actually checked against). Computed with no new series:
`debt$ = FYGFGDQ188S (%) × GDP ($)`, divided by the same on-budget-receipts
TTM denominator as both debt-service rows (`series.py::debt_to_revenue_pct`,
`treasury.py::revenue_ttm_dollars`). **Live result (2026-07-19, confirmed
end-to-end in `public/data.json`): debt/GDP 99%, debt/revenue 692%** — very
different scales by design (hundreds of percent vs. ~100%), so the two rows
are not visually confusable, and `Chart.jsx` scales each row's sparkline
y-axis independently already (confirmed by reading the component: each
`MetricRow` renders its own `<Chart data={r.history}>` instance, and
`niceDomain()` computes min/max from that instance's own data — no shared
axis to worry about). Sanity band 200–1200%, wide enough for real movement,
tight enough to catch a units error (FYGFGDQ188S is a percent, GDP is
billions SAAR — confirmed, not assumed, by reading both units strings
`--verify` dumps). Dalio's table has no debt/revenue figure to calibrate
against — noted in §9 rather than left blank.

### IMF COFER via DBnomics (`scripts/imf.py`) — reserve-currency USD share
No API key. Feeds the "World CB reserves in USD" row in the reserve-currency
panel.

**IMF's own legacy API host (`dataservices.imf.org`) is decommissioned** — DNS
doesn't resolve. Discovered live in CI, not documented anywhere I could find
beforehand. Repointed at **DBnomics** (`api.db.nomics.world`), a free,
stable, no-key mirror of IMF datasets.

Two more bugs after the DBnomics switch:
1. First attempt tried to sum per-currency components
   (`RAXGFXAR<CUR>_USD`) to compute a share, with a wrong currency-code regex
   (missed `EURO`, used `US` instead of the actual `USD` 3-letter code) →
   "no USD/total overlap" failure (safe: fell back to manual, didn't ship
   garbage).
2. The `--verify` dump revealed DBnomics actually exposes a **ready-made
   percent series** — `Q.W00.RAXGFXARUSDRT_PT` — so the fix was to read that
   directly instead of summing anything. Much simpler, and it's what ships
   today.

**Fallback behavior (by design, and proven to work in practice):** if COFER
is unreachable or malformed, the build catches the exception, logs it, and
falls back to the static value in `data/manual.json` — the monthly run stays
green either way. This fired for real on two separate live runs before the
final fix landed (both times: no crash, no bad data, just the old manual
number shipped).

**Current value: live**, quarterly history from 1999, `tag: "live"`,
`src: "IMF COFER (DBnomics)"`.

### Reserves including gold at market value (`scripts/gold.py`) — RESOLVED 2026-07-19
This is the "reserves discrepancy" §9 explains in full — flagged by a Ch.17
calibration comparison, not by anything in an earlier version of this file.
`TRESEGUSM052N` is *"Total Reserves EXCLUDING Gold"* by its own name — it
structurally can't reconcile with Dalio's "FX reserves, 3% of GDP" figure.
US reserves excl. gold alone are ~0.8% of GDP; the gap is the US's ~261.5M
troy oz of gold, carried by Treasury at a $42.2222/oz statutory book rate
(~$11B) instead of market value ($876.5B in the 2026-07-19 live run).

Fix: `scripts/gold.py` composes Treasury's gold holdings (troy oz, monthly,
`/v2/accounting/od/gold_reserve`) × a live gold price, valued at **market**,
added to FRED's excl.-gold reserves, over GDP.

Getting a live, no-key gold **price** took three attempts, all against
DBnomics (`api.db.nomics.world`), because the obvious source turned out to be
dead upstream, not just a wrong URL guess:
1. `LBMA/gold_D/gold_D_USD_AM` (direct series path) → 404.
2. `LBMA/gold_D` with a `dimensions` filter → also 404.
3. A bare, unfiltered dump of `LBMA/gold_D` → **still** 404 — at this point
   the dataset itself, not the query shape, was the problem. Confirmed via
   web research (not guessed): LBMA moved its benchmark price tables behind
   a members-only portal starting the week of 2025-11-24, and FRED's own
   mirror of the same series (`GOLDAMGBD228NLBM`) was separately discontinued
   with no replacement — DBnomics' LBMA dataset was downstream of the same
   now-restricted source.
4. Switched to **IMF's Primary Commodity Price System** (PCPS, indicator
   `PGOLD`), mirrored on DBnomics under the same `IMF` provider that already
   works for COFER. This worked — no 404 — but PCPS carries four series per
   commodity per frequency (`.IX` index, two `.PC_*` percent-change series,
   `.USD` the actual dollar level), and the first live run picked the wrong
   one: `M.W00.PGOLD.IX` (~268, a rebased index), not `M.W00.PGOLD.USD`
   (~$3,352/oz). That fed a ~10x-too-low price into the market-value calc.
   Fixed by filtering matches down to series ending `.USD` before picking a
   frequency.

**Confirmed live (2026-07-19 run):** gold price `M.W00.PGOLD.USD` =
$3,351.86/oz → gold market value $876.5B → **reserves incl. gold = 3.7% of
GDP**, `tag: "live"`, reconciling closely to Dalio's 3% (residual attributed
to the same time-snapshot gap as debt service, plus PCPS's own reporting lag
— see the note below).

**Both rows ship, separately labelled, per the task's requirement not to
collapse two different things into one number:**
- `"Reserves incl. gold (market)"` — the new headline `reserves_to_gdp`
  vital, `tag: "live"` when the gold fetch succeeds.
- `"FX reserves excl. gold"` — `TRESEGUSM052N` alone, kept as a separate
  panel row so the FX-only figure isn't discarded.

**Fallback (proven, not just written):** if either the Treasury gold-holdings
fetch or the DBnomics price fetch fails, `gold_market_value_usd()` raises and
`fetch.py` catches it, falling back to `data/manual.json`'s
`reservesInclGoldFallback` (3.0%, `tag: "manual"`) rather than shipping a
live-tagged number built on a stale price. This fired for real during
development (both LBMA-404 attempts degraded cleanly to the manual value,
no build breakage) before the PCPS fix made the live path actually succeed.

**Gold-price staleness: retracted claim, corrected 2026-07-19.** The prior
write-up here said the ~13-month lag (PCPS's `PGOLD.USD` last observed
2025-06 as of a 2026-07-19 run, vs. Treasury's gold-holdings figure current
to 2026-06) was "a genuine reporting lag in the IMF PCPS dataset itself
(confirmed via the `--verify` dump, not assumed)." **That claim was too
strong and is retracted.** The `--verify` dump confirms only that
**DBnomics** returns nothing after 2025-06 for that series — it says
nothing about IMF's own PCPS publication schedule, because this pipeline
has never queried IMF directly, only DBnomics' mirror of it. Confirming vs.
assuming the *mirror* is stale is not the same as confirming vs. assuming
*IMF itself* is stale, and the two were conflated.

**What's actually known, from research (not from live introspection — IMF's
own API isn't reachable from this sandbox either):** IMF's Primary
Commodity Price System publishes monthly data in the first full week of the
following month. If that cadence holds, IMF should have had June 2026 data
available well before this pipeline's 2026-07-19 run — meaning **a stale
DBnomics mirror is the more likely explanation**, not a stale IMF
publication, though this is inferred from IMF's documented general cadence,
not verified against IMF's raw feed for this specific series. **Report:
DBnomics mirror is more likely stale than IMF itself — not confirmed
either way by direct comparison.**

**What was NOT done this session, flagged as a next step:** IMF publishes a
modern SDMX 3.0 API directly (`api.imf.org`) that could be queried without
going through DBnomics at all, which would let a live run compare IMF's own
latest PGOLD observation against DBnomics' mirror directly — the strongest
possible test of which one is actually behind. This wasn't implemented:
adding a second gold-price integration is real scope, and the higher-value
fix (below) was judged more urgent given the time available.

**UI fix that WAS done:** regardless of which side is stale, shipping a
`tag: "live"` reserves figure that silently mixes a 2026-06 gold-holdings
count with a 2025-06 gold price was the more directly actionable problem —
a reader has no way to know that from the number alone. Fixed: `src` now
names both dates explicitly whenever they differ (e.g. `"Treasury (gold oz
2026-06) + DBnomics (price 2025-06)"`, confirmed live in the 2026-07-19
run — see `docs/current-values.md`), instead of a generic string that reads
as fully current. The tag stays `"live"` rather than being downgraded,
since both components genuinely are live data, just not from the same
month — downgrading the tag would hide that distinction rather than
surface it.

The chosen basis is recorded in `provenance.reservesBasis` and
`provenance.reservesInclGoldTag`, and in the `reserves_to_gdp` vital's `src`.
A **sanity band** (`0.5% ≤ ratio ≤ 15%`) guards the live path.

---

## 4. GitHub Actions: has it actually run, and when

Both workflows exist on `main` and have executed successfully against live
infrastructure — this was proven interactively during the session (I
triggered `workflow_dispatch` runs directly via the GitHub API and read the
job logs), not just written and assumed to work.

- **`update-data.yml`** — cron `0 6 5 * *` (06:00 UTC, 5th of each month) +
  manual dispatch with a `force` boolean input (bypasses the
  value-move guard, needed the first time a legitimate number moved >25%
  after a source swap).
  **On `main`**, the last confirmed successful run produced `debt_to_gdp=99%`,
  `debt_service_to_revenue=18%`, `real_rates=0.6%`, `reserves_to_gdp=0.8%`.
  **This session's debt-service and reserves fixes (§3) have been verified
  live via `workflow_dispatch` on `claude/new-session-ldotj8` only** —
  several runs there confirm `debt_service_to_revenue=23%` and
  `reserves_to_gdp=3.7%` end-to-end (see §9), but per this session's branch
  policy those commits have **not been merged to `main`**, so the live site
  (deployed from `main`) still shows the pre-fix 18%/0.8% figures as of this
  writing. Merging `claude/new-session-ldotj8` (or opening a PR for it) is
  the remaining step to get these values onto the live site — deliberately
  left for explicit approval rather than done unilaterally.
  **The cron has not yet fired on its own** (only `workflow_dispatch` runs
  have happened so far, since the project is only hours old) — the schedule
  will produce its first unattended run around the 5th of next month. If
  you're reading this a month+ later, check whether that happened cleanly.
- **`deploy.yml`** — triggers on push to `main`, on `workflow_dispatch`, and
  via `workflow_run` after `update-data.yml` completes (a bot commit doesn't
  itself trigger `push`). Confirmed successful multiple times, most recently
  after every data-fixing commit landed.

**Check current status yourself** rather than trusting this file's dates:
`https://github.com/willywonka616/macro-indicator-dashboard/actions`

**Known rough edge, not a bug:** on a couple of runs, the `update-data.yml`
job queued for 20–60s longer than usual before a runner picked it up. Not
investigated further — didn't affect correctness, just wall-clock time.

---

## 5. Current `data.json` schema — drift from the brief

The brief's example schema (§4 of the original brief) is followed closely.
Verified directly against the live file (206,311 bytes / ~206 KB as of last
commit — the
brief's "downsample + separate `history/` file if it gets large" contingency
has **not been needed** and is **not implemented**; revisit if size becomes a
real problem, but 206 KB is not that).

**Additions beyond the brief's example** (both intentional, neither asked
for explicitly, both defensible):
- Top-level **`meta`**: `{ "seed": bool, "schema": 1 }`. `seed: true` marks
  the bootstrap snapshot committed before the fetcher ever ran (checked into
  the repo so the site renders before CI's first pass); `seed: false` is what
  ships after any real fetch. `schema` is a version int, currently always `1`
  — bump it if the shape changes in a way old clients would choke on.
- Per-country **`provenance`**: `{ modelSnapshot, manualLastChecked,
  currentAccountAnnualizedInput }`. Exists so the UI/reader can see when the
  manual Dalio-model figures were last checked, and whether the current-
  account derivation treated the FRED input as already-annualized (see next
  paragraph).

**Everything else matches the brief's shape**: `vitals[]` have
`key/label/value/display/unit/tone/tag/src/asOf/history`; panel `rows[]` have
the same live/manual shape; `history` is `[{y: decimalYear, v: value}]` at
native-ish frequency (Treasury history is pre-downsampled to one point per
quarter in `treasury.py`; FRED-sourced history is quarterly-native already
for the quarterly series, and derived-and-collapsed to quarterly for the
originally-monthly ones).

**Unverified assumption, flagged not confirmed:** `current_account_pct_gdp_3yr`
in `series.py` decides whether to annualize the raw current-account flow
based on whether FRED's reported units string for `IEABC` contains "annual
rate." I have **not manually confirmed** what that units string actually
says by reading a live `--verify` dump specifically for `IEABC` — the code
branches on it automatically and the current output value (~-4% of GDP, 95
history points) looks directionally sane, but this specific unit-detection
branch is inferred, not eyeballed. `provenance.currentAccountAnnualizedInput`
in the live data.json records which branch fired, which is the fastest way
to check.

*(This is a separate, still-open item from the debt-service and reserves
assumptions resolved this session — see §3 and §9. Nobody has re-verified
this one yet.)*

---

## 6. What's stubbed, manual, or hardcoded — and why (per-item)

Every one of these is `tag: "manual"` in `data.json` and shows the
provenance badge in the UI. None of it is hidden or unlabeled.

| What | Why manual | Brief said |
|---|---|---|
| **Dalio's Z-score gauges** (headline gov/cb, short-term level, full gov/cb gauge component rows) | The derivation is **not published in any of his sources** — confirmed by the user, who searched independently. Recomputing it would be fabrication. | Brief was explicit: never approximate this. Correctly honored. Later moved to the very bottom of the page (user request) with a caveat paragraph explaining why. |
| **Debt held by central bank / domestic / abroad (%)** | TIC data needs its own parsing pass | Brief explicitly deferred this: "do this in a later pass, not v1." Correctly deferred, still todo. |
| **CBO 10-year debt projection** | Annual publication, no clean API | Brief said manual/annual is fine. As specified. |
| **Sovereign wealth assets, "share in hard FX," gov-assets-minus-debt** | No live source identified/attempted | Static since the legacy dashboard; not revisited this session. |
| **World trade in USD / World debt in USD / Global equity market cap** (3 of 4 reserve-currency shares) | No free, reliable API found (SWIFT-style trade data is PDF/monthly with shifting definitions; BIS debt share needs derivation from a non-trivial dataset; equity market cap needs commercial data) | Brief flagged these as hard; only "world CB reserves" (the 4th share) got automated this session via IMF COFER, per explicit user ask. |
| **Two red flags text, all interpretation prose in `commentary.js`** | Brief required this be hand-written, never auto-generated, no LLM call | Correctly honored — it's static prose carried over from the legacy dashboard, with a few "stale-risk" comments flagging which claims are pinned to which live numbers. |
| **`reservesInclGoldFallback` (3.0%, `data/manual.json`)** | Not stubbed by design — this is a **fallback**, only shipped if the live Treasury gold-holdings or DBnomics gold-price fetch fails (see §3's reserves subsection). The live path has been confirmed working as of the 2026-07-19 run; this exists purely so a source hiccup degrades gracefully instead of shipping a stale-priced number tagged `live`. | Not in the original brief — added this session per the task that resolved the reserves discrepancy. |

**Nothing in the live-tagged data path is faked.** Every `tag: "live"` value
traces to a real HTTP call to FRED, Treasury, or IMF/DBnomics in
`scripts/fetch.py` — there is no hardcoded live-looking number anywhere in
the Python or JS.

---

## 7. Known bugs / rough edges (open, as of last commit)

- **None are currently known-broken and unfixed** as far as I can tell — every
  bug found this session (wrong receipts table, excluded amortized discount,
  wrong COFER currency codes, transient network drops, mismatched debt
  headline number, y-vs-x-axis label collision) was fixed and verified before
  the session ended.
- **Soft spot, not a bug:** the crisis-marker label layout in `Chart.jsx`
  (`LABEL_MIN_GAP = 16`) cascades labels rightward with a guaranteed minimum
  pixel gap to avoid collisions — verified at 1100px and 390px (phone) widths
  via headless-browser DOM inspection. It has not been tested below ~390px or
  with more than 7 crisis markers; if more markers are added later and start
  cascading off the right edge of the chart on narrow phones, this is the
  function to revisit (`src/components/Chart.jsx`, the `crises` computation
  right before the SVG render).
- **One assumption still open** (see §5's `IEABC` annualization-detection
  branch) — produces sane-looking output but hasn't been manually
  cross-checked against an authoritative definition. The Treasury
  "net interest" assumption that used to be flagged alongside it was
  resolved this session (§3, §9) — replaced with a gross-interest basis
  cross-checked against named GAO/CBO figures.
- **Debt/GDP now reads "held by the public" (`FYGFGDQ188S`, ~99%), not gross
  debt (`GFDEGDQ188S`, ~123%).** This is a deliberate, user-approved
  deviation from the brief's original candidate ID, not a bug — flagging it
  here only because it's the single biggest number on the page and worth
  double-checking if Dalio's own figures ever seem to disagree.
- **The gold price DBnomics returns lags ~13 months** (last observed
  2025-06 as of the 2026-07-19 run) behind Treasury's gold-holdings figure.
  A prior write-up here called this "confirmed" to be an IMF PCPS upstream
  lag — **that was too strong and has been retracted** (see §3's reserves
  subsection): the `--verify` dump only confirms DBnomics' mirror is
  behind, not that IMF's own publication is. Research suggests DBnomics is
  the more likely stale link (IMF's documented cadence would have June 2026
  data out by now), but this is not directly verified. The reserves row's
  `src` now names both dates explicitly so the gap is visible regardless of
  which side is actually behind.
- **This session's fixes live on `claude/new-session-ldotj8`, not yet merged
  to `main`** (see §4) — the live site does not yet reflect this session's
  or the prior session's figures (debt service now 23.1% net/on-budget,
  reserves 3.7%, debt/revenue 692% new, total debt 362.6%). Merging is the
  next step.

---

## 8. What's next

In rough priority order, based on what the brief and the user's requests
left open:

1. **Merge `claude/new-session-ldotj8` to `main`** (or open a PR for it) so
   this session's debt-service and reserves fixes actually reach the live
   site — deliberately not done unilaterally, see §4/§7.
2. **Let the monthly cron actually fire once unattended** and confirm it
   behaves the same as the manual `workflow_dispatch` runs did. Nobody has
   observed a real scheduled (non-manual) run yet.
3. **Euro area** (brief's explicit step 8, and the user has referenced it as
   the natural next expansion): new key under `countries` in `data.json`,
   new manual entries in `data/manual.json`, ECB/Eurostat sources in a new
   fetcher module, new commentary in `commentary.js`. **No component changes
   needed** — `src/App.jsx` and everything under `src/components/` are
   already country-agnostic (the country switcher is driven by
   `Object.keys(data.countries)`).
4. **TIC-based holder breakdown** (central bank / domestic / foreign %) —
   explicitly deferred by the brief, still fully static.
5. **Consider automating one more reserve-currency share** if a free source
   turns up — BIS debt-in-USD is the next most plausible candidate (has an
   API, just needs a derivation), trade and equity are probably permanently
   manual without a paid data source.
6. **Re-verify the `IEABC` current-account annualization assumption** (§5) —
   the one remaining unverified-but-plausible branch; low urgency since the
   output number looks directionally sane.
7. **Query IMF's own SDMX 3.0 API directly** (`api.imf.org`) for the latest
   PGOLD observation and compare it against DBnomics' mirror — the direct
   test of which side is actually stale (§3), not yet implemented. If
   DBnomics is confirmed behind, either switch the live source to IMF
   directly or find another live mirror.
8. **Investigate what Dalio's "other debt" (340%) row actually scopes** (§9)
   — TCMDO (all sectors, 362.6%) is the closer of two tried series but still
   22.6pts over; TCMDODNS (nonfinancial only) was refuted, not confirmed.
   Untested idea: total debt minus government debt, to avoid double-counting
   against the debt/GDP row shown separately.

---

## 9. Calibration against Dalio's Ch.17 US column

This project's work has repeatedly started from a direct comparison of this
pipeline's live output against the actual published numbers in the US
column of *How Countries Go Broke* Ch.17 (March 2025 snapshot). **This
comparison is the strongest correctness check this project has** — every
real gap found so far (debt service, reserves, total debt) was invisible to
sanity bands and local mock tests, because the wrong numbers all looked
"sane" in isolation. Extended below (2026-07-19, second pass) to cover
*every* book row with a published figure, not just the two flagged in the
first pass, per an external review that pointed out a 23-point total-debt
gap had gone unnoticed because it was never added to this table.

| Metric | Dalio Ch.17 (US, Mar 2025) | This pipeline (2026-07-19) | Basis | Match? |
|---|---|---|---|---|
| Debt held by public / GDP | ~100% (99%) | 99% | live, `FYGFGDQ188S` | Matches closely |
| Debt, 10-yr projection / GDP | 122% | 122% | **manual**, carried from `data/manual.json` (CBO) | Trivial — same figure, not independently derived |
| Held by CB / domestic / abroad | 13% / 57% / 29% | 13% / 57% / 29% | **manual**, carried from `data/manual.json` (TIC) | Trivial — same figures, not independently derived |
| Debt service / revenue | 22% | 23.1% (net-to-public / on-budget receipts) | live, `scripts/treasury.py` | Close but not exact — see §3, §10.2's retraction. Residual ~1pt, unexplained |
| FX reserves / GDP | 3% | 3.7% (excl.-gold FX + gold at market) | live, `scripts/gold.py` + FRED | Close but not exact — residual ~0.7pt, attributed partly to the gold-price staleness (§3/§7) |
| Total debt (Dalio's "other debt") / GDP | 340% | 362.6% (TCMDO, all sectors incl. financial) | live, `FRED: TCMDO` | **Does not match** — +22.6pt gap. A nonfinancial-only alternative (TCMDODNS) was tried and made it *worse* (256.7%, -83pt) — see below |
| Current account, 3-yr avg / GDP | −4% | −3.7% | live, `IEABC` (FRED) | Matches closely |
| World trade in USD | 52.6% | 52.6% | **manual**, carried from `data/manual.json` | Trivial — same figure |
| World debt in USD | 80.7% | 80.7% | **manual**, carried from `data/manual.json` | Trivial — same figure |
| Global equity market cap in USD | 65.7% | 65.7% | **manual**, carried from `data/manual.json` | Trivial — same figure |
| World CB reserves in USD | 57.0% | 57.7% | live, IMF COFER via DBnomics | Matches closely — independently computed, not carried |
| Debt / on-budget revenue | *(no book figure)* | 692% | live, derived (§3) | **No book value to calibrate against** — Dalio's table reports only debt/GDP; noted here rather than left blank, per the task that added this row |

**Read the "Basis" column before trusting a "match."** Six of the twelve
rows are `manual` — hand-carried from `data/manual.json`, which in most
cases was originally *transcribed from this same book*. Those matching is
not a validation of anything; it would be surprising if they didn't match.
The rows worth trusting as genuine checks are the `live` ones — five
numbers this pipeline actually derived from FRED/Treasury/DBnomics without
looking at Dalio's figure first, three of which land close (debt/GDP,
current account, COFER share) and two of which don't fully reconcile
(debt service, reserves) despite real investigation.

**Three rows needed more than a bug fix — a definitional decision or a new
data source:**
- **Debt service**: required deciding which numerator (gross vs.
  net-to-public vs. function-900) and denominator (tax receipts, total
  receipts, or on-budget receipts) this pipeline uses — a 3×3 matrix (§3)
  made all nine candidates explicit. The current basis (net-to-public /
  on-budget receipts) is chosen on definitional grounds, not because it's
  the closest fit to 22% (it ties with net-function-900/on-budget, and
  isn't meaningfully closer than the old gross/total-receipts basis was).
- **Reserves**: no amount of debugging FRED's `TRESEGUSM052N` alone could
  close this gap — the series structurally excludes gold. Required a new
  data source (Treasury gold holdings × a live gold price).
- **Total debt**: investigated but **not resolved**. TCMDO (all sectors) at
  362.6% is the closer of two tried series, but still 22.6pts over Dalio's
  340%. The hypothesis that "other debt" means nonfinancial-sectors-only
  was tested against TCMDODNS and refuted (256.7%, further from target, not
  closer). What Dalio's "other debt" row actually scopes remains unknown —
  possibly a different aggregation entirely (e.g. total minus government
  debt, to avoid double-counting the debt/GDP row above it — untested this
  session). **Reported as an open gap, not forced to reconcile.**

**Two rows already matched before this session** (debt/GDP, COFER USD
share) and needed no change. **One row has no book figure to compare
against** (debt/revenue) and is noted as such rather than left blank.

---

## 10. Review package, first round (2026-07-19, commit `4c344e1`) — HISTORICAL

> **This section is the first-round review package, kept for the record —
> it is not the current state.** A review of it (the task that produced §11
> below) caught a real error in §10.2 (now marked with an explicit
> retraction block, not silently fixed) and prompted further changes that
> superseded some of the numbers quoted here (the debt-service basis
> changed from gross/total-receipts to net/on-budget-receipts; total debt
> was investigated further). **For the current state, read §3, §9, and §11
> instead.** This section is left as-is (other than the one retraction
> block) so the review trail — what was claimed, what was wrong, what
> changed — stays visible rather than being overwritten.

Written for an AI assistant (or human) reviewing this project that **can
only read individual files by public GitHub blob URL** — it cannot open the
Actions tab, cannot browse directories, cannot read `git log`, and may be
served a cached copy of any file. Everything claimed below is either quoted
verbatim from a real file in this repo, or explicitly marked as inferred.
Base commit for everything in this section: `4c344e1` (branch
`claude/new-session-ldotj8`).

**Supporting files** (full paths from repo root):
- `docs/verification-log.md` — the actual Actions run output, pasted
  verbatim (timestamps/ANSI codes stripped only), including the 3×2 matrix,
  every `--verify` schema dump, the sanity-band source, and the prior
  gold-price failures.
- `docs/current-values.md` — every headline number as a table, with
  `tag`/`src`/`asOf`/`unit`, instead of asking the reviewer to parse the
  ~200KB `public/data.json` by hand.

> **Note:** these two files are overwritten in place on each regeneration,
> not versioned per round — as of this edit they've been **regenerated to
> match §11's current state** (3×3 matrix, new debt-service basis, fresh
> SHA/timestamp), so the "3×2 matrix" and other specifics described in
> §10.1–10.5 below no longer match what's actually in those files. §10's
> own prose is left as the historical record of what was true and quoted
> at the time; if you need the literal file contents from that round, they
> are only in `git log` for `docs/verification-log.md` /
> `docs/current-values.md` at or before commit `4c344e1`.

### 10.1 The 3×2 debt-service matrix, copied verbatim from the run log

```
  Debt-service calibration matrix (Dalio Ch.17 US target: 22%, Mar 2025):
  numerator                          tax receipts only        total receipts
  gross (incl. GAS)                              35.0%                 23.0%
  net-to-public (excl. GAS)                      27.8%                 17.9%
  net interest, function 900                     27.8%                 17.8%
```
**Claim status: VERIFIED** — copied from `docs/verification-log.md`, which
is itself a verbatim paste of the job log of a real `workflow_dispatch` run
(2026-07-19 12:03–12:05 UTC, commit `4c344e1`). I ran this and read the
output; it is not a recalculation or a re-derivation done just now.

**Combination adopted: gross (incl. GAS) ÷ total receipts = 23.0%.**
Why: it's the cell closest to Dalio's 22% target of all six, and — more
importantly than closeness alone — it's the only one that also matches a
named external statistic (§10.2). The other five cells were considered and
rejected: the two "total receipts" cells below it (17.9%, 17.8%) are what
this pipeline shipped *before* this session and are ~4pts off; the three
"tax receipts only" cells (35.0%, 27.8%, 27.8%) are all too high to be
plausible matches for a 22% target, because tax receipts alone
(`W006RC1Q027SBEA`-style) are a narrower denominator than Dalio's "revenue"
framing — this exact overstatement was already a documented bug earlier in
the project (STATUS.md §2, the original `W006RC1Q027SBEA` mis-use produced
33% for the same reason).

### 10.2 Named official statistic cross-check, and the exact residual

**Numerator (gross interest) checked against:** GAO, *Schedule of Federal
Debt*, report GAO-25-107138 — FY2024 gross interest expense on the total
public debt outstanding = **$1,126.5B**.
**Denominator (total receipts) checked against:** CBO, *Monthly Budget
Review*, FY2024 summary — total federal receipts = **$4.9T**.
**Independent ratio from those two named figures: $1,126.5B / $4,900B =
23.0%** (rounds to the same 23.0% this pipeline's live TTM computation
produced, from an entirely separate data path — Treasury Fiscal Data API
observations, not GAO/CBO publications).

**Residual vs. Dalio's 22%: +1.0 percentage point.** Stated plainly: this
does **not** exactly reconcile. My attribution — the book's figure is
pinned to a March 2025 snapshot; this pipeline computes a rolling
trailing-12-month ratio that, at the time of the run quoted above, ended
2026-06 — is a plausible explanation for a 1pt drift over roughly a year,
but it is **not independently confirmed**. I did not obtain Dalio's own
underlying month-by-month series to check whether the ratio was closer to
22% specifically in March 2025 and has since drifted to 23%, versus some
other cause (a data revision, a different treatment of GAS, etc.).
**Claim status for the attribution: ASSUMED, not verified.** The 23.0% ↔
23.0% match between this pipeline and the independent GAO/CBO figures *is*
verified; the *reason* for the 1pt gap to Dalio specifically is inferred.

> **⚠️ RETRACTED, 2026-07-19 (same day, after external review).** The
> timing-drift attribution two paragraphs up is **contradicted by this
> section's own evidence** and should not be trusted. The GAO/CBO
> cross-check above computes the **FY2024** ratio — a period ending
> September 2024, *before* Dalio's March 2025 snapshot — and it also came
> out to 23.0%. This pipeline's live rolling window (ending 2026-06) is
> *also* 23.0%. The ratio is flat at 23% on both sides of March 2025, which
> means it was already ~23% *at* March 2025 too — there is no drift for a
> timing gap to explain. Whatever the ~1pt gap to Dalio's 22% actually is,
> it is not this.
>
> This was caught precisely because the attribution was labelled ASSUMED
> rather than asserted as fact — the epistemic hygiene worked even though
> the inference itself didn't hold up. It is retracted here explicitly,
> not quietly edited out, so a future reader can see both the original
> mistake and the correction.
>
> **What actually changed as a result:** the debt-service basis itself was
> revised (see §3) — from gross interest / total receipts to net interest /
> on-budget receipts — on definitional grounds (a numerator/denominator
> scope mismatch, not a fix for this residual). The revised basis's
> residual (net-to-public / on-budget receipts = 23.1% vs. Dalio's 22%) is
> almost the same size (~1pt) as this one was. **The more likely
> explanation, unconfirmed:** a difference in Dalio's own revenue base or
> interest scope that this pipeline hasn't identified — possibly something
> in how he defines "revenue" that doesn't map cleanly onto any Treasury
> MTS line item tried here (on-budget, total, or tax-only), or a different
> treatment of what counts as "interest." **This has not been verified
> either** — it is offered as the more evidenced guess, not a resolved
> answer. Getting Dalio's own underlying figures (not available from public
> data as far as this project has found) is the only way to actually close
> this gap; barring that, it should stay marked as an open ~1pt residual,
> not explained away by any story about timing.

### 10.3 Reserves reconciliation

**What `TRESEGUSM052N` actually covers**, quoted verbatim from the FRED
metadata returned by `--verify` (see `docs/verification-log.md`):
```
TRESEGUSM052N      yes M          Millions of Dollars          1950-12-01   Total Reserves excluding Gold for United
```
i.e. the series title is *"Total Reserves excluding Gold for United
States"* — confirmed live against FRED's own metadata, not inferred from
the series ID alone. **Claim status: VERIFIED.**

**Gold holdings source:** US Treasury Fiscal Data API,
`/v2/accounting/od/gold_reserve` — 8 rows (by facility/form/location) as of
`record_date` 2026-06-30, summed to total fine troy ounces. Fields and
latest rows are quoted verbatim in `docs/verification-log.md`. This is
**quantity of gold** (troy oz), not a price — Treasury also reports a
`book_value_amt` per row, but that's the $42.2222/oz statutory rate, which
this pipeline explicitly does **not** use (see §3).

**Gold price source:** IMF Primary Commodity Price System (PCPS), indicator
`PGOLD`, series `M.W00.PGOLD.USD`, via DBnomics
(`https://api.db.nomics.world/v22/series/IMF/PCPS`). Confirmed live:
`selected series_code: M.W00.PGOLD.USD`, latest observation `2025-06 =
3351.85857142857 USD/oz` (quoted verbatim in `docs/verification-log.md`).

**Computed including-gold % of GDP: 3.7%** (`tag: "live"`,
`reserves_to_gdp` vital and the `"Reserves incl. gold (market)"` panel row —
both in `docs/current-values.md`, sourced from `public/data.json` at commit
`4c344e1`). Composition: gold holdings (troy oz, 2026-06-30) × PCPS gold
price ($3,351.86/oz, dated 2025-06) = **$876.5B** gold market value, plus
FRED's excl.-gold reserves, over nominal GDP. **Claim status: VERIFIED** —
read directly from the committed `public/data.json`, not recomputed for
this section.

### 10.4 What did NOT reconcile — stated plainly

- **Residual vs. Dalio's 3% target: +0.7 percentage points** (3.7% vs 3%).
  Larger, proportionally, than the debt-service residual. Not explained by
  a single clean cause — see the next two points, both of which contribute
  and neither of which is fully quantified.
- **The gold price and the gold quantity are not from the same point in
  time.** Treasury's holdings figure is dated 2026-06-30 (current to the
  month before this run). The PCPS gold price is dated 2025-06 — **over a
  year older**. The $876.5B market-value figure therefore multiplies a
  current quantity by a stale price, not a fully current snapshot. This is
  a genuine data-quality gap in the live pipeline, not a display artifact:
  if gold's actual price in mid-2026 differs materially from its mid-2025
  price, the true current market value (and therefore the true current
  reserves-incl-gold %) differs from what `data.json` reports.
- **The two reserves panel rows carry different `asOf` dates** (2025-Q2 for
  incl.-gold, 2026-Q1 for excl.-gold — see `docs/current-values.md`) for the
  same reason: the incl.-gold figure is bottlenecked by PCPS's lag.
- **This was not corrected or compensated for.** No attempt was made to
  inflate the stale gold price to a current estimate, or to flag the
  specific figure as extra-stale in the UI beyond the existing `asOf` field.
  The pipeline ships the real PCPS observation as-is, most-recent-available,
  same as every other live series in this project — but the resulting
  ~13-month price lag is real and unresolved, not smoothed into the 3.7%
  headline number.
- **Debt service's 1pt residual (§10.2) is attributed but not confirmed** —
  restated here because "did not fully reconcile" applies to both metrics,
  not just reserves.

### 10.5 Verified vs. assumed — summary

| Claim | Status |
|---|---|
| 3×2 matrix values (all six cells) | **VERIFIED** — read from a real run log |
| Gross/total-receipts (23.0%) is the closest cell to Dalio's 22% | **VERIFIED** — arithmetic on the quoted matrix |
| 23.0% matches an independent GAO+CBO calculation | **VERIFIED** — both source figures are named, publicly citable statistics |
| The 1pt gap to Dalio is caused by the March-2025-vs-rolling-TTM timing difference | **ASSUMED, then REFUTED** — labelled assumed rather than verified at the time (correctly), and subsequently shown to be wrong by this section's own evidence — see §10.2's retraction block |
| `TRESEGUSM052N` = "Total Reserves excluding Gold" | **VERIFIED** — quoted from live FRED metadata |
| Gold holdings = 2026-06-30, ~261.5M troy oz (sum of 8 Treasury rows) | **VERIFIED** — quoted from live Treasury API response |
| Gold price = $3,351.86/oz, dated PCPS 2025-06 | **VERIFIED** — quoted from live DBnomics/PCPS response |
| Gold market value = $876.5B | **VERIFIED** — printed by the run itself, not recomputed here |
| Reserves incl. gold = 3.7% of GDP, `tag: "live"` | **VERIFIED** — read from committed `public/data.json` |
| The 0.7pt gap to Dalio's 3% is caused by the same timing issue as debt service | **NOT CLAIMED** — see §10.4; the price/quantity time-mismatch is a distinct, larger, and unquantified factor |
| These fixes are live on `main` / on the deployed site | **FALSE, explicitly** — see §4/§8; verified only on `claude/new-session-ldotj8` via direct `workflow_dispatch` |

---

## 11. Review package, second round (2026-07-19, current state)

This is the **current** review package — supersedes §10's numbers (§10
itself is kept, marked historical, not deleted). Base commit: `3ed5858`
(branch `claude/new-session-ldotj8`). Same file-only-reviewer constraints
as §10 (no Actions tab, no directory browsing, no `git log`); same
`docs/verification-log.md` / `docs/current-values.md` support files,
regenerated this pass with the fresh SHA/timestamp at their own top.

### 11.1 The 3×3 debt-service matrix, copied verbatim from the run log
```
  Debt-service calibration matrix (Dalio Ch.17 US target: 22%, Mar 2025):
  numerator                         on-budget receipts     tax receipts only        total receipts
  gross (incl. GAS)                              29.7%                 35.0%                 23.0%
  net-to-public (excl. GAS)                      23.1%                 27.8%                 17.9%
  net interest, function 900                     23.0%                 27.8%                 17.8%
```
**Claim status: VERIFIED** — copied from the `workflow_dispatch` run
attached to commit `bb1d887` (2026-07-19 18:06–18:08 UTC; the on-budget
column and the two ratios themselves are unchanged by the two commits
since, which only touched total-debt and commentary), pasted into
`docs/verification-log.md` verbatim.

**Combination adopted: net-to-public (excl. GAS) ÷ on-budget receipts =
23.1%**, ships as the headline `debt_service_to_revenue`. Gross ÷ on-budget
(29.7%) ships as the explicit second row. See §3 for the full reasoning
(numerator/denominator scope consistency, not just closeness-to-22%) and
§10.2's retraction block for what changed since round one.

### 11.2 What reconciles, what doesn't — updated residuals

| Row | Dalio | Live | Residual | Status |
|---|---|---|---|---|
| Debt service (net/on-budget) | 22% | 23.1% | +1.0pt | Not reconciled — cause unknown, see §10.2 retraction |
| Reserves (incl. gold) | 3% | 3.7% | +0.7pt | Not reconciled — gold price/quantity date mismatch is a real, unquantified contributor, see §3 |
| Total debt (TCMDO) | 340% | 362.6% | +22.6pt | Not reconciled — TCMDODNS hypothesis tested and refuted (256.7%, further off), see §9 |
| Debt/GDP | ~100% | 99% | ~0pt | Reconciles |
| Current account | −4% | −3.7% | ~0.3pt | Reconciles |
| COFER USD share | 57.0% | 57.7% | 0.7pt | Reconciles (closely) |
| Debt/revenue | *n/a* | 692% | *n/a* | No book figure to compare |

**Three of seven live-derived rows don't fully reconcile.** That's stated
plainly, not smoothed into "close enough" — each has a named, specific
open question (§3, §9) rather than a hand-wave.

### 11.3 What was checked and found NOT to hold — the two refutations this round

1. **Timing-drift explanation for the debt-service residual** (§10.2):
   refuted by the review's own point that the GAO/CBO FY2024 cross-check
   predates Dalio's snapshot and still shows 23%, so there's no drift to
   attribute the gap to. Retracted explicitly (§10.2's retraction block),
   not silently removed.
2. **Nonfinancial-sectors-only total debt (TCMDODNS)** (§9): tried on the
   hypothesis that it would close the gap to Dalio's 340% "other debt"
   figure. Live result: 256.7%, an 83pt gap — worse than TCMDO's 22.6pt
   gap, not better. Reverted; the hypothesis is refuted, not just unproven.

Both refutations exist in this file because a specific, falsifiable claim
was made and then actually checked against live data, rather than assumed
correct because it sounded plausible. That's the pattern worth continuing.

### 11.4 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| 3×3 matrix values (all nine cells) | **VERIFIED** — read from a real run log |
| Net-to-public/on-budget (23.1%) is the numerator/denominator-consistent choice | **VERIFIED** — debt_to_gdp's own scope (held by the public) is a documented fact about FYGFGDQ188S, matched against net_to_public_interest_monthly's documented scope |
| 23.1% is close to Dalio's 22% | **VERIFIED** — arithmetic on the quoted matrix |
| The remaining ~1pt gap is caused by a revenue-base or interest-scope difference in Dalio's own methodology | **ASSUMED, not verified** — offered as the more evidenced guess after retracting the timing explanation; not confirmed |
| TCMDODNS is a worse match than TCMDO for Dalio's "other debt" | **VERIFIED** — both read from the same live run's `--verify` diagnostic dump |
| DBnomics' gold-price mirror is more likely stale than IMF's own PCPS publication | **ASSUMED, not verified** — inferred from IMF's documented ~1-week publication cadence, not from directly querying IMF's own API |
| Gold price/holdings date mismatch is now visible in `src` | **VERIFIED** — read from committed `public/data.json`: `"Treasury (gold oz 2026-06) + DBnomics (price 2025-06)"` |
| Debt/revenue = 692%, `tag: "live"` | **VERIFIED** — read from committed `public/data.json` |
| Debt/revenue and debt/GDP are visually distinguishable | **VERIFIED** — different scales (692% vs 99%) and `Chart.jsx`'s `niceDomain()` is confirmed (by reading the component) to compute each row's y-axis independently from that row's own history |
| These fixes are live on `main` / the deployed site | **FALSE, explicitly** — still only on `claude/new-session-ldotj8`, same as §10's finding; unchanged this round |

---

## Meta: how to keep this file honest

- Don't hand-wave dates or run outcomes — check the Actions tab
  (`https://github.com/willywonka616/macro-indicator-dashboard/actions`) and
  quote what you actually saw, the way this file's §4 does.
- When you fix something, note *what broke and how you found out*, not just
  the fix — that's what made this file useful to write and should make it
  useful to read.
- Mark every claim as verified (you ran it / read the log / inspected the
  file) or assumed (you inferred it and didn't double-check) — see §3 and §5
  for the pattern.
