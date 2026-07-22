# STATUS

Living document. **Update this at the end of every session** — that's the
instruction this file was created under, and it stands going forward. Written
for another AI assistant (or human) picking this up cold, with no memory of
prior sessions and no access to this repo's chat history.

> **Current review-round files:**
> `docs/review/2026-07-22c-verification.md` (run output) and
> `docs/review/2026-07-22c-values.md` (headline values), base commit
> `46c168a` — a same-day follow-up on §23's bottleneck finding: per the
> user's explicit direction, added "Gold holdings, at current price" as a
> new row (key `gold_value_current`) — live gold oz × live gold price
> only, no GDP or `TRESEGUSM052N` denominator, so it updates every time
> the gold price does instead of waiting on those series' own release
> cadence. Confirmed GDP itself (not just `TRESEGUSM052N`) is the actual
> binding constraint on the existing headline row's 2026-Q1 lag. Confirmed
> live in production: the new row ships `asOf: "2026-06"` right next to
> the existing row's `asOf: "2026-Q1"` — the vintage gap is now visible on
> the page itself. See §24.
> Each review pass gets its own new file under `docs/review/` instead of
> rewriting `docs/verification-log.md` / `docs/current-values.md` in
> place — a reviewer's fetch tool caches by URL and can't see edits to an
> already-fetched path, so an old path that keeps getting rewritten is
> invisible on a repeat check. Those two old paths hold short tombstone
> stubs pointing here; do not resurrect the regenerate-in-place pattern.
> Prior rounds: `docs/review/2026-07-19c-*.md`, `docs/review/2026-07-19d-*.md`,
> `docs/review/2026-07-20a-*.md`, `docs/review/2026-07-20b-*.md`,
> `docs/review/2026-07-20c-*.md`, `docs/review/2026-07-20d-*.md`,
> `docs/review/2026-07-21a-*.md`, `docs/review/2026-07-21b-*.md`,
> `docs/review/2026-07-21c-*.md`, `docs/review/2026-07-21d-*.md`,
> `docs/review/2026-07-22a-*.md`, `docs/review/2026-07-22b-*.md`
> (superseded, left in place). When you add
> a new round, update this line
> to point at it.

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

**Later the same day, a seventh pass (§16): quantified the gold-staleness
error instead of leaving it as an unquantified "old" flag.** Tried two
keyless alternatives to the stale shipped gold price — World Bank Pink
Sheet via DBnomics (real dataset found, but annual with a 2030 *projected*
value as its "latest" point, not the monthly Pink Sheet) and Stooq's
XAUUSD CSV (blocked by a client-side JS proof-of-work anti-bot challenge,
confirmed live in the response body) — both ruled out for specific,
evidenced reasons, neither a dead-end guess. Since neither worked,
computed the actual size of the error live against real FRED/Treasury
data: the shipped row reads **3.7% of GDP**, a current-market $4,000/oz
estimate gives **4.2%** — a **+0.5 point gap** ($169.5B at the same gold
holdings), independently reproducing the task's own estimate almost
exactly. Kept the staleness note as-is; deliberately did not fold the
magnitude into the shipped (live-tagged) note text itself, to avoid
mixing a manually-sourced price estimate into a row the UI presents as
live — documented here instead. See §16 for the full writeup and
`docs/review/2026-07-20c-verification.md` for the run output (no shipped
code or data changed this pass).

**Later the same day, an eighth pass (§17): tried five named gold sources
(FRED, World Bank, Bundesbank, Nasdaq Data Link, Stooq) in order — all
five fail, for five different, evidenced reasons — then added the more
valuable half of the task: a freshness guard that checks every fetched
series' DATE, not just its magnitude.** First live run immediately caught
a *second* frozen source nobody had found: IMF COFER has been stuck at
2025-Q1 for 565 days, meaning `World CB reserves in USD` — previously
logged in §9 as "live, matches closely, independently computed" — had
also been silently stale the whole time. Calibrated the thresholds against
real observed lag (FRED's quarterly series are dated to period-*start*,
so ~200 days old is normal, not stale; fixed two false positives without
weakening the real catches). Ran the actual `update-data.yml` end to end:
both frozen sources (gold price, COFER) now correctly fall back to
`manual` instead of shipping as falsely `live` — `reserves_to_gdp` is now
3.0% (manual, was 3.7% live) and `World CB reserves in USD` is 57.0%
(manual, was 57.7% live), committed as `a93e485`. Also fixed a real,
unrelated gap: `manual.json`'s fallback `note` field existed but was
never actually surfaced on the row — it is now. §9's table updated to
mark both rows `manual` with an explanation. See §17 for the full writeup
and `docs/review/2026-07-20d-*.md` for the run output and headline
values.

**2026-07-21, a ninth pass (§18): the user correctly flagged that §17's
fix had swapped one problem for a worse one — replacing a stale-but-live
number with a fully manual output that, for gold, was literally Dalio's
own book figure, and, for COFER, was transcribed from the same book §9
calibrates against. Fixed both as manual PRICE/VALUE INPUTS rather than
manual OUTPUTS:** gold reserves now apply a hand-entered price (~$4,000/oz,
dated) to the still-live Treasury ounce count (new `manual_price` tag);
COFER's fallback is now the latest actually-published IMF figure
(57.13%, 2026-Q1) instead of the book value. The first implementation of
the gold fix had a real bug — a single-point manual price dict didn't
overlap `TRESEGUSM052N`'s own lagging history, so it silently fell all
the way back to the old manual output in a live production run — found
via that run's own log output and fixed same-round (patch only the
missing months, keep any real historical price data the fetch did
return). Confirmed working in a second live production run:
`reserves_to_gdp` is now **4.1%** of GDP (`manual_price`, live ounce
count × manual price), `World CB reserves in USD` is **57.1%** (`manual`,
real 2026-Q1 COFER). §9's table is updated to explicitly label the
circularity in the old fix and why the new figures are non-circular (or,
for gold, deliberately don't try to match the book at all). Also retried
three gold sources not yet properly attempted per the user's correction
— the actual World Bank Pink Sheet (distinct from the CMO forecast table
already ruled out), ECB Data Portal, and IMF IFS (distinct from PCPS) —
all three ruled out for specific, evidenced reasons; no source switched.
See §18 for the full writeup and `docs/review/2026-07-21a-*.md` for the
run output and headline values.

**Later the same day, a tenth pass (§19): closed two more silently-wrong-
data gaps.** §17's freshness guard only ever checked FETCHED series —
`data/manual.json`'s own hand-entered values (the gold price added in
§18) had no threshold at all, and could go stale with nothing to catch
it. Added thresholds for every dated manual value (`goldPriceManualFallback.asOf`,
`reserveCurrency.cbReserves.asOf`, and the catch-all `lastChecked`),
checked both when actually used as a fallback and unconditionally during
`--verify`; none are stale as of this pass, but the audit found **11 of
14 manual.json values have no date of their own at all** (TIC holder
shares, the CBO projection, and the three reserve-currency market-share
figures — recorded, not fixed, since fixing it means sourcing 11 new
independently-tracked dates). Separately, added a per-row provenance
assertion (`assert_provenance`) at both fallback-capable rows (gold
reserves, COFER) — this is the structural fix for how §18.2's bug was
actually found: by reading a build log line-by-line, not by any
automated check. A fallback firing is now a loud, unmissable signal
(console banner + GitHub Actions `::warning::` annotation) AND a
structured field in the shipped data (`country.provenance.fallbacksFired`),
not just a `print()` line easy to miss. Both new mechanisms are
deliberately non-fatal — these are already the fallback of last resort,
so failing the build over their own staleness or over a fallback firing
would defeat the entire "degrade rather than break" point of the
fallback chains §17/§18 built in the first place. Confirmed working in a
live production run (`3335451`): both known fallbacks (gold, COFER)
correctly produced loud warnings and `fallbacksFired` entries; headline
values unchanged from §18. See §19 for the full writeup and
`docs/review/2026-07-21b-*.md` for the run output and headline values.

**Later the same day, an eleventh pass (§20): the equation button —
`TASK-equation-button.md`.** A small "ƒx" disclosure on every metric row
now reveals the formula behind it in Ray Dalio's own variable names
(*How Countries Go Broke* Ch. 3), keeping current-value definitions
visibly separate from his forward-looking projection formulas so the
maths view can never be read as though a projection formula produced the
number on screen. `scripts/fetch.py` now attaches a stable `key` to every
panel row and a `terms` array (each with its own src/asOf/tag) to the
five rows whose Dalio equation names multiple distinct inputs the
pipeline currently exposes as one combined row. `src/content/equations.js`
holds only the hand-written formulas/prose — per the task's addendum, the
mapping table's src/asOf/tag are read from `data.json` at render time,
never hardcoded, so the tag vocabulary changing (as it just did with
`manual_price`) needs no content update. Browser-tested live with
Playwright (`chromium-cli` unavailable in this environment; used the
`playwright` package already in `node_modules`) — found and fixed a real
390px horizontal-overflow bug before shipping (a flex row couldn't wrap
a long src string; fixed by stacking label/src instead of fitting them
side by side), confirmed zero overflow across all 24 buttons on the page
afterward, confirmed correct `aria-expanded`/keyboard behaviour
programmatically, and confirmed the feature against real production data
including a genuine mixed-tag case (three live terms, one `manual_price`
term, in the same reserves-incl-gold mapping table). Bundle impact:
+3.39kB gzip, no new runtime dependency. See §20 for the full writeup and
`docs/review/2026-07-21c-verification.md` for the run output (headline
values unchanged from round b, so no new `-values.md` this round).

