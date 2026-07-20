# Verification log, review round `2026-07-20c` — gold alt-source probes, run output

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-20b-verification.md` (round b, base
> commit `688e24a`, the dated-matrix / IMF-direct-gold follow-up). Every
> review pass gets its own new file under `docs/review/` — check
> STATUS.md's "current review-round files" note (top of file) for whichever
> round is actually current when you're reading this.
>
> **Base commit:** `bf0ec51` (HEAD of `claude/new-session-ldotj8` when this
> file was written)
> **Written:** 2026-07-20T08:05:00Z UTC
>
> **No companion `-values.md` this round.** No shipped code changed — both
> candidate sources were tested and rejected before touching `gold.py`;
> `public/data.json` is untouched. `docs/review/2026-07-20a-values.md`
> remains current for headline values.

**What this round answers:** the user flagged that the shipped gold price
isn't just stale, it's now materially wrong — spot gold has run from
~$3,352/oz (2025-06, the shipped DBnomics-mirrored IMF PCPS quote) through
a ~$5,595 Jan-2026 peak and back down to ~$4,000 today, a move the
dashboard's `reserves_incl_gold` row hasn't reflected at all. Asked to try
two specific keyless sources before falling back to "just keep the
staleness note": (1) World Bank "Pink Sheet" monthly commodity prices,
checking whether DBnomics mirrors it; (2) Stooq's daily XAUUSD CSV. If
either is current, switch; if both fail, quantify the error in STATUS.md
rather than leave it as an unquantified "old" flag.

## 1. World Bank Pink Sheet via DBnomics — real dataset found, wrong shape

`scripts/gold_altsource_check.py`, run via a temporary push-triggered
workflow (`followup-check.yml`, same pattern as round b). DBnomics does
carry a World Bank provider (`WB`, 14 datasets), and one of those datasets
is real and gold-relevant:

```
provider WB: 14 datasets
  candidate dataset: GEM — Global Economic Monitor
  candidate dataset: commodity_prices — Commodity Prices: History and Projections

WB/commodity_prices q=gold -> 2 series
  FGOLD-1W (Gold, nominal, $/troy oz – World): 71 obs, latest 2030 = 1100.0
  KFGOLD-1W (Gold, real, $/troy oz – World): 71 obs, latest 2030 = 907.3986282

WB/GEM q=gold -> 0 series
```

`commodity_prices` is real and does contain gold (`FGOLD-1W`) — but it is
**not** the monthly Pink Sheet: it's an **annual** history-and-projections
series, and its "latest" period is **2030**, a *forecast* year (value
$1,100/oz — nowhere near any real gold price this decade, confirming it's
a long-run projected average, not an observation). DBnomics does not
appear to mirror the actual monthly World Bank Pink Sheet CSV under this
provider — only this annual outlook dataset. Not usable as a current
monthly market price under any interpretation of "latest."

**Claim status: VERIFIED (as a negative result)** — the dataset exists and
was queried successfully (not a reachability failure); it's the wrong
periodicity and dominated by out-year projections, not a current price
feed.

## 2. Stooq XAUUSD CSV — blocked by a JS proof-of-work challenge

```
[no UA, base url] FAILED: 404 Client Error: Not Found for url:
  https://stooq.com/q/d/l/?s=xauusd&i=d

[with UA, base url] GET https://stooq.com/q/d/l/?s=xauusd&i=d
  status: 200, content-type: text/html; charset=utf-8
  first 200 chars: '<!DOCTYPE html><html><head><meta charset="utf-8">
  <meta name="robots" content="noindex,nofollow"></head><body><noscript>
  This site requires JavaScript to verify your browser. Please enable
  JavaScript and reload.</noscript><script nonce="...">
  (async()=>{const c="...";...const h=await crypto.subtle.digest("SHA-256",
  e.encode(c+n))...fetch("/__verify",{method:"POST",...})})();</script>'
```

A bare `requests.get` (no `User-Agent`) 404s outright. Adding a
browser-like `User-Agent` gets a `200`, but the body is not the CSV — it's
an anti-bot interstitial that requires executing JavaScript to solve a
SHA-256 proof-of-work challenge and POST the result to `/__verify` before
the real page is served. This is not a URL-shape or header problem a
plain HTTP client can work around; it would require a headless browser (or
deliberately reverse-engineering and automating the challenge, which this
project has no reason to do for a legitimate keyless data source). Stooq
is not usable as a plain-HTTP, no-key CI source as currently protected.

**Claim status: VERIFIED (as a negative result)** — confirmed live, not
guessed: the exact failure mode (JS PoW gate, not a dead endpoint or wrong
symbol) is visible in the response body.

## 3. Magnitude of the current error, computed live

Since neither candidate worked, quantified the actual size of the gap
instead of leaving the staleness note unquantified. `scripts/
gold_error_magnitude_check.py` (needs `FRED_API_KEY`, same secret
`update-data.yml` uses) pulled the real, live `TRESEGUSM052N` (reserves
excl. gold) and `GDP` series from FRED and the real Treasury gold-oz
holdings, then recomputed `reserves_incl_gold_pct_gdp` three ways —
baseline (shipped stale price), at a $4,000/oz current-market estimate
(the figure given in the task), and at the ~$5,595 Jan-2026 peak for
context — substituting the counterfactual price at the same month
(2025-06) the baseline calculation actually uses, holding gold-oz and GDP
fixed, so the comparison isolates exactly the price correction:

```
Fetching live TRESEGUSM052N (reserves excl. gold) and GDP from FRED...
Fetching live Treasury gold holdings (troy oz)...
  latest gold-oz month: 2026-06, 261,498,926 troy oz
Fetching live DBnomics-mirrored IMF PCPS gold price (the shipped, stale source)...
  latest gold-price month: 2025-06 = $3,351.86/oz

=== Baseline: shipped stale price ===
  [shipped, 2025-06 price] reserves_incl_gold_pct_gdp: 3.7% of GDP as of 2025-Q2

=== Counterfactual: current market price substituted at the same month the baseline actually uses (2025-06) ===
  [$4,000/oz market estimate] reserves_incl_gold_pct_gdp: 4.2% of GDP as of 2025-Q2

=== For context only: at the ~Jan-2026 peak price ===
  [$5,595/oz peak estimate] reserves_incl_gold_pct_gdp: 5.6% of GDP as of 2025-Q2

Gap: shipped (3.7%) vs current-market-corrected (4.2%) = +0.5 points of GDP
Underlying gold market-value gap at the same oz holdings: $169.5B ($3,351.86/oz -> $4,000/oz, same 261,498,926 oz)

(For context: gold-oz data itself is current through 2026-06, 261,498,926 oz — the price series is the only stale leg.)
```

(First run of this script crashed with a `KeyError` substituting the
counterfactual price at the gold-*oz* month, 2026-06 — but the shipped
price series has no 2026-06 entry, so that month was never part of the
intersection the baseline itself uses. Fixed by substituting at the price
series' own latest month, 2025-06, instead — see commit history on this
branch for the one-line fix.)

**Claim status: VERIFIED** — live run, real FRED/Treasury/DBnomics data,
not a back-of-envelope estimate from rounded headline percentages. This
independently confirms the task's own ~4.2-4.3%-of-GDP estimate (landed
exactly at 4.2% using its own $4,000/oz figure) and quantifies the gap
precisely: **the shipped `reserves_incl_gold` row currently reads ~0.5
points of GDP low** (3.7% shown vs. ~4.2% at a $4,000/oz current estimate;
would be ~5.6% at January's ~$5,595 peak, for scale on how large the swing
within the stale window has been). See STATUS.md §16 for the disposition.
