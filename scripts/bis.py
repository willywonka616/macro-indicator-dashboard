"""BIS debt-currency share — world debt securities denominated in USD
(no API key), TASKmanualvalues.md.

Replaces `reserveCurrency.debt` (80.7%, undated, transcribed from Dalio's
Ch.17 book table) with a live figure if one can be confirmed. Source:
DBnomics (https://db.nomics.world), mirroring BIS's `WS_NA_SEC_DSS`
("Debt securities statistics") dataset — the same free, stable aggregator
already used for IMF COFER (imf.py) and, until it froze, LBMA gold
(gold.py's module docstring).

**Honest limitation, stated up front rather than glossed over**: the
exact SDMX dimension names DBnomics uses for this specific BIS dataset
were NOT confirmed before writing this module. Both `data.bis.org` and
`db.nomics.world` are blocked by this project's dev sandbox proxy (the
same "not reachable from dev, but CI has full internet" asymmetry
already documented for FRED/Treasury/CBO/gold in this project — see
treasury.py's module docstring), so this could not be verified live from
here the way COFER's dimension names were. Research into BIS's own
published example series keys (e.g.
`Q.N.KR.XW.S13.S1.N.L.LE.F3.T._Z.USD._T.N.V.N.C02`) confirmed the
dataset uses a positional dot-separated SDMX key, not named dimensions —
but did not yield high-confidence values for a "world total" issuer
residence or an "all currencies" comparator to compute a clean USD share
against. Rather than force a guess and risk silently shipping a
wrong-basis number (the exact failure mode `--verify`'s "check before
building on it" discipline exists to catch), this module does the
best-effort version: a bounded, defensive server-side query, dumped in
full via `verify()` so the first live CI run is the actual test — and if
it doesn't resolve, `debt_currency_share_usd()` raises cleanly and the
caller falls back to the existing manual value, same as every other
source in this project that can fail.

**TASKnativesources.md §4 audit note**: BIS *does* have its own native
SDMX RESTful API, confirmed via live web research —
`https://stats.bis.org/api/v1/data/{dataset}/{key}/all` (real example:
`.../data/WS_EER_M/M.N.B.CH/all?startPeriod=2000&endPeriod=2000&detail=full`).
Unlike the Eurostat/ECB/COFER migrations elsewhere in this project, this
module's blocker was never DBnomics-mirror staleness — it's the
underlying SDMX dimension codes themselves being unconfirmed, a problem
transport migration alone doesn't fix. `verify()` now also probes the
native endpoint (`_native_probe()`) with the same best-effort attempts,
so if a future session (or this one, live) gets lucky, it's visible —
but this stays a DBnomics-based module for now, not a completed native
migration; kept as documented migration debt, not silently left as if
nothing changed.
"""

from __future__ import annotations

import json
import time

import requests

DATASET = "https://api.db.nomics.world/v22/series/BIS/WS_NA_SEC_DSS"
NATIVE_BASE = "https://stats.bis.org/api/v1/data/WS_NA_SEC_DSS"

# Best-effort dimension-name guesses, tried in order — DBnomics generally
# preserves a dataset's own SDMX dimension IDs, but BIS's own public docs
# didn't yield a confirmed list (see module docstring). FREQ=Q narrows the
# ~50,840-series dataset to a fetchable size; a second dimension (issuer
# residence) is needed to reach "world" rather than one country, but
# which key name and which code means "world" were not confirmed —
# several plausible pairs are tried, first one that returns any series wins.
_ATTEMPTS = [
    {"FREQ": ["Q"], "ISSUER_RES": ["5J"]},   # 5J is BIS's common "all countries" code
    {"FREQ": ["Q"], "ISSUER_RES": ["3P"]},   # 3P: another BIS "all reporting countries" code seen in the wild
    {"FREQ": ["Q"], "L_REP_CTY": ["5J"]},
]


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
                time.sleep(2 ** i)
    raise RuntimeError(f"DBnomics/BIS request failed after {tries} tries: {last}")


