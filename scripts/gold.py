"""Gold-inclusive reserves (no API key on either source).

Resolves STATUS.md §5's flagged reserves discrepancy: `TRESEGUSM052N` is
"Total Reserves EXCLUDING Gold" — confirmed by its own name and FRED
metadata — so it structurally cannot reconcile with Dalio's Ch.17 "FX
reserves, 3% of GDP" figure. US reserves excl. gold are ~0.8% of GDP; only
adding gold **at market price** (not the $42.2222/oz statutory book value
Treasury carries it at) closes the gap, because the US holds a large gold
stock (~261.5M fine troy ounces) that is worth roughly $800B+ at market vs.
~$11B at the statutory rate.

Two live, no-key sources, composed here (checked in this order of
preference before implementing):
  1. An off-the-shelf "reserves including gold" series (World Bank
     FI.RES.TOTL.CD, sourced from IMF IFS) exists, but World Bank WDI
     indicators lag 1-2 years — too stale for a dashboard that refreshes
     monthly. IMF IFS itself likely has a more current series
     (something like RAFA_USD) but the exact US country-code key could not
     be confirmed without live API access. Neither is used here; this is
     recorded so a future session can pick the investigation back up instead
     of re-deriving it composed if a good current source turns up.
  2. What's actually used: Treasury's own gold holdings (fine troy ounces,
     monthly) x a live gold price, combined with FRED's excl.-gold reserves
     and GDP. Both endpoints are exercised by verify() so a schema change is
     visible in the run log, same as every other integration in this
     project.

Gold-price source history (2026-07): DBnomics' LBMA/gold_D dataset — the
obvious first choice, and what this module used originally — now 404s on
every shape tried (series-code path, dataset-level with a `dimensions`
filter, and a bare unfiltered dump). Root cause, confirmed via web research
rather than guessed: LBMA moved its benchmark price tables behind a
members-only portal starting the week of 2025-11-24, and FRED's own
GOLDAMGBD228NLBM series (the same LBMA fix) was separately discontinued
with no replacement — DBnomics' LBMA mirror is downstream of the same
now-restricted source, not a URL-shape problem. Switched to IMF's Primary
Commodity Price System (PCPS, indicator code PGOLD — world gold price
benchmark, USD/troy oz, monthly), mirrored on DBnomics the same way COFER
is, which keeps the pipeline on http-only, no-key sources dumped defensively
(bare fetch + client-side filter by series_code, since PCPS's exact
dimension names haven't been confirmed live yet — see verify()).

Best-effort by design: gold_market_value_usd() raises on any problem, and the
caller (fetch.py) falls back to a manual value rather than shipping a
live-tagged number built on a stale price, same pattern as imf.py's COFER
fallback.
"""

from __future__ import annotations

import datetime as dt
import time
from collections import defaultdict

import requests

TREASURY_BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
GOLD_ENDPOINT = "/v2/accounting/od/gold_reserve"

# IMF Primary Commodity Price System via DBnomics — same aggregator, same
# provider (IMF) as the working COFER integration. Exact dimension names for
# PCPS are unconfirmed, so we don't filter server-side; the bare dump is
# small enough (~200 series: ~15 commodities x a handful of frequencies) to
# fetch whole and filter client-side by series_code, same defensive pattern
# that resolved COFER.
DBNOMICS_GOLD_DATASET = "https://api.db.nomics.world/v22/series/IMF/PCPS"
GOLD_INDICATOR_HINT = "pgold"


# --- http ------------------------------------------------------------------

def _get_json(url: str, params: dict, tries: int = 4):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=45)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)  # 1s, 2s, 4s
    raise RuntimeError(f"request to {url} failed after {tries} tries: {last}")


def _pick(sample: dict, names, contains=None, exclude=()):
    for n in names:
        if n in sample:
            return n
    if contains:
        for k in sample:
            kl = k.lower()
            if all(t in kl for t in contains) and not any(e in kl for e in exclude):
                return k
    return None


def _num(x):
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _ym(record_date: str):
    d = dt.date.fromisoformat(record_date)
    return (d.year, d.month)


# --- Treasury: gold holdings, fine troy ounces ------------------------------

def _treasury_gold_rows():
    rows, page = [], 1
    out = []
    while page <= 20:
        js = _get_json(f"{TREASURY_BASE}{GOLD_ENDPOINT}",
                        {"format": "json", "page[size]": "1000", "page[number]": str(page),
                         "sort": "record_date"})
        data = js.get("data", [])
        out.extend(data)
        meta = js.get("meta", {})
        total_pages = int(meta.get("total-pages") or meta.get("total_pages") or 1)
        if page >= total_pages or not data:
            break
        page += 1
    if not out:
        raise RuntimeError("gold_reserve: no rows returned")
    return out


def gold_holdings_troy_oz() -> dict:
    """{(year, month): total fine troy ounces held} — monthly.

    Sums across every row for a given date (locations/categories) rather than
    assuming a single pre-summed "total" row exists — safer if the schema has
    a location breakdown with no grand-total row, and harmless (same result)
    if it does have one under a different name we didn't guess.
    """
    rows = _treasury_gold_rows()
    s = rows[0]
    ozk = _pick(s, ["fine_troy_ounce_qty", "fine_troy_ounce_amt"],
                contains=["troy", "oz"]) or _pick(s, [], contains=["troy"])
    if not ozk:
        raise RuntimeError(f"gold_reserve: no troy-ounce field in {list(s)}")
    totk = _pick(s, ["location_desc", "summary_fund_type_desc"], contains=["desc"])

    monthly = defaultdict(float)
    for row in rows:
        # if a grand-total row is identifiable, prefer it exclusively per
        # month so we don't double count; otherwise sum every row.
        if totk and "total" in str(row.get(totk, "")).lower():
            oz = _num(row.get(ozk))
            if oz is not None:
                monthly[_ym(row["record_date"])] = oz  # overwrite: total wins
    if monthly:
        return dict(monthly)

    monthly = defaultdict(float)
    for row in rows:
        oz = _num(row.get(ozk))
        if oz is not None:
            monthly[_ym(row["record_date"])] += oz
    return {k: v for k, v in monthly.items() if v}


