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
import time

import requests

import series as S

DATASET = "https://api.db.nomics.world/v22/series/IMF/COFER"
# COFER exposes a ready-made percent series: allocated reserves, US dollar,
# share (RaTe, _PT = percent), world, quarterly. Use it directly — no summing.
SHARE_SERIES = "Q.W00.RAXGFXARUSDRT_PT"
# Same series family, euro instead of dollar (TASKeuroarea.md: "World CB
# reserves in EUR", Dalio's Ch.17 EUR-column target 20.0%) — the currency
# code is the only part of the series name that changes, so this is a
# well-grounded guess rather than a blind one, but still unconfirmed from
# this sandbox until a live run's verify() dump proves it out.
SHARE_SERIES_EUR = "Q.W00.RAXGFXAREURRT_PT"


def _get(url, params, tries=3):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=45)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)  # 1s, 2s
    raise RuntimeError(f"DBnomics/COFER request failed after {tries} tries: {last}")


def _docs():
    """All world (W00) quarterly COFER series (for the --verify dump)."""
    params = {
        "observations": "1",
        "dimensions": json.dumps({"FREQ": ["Q"], "REF_AREA": ["W00"]}),
        "limit": "1000",
    }
    js = _get(DATASET, params)
    return js.get("series", {}).get("docs", [])


def _qkey(period):
    # DBnomics quarterly periods look like "1999-Q1" (occasionally "1999Q1").
    p = period.replace("Q", "-Q") if "-Q" not in period and "Q" in period else period
    y, q = p.split("-Q")
    return (int(y), int(q))


def _qdec(k):
    return round(k[0] + (k[1] - 1) / 4.0, 3)


def _cofer_share(series_code: str) -> dict:
    js = _get(f"{DATASET}/{series_code}", {"observations": "1"})
    docs = js.get("series", {}).get("docs", [])
    if not docs:
        raise RuntimeError(f"COFER: {series_code} returned no series — check code via --verify")
    doc = docs[0]

    share = {}
    for period, val in zip(doc.get("period", []), doc.get("value", [])):
        if val is None or period is None:
            continue
        try:
            share[_qkey(period)] = float(val)
        except (TypeError, ValueError):
            continue
    if not share:
        raise RuntimeError(f"COFER: {series_code} has no usable observations")

    last = max(share)
    hist = [{"y": _qdec(k), "v": round(share[k], 1)} for k in sorted(share)]
    return {"latest": round(share[last], 1), "asOf": f"{last[0]}-Q{last[1]}", "history": hist}


def cofer_usd_share():
    """{"latest": float, "asOf": "YYYY-Qn", "history": [{y, v}]} — USD % of
    world allocated reserves, read directly from the COFER percent series."""
    return _cofer_share(SHARE_SERIES)


def cofer_eur_share():
    """Same construction as cofer_usd_share(), euro instead of dollar
    (TASKeuroarea.md) — reuses the identical DBnomics dataset and query
    shape, just SHARE_SERIES_EUR instead of SHARE_SERIES.

    **Confirmed live, 2026-07-23 CI run**: `Q.W00.RAXGFXAREURRT_PT` 404'd
    — the USD->EUR currency-code substitution that works throughout this
    file's own SHARE_SERIES naming pattern isn't how this particular
    percent-share series is actually keyed for EUR. Unconfirmed; caller
    falls back to the manual (book) figure. Worth noting separately: the
    USD share this same run returned 57.7% as of 2025-Q1 — 568 days old,
    past its own freshness threshold — so COFER's DBnomics mirror is
    ALSO currently stale for the row this function's US counterpart
    feeds (a pre-existing issue, STATUS.md §17/§18, not caused by this
    euro-area addition)."""
    return _cofer_share(SHARE_SERIES_EUR)


def verify() -> bool:
    """Dump the COFER series codes DBnomics returns + the computed share.
    Non-fatal: always returns True (a source hiccup must not red the run — the
    build falls back to the manual value)."""
    print("\nVerifying IMF COFER via DBnomics (non-fatal — manual fallback on failure)\n")
    try:
        docs = _docs()
        codes = sorted({d.get("series_code", "") for d in docs})
        print(f"[cofer] {DATASET} (FREQ=Q, REF_AREA=W00)")
        print(f"  {len(docs)} series; codes: {codes[:40]}")
        r = cofer_usd_share()
        f = S.freshness("COFER USD share", r["asOf"], S.COFER_FRESH_DAYS)
        fresh_s = "STALE" if f["stale"] else "ok"
        print(f"  computed USD share: {r['latest']}% as of {r['asOf']} ({len(r['history'])} pts)"
              f" — freshness: {f['age_days']}d old, {S.COFER_FRESH_DAYS}d threshold, {fresh_s}")
    except Exception as e:  # noqa: BLE001
        print(f"[cofer] unavailable — build will use the manual value: {e}")

    # TASKeuroarea.md: EUR share, same series family as USD above.
    try:
        r_eur = cofer_eur_share()
        print(f"  computed EUR share: {r_eur['latest']}% as of {r_eur['asOf']} ({len(r_eur['history'])} pts)")
    except Exception as e:  # noqa: BLE001
        print(f"[cofer] EUR share unavailable — build will use the manual value: {e}")
    return True
