"""Generic SDMX 2.1 REST client — Eurostat, ECB, IMF (TASKnativesources.md).

**Native-first policy** (recorded in STATUS.md and CLAUDE.md): DBnomics is
a convenience cache, not the default. Three incidents forced this — gold's
PCPS mirror frozen, IMF COFER 568 days stale, and the euro-area series
380-480 days stale (STATUS.md §32) — in every case the actual upstream
(Eurostat/ECB/IMF) was fine and only the mirror had rotted. This module
talks to the native SDMX endpoints directly.

Base URLs and formats below were confirmed via live web research
(2026-07-24) — this dev sandbox cannot reach any of these hosts directly
to verify by calling them (same "not reachable from dev, CI has full
internet" asymmetry already documented for FRED/Treasury/CBO/gold/
DBnomics throughout this project — see treasury.py's module docstring),
so `verify()` dumping a real CI run's actual response is still the real
test, same discipline as every other integration here.

**Eurostat** — SDMX 2.1, JSON-stat 2.0 response:
    https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{dataset}/{key}?format=JSON
`key` is a dot-separated string of dimension codes IN THE DATASET'S OWN
ORDER (confirmed real example: `NAMA_10_GDP/A.CP_MEUR.B1GQ.LU`, order
FREQ.UNIT.NA_ITEM.GEO for that dataset). Crucially, DBnomics' Eurostat
mirror preserves Eurostat's native key order verbatim — every key already
confirmed live against DBnomics in scripts/eurostat.py (e.g.
`gov_10q_ggdebt`: `Q.GD.S13.PC_GDP.EA20`) should resolve unchanged here,
same series, new transport, not a re-guess.

**ECB** — SDMX 2.1, CSV response (simplest to parse, per the task):
    https://data-api.ecb.europa.eu/service/data/{flow}/{key}?format=csvdata
Confirmed real examples: `EXR/M.USD.EUR.SP00.A?format=csvdata`,
`YC/B.U2.EUR.4F.G_N_A+G_N_C.SV_C_YM.?lastNObservations=1&format=csvdata`.
CSV columns include `REF_AREA`, `TIME_PERIOD`, `OBS_VALUE` plus every
other series-key dimension as its own column.

**IMF** — genuinely unstable; this project's own gold.py module docstring
already flags dataservices.imf.org as decommissioned. Two base-URL
candidates are tried in imf.py's cofer_native() (api.imf.org's SDMX 3.0
endpoint, then the legacy sdmxcentral.imf.org SDMX 2.1 REST endpoint) —
if neither resolves, TASKnativesources.md §1's own instruction is to stop
and keep the manual-dated fallback, not keep guessing.
"""

from __future__ import annotations

import csv
import io
import time

import requests

EUROSTAT_BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data"
ECB_BASE = "https://data-api.ecb.europa.eu/service/data"

# Some SDMX endpoints throttle or reject the default python-requests
# User-Agent (TASKnativesources.md §1's own warning) — a real browser-like
# UA avoids that without misrepresenting what's making the request beyond
# what's needed to not get bucketed with naive scrapers.
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; macro-indicator-dashboard/1.0; "
                          "+https://github.com/willywonka616/macro-indicator-dashboard)"}


def _get(url, params=None, headers=None, tries=4, timeout=45):
    last = None
    hdrs = {**_HEADERS, **(headers or {})}
    for i in range(tries):
        try:
            r = requests.get(url, params=params or {}, headers=hdrs, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)  # 1s, 2s, 4s
    raise RuntimeError(f"SDMX request to {url} failed after {tries} tries: {last}")


# --- period parsing --------------------------------------------------------

def _parse_period(period: str):
    """'2025-Q1'/'2025Q1' -> ('Q', (2025,1)); '2025-06'/'2025M06' -> ('M', (2025,6));
    '2025' -> ('A', (2025,)). Returns (freq_guess, tuple_key)."""
    p = period.strip()
    if "Q" in p:
        p2 = p.replace("-Q", "Q").replace("Q", "-Q") if "-Q" not in p else p
        y, q = p2.split("-Q")
        return "Q", (int(y), int(q))
    if "M" in p and not p[0:1].isalpha():
        p2 = p.replace("-M", "M").replace("M", "-M") if "-M" not in p else p
        y, m = p2.split("-M")
        return "M", (int(y), int(m))
    if "-" in p and len(p.split("-")) == 2:
        y, m = p.split("-")
        return "M", (int(y), int(m))
    if len(p) == 4 and p.isdigit():
        return "A", (int(p),)
    raise ValueError(f"unrecognised SDMX period format: {period!r}")


