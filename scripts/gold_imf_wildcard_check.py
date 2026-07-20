#!/usr/bin/env python3
"""ONE-OFF DIAGNOSTIC — final follow-up. PGOLD is confirmed as the correct
INDICATOR code (found in IMF's own CL_PCPS_COMMODITY codelist, matching
DBnomics' code exactly) and COUNTRY.INDICATOR.DATA_TRANSFORMATION.FREQUENCY
is the DSD's own declared key order, yet W00.PGOLD.USD.M still returns
200-but-empty. Wildcards the COUNTRY and DATA_TRANSFORMATION positions
(leaving them blank, standard SDMX-REST syntax for "all values") to see
whether PGOLD data exists in this dataflow via this API at all, and if so,
what the real valid dimension codes look like — instead of guessing again.
"""

from __future__ import annotations

import requests

BASE = "https://api.imf.org/external/sdmx/3.0"


def query(key, label):
    url = f"{BASE}/data/dataflow/IMF.RES/PCPS/~/{key}"
    r = requests.get(url, params={"c[TIME_PERIOD]": "ge:2024-01"}, timeout=30)
    print(f"\n[{label}] {url}")
    print(f"  status: {r.status_code}")
    if r.status_code != 200:
        print(f"  body: {r.text[:500]}")
        return
    d = r.json()
    data = d.get("data", {})
    structures = data.get("structures", [])
    series_dims = structures[0].get("dimensions", {}).get("series", []) if structures else []
    obs_dims = structures[0].get("dimensions", {}).get("observation", []) if structures else []
    period_values = obs_dims[0].get("values", []) if obs_dims else []
    datasets = data.get("dataSets", [{}])
    series = datasets[0].get("series", {}) if datasets else {}
    print(f"  series dim order: {[sd.get('id') for sd in series_dims]}")
    print(f"  series count: {len(series)}")
    for skey, sval in list(series.items())[:5]:
        obs = sval.get("observations", {})
        periods = sorted(period_values[int(i)]["id"] for i in obs if int(i) < len(period_values))
        print(f"    seriesKey={skey}  n_obs={len(obs)}  periods={periods[:3]}...{periods[-3:] if periods else []}")


def main():
    # Wildcard COUNTRY and DATA_TRANSFORMATION; pin INDICATOR=PGOLD, FREQUENCY=M
    query(".PGOLD..M", "wildcard country+transformation, monthly PGOLD")
    # Also try wildcarding just DATA_TRANSFORMATION, pinning COUNTRY=W00
    query("W00.PGOLD..M", "pin country=W00, wildcard transformation")
    # Also try wildcarding COUNTRY, pinning DATA_TRANSFORMATION=USD
    query(".PGOLD.USD.M", "wildcard country, pin transformation=USD")
    print("\nDone.")


if __name__ == "__main__":
    main()
