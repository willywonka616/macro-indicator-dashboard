# STATUS

Living document. **Update this at the end of every session** — that's the
instruction this file was created under, and it stands going forward. Written
for another AI assistant (or human) picking this up cold, with no memory of
prior sessions and no access to this repo's chat history.

> **Current review-round files:**
> `docs/review/2026-07-20b-verification.md` (follow-up diagnostics: dated
> matrix re-run, IMF-direct gold query — run output; no companion
> `-values.md`, nothing in `public/data.json` changed this round), base
> commit `8c5d3bb`. For headline values, `docs/review/2026-07-20a-values.md`
> is still current (base commit `9bace30`). Each review pass gets its own
> new file under `docs/review/` instead of rewriting
> `docs/verification-log.md` / `docs/current-values.md` in place — a
> reviewer's fetch tool caches by URL and can't see edits to an
> already-fetched path, so an old path that keeps getting rewritten is
> invisible on a repeat check. Those two old paths hold short tombstone
> stubs pointing here; do not resurrect the regenerate-in-place pattern.
> Prior rounds: `docs/review/2026-07-19c-*.md`, `docs/review/2026-07-19d-*.md`,
> `docs/review/2026-07-20a-*.md` (superseded, left in place). When you add
> a new round, update this line to point at it.

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

**Later the same day, a third pass (§12):** ran a diagnostic — not a
feature, ships nothing on its own — recomputing the debt-service matrix as
a **monthly** series at Dalio's stated March-2025 vintage, extended with a
4th denominator (CBO's Jan-2025 baseline projected receipts). Finding:
**gross interest ÷ total receipts** (not the shipped net-to-public /
on-budget basis) is the construction that best reproduces *both* of
Dalio's independent anchors — the 22% interest figure (22.3% at his
vintage, drifting to 23.0% today, genuine measured drift on this cell) and
his own previously-unused ~580% debt-to-revenue figure (542%, closest of
four denominators tested, vs. on-budget's 714%). This is a
basis-*identification* finding, not a basis change — §12 records it as a
recommendation for the next task, and revises §10.2's retraction (real
drift does exist, just not where the first retraction looked).

**Later the same day, a fourth pass (§13, ships): the "total receipts"
§12 (and every round before it) computed had been GROSS receipts, not
net of refunds** — a ~7% overstatement, checked against CBO's published
FY2024 ($4.920T) and FY2025 ($5.235T) totals (net matches both almost
exactly; gross misses both by ~7%). Fixed in `treasury.py`. Two
consequences: (1) no realised-data basis reproduces Dalio's 22% closely
any more (closest: gross/total at 23.9%, ~2pt off — within the book's own
Ch.3-vs-Ch.17 20%/22% spread); (2) **debt/revenue on the corrected TOTAL,
net-of-refunds basis lands at 580% for 2025-Q1 — essentially exact
against Dalio's own stated ~580%**, the strongest independent
confirmation this project has found for what his denominator actually
is. Shipped: `debt_service_ratio()`, `gross_debt_service_ratio()`, and
`revenue_ttm_dollars()` now all divide by TOTAL receipts, net of refunds
(dropping the on-budget basis §3/§11 adopted, whose closeness to 22% is
now understood to have been an artifact of the gross-receipts bug). Also
found and stated plainly: §10.2's "the pipeline's 23.0% matches GAO/CBO's
23.0%" was coincidence, not corroboration — the pipeline's actual figure
at the time used the inflated gross denominator. See §13 for the full
writeup, including the corrected 3×4 matrix and why on-budget was
dropped for total on definitional (not just numerical) grounds.

**2026-07-20, a fifth pass (§14): closed out the remaining open items.**
Re-ran the drift matrix on the corrected basis and confirmed §13's "no
realised basis near 22%" conclusion holds (verification exercise, no
basis change). Found IMF's own SDMX 3.0 API is reachable from CI, no key
— new for this project — and its PCPS dataflow metadata is suggestive
(not conclusive) that gold-price staleness is upstream at IMF, not just
DBnomics' mirror; couldn't pull the actual PGOLD series data directly
after eight key-format attempts, so shipped a visible staleness indicator
on the reserves row instead (exact month count, not the earlier "~13
months" estimate — it's 12). Tested and eliminated a second "other debt"
hypothesis (TCMDO minus government debt, 263.9% vs. Dalio's 340%, worse
than TCMDO alone). Resolved the long-open `IEABC` annualization question
from evidence already sitting in committed files. Fixed `gold.py`'s stale
verify banner. Added row-level net/gross framing captions (new
`MetricRow` `note` field) alongside the panel-level explanation. See §14
for the full writeup and `docs/review/2026-07-20a-*.md` for the run that
shipped it (commit `9bace30`).

**Later the same day, a sixth pass (§15): closed the two loose ends a
reviewer flagged in round a's own writeup.** Fixed `treasury.py`'s matrix
header, which claimed cells were dated to Mar-2025 when they were actually
latest-TTM — then re-ran the matrix as two explicit, separately-dated
grids (Mar-2025 and today) and confirmed, via an independent
re-derivation, that §13's "no realised basis near 22%" conclusion
holds exactly (no basis change). Actually queried IMF PCPS directly for
`PGOLD` — went past round a's dataflow-level-metadata inference to try the
real series: confirmed `PGOLD` is the exact right code, confirmed the
query's dimension order matches the DSD's own declaration, and still got
zero retrievable observations even after wildcarding every uncertain
dimension. Neither of the task's two conditional outcomes ("fresher,
switch" / "same, closes the question") could be evaluated, since no
per-series date was retrievable at all — recorded as an honest open
dead-end, not forced into a false resolution. No gold source switched. See
§15 for the full writeup and `docs/review/2026-07-20b-verification.md`
for the run output (no data change this pass, so no new `-values.md`;
`2026-07-20a-values.md` remains current).

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

> **Superseded again — see §13.** Rounds 1 and 2 below (kept for the
> record) are followed by a Round 3 (§12, diagnostic) and Round 4 (§13,
> the current state): the on-budget-receipts denominator both rounds below
> settled on turned out to rest on a field-selection bug (summing GROSS
> receipts, not net of refunds) — fixed in §13, which also drops on-budget
> for TOTAL receipts. **For the current shipped basis, read §13, not the
> "Round 2" text below.**

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
run — see `docs/review/2026-07-19c-values.md`), instead of a generic
string that reads as fully current. The tag stays `"live"` rather than being downgraded,
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
| Debt service / revenue | 22% (Ch.17 table); **~20% (Ch.3 prose, "the US is also borrowing ~20% of its income each year to cover interest expenses")** | 19.6% (net-to-public / **total** receipts, net of refunds) | live, `scripts/treasury.py` | **Matches the Ch.3 figure** (−0.4pt) — **does not match Ch.17's 22%** (−2.4pt). The book gives two figures for this ratio, ~2pt apart, in the same March-2025 vintage; exact reproduction of both is impossible. This pipeline reproduces the one computed on the standard (net-to-public / total, net-of-refunds) definition — see §14.1 for the recomputed matrix confirming no realised basis reproduces 22% |
| FX reserves / GDP | 3% | 3.7% (excl.-gold FX + gold at market) | live, `scripts/gold.py` + FRED | Close but not exact — residual ~0.7pt, attributed partly to the gold-price staleness (§3/§7) |
| Total debt (Dalio's "other debt") / GDP | 340% | 362.6% (TCMDO, all sectors incl. financial) | live, `FRED: TCMDO` | **Does not match** — +22.6pt gap. Two alternative readings tried and **both eliminated**: nonfinancial-sectors-only (TCMDODNS, 256.7%, −83pt) and non-government debt (TCMDO minus government's own ~99%, 263.9%, −76pt) — both further from 340% than TCMDO itself. See §14.4 |
| Current account, 3-yr avg / GDP | −4% | −3.7% | live, `IEABC` (FRED) | Matches closely |
| World trade in USD | 52.6% | 52.6% | **manual**, carried from `data/manual.json` | Trivial — same figure |
| World debt in USD | 80.7% | 80.7% | **manual**, carried from `data/manual.json` | Trivial — same figure |
| Global equity market cap in USD | 65.7% | 65.7% | **manual**, carried from `data/manual.json` | Trivial — same figure |
| World CB reserves in USD | 57.0% | 57.7% | live, IMF COFER via DBnomics | Matches closely — independently computed, not carried |
| Debt / revenue | ~580% (Mar 2025, stated) | 576% (2026-Q1, shipped); **580% at 2025-Q1 (Mar-2025, his own vintage)** | live, derived (§3, §12, §13) | **Matches almost exactly at his vintage** — see §13: switching to TOTAL receipts, net of refunds (the corrected, shipped basis) puts debt/revenue at $28.93T / $4.99T TTM = 580% for 2025-Q1, essentially identical to his stated figure. Strongest confirmation yet that TOTAL, net-of-refunds receipts is his denominator |
| Debt / revenue, 10-yr projection | ~700% (his stated forward projection) | *(not yet checkable)* | *n/a* | **Forward anchor, recorded not verified** — this pipeline has no 10-year debt/revenue projection to compare (only Dalio's own manual `cboProjection` figure exists, and that's for debt/GDP, not debt/revenue). Noted here so the anchor isn't lost, not claimed as checked |

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
  made all nine candidates explicit. §12's drift test identified gross ÷
  total receipts as the closest reconstruction of Dalio's 22% — but §13
  found the "total receipts" both §3 and §12 used had been GROSS receipts
  (before refunds, a ~7% overstatement), not net. Corrected, no realised
  basis reproduces 22% closely (closest: gross/total, 23.9% @ Mar-2025).
  **The shipped basis is now net-to-public / TOTAL receipts (net of
  refunds)** — chosen on definitional grounds (the numerator/denominator
  scope-consistency argument from Round 2, unaffected by the receipts
  bug, plus TOTAL being the standard published denominator once
  closeness-to-22% stopped being a live consideration). See §13.