**Later the same day, a twelfth pass (§21): CBO projections —
`TASKprojections.md`, run deliberately after the equation-button pass
since the projection rows are what its "Dalio's formula" blocks
describe.** Three live rows in the Government debt panel, all from CBO's
own published 10-year baseline, no home-grown forecasting anywhere:
"Debt, 10-yr projection" replaces the hand-carried, undated 122% in
`manual.json` (one of the 11 dateless values §19.2 found) with a live
figure (120%, February-2026 CBO vintage); "Debt vs revenue" (existing
live row) gains a dashed projected tail on its chart, its own headline
value staying the live current figure; a new "Interest rate to keep debt
flat (Dalio eq. #3)" row computes his equation #3 entirely from CBO's
baseline fields and states the gap against the ACTUAL average effective
rate (Treasury, live) directly on the row. The task assumed cbo.gov's
downloadable xlsx files; following its own "verify rather than assume"
instruction found a better source instead — CBO's own official
machine-readable GitHub data mirror (`US-CBO/cbo-data`) — verified
against three independently-known facts (122% at the June-2024 vintage,
118% at January-2025, ~101%/~120% at the current February-2026 vintage)
before trusting it. `Chart.jsx` now renders any history array containing
`projected: true` points as a dashed, shaded, labelled forward
extension, distinct from the solid historical line; a new `projection`
tag (dashed border) matches. Confirmed working end to end against real
production data, including a genuine current comparison (CBO's required
rate 4.2% vs. Treasury's actual 3.41%, a −0.8pt gap). §9's calibration
table gained both of Dalio's forward-looking book targets, computed at
his own vintage rather than the current one (122.4% vs. his stated 122%,
essentially exact; 679.3% vs. his stated ~700%, close but not exact — the
more interesting test, since he derives that ratio rather than
transcribing it). See §21 for the full writeup and
`docs/review/2026-07-21d-*.md` for the run output and headline values.

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
| Debt, 10-yr projection / GDP | 122% | **120%** (2026-07-21, current CBO vintage: Feb 2026, FY2036) | **projection**, live from CBO's own GitHub data mirror (§21) | **No longer trivial — see §21.** Was `manual`, hand-carried from `data/manual.json`, and happened to equal his figure exactly because it was transcribed from his own book with no date at all (one of the 11 undated manual values §19.2 found). §21 replaces it with a live fetch of CBO's *current* vintage — expected to differ from his book value, since CBO republishes ~twice a year and his book cites a specific (June 2024) vintage. **Recomputed at his own vintage instead (June 2024, FY2034): 122.4%** — reproduces his stated 122% almost exactly, confirming June 2024 as his source, per TASKprojections.md §5's calibration target |
| Debt, 10-yr projection / revenue | ~700% (his stated forward projection) | **679.3%** at his own vintage (June 2024, FY2034: $50,664.2B ÷ $7,458.7B) | **derived**, from CBO's own baseline dollar levels (debt held by public ÷ total revenue) at the June-2024 vintage | **Real check, not exact — see §21.** −21pt off his stated ~700%, the more interesting of the two 10-yr targets since he *derives* this ratio rather than transcribing it (TASKprojections.md §5). Close enough to support June 2024 as his source vintage (same conclusion as the row above), not close enough to claim exact reproduction. Was "not yet checkable" prior to §21 (no CBO integration existed) |
| Held by CB / domestic / abroad | 13% / 57% / 29% | 13% / 57% / 29% | **manual**, carried from `data/manual.json` (TIC) | Trivial — same figures, not independently derived |
| Debt service / revenue | 22% (Ch.17 table); **~20% (Ch.3 prose, "the US is also borrowing ~20% of its income each year to cover interest expenses")** | 19.6% (net-to-public / **total** receipts, net of refunds) | live, `scripts/treasury.py` | **Matches the Ch.3 figure** (−0.4pt) — **does not match Ch.17's 22%** (−2.4pt). The book gives two figures for this ratio, ~2pt apart, in the same March-2025 vintage; exact reproduction of both is impossible. This pipeline reproduces the one computed on the standard (net-to-public / total, net-of-refunds) definition — see §14.1 for the recomputed matrix confirming no realised basis reproduces 22% |
| FX reserves / GDP | 3% | **5.1%** (excl.-gold FX, live + gold at market, live oz × live price) | **live** (2026-07-22, §22/§23 — no manual price input) | **Fully automated — see §22 (source) and §23 (a real bottleneck found the same day).** §18's manual PRICE INPUT is retired; the gold price now comes from LBMA's daily fix (primary) or the World Bank Pink Sheet (fallback), both live. **But the headline value is bottlenecked to `TRESEGUSM052N`/GDP's own latest common quarter (2026-Q1, per `asOf`) regardless of which gold-price leg is active** — §23 found the fresher LBMA price does NOT make this row more current; it changed 4.9%→5.1% only because LBMA's and the World Bank's respective *March-2026* values genuinely differ, not because June/July gold pricing entered the calculation. Further from Dalio's 3% than §18's manual-price figure — expected, gold having risen past his March-2025 vintage; the widening tracks real gold-price differences, not a bug |
| Total debt (Dalio's "other debt") / GDP | 340% | 362.6% (TCMDO, all sectors incl. financial) | live, `FRED: TCMDO` | **Does not match** — +22.6pt gap. Two alternative readings tried and **both eliminated**: nonfinancial-sectors-only (TCMDODNS, 256.7%, −83pt) and non-government debt (TCMDO minus government's own ~99%, 263.9%, −76pt) — both further from 340% than TCMDO itself. See §14.4 |
| Current account, 3-yr avg / GDP | −4% | −3.7% | live, `IEABC` (FRED) | Matches closely |
| World trade in USD | 52.6% | 52.6% | **manual**, carried from `data/manual.json` | Trivial — same figure |
| World debt in USD | 80.7% | 80.7% | **manual**, carried from `data/manual.json` | Trivial — same figure |
| Global equity market cap in USD | 65.7% | 65.7% | **manual**, carried from `data/manual.json` | Trivial — same figure |
| World CB reserves in USD | 57.0% | 57.1% (2026-Q1, latest actually-published IMF figure) | **manual** as of 2026-07-20 | **Also retracted-then-fixed, §18.** §17's fix fell back to the manual figure already sitting in `data/manual.json` — which had been transcribed from this same book (57.0%, ~2024) — so it "matched" Dalio's own number by construction, not independent corroboration, same flaw as the reserves row above. §18 replaces it with the **latest actually-published IMF COFER figure** (57.13%, 2026-Q1, researched via web search against IMF's own data brief and cross-checked against two independent secondary sources), deliberately NOT the book's number. It happens to land close to his 57.0% anyway — a **genuine, non-circular near-match**, unlike the row above |
| Debt / revenue | ~580% (Mar 2025, stated) | 576% (2026-Q1, shipped); **580% at 2025-Q1 (Mar-2025, his own vintage)** | live, derived (§3, §12, §13) | **Matches almost exactly at his vintage** — see §13: switching to TOTAL receipts, net of refunds (the corrected, shipped basis) puts debt/revenue at $28.93T / $4.99T TTM = 580% for 2025-Q1, essentially identical to his stated figure. Strongest confirmation yet that TOTAL, net-of-refunds receipts is his denominator |

**Read the "Basis" column before trusting a "match."** As of this pass
(§17, 2026-07-20), **eight** of the twelve rows are `manual` — hand-carried
from `data/manual.json`, which in most cases was originally *transcribed
from this same book*. Those matching is not a validation of anything; it
would be surprising if they didn't match. Two of those eight (reserves,
COFER share) were `live` as recently as §16 — they moved to `manual` this
pass not because anything about them was rolled back, but because a new
freshness guard (§17) correctly caught both sources frozen for well over a
year and refused to keep shipping them as "live." The rows still worth
trusting as genuine checks are the three remaining `live` ones — debt/GDP,
debt service, and current account — of which one lands close (debt/GDP),
one is close on one of the book's own two stated figures but not the other
(debt service — see the row above), and current account matches closely
too.

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
  data source (Treasury gold holdings × a live gold price). **Update,
  2026-07-20 (§17):** that live gold price has been frozen at 2025-06 for
  over a year — a fact the pipeline had no way to know until this pass
  added a freshness guard, since a stale-but-plausible number passes every
  other check silently. The row now ships `manual` (3.0%, exactly Dalio's
  figure by construction) rather than a live number built on dead data.
  **When a working live gold-price source is eventually found**, expect
  this row to move to a different value than 3.0% or the old 3.7% — gold
  has run from ~$3,352/oz (the frozen price) through a ~$5,595 Jan-2026
  peak to ~$4,000/oz today (§16), so a genuinely current price will price
  US gold holdings well above either figure, widening the gap from Dalio's
  3% rather than closing it. **That would be correct behaviour, not a
  regression** — his 3% reflects gold priced as of his March-2025 vintage;
  a live figure reflects whatever day the pipeline last ran.
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

## 16. Gold staleness is now quantified: ~0.5pt of GDP low, both keyless alternatives ruled out (2026-07-20, seventh pass)

Follow-up on §14.3/§15.2's "gold staleness" finding: the shipped
`reserves_incl_gold` row isn't just *old*, it's now *materially wrong* —
spot gold ran from the shipped 2025-06 quote (~$3,352/oz) to a ~$5,595
Jan-2026 peak and back to ~$4,000 today, and the row hasn't moved through
any of it. Tasked with trying two specific keyless sources before
accepting the staleness note as the final answer, and — if both failed —
quantifying the error rather than leaving it as an unquantified "old"
flag. Full run output: `docs/review/2026-07-20c-verification.md`.

### 16.1 Two candidates tried, both ruled out for specific, evidenced reasons

**World Bank "Pink Sheet" via DBnomics:** DBnomics does carry a World Bank
provider (`WB`) with a real, gold-relevant dataset —
`commodity_prices` ("Commodity Prices: History and Projections"),
containing `FGOLD-1W` (Gold, nominal, $/troy oz – World). But it is
**annual, not monthly**, and its "latest" period is **2030** — a
*projected* out-year (value $1,100/oz, nowhere near any real gold price
this decade, confirming it's a long-run forecast average). DBnomics does
not mirror the actual monthly Pink Sheet CSV under this provider, only
this annual outlook series. Not usable as a current price under any
reading of "latest."

**Stooq XAUUSD daily CSV:** a bare request 404s; adding a browser-like
`User-Agent` gets a `200`, but the body is an anti-bot interstitial that
requires solving a client-side SHA-256 proof-of-work challenge in
JavaScript before serving the real CSV (`"This site requires JavaScript to
verify your browser"` → `crypto.subtle.digest("SHA-256", ...)` → POST to
`/__verify`). This is not a header or URL-shape problem a plain HTTP
client can route around — it would need a headless browser or a
deliberately-automated challenge-solve, neither appropriate for a
legitimate keyless data source in this pipeline.

**Claim status: VERIFIED (both as negative results)** — both failures were
observed directly (dataset periodicity/projection-year in the JSON;
anti-bot challenge markup in the HTML body), not inferred from a timeout
or a generic error.

### 16.2 The error, quantified live rather than left as "old"

Since neither candidate worked, computed the actual size of the gap
instead of shipping only a staleness flag. Reused the real pipeline
functions (`series.reserves_incl_gold_pct_gdp`, live `TRESEGUSM052N` +
`GDP` from FRED, live Treasury gold-oz holdings) and substituted a
current-market price estimate for the shipped stale one, holding
everything else (gold-oz month, GDP quarter) fixed so the comparison
isolates exactly the price correction:

| Price used | reserves_incl_gold_pct_gdp |
|---|---|
| Shipped (DBnomics IMF PCPS, 2025-06): $3,351.86/oz | **3.7%** (shipped) |
| Current-market estimate: $4,000/oz | **4.2%** |
| ~Jan-2026 peak, for scale: $5,595/oz | **5.6%** |

**Gap: +0.5 points of GDP** (3.7% shown vs. ~4.2% at a $4,000/oz current
estimate) — underlying gold market-value gap $169.5B at the same 261.5M
oz holdings. This independently reproduces the task's own ~4.2-4.3%
estimate almost exactly (landed at 4.2% using its own $4,000/oz figure).
Gold-oz data itself is current through 2026-06; the price series is the
only stale leg (12 months behind as of this pass, matching the shipped
staleness note in §14.3/§14.6).

**Claim status: VERIFIED** — live run against real FRED/Treasury/DBnomics
data, not a back-of-envelope estimate from rounded headline percentages.

### 16.3 Disposition: staleness note kept, no shipped code change

Per the task's own fallback instruction, the shipped staleness `note`
(§14.3/§14.6 — `"⚠ gold priced as of 2025-06 (N months old) — market value
may be off if gold has moved since"`) is kept as-is; no source switch,
since neither candidate produced usable data. **Deliberately not** folding
the $169.5B/+0.5pt magnitude into the shipped `note` string itself: that
number depends on a manually-sourced, non-live "$4,000/oz current market"
estimate the pipeline has no live way to verify or refresh — baking it
into a `tag: "live"` row's own text would blur exactly the live/manual
distinction this project has otherwise been careful to keep (see
`gold.py`'s own docstring: *"a live-tagged number built on a stale price"*
is the failure mode the manual-fallback pattern exists to avoid). The
magnitude belongs here, in documentation a reader can check the
provenance of, not baked into a number the UI presents as live. If a
working live source is found in a future session, this is the first place
to update.

### 16.4 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| DBnomics mirrors a World Bank gold-price dataset (`WB/commodity_prices`, `FGOLD-1W`) | **VERIFIED** — live query, real series returned |
| That dataset is annual with projected out-years, not a usable current monthly price | **VERIFIED** — latest period is 2030, value ($1,100) consistent with a forecast average, not a real quote |
| DBnomics does not mirror the actual monthly World Bank Pink Sheet under provider WB | **VERIFIED (negative)** — only `GEM` and `commodity_prices` exist under WB; neither is the monthly Pink Sheet |
| Stooq's XAUUSD CSV endpoint is gated by a client-side JS proof-of-work anti-bot challenge | **VERIFIED** — challenge markup observed directly in the live response body |
| Stooq is not usable as a plain-HTTP keyless CI source, as currently protected | **VERIFIED (negative)** — confirmed live, not inferred from a timeout |
| The shipped `reserves_incl_gold` row currently reads ~0.5pt of GDP low vs. a $4,000/oz current-market estimate | **VERIFIED** — live computation via the real pipeline functions and real FRED/Treasury data |
| No gold source switched; staleness note kept as-is | **VERIFIED** — no working alternative found |

---

## 17. Gold price fix attempt + a freshness guard for every series (2026-07-20, eighth pass)

Per `TASKgoldpricefreshness.md`: two parts. First, try five named keyless
gold-price sources in order and stop at the first current one, or record
all five as tried-and-failed. Second — "the more valuable half" — add a
freshness guard so a frozen source can never again pass silently, the way
the 2025-06 gold price and (newly discovered this pass) IMF COFER both
did. Full run output: `docs/review/2026-07-20d-verification.md`.

### 17.1 All five candidate gold sources tried, in the specified order — none usable

1. **FRED**, tried first as instructed
   (`series/search?search_text=gold price`, plus `LBMA gold`/`gold
   fixing`/`gold spot`): zero genuine spot/fixing series. The two old LBMA
   fixings, `GOLDAMGBD228NLBM`/`GOLDPMGBD228NLBM`, now return a hard `400`
   — not "discontinued with history," the IDs are gone outright, settling
   the "believed discontinued" question the task flagged as unverified.
   The only current, on-cadence hits among 30 search results are a
   volatility index (`GVZCLS`) and PPI/import/export price *indices*
   (base-year, e.g. `IQ12260`) — none a $/oz spot price.
2. **World Bank Pink Sheet via DBnomics** (provider `WB`): the real
   dataset (`commodity_prices`) exists with a gold series (`FGOLD-1W`),
   but it's annual and its "latest" point is **2030** — a *projected*
   out-year, not an observation (§16.1, prior pass).
3. **Bundesbank**, both directly (three guessed series keys against
   `api.statistiken.bundesbank.de` — all 404) and via DBnomics (provider
   `BUBA`, full 50-dataset catalog dump plus server-side `q=gold`/`q=XAU`
   search): found the real series (`BBEX3`, D-Mark/Frankfurt fixing) —
   but it stops at **end-1998**, pre-euro, permanently discontinued, not
   a stale-but-alive feed.
4. **Nasdaq Data Link** (ex-Quandl), LBMA/GOLD, no-key attempt: blocked
   by an Incapsula anti-bot WAF (`403`, JS challenge page) on both the
   CSV and JSON endpoints. Would need a paid API key (a new GitHub
   secret) to test properly — not added without that being explicitly
   requested.
5. **Stooq** daily XAUUSD CSV, no key (§16.1, prior pass): blocked by a
   client-side SHA-256 proof-of-work anti-bot challenge, not a real
   URL/header problem.

**All five tried, all five fail** — acceptance criterion 1's second
branch. No source switch. DBnomics-mirrored IMF PCPS remains primary,
`data/manual.json`'s fallback remains the fallback, unchanged. Full
findings recorded in `scripts/gold.py`'s module docstring as well as here.

### 17.2 The freshness guard: what it's for, and what it immediately caught

The stale gold price survived every review round this project has done
because **the existing sanity bands check magnitude, not date** — a dead
source returning a plausible in-band number looks completely healthy.
Added `series.freshness()`/`series.require_fresh()`: every fetched series'
latest observation date is compared against a per-cadence threshold
(`FRESHNESS_DAYS_BY_FREQ`: Daily 20d, Monthly 60d, Quarterly 220d), with
explicit overrides where a longer lag is genuinely normal rather than
exempting the series outright, per the task's own instruction:
- **COFER**: 270d (documented as running "a quarter or two" behind even healthy).
- **TRESEGUSM052N** (Total Reserves excl. Gold, IMF/BOP-sourced): 180d.

Series with an existing manual-value fallback (gold price, COFER) raise
inside the same `try`/`except` that already handles fetch failures, so a
frozen source now degrades to manual instead of shipping as falsely
"live." Series with no fallback (the 7 core FRED series, both Treasury
debt-service ratios) raise uncaught, failing the whole run loudly — same
convention as every other guard in this pipeline (exit non-zero, no
partial write).

**First live run immediately caught a second frozen source nobody had
found:** IMF COFER has been stuck at **2025-Q1 for 565 days** — past even
the generous 270d COFER-specific threshold by a wide margin. This is
exactly the failure mode the task predicted ("there may be more than one
frozen series") and exactly why this half of the task is the more
valuable one: the gold price was already known-suspect from earlier
rounds; COFER was not on anyone's radar until the guard checked its date
instead of just its magnitude. The `World CB reserves in USD` row —
previously reported as "live, independently computed, matches closely" in
§9's own table — has therefore *also* been silently stale this whole time.

**Two false positives found and fixed during calibration, not shipped:**
- FRED dates quarterly macro series (`GDP`, `FYGFGDQ188S`, `TCMDO`,
  `IEABC`) to the **start** of the quarter, not the release date. Right
  before the next quarter's print, a perfectly healthy series is
  legitimately ~200 days past its own date-stamp (observed live:
  `2026-01-01`, 200d old, still the genuinely latest point). The initial
  150d Quarterly threshold flagged this as stale; raised to 220d.
- `TRESEGUSM052N` observed at 141d old, still genuinely current (IMF/BOP
  reserves data runs a real, longer lag than domestic monthly series even
  when healthy) — the initial generic 60d Monthly threshold was too tight
  for this specific series; given its own 180d override.

Both fixes are recalibration, not weakening: gold price (414d) and COFER
(565d) still fail decisively at every threshold considered.

**A real, unrelated gap found and fixed in the process:** `data/manual.json`'s
`reservesInclGoldFallback.note` field existed but was never actually
attached to the shipped row — `fetch.py` built the manual fallback dict
without carrying it through. Now fixed; the fallback's own explanatory
note (*"Fallback only, used if the live Treasury gold-holdings or
DBnomics gold-price fetch fails..."*) renders on the row whenever the
fallback is actually in use, which — as of this run — it is.

**`--verify` output** (fetch.py, treasury.py, imf.py, gold.py) now prints
every series' latest observation date, age, threshold, and ok/STALE
status, per acceptance criterion 4.

### 17.3 Full production run: both stale sources correctly degraded to manual

Ran the real `update-data.yml` (`workflow_dispatch`, not just `--verify`)
end to end with all of the above live. Run
`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29756605271`,
committed as `a93e485`:

```
Gold-inclusive reserves unavailable, using manual value: freshness guard:
  gold price (DBnomics PCPS) latest observation is (2025, 6) (414d old,
  today 2026-07-20) — exceeds the 60d threshold for this series' cadence.
IMF COFER unavailable, using manual value: freshness guard: IMF COFER
  USD share latest observation is 2025-Q1 (565d old, today 2026-07-20) —
  exceeds the 270d threshold for this series' cadence.
Wrote public/data.json — generatedAt 2026-07-20T15:47:15Z
  debt_to_gdp                     99%  (2026-Q1, 225 pts)
  debt_service_to_revenue         20%  (2026-06, 42 pts)
  real_rates                     0.6%  (2026-Q2, 258 pts)
```

`reserves_to_gdp` no longer appears in that "live" summary because it
correctly flipped to `tag: "manual"` — **the new `reserves_to_gdp` is
3.0% of GDP** (was 3.7%, live), and **no gold price was used this run** —
the guard rejected the frozen 2025-06 quote during the fallback decision
itself, which is the intended, correct behaviour per the task's own
fallback-chain instruction ("a future outage degrades rather than
breaks"), not a bug. `World CB reserves in USD` similarly flipped to
`manual`, 57.0% (was 57.7%, live). All other live rows (`debt_to_gdp`,
`debt_service_to_revenue`, `real_rates`, `FX reserves excl. gold`, both
debt-service panel rows) are unaffected — their own freshness checks all
passed. §9's table above is updated to reflect both rows' new `manual`
status and why.

**Claim status: VERIFIED** — live `workflow_dispatch` run, not a mock;
`public/data.json` at commit `a93e485` reflects exactly this.

### 17.4 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| FRED has no current gold spot/fixing series (search + explicit ID checks) | **VERIFIED** — live queries, zero usable results, both old fixing IDs return hard 400s |
| World Bank Pink Sheet is not mirrored on DBnomics (only an annual outlook dataset is) | **VERIFIED** — carried forward from §16, re-confirmed |
| Bundesbank's own gold series (`BBEX3`) is discontinued at end-1998 | **VERIFIED** — live query, full catalog + server-side search, observed data range |
| Nasdaq Data Link blocks no-key access via an anti-bot WAF | **VERIFIED** — live 403 with Incapsula challenge markup |
| Stooq blocks no-key access via a JS proof-of-work challenge | **VERIFIED** — carried forward from §16 |
| All five specified gold sources tried and failed; no switch made | **VERIFIED** |
| IMF COFER has been frozen at 2025-Q1 for 565 days | **VERIFIED** — live query, computed directly from the observation dates returned |
| The freshness guard correctly demotes both gold price and COFER to manual in a real production run, without breaking any other row | **VERIFIED** — live `workflow_dispatch` run, `a93e485` |
| Quarterly/TRESEGUSM052N threshold recalibration (220d/180d) doesn't mask genuine staleness | **VERIFIED** — gold price and COFER still fail decisively at the recalibrated thresholds |
| `manual.json`'s fallback `note` field is now actually surfaced on the shipped row | **VERIFIED** — code change, confirmed in the live `a93e485` `data.json` |
| Once a working live gold price is found, the reserves-incl-gold figure is expected to move away from 3.0%/3.7%, not toward it | **ASSUMED** — reasoned from gold's known price path (~$3,352 → ~$5,595 → ~$4,000), not yet observed live since no working live source exists |

---

## 18. Manual-INPUT (not OUTPUT) fallback for gold + COFER; circularity labelled; World Bank/ECB/IMF-IFS retried (2026-07-21, ninth pass)

**What this round covers:** a 3-part user correction to §17's fix. (1)
§17's gold and COFER fallbacks were both manual *outputs* — full
hand-carried percentages, one of them (gold) literally equal to Dalio's
own book figure by construction. Flagged as materially worse than the
stale-but-live number it replaced (3.0% manual vs. 3.7% stale-live, when
gold's actual live-oz-count × current price is closer to 4%). Fix: switch
gold to a manual *price input* (one hand-entered number, ~$4,000/oz,
dated) applied to the still-live Treasury ounce count, and switch COFER's
fallback from the book-transcribed 57.0%/~2024 to the latest *actually
published* IMF figure (57.13%, 2026-Q1). (2) Label the resulting
circularity in §9's calibration table explicitly, so a fallback-vs-book
"match" doesn't read as independent corroboration. (3) Retry three gold
sources not yet properly attempted: World Bank's actual Pink Sheet
(distinct from the CMO forecast table already ruled out in §16), the ECB
Data Portal, and IMF IFS (distinct from the already-tried PCPS dataflow).

### 18.1 A new tag: `manual_price`

Added a fourth provenance tag alongside `live` / `model` / `manual` for
this exact hybrid case — one input hand-entered, everything else
(ounce count, FX-excl-gold, GDP) still live. `Tag.jsx`'s `KINDS` map and
`App.jsx`'s `dotColor` helper both updated; the frontend already handled
an unrecognized tag safely (falls through to the caution/hollow-dot
treatment), confirmed by reading the code before making any change, so
this was a labelling addition, not a rendering fix.

### 18.2 The 3-tier fallback chain, and a real bug it exposed

Redesigned `scripts/fetch.py`'s gold-reserves block from a 2-tier chain
(live → full manual output) to 3-tier: **live** (both ounce count and
price fresh) → **manual price input** (ounce count still live, only the
price hand-entered) → **manual output** (last resort, only if the ounce
count itself is unavailable). `data/manual.json` gained
`goldPriceManualFallback` (price=$4,000/oz, dated 2026-07-20, with a
`history` array giving the last live price and the Jan-2026 peak for
context) as the new primary fallback; the old `reservesInclGoldFallback`
(3.0%, still Dalio's book figure) is retained but re-documented as a
last-resort-only path that is NOT an independent check.

**The first attempt at this had a real bug, caught by a live production
run before it shipped.** The inner exception handler replaced the price
dict with a single entry — `{oz_asof: gpf["pricePerOz"]}` — at the live
ounce-count month. `TRESEGUSM052N` (FX reserves excl. gold) lags the gold
ounce data by several months in practice (2026-03 vs. 2026-06 in the run
that caught this), so that single-point dict shared zero overlapping
months with `TRESEGUSM052N`'s own history. `series.reserves_incl_gold_pct_gdp()`
requires overlap between the two to compute anything, so it raised `"no
overlapping quarters"` — caught by the *outer* exception handler, which
misreported it as "live ounce count itself failed" (it hadn't) and fell
all the way back to the old 3.0% manual output, silently defeating the
entire fix. Evidence, verbatim from the production run
(`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29767418637`,
job `88436912553`, commit `44d4320` — since superseded):
```
Gold price unavailable/stale, using manual price input at the live oz month: freshness guard: gold price (DBnomics PCPS) latest observation is (2025, 6) (414d old, today 2026-07-20) — exceeds the 60d threshold for this series' cadence. The source is likely dead or frozen, not just running a normal lag.
Gold-inclusive reserves unavailable even with a manual price input (live ounce count itself failed), using the full manual fallback: reserves_incl_gold_pct_gdp: no overlapping quarters
```
**Fix:** instead of discarding whatever real (if stale) historical price
data the fetch attempt actually returned, keep it and only patch in the
manual price for the months it's missing — restoring full month coverage
so the intersection with `TRESEGUSM052N`'s own lagging history is
non-empty again, while old chart history still uses real historical
prices rather than the flat manual value:
```python
gold_price_monthly = {}
try:
    gold_price_monthly = G.gold_price_usd_per_oz()
    price_asof = max(gold_price_monthly)
    S.require_fresh(...)
    price_is_live = True
except Exception as price_e:
    gpf = mu["goldPriceManualFallback"]
    for ym in gold_oz_monthly.keys() - gold_price_monthly.keys():
        gold_price_monthly[ym] = gpf["pricePerOz"]
    price_asof = oz_asof
    price_is_live = False
```
Verified two ways: (1) locally, against a strengthened mock test that now
simulates the real lag (a `TRESEGUSM052N` stub cut off 3 months before
"today" and a gold-price stub whose real history also stops short of the
gap) — the pre-fix code reproduces the exact same "no overlapping
quarters" failure against this mock, and the post-fix code resolves it
correctly to `manual_price`, not `manual`; (2) live, in production (below).

### 18.3 Live production run: confirmed working end to end

Two production runs were needed. The first re-run after the fetch.py fix
(`29806735725`, job `88558737649`) computed correctly — no more "no
overlapping quarters" — but its own `git push` step lost a race against
an unrelated STATUS.md commit pushed from this session moments earlier,
so the resulting `data.json` was never actually saved to the branch. A
second `workflow_dispatch` (`29806949328`, job `88559389516`,
2026-07-21 06:25-06:27 UTC, committed as `b0e8827`) ran clean:
```
Gold price unavailable/stale, patching a manual price input across the gap: freshness guard: gold price (DBnomics PCPS) latest observation is (2025, 6) (415d old, today 2026-07-21) — exceeds the 60d threshold for this series' cadence. The source is likely dead or frozen, not just running a normal lag.
IMF COFER unavailable, using manual value: freshness guard: IMF COFER USD share latest observation is 2025-Q1 (566d old, today 2026-07-21) — exceeds the 270d threshold for this series' cadence. The source is likely dead or frozen, not just running a normal lag.
Wrote public/data.json — generatedAt 2026-07-21T06:26:59Z
```
Resulting values, read directly from the committed `public/data.json`:
- `reserves_to_gdp`: **4.1%** of GDP, `tag: "manual_price"`, `src: "derived · Treasury (gold oz, live, 2026-06) + manual price ($4,000/oz as of 2026-07-20) + FRED"`, `asOf: "2026-Q1"`. Close to, but not exactly, the task's own ~4.2-4.3% estimate — expected, since the task's figure was a rough hand-estimate and this pipeline's number is the actual computed ratio against real live `TRESEGUSM052N`/GDP data at their native (lagging) latest quarter. **Further from Dalio's 3% than even the old stale-priced 3.7% was** — correct, since gold has risen well past his March-2025 price; the widening is the fix working, not a regression.
- `World CB reserves in USD`: **57.1%**, `tag: "manual"` (COFER has no live-partial-input concept — it's a single percentage, not derived from a live component + a separate price), `src` names the real IMF figure and cites STATUS.md for why it deliberately isn't the book value.

**Claim status: VERIFIED** — both figures read directly from the live
`workflow_dispatch` output and the committed `public/data.json` at
`b0e8827`, not computed by hand or assumed.

### 18.4 The circularity, now labelled

§9's table previously logged both rows above as "manual, matches Dalio's
figure" without flagging that the match was tautological — the fallback
value literally *was* his figure, transcribed into `data/manual.json`.
§9's two rows are now updated in place (not a new table) to say so
explicitly: the FX-reserves row is marked `manual_price` and its
narrative states the old fix was retracted for this reason; the COFER row
states the new value is a **genuine, non-circular near-match** specifically
*because* it no longer traces back to the book. See §9's table directly.

### 18.5 World Bank Pink Sheet, ECB Data Portal, IMF IFS — three more sources tried, all ruled out

None of the three replaces the frozen DBnomics/IMF-PCPS gold price;
`scripts/gold_source_retry.py` (run twice via a temporary CI workflow,
findings captured below, then deleted per this project's
diagnostic-not-a-feature convention — commit `f0d7209`) found:

- **World Bank — the actual monthly Pink Sheet, not the CMO forecast
  table already ruled out in §16.** All 14 DBnomics `WB` datasets
  enumerated by name and description. `GEM` (Global Economic Monitor) is
  CPI/inflation series per country, not commodities. `commodity_prices`
  is confirmed to be the same annual Commodity Markets Outlook table
  already ruled out (its "latest" value is a 2030 *projection*).
  **DBnomics simply does not mirror the World Bank Pink Sheet at all** —
  an exhaustive negative, not a search-term artifact.
- **ECB Data Portal.** Found the right dataset category (`FM`, confirmed
  present alongside other commodities like Brent crude) but no gold/XAU/
  bullion/precious-metal series turned up across 4 keyword variants plus
  a raw naming-convention sample of the dataset. Two guessed direct-API
  series keys both 404'd. **No usable gold price found.**
- **IMF IFS** (distinct dataset from the already-tried PCPS). Does
  contain gold-related series, but they are all per-country reserve
  *holdings* valued at market price — a stock/quantity measure, not a
  market price benchmark itself. **Not usable as a price source** for
  this pipeline, which needs a $/oz series to multiply against ounces,
  not an already-valued holdings figure.

No source switched. The manual-price-input mechanism (§18.2) remains the
correct fallback until a working live source is found.

### 18.6 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| §17's original gold/COFER fallback was less accurate than the stale-live value it replaced, and circular against §9's own table | **VERIFIED** — user-flagged, confirmed by inspection: `reservesInclGoldFallback` (3.0%) was hand-set to Dalio's own book figure, and §9 compared the shipped value against that same book |
| The first manual-price-input implementation had a live bug that silently fell through to the old full-manual output | **VERIFIED** — live production run `29767418637`/`44d4320`, "no overlapping quarters" traced to a single-entry price dict not overlapping `TRESEGUSM052N`'s lagging history |
| The fix (patch only the missing months, keep real historical data) resolves the bug | **VERIFIED** — both locally (strengthened mock reproducing the lag) and live (`29806949328`/`b0e8827`) |
| `reserves_to_gdp` is now 4.1% of GDP, `tag: manual_price`, live ounce count (2026-06) × manual price ($4,000/oz) | **VERIFIED** — read directly from committed `public/data.json` |
| `World CB reserves in USD` is now 57.1%, `tag: manual`, the real 2026-Q1 IMF COFER figure, not the book value | **VERIFIED** — read directly from committed `public/data.json`; underlying figure cross-checked in §17→§18's manual.json update against two independent secondary sources citing the same IMF release |
| DBnomics does not mirror the World Bank Pink Sheet in any of its 14 `WB` datasets | **VERIFIED** — all 14 enumerated by name/description |
| ECB Data Portal has no gold/XAU series discoverable via keyword search or raw sample of its `FM` dataset | **VERIFIED** — 4 keyword variants + raw sample, all negative; 2 guessed series keys 404'd |
| IMF IFS's gold series are reserve holdings, not a price benchmark, and are therefore unusable here | **VERIFIED** — live query, series descriptions confirm holdings/stock framing |

---

## 19. Freshness guard extended to manual inputs; per-row provenance assertion (2026-07-21, tenth pass)

**What this round covers:** a follow-up correction identifying two classes
of silently-wrong-data this project hadn't yet closed. (1) §17's
freshness guard only ever checked FETCHED series' dates — a hand-entered
manual value (the new `goldPriceManualFallback`, §18) is exactly as
capable of going stale, and had no threshold of its own at all. (2) A
fallback firing (live → manual/manual_price) was only ever visible as an
incidental `print()` line in the middle of a long build log — nothing
asserted that the shipped tag matched what a healthy run should have
produced, and nothing made a fallback firing structurally impossible to
miss. Both closed this round; a third, narrower ask (retry World Bank/
ECB/IMF IFS) doesn't apply here — that was §18's task, not this one.

### 19.1 Manual-value freshness thresholds

Three new thresholds in `series.py`, each reasoned from what the value
stands in for, not an arbitrary number:
- `GOLD_MANUAL_PRICE_FRESH_DAYS` (60d) — same cadence as the live Monthly
  threshold it replaces; the hand-entered gold price shouldn't go
  unreviewed longer than the live source it's standing in for would.
- `CBRESERVES_MANUAL_FRESH_DAYS` (270d, = `COFER_FRESH_DAYS`) — the
  manual COFER snapshot is a snapshot of the same series, so it gets the
  same cadence reasoning.
- `MANUAL_FRESH_DAYS` (180d) — the catch-all for `lastChecked`, which is
  the *implicit* date for every manual value that has no `asOf` of its
  own (§19.2). A review cadence, not a data cadence — most of what it
  governs (TIC holder shares, CBO's projection, market-cap shares) has no
  natural update schedule at all.

All three are checked with the non-raising `S.freshness()`, not
`require_fresh()` — deliberately non-fatal. These are already the
fallback of last resort; there's no further live source behind them to
degrade to, so failing the build over their own staleness would take the
whole site down over a metadata gap, the opposite of the "degrade rather
than break" principle §17/§18 built the fallback chains around in the
first place. Instead, staleness triggers `fetch.py`'s new `loud_warn()` —
a console banner AND a GitHub Actions `::warning::` annotation (a real
Annotation on the run's Checks page, not just a line in a log a human
has to go find) — and, when the stale manual value is the one actually
shipped, the staleness is folded into the row's own `note` field, so a
site visitor sees it too, not only a CI log:
```python
def check_manual_freshness(label, date_str, max_age_days, today=None):
    f = S.freshness(label, date_str, max_age_days, today)
    if f["stale"]:
        loud_warn(f"manual value '{label}' is {f['age_days']}d old ...")
    return f
```
Wired in at all three of the places a manual value can actually ship:
the gold-price manual-input branch (checks `goldPriceManualFallback.asOf`),
the full-manual gold-output branch (checks `lastChecked`, since
`reservesInclGoldFallback` has no `asOf` of its own), and the COFER
manual-fallback branch (checks `reserveCurrency.cbReserves.asOf`). Also
wired into `--verify` unconditionally (`audit_manual_values()`), so
drift is visible during routine health checks even while the live
sources these values would replace are still healthy — not only at the
moment a fallback actually fires.

### 19.2 Audit: which manual values have no date at all

Ran `audit_manual_values()` against the current `data/manual.json`:
```
Manual-value freshness audit (data/manual.json):
  goldPriceManualFallback.asOf                            2026-07-20      1d old   60d threshold  ok
  reserveCurrency.cbReserves.asOf                         2026-Q1       201d old  270d threshold  ok
  lastChecked (governs every dateless value below)        2026-07-18      3d old  180d threshold  ok
  11 manual values have NO individual date, relying solely on
    lastChecked above:
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
**Finding: 11 of the 14 manual values in `manual.json["US"]` carry no
date of their own** — TIC holder-composition shares, the CBO 10-year
projection, sovereign-wealth/hard-FX facts, and the three reserve-
currency market-share figures (world trade/debt/equity in USD) all rely
solely on the single top-level `lastChecked` for any notion of
"how old is this." That's a real gap for the ones with an actual
natural update cadence (TIC data, CBO baselines) — currently
indistinguishable in age from `sovereignWealth: "None"`, a fact that
doesn't go stale at all. Not fixed this round (would mean sourcing 11
new independently-tracked dates, out of scope for a freshness-guard
pass) — recorded here as the honest answer to "check whether any other
manual value lacks a date entirely," per the task.

### 19.3 Per-row provenance assertion

New `assert_provenance(fallbacks_fired, row_label, expected_tag,
actual_tag, reason)` in `fetch.py`, called at both places a row's tag can
legitimately diverge from `"live"`:
```python
assert_provenance(fallbacks_fired, "Reserves incl. gold (market)", "live",
                   reserves_incl_gold_tag, reason="...")
assert_provenance(fallbacks_fired, "World CB reserves in USD", "live",
                   cb_reserves_tag, reason="...")
```
A mismatch is loudly warned (same `loud_warn()` mechanism as §19.1) and
recorded in a new `country.provenance.fallbacksFired` array — empty on a
fully-healthy run, non-empty (with row, expected tag, actual tag, and
reason) whenever a fallback fired. This is the structural fix for the
actual failure mode found in §18.2: that bug's symptom was a legitimate
`print()` line sitting in the CI log, easy to miss unless someone read
the whole build log start to finish — now a fallback firing is a
first-class, machine-checkable field in the shipped data itself, not
just prose in a log.

**Deliberately non-fatal, same reasoning as §19.1**: the two rows this
guards (gold reserves, COFER) exist specifically so a dead source
degrades the site rather than takes it down. Asserting and then failing
the build on every mismatch would defeat the fallback chains §17/§18
built for exactly this scenario. The assertion's job is to make a
fallback firing *undeniable*, not to treat "a fallback fired" as itself
an error — that would conflate "the underlying source is unhealthy"
(true, and already surfaced via the `manual`/`manual_price` tag and the
row's own `note`) with "the pipeline behaved incorrectly" (false — this
is the pipeline working as designed under a real source outage).

### 19.4 Verified locally

Extended the scratchpad mock test (not part of the repo) with three new
assertions: (1) a fully-live run produces `provenance.fallbacksFired ==
[]`; (2) the manual-price scenario (stale gold price, live oz) records a
`manual_price` mismatch entry; (3) the full-manual scenario (both stale)
records a `manual` mismatch entry. All three pass, and the loud-warning
banners + `::warning::` annotations print correctly in each fallback
case, confirmed by inspecting the raw test output.

### 19.5 Live production run

Two runs were needed (same race pattern as §18.3: a `workflow_dispatch`'s
own `git push` losing against a STATUS.md commit pushed moments later
from this session). The clean run
(`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29809275699`,
job `88566499233`, 2026-07-21 07:07-07:09 UTC) pushed as `3335451`.
Verbatim `--verify` output showing the new manual-value audit running
unconditionally, plus the build step showing both loud warnings firing
correctly for the (still-expected, unchanged from §18) gold-price and
COFER fallbacks:
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
The `##[warning]`-prefixed lines are GitHub's own rendering of the
`::warning::` annotations — they appear as actual Annotations on the
run's Checks page, not just log text. `public/data.json`'s
`countries.US.provenance.fallbacksFired`, read directly from the
committed file:
```json
[
  {
    "row": "Reserves incl. gold (market)",
    "expectedTag": "live",
    "actualTag": "manual_price",
    "reason": "live gold price and/or holdings fetch failed or exceeded its freshness threshold"
  },
  {
    "row": "World CB reserves in USD",
    "expectedTag": "live",
    "actualTag": "manual",
    "reason": "live IMF COFER fetch failed or exceeded its freshness threshold"
  }
]
```
Headline values unchanged from §18 (as expected — nothing about the
underlying fallback logic changed this round, only its visibility):
`reserves_to_gdp` 4.1% (`manual_price`), `World CB reserves in USD`
57.1% (`manual`). None of the three manual dates (`goldPriceManualFallback.asOf`,
`cbReserves.asOf`, `lastChecked`) are stale as of this run, so no
manual-value-staleness warning fired — only the (expected, unchanged)
provenance mismatches for the two known fallback rows.

**Claim status: VERIFIED** — live `workflow_dispatch` run, not a mock;
`public/data.json` at commit `3335451` reflects exactly this, including
the new `fallbacksFired` field.

### 19.6 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| §17's freshness guard only checked fetched series, not manual.json's own dated values | **VERIFIED** — read directly from the pre-this-round code: `require_fresh()` was only ever called on `raw[sid]`/Treasury/COFER/gold fetch results, never on `goldPriceManualFallback.asOf` or `cbReserves.asOf` |
| A fallback firing was only visible as a `print()` line, not a structured/asserted signal | **VERIFIED** — this is exactly how §18.2's bug was found: by reading the build log line-by-line, not by any automated check catching the mismatch |
| 11 of 14 manual.json values have no date of their own | **VERIFIED** — `audit_manual_values()` output above, cross-checked by hand against `data/manual.json`'s actual keys |
| The new manual-value freshness checks and provenance assertion don't false-positive on a healthy run | **VERIFIED** — local mock test, fully-live scenario asserts `fallbacksFired == []` and no staleness warnings fire (all three manual dates are within their thresholds as of 2026-07-21) |
| The provenance assertion correctly fires for both fallback tiers (`manual_price`, `manual`) | **VERIFIED** — local mock test, both scenarios explicitly assert the recorded entry's `actualTag` |

---

## 20. Equation button: the maths behind every metric, in Dalio's notation (2026-07-21, eleventh pass)

**What this round covers:** `TASK-equation-button.md` — a small disclosure
control on every derived metric revealing the formula behind it in Ray
Dalio's own variable names (transcribed from *How Countries Go Broke*
Ch. 3, "The Mechanics in Numbers and Equations," pp. 69-73), with source
identifiers demoted to a mapping table below the maths rather than being
the headline.

### 20.1 Two separate concerns, kept separate

Every metric's panel can show up to two blocks: a **Definition** (the
identity actually computed this run — always present) and, only where
Dalio gives one, his **projection formula** (forward-looking, explicitly
labelled as such — never presented as though it produced the number on
screen). This matters because every one of Dalio's Ch. 3 equations has
"Future X" on the left-hand side; the dashboard shows current observed
levels, not his projections. Conflating the two would make the feature
actively misleading, per the task's own framing.

### 20.2 Backend: `key` and `terms` added to every row

`scripts/fetch.py` now attaches a stable `key` to every panel row (vitals
already had one), and a `terms` array to the five rows whose Dalio
equation names multiple distinct inputs the pipeline currently only
exposes as one combined row: net interest ÷ revenue, gross interest ÷
revenue, debt ÷ revenue, real 10-year rate, and reserves incl. gold. Each
term carries its own `{label, src, asOf, tag}` — computed fresh from this
run's actual fetch results (`_series_asof()` formats a raw series' latest
date the same way the rest of the pipeline does; `_term()` is a plain
constructor). For the reserves row specifically, `reserves_incl_gold_terms`
is built only inside the try block that succeeds (live or manual_price
tier) — the full-manual fallback has nothing to break down, so it's left
`None` and the frontend falls back to a single row built from the parent
row's own `src`/`asOf`/`tag`, same as every other (non-compound) row.

**Per the task addendum, nothing about provenance is hardcoded in
`src/content/`.** `src/content/equations.js` holds only the formulas,
Dalio quotes, and caveats — static, hand-written, doesn't change month
to month. The mapping table's src/asOf/tag always comes from `row.terms`
(or the single-row fallback) at render time, so a new tag added to the
pipeline (like `manual_price` was) needs no change to this file — it just
renders, exactly the way `Tag.jsx` already falls through safely for an
unrecognized `kind`.

### 20.3 Frontend: `Frac`, `EquationLine`, `EquationButton`

No LaTeX dependency — `Frac.jsx` is a ~15-line numerator/rule/denominator
stack in plain styled HTML; `EquationLine.jsx` lays a mix of plain-text
parts and `Frac`s out in a wrapping flex row. `EquationButton.jsx` is the
disclosure itself: a small `ƒx` toggle (`aria-expanded`, `aria-controls`,
a descriptive `aria-label`), rendering nothing when `src/content/equations.js`
has no entry for the row's `key` (the "row without an entry simply shows
no button" rule). Wired into `MetricRow.jsx` (every panel row) and
`App.jsx` (the four top vital-sign cards) via the row's own `key`/`terms`.
Every one of the 19 metric keys in `equations.js` — both `kind: "derived"`
rows with a real formula and `kind: "observed"` rows (a directly published
series or a hand-entered fact) — gets a button; observed rows render
"Directly observed — no derivation" plus their own definition, per the
task's explicit allowance that this is "a useful answer, not a failure."

### 20.4 A real overflow bug, found and fixed before shipping

First browser pass at 390px width showed `document.documentElement.scrollWidth`
at 481px against a 390px viewport — genuine horizontal overflow. Root
cause: the mapping table's term rows tried to fit a label and a long,
unbroken `src` string (e.g. "Treasury (MTS mts_table_4, total receipts
net of refunds, TTM)") side by side in a `shrink-0` flex row; flex's
default `min-width: auto` on a `shrink-0` item refuses to shrink below
its content's natural width, so the row just grew past the viewport
instead of wrapping. Fixed by stacking each term (label, then src/asOf/tag
below it) instead of trying to fit them on one line — a block-level
stack wraps naturally at any width, with no flex-shrink interaction to
get wrong. Also added a `max-width` guard to `Frac`'s numerator/denominator
spans for the same reason (long formula terms have the identical failure
mode). Re-tested: all 24 equation buttons on the page opened one at a
time at a 390px viewport, `scrollWidth` checked after each — zero
overflow across all of them, confirmed via a scripted Playwright pass,
not just eyeballing one row.

### 20.5 Verified in a real browser

Per this project's own UI-testing convention: started the Vite dev
server, drove it with Playwright (`chromium-cli` wasn't available in
this environment; used the `playwright` package already in
`node_modules` directly instead), against a full-featured local
`data.json` generated from the scratchpad mock test (production
`data.json` was temporarily swapped in, then restored byte-for-byte
before committing — confirmed via `git status` showing no diff).
Checked:
- **Golden path**: click a `ƒx` button → panel opens, shows Definition,
  Dalio's formula (fraction layout rendering correctly), the mapping
  table with real src/asOf/tag values and a live `Tag` pill, and caveats.
- **Keyboard + ARIA**: `aria-expanded` toggles `false`→`true`→`false`
  correctly across click and `Enter`-key activation (confirmed
  programmatically, not just visually).
- **Observed-only row**: "Share in hard (foreign) FX" renders "Directly
  observed — no derivation" with its own definition and a single-row
  mapping table pulled from the row's own `src`/`tag`.
- **390px width**: zero horizontal overflow across all 24 buttons on the
  page, both before (found the bug) and after (confirmed fixed) §20.4's
  fix.
- **Console**: zero console/page errors throughout.

**Claim status: VERIFIED** — live Playwright browser session against the
actual dev server and built components, screenshots inspected directly,
not assumed from code review.

### 20.6 Bundle size impact

Measured via `npm run build`, isolating the frontend diff (`git stash`
of just the `src/`/`index.css` changes, rebuild, compare):

| | Before | After | Δ |
|---|---|---|---|
| JS (raw) | 163.47 kB | 174.47 kB | +11.00 kB |
| JS (gzip) | 52.84 kB | 56.08 kB | **+3.24 kB** |
| CSS (raw) | 9.47 kB | 9.97 kB | +0.50 kB |
| CSS (gzip) | 2.71 kB | 2.86 kB | +0.15 kB |

**+3.39 kB gzip total** (~6% growth on the JS bundle) for four new
components, one new content file (19 metric entries' worth of hand-written
formulas/prose), and the equation-button feature end to end. No new
runtime dependency was added — the "no LaTeX" call in §1 of the task file
held up in practice, not just in principle.

### 20.7 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| Every Ch. 3 formula/quote in `equations.js` traces to `TASK-equation-button.md` §2, nothing invented | **VERIFIED** — direct transcription, checked against the task file line by line while writing content |
| The mapping table reads src/asOf/tag from data.json at render time, never hardcoded in content | **VERIFIED** — `equations.js` contains no src/asOf/tag literals; confirmed by grep and by design (EquationButton.jsx builds `terms` from `row.terms`/`row.src`/`row.asOf`/`row.tag` only) |
| The first mobile layout had a real horizontal-overflow bug | **VERIFIED** — measured `document.documentElement.scrollWidth` = 481px against a 390px viewport, live in a Playwright browser, not inferred |
| The fix resolves it across every button on the page, not just the one row that surfaced it | **VERIFIED** — scripted pass opened all 24 buttons individually at 390px, checked `scrollWidth` after each, zero overflow |
| Keyboard operability and ARIA state are correct | **VERIFIED** — `aria-expanded` read programmatically before/after both a click and an `Enter` keypress |
| No new runtime dependency (no LaTeX library) was pulled in | **VERIFIED** — `package.json` unchanged this round; fraction rendering is ~15 lines of styled HTML (`Frac.jsx`) |
| Bundle size impact is +3.39 kB gzip | **VERIFIED** — `npm run build` output compared before/after via `git stash` isolation of the frontend-only diff |

---

## 21. CBO projections: Dalio's forward-looking equations, made real (2026-07-21, twelfth pass)

**What this round covers:** `TASKprojections.md` — a projection layer from
CBO's published baseline (the same source Dalio himself uses, his
footnote 20), run deliberately after the equation-button pass (§20) since
the projection rows are exactly what its "Dalio's formula" blocks
describe. Three things: (1) live 10-year projections for debt/GDP and
debt/revenue, extending the dashboard's existing sparklines forward
rather than adding separate charts; (2) Dalio's equation #3 (the interest
rate that would keep debt flat), computed entirely from CBO's baseline
and compared against the ACTUAL average effective rate (Treasury, live);
(3) replacing the hand-carried, undated 122% debt projection
(`data/manual.json`, one of the 11 dateless values §19.2 found) with a
live fetch of CBO's current vintage.

### 21.1 A better source than the task assumed — verify, don't scrape

The task's own brief assumed downloadable xlsx files from cbo.gov and
said to "verify the current URLs and file formats rather than assuming."
Doing so found something better: CBO's own machine-readable data mirror,
**`US-CBO/cbo-data` on GitHub** — an official CBO product ("for use by
programmers, AI agents, and automated systems," per its own README), not
scraped xlsx. It publishes exactly the needed dataset
(`ten_year_budget`, publication #51118) as clean, versioned, long-format
CSVs, one file per vintage (`annual_fy_<YYYY-MM>.csv`), with a documented
`schema.json`. Used instead of the task's assumed approach —
`scripts/cbo.py`'s module docstring records this reasoning.

**Verified against three independently-known facts before trusting it**
(cbo.gov itself is not reachable from this project's dev sandbox — proxy
policy denial, same as `github.io` earlier this session — but
`raw.githubusercontent.com` and `api.github.com` are, the same "not
reachable from dev, but CI has full internet access" asymmetry every
other source in this project has, per `treasury.py`'s own docstring):
- Vintage `2024-06`'s FY2034 debt/GDP = **122.4%** — Dalio's own stated
  figure (his book cites CBO's footnote 20; the task file's own
  calibration target).
- Vintage `2025-01`'s FY2035 debt/GDP = **118.5%** — matches the task
  file's own stated "January 2025 outlook projected 118% by 2035."
- Vintage `2026-02`'s FY2026 = **100.6%** (~101%) and FY2036 = **120.2%**
  (~120%) — matches independently reported figures for the current
  (February 2026) CBO baseline.

Three independent confirmations, not one — this is a trustworthy source,
not a lucky guess.

### 21.2 What's built: three rows in the Government debt panel

1. **"Debt, 10-yr projection"** — was `manual`, now `tag: "projection"`,
   live from the current CBO vintage. Its own dedicated chart (not merged
   into the live `debt_to_gdp` row, which needs no projected tail
   duplicating this one) extends the existing live debt/GDP history with
   CBO's annual projected tail. Vintage and the current-law assumption
   are stated in the row's own `note`, per the task's explicit
   requirement ("show the vintage on every projected row in the UI, not
   just in provenance").
2. **"Debt vs revenue"** (existing live row) — its chart gains the same
   kind of projected tail (debt held by the public ÷ total revenue, both
   from CBO's baseline); the row's own headline value/`asOf` are
   unchanged — still the live, current figure. Only the chart gains a
   dashed forward extension, per the task's central design constraint
   (§1: a projection must never be mistaken for a measurement).
3. **"Interest rate to keep debt flat (Dalio eq. #3)"** — new,
   `tag: "projection"`, computed entirely from CBO's own baseline (see
   §21.3). Its `note` states the ACTUAL average effective rate on
   marketable debt (Treasury, live) and the gap between them, so the
   comparison the task calls "the single most useful thing this feature
   can show" is legible directly on the row, not just implied by the
   chart.

**Deliberately NOT extended:** "Net interest (to the public)"'s chart.
CBO's own projected "net interest" concept doesn't cleanly match this
row's precise definition (net-to-public, excluding Government Account
Series interest — see `treasury.py`'s module docstring) — extending it
with a mismatched-basis series would misrepresent both. Recorded as a
deliberate scope decision, not an oversight, same as this project's
practice of not forcing a match it can't defend (e.g. §14.4's total-debt
hypotheses, eliminated rather than forced).

### 21.3 Equation #3, computed from CBO's own numbers — no home-grown forecasting

```
  Interest Rate Required                      (Future Expenses Excl. Interest − Future Revenue)
  to Keep Debt Flat      =  Revenue Growth −  ─────────────────────────────────────────────
                                                        Starting Debt Level
```

Every term is CBO's own published baseline field, computed per projected
fiscal year (`series.py`'s `interest_rate_to_keep_debt_flat()`):
- **Revenue Growth** — year-over-year change in CBO's own
  `proj_rev_total`, including the vintage's first (actual, not
  projected) year as the base for the first projected year's growth.
- **"Future Expenses Excl. Interest − Future Revenue"** — CBO's own
  `proj_primary_deficit`, sign-flipped. Verified live (not assumed) that
  this equals `outlays_total − outlays_net_interest − rev_total` exactly,
  to the dollar, in every fiscal year checked.
- **"Starting Debt Level"** — CBO's own `proj_debt_held_by_public_begin`,
  not a prior-year lookup into the end-of-year series (avoids an
  off-by-one at the first projected year, and uses the field CBO itself
  designed for this).

Nothing here is extrapolated, fitted, or a scenario output — every input
traces directly to a CBO-published field (TASKprojections.md §1: "Do not
build: our own forecasts"). Sample computed values (current, Feb-2026
vintage): the required rate ranges roughly 0.6%–4.2% across the 10-year
window against an actual current average effective rate (Treasury,
marketable securities) of ~3.3% — some years above, some below, exactly
the kind of "is the debt stabilising or not" signal the task asked for.

### 21.4 Treasury additions: the actual rate (live, used) + a maturity probe (diagnostic only)

`treasury.py` gained `avg_interest_rate_marketable()` — Treasury's own
published average interest rate across all MARKETABLE debt (`/v2/accounting/od/avg_interest_rates`,
the "Total Marketable" row), the ACTUAL rate equation #3's row compares
against. Marketable-only, not the blended total including
non-marketable Government Account Series securities (a different,
largely-imputed rate) — matches the scope of "debt held by the public"
that equation #3's Starting Debt Level term uses, an apples-to-apples
comparison.

The task's acceptance criteria also ask for the MSPD maturity-profile
endpoint ("share of debts coming due," Dalio's equation #2 term) to be
"confirmed and dumped." This is genuinely NOT needed by anything built
this round — equation #3's terms are all CBO-baseline, and the debt-service
rows (equation #2) were already built in an earlier pass using interest
alone, not interest+principal. Added `maturity_profile_probe()` as an
honest best-effort: tries three plausible MSPD endpoint candidates in
order and reports whichever (if any) resolves — groundwork for a future
equation-#2 pass, not a claim that any specific endpoint is confirmed
correct (this project's dev sandbox can't reach `api.fiscaldata.treasury.gov`
to test it directly — see `--verify`'s live dump for the actual result).

### 21.5 Vintage handling

`cbo.py`'s `list_vintages()` lists the GitHub dataset directory (via the
Contents API) and picks the lexicographically-last `annual_fy_<YYYY-MM>.csv`
— a new CBO vintage is picked up automatically, no code change needed,
no hardcoded "current" vintage to go stale. `vintage_label()` builds a
factual, data-derived description ("CBO 10-Year Budget Projections,
February 2026 baseline (FY2025–FY2036, current law)") from the vintage
string and the fiscal-year range actually present in the fetched file —
not a guessed report title. Freshness threshold: `S.FRESHNESS_DAYS_BY_FREQ["Annual"]`
(400d, already existing in `series.py` — reused rather than inventing a
new constant), matching CBO's roughly-twice-a-year cadence, per the
task's own recommendation.

`provenance.cboVintage` carries this label at the country level; every
projected row also states it in its own `note` — both, per the task's
explicit instruction ("show the vintage on every projected row in the
UI, not just in provenance"), since a jump in these rows should read as
"new baseline landed," never as "data error" or "news about the fiscal
position."

### 21.6 Presentation: projections cannot be mistaken for measurements

New `projection` tag (`Tag.jsx`) — dashed border (not solid), sharing
`model`'s blue but visually distinguished by the dash, matching the
dashed line convention on its chart. `Chart.jsx` now splits any history
array containing `projected: true` points into a solid historical
polyline and a dashed projected polyline (starting at the shared
transition point, so the line reads as continuous, not disconnected),
plus a shaded background region from the transition to the chart's right
edge and a small "PROJECTED" label — three redundant signals (dash,
shade, label), not just one, per the task's "a reader must never mistake
a projection for a measurement." The transition point's marker is a
hollow ring instead of a filled dot when the series' last point is
itself projected (matching this project's existing filled/hollow
convention for live vs. non-live). Charts with no projected points render
exactly as before — purely additive, confirmed via the existing full
mock-test suite still passing unchanged.

`equations.js` (§20) updated for the three new/changed rows:
`debt_10yr_projection`'s entry rewritten (was "manually hand-entered,"
now live, with a caveat recording the exact June-2024-vintage
reproduction of Dalio's 122%); new `interest_rate_to_keep_debt_flat`
entry with Dalio's actual equation #3 and its diagnostic-comparison
caveat; `debt_to_revenue`'s caveats gained a note about its own chart's
new projected tail.

### 21.7 §9 calibration: both book targets, marked at his vintage

Per the task's explicit instruction (§5), both forward figures are now
in §9's table, computed at Dalio's *own* March-2025 vintage (June 2024
CBO baseline) rather than the current one, with the mismatch against the
current vintage flagged as expected:
- **Debt/GDP in 10 years: 122.4%** (computed) vs. his stated 122% — an
  almost-exact reproduction, confirming June 2024 as his source.
- **Debt/revenue in 10 years: 679.3%** (computed) vs. his stated ~700% —
  the more interesting test, since he *derives* this ratio rather than
  transcribing it. Close, not exact (−21pt) — a real, evidenced finding,
  not forced to match.

### 21.8 Verified locally, then in a live browser

Local: extended the scratchpad mock test with real CBO data (fetched
once via `raw.githubusercontent.com`, which this sandbox CAN reach, then
stubbed as `current_vintage_data()`'s return value, since the
vintage-*listing* call specifically needs `api.github.com`, which this
sandbox cannot reach — same "not reachable from dev" pattern as every
Treasury endpoint). Confirmed: all three new/changed rows appear with
correct tags and history shapes on a healthy run; a simulated CBO outage
correctly falls back the projection row to manual, omits equation #3
entirely, strips the projected tail from "Debt vs revenue," and records
the mismatch in `provenance.fallbacksFired` (STATUS.md §19's mechanism,
reused here without any changes needed — confirms that pass generalised
correctly to a new fallback-capable row).

Browser: same Playwright approach as §20 (dev server + `playwright`
package directly). Screenshots confirmed — the dashed projected tail,
shaded region, "PROJECTED" label, and hollow end-marker all render
correctly on both "Debt vs revenue" and "Debt, 10-yr projection"; the
equation-#3 row's fully-projected chart (no historical portion at all)
renders as an all-dashed line with the label at the chart's left edge,
correctly handling that edge case. Re-ran the 390px overflow check
established in §20 (a real bug was found there) against all three new
rows and their equation-button panels — zero overflow, zero console
errors.

**Claim status: VERIFIED** — live CBO/Treasury data fetched directly
against `raw.githubusercontent.com`/local mock, screenshots inspected
directly in a real Playwright browser session, not assumed from code
review.

### 21.9 Bundle size impact

| | Before | After | Δ |
|---|---|---|---|
| JS (gzip) | 56.08 kB | 57.04 kB | **+0.96 kB** |
| CSS (gzip) | 2.87 kB | 2.87 kB | +0 kB |

No new runtime dependency — `Chart.jsx`'s projected-segment rendering is
pure SVG, reusing the existing polyline/polygon primitives.

### 21.10 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| CBO's own GitHub data mirror (`US-CBO/cbo-data`) exists and is a better source than the task's assumed xlsx-scraping approach | **VERIFIED** — live fetch of its README, schema.json, and three actual vintage CSVs |
| The GitHub mirror's data matches three independently-known facts (122% @ 2024-06, 118% @ 2025-01, ~101%/~120% @ 2026-02) | **VERIFIED** — computed directly from the fetched CSVs, cross-checked against the task file's own stated figures and an independent web search |
| `proj_primary_deficit` (sign-flipped) exactly equals `outlays_total − outlays_net_interest − rev_total` | **VERIFIED** — computed both ways from the same fetched vintage, identical to the dollar |
| Equation #3's terms are entirely CBO's own baseline, nothing extrapolated or fitted | **VERIFIED** — `series.py`'s `interest_rate_to_keep_debt_flat()` reads only `cbo_data` fields, no other inputs |
| Debt/GDP at Dalio's own vintage (June 2024, FY2034) reproduces his stated 122% | **VERIFIED** — 122.4% computed live from the fetched 2024-06 CSV |
| Debt/revenue at the same vintage is close to, but doesn't exactly reproduce, his stated ~700% | **VERIFIED** — 679.3% computed live from the same fetched CSV |
| The CBO-outage fallback path (manual projection row, no equation-#3 row, no projected tail) works correctly | **VERIFIED** — local mock test, simulated outage, all three degradations asserted explicitly |
| Chart.jsx's projected-segment rendering doesn't break existing (non-projected) charts | **VERIFIED** — full existing mock-test suite (all prior rounds' assertions) still passes unchanged |
| No horizontal overflow introduced at 390px width by the three new rows or their equation buttons | **VERIFIED** — scripted Playwright pass, zero overflow across all checked elements |
| The Treasury maturity-profile endpoint is confirmed and working | **NOT VERIFIED — honest open item.** Best-effort probe added (`maturity_profile_probe()`), tries three candidates; this project's dev sandbox cannot reach `api.fiscaldata.treasury.gov` to test which (if any) resolves. Not used to build any shipped row — see `--verify`'s live output for the actual result |

---

## 22. Gold price, automated for real: World Bank Pink Sheet replaces the manual price input (2026-07-22, thirteenth pass)

**What this round covers:** `TASKgoldautomation.md` — the hand-entered gold
price (`data/manual.json`'s `goldPriceManualFallback`, §18) was the only
manual input on a monthly cadence, and the task's framing was blunt: "a
source that updates itself... it should stop firing." Every candidate in
the task's own §§1-5 was retried or probed and the exact result recorded
below, not just asserted from the prior round's prose.

### 22.1 §§1-2 retried: Nasdaq, Stooq still blocked; LBMA's result was a surprise

Retried with a full browser header set (User-Agent, Accept,
Accept-Language) per the task's hypothesis that the earlier failures were
default-`requests` fingerprinting, not IP-based. **Confirmed live in CI**
(`gold.py verify()`'s diagnostic probes, run `29890754964`):

| Source | Result |
|---|---|
| Nasdaq Data Link (`LBMA/GOLD.csv`) | HTTP 403, Incapsula bot-challenge HTML — identical to the unheadered attempt. Headers change nothing |
| Stooq (`xauusd` daily CSV) | HTTP 200 but body is a client-side JS proof-of-work challenge page, not CSV — identical to before |
| LBMA's own feed (`prices.lbma.org.uk/json/gold_pm.json`) | **This one actually returned data** — HTTP 200, real JSON, history back to 1968 — see §22.2 for why it's still not used |

### 22.2 LBMA's feed resolves after all — but its actual freshness is an open question, not re-verified as "blocked"

The retry above surprised the prior round's docstring, which said LBMA's
feed had moved fully behind a licensed portal. It hasn't, at least not
completely — `gold_pm.json` returns HTTP 200 with real JSON, not a
challenge page. **What this round did NOT establish: whether that feed is
current.** `verify()`'s diagnostic probe only logs a 200-character body
preview, and the array is ordered chronologically ascending from 1968 —
so the preview shows only the earliest records, not the latest, and no
claim about the feed's actual freshness can honestly be made from it.
Given a working, confirmed-current source was already in hand (§22.3/
§22.4), this wasn't chased further this round. **Left as an explicit open
item, not asserted either way** — a future round wanting to revisit LBMA
should check the tail of the response, not just that it returns 200.

### 22.3 §3: World Bank Pink Sheet, direct download — the winning primary, with a real bug found and fixed live

Implemented `_worldbank_pink_sheet_gold_monthly()` in `scripts/gold.py`:
downloads the actual "CMO Historical Data" monthly spreadsheet directly
from `thedocs.worldbank.org` (not the annual *forecast* table DBnomics
exposed — see §16) and parses it defensively (searches for a "gold"
column header and `YYYY`M`MM`-labelled date rows, rather than a hardcoded
cell range, since the layout couldn't be confirmed from this project's
dev sandbox — `thedocs.worldbank.org` is proxy-blocked here, same as
`cbo.gov`).

**A live CI run caught a real design flaw, not just a URL guess:** the
first `workflow_dispatch` (run `29890496801`) showed the direct download
parsing *successfully* — 792 months, no exception — but its **latest
observation was frozen at 2025-12, 233 days old**. The World Bank had
quietly rotated its live data to a new document hash
(`.../74e8be41...-0050012026/...`, in place since 2026-02-03, confirmed
via web research) while the *old* hash
(`.../18675f1d...-0050012025/...`) kept resolving 200 and parsing cleanly
forever, just with data that stopped updating. A successful parse was
**not proof of freshness** for this source — the opposite of every other
"if it 404s, that's the signal" source this project has integrated so
far. Because `gold_price_usd_per_oz_labeled()` originally only fell
through to the mirror on an *exception*, this stale-but-successful direct
leg was preferred and shipped — caught only because `fetch.py`'s
independent freshness guard on the *combined* price correctly flagged it
233 days old and forced the fallback to `manual_price` instead of
`live`. The system degraded safely, but for the wrong reason (staleness
caught two layers downstream, not at the source-selection point) and it
skipped a perfectly good, current source (the mirror, §22.4) that was
sitting right there.

**Fixed** (`af3a643` → `ce6c4d6`): `gold_price_usd_per_oz_labeled()` now
checks the direct leg's own latest observation against the Monthly
freshness threshold *before* preferring it over the mirror — a stale
"successful" parse is now treated the same as an exception, so a future
hash rotation degrades automatically instead of silently shipping old
data or needing another manual URL fix. Also updated the hardcoded URL to
the currently-live hash. **Re-run in CI confirmed the fix** (run
`29890754964`): direct download now parses 798 months, latest 2026-06,
51 days old, "ok" — selected as the active leg, matching the mirror
exactly.

### 22.4 §4: GitHub mirror (`datasets/gold-prices`) — the confirmed, live-tested fallback

`datasets/gold-prices` mirrors this *same* World Bank Commodity Markets
data, auto-updated daily via its own GitHub Actions workflow. Confirmed
live directly from this project's own dev sandbox (unlike almost every
other external source this project touches) — `raw.githubusercontent.com`
is reachable even through the restrictive proxy here, the same host
`cbo.py` already relies on. This is what actually shipped in the *first*
CI run (before the §22.3 fix), and correctly serves as the fallback leg
whenever the direct download is missing, broken, or stale.

Other §4 candidates, probed and not used:
- **SNB data portal** (`data.snb.ch`) publishes Switzerland's own gold
  bullion *holdings* — the same kind of series Treasury's `gold_reserve`
  already provides for the US — not a market price benchmark. Scope
  mismatch, not a blocked source.
- **UNCTADstat** — its public site 403s to an out-of-sandbox fetch
  attempt and its documented access pattern is a session-based SDMX
  portal, not a lightweight bulk endpoint. Not pursued once §3/§4's Pink
  Sheet path worked.
- **FX-style "XAU as a currency" APIs** (exchangerate.host, Metals-API,
  GoldAPI.io, Commodities-API, UniRateAPI) — all require a key in their
  free tier as of 2026, despite frequently being described as keyless.
  None actually is.

### 22.5 §5 (keyed source) — not needed

§3/§4 produced a working keyless institutional source (twice over, with a
live-tested fallback). No new API key requested.

### 22.6 §6/§3 units and sanity check

Confirmed **USD per troy ounce** directly from the World Bank spreadsheet
schema (column header text, not inferred) and from the GitHub mirror's
own documented schema (`datapackage.json`: "Gold price in USD per troy
ounce"). Live value: $4,228/oz (2026-06). `reserves_incl_gold_pct_gdp`'s
existing 0.5-15% sanity band (unchanged) passed; the actual shipped value
is 4.9% of GDP, somewhat above the task's own "~$4,000/oz, ~4.1-4.3%"
rough estimate — directionally consistent with gold pricing above that
$4,000 baseline, though the excl.-gold reserves and GDP denominators have
also moved since the task was written, so this is a plausibility check,
not a reproduction of an exact figure.

### 22.7 §7: UI staleness indicator

`MetricRow.jsx`'s `note` field already rendered in the UI (confirmed by
reading the component), but in the same muted gray as any ordinary
explanatory caption — nothing distinguished a "the live source is dead"
warning from "net vs. gross interest" framing text. Every fallback-
staleness note this codebase writes (`fetch.py`'s gold/COFER/manual-
freshness notes) already starts with "⚠" by convention; `MetricRow.jsx`
now renders a note starting with "⚠" in the theme's warning color
(`c.caution`, amber) and bold, reusing that existing convention as the
signal rather than adding a second, parallel "is this stale" field that
could drift out of sync with it. Verified visually: patched a local
`data.json` to simulate the `manual_price` fallback, screenshotted via
Playwright, confirmed the note renders at `rgb(224, 169, 59)` (=
`#E0A93B` = `c.caution`) with `font-weight: 600`, clearly distinct from
the muted gray source line beneath it.

### 22.8 Net effect

`gold_price_usd_per_oz()`'s DBnomics/IMF PCPS implementation (permanently
frozen since 2025-06, §16/§17) is removed outright, not just unused.
`manual_price` should no longer fire for gold under normal operation —
confirmed in production (run `29890754964`): the "Reserves incl. gold
(market)" row shipped `tag: "live"`, `src: "... World Bank (Pink Sheet,
direct), both 2026-06 ..."`, with no provenance-mismatch warning.
`goldPriceManualFallback` stays wired in `fetch.py` as the last-resort
leg if both World Bank paths ever go down together — degrade, don't
break, same convention as every other fallback chain in this project.

### 22.9 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| Nasdaq/Stooq are blocked regardless of request headers | **VERIFIED** — retried with full browser headers in live CI, identical failure mode to the unheadered attempt |
| LBMA's public JSON feed still resolves (not fully behind the licensed portal) | **VERIFIED** — live CI probe returned real historical JSON, HTTP 200, not a challenge page |
| That feed's actual freshness (current vs. stale) | **NOT VERIFIED — honest open item.** The probe's 200-char preview shows only the chronologically-earliest records (array starts at 1968); no claim about its latest observation can honestly be made from this round's evidence |
| The World Bank direct-download URL's hash rotates and the old hash keeps resolving with frozen data | **VERIFIED** — caught live: first CI run parsed 792 months successfully but latest was frozen at 2025-12; confirmed via web research that the World Bank had moved to a new hash in Feb 2026; second CI run with the fix + new URL confirmed current (2026-06) |
| `datasets/gold-prices` (GitHub mirror) is live, current, and reachable even from this project's own dev sandbox | **VERIFIED** — direct fetch from this sandbox during development, and again in both CI runs |
| The freshness-aware direct-vs-mirror selector correctly prefers a stale "successful" direct parse's alternative | **VERIFIED** — unit-level test with a stubbed stale direct response asserts the mirror is chosen instead; a stubbed *fresh* direct response asserts direct is still preferred |
| Gold price units are USD/troy oz, not per-gram or per-kilo | **VERIFIED** — read directly from both sources' own schema/column text, not inferred from magnitude |
| `manual_price` no longer fires for gold under normal operation | **VERIFIED** — live production run, `reserves_to_gdp` shipped `tag: "live"`, no provenance mismatch |
| The UI staleness note is visually distinct, not just present | **VERIFIED** — Playwright screenshot + computed-style check (`rgb(224, 169, 59)`, `font-weight: 600`) against a simulated fallback |

---

## 23. Gold price, round two: a monthly average isn't spot — and a bottleneck neither source fixes (2026-07-22, same day, fourteenth pass)

**What prompted this round:** a manual check on §22's shipped figure (4.9%
of GDP, off a $4,228/oz "June 2026" Pink Sheet price) found actual spot
gold running $4,070-4,083/oz in the days the check was made — a real
~3.5% gap. Two questions, both answered by evidence rather than assumed.

### 23.1 What price and date did §22 actually ship?

Confirmed by reading `public/data.json` at commit `8a92e75` directly:
**$4,228.00/oz, dated 2026-06**, `src: "... World Bank (Pink Sheet,
direct), both 2026-06 ..."`.

**The "~2-month-stale, corresponds to May" framing doesn't hold up exactly
as stated — but the underlying complaint is real.** Cross-referencing
actual daily gold prices for 2026 (web research, not assumed): June opened
near $4,460 (June 1), fell to $4,152 by June 10, and was down to $4,005-
4,015 by June 25-30. A **$4,228 whole-month average is consistent with
that real trajectory** — it's a genuine June average, not a mislabeled May
figure. What IS true, and is the actual problem: an average over a
declining month represents gold's price as of roughly the *middle* of
that window, not "today" — and by the time this was checked (July 21,
spot ~$4,070-4,083, itself a partial rebound off June's ~$4,005 low),
the effective gap between the shipped average and current spot really was
material (~3.5-4%), just not for the "2 months" reason originally guessed.

### 23.2 Is a lagged monthly average the right source for this row? No — switched to LBMA

Added `_lbma_gold_monthly_and_latest()` (`scripts/gold.py`) as the new
primary leg, ahead of the World Bank Pink Sheet: LBMA's own daily PM-fix
feed, the actual published gold benchmark, not a redistributor. Re-probed
per the user's request rather than trusting §22's "still blocked" note:

```
[lbma] https://prices.lbma.org.uk/json/gold_pm.json
  parsed 700 months; latest observation: 2026-07-21 = 4052.3 USD/oz
  freshness: 1d old, 20d threshold, ok
  active leg this run: LBMA (PM fix, direct)
```

§22's "still fully behind a licensed portal" claim was wrong — the public
feed resolves fine; the earlier diagnostic probe just never looked past
its own 200-character preview (which only showed the chronologically-
*earliest* 1968 records), so its actual freshness was genuinely unknown,
not confirmed-stale, at the time. This round fixed the probe function too
(`_probe()` now takes an optional `find` substring checked against the
*full* body, not just the preview — used below for the FX-API check).

**Also re-probed the XAU-as-currency FX APIs**, specifically the
supposedly-keyless tier of exchangerate-api.com
(`open.er-api.com/v6/latest/USD`, the "open access, no key required"
endpoint their own docs distinguish from the paid "Free" tier):
```
[open.er-api.com] -> HTTP 200, real JSON
[open.er-api.com] '"XAU"' present anywhere in full body: False
```
Confirms §22's finding rather than reversing it: XAU is NOT in the
keyless tier, despite third-party summaries claiming otherwise. Ruled out
with evidence, not assumption.

### 23.3 The reserves number moved to 5.1%, not toward 4.1-4.3% — because of a bottleneck the gold price was never going to fix

This is the important finding of this round, and it means the fix above,
while correct and worth keeping, did not accomplish what it looked like it
would. Reading the shipped `history[]` array directly:

| | `asOf` | Q1-2026 (`y: 2026.0`) history point |
|---|---|---|
| Before (WB Pink Sheet, commit `8a92e75`) | `2026-Q1` | `4.888` |
| After (LBMA, commit `89bffc1`) | `2026-Q1` | `5.054` (→ displayed `5.1%`) |

**`asOf` is `2026-Q1` in *both* runs.** `reserves_incl_gold_pct_gdp()`
(`series.py`) takes the most recent quarter where reserves-excl-gold
(`TRESEGUSM052N`), the combined gold value, and GDP *all* have data —
and `TRESEGUSM052N` (IMF/BOP-sourced, its own longer lag documented since
§17) currently tops out at 2026-03. **Whichever gold-price leg is active,
the headline ratio only ever uses that leg's price for the LAST month of
whatever quarter TRESEGUSM052N and GDP can both reach — March 2026, right
now — never June or July**, regardless of how fresh the fetched price
itself is. The `src` string's "price 2026-07" is the leg's own latest
*fetched* observation, shown for transparency about the source, but it is
not necessarily the observation actually used in the headline `value`.

The 4.888 → 5.054 shift is therefore explained by a **real, legitimate
difference between the World Bank's March-2026 monthly average and
LBMA's March-2026 last-trading-day price** — both genuine data points,
just measuring March differently (whole-month average vs. one day) — not
by either source becoming more "spot-like" in the headline number. LBMA
is still the better choice going forward (correct daily cadence, the
actual benchmark, no averaging-window ambiguity), but **its benefit won't
show up in this row's headline until `TRESEGUSM052N`/GDP themselves
advance to a quarter where June or July gold pricing is the relevant
month** — which could be months away, tracking those series' own release
cadence, not gold's.

**Not fixed this round, flagged for the user rather than decided
unilaterally:** whether this row's design should change — e.g., a second,
explicitly-labelled "gold value at current price" figure alongside the
officially-lagged reserves-excl-gold ratio, decoupling gold's freshness
from `TRESEGUSM052N`'s — is a real product decision (it changes what the
headline number *means*, not just which source feeds it) and wasn't made
here.

### 23.4 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| §22's shipped $4,228/oz "June 2026" figure was a mislabeled ~May value | **NOT CONFIRMED — the more precise finding replaces it.** Cross-referenced daily 2026 gold prices; $4,228 is consistent with a genuine June whole-month average given June's real decline from ~$4,460 to ~$4,005-4,015 |
| LBMA's public feed is reachable AND fresh | **VERIFIED** — live CI: latest observation 2026-07-21, 1 day old, well under the 20d threshold now applied to it |
| XAU is absent from exchangerate-api.com's truly-keyless tier | **VERIFIED** — live CI probe of the full response body, not a truncated preview |
| Switching to LBMA moves the headline reserves-incl-gold value toward today's spot | **DISCONFIRMED.** The headline is bottlenecked to `TRESEGUSM052N`/GDP's own latest common quarter (2026-Q1) regardless of gold price source; the observed 4.9%→5.1% shift reflects two sources' differing March-2026 values, not a spot-price effect |

---

## 24. A decoupled "gold at current price" row, so §23's fix actually shows up somewhere (2026-07-22, same day, fifteenth pass)

**What this round covers:** §23 found LBMA's fresher gold price doesn't
reach the "Reserves incl. gold (market)" headline at all — that row is
bottlenecked to `TRESEGUSM052N`/GDP's own latest common quarter
(2026-Q1) regardless of price source, and checking directly confirmed
GDP itself is the binding constraint (FRED's `GDP` series is dated
`2026-01-01`, 202 days old — Q2 2026 GDP hasn't been published yet, not
specific to `TRESEGUSM052N`). Given the user's explicit direction — "have
the figure with the existing and live gold price as a separate number" —
this round adds that second figure rather than changing the existing
row's (correct, if slow) definition.

### 24.1 Design: a dollar figure, not another ratio

New row, "Gold holdings, at current price" (`scripts/fetch.py`, key
`gold_value_current`): live gold troy-oz holdings (Treasury) × the live
gold price (LBMA, or the World Bank Pink Sheet fallback tier — same
`gold_value_monthly` computation the headline row already builds),
taking its own latest overlapping month rather than being intersected
with `TRESEGUSM052N`/GDP at all. **Deliberately a plain dollar figure
($B), not a %-of-GDP ratio** — since GDP itself is the Q1-2026
bottleneck (confirmed above, not assumed), dividing this row's fresh
numerator by GDP would recreate the exact mixed-vintage problem §23
diagnosed, just with an even bigger vintage gap on the denominator side.
Tag mirrors `reserves_incl_gold_tag` (`live` / `manual_price`) since both
rows are built from the identical gold-value computation; the row is
omitted entirely (not given a manual-dollar fallback) if the live ounce
count itself is unavailable, the same precedent
`interest_rate_to_keep_debt_flat` (TASKprojections.md) set for its own
live-only equation-#3 row.

### 24.2 Verified in production

Live `workflow_dispatch` run
(`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29894871465`,
job `88842789540`, committed as `46c168a`) — read directly from the
resulting `public/data.json`:
```json
{
  "label": "Gold holdings, at current price",
  "value": 1052.8, "display": "$1,052.8B",
  "tag": "live", "key": "gold_value_current",
  "src": "derived · Treasury (gold oz 2026-06) + LBMA (PM fix, direct) (price 2026-07)",
  "asOf": "2026-06"
}
```
Note `asOf: "2026-06"` here vs. `"2026-Q1"` on "Reserves incl. gold
(market)" directly above it in the same panel — the two rows' vintages
are now visibly different on the page itself, not just in STATUS.md
prose. `provenance.fallbacksFired` contains only the pre-existing,
unrelated COFER entry — no gold-related fallback fired.

### 24.3 Local + browser verification

Extended the scratchpad mock-test suite: golden-path run asserts the new
row's tag/display/exact value (`round(oz × price / 1e9, 1)`); the
manual-price-input scenario (§18's fallback path) asserts the row
survives tagged `manual_price`; the full-manual-fallback scenario (live
ounce count itself unavailable) asserts the row is **absent** from the
panel entirely. All three pass.

Browser (Playwright): patched a local `data.json` with the row, confirmed
it renders directly below "Reserves incl. gold (market)" with its `$` 
display, `ƒx` equation button (new `equations.js` entry — definition,
"what fills each term" with a LIVE DATA tag, and a caveat explaining why
it's a dollar figure and not a ratio), zero console errors. Patched file
discarded before committing.

### 24.4 Verified vs. assumed — this round's new claims

| Claim | Status |
|---|---|
| GDP itself (not just `TRESEGUSM052N`) is the binding constraint on the 2026-Q1 bottleneck | **VERIFIED** — FRED's `GDP` series confirmed dated `2026-01-01` (202d old) in the CI verify log, independent of `TRESEGUSM052N` |
| The new row is genuinely decoupled and shows a materially fresher `asOf` than the headline row | **VERIFIED** — live production `public/data.json`: `2026-06` vs. `2026-Q1` on the same panel |
| The new row correctly omits itself (not a stale manual fallback) when the live ounce count fails | **VERIFIED** — local mock-test scenario 3 asserts absence |
| No regression to the existing "Reserves incl. gold (market)" row or its equation button | **VERIFIED** — full mock-test suite (every prior round's assertions) still passes; live production value/tag for that row unchanged by this addition |

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