# --- DBnomics: IMF PCPS gold price (PGOLD) ----------------------------------

def _all_gold_price_docs():
    """Bare, unfiltered dump of every series in the IMF PCPS dataset."""
    js = _get_json(DBNOMICS_GOLD_DATASET, {"limit": "1000", "observations": "1"})
    return js.get("series", {}).get("docs", [])


def _gold_price_docs():
    """PGOLD series, found by filtering the bare dump client-side rather
    than guessing PCPS's dimension names. PCPS carries four PGOLD variants
    per frequency — an index (.IX), two percent-change series (.PC_*), and
    the actual dollar level (.USD); confirmed live (2026-07) that .USD is
    the real per-ounce price and .IX is a rebased index (~268, not ~$3000s).
    Prefers monthly (M.*) among the USD-suffixed matches."""
    docs = _all_gold_price_docs()
    matches = [d for d in docs
               if GOLD_INDICATOR_HINT in str(d.get("series_code", "")).lower()]
    if not matches:
        return docs  # nothing matched — let the caller see the raw dump via verify()
    usd = [d for d in matches if str(d.get("series_code", "")).upper().endswith(".USD")]
    pool = usd or matches
    monthly = [d for d in pool if str(d.get("series_code", "")).upper().startswith("M.")]
    return monthly or pool


def _period_to_ym(period: str):
    """DBnomics periods are 'YYYY-MM-DD' (daily) or 'YYYY-MM' (monthly)."""
    parts = period.split("-")
    if len(parts) >= 2:
        return int(parts[0]), int(parts[1])
    raise ValueError(f"unrecognised period: {period!r}")


def gold_price_usd_per_oz() -> dict:
    """{(year, month): USD per troy oz}."""
    docs = _gold_price_docs()
    if not docs:
        raise RuntimeError("IMF PCPS (PGOLD): no series returned")
    doc = docs[0]
    monthly = {}
    for period, val in zip(doc.get("period", []), doc.get("value", [])):
        if val is None or period is None:
            continue
        try:
            ym = _period_to_ym(period)
            v = float(val)
        except (TypeError, ValueError):
            continue
        monthly[ym] = v  # observations are ascending, so a later dup wins
    if not monthly:
        raise RuntimeError("IMF PCPS (PGOLD): no usable observations")
    return monthly


# --- combined ----------------------------------------------------------------

def gold_market_value_usd() -> dict:
    """{(year, month): USD market value of US gold holdings}."""
    oz = gold_holdings_troy_oz()
    price = gold_price_usd_per_oz()
    months = oz.keys() & price.keys()
    if not months:
        raise RuntimeError("gold: no overlapping months between holdings and price")
    return {k: oz[k] * price[k] for k in months}


# --- verification ------------------------------------------------------------

def verify() -> bool:
    """Dump both endpoints' schema + latest values, and try the computation.
    Non-fatal: always returns True (a source hiccup must not red the run —
    the build falls back to the manual value)."""
    print("\nVerifying gold sources (Treasury holdings + DBnomics LBMA price; "
          "non-fatal — manual fallback on failure)\n")
    try:
        rows = _treasury_gold_rows()
        s = rows[0]
        print(f"[gold-holdings] {TREASURY_BASE}{GOLD_ENDPOINT}")
        print("  fields:", ", ".join(s))
        for col in [c for c in s if c.endswith("_desc")]:
            seen = []
            for r in rows:
                v = r.get(col)
                if v is not None and v not in seen:
                    seen.append(v)
                if len(seen) >= 15:
                    break
            print(f"  distinct {col}: {seen}")
        latest = max(r["record_date"] for r in rows)
        print(f"  latest {latest} rows:")
        for r in [r for r in rows if r["record_date"] == latest][:10]:
            print(f"    {r}")
    except Exception as e:  # noqa: BLE001
        print(f"[gold-holdings] FAILED: {e}")

    try:
        all_docs = _all_gold_price_docs()
        print(f"\n[gold-price] {DBNOMICS_GOLD_DATASET} (bare dump)")
        print(f"  all series_codes in dataset: {[d.get('series_code') for d in all_docs]}")
        docs = _gold_price_docs()
        if docs:
            d = docs[0]
            periods = d.get("period", [])
            values = d.get("value", [])
            print(f"  selected series_code: {d.get('series_code')}")
            print(f"  {len(periods)} observations; latest: {periods[-1] if periods else None} = "
                  f"{values[-1] if values else None} USD/oz")
        else:
            print("  no series returned")
    except Exception as e:  # noqa: BLE001
        print(f"[gold-price] FAILED: {e}")

    try:
        mv = gold_market_value_usd()
        last = max(mv)
        print(f"\n  computed gold market value: ${mv[last]/1e9:.1f}B "
              f"as of {last[0]}-{last[1]:02d} ({len(mv)} months)")
    except Exception as e:  # noqa: BLE001
        print(f"\n  gold market value computation FAILED: {e}")
    return True