- **Reserves**: no amount of debugging FRED's `TRESEGUSM052N` alone could
  close this gap — the series structurally excludes gold. Required a new
  data source (Treasury gold holdings × a live gold price).
- **Total debt**: investigated but **not resolved**. TCMDO (all sectors) at
  362.6% is the closest of three tried readings, still 22.6pts over Dalio's
  340%. Two alternative hypotheses tested and **both eliminated**:
  nonfinancial-sectors-only (TCMDODNS, refuted this session — 256.7%,
  further from target) and non-government debt, i.e. TCMDO minus the
  government's own ~99% (tested §14.4 — 263.9%, also further from target,
  not closer). What Dalio's "other debt" row actually scopes remains
  unknown; a household+corporate-debt-specifically aggregation (summed
  from separate FRED series rather than derived by subtraction) is a
  candidate for a future session but wasn't attempted here. **Reported as
  an open gap with two hypotheses now eliminated, not forced to
  reconcile.**

**Two rows already matched before this session** (debt/GDP, COFER USD
share) and needed no change. **Debt/revenue now has a book anchor and
matches it almost exactly** (§12 found Dalio's own stated ~580%/~700%
figures; §13's corrected TOTAL-receipts basis puts debt/revenue at 580%
for 2025-Q1, his own vintage — see §13).

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
>
> **⚠️ ADDENDUM, same day, §12's drift test.** The paragraph above says the
> gap is "not this" (timing) and reaches for a revenue-base/interest-scope
> guess instead. §12 replaces that guess with a direct monthly
> recomputation and finds the picture is more specific than either the
> original claim or its retraction: **on the gross ÷ total-receipts cell
> specifically** (not net ÷ on-budget, the basis this pipeline actually
> ships), there **is** real measured drift — 22.3% at Mar-2025 rising to
> 23.0% today — which is consistent with, not contradicted by, the GAO/CBO
> FY2024 figure two paragraphs up: FY2024 ended September 2024, sits
> earlier on the same climbing trajectory, and both this run and that
> static figure land in the same 22–23% band, not on opposite sides of it.
> The original retraction's *narrow* claim — "there is no drift in the
> data this project has looked at" — undersold it: the drift is real, on
> a cell nobody had directly measured monthly at the time. Left as-is
> above per the "retract explicitly, don't edit" convention; see §12 for
> the full measurement and what it changes.

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

This round's numbers supersede §10's (§10 itself is kept, marked
historical, not deleted); §12 (a diagnostic, not a further numbers
revision) supersedes neither — read this section and §12 together for the
current state. Base commit: `3ed5858` (branch `claude/new-session-ldotj8`).
Same file-only-reviewer constraints as §10 (no Actions tab, no directory
browsing, no `git log`). **Support-file location changed after this round
was first written:** the content quoted below was originally in
`docs/verification-log.md` / `docs/current-values.md`, regenerated in
place; those paths are now short tombstone stubs, and the actual content
lives at `docs/review/2026-07-19c-verification.md` /
`docs/review/2026-07-19c-values.md` (see the note at the top of this
file) — nothing about the numbers changed, only where the supporting file
lives.

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

## 12. Drift test — matrix recomputed at Dalio's stated vintage (2026-07-19, third pass)

Per `TASKdrifttest.md`: run *before* selecting the debt-service basis, as a
diagnostic — nothing ships from it except what's recorded here. Three facts
read directly out of the book made this decisive: the vintage is stated
("as of this writing in March 2025"), not guessed; Dalio publishes his own
debt-to-revenue figure (~580%, ~700% in ten years) as a second, independent
calibration anchor; and footnote 20 says he uses CBO projections as a
baseline where possible. `scripts/drift_test.py` (temporary — removed this
pass, see below) recomputed the 3×3 matrix as a **monthly** series,
2023-01→present, reusing `treasury.py`/`series.py`'s numerator and
denominator definitions **unchanged**, extended with a 4th denominator:
CBO's January 2025 baseline projected total receipts, by fiscal year. Full
run output: `docs/review/2026-07-19c-verification.md`, "Drift test"
section.

### 12.1 CBO figures used, and why direct CBO access wasn't possible

Direct network access to `www.cbo.gov`, `api.fiscaldata.treasury.gov`, and
`api.stlouisfed.org` from this session's dev sandbox is blocked at the org
egress-policy level — confirmed via `/root/.ccr/README.md`'s own
diagnostic endpoint, which logged `gateway answered 403 to CONNECT (policy
denial)` for all three hosts. Per that same doc, policy denials are
reported, not retried or routed around. (Treasury/FRED access still works
*inside* GitHub Actions, which is how every other live figure in this
project is fetched — only this session's own sandbox is blocked; CBO's own
site is blocked everywhere the same way, including from Actions, so there
was no path to it this session.)

