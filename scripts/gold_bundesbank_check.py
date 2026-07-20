"""Diagnostic (not shipped): TASKgoldpricefreshness.md step 1.3 — check the
Bundesbank time series API (keyless, stable) for a current gold price,
both directly (api.statistiken.bundesbank.de) and via its DBnomics mirror
(provider BUBA). FRED (step 1.1) came up empty — no LBMA/fixing/spot gold
series exist there any more, confirmed by three separate search terms
plus hard 400s on both old fixing IDs. Deleted after this round's findings
are copied into STATUS.md/docs.
"""

import csv
import io
import time

import requests

BBK_DIRECT = "https://api.statistiken.bundesbank.de/rest"
DBN = "https://api.db.nomics.world/v22"


def _get(url, params=None, tries=3, timeout=25, **kw):
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


def check_direct_bundesbank():
    print("=== 1. Bundesbank direct SDMX API — known/likely gold series codes ===")
    # BBK01.WT5511 is the commonly-cited Bundesbank code for "Goldpreis,
    # Feinunze, in US-Dollar" (gold price, fine ounce, in USD) — trying it
    # plus a couple of nearby guesses since the exact code isn't confirmed
    # without live access.
    candidates = ["BBK01.WT5511", "BBK01.WT5510", "BBEX3.D.XAU.EUR.CA.AC.A01"]
    for series_key in candidates:
        url = f"{BBK_DIRECT}/download/{series_key.split('.', 1)[0]}/{series_key.split('.', 1)[1]}"
        try:
            r = _get(url, params={"format": "csv", "lang": "en"})
            text = r.text
            print(f"\n  [{series_key}] GET {r.url}")
            print(f"  status: {r.status_code}, content-type: {r.headers.get('content-type')}")
            print(f"  first 300 chars: {text[:300]!r}")
            rows = list(csv.reader(io.StringIO(text)))
            print(f"  {len(rows)} raw CSV rows; last 3: {rows[-3:] if len(rows) >= 3 else rows}")
        except Exception as e:  # noqa: BLE001
            print(f"\n  [{series_key}] FAILED: {e}")


def check_dbnomics_buba():
    print("\n=== 2. DBnomics provider BUBA (Bundesbank mirror) ===")
    try:
        r = _get(f"{DBN}/datasets/BUBA")
        datasets = r.json().get("datasets", {}).get("docs", [])
        print(f"  provider BUBA: {len(datasets)} datasets")
        hits = [d for d in datasets
                if any(t in str(d.get("name", "")).lower() for t in
                       ("gold", "price", "metal", "precious"))]
        for d in hits[:20]:
            print(f"    candidate dataset: {d.get('code')} — {d.get('name')}")
        if not hits:
            names = [(d.get("code"), d.get("name")) for d in datasets][:30]
            print(f"    no obvious gold/price/metal dataset name; sample: {names}")
    except Exception as e:  # noqa: BLE001
        print(f"  provider BUBA dataset list FAILED: {e}")
        return

    for d in hits[:5]:
        code = d.get("code")
        try:
            r = _get(f"{DBN}/series/BUBA/{code}", params={"limit": "20", "observations": "1", "q": "gold"})
            docs = r.json().get("series", {}).get("docs", [])
            print(f"\n  BUBA/{code} q=gold -> {len(docs)} series")
            for doc in docs[:10]:
                periods = doc.get("period", [])
                values = doc.get("value", [])
                print(f"    {doc.get('series_code')} ({doc.get('series_name')}): "
                      f"{len(periods)} obs, latest {periods[-1] if periods else None} = "
                      f"{values[-1] if values else None}")
        except Exception as e:  # noqa: BLE001
            print(f"  BUBA/{code} q=gold FAILED: {e}")


if __name__ == "__main__":
    check_direct_bundesbank()
    check_dbnomics_buba()
