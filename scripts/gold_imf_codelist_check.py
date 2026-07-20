#!/usr/bin/env python3
"""ONE-OFF DIAGNOSTIC — find IMF PCPS's actual INDICATOR code for gold by
reading its own codelist (not guessing "PGOLD" again), then query data with
the discovered code and report the latest observation date, compared
directly against DBnomics' mirror.

Not part of the build. Answers TASKremainingissues-followup item 2 with an
actual data point instead of dataflow-level metadata.
"""

from __future__ import annotations

import json

import requests

import gold as G

BASE = "https://api.imf.org/external/sdmx/3.0"


def _get(url, params=None, timeout=30):
    r = requests.get(url, params=params or {}, timeout=timeout)
    return r


def find_gold_codes(obj, path=""):
    """Recursively search a decoded SDMX-JSON structure response for any
    codelist entry whose id/name mentions gold."""
    hits = []
    if isinstance(obj, dict):
        ident = str(obj.get("id", ""))
        name = ""
        if isinstance(obj.get("name"), str):
            name = obj["name"]
        elif isinstance(obj.get("names"), dict):
            name = obj["names"].get("en", "")
        if "gold" in ident.lower() or "gold" in name.lower():
            hits.append((path, ident, name))
        for k, v in obj.items():
            hits.extend(find_gold_codes(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(find_gold_codes(v, f"{path}[{i}]"))
    return hits


def main():
    print("--- Step 1: fetch PCPS's DSD with referenced codelists ---")
    r = _get(f"{BASE}/structure/datastructure/IMF.RES/DSD_PCPS/~", {"references": "all"})
    print(f"status: {r.status_code}")
    codes = []
    if r.status_code == 200:
        d = r.json()
        codes = find_gold_codes(d)
        print(f"{len(codes)} gold-related entries found in the DSD+codelists response:")
        for path, ident, name in codes[:30]:
            print(f"  id={ident!r} name={name!r} at {path}")
    else:
        print(f"body: {r.text[:1000]}")

    print("\n--- Step 2: also try the codelist endpoint directly (INDICATOR list) ---")
    # PCPS's INDICATOR codelist is very likely named CL_INDICATOR or similar
    # under IMF.RES; try the generic "all codelists for this agency" probe.
    r2 = _get(f"{BASE}/structure/codelist/IMF.RES", {"references": "none"})
    print(f"status: {r2.status_code}")
    if r2.status_code == 200:
        d2 = r2.json()
        cls = d2.get("data", {}).get("codelists", [])
        print(f"{len(cls)} codelists owned by IMF.RES; names containing 'INDIC' or 'COMM':")
        for cl in cls:
            cid = cl.get("id", "")
            if "INDIC" in cid.upper() or "COMM" in cid.upper():
                print(f"  {cid}  (version {cl.get('version')})")
    else:
        print(f"body: {r2.text[:500]}")

    print("\n--- Step 3: query data with every candidate gold code found ---")
    candidates = sorted({ident for _, ident, _ in codes if ident})
    if not candidates:
        print("no candidate codes discovered from the codelist search; falling back to")
        print("a short manual list, in case the codelist search itself missed them")
        candidates = ["PGOLD", "GOLD", "PGOLD_USD"]

    found_any = False
    for code in candidates:
        url = f"{BASE}/data/dataflow/IMF.RES/PCPS/~/W00.{code}.USD.M"
        r3 = _get(url, {"c[TIME_PERIOD]": "ge:2024-01"})
        status = r3.status_code
        n_obs = 0
        latest = None
        if status == 200:
            try:
                d3 = r3.json()
                data = d3.get("data", {})
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
                    found_any = True
            except Exception as e:  # noqa: BLE001
                print(f"  {code}: parse error {e}")
        print(f"  key W00.{code}.USD.M -> status={status} obs={n_obs} latest={latest}")

    print("\n--- Step 4: DBnomics mirror latest, for direct comparison ---")
    try:
        price = G.gold_price_usd_per_oz()
        last = max(price)
        print(f"  DBnomics latest: {last[0]}-{last[1]:02d} = {price[last]} USD/oz")
    except Exception as e:  # noqa: BLE001
        print(f"  DBnomics FAILED: {e}")

    if not found_any:
        print("\nNo candidate key returned actual observations. Could not determine")
        print("IMF's own PGOLD latest date directly via the SDMX 3.0 API this pass.")

    print("\nDone.")


if __name__ == "__main__":
    main()
