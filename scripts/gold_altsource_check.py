"""Diagnostic (not shipped): test two keyless alternative gold-price sources
against the DBnomics-mirrored IMF PCPS PGOLD series currently in gold.py,
which is stuck at 2025-06 while spot gold has moved from ~$3,352 (2025-06)
to a ~$5,595 Jan-2026 peak and back down to ~$4,000 today (per the task
that produced this script). Two candidates, in the order the task asked
for:

  1. World Bank "Pink Sheet" monthly commodity prices, via DBnomics (if
     DBnomics mirrors it — provider code likely "WB"). Reuses the working
     DBnomics client pattern from gold.py/imf.py.
  2. Stooq daily CSV for XAUUSD (https://stooq.com/q/d/l/?s=xauusd&i=d),
     no key, plain CSV.

Prints latest observation date + value for each so the source with the
most current data can be picked. Deleted after this round's findings are
copied into STATUS.md / docs/review, per this project's
diagnostic-scripts-are-not-features convention.
"""

import csv
import io

import requests


def _get(url, params=None, tries=2, timeout=20, **kw):
    import time
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=timeout, **kw)
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)
    raise RuntimeError(f"request to {url} failed after {tries} tries: {last}")


# --- 1. World Bank Pink Sheet, via DBnomics ---------------------------------

def check_worldbank_dbnomics():
    print("\n=== 1. World Bank Pink Sheet via DBnomics ===")
    try:
        r = _get("https://api.db.nomics.world/v22/providers")
        js = r.json()
        providers = js.get("providers", {}).get("docs", js.get("providers", []))
        wb_codes = [p.get("code") for p in providers
                    if "world bank" in str(p.get("name", "")).lower()
                    or str(p.get("code", "")).upper() == "WB"]
        print(f"  providers matching 'world bank' or code WB: {wb_codes}")
        all_codes_sample = [p.get("code") for p in providers][:60]
        print(f"  (sample of all provider codes, for context): {all_codes_sample}")
    except Exception as e:  # noqa: BLE001
        print(f"  provider list FAILED: {e}")
        wb_codes = ["WB"]  # try the obvious guess anyway

    try:
        r = _get(f"https://api.db.nomics.world/v22/datasets/WB")
        js = r.json()
        datasets = js.get("datasets", {}).get("docs", [])
        print(f"\n  provider WB: {len(datasets)} datasets")
        hits = [d for d in datasets
                if any(t in str(d.get("name", "")).lower() for t in
                       ("pink sheet", "commodity", "gem", "global economic monitor"))]
        for d in hits:
            print(f"    candidate dataset: {d.get('code')} — {d.get('name')}")
    except Exception as e:  # noqa: BLE001
        print(f"  provider WB dataset list FAILED: {e}")

    # Query the two real dataset codes directly (confirmed to exist from the
    # listing above: "GEM" and "commodity_prices" — "Commodity Prices:
    # History and Projections", the actual Pink-Sheet-shaped one), q=gold
    # only, small limit — no unfiltered fallback dump (a bare dump of GEM
    # timed out this diagnostic's first attempt; not worth retrying broad).
    for ds in ("commodity_prices", "GEM"):
        try:
            r = _get(f"https://api.db.nomics.world/v22/series/WB/{ds}",
                     params={"limit": "40", "observations": "1", "q": "gold"})
            js = r.json()
            docs = js.get("series", {}).get("docs", [])
            print(f"\n  WB/{ds} q=gold -> {len(docs)} series")
            for d in docs[:15]:
                periods = d.get("period", [])
                values = d.get("value", [])
                print(f"    {d.get('series_code')} ({d.get('series_name')}): "
                      f"{len(periods)} obs, latest {periods[-1] if periods else None} = "
                      f"{values[-1] if values else None}")
        except Exception as e:  # noqa: BLE001
            print(f"  WB/{ds} q=gold FAILED: {e}")


# --- 2. Stooq daily CSV for XAUUSD ------------------------------------------

def check_stooq():
    print("\n=== 2. Stooq daily CSV, XAUUSD ===")
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
    # First attempt bare (no UA) to confirm/refute a UA-based 404, then a
    # couple of URL-shape variants in case the endpoint path is off.
    attempts = [
        ("no UA, base url", "https://stooq.com/q/d/l/", {"s": "xauusd", "i": "d"}, {}),
        ("with UA, base url", "https://stooq.com/q/d/l/", {"s": "xauusd", "i": "d"}, headers),
        ("with UA, .csv path", "https://stooq.com/q/d/l/", {"s": "xauusd", "i": "d", "d1": "", "d2": ""}, headers),
        ("with UA, no trailing slash", "https://stooq.com/q/d/l", {"s": "xauusd", "i": "d"}, headers),
    ]
    for label, url, params, hdrs in attempts:
        try:
            r = _get(url, params=params, headers=hdrs, tries=2)
            text = r.text
            print(f"\n  [{label}] GET {r.url}")
            print(f"  status: {r.status_code}, content-type: {r.headers.get('content-type')}")
            print(f"  first 200 chars: {text[:200]!r}")
            rows = list(csv.DictReader(io.StringIO(text)))
            print(f"  {len(rows)} rows parsed")
            if rows:
                print(f"  first row: {rows[0]}")
                print(f"  latest row: {rows[-1]}")
                return  # got usable data, no need to try further variants
        except Exception as e:  # noqa: BLE001
            print(f"\n  [{label}] FAILED: {e}")


if __name__ == "__main__":
    check_worldbank_dbnomics()
    check_stooq()
