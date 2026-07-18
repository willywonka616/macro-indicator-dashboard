# Sovereign Debt Vitals

A dashboard of Ray Dalio's sovereign debt-risk indicators (from *How Countries
Go Broke*, Ch. 17), starting with the US and auto-refreshing monthly from public
data.

It reads like a medical chart: the gauges flag **vulnerability, not timing**, and
they cover only the debt/financial slice — not politics, geopolitics, nature or
technology.

**Live site:** https://willywonka616.github.io/macro-indicator-dashboard/
*(after Pages is enabled — see setup below)*

---

## How it works

```
FRED API ─┐
          ├─► scripts/fetch.py ─► public/data.json ─► React app ─► GitHub Pages
manual ───┘        ▲                                     ▲
(data/manual.json) │                                     │
                   └── verify + derive + guard           └── reads data.json,
                                                             no hardcoded figures
```

- **React dashboard** (`src/`) renders entirely from `public/data.json`. No
  numbers are baked into components.
- **`scripts/fetch.py`** pulls FRED series, computes derived metrics, merges the
  non-FRED figures from `data/manual.json`, and writes `public/data.json`
  (including full history for the sparklines).
- **GitHub Actions** runs the fetcher monthly, commits the result, and deploys.

Every metric carries a provenance tag:

| Tag | Meaning |
|---|---|
| **Live data** | Fetched/derived from public sources (FRED, IMF, BIS). |
| **Dalio model** | Proprietary Z-scores from the book's March 2025 snapshot. Not reproducible from public data — carried verbatim, **never recomputed**. |
| **Manual** | Hand-updated figures (USD shares, holder breakdown, CBO projection) with a `lastChecked` date. |

---

## Repo layout

```
public/data.json          generated — the only source of numbers (seeded until CI runs)
src/
  App.jsx                 data-driven page
  components/             ZScale, Sparkline, Tag, MetricRow, GaugeRow, Panel, HeadlineGauge
  content/commentary.js   hand-written interpretation prose (no LLM, not auto-generated)
  theme.js                colour tokens + z/tone scales
scripts/
  series.py               FRED ID registry + derived-metric math
  fetch.py                verify / fetch / build data.json
  requirements.txt
data/manual.json          Dalio model Z-scores + non-FRED figures (with dates)
.github/workflows/
  update-data.yml         monthly fetch + commit
  deploy.yml              build + publish to Pages
```

---

## Setup (one-time)

Steps 1–3 need a browser (the GitHub mobile *app* can't manage secrets or Pages).

1. **FRED API key** — free from https://fredaccount.stlouisfed.org/apikeys.
2. **Add the secret** — repo → Settings → Secrets and variables → Actions →
   New repository secret → name `FRED_API_KEY`.
   Direct: `.../settings/secrets/actions`
3. **Enable Pages** — Settings → Pages → Source: **GitHub Actions**.
   Direct: `.../settings/pages`
4. **Merge to `main`** — workflows and schedules only run from the default
   branch. (If your default branch isn't `main`, update the branch names in the
   two workflow files.)
5. **Run the fetch once** — Actions → **Update data** → Run workflow. The first
   step (`fetch.py --verify`) prints a table of every FRED ID with its resolved
   units/frequency/start; the run goes **red** and names any ID that failed.
6. **Watch it deploy** — once `data.json` is committed, **Deploy to Pages** runs
   and publishes the site.

> ⚠️ **FRED IDs are unverified until step 5.** The candidate IDs in
> `scripts/series.py` came from the brief (from memory) and some may be renamed
> or discontinued. `--verify` is the check — read its output on the first run
> and fix any misses (it suggests replacements via FRED search).

---

## Local development

```bash
npm install
npm run dev            # http://localhost:5173  (uses the committed data.json)
npm run build          # production build to dist/ (base /macro-indicator-dashboard/)

# fetcher (needs a key; FRED must be reachable from your network)
export FRED_API_KEY=xxxx
python scripts/fetch.py --verify     # check IDs
python scripts/fetch.py              # rebuild public/data.json
```

---

## Adding a country

The components are country-agnostic. To add one (e.g. the euro area):

1. Add its key under `data/manual.json` (model gauges, shares, dates).
2. Add a builder in `scripts/fetch.py` for its live series (ECB/Eurostat), and
   register any new series IDs in `scripts/series.py`.
3. Add its narrative to `src/content/commentary.js`.

No component changes needed — the country selector is driven by the keys in
`data.json`.

---

## Data notes & caveats

- **Sparklines** show real historical series at native frequency (downsampled to
  quarterly for display); model gauges and short-history shares carry none.
- **Current account / GDP** is a 3-year trailing average; the fetcher annualises
  the quarterly flow unless FRED reports the series as already annualised
  (`--verify` shows the units so this can be confirmed).
- **Dalio's Z-score gauges are model output, not live data.** There is no public
  series behind them; they change only when he republishes. A fabricated Z-score
  would be worse than none.
- These gauges signal vulnerability, not timing, and cover only the
  debt/financial picture.

Source: Ray Dalio, *How Countries Go Broke: The Big Cycle*, Ch. 17 (snapshot
March 2025). Z-score convention: **up = more vulnerable; +2 and above is "quite
bad".**
