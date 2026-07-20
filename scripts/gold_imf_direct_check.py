#!/usr/bin/env python3
"""ONE-OFF DIAGNOSTIC — follow-up to remaining_issues_check.py's gold-staleness
section. That run proved api.imf.org's SDMX 3.0 API is reachable (200s) but
used "+" instead of "~" for the version segment (SDMX-REST 2.x path is
.../data/dataflow/{agency}/{dataflow}/{version}/{key}, "~" = latest version),
so the observation values array came back empty. Corrected here, with proper
parsing of the SDMX-JSON response instead of printing a raw 800-char prefix.
"""

from __future__ import annotations

import json

import requests

URL = "https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.RES/PCPS/~/M.W00.PGOLD.USD"


def main():
    print(f"GET {URL}")
    r = requests.get(URL, params={"c[TIME_PERIOD]": "ge:2024-01"}, timeout=30)
    print(f"status: {r.status_code}")
    if r.status_code != 200:
        print(f"body: {r.text[:2000]}")
        return
    d = r.json()
    data = d.get("data", {})
    structures = data.get("structures", [])
    if not structures:
        print("no structures in response")
        print(json.dumps(d)[:3000])
        return
    obs_dims = structures[0].get("dimensions", {}).get("observation", [])
    period_values = obs_dims[0].get("values", []) if obs_dims else []
    print(f"TIME_PERIOD values in structure: {len(period_values)}")
    if period_values:
        print(f"  first: {period_values[0]}")
        print(f"  last:  {period_values[-1]}")

    datasets = data.get("dataSets", [])
    if not datasets:
        print("no dataSets in response")
        return
    series = datasets[0].get("series", {})
    print(f"series keys: {list(series.keys())}")
    all_points = []
    for skey, sval in series.items():
        obs = sval.get("observations", {})
        for idx_str, obsval in obs.items():
            idx = int(idx_str)
            period = period_values[idx]["id"] if idx < len(period_values) else f"idx{idx}"
            value = obsval[0] if obsval else None
            all_points.append((period, value))
    all_points.sort()
    print(f"\n{len(all_points)} observations parsed:")
    for period, value in all_points:
        print(f"  {period} = {value}")
    if all_points:
        print(f"\nLatest observation via direct IMF API: {all_points[-1]}")

    # also dump the dataflow-level annotations again for the record
    print("\n--- raw response, first 4000 chars (for the record) ---")
    print(r.text[:4000])


if __name__ == "__main__":
    main()