CBO's January 2025 baseline figures below are therefore sourced from
secondary web reporting (WebSearch), cross-checked for internal arithmetic
consistency where possible, per the task's own built-in caveat that
"these figures were derived from secondary summaries, not CBO's own
tables":

- **FY2025: $5,163B — VERIFIED (secondary, cross-checked).** Two
  independent search results state "$5.235T actual, $72B (1%) above the
  $5.163T baseline projection" — 5.235 − 0.072 = 5.163 exactly, internally
  consistent, and matches the task brief's own stated ~$5.163T.
- **FY2026: $5,524B — ASSUMED.** Derived from "revenues increase by $361B
  (7%) in 2026" (361/5163 = 6.99%, consistent with "7%"), not independently
  confirmed against a primary table.
- **FY2023/FY2024: no separate CBO figure used.** For already-closed
  fiscal years, the Jan-2025 baseline just carries the realised Treasury
  actual — so `drift_test.py` falls back to the same `monthly_receipts()`
  actuals used for the "total receipts" column for those months. This
  fallback is itself a finding: the CBO-projected column is only
  *informative* (different from realised total receipts) from FY2025
  (Oct 2024) on.
- **Discarded:** a WebSearch synthesis that produced a full FY2023–2030
  table (2023: $4,441B, 2024: $5,082B, 2025: $5,485B, …) — rejected
  because it contradicts the two cross-checked figures above (FY2025
  should be $5,163B not $5,485B; FY2024 actual is well-documented near
  $4.92T, not $5,082B) and reads as a search-model fabrication rather than
  a quoted table. Not used anywhere in this section.

### 12.2 The matrix at his vintage — Mar-2025 vs. today

3 numerators × 4 denominators, TTM ratio, read at Mar-2025 and at the
latest available month (full min/max/slope/crossings in
`docs/review/2026-07-19c-verification.md`):

| Numerator | Denominator | Mar-2025 | Today | Crosses 22% in 2024-01→2025-06? |
|---|---|---|---|---|
| gross (incl. GAS) | on-budget | 29.4% | 29.7% (2026-06) | No — closest 26.1% |
| gross (incl. GAS) | **total receipts** | **22.3%** | **23.0%** (2026-06) | **Yes — 2024-12, 2025-04** |
| gross (incl. GAS) | **CBO Jan-2025 projected** | **21.8%** | 24.9% (2026-06) | Yes — 2025-04 |
| gross (incl. GAS) | tax only | 37.6% | 35.0% (2026-03) | No — closest 33.4% |
| net-to-public | on-budget (shipped) | 23.4% | 23.1% (2026-06) | Yes — 2024-07 |
| net-to-public | total receipts | 17.8% | 17.9% (2026-06) | No — closest 17.8% |
| net-to-public | CBO Jan-2025 projected | 17.4% | 19.4% (2026-06) | No — closest 18.9% |
| net-to-public | tax only | 29.9% | 27.8% (2026-03) | No — closest 25.8% |
| net interest, fn900 | on-budget | 23.2% | 23.0% (2026-06) | Yes — 2024-08 |
| net interest, fn900 | total receipts | 17.6% | 17.8% (2026-06) | No — closest 17.6% |
| net interest, fn900 | CBO Jan-2025 projected | 17.2% | 19.3% (2026-06) | No — closest 18.8% |
| net interest, fn900 | tax only | 29.7% | 27.8% (2026-03) | No — closest 25.5% |

**Claim status: VERIFIED** — every cell above is copied from the live run
in `docs/review/2026-07-19c-verification.md`.

**Regime, per the task's slope guardrail:** the whole-window (2023-01→now)
slope on every cell is steep (+2.2 to +3.6 pt/yr — the 2022–2023 rate-hike
cycle driving interest costs up fast), but the gross/total-receipts and
gross/CBO-projected cells specifically move much more slowly near the
22–23% mark itself (22.3%→23.0% over ~15 months, a *local* rate closer to
+0.6 pt/yr) — closer to a noisy plateau in the 22–23% band than to a clean
trend still climbing through it. A 22% crossing in a flat regime is
stronger evidence than the same crossing in a still-steep one; this one is
in the flatter regime, which is why it's treated as a real finding below,
not noise.

### 12.3 debt_to_revenue against Dalio's ~580% / ~700% anchor

Debt held by the public, 2025-Q1 (Mar-2025): **$28.93T** — matches the
task's own stated ~$28.9T estimate almost exactly. **Claim status:
VERIFIED** (computed live from `FYGFGDQ188S` × `GDP`, both FRED).

| Denominator | TTM $ at 2025-Q1 | Debt/revenue at 2025-Q1 | vs. Dalio's ~580% |
|---|---|---|---|
| on-budget receipts (shipped) | $4.05T | 714% | +134pt |
| **total receipts** | **$5.34T** | **542%** | **−38pt (closest)** |
| CBO Jan-2025 projected receipts | $5.46T | 530% | −50pt |
| tax receipts only | $3.17T | 912% | +332pt |

This independently confirms the task's own hypothesis in `TASKdrifttest.md`
§2/§3 that 580% identifies his denominator as **total receipts**, not
on-budget (our on-budget figure, 714%, is close to the task's own rough
~780% on-budget estimate — both clearly too high) and not tax-only (way
too high). **Claim status: VERIFIED** for the ranking (total/CBO-projected
closest, on-budget/tax-only clearly ruled out); the exact ~38–50pt residual
to 580% itself is not explained — possibly his $28.9T or his receipts
figure being a rounder snapshot than this pipeline's precise TTM
computation, not investigated further this pass.

One coincidence flagged, not trusted: at 2026-Q1 ("today"), CBO-projected
receipts happens to give 589% — *closer* to 580% than it was at Mar-2025
(530%). This is very likely noise, not signal: it's the FY2026 projection
(a year-plus past its own forecast horizon) drifting against realised
GDP/debt growth, exactly the "denominator moves independently of the real
fiscal position" failure mode `TASKdrifttest.md` warned a CBO-projected
denominator would have. It is not used as evidence for anything here.

### 12.4 Two hypotheses tested, both hold up

