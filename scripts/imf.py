"""IMF COFER — USD share of world *allocated* FX reserves (no API key).

COFER reports allocated reserves per currency, valued in USD, for the world
(REF_AREA = W00), quarterly. The USD share is computed here as

    USD-allocated  /  sum of all currency-allocated components  * 100

so we don't depend on guessing a separate "shares" indicator code — only the
per-currency amount indicators, which follow RAXGFXAR<CUR>_USD.

The IMF host isn't reachable from the build's dev environment and the data API
is mid-migration, so this is best-effort:
  * cofer_usd_share() RAISES on any problem;
  * the caller (fetch.py) falls back to the manual value, so a flaky or
    retired endpoint never reds the monthly run;
  * verify() dumps the indicators COFER returns so the codes can be confirmed
    or corrected from the first CI run.

Docs: https://data.imf.org/en/Resource-Pages/IMF-API
"""

from __future__ import annotations

import re
import time

import requests

# Legacy CompactData JSON endpoint: FREQ.REF_AREA.INDICATOR (indicator wildcard).
LEGACY = "http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/COFER/Q.W00"

# Per-currency allocated reserves, valued in USD (US, EUR, CNY, JPY, GBP, AUD,
# CAD, CHF, other …). 2–3 letter currency segment.
CUR_RE = re.compile(r"^RAXGFXAR[A-Z]{2,3}_USD$")
USD_IND = "RAXGFXARUS_USD"


def _get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, timeout=45, headers={"Accept": "application/json"})
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)  # 1s, 2s
    raise RuntimeError(f"IMF request failed after {tries} tries: {last}")


def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _series(js):
    return _as_list(js.get("CompactData", {}).get("DataSet", {}).get("Series"))


def _qkey(tp):  # "1999-Q1" -> (1999, 1)
    y, q = tp.split("-Q")
    return (int(y), int(q))


def _qdec(k):
    return round(k[0] + (k[1] - 1) / 4.0, 3)


def cofer_usd_share():
    """{"latest": float, "asOf": "YYYY-Qn", "history": [{y, v}]} — USD % of
    world allocated reserves."""
    series = _series(_get(LEGACY))
    if not series:
        raise RuntimeError("COFER: no series returned")

    usd, total = {}, {}
    for s in series:
        ind = s.get("@INDICATOR", "")
        if not CUR_RE.match(ind):
            continue
        for o in _as_list(s.get("Obs")):
            tp = o.get("@TIME_PERIOD")
            val = o.get("@OBS_VALUE")
            if not tp or val in (None, ""):
                continue
            try:
                v = float(val)
            except ValueError:
                continue
            k = _qkey(tp)
            total[k] = total.get(k, 0.0) + v
            if ind == USD_IND:
                usd[k] = v

    ks = sorted(k for k in usd.keys() & total.keys() if total[k])
    if not ks:
        raise RuntimeError("COFER: no USD/total overlap — check indicator codes via --verify")
    share = {k: usd[k] / total[k] * 100.0 for k in ks}
    last = max(share)
    hist = [{"y": _qdec(k), "v": round(share[k], 1)} for k in sorted(share)]
    return {"latest": round(share[last], 1), "asOf": f"{last[0]}-Q{last[1]}", "history": hist}


def verify() -> bool:
    """Dump COFER's returned indicators + the computed share. Non-fatal: always
    returns True (IMF flakiness must not red the run — the build falls back to
    the manual value)."""
    print("\nVerifying IMF COFER endpoint (non-fatal — manual fallback on failure)\n")
    try:
        series = _series(_get(LEGACY))
        inds = sorted({s.get("@INDICATOR", "") for s in series})
        print(f"[cofer] {LEGACY}")
        print(f"  {len(series)} series; indicators: {inds[:40]}")
        r = cofer_usd_share()
        print(f"  computed USD share: {r['latest']}% as of {r['asOf']} ({len(r['history'])} pts)")
    except Exception as e:  # noqa: BLE001
        print(f"[cofer] unavailable — build will use the manual value: {e}")
    return True