# --- Eurostat: JSON-stat 2.0 -----------------------------------------------

def eurostat_series(dataset: str, key: str) -> dict:
    """Fetch one Eurostat SDMX series (all dimensions pinned to a single
    code except time) and return {tuple_key: value} ascending, keyed the
    same shape scripts/eurostat.py's DBnomics functions already use
    ((year,quarter) or (year,month)). Raises on any failure or if the key
    doesn't pin down to a single non-time series."""
    url = f"{EUROSTAT_BASE}/{dataset}/{key}"
    r = _get(url, params={"format": "JSON"})
    js = r.json()
    if "dimension" not in js or "value" not in js:
        raise RuntimeError(f"eurostat_series({dataset}, {key}): unexpected response shape "
                            f"(no dimension/value) — {list(js.keys())}")
    dims = js["dimension"]
    dim_ids = js.get("id") or list(dims.keys())
    sizes = js.get("size") or [len(dims[d]["category"]["index"]) for d in dim_ids]
    if "time" not in dims:
        raise RuntimeError(f"eurostat_series({dataset}, {key}): no 'time' dimension in response")
    time_idx = dim_ids.index("time")
    time_index = dims["time"]["category"]["index"]  # {period_code: position}
    # Every other dimension must be pinned to exactly one category (the key
    # should already ensure this) — verify, don't assume, since a wrong key
    # segment could silently return multiple series flattened together.
    for i, d in enumerate(dim_ids):
        if i == time_idx:
            continue
        if sizes[i] != 1:
            raise RuntimeError(f"eurostat_series({dataset}, {key}): dimension {d!r} has "
                                f"{sizes[i]} categories, expected 1 — key doesn't fully pin it down")
    # Flat-index stride for the time dimension (row-major, JSON-stat convention).
    stride = 1
    for s in sizes[time_idx + 1:]:
        stride *= s
    value = js["value"]
    # JSON responses may give `value` as a dict (sparse) or a list (dense).
    def _get_val(flat_idx):
        if isinstance(value, dict):
            return value.get(str(flat_idx))
        return value[flat_idx] if 0 <= flat_idx < len(value) else None

    out = {}
    for period_code, pos in time_index.items():
        v = _get_val(pos * stride)
        if v is None:
            continue
        try:
            _, tkey = _parse_period(period_code)
        except ValueError:
            continue
        out[tkey] = float(v)
    if not out:
        raise RuntimeError(f"eurostat_series({dataset}, {key}): resolved but no usable observations")
    return out


# --- ECB: CSV ---------------------------------------------------------------

def ecb_series(flow: str, key: str, last_n: int | None = None) -> dict:
    """Fetch one ECB SDMX series via the CSV data format and return
    {tuple_key: value} ascending. Raises on any failure."""
    url = f"{ECB_BASE}/{flow}/{key}"
    params = {"format": "csvdata"}
    if last_n:
        params["lastNObservations"] = str(last_n)
    r = _get(url, params=params)
    text = r.text
    reader = csv.DictReader(io.StringIO(text))
    out = {}
    freq_col = None
    for row in reader:
        if freq_col is None:
            freq_col = "FREQ" if "FREQ" in row else None
        period = row.get("TIME_PERIOD")
        val = row.get("OBS_VALUE")
        if not period or val in (None, ""):
            continue
        try:
            _, tkey = _parse_period(period)
            out[tkey] = float(val)
        except (ValueError, TypeError):
            continue
    if not out:
        raise RuntimeError(f"ecb_series({flow}, {key}): resolved (HTTP ok) but no usable "
                            f"observations parsed from the CSV response")
    return out


# --- verification ------------------------------------------------------------

def verify_eurostat(dataset: str, key: str, label: str = ""):
    try:
        series = eurostat_series(dataset, key)
        last = max(series)
        print(f"  [Eurostat native] {dataset}/{key} ({label}): "
              f"latest {last} = {series[last]}, {len(series)} pts")
        return series
    except Exception as e:  # noqa: BLE001
        print(f"  [Eurostat native] {dataset}/{key} ({label}): FAILED: {e}")
        return None


def verify_ecb(flow: str, key: str, label: str = "", last_n: int = 6):
    try:
        series = ecb_series(flow, key, last_n=last_n)
        last = max(series)
        print(f"  [ECB native] {flow}/{key} ({label}): "
              f"latest {last} = {series[last]}, {len(series)} pts")
        return series
    except Exception as e:  # noqa: BLE001
        print(f"  [ECB native] {flow}/{key} ({label}): FAILED: {e}")
        return None
