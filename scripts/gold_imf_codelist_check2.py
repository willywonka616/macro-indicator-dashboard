#!/usr/bin/env python3
"""ONE-OFF DIAGNOSTIC — follow-up to gold_imf_codelist_check.py. That run's
generic gold-keyword search hit 31 unrelated codelists (BOP/company/currency
codes sharing IMF's SDMX code-list repository) instead of PCPS's own
INDICATOR codelist, which it also found by name: CL_PCPS_INDICATOR (v3.0.0),
alongside CL_PCPS_COMMODITY (v1.0.0). Every "gold" guess queried against the
wrong codelist's codes, hence 200-but-empty every time. This queries those
two PCPS-specific codelists directly.
"""

from __future__ import annotations

import requests

import gold as G

BASE = "https://api.imf.org/external/sdmx/3.0"


def dump_codelist(agency, cl_id, version):
    url = f"{BASE}/structure/codelist/{agency}/{cl_id}/{version}"
    r = requests.get(url, timeout=30)
    print(f"\n{cl_id} ({version}): status={r.status_code}")
    if r.status_code != 200:
        print(f"  body: {r.text[:500]}")
        return []
    d = r.json()
    cls = d.get("data", {}).get("codelists", [])
    if not cls:
        print("  no codelists in response")
        return []
    codes = cls[0].get("codes", [])
    print(f"  {len(codes)} codes total")
    for c in codes:
        cid = c.get("id", "")
        name = c.get("name", "")
        if not isinstance(name, str):
            name = c.get("names", {}).get("en", "") if isinstance(c.get("names"), dict) else ""
        print(f"    {cid:<20} {name}")
    return [c.get("id", "") for c in codes]


def try_query(indicator_code, freq="M", unit="USD"):
    url = f"{BASE}/data/dataflow/IMF.RES/PCPS/~/W00.{indicator_code}.{unit}.{freq}"
    r = requests.get(url, params={"c[TIME_PERIOD]": "ge:2024-01"}, timeout=30)
    n_obs, latest = 0, None
    if r.status_code == 200:
        d = r.json()
        data = d.get("data", {})
        structures = data.get("structures", [])
        obs_dims = structures[0].get("dimensions", {}).get("observation", []) if structures else []
        period_values = obs_dims[0].get("values", []) if obs_dims else []
        series = data.get("dataSets", [{}])[0].get("series", {})
        points = []
        for skey, sval in series.items():
            for idx_str in sval.get("observations", {}):
                idx = int(idx_str)
                if idx < len(period_values):
                    points.append(period_values[idx]["id"])
        n_obs = len(points)
        if points:
            latest = max(points)
    print(f"  W00.{indicator_code}.{unit}.{freq} -> status={r.status_code} obs={n_obs} latest={latest}")
    return latest


def main():
    indicator_codes = dump_codelist("IMF.RES", "CL_PCPS_INDICATOR", "3.0.0")
    commodity_codes = dump_codelist("IMF.RES", "CL_PCPS_COMMODITY", "1.0.0")

    gold_candidates = [c for c in (indicator_codes + commodity_codes)
                        if "GOLD" in c.upper() or c.upper() == "PGOLD"]
    print(f"\nGold-looking candidates from PCPS's own codelists: {gold_candidates}")

    print("\n--- querying data with each real candidate ---")
    best = None
    for code in gold_candidates or indicator_codes:
        latest = try_query(code)
        if latest and (best is None or latest > best[1]):
            best = (code, latest)

    print("\n--- DBnomics mirror latest, for direct comparison ---")
    try:
        price = G.gold_price_usd_per_oz()
        last = max(price)
        print(f"  DBnomics latest: {last[0]}-{last[1]:02d} = {price[last]} USD/oz")
    except Exception as e:  # noqa: BLE001
        print(f"  DBnomics FAILED: {e}")

    if best:
        print(f"\nBEST DIRECT-IMF RESULT: indicator={best[0]} latest={best[1]}")
    else:
        print("\nNo indicator code returned observations for gold.")

    print("\nDone.")


if __name__ == "__main__":
    main()
