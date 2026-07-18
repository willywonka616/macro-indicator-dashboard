"""IMF COFER — USD share of world *allocated* FX reserves (no API key).

Source: DBnomics (https://db.nomics.world), a free, stable aggregator that
mirrors IMF COFER as simple JSON. IMF's own legacy CompactData host
(dataservices.imf.org) has been decommissioned, and its new SDMX-3.0 API is
awkward to consume; DBnomics exposes the same COFER series reliably.

COFER reports allocated reserves per currency, valued in USD, for the world
(REF_AREA = W00), quarterly. The USD share is computed as

    USD-allocated  /  sum of all currency-allocated components  * 100

using the per-currency amount series (Q.W00.RAXGFXAR<CUR>_USD), so we never
depend on a separate "shares" indicator.

Best-effort by design: cofer_usd_share() RAISES on any problem and the caller
(fetch.py) falls back to the manual value, so a flaky/renamed source never reds
the monthly run. verify() dumps the series codes returned so they can be
confirmed from the first CI run.
"""

from __future__ import annotations

import json
import re
import time

import requests

DBNOMICS = "https://api.db.nomics.world/v22/series/IMF/COFER"
# Per-currency allocated reserves, valued in USD (last dotted segment of the
# DBnomics series_code, e.g. Q.W00.RAXGFXARUS_USD -> RAXGFXARUS_USD).
CUR_RE = re.compile(r"^RAXGFXAR[A-Z]{2,3}_USD$")
USD_IND = "RAXGFXARUS_USD"


def _get(params, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(DBNOMICS, params=params, timeout=45)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)  # 1s, 2s
    raise RuntimeError(f"DBnomics/COFER request failed after {tries} tries: {last}")


def _docs():
    """All world (W00) quarterly COFER series, with observations."""
    params = {
        "observations": "1",
        "dimensions": json.dumps({"FREQ": ["Q"], "REF_AREA": ["W00"]}),
        "limit": "1000",
    }
    js = _get(params)
    return js.get("series", {}).get("docs", [])


def _indicator(doc):
    code = doc.get("series_code", "")
    return code.split(".")[-1] if code else ""


def _qkey(period):
    # DBnomics quarterly periods look like "1999-Q1" (occasionally "1999Q1").
    p = period.replace("Q", "-Q") if "-Q" not in period and "Q" in period else period
    y, q = p.split("-Q")
    return (int(y), int(q))


def _qdec(k):
    return round(k[0] + (k[1] - 1) / 4.0, 3)


def cofer_usd_share():
    """{"latest": float, "asOf": "YYYY-Qn", "history": [{y, v}]} — USD % of
    world allocated reserves."""
    docs = _docs()
    if not docs:
        raise RuntimeError("COFER: no series returned")

    usd, total = {}, {}
    for doc in docs:
        ind = _indicator(doc)
        if not CUR_RE.match(ind):
            continue
        periods = doc.get("period", [])
        values = doc.get("value", [])
        for period, val in zip(periods, values):
            if val is None or period is None:
                continue
            try:
                v = float(val)
            except (TypeError, ValueError):
                continue
            k = _qkey(period)
            total[k] = total.get(k, 0.0) + v
            if ind == USD_IND:
                usd[k] = v

    ks = sorted(k for k in usd.keys() & total.keys() if total[k])
    if not ks:
        raise RuntimeError("COFER: no USD/total overlap — check series codes via --verify")
    share = {k: usd[k] / total[k] * 100.0 for k in ks}
    last = max(share)
    hist = [{"y": _qdec(k), "v": round(share[k], 1)} for k in sorted(share)]
    return {"latest": round(share[last], 1), "asOf": f"{last[0]}-Q{last[1]}", "history": hist}


def verify() -> bool:
    """Dump the COFER series codes DBnomics returns + the computed share.
    Non-fatal: always returns True (a source hiccup must not red the run — the
    build falls back to the manual value)."""
    print("\nVerifying IMF COFER via DBnomics (non-fatal — manual fallback on failure)\n")
    try:
        docs = _docs()
        codes = sorted({d.get("series_code", "") for d in docs})
        print(f"[cofer] {DBNOMICS} (FREQ=Q, REF_AREA=W00)")
        print(f"  {len(docs)} series; codes: {codes[:40]}")
        r = cofer_usd_share()
        print(f"  computed USD share: {r['latest']}% as of {r['asOf']} ({len(r['history'])} pts)")
    except Exception as e:  # noqa: BLE001
        print(f"[cofer] unavailable — build will use the manual value: {e}")
    return True
