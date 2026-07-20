"""Diagnostic (not shipped): follow-up on the gold-price source search after
a user correction — the DBnomics "commodity_prices" dataset checked
previously is World Bank's Commodity Markets Outlook (CMO) forecast table
(annual, includes projected years like 2030), NOT the monthly Pink Sheet
(historical commodity prices, incl. gold, published monthly). Distinguishes
the two properly, and tries two sources not attempted before: ECB Data
Portal (direct + DBnomics) and IMF IFS (a dataset distinct from the
already-tried PCPS). Deleted after this round's findings are copied into
STATUS.md/docs.
"""

import time

import requests

DBN = "https://api.db.nomics.world/v22"


def _get(url, params=None, tries=2, timeout=20, **kw):
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


# --- 1. World Bank: full dataset list, then look for the Pink Sheet specifically ---

def check_worldbank_full():
    print("=== 1. World Bank (provider WB) — full dataset list ===")
    r = _get(f"{DBN}/datasets/WB")
    datasets = r.json().get("datasets", {}).get("docs", [])
    print(f"  {len(datasets)} datasets:")
    for d in datasets:
        print(f"    {d.get('code'):<15} {d.get('name')}")

    # "commodity_prices" (Commodity Markets Outlook, annual+projections) is
    # already known and ruled out. Try GEM (Global Economic Monitor) more
    # thoroughly this time -- broader keyword set, and print a raw sample
    # instead of only a 'gold' substring match (naming may differ).
    print("\n  --- WB/GEM: broader keyword search ---")
    for kw in ("gold", "precious", "commodity", "metal", "pink"):
        try:
            r = _get(f"{DBN}/series/WB/GEM", params={"limit": "10", "observations": "1", "q": kw})
            docs = r.json().get("series", {}).get("docs", [])
            print(f"    q={kw!r} -> {len(docs)} series")
            for d in docs[:5]:
                print(f"      {d.get('series_code')} ({d.get('series_name')})")
        except Exception as e:  # noqa: BLE001
            print(f"    q={kw!r} FAILED: {e}")

    print("\n  --- WB/GEM: raw sample (no filter) to see naming convention ---")
    try:
        r = _get(f"{DBN}/series/WB/GEM", params={"limit": "30", "observations": "0"})
        docs = r.json().get("series", {}).get("docs", [])
        print(f"    {len(docs)} series (sample of first 30):")
        for d in docs:
            print(f"      {d.get('series_code')}  {d.get('series_name')}")
    except Exception as e:  # noqa: BLE001
        print(f"    FAILED: {e}")


# --- 2. ECB Data Portal: direct SDMX + DBnomics mirror ---

def check_ecb():
    print("\n=== 2. ECB Data Portal ===")
    # Direct SDMX 2.1 API. Financial market data (FM) dataflow historically
    # carries a gold price series among precious metals / bullion codes.
    candidates = [
        "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.GB.XAU_HP.D",
        "https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.GB.XAU_HP.HSTA",
    ]
    for url in candidates:
        try:
            r = _get(url, params={"format": "jsondata"}, headers={"Accept": "application/json"})
            print(f"  [direct] {url}\n    status={r.status_code} first 300 chars: {r.text[:300]!r}")
        except Exception as e:  # noqa: BLE001
            print(f"  [direct] {url} FAILED: {e}")

    print("\n  --- DBnomics provider ECB: dataset list + gold search ---")
    try:
        r = _get(f"{DBN}/datasets/ECB")
        datasets = r.json().get("datasets", {}).get("docs", [])
        print(f"  provider ECB: {len(datasets)} datasets")
        hits = [d for d in datasets if any(
            t in str(d.get("name", "")).lower() for t in
            ("financial market", "gold", "commodity", "precious", "bullion"))]
        for d in hits[:20]:
            print(f"    candidate: {d.get('code')} — {d.get('name')}")
        if not hits:
            sample = [(d.get("code"), d.get("name")) for d in datasets][:30]
            print(f"    no obvious match; sample: {sample}")
    except Exception as e:  # noqa: BLE001
        print(f"  provider ECB dataset list FAILED: {e}")

    for ds in ("FM",):
        try:
            r = _get(f"{DBN}/series/ECB/{ds}", params={"limit": "20", "observations": "1", "q": "gold"})
            docs = r.json().get("series", {}).get("docs", [])
            print(f"\n  ECB/{ds} q=gold -> {len(docs)} series")
            for d in docs[:10]:
                periods = d.get("period", [])
                values = d.get("value", [])
                print(f"    {d.get('series_code')} ({d.get('series_name')}): "
                      f"{len(periods)} obs, latest {periods[-1] if periods else None} = "
                      f"{values[-1] if values else None}")
        except Exception as e:  # noqa: BLE001
            print(f"  ECB/{ds} q=gold FAILED: {e}")


# --- 3. IMF IFS (distinct from PCPS, already tried) ---

def check_imf_ifs():
    print("\n=== 3. IMF IFS via DBnomics (provider IMF, dataset IFS) ===")
    try:
        r = _get(f"{DBN}/series/IMF/IFS", params={"limit": "20", "observations": "1", "q": "gold"})
        docs = r.json().get("series", {}).get("docs", [])
        print(f"  IMF/IFS q=gold -> {len(docs)} series")
        for d in docs[:15]:
            periods = d.get("period", [])
            values = d.get("value", [])
            print(f"    {d.get('series_code')} ({d.get('series_name')}): "
                  f"{len(periods)} obs, latest {periods[-1] if periods else None} = "
                  f"{values[-1] if values else None}")
    except Exception as e:  # noqa: BLE001
        print(f"  IMF/IFS q=gold FAILED: {e}")

    try:
        r = _get(f"{DBN}/series/IMF/IFS", params={"limit": "20", "observations": "1", "q": "XAU"})
        docs = r.json().get("series", {}).get("docs", [])
        print(f"  IMF/IFS q=XAU -> {len(docs)} series")
        for d in docs[:15]:
            periods = d.get("period", [])
            values = d.get("value", [])
            print(f"    {d.get('series_code')} ({d.get('series_name')}): "
                  f"{len(periods)} obs, latest {periods[-1] if periods else None} = "
                  f"{values[-1] if values else None}")
    except Exception as e:  # noqa: BLE001
        print(f"  IMF/IFS q=XAU FAILED: {e}")


if __name__ == "__main__":
    check_worldbank_full()
    check_ecb()
    check_imf_ifs()
