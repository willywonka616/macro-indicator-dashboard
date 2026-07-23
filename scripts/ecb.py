"""ECB Data Portal — Eurosystem official reserve assets, via DBnomics
(TASKeuroarea.md).

Source: DBnomics (https://db.nomics.world), mirroring the ECB's `RAS`
dataset ("Official reserve assets and other foreign currency assets",
BPM6-classified, monthly). Reserves are reported gross, incl. gold and
FX; TASKeuroarea.md §3 notes gold is a large share of Eurosystem reserves
so the incl./excl. split matters the same way it does for the US.

**Honest limitation, same as bis.py/eurostat.py**: this dev sandbox
cannot reach db.nomics.world directly, so the exact SDMX series key below
is a best-effort guess from ECB Data Portal documentation, not something
verified live from here. `verify()` dumps whatever the first live CI run
actually returns; `reserves_pct_gdp()` raises cleanly on any mismatch and
the caller falls back to the manual (book) figure, same as every other
best-effort source in this project (bis.py, gold.py's dead legs).
"""

from __future__ import annotations

import time

import requests

DATASET_RAS = "https://api.db.nomics.world/v22/series/ECB/RAS"

# ECB SDMX series keys are FREQ.REF_AREA.ADJUSTMENT.REF_SECTOR.COUNTERPART_SECTOR.
# REFERENCE_ITEM.REF_ITEM_DETAIL.MATURITY_CAT.DATA_TYPE_FM.UNIT_MEASURE... — the
# exact dimension layout for RAS specifically was not confirmed from this
# sandbox. A handful of plausible full keys (total reserve assets, euro
# area, gross, monthly) are tried in order; verify() dumps whichever (if
# any) resolves, and the raw docs it does return, so the real key is
# confirmed from a live job log rather than guessed twice.
_KEY_ATTEMPTS = [
    "M.U2.S1.S1._Z.RES.T._Z.LE.EUR",
    "M.U2.N.RAS.RAS0.TOT.RAS0",
    "M.U2.S121.RES.RAS0.TOT",
]


def _get(url, params=None, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params or {}, timeout=45)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)
    raise RuntimeError(f"DBnomics/ECB request failed after {tries} tries: {last}")


def _mkey(period):
    """DBnomics monthly periods look like '2026-06'."""
    y, m = period.split("-")
    return (int(y), int(m))


def _first_that_resolves():
    last_err = None
    for key in _KEY_ATTEMPTS:
        try:
            js = _get(f"{DATASET_RAS}/{key}", {"observations": "1"})
            docs = js.get("series", {}).get("docs", [])
            if not docs:
                continue
            doc = docs[0]
            out = {}
            for period, val in zip(doc.get("period", []), doc.get("value", [])):
                if val is None or period is None:
                    continue
                try:
                    out[_mkey(period)] = float(val)
                except (TypeError, ValueError):
                    continue
            if out:
                return out, key
        except RuntimeError as e:
            last_err = e
            continue
    raise RuntimeError(f"ECB RAS: no key attempt resolved ({_KEY_ATTEMPTS}): {last_err}")


def reserve_assets_eur() -> dict:
    """{"latest": float (EUR, millions), "asOf": "YYYY-MM", "history": [...]}
    — Eurosystem total official reserve assets. Raises if no attempted key
    resolves; caller falls back to the manual (book) figure."""
    hist, key = _first_that_resolves()
    last = max(hist)
    return {
        "latest": round(hist[last], 1),
        "asOf": f"{last[0]}-{last[1]:02d}",
        "history": [{"y": round(k[0] + (k[1] - 1) / 12.0, 3), "v": round(v, 1)} for k, v in sorted(hist.items())],
        "seriesKey": key,
        "raw": hist,  # {(year, month): value} — for the caller's own quarter-bucketing (fetch.py's build_eur)
    }


def _docs_dump(limit=20):
    """Best-effort schema dump: query the dataset root (no series code) to
    see what dimension values actually exist, for when every _KEY_ATTEMPTS
    guess fails outright."""
    js = _get(DATASET_RAS, {"limit": str(limit), "observations": "0"})
    return js.get("series", {}).get("docs", [])


def verify() -> bool:
    """Dumps whichever key attempt (if any) resolves, plus a raw dataset
    listing if all guesses fail — non-fatal, always returns True."""
    print(f"\n[ECB] {DATASET_RAS}")
    for key in _KEY_ATTEMPTS:
        try:
            js = _get(f"{DATASET_RAS}/{key}", {"observations": "1"})
            docs = js.get("series", {}).get("docs", [])
            print(f"  key={key} -> {len(docs)} series"
                  + (f", latest obs: {list(zip(docs[0].get('period', [])[-3:], docs[0].get('value', [])[-3:]))}"
                     if docs else ""))
        except Exception as e:  # noqa: BLE001
            print(f"  key={key} -> FAILED: {e}")
    try:
        r = reserve_assets_eur()
        print(f"  computed: reserve assets €{r['latest']:,.0f}M as of {r['asOf']} (key={r['seriesKey']})")
    except Exception as e:  # noqa: BLE001
        print(f"  reserve_assets_eur() FAILED (see key attempts above): {e}")
        try:
            docs = _docs_dump()
            print(f"  fallback dataset-root dump ({len(docs)} series, no filter): "
                  f"{[d.get('series_code') for d in docs[:10]]}")
        except Exception as e2:  # noqa: BLE001
            print(f"  dataset-root dump also FAILED: {e2}")
    return True
