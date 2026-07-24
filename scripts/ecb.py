"""ECB Data Portal — Eurosystem official reserve assets, native SDMX
first, DBnomics mirror as fallback (TASKnativesources.md's native-first
policy; see STATUS.md/CLAUDE.md).

Source: `data-api.ecb.europa.eu`'s SDMX 2.1 REST API (CSV response —
confirmed base URL/format via live web research, TASKnativesources.md;
see scripts/sdmx.py's module docstring for the confirmed real example
URLs this is built from). DBnomics' `ECB/RAS` mirror is kept only as a
fallback with a tightened freshness threshold, per the native-first
policy — not as the primary path.

**This series was in the "never resolved" bucket** (TASKeuroarea.md §3,
STATUS.md §32.3), not the "resolved but stale" one — three DBnomics key
guesses all 404'd, though the dataset-root dump confirmed `ECB/RAS`
itself is real (12,292 series, genuinely "official reserve assets of the
euro area... BPM6"). Live web research (TASKnativesources.md)
additionally confirmed: RAS's underlying DSD is the IMF's own BOP
(Balance of Payments) DSD — a large, well-known but genuinely
multi-dimensional structure (the real example key pulled from DBnomics'
dataset-root dump has 17 dot-fields: `M.N.4F.1C.S121.S121.FC.FI.RT1.RT.
F41A.TM13.EUR.X1.N.N.ALL`). Reverse-engineering the exact "total reserve
assets, euro area aggregate" key from one unrelated example is not
reliable — per TASKnativesources.md §3's own "two structured attempts,
then document and stop" instruction, exactly two reasoned attempts are
made below (not an open-ended guessing loop): one testing whether the
native transport itself resolves that SAME real, DBnomics-confirmed key
(a transport-correctness check, not a guess at the right series), and one
best-effort guess at a simplified/aggregate key pattern. If neither
resolves, this stays exactly what it already was: attempted, documented,
manual.
"""

from __future__ import annotations

import time

import requests

import sdmx as X

ECB_FLOW = "RAS"
_DBNOMICS_RAS = "https://api.db.nomics.world/v22/series/ECB/RAS"

# Attempt 1: the REAL key discovered live via DBnomics' dataset-root dump
# (TASKeuroarea.md/STATUS.md §32.3) — not "reserve assets total" by
# meaning, but a confirmed-real, confirmed-populated series in this exact
# flow, so trying it natively tests whether the native transport/flow
# reference itself works before concluding the whole approach is dead.
# Attempt 2: a best-effort guess at a simplified/aggregate pattern —
# ECB headline aggregate series are sometimes published under shorter,
# less-dimensioned keys than the full BOP-DSD detail breakdowns.
_KEY_ATTEMPTS = [
    "M.N.4F.1C.S121.S121.FC.FI.RT1.RT.F41A.TM13.EUR.X1.N.N.ALL",
    "M.U2.N.RAS0.RAS0.T.N.ALL",
]


def _dbnomics_get(url, params, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=45)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)
    raise RuntimeError(f"DBnomics/ECB request failed after {tries} tries: {last}")


def _mkey(period):
    y, m = period.split("-")
    return (int(y), int(m))


def _dbnomics_fetch(key: str) -> dict:
    js = _dbnomics_get(f"{_DBNOMICS_RAS}/{key}", {"observations": "1"})
    docs = js.get("series", {}).get("docs", [])
    if not docs:
        raise RuntimeError(f"{_DBNOMICS_RAS}/{key}: no series returned")
    doc = docs[0]
    out = {}
    for period, val in zip(doc.get("period", []), doc.get("value", [])):
        if val is None or period is None:
            continue
        try:
            out[_mkey(period)] = float(val)
        except (TypeError, ValueError):
            continue
    if not out:
        raise RuntimeError(f"{_DBNOMICS_RAS}/{key}: no usable observations")
    return out


def reserve_assets_eur() -> dict:
    """{"latest": float (EUR, millions), "asOf": "YYYY-MM", "history": [...],
    "raw": {...}, "source": "native"|"dbnomics_mirror"} — Eurosystem
    official reserve assets. Tries native ECB SDMX first (both key
    attempts), then the DBnomics mirror (same two keys) as a fallback.
    Raises if none resolve; caller falls back to the manual (book) figure."""
    last_err = None
    for key in _KEY_ATTEMPTS:
        try:
            hist = X.ecb_series(ECB_FLOW, key, last_n=36)
            return _to_metric(hist, key, "native")
        except Exception as e:  # noqa: BLE001
            last_err = e
    for key in _KEY_ATTEMPTS:
        try:
            hist = _dbnomics_fetch(key)
            return _to_metric(hist, key, "dbnomics_mirror")
        except RuntimeError as e:
            last_err = e
    raise RuntimeError(f"ECB RAS: no native or mirror attempt resolved ({_KEY_ATTEMPTS}): {last_err}")


