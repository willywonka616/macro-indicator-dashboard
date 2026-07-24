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

# --- native IMF SDMX attempts (TASKnativesources.md §1/§3) -----------------
#
# IMF's own API access has moved repeatedly and is documented (this
# module's own original docstring, and this project's gold.py) as
# genuinely unstable: dataservices.imf.org (legacy CompactData) is
# decommissioned; a prior probe for gold price data (PGOLD) against an
# IMF SDMX endpoint returned HTTP 200 with ZERO series — a worse failure
# mode than a clean 404, since it looks superficially like success.
# TASKnativesources.md §1's own instruction, given that history: "if
# IMF-native COFER also comes back empty after two structured attempts,
# keep the current manual-dated COFER and stop" — exactly two base-URL
# candidates are tried below, not an open-ended search.
_IMF_SDMX3_BASE = "https://api.imf.org/external/sdmx/3.0"  # current, per live web research
_IMF_SDMX21_BASE = "https://sdmxcentral.imf.org/ws/public/sdmxapi/rest"  # legacy, well-documented shape
COFER_DATAFLOW = "COFER"

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


def _get_raw(url, params, headers=None, tries=2):
    """Like _get(), but returns the raw requests.Response (not .json()) —
    native IMF probes need to distinguish 'HTTP 200 with zero series'
    (the documented PGOLD failure mode) from a clean network failure,
    which requires inspecting the body, not just catching an exception.
    Only 2 tries (not 3) — TASKnativesources.md §3's "two structured
    attempts" budget applies to the whole native-COFER effort, not per
    retry layer on top of that."""
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=headers or {}, timeout=30)
            return r
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                time.sleep(1)
    raise RuntimeError(f"IMF native request to {url} failed after {tries} tries: {last}")


def _cofer_native_sdmx3(currency_code: str) -> dict:
    """Attempt 1: api.imf.org's current SDMX 3.0 endpoint."""
    url = f"{_IMF_SDMX3_BASE}/data/dataflow/IMF/{COFER_DATAFLOW}/1.0/Q.W00.RAXGFXAR{currency_code}RT_PT"
    r = _get_raw(url, {"format": "json"})
    if r.status_code != 200:
        raise RuntimeError(f"IMF SDMX 3.0 native ({currency_code}): HTTP {r.status_code}")
    try:
        js = r.json()
    except ValueError:
        raise RuntimeError(f"IMF SDMX 3.0 native ({currency_code}): HTTP 200 but not valid JSON "
                            f"(first 200 chars: {r.text[:200]!r})")
    # The documented PGOLD failure mode: HTTP 200, syntactically valid,
    # but zero observations — must be checked explicitly, not assumed
    # absent just because the request itself didn't raise.
    obs = _dig_sdmx3_observations(js)
    if not obs:
        raise RuntimeError(f"IMF SDMX 3.0 native ({currency_code}): HTTP 200, 0 series/observations "
                            f"— same 'looks like success, isn't' failure mode as the earlier PGOLD probe")
    return obs


def _dig_sdmx3_observations(js: dict) -> dict:
    """Best-effort walk of an SDMX-JSON 3.0-shaped response for COFER's
    quarterly percent series -> {(year,quarter): value}. Returns {} (not
    an exception) if the shape doesn't match what's expected, so the
    caller's own explicit empty-check produces the right error message."""
    try:
        datasets = js.get("data", {}).get("dataSets", [])
        structure = js.get("data", {}).get("structures", [{}])[0]
        time_dim = next((d for d in structure.get("dimensions", {}).get("observation", [])
                          if d.get("id") == "TIME_PERIOD"), None)
        if not datasets or not time_dim:
            return {}
        periods = [v.get("id") for v in time_dim.get("values", [])]
        out = {}
        for series in datasets[0].get("series", {}).values():
            for idx, obs in series.get("observations", {}).items():
                i = int(idx)
                if i >= len(periods):
                    continue
                try:
                    tkey = _qkey(periods[i])
                except (ValueError, IndexError):
                    continue
                val = obs[0] if isinstance(obs, list) and obs else None
                if val is not None:
                    out[tkey] = float(val)
        return out
    except (AttributeError, TypeError, KeyError, IndexError, ValueError):
        return {}


def _cofer_native_sdmx21(currency_code: str) -> dict:
    """Attempt 2: sdmxcentral.imf.org's legacy SDMX 2.1 REST endpoint."""
    url = f"{_IMF_SDMX21_BASE}/data/IMF,{COFER_DATAFLOW},1.0/Q.W00.RAXGFXAR{currency_code}RT_PT/all"
    r = _get_raw(url, {"format": "sdmx-json"})
    if r.status_code != 200:
        raise RuntimeError(f"IMF SDMX 2.1 native ({currency_code}): HTTP {r.status_code}")
    try:
        js = r.json()
    except ValueError:
        raise RuntimeError(f"IMF SDMX 2.1 native ({currency_code}): HTTP 200 but not valid JSON "
                            f"(first 200 chars: {r.text[:200]!r})")
    obs = _dig_sdmx3_observations(js)  # SDMX-JSON 2.1's dataSets/series shape is close enough to reuse
    if not obs:
        raise RuntimeError(f"IMF SDMX 2.1 native ({currency_code}): HTTP 200, 0 series/observations "
                            f"— same 'looks like success, isn't' failure mode as the earlier PGOLD probe")
    return obs


