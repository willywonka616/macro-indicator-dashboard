# STATUS

Living document. **Update this at the end of every session** — that's the
instruction this file was created under, and it stands going forward. Written
for another AI assistant (or human) picking this up cold, with no memory of
prior sessions and no access to this repo's chat history.

Last updated: **2026-07-19**, by Claude (Sonnet 5). This session closed out
two items §3 had flagged as unverified assumptions (debt-service basis) and
resolved a reserves discrepancy against Dalio's Ch.17 US figures that hadn't
been caught before (§3, new subsection, and §9). See §9 for the calibration
comparison this work was built around, and **§10 for a self-contained
review package** built for a reviewer who can only read individual files by
public GitHub blob URL (no Actions tab, no directory browsing, no commit
history) — `docs/verification-log.md` and `docs/current-values.md`.

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

**RESOLVED 2026-07-19** (was flagged unverified above — see §9 for the full
calibration comparison). Dalio's Ch.17 book value for the US is **22%**; the
"net interest to the public" basis this file used to ship (~18%) was ~4pts
off, and had never been checked against a named official statistic.

What was done: computed a 3×2 matrix (numerator ∈ {gross interest incl. GAS,
net-to-public excl. GAS, net interest via Treasury's function-900
classification} × denominator ∈ {tax receipts only, total receipts}) and
printed it in the `--verify` run log every run
(`scripts/treasury.py::debt_service_matrix`). Live result (2026-07-19 run):

```
numerator                          tax receipts only   total receipts
gross (incl. GAS)                        35.0%              23.0%
net-to-public (excl. GAS)                27.8%              17.9%
net interest, function 900               27.8%              17.8%
```

**Gross interest / total receipts (23.0%)** is closest to Dalio's 22% and was
adopted as the new live basis. Cross-checked against two named official
statistics, independent of this pipeline's own math: FY2024 gross interest on
the total public debt = **$1,126.5B** (GAO, *Schedule of Federal Debt*,
GAO-25-107138) and FY2024 total federal receipts = **$4.9T** (CBO Monthly
Budget Review) → **23.0%**, matching this pipeline's live TTM figure almost
exactly. Residual vs. Dalio's 22% (~1pt) is attributed to the time-snapshot
difference — his figure is pinned to the book's March 2025 baseline, this
pipeline's is a rolling trailing-12-month window that currently ends 2026-06.

The chosen basis is recorded in `data.json`'s `provenance.debtServiceBasis`
(a plain-English string) and in the `debt_service_to_revenue` vital's `src`
(`"derived · Treasury (gross interest, budget basis)"`) and the `gov_panel`
row label (`"Government interest (gross)"`) — the switch from net-to-public
to gross is visible in both places, not just the number.

The existing **sanity band** (`5% ≤ ratio ≤ 40%`) was re-checked against the
new gross basis rather than assumed still-correct: 23% sits comfortably
inside it (with headroom up toward the tax-only gross figure of 35% if
receipts data ever narrows), so it was left unchanged.

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

**Known lag, not a bug:** PCPS's `PGOLD.USD` series was last observed
**2025-06** as of the 2026-07-19 run — over a year stale relative to the run
date, even though Treasury's gold-holdings figure is current to 2026-06.
This is a genuine reporting lag in the IMF PCPS dataset itself (confirmed via
the `--verify` dump, not assumed), not a parsing bug in this pipeline. Worth
rechecking periodically — if PCPS's update cadence improves, the live gold
price (and therefore the reserves figure) should track more current market
prices.

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
- **IMF PCPS's `PGOLD.USD` gold-price series lags ~13 months** (last observed
  2025-06 as of the 2026-07-19 run, see §3's reserves subsection) — a genuine
  upstream reporting lag, not a bug in this pipeline, but worth knowing if
  the reserves-incl-gold figure looks stale relative to a real-time gold
  price quote.