def _try_docs():
    """Returns (docs, which_attempt_dict) for the first dimension-filter
    guess that returns any series at all — or ([], None) if none do."""
    for attempt in _ATTEMPTS:
        params = {"dimensions": json.dumps(attempt), "limit": "1000", "observations": "1"}
        try:
            js = _get(DATASET, params)
        except RuntimeError:
            continue
        docs = js.get("series", {}).get("docs", [])
        if docs:
            return docs, attempt
    return [], None


def debt_currency_share_usd() -> dict:
    """{"latest": float, "asOf": "YYYY-Qn", "history": [{y, v}]} — % of
    world debt securities denominated in USD. Raises on any failure; the
    caller (fetch.py) falls back to the existing manual value (Dalio's
    Ch.17 80.7%, dated)."""
    docs, attempt = _try_docs()
    if not docs:
        raise RuntimeError(
            "BIS WS_NA_SEC_DSS: no dimension-filter guess returned any series — "
            "exact schema unconfirmed, see bis.py module docstring")
    usd_docs = [d for d in docs if "USD" in str(d.get("series_code", "")).upper().split(".")]
    total_docs = [d for d in docs if any(tok in str(d.get("series_code", "")).upper().split(".")
                                          for tok in ("_T", "_Z", "TOTAL"))]
    if not usd_docs or not total_docs:
        raise RuntimeError(
            f"BIS WS_NA_SEC_DSS: filter {attempt} resolved ({len(docs)} series) but no "
            f"USD-denominated or all-currency-total series identifiable among them — "
            f"exact key layout unconfirmed, see --verify dump")
    raise RuntimeError(
        "BIS WS_NA_SEC_DSS: found candidate USD/total series but computing a clean "
        "matched-basis share from them is not yet implemented — see --verify dump "
        "and bis.py module docstring for what was found")


def _native_probe():
    """TASKnativesources.md §4: best-effort probe of BIS's own native SDMX
    endpoint, same unconfirmed dimension-code guesses as the DBnomics
    attempts above (Q.5J and Q.3P as the "world" issuer-residence code).
    Diagnostic only — dumped via verify(), not wired into
    debt_currency_share_usd() (this module's real blocker is the
    dimension codes, not which transport serves them)."""
    for key in ("Q.5J", "Q.3P"):
        url = f"{NATIVE_BASE}/{key}/all"
        try:
            r = requests.get(url, params={"format": "csv", "detail": "full"}, timeout=30)
            print(f"  native probe {url}: HTTP {r.status_code}, "
                  f"{len(r.text.splitlines())} lines" if r.status_code == 200
                  else f"  native probe {url}: HTTP {r.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  native probe {url}: FAILED: {e}")


def verify() -> bool:
    """Dumps whatever the best-effort dimension-filter attempts actually
    return, so the exact schema (or exact failure) is visible in the run
    log. Non-fatal: always returns True."""
    print(f"\n[BIS] native SDMX probe (TASKnativesources.md §4, diagnostic only): {NATIVE_BASE}")
    _native_probe()
    print(f"\n[BIS] {DATASET}")
    for attempt in _ATTEMPTS:
        params = {"dimensions": json.dumps(attempt), "limit": "20", "observations": "1"}
        try:
            js = _get(DATASET, params)
            docs = js.get("series", {}).get("docs", [])
            print(f"  dimensions={attempt} -> {len(docs)} series"
                  + (f", e.g. {[d.get('series_code') for d in docs[:5]]}" if docs else ""))
        except Exception as e:  # noqa: BLE001
            print(f"  dimensions={attempt} -> FAILED: {e}")
    try:
        share = debt_currency_share_usd()
        print(f"  computed USD share: {share['latest']}% as of {share['asOf']}")
    except Exception as e:  # noqa: BLE001
        print(f"  debt_currency_share_usd() FAILED (expected until the schema above is confirmed): {e}")
    return True