def _cofer_native(currency_code: str) -> dict:
    """Exactly two structured attempts (TASKnativesources.md §3), then
    raise — no further guessing. Both hit the exact same documented
    failure mode this module's own module-level comment already expects."""
    errors = []
    for attempt_fn, label in ((_cofer_native_sdmx3, "SDMX 3.0 (api.imf.org)"),
                               (_cofer_native_sdmx21, "SDMX 2.1 (sdmxcentral.imf.org)")):
        try:
            share = attempt_fn(currency_code)
            last = max(share)
            hist = [{"y": _qdec(k), "v": round(share[k], 1)} for k in sorted(share)]
            return {"latest": round(share[last], 1), "asOf": f"{last[0]}-Q{last[1]}",
                    "history": hist, "source": "native", "attempt": label}
        except Exception as e:  # noqa: BLE001
            errors.append(f"{label}: {e}")
    raise RuntimeError("IMF-native COFER: both structured attempts failed — " + " | ".join(errors))


def cofer_usd_share():
    """{"latest": float, "asOf": "YYYY-Qn", "history": [{y, v}], "source"}
    — USD % of world allocated reserves. Tries IMF-native first (exactly
    two attempts, TASKnativesources.md §3), then the DBnomics mirror."""
    try:
        return _cofer_native("USD")
    except Exception as e:  # noqa: BLE001
        print(f"IMF-native COFER USD unavailable, falling back to DBnomics mirror: {e}")
        result = _cofer_share(SHARE_SERIES)
        result["source"] = "dbnomics_mirror"
        return result


def cofer_eur_share():
    """Same construction as cofer_usd_share(), euro instead of dollar
    (TASKeuroarea.md) — tries IMF-native first, DBnomics mirror second.

    **Mirror confirmed live, 2026-07-23 CI run**: `Q.W00.RAXGFXAREURRT_PT`
    404'd on DBnomics — the USD->EUR currency-code substitution that works
    throughout this file's own SHARE_SERIES naming pattern isn't how that
    mirror-side series is actually keyed for EUR. Native COFER (§1/§3),
    if it resolves for either currency, migrates BOTH together per the
    task's own "migrate both or neither, same series family" instruction
    — see fetch.py's build_eurosystem() for where that's enforced. Worth
    noting separately: the USD share via the mirror that same run
    returned 57.7% as of 2025-Q1 — 568 days old — so COFER's DBnomics
    mirror is ALSO currently stale for the pre-existing US row (STATUS.md
    §17/§18), independent of anything in this euro-area addition."""
    try:
        return _cofer_native("EUR")
    except Exception as e:  # noqa: BLE001
        print(f"IMF-native COFER EUR unavailable, falling back to DBnomics mirror: {e}")
        result = _cofer_share(SHARE_SERIES_EUR)
        result["source"] = "dbnomics_mirror"
        return result


def verify() -> bool:
    """Dump IMF-native attempts first, then the DBnomics mirror series
    codes + computed shares. Non-fatal: always returns True (a source
    hiccup must not red the run — the build falls back to the manual
    value)."""
    print("\nVerifying IMF COFER — native first (2 structured attempts), "
          "DBnomics mirror as fallback (TASKnativesources.md)\n")
    for label, fn in (("USD", cofer_usd_share), ("EUR", cofer_eur_share)):
        try:
            r = fn()
            src = r.get("source", "?")
            if src == "native":
                print(f"[cofer] {label} share resolved NATIVE ({r.get('attempt')}): "
                      f"{r['latest']}% as of {r['asOf']}")
            else:
                f = S.freshness(f"COFER {label} share", r["asOf"], S.COFER_FRESH_DAYS)
                fresh_s = "STALE" if f["stale"] else "ok"
                print(f"[cofer] {label} share resolved via DBnomics mirror (native failed): "
                      f"{r['latest']}% as of {r['asOf']} ({len(r['history'])} pts) — "
                      f"freshness: {f['age_days']}d old, {S.COFER_FRESH_DAYS}d threshold, {fresh_s}")
        except Exception as e:  # noqa: BLE001
            print(f"[cofer] {label} share unavailable (native and mirror both failed) — "
                  f"build will use the manual value: {e}")

    try:
        docs = _docs()
        codes = sorted({d.get("series_code", "") for d in docs})
        print(f"\n[cofer] DBnomics mirror dataset dump (for reference): {DATASET} (FREQ=Q, REF_AREA=W00)")
        print(f"  {len(docs)} series; codes: {codes[:40]}")
    except Exception as e:  # noqa: BLE001
        print(f"[cofer] DBnomics mirror dataset dump FAILED: {e}")
    return True
