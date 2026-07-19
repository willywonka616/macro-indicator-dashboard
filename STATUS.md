# STATUS

Living document. **Update this at the end of every session** — that's the
instruction this file was created under, and it stands going forward. Written
for another AI assistant (or human) picking this up cold, with no memory of
prior sessions and no access to this repo's chat history.

Last updated: **2026-07-18**, by Claude (Sonnet 5), end of the session that
built this project from scratch through to a live, auto-refreshing site.

---

## 1. What's built and working

A live, auto-refreshing dashboard of Ray Dalio's sovereign debt-risk
indicators (*How Countries Go Broke*, Ch. 17), US only so far.

- **Live site:** https://willywonka616.github.io/macro-indicator-dashboard/
- **Repo:** `willywonka616/macro-indicator-dashboard`, public, default branch
  `main` (there is no separate `develop`/feature branch convention — work
  lands on `main` directly in this project).
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

**Current value: ~18% of total receipts**, which lines up with Dalio's "roughly
a fifth of federal revenue" framing. This is presented as **live** data
(`tag: "live"`, `src: "derived · Treasury"`).

**Unverified assumption, flagged not confirmed:** the "interest on public
issues minus GAS" computation is *my* approximation of "net interest to the
public." I have not cross-checked it against any single official published
"net interest" statistic — I inferred the right categories from the
`--verify` schema dump, not from Treasury's own definitions doc. If the
number ever looks wrong, this is the first place to check.

A **sanity band** (`5% ≤ ratio ≤ 40%`) guards the build: if a future schema
change drives the computed ratio outside that range, the build raises and the
site keeps last month's good data rather than shipping garbage.

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
  **Last confirmed successful run** produced the `data.json` currently on
  `main` (commit `65e94e3`, "data: monthly refresh"), with `debt_to_gdp=99%`,
  `debt_service_to_revenue=18%`, `real_rates=0.6%`, `reserves_to_gdp=0.8%`,
  and a live IMF COFER value in the reserve-currency panel.
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
- **Two assumptions flagged above, not re-flagging here** (see §3's Treasury
  "net interest" approximation, and §5's `IEABC` annualization-detection
  branch) — both produce sane-looking output but weren't manually
  cross-checked against an authoritative definition.
- **Debt/GDP now reads "held by the public" (`FYGFGDQ188S`, ~99%), not gross
  debt (`GFDEGDQ188S`, ~123%).** This is a deliberate, user-approved
  deviation from the brief's original candidate ID, not a bug — flagging it
  here only because it's the single biggest number on the page and worth
  double-checking if Dalio's own figures ever seem to disagree.

---

## 8. What's next

In rough priority order, based on what the brief and the user's requests
left open:

1. **Let the monthly cron actually fire once unattended** and confirm it
   behaves the same as the manual `workflow_dispatch` runs did. Nobody has
   observed a real scheduled (non-manual) run yet.
2. **Euro area** (brief's explicit step 8, and the user has referenced it as
   the natural next expansion): new key under `countries` in `data.json`,
   new manual entries in `data/manual.json`, ECB/Eurostat sources in a new
   fetcher module, new commentary in `commentary.js`. **No component changes
   needed** — `src/App.jsx` and everything under `src/components/` are
   already country-agnostic (the country switcher is driven by
   `Object.keys(data.countries)`).
3. **TIC-based holder breakdown** (central bank / domestic / foreign %) —
   explicitly deferred by the brief, still fully static.
4. **Consider automating one more reserve-currency share** if a free source
   turns up — BIS debt-in-USD is the next most plausible candidate (has an
   API, just needs a derivation), trade and equity are probably permanently
   manual without a paid data source.
5. **Re-verify the Treasury "net interest" definition** against an
   authoritative Treasury/CBO source rather than my inferred category split
   (see §3) — low urgency since the output number looks right, but it's an
   assumption, not a confirmed match to a named official statistic.

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