- **This session's fixes live on `claude/new-session-ldotj8`, not yet merged
  to `main`** (see §4) — the live site does not yet reflect the
  23%/3.7% debt-service and reserves figures. Merging is the next step.

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
7. **Watch whether IMF PCPS's gold price catches up** to a more current
   month than the ~13-month lag seen in the 2026-07-19 run (§3, §7) — if it
   stays this stale, the reserves-incl-gold figure will always trail actual
   market gold prices by over a year.

---

## 9. Calibration against Dalio's Ch.17 US column

This session's work started from a direct comparison of this pipeline's live
output against the actual published numbers in the US column of *How
Countries Go Broke* Ch.17 (March 2025 snapshot). **This comparison is the
strongest correctness check this project has** — it caught a real ~4pt
definitional gap in debt service and a structural ~2pt gap in reserves that
neither the sanity bands nor the local mock tests would ever have surfaced,
because both the wrong numbers looked "sane" in isolation. The next person
touching this pipeline should re-run this comparison whenever the fetcher
changes, not just trust that the sanity bands are enough.

| Metric | Dalio Ch.17 (US, Mar 2025) | This pipeline (2026-07-19 live run) | Match? |
|---|---|---|---|
| Debt held by public / GDP | ~100% | 99% (`FYGFGDQ188S`) | Matches closely, no change needed |
| Debt service / revenue | 22% | 23.0% (gross interest incl. GAS ÷ total receipts) | **Required a definitional change** — see §3. Previously shipped 18% on a different (net-to-public) basis |
| Reserves / GDP | 3% | 3.7% (FX reserves excl. gold + gold at market value) | **Required a new data source** — see §3. Previously shipped 0.8% because gold wasn't included at all |
| Reserve-currency USD share (world CB reserves) | ~58% (book's framing) | 57.7% (IMF COFER via DBnomics) | Matches closely, already live before this session |

**Two rows needed a definitional decision, not just a bug fix:**
- **Debt service**: the book's 22% could only be reproduced by switching
  which numerator (gross vs. net-to-public vs. function-900) and denominator
  (tax receipts vs. total receipts) this pipeline used — a 3×2 matrix made
  the six candidate combinations explicit (printed every `--verify` run,
  `scripts/treasury.py::debt_service_matrix`), and gross-interest-over-total-
  receipts was the only one that landed near 22% *and* matched a named
  official statistic (GAO's gross interest figure ÷ CBO's receipts figure).
- **Reserves**: no amount of debugging FRED's `TRESEGUSM052N` alone could
  have closed this gap — the series is *defined* to exclude gold. Matching
  Dalio's figure required adding an entirely new data source (Treasury gold
  holdings × a live gold price) that didn't exist in the pipeline before this
  session.

**Two rows already matched** (debt/GDP, COFER USD share) and needed no
change — worth noting so a future reader doesn't assume everything on the
page was wrong before this session; only the two flagged assumptions were.

---

## 10. Review package for a file-only reviewer (2026-07-19)

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
| The 1pt gap to Dalio is caused by the March-2025-vs-rolling-TTM timing difference | **ASSUMED** — plausible, not independently confirmed |
| `TRESEGUSM052N` = "Total Reserves excluding Gold" | **VERIFIED** — quoted from live FRED metadata |
| Gold holdings = 2026-06-30, ~261.5M troy oz (sum of 8 Treasury rows) | **VERIFIED** — quoted from live Treasury API response |
| Gold price = $3,351.86/oz, dated PCPS 2025-06 | **VERIFIED** — quoted from live DBnomics/PCPS response |
| Gold market value = $876.5B | **VERIFIED** — printed by the run itself, not recomputed here |
| Reserves incl. gold = 3.7% of GDP, `tag: "live"` | **VERIFIED** — read from committed `public/data.json` |
| The 0.7pt gap to Dalio's 3% is caused by the same timing issue as debt service | **NOT CLAIMED** — see §10.4; the price/quantity time-mismatch is a distinct, larger, and unquantified factor |
| These fixes are live on `main` / on the deployed site | **FALSE, explicitly** — see §4/§8; verified only on `claude/new-session-ldotj8` via direct `workflow_dispatch` |

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