**"gross ÷ CBO-projected receipts ≈ 22% at his vintage"** (the task's
"trailing numerator, projected denominator" hypothesis, footnote 20):
FY2024 gross interest (actual, summed from live data) = **$1,133.0B**
(task's estimate: ~$1,126.5B) over CBO's Jan-2025 FY2025-projected receipts
$5,163B = **21.9%** (task's estimate: ~21.8%) — both this FY-total
construction and the monthly-TTM-ending-Mar-2025 construction (21.8%,
§12.2) land in the same place. **Claim status: VERIFIED**, matching the
task's own hypothesis closely.

**"gross ÷ total receipts ≈ 22% at Mar-2025, ≈23% today"** (the task's
outcome table's "drift confirmed" row): 22.3% → 23.0%, matching that
row's stated pattern almost exactly. **Claim status: VERIFIED.**

**Both hypotheses hold simultaneously** because CBO's Jan-2025 FY2025
projection ($5,163B) and realised trailing receipts around that period
were close to each other — the two denominators hadn't yet diverged much
at his own vintage. **A single consistent basis — gross interest ÷ total
receipts, realised — reproduces both of Dalio's independent anchors**: the
22% interest figure (22.3% at Mar-2025) *and* the 580% debt/revenue figure
(542%, the closest of four denominators tested) with the same denominator.
Neither net-to-public nor on-budget reproduces either anchor as well (net
never gets close to 22% on any receipts-only denominator except on-budget,
and on-budget overshoots 580% by 134pt). Per the task's outcome-reading
table, this most closely matches: *"gross÷total ≈ 22% at Mar-2025, ≈23%
today → Drift confirmed for that cell."*

**What this does and doesn't decide.** Per `TASKdrifttest.md`: "Identifying
how Dalio built his number is not a reason to build ours the same way."
That caveat is specifically about a *forecast-based* denominator moving
independently of the real fiscal position (§12.3's "today" coincidence is
a live example of exactly that risk) — it does **not** apply to gross ÷
**total receipts**, which is fully realised data, refreshes monthly like
every other row, and has no forecast-staleness problem. So the caveat that
would block adopting the identified basis doesn't apply here. That said,
**this task is diagnostic only and ships nothing** (per its own header) —
whether to actually change `debt_service_to_revenue`'s shipped basis from
net-to-public/on-budget to gross/total-receipts is a decision for the next
task, informed by this finding, not decided by it. Recorded here as a
clear recommendation, not implemented in `treasury.py`/`fetch.py` this
pass.

### 12.5 Known partial results, checked against real data

| Task's stated estimate | This run's computed value |
|---|---|
| Net interest / total receipts, Mar-2025 ≈ 18.9% | **17.8%** |
| Net interest / total receipts, today ≈ 17.9% | **17.9%** (exact match) |
| FY2024 gross interest ≈ $1,126.5B | **$1,133.0B** (0.6% off) |
| CBO FY2025-projected receipts ≈ $5.163T | **$5.163T** (as sourced, §12.1) |
| Debt held by public, Mar-2025 ≈ $28.9T | **$28.93T** (essentially exact) |

The Mar-2025 net/total figure (17.8% vs. the task's rough ~18.9% estimate)
is the one visible miss — a 1.1pt gap, plausibly because the task's own
estimate was built from "secondary summaries, not CBO's own tables" (its
own stated caveat). Not investigated further; flagged rather than silently
accepted, per the task's own instruction to "suspect the series before the
estimate — but investigate."

### 12.6 Two conflicting book figures for interest-to-income — recorded as a limit on the calibration target itself

Ch. 3 states the US borrows ~20% of its income each year to cover interest;
Ch. 17's table states 22%. Same vintage (~March 2025), ~2 points apart in
the book itself. Per the task: the 20% figure reads as a forward-looking
decade average, a different quantity from the table's current-reading 22%
— **not a second target to tune to**, but a ceiling on how precisely any
pipeline can be expected to reproduce "the" Dalio figure, since the book
does not present a single unambiguous number even internally. Recorded
here as a known limitation of the calibration target, not of this
pipeline. **Claim status: VERIFIED** (both figures are directly read from
the task brief's quotation of the book; this project has not independently
obtained the book text).

### 12.7 Limitations acknowledged, not resolved

- **Data revisions**: FRED and Treasury restate history, so today's value
  *for* March 2025 is not necessarily what was visible *in* March 2025.
  Not eliminated. A vintage-aware cross-check (FRED's ALFRED archive) was
  considered but not attempted this pass — the task says not to block on
  it, and this pass was already large in scope; flagged as a next step.
- **The ~38–50pt residual on debt/revenue** (§12.3) between the
  closest-matching denominator (total receipts, 542%) and Dalio's stated
  580% is unexplained. Reported, not forced to reconcile.
- **`scripts/drift_test.py` and `.github/workflows/drift-test.yml` are
  removed** immediately after this pass (commit follows this one) — per
  the task's framing ("a diagnostic, not a feature… nothing ships from it
  except findings"), the reusable artifact is this file and
  `docs/review/2026-07-19c-verification.md`, not a permanent script.
- **Review-file convention changed after this pass was first written:**
  `docs/verification-log.md` / `docs/current-values.md` (rewritten in
  place, referenced throughout this section as written) have since moved
  to per-round files under `docs/review/` — see the note at the top of
  this file. Nothing in §12's findings changed; only the support-file
  paths did.

### 12.8 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| The full 3×4 monthly matrix values | **VERIFIED** — read from a real run log |
| CBO Jan-2025 FY2025 baseline = $5,163B | **VERIFIED (secondary, cross-checked)** — two independent sources, internally consistent arithmetic |
| CBO Jan-2025 FY2026 baseline = $5,524B | **ASSUMED** — derived from a percentage-change statement, not a primary table |
| Debt held by public, Mar-2025 ≈ $28.9T | **VERIFIED** — computed live, matches the task's estimate |
| gross ÷ total receipts ≈ 22% (Mar-2025) → ≈23% (today) | **VERIFIED** — read from the live run |
| gross ÷ total receipts also reproduces the 580% debt/revenue anchor most closely | **VERIFIED** — read from the live run, ranked against the other three denominators |
| A single consistent basis (gross/total) reproduces both of Dalio's anchors | **VERIFIED**, within the residuals stated above (not exact) |
| The §10.2 timing-drift retraction was too broad — real drift exists on the gross/total cell | **VERIFIED** — direct monthly recomputation, not inference |
| The next task should adopt gross/total-receipts as the shipped basis | **RECOMMENDATION, not a verified fact** — a decision this task explicitly defers, offered with the evidence above |
| Direct CBO/FRED/Treasury access is blocked from this session's sandbox (not from Actions) | **VERIFIED** — quoted from the proxy's own diagnostic endpoint |

**⚠️ ADDENDUM, same day, §13.** This entire §12 analysis — including the
matrix in §12.2, the "total receipts" TTM$ figures in §12.3, and the
"gross ÷ total ≈ 22%" identification above — used `monthly_receipts()`,
which §13 found had been summing GROSS receipts (before refunds) the
whole time, a ~7% overstatement. The *debt/revenue* finding held up
anyway (§13 finds an even closer match, 580% almost exact, on the
corrected basis) — but the *interest-ratio* identification did not:
corrected, gross/total lands at 23.9% at Mar-2025, not 22.3%, a
materially worse match. Left as-is above per the retract-explicitly
convention; see §13 for the corrected numbers and what they change.

---

## 13. Receipts denominator fix: gross → net, on-budget → total (2026-07-19, fourth pass)

Per `TASKreceiptsdenominator.md`: a reviewer working from §12/`docs/review/
2026-07-19c-verification.md` alone (i.e. from committed files, not this
session's live transcript) spotted that the drift test's own $5.34T
"total receipts" figure at 2025-Q1 didn't match three independent
estimates of Dalio's actual denominator (~$4.99T from his 580% figure,
CBO's $4.92T FY2024 total already cited in §10.2, and an independent
Treasury/JEC estimate) — and correctly traced the ~7% gap to
`mts_table_4`'s **gross** vs **net-of-refunds** receipts fields, not a
new numerator question. **This basis change ships** — unlike §12, this
pass is not diagnostic-only.

### 13.1 The bug, confirmed against CBO's published FY totals

`mts_table_4`'s "Total -- Receipts" row (2026-06 shown, but the same
three fields exist every month):
```
classification_desc: 'Total -- Receipts'
gross=563,801,628,771.00  refund=68,040,147,202.30  net=495,761,481,568.70
gross - refund = 495,761,481,568.70 = net  (exact, confirms the arithmetic)
```
`monthly_receipts()` (and `off_budget_receipts_monthly()`) had summed
`current_month_gross_rcpt_amt` since this function was first written —
every prior round's "total receipts"/"on-budget receipts" figure used it.

| FY | CBO published | Pipeline, GROSS (old) | Pipeline, NET (fixed) |
|---|---|---|---|
| FY2024 | $4.920T | $5.265T (**+7.0%**) | $4.919T (**-0.03%**) |
| FY2025 | $5.235T | $5.617T (**+7.3%**) | $5.235T (**-0.01%**) |

**Claim status: VERIFIED** — both rows read from a live `workflow_dispatch`
run (`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29703925309`,
job `88237568913`), CBO's FY2024/FY2025 totals as cited in `TASKreceiptsdenominator.md`
(FY2024 already independently cited in §10.2; FY2025 cross-checked via
WebSearch against two independent statements — "$5.235T actual, $72B/1%
above the $5.163T Jan-2025 baseline" and "+$317B/6% over FY2024's $4.92T"
— both arithmetically consistent with $5.235T). Net matches both to
within rounding; gross misses both by essentially the same ~7%. Fixed:
`monthly_receipts()` and `off_budget_receipts_monthly()` now sum
`current_month_net_rcpt_amt` (see `scripts/treasury.py`).

### 13.2 The on-budget-vs-total question, re-examined

With the field bug fixed, `TASKreceiptsdenominator.md` §1's own predicted
consequence held almost exactly: gross ÷ total (now correctly net) at
Mar-2025 came in at **23.9%** (task's estimate: "roughly 23.9%") and
net-to-public ÷ total at **19.0%** (task's estimate: "roughly 19.0%") —
both confirmed live, not just predicted. Full corrected 3×4 matrix
(monthly TTM, Mar-2025 vs. today; verbatim run in
`docs/review/2026-07-19d-verification.md`):

| Numerator | Denominator | Mar-2025 | Today (2026-06) |
|---|---|---|---|
| gross (incl. GAS) | **total (net, shipped)** | 23.9% | 25.1% |
| gross (incl. GAS) | on-budget (net) | 32.2% | 33.3% |
| gross (incl. GAS) | tax only | 37.6% | 35.0% |
| gross (incl. GAS) | CBO Jan-2025 projected | 22.5% | 24.9% |
| net-to-public | **total (net, shipped)** | 19.0% | 19.6% |
| net-to-public | on-budget (net) | 25.6% | 25.9% |
| net-to-public | tax only | 29.9% | 27.8% |
| net-to-public | CBO Jan-2025 projected | 17.9% | 19.4% |
| net interest, fn900 | **total (net, shipped)** | 18.9% | 19.5% |
| net interest, fn900 | on-budget (net) | 25.4% | 25.8% |
| net interest, fn900 | tax only | 29.7% | 27.8% |
| net interest, fn900 | CBO Jan-2025 projected | 17.7% | 19.3% |

**No realised-data cell is close to 22%** — the closest, gross/total at
23.9%, is ~2pt off, which is inside the book's own internal spread (Ch.3
says 20%, Ch.17 says 22% — a 2pt gap in the source itself). Per
`TASKreceiptsdenominator.md`'s own outcome table, this is closest to *"No
cell near 22% at his vintage, on any denominator → Definitional gap
confirmed. Choose on definitional grounds, document the residual"* — with
one caveat: **gross ÷ CBO-projected receipts is closer still (22.5%)**,
mildly reviving the footnote-20 "trailing numerator, projected
denominator" hypothesis for *his* construction specifically. That doesn't
change what ships (`TASKreceiptsdenominator.md`'s prior-round guidance
still applies: identifying his construction isn't a reason to build ours
on a forecast-dependent denominator that moves independently of the real
fiscal position).

### 13.3 debt_to_revenue: the strongest confirmation this project has found

This is the finding `TASKreceiptsdenominator.md` didn't predict. Debt held
by the public, 2025-Q1 (Mar-2025): **$28.93T** (matches the task's ~$28.9T
estimate). Against each of the four denominators' TTM$ at that same
quarter:

| Denominator | TTM$ at 2025-Q1 | debt/revenue | vs. Dalio's ~580% |
|---|---|---|---|
| **total, net of refunds (shipped)** | **$4.99T** | **580%** | **~0pt — essentially exact** |
| CBO Jan-2025 projected | $5.31T | 545% | -35pt |
| on-budget, net | $3.71T | 780% | +200pt |
| tax receipts only | $3.17T | 912% | +332pt |

**Claim status: VERIFIED** — computed live in the same run as §13.2's
matrix (`docs/review/2026-07-19d-verification.md`). $4.99T is, to the
cent this pipeline can measure it, the same figure the task derived by
hand from Dalio's own 580% ("$28.9T / 580% ≈ $4.99T"). This is the
single strongest piece of evidence in this project for what Dalio's
denominator actually is: TOTAL receipts, net of refunds — not on-budget,
not tax-only, and (at his own March-2025 vintage) not meaningfully
different from the CBO-projected variant either, though the realised
figure is the closer of the two and has no forecast-staleness risk.

### 13.4 Basis shipped

`debt_service_ratio()`, `gross_debt_service_ratio()`, and
`revenue_ttm_dollars()` now all divide by `monthly_receipts()` — TOTAL
receipts, net of refunds — instead of `on_budget_receipts_monthly()`.
`on_budget_receipts_monthly()` is kept for the diagnostic matrix only.
Confirmed live in the production run that follows this fix
(`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29704235465`,
commit `76362af`):

- `debt_service_to_revenue` (headline): **19.6%** (display "20%"), was 23.1%
  (display "23%") under the on-budget basis.
- Gross interest, second row: **25.1%** (display "25%"), was 29.7% (display "30%").
- `Debt vs revenue` (renamed from "Debt vs on-budget revenue"): **576%**
  (2026-Q1), was 692%.

All within the existing sanity bands (10-40%, 15-50%, 200-1200%) with
comfortable headroom — no band changes needed. One shared
`provenance.revenueDefinition` (TOTAL, net of refunds) now covers both
debt-service rows and `debt_to_revenue`, per acceptance criterion 4.
Local mock test (`scripts/requirements.txt`-installed, no network) updated
and re-run: `ALL CHECKS PASSED`.

### 13.5 The §10.2 GAO/CBO "corroboration" — coincidence, not corroboration

`TASKreceiptsdenominator.md` §1 asked this to be checked explicitly.
§10.2's independent cross-check computed GAO's FY2024 gross interest
($1,126.5B) over **CBO's own published FY2024 total ($4.9T, i.e. net of
refunds)** = 23.0%, and noted this matched the pipeline's own live ratio
at the time, also ~23.0%. But the pipeline's live ratio at that time was
gross interest over the pipeline's **gross**-receipts denominator — a
different, inflated quantity that happened to round to the same headline
percentage as the correct external calculation. Recomputing what the
pipeline's TTM-ending-then figure actually was on a like-for-like FY2024
basis (gross interest $1,133.0B / gross receipts $5.265T = 21.5%) does
**not** match 23.0% — the apparent agreement was between two different
quantities that both rounded near 23%, not a genuine independent
corroboration of the pipeline's method. **Say-so, per the task's
instruction: yes, this was coincidence, not corroboration.** The GAO/CBO
figures themselves (external, correctly using CBO's net-of-refunds total)
remain valid — only the "the pipeline agrees with them" claim is
retracted.

### 13.6 Denominator choice: on-budget dropped, total adopted, on definitional grounds

`TASKreceiptsdenominator.md` §2 asked this to be re-examined once §1
resolved, and to be explicit that on-budget's original selling point
(closeness to 22%) might be shown to be an artifact. It was: on-budget's
23.1% (old, gross-receipts basis) vs. Dalio's 22% was a ~1pt "match" built
on a ~7%-inflated denominator that happened to still land close by
chance of scale. Once receipts are corrected, on-budget is no longer
close to anything (25.6-25.9% net-to-public, 32.2-33.3% gross — both
further from 22% than the total-receipts variants). With
closeness-to-target no longer a live consideration, TOTAL receipts is
adopted on the grounds that matter: it's the denominator every standard
published interest-to-revenue figure (CBO, OMB, GAO) actually uses,
where on-budget/off-budget is a budget-*process* artifact (2 U.S.C.
622(7) governs statutory budget-enforcement totals, not which cash is
economically available to pay interest — Treasury commingles on- and
off-budget receipts in the same general account). §13.3's debt/revenue
match is independent confirmation this was the right call, arrived at
without targeting that figure.

### 13.7 §3 rising-burden note (task §3)

Noted, not acted on further this pass: the shipped headline (net /
total) reads 19.0% at Mar-2025 and 19.6% today — rising, not falling
(the opposite of what the equivalent on-budget-basis figures showed,
23.4% → 23.1%). Dalio's framing is of a rising burden, so the corrected
basis is *more* consistent with that framing than the one it replaced,
not less — worth a line in the commentary if/when the equation-button
task (still out of scope here) revisits panel copy.

### 13.8 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| `monthly_receipts()` had been summing gross, not net, receipts | **VERIFIED** — read live from `mts_table_4`'s three fields, arithmetic checks (gross − refund = net) |
| Net matches CBO's FY2024/FY2025 published totals; gross overshoots both by ~7% | **VERIFIED** — live run vs. cited CBO figures |
| No realised-data cell reproduces 22% closely post-fix | **VERIFIED** — full corrected matrix, live |
| gross ÷ CBO-projected (22.5%) is the closest surviving cell to 22% | **VERIFIED**, but not adopted — forecast-dependent denominator, see §13.2 |
| debt/revenue on the corrected total-receipts basis ≈ Dalio's 580% at his vintage | **VERIFIED** — 580% computed live vs. his stated ~580% |
| The §10.2 GAO/CBO "agreement" was coincidental, not corroborating | **VERIFIED** — recomputed the like-for-like FY2024 figure, doesn't match |
| TOTAL (net) receipts is now the shipped denominator for all three revenue-denominated rows | **VERIFIED** — read from committed `public/data.json` at commit `76362af` |
| This basis is closer to Dalio's rising-burden framing than the one it replaced | **VERIFIED** (directionally: 19.0%→19.6% rises; the old on-budget 23.4%→23.1% fell) |

---

## 14. Closing out the remaining open issues (2026-07-20, fifth pass)

Per `TASKremainingissues.md`: the receipts fix (§13) is accepted as correct.
This pass works through everything still open, in the task's priority order.
Ran via three temporary diagnostic scripts (`remaining_issues_check.py`,
`gold_imf_direct_check.py` ×2 iterations), all since removed — full run
output in `docs/review/2026-07-20a-verification.md`.

### 14.1 The 22% question, shown not asserted

Re-ran the 3×4 drift matrix on the corrected net-of-refunds basis,
confirming §13's numbers were not a one-off:

```
gross (incl. GAS):
  total (net, shipped)     Mar-2025: 23.9%   today (2026-06): 25.1%
  on-budget (net)          Mar-2025: 32.2%   today (2026-06): 33.3%
  tax receipts only        Mar-2025: 37.6%   today (2026-03): 35.0%
  CBO Jan-2025 projected   Mar-2025: 22.5%   today (2026-06): 24.9%
net-to-public (excl. GAS):
  total (net, shipped)     Mar-2025: 19.0%   today (2026-06): 19.6%
  on-budget (net)          Mar-2025: 25.6%   today (2026-06): 25.9%
  tax receipts only        Mar-2025: 29.9%   today (2026-03): 27.8%
  CBO Jan-2025 projected   Mar-2025: 17.9%   today (2026-06): 19.4%
```

**Claim status: VERIFIED** — live run, matches §13's numbers exactly (same
underlying data, re-derived independently). The task's own arithmetic
concern (gross reads 25.1% today; at ~2.3pt/yr drift that "implies
something near 22% around March 2025") is answered directly: gross/total
at Mar-2025 is 23.9%, not ~22% — the naive linear-extrapolation estimate
overshoots because the series isn't drifting at a constant rate through
this whole window (see §12.2's regime note: steep 2023 climb, flatter
since). **§13's conclusion stands, on this evidence: no realised basis
reproduces 22% closely.** The shipped basis is unchanged (net-to-public /
total, net of refunds) — this was a verification exercise, not grounds to
switch, per the task's explicit instruction not to change the basis on
this evidence.

### 14.2 Ch.3's ~20% — recorded in §9

Done directly in the §9 table (Debt service / revenue row): the pipeline
(19.6%) matches Ch.3's ~20% (−0.4pt) and does not match Ch.17's 22%
(−2.4pt); both book figures are recorded rather than picking one. The
~700% ten-year debt/revenue projection is recorded as a forward anchor,
explicitly not yet checkable (this pipeline has no 10-year debt/revenue
projection to compare it against).

### 14.3 Gold staleness: real progress, not a full resolution

**What's new this pass:** found and confirmed live that IMF's own SDMX 3.0
API (`https://api.imf.org/external/sdmx/3.0`) is reachable, no key, from
CI (previous sessions couldn't confirm this — `dataservices.imf.org`, the
older API host, doesn't resolve at all; `api.imf.org` does and returns
200s). Querying its PCPS dataflow structure directly returned:
```
"annotations":[...,{"id":"lastUpdatedAt","value":"2025-06-16T17:59:44.643694Z"}]
```
**This is suggestive evidence that IMF's PCPS dataflow itself, not just
DBnomics' mirror, was last refreshed around June 2025** — matching
DBnomics' own last observation (2025-06) almost exactly. That would mean
the earlier session's inference ("DBnomics' mirror is more likely stale
than IMF's own PCPS," based only on IMF's documented monthly cadence, not
a direct check) had it backwards. **Claim status: ASSUMED, not
VERIFIED** — this is dataflow-level metadata (when the *dataflow's
structure* was last touched), not confirmed to be the PGOLD *series'*
own latest-observation date specifically.

**What didn't work:** getting the actual PGOLD observations directly from
IMF's API to check that per-series date with certainty. Eight key
combinations were tried across three query attempts (DBnomics' own
`M.W00.PGOLD.USD` ordering; IMF's declared dimension order
`W00.PGOLD.USD.M`, `W00.PGOLD..M`, `W00.PGOLD.IX.M`, `W00.PGOLD.USD.A`) —
all returned HTTP 200 but an empty `dataSets` (no matching series), meaning
the indicator/transformation dimension member codes guessed for gold
weren't right. Resolving this fully would need IMF's own codelist for the
PCPS dataflow's `INDICATOR`/`DATA_TRANSFORMATION` dimensions (a further
API call this session didn't reach) — flagged as the concrete next step,
not re-guessed further.

**No fresher alternative source found or switched to.** The World Bank
Pink Sheet (monthly, no key, updated through the current month per its own
publication schedule) is a real candidate, but its distribution is a
monthly Excel/CSV file rather than a queryable API, needs a new parsing
dependency, and CI-reachability from `worldbank.org`/`thedocs.worldbank.org`
was never confirmed live (this session's tools got 403s researching it,
which — per this project's own established pattern — doesn't distinguish
a genuine block from a bot-facing 403 without an actual CI test). Recorded
as a candidate for a future session, not implemented.

**Fallback implemented, per the task's own instruction:** `reserves_incl_gold_row`
now carries a visible `note` whenever the gold price and gold-quantity
months differ by 2+ months — e.g. `"⚠ gold priced as of 2025-06 (12
months old) — market value may be off if gold has moved since"` — computed
from the actual source dates, not a hardcoded "~13 months" estimate (the
real figure is 12 months as of this pass's data). This renders on the row
itself (new `MetricRow` `note` prop, §14.6), not only inferable from
`src`/`asOf`. **Claim status: VERIFIED** — code change, confirmed by the
local mock test and (pending) a live production run.

### 14.4 Total debt: second hypothesis tested and eliminated

TCMDO and government debt read at the same live quarter (2026-Q1):
```
TCMDO (total debt, all sectors) / GDP: 362.6%
FYGFGDQ188S (govt debt held by public) / GDP: 98.7%
Non-government-debt proxy (TCMDO - govt): 263.9%
Dalio's Ch.17 'other debt' target: 340%
Residual vs. 340%: -76.1pt (TCMDO itself: +22.6pt)
```
**Claim status: VERIFIED** — live run. The non-government-debt reading
(TCMDO minus the government's own debt, to avoid double-counting against
the debt/GDP row above it in Dalio's table) moves in the **wrong**
direction and by more than TCMDONS did — 76pt short of 340% versus
TCMDO's 22.6pt over. **Both tested alternatives (TCMDODNS,
non-government-debt) are now eliminated; TCMDO itself remains the closest
of the three.** §9's table and the "three rows needed more" bullet list
both updated to record this rather than leave the gap unattended. A
household+corporate-debt-specifically aggregation (summed from separate
FRED series, not derived by subtraction) is named as the remaining
untested candidate, not attempted this pass.

### 14.5 Loose ends closed

- **`IEABC` annualization branch**: resolved from evidence **already
  committed**, no new run needed. `docs/review/2026-07-19d-verification.md`'s
  own FRED table shows `IEABC ... Millions of Dollars ... Balance on
  current account` (does not contain "annual rate"), and the committed
  `public/data.json`'s `provenance.currentAccountAnnualizedInput` reads
  `false` — confirming the non-annualized, trailing-4-quarter-sum branch
  of `current_account_pct_gdp_3yr` is the one that actually fires live.
  **Claim status: VERIFIED** — both pieces of evidence read directly from
  already-committed files, cross-checked against each other.
- **`gold.py`'s stale `--verify` banner**: fixed — was "DBnomics LBMA
  price" (stale label from before the 2026-07 IMF PCPS switch), now
  "DBnomics-mirrored IMF PCPS price". Cosmetic, but the banner is exactly
  what a reviewer reads first. **Claim status: VERIFIED** — code change.

### 14.6 Commentary refresh

The panel-note prose in `commentary.js` (net = current situation vs. gross
= leading indicator; debt/GDP vs. debt/revenue) makes no numeric claims,
so it needed no changes for the 20%/25%/576% move — checked, not assumed.
The one vital-level numeric claim ("about a fifth of total revenue") was
already corrected in §13 and is accurate at 19.6%. New this pass: a
`note` field on `MetricRow` (`src/components/MetricRow.jsx`), a short
caption under the row label, distinct from `Panel.jsx`'s `longNote` (the
fuller explanation several screens down) — so the net/gross framing is
visible on the rows themselves, per the task's explicit ask, not only in
the panel note above them. "Net interest (to the public)" now carries
*"The current situation — cash leaving the government today"*; "Gross
interest" carries *"The leading indicator — the gap is obligation
accruing before it's an outflow"*. Same mechanism used for the gold
staleness note (§14.3). **Claim status: VERIFIED** — code change,
confirmed via the local mock test, and by an actual Playwright screenshot
against a real `npm run build` + `vite preview`, once the production run
that follows (commit `9bace30`) put real `note` values into
`public/data.json`: both the net/gross captions and the gold-staleness
warning render exactly as written, in the right place, correctly styled.
Not just asserted — screenshots taken, read back, and matched against the
intended text before this was called done.

### 14.7 Merge / PR, and watching the cron

Per the task: once the above was settled, get this branch off of
feature-branch-only and stop the live site serving pre-fix figures. Opted
for a **pull request rather than a direct merge** — this branch touches
the shipped debt-service basis (a real, user-visible number change) and
merging to `main` triggers the Pages deploy workflow immediately; a PR is
the same practical outcome (reviewable, mergeable when ready) without
taking that action unilaterally. Opened:
**https://github.com/willywonka616/macro-indicator-dashboard/pull/1**
(`claude/new-session-ldotj8` → `main`, 46 commits). Test plan in the PR
description covers the local mock test, live Actions runs, the production
build, and the manual browser verification (§14.6) — all done. **Not**
done: merging it — left for explicit approval, per this project's
standing instruction not to merge without it.

**Watching the cron**: `update-data.yml`'s schedule (`0 6 5 * *`, the 5th
of each month) hasn't fired unattended even once in this project's
history — every run so far has been a manual `workflow_dispatch`. The
next scheduled firing is 2026-08-05, over two weeks from this pass.
**Not observed this session** — flagged here as the one remaining
unproven piece of the pipeline, per the task, rather than silently
assumed to work because the manual-dispatch path does. Left as an open
item rather than fabricating a monitoring setup nobody asked for.

### 14.8 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| Recomputed matrix confirms §13's conclusion (no realised basis near 22%) | **VERIFIED** — live run, independent re-derivation |
| The naive linear-drift extrapolation to "~22% at Mar-2025" doesn't hold | **VERIFIED** — actual Mar-2025 value is 23.9%, not ~22% |
| `api.imf.org` SDMX 3.0 is reachable, no key, from CI | **VERIFIED** — live 200 responses |
| PCPS dataflow's own `lastUpdatedAt` (2025-06-16) suggests upstream staleness, not just a DBnomics-mirror problem | **ASSUMED** — dataflow-level metadata, not a confirmed per-series observation date |
| No fresher no-key gold source was found and confirmed CI-reachable | **VERIFIED** (as a negative — World Bank Pink Sheet identified but not confirmed reachable or implemented) |
| Gold staleness is now visible on the row itself, not only in `src`/`asOf` | **VERIFIED** — code change, mock-tested |
| Non-government-debt hypothesis for "other debt" (263.9%) is eliminated | **VERIFIED** — live run |
| `IEABC` uses the non-annualized branch | **VERIFIED** — read from two independent already-committed files |
| `gold.py`'s verify banner now names IMF PCPS, not DBnomics LBMA | **VERIFIED** — code change |
| Commentary prose needed no numeric changes; row-level framing added | **VERIFIED** — code change, mock-tested, and confirmed by real-browser screenshot |
| The row-level `note` and gold-staleness warning render correctly in a real build | **VERIFIED** — Playwright screenshot against `npm run build` + `vite preview` with the live post-fix `public/data.json` |
| Pull request #1 opened, `claude/new-session-ldotj8` → `main`, 46 commits | **VERIFIED** — `https://github.com/willywonka616/macro-indicator-dashboard/pull/1` |
| The unattended monthly cron (5th of the month) has fired successfully at least once | **NOT VERIFIED, not yet true** — every run to date has been a manual `workflow_dispatch`; next scheduled firing is 2026-08-05 |

---

## 15. Follow-up on §14: dated matrix re-run and direct IMF gold query (2026-07-20, sixth pass)

A reviewer working from round a's own files (§14.1, §14.3) flagged two
loose ends and asked for both to be closed with live evidence rather than
re-assertion: (1) `treasury.py`'s `verify()` matrix header said "Mar 2025"
above cells that were actually latest-TTM values — fix it, then re-run and
paste a genuinely-dated Mar-2025 grid next to a today grid; (2) §14.3 cited
only PCPS *dataflow-level* metadata as suggestive of upstream gold
staleness — actually query IMF PCPS directly for the `PGOLD` series' own
latest observation. Full run output: `docs/review/2026-07-20b-verification.md`.

### 15.1 Dated matrix: §13 CONFIRMED, not revised

Fixed the header (commit `95dd7c1`) and re-ran the matrix via a new,
temporary script (`dated_matrix_check.py`, reusing round c's
`ttm_series_full()`/CBO-projection logic) that prints two explicitly
separate grids instead of one ambiguously-headed grid:

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

**Claim status: VERIFIED** — every cell matches §13.2/§14.1's
previously-reported numbers exactly, via an independent re-derivation
(separate script, freshly-fetched live data). **§13's conclusion is
CONFIRMED on this evidence, not revised: no realised-data basis reproduces
Dalio's 22% at his Mar-2025 vintage** — closest is gross/total at 23.9%
(~1.9pt off, itself inside the book's own internal 20%-vs-22% spread). No
basis change. The header bug is fixed in shipped code (`95dd7c1`); the
diagnostic script itself was deleted after this round per the
diagnostic-not-a-feature convention (§14's own precedent) — its output is
preserved verbatim in `docs/review/2026-07-20b-verification.md`.

### 15.2 IMF-direct gold query: reachable, correct code, still zero data — the question stays open

Went past round a's dataflow-metadata inference and queried IMF PCPS
directly for `PGOLD` observations, across three escalating attempts (full
detail and exact queries in `docs/review/2026-07-20b-verification.md`):

1. Broad keyword search across all 31 codelists for "gold" — found the
   right codelist *names* (`CL_PCPS_INDICATOR`, `CL_PCPS_COMMODITY`) but
   queried data with keyword-matched guesses instead of confirmed codes
   first. Every guess: `200 obs=0`.
2. Fetched `CL_PCPS_COMMODITY` directly and confirmed `PGOLD` → `"Gold"`
   is the exact right code (matches DBnomics' own code). Queried it
   directly: still `200 obs=0`.
3. Wildcarded the two remaining uncertain dimensions (`COUNTRY`,
   `DATA_TRANSFORMATION`) to test whether *any* monthly PGOLD data is
   reachable at all, independent of guessing exact codes. All three
   wildcard variants returned `200`, confirmed the series-dimension order
   matches the DSD's own declaration exactly, and still returned **zero
   series** — even with both uncertain dimensions fully open.

**Disposition against the task's own two-way conditional** ("if fresher,
switch source; if the same, the staleness is upstream and that closes the
question"): **neither outcome applies.** No PGOLD observation was
retrievable at all via `api.imf.org`'s SDMX 3.0 REST API for the
`IMF.RES/PCPS` dataflow, as tested — not "same date" and not "fresher,"
because no date could be read at all. Wrong-code and wrong-dimension-order
are now both ruled out with direct evidence (the confirmed-correct
`PGOLD` code, and the wildcard test's confirmed dimension order); the
actual blocker is something this round's testing didn't isolate —
candidates not yet tested: the `~` "latest version" resolving to a
dataflow/DSD version pairing that doesn't actually carry PGOLD
observations, a required content-negotiation header this session's plain
`Accept: application/json`/default didn't send, an access restriction on
observation data that isn't visible in the (public) structure/metadata
endpoints, or the data being served under a different agency/dataflow
than `IMF.RES/PCPS`.

**No gold source switch performed** — there is nothing to switch to: this
round didn't get IMF PCPS to return any data at all, direct or otherwise,
so it cannot be shown fresher than DBnomics' 2025-06, and DBnomics' mirror
remains the only working source. Round a's §14.3 metadata-level inference
(`lastUpdatedAt: 2025-06-16`, suggestive of upstream staleness) is
neither strengthened nor refuted by this round — it stands as **ASSUMED**,
exactly as before, since this round could not reach the series level
either way. The shipped gold-staleness `note` (§14.3/§14.6) already covers
the user-facing risk regardless of which side the staleness sits on.

**Claim status: VERIFIED (as a negative result)** — three independent,
methodical attempts, each ruling out a specific hypothesis (wrong
codelist searched, wrong code, wrong dimension order/uncertain dimensions)
without ever finding a positive cause. Recorded as an open dead-end rather
than forced into a false resolution.

### 15.3 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| `treasury.py`'s matrix header no longer claims cells are dated to Mar-2025 when they're latest-TTM | **VERIFIED** — code change (`95dd7c1`) |
| Dated Mar-2025 grid, re-derived independently, matches §13.2/§14.1 exactly | **VERIFIED** — live run, separate script, fresh data fetch |
| §13's "no realised basis near 22%" conclusion | **CONFIRMED, not revised** — same live evidence as above |
| `PGOLD` is the exact correct IMF PCPS indicator code for gold | **VERIFIED** — read directly from `CL_PCPS_COMMODITY` v1.0.0 |
| The series-dimension order used in queries (`COUNTRY.INDICATOR.DATA_TRANSFORMATION.FREQUENCY`) is correct | **VERIFIED** — matches the DSD's own declared order, confirmed via wildcard query response |
| IMF PCPS returns zero retrievable `PGOLD` observations via `api.imf.org`, as tested | **VERIFIED (negative result)** — 200 responses, zero series, across guessed codes, confirmed-correct code, and full wildcarding of remaining uncertain dimensions |
| Root cause of the zero-series response | **NOT IDENTIFIED** — open dead-end, candidates listed in §15.2, not pursued further |
| Whether IMF PCPS itself is fresher than, or exactly as stale as, DBnomics' mirror | **STILL OPEN** — neither of the task's two conditional outcomes could be evaluated; no per-series date was retrievable at all |
| No gold source switched | **VERIFIED** — nothing found to switch to |

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
