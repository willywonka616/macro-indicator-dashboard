"""Diagnostic (not shipped): TASKgoldpricefreshness.md step 1 — find a gold
price source that is actually current. Tries FRED first (search + the two
believed-discontinued LBMA fixings), stops early if a good candidate is
found; otherwise the later steps (Bundesbank via DBnomics, Nasdaq Data
Link, Stooq) are separate scripts run only if this one comes up empty.
Deleted after this round's findings are copied into STATUS.md/docs.
"""

import datetime as dt
import os
import sys
import time

import requests

FRED = "https://api.stlouisfed.org/fred"
TODAY = dt.date.today()


def _key():
    k = os.environ.get("FRED_API_KEY")
    if not k:
        sys.exit("ERROR: FRED_API_KEY not set")
    return k


def fred_get(path, **params):
    params = {"api_key": _key(), "file_type": "json", **params}
    last = None
    for i in range(4):
        try:
            r = requests.get(f"{FRED}/{path}", params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < 3:
                time.sleep(2 ** i)
    raise RuntimeError(f"request to {path} failed after 4 tries: {last}")


def series_latest(series_id):
    meta_js = fred_get("series", series_id=series_id)
    seriess = meta_js.get("seriess") or []
    if not seriess:
        raise RuntimeError("no metadata")
    meta = seriess[0]
    obs_js = fred_get("series/observations", series_id=series_id, sort_order="desc", limit=5)
    obs = [o for o in obs_js.get("observations", []) if o.get("value") not in (".", "", None)]
    latest = obs[0] if obs else None
    return meta, latest


def report(series_id):
    try:
        meta, latest = series_latest(series_id)
        freq = meta.get("frequency_short") or meta.get("frequency", "")
        units = meta.get("units", "")
        title = meta.get("title", "")
        end = meta.get("observation_end", "")
        if latest:
            d = dt.date.fromisoformat(latest["date"])
            age_days = (TODAY - d).days
            print(f"  {series_id:<22} freq={freq:<3} units={units!r:<20} "
                  f"latest_obs={latest['date']} (age {age_days}d) = {latest['value']} "
                  f"| meta.observation_end={end} | {title}")
            return series_id, d, latest["value"], units
        else:
            print(f"  {series_id:<22} FAILED: metadata OK but no non-missing observations "
                  f"(observation_end={end}) | {title}")
            return series_id, None, None, units
    except Exception as e:  # noqa: BLE001
        print(f"  {series_id:<22} FAILED: {e}")
        return series_id, None, None, None


def search_and_list(text, limit=30):
    print(f"\n=== FRED: series/search?search_text={text!r} ===")
    js = fred_get("series/search", search_text=text, limit=limit,
                   order_by="popularity", sort_order="desc")
    seriess = js.get("seriess", [])
    print(f"{len(seriess)} results:")
    for s in seriess:
        sid = s["id"]
        freq = s.get("frequency_short", "")
        units = s.get("units", "")
        end = s.get("observation_end", "")
        title = s.get("title", "")
        print(f"  {sid:<22} freq={freq:<3} units={units!r:<24} end={end:<12} {title}")
    return seriess


def main():
    for text in ("LBMA gold", "gold fixing", "gold spot"):
        search_and_list(text, limit=15)

    js = fred_get("series/search", search_text="gold price", limit=30,
                   order_by="popularity", sort_order="desc")
    seriess = js.get("seriess", [])
    print(f"\n=== FRED: series/search?search_text='gold price' ===")
    print(f"{len(seriess)} results (top 30 by popularity):")
    candidates = []
    for s in seriess:
        sid = s["id"]
        freq = s.get("frequency_short", "")
        units = s.get("units", "")
        end = s.get("observation_end", "")
        title = s.get("title", "")
        print(f"  {sid:<22} freq={freq:<3} units={units!r:<24} end={end:<12} {title}")
        candidates.append(sid)

    print("\n=== Explicitly checking the two believed-discontinued LBMA fixings ===")
    for sid in ("GOLDAMGBD228NLBM", "GOLDPMGBD228NLBM"):
        report(sid)

    print("\n=== Latest-observation check on every search result (top 15) ===")
    results = []
    for sid in candidates[:15]:
        results.append(report(sid))

    print("\n=== Summary: candidates within ~2 months of today ===")
    fresh = [(sid, d, v, u) for sid, d, v, u in results
             if d is not None and (TODAY - d).days <= 62]
    if fresh:
        for sid, d, v, u in fresh:
            print(f"  CANDIDATE: {sid} — {d} ({(TODAY - d).days}d old) = {v} {u}")
    else:
        print("  none of the checked series are within ~2 months of today")


if __name__ == "__main__":
    main()