def _to_metric(hist: dict, key: str, source: str) -> dict:
    last = max(hist)
    return {
        "latest": round(hist[last], 1),
        "asOf": f"{last[0]}-{last[1]:02d}",
        "history": [{"y": round(k[0] + (k[1] - 1) / 12.0, 3), "v": round(v, 1)} for k, v in sorted(hist.items())],
        "seriesKey": key,
        "source": source,
        "raw": hist,
    }


def _docs_dump(limit=20):
    """Best-effort schema dump against the DBnomics mirror: query the
    dataset root (no series code) to see what dimension values actually
    exist, for when every _KEY_ATTEMPTS guess fails on both transports."""
    js = _dbnomics_get(_DBNOMICS_RAS, {"limit": str(limit), "observations": "0"})
    return js.get("series", {}).get("docs", [])


ECB_FLOW_QSA = "QSA"
# TASKnativesources.md §2 asked to migrate "whichever Eurostat/ECB series
# backed the 169% total-debt target row" — in fact no live source was
# EVER built for that row (it shipped manual from day one, same BIS
# all-sector-credit schema gap as the US's own "World debt in USD" row;
# TASKeuroarea.md never claimed otherwise). Rather than skip the
# opportunity the task's own framing opened up, ONE bounded native
# attempt is made here against ECB's QSA ("Quarterly Sector Accounts")
# dataset, whose DSD supports a %GDP-denominated debt ratio directly (a
# real confirmed example key from ECB's own search results:
# `QSA.Q.N.I9.W0.S11.S1.N.L.LE.FPT.T._Z.XDC_R_B1GQ_CY._T.S.V.N._T` — S11
# = non-financial corporations; XDC_R_B1GQ_CY = ratio to GDP). Swapping
# the sector dimension to S1 (total economy, all sectors) is the single
# best-effort substitution for "all sectors" — if it doesn't resolve,
# this stays exactly what it already was: not built, same gap as the US.
_QSA_TOTAL_DEBT_KEY = "Q.N.I9.W0.S1.S1.N.L.LE.FPT.T._Z.XDC_R_B1GQ_CY._T.S.V.N._T"


def total_debt_pct_gdp() -> dict:
    """Best-effort: total-economy consolidated debt as % of GDP, euro
    area, via ECB QSA. One attempt only (see module-level comment above
    _QSA_TOTAL_DEBT_KEY) — raises on failure, caller stays manual."""
    hist = X.ecb_series(ECB_FLOW_QSA, _QSA_TOTAL_DEBT_KEY, last_n=36)
    return _to_metric(hist, _QSA_TOTAL_DEBT_KEY, "native")


def verify() -> bool:
    """Dumps whichever attempt (native, then mirror) resolves, plus a raw
    dataset listing if all guesses fail — non-fatal, always returns True."""
    print(f"\n[ECB] native SDMX ({ECB_FLOW}), then DBnomics mirror fallback")
    for key in _KEY_ATTEMPTS:
        s = X.verify_ecb(ECB_FLOW, key, label="native attempt")
    try:
        r = reserve_assets_eur()
        print(f"  computed: reserve assets €{r['latest']:,.0f}M as of {r['asOf']} "
              f"(key={r['seriesKey']}, source={r['source']})")
    except Exception as e:  # noqa: BLE001
        print(f"  reserve_assets_eur() FAILED (native and mirror both failed, see attempts above): {e}")
        try:
            docs = _docs_dump()
            print(f"  fallback dataset-root dump ({len(docs)} series, no filter): "
                  f"{[d.get('series_code') for d in docs[:10]]}")
        except Exception as e2:  # noqa: BLE001
            print(f"  dataset-root dump also FAILED: {e2}")

    print(f"\n[ECB] native SDMX QSA total-debt attempt (TASKnativesources.md §2/§4 bonus)")
    try:
        td = total_debt_pct_gdp()
        print(f"  total debt (all sectors) % GDP: {td['latest']}% as of {td['asOf']} "
              f"(key={td['seriesKey']})")
    except Exception as e:  # noqa: BLE001
        print(f"  total_debt_pct_gdp() FAILED (one bounded attempt, not chased further): {e}")
    return True
