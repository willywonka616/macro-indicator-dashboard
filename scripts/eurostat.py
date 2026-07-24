"""Eurostat government finance statistics + balance of payments —
native SDMX first, DBnomics mirror as a tightened-threshold fallback
(TASKnativesources.md's native-first policy; see STATUS.md/CLAUDE.md).

**Why native-first**: the DBnomics mirror of these exact series resolved
correct VALUES (TASKeuroarea.md, STATUS.md §32) but was itself frozen
380-478 days behind — the same "mirror rots, upstream is fine" pattern
already hit for gold's PCPS feed and IMF COFER. `scripts/sdmx.py` talks to
Eurostat's own SDMX 2.1 REST API directly; every series code below is
UNCHANGED from the DBnomics integration (`Q.GD.S13.PC_GDP.EA20` etc. —
Eurostat's own key order, which DBnomics preserves verbatim) — this is a
transport migration, not a re-derivation. See sdmx.py's module docstring
for the confirmed base URL/response format.

Every function tries native first, the DBnomics mirror second (kept only
as a defensive fallback, with a materially tighter freshness threshold
than before — see series.py's EUROSTAT_FRESH_DAYS vs.
EUROSTAT_MIRROR_FRESH_DAYS), and raises if neither resolves so the caller
falls back to the manual book value, same three-tier pattern already
established elsewhere in this project (gold: LBMA -> World Bank ->
manual).

**Central vs general government** (TASKeuroarea.md §3's "big one"): Dalio's
Ch.17 table's debt figure is central-government only; Eurostat's own
headline euro-area ratio is general government (sector S13). Central
government alone is sector S1311. Both are fetched and compared at his
March 2025 vintage against his 85% — see fetch.py's build_eur() and
STATUS.md's EUR section for which basis was actually adopted (finding:
general, not central — STATUS.md §32.4).
"""

from __future__ import annotations

import time

import requests

import sdmx as X

GEO_ATTEMPTS = ["EA20", "EA19"]  # EA20 = current composition (Croatia joined 2023);
# EA19 kept as a fallback for datasets not yet updated to the new aggregate.

# Native Eurostat dataset codes (bare — sdmx.py's EUROSTAT_BASE prefixes them).
DS_GGDEBT = "gov_10q_ggdebt"
DS_GGNFA = "gov_10q_ggnfa"
DS_BOP = "bop_gdp6_q"
DS_GDP = "namq_10_gdp"

# DBnomics mirror fallback (unchanged from the pre-migration integration).
_DBNOMICS_GGDEBT = "https://api.db.nomics.world/v22/series/Eurostat/gov_10q_ggdebt"
_DBNOMICS_GGNFA = "https://api.db.nomics.world/v22/series/Eurostat/gov_10q_ggnfa"
_DBNOMICS_BOP = "https://api.db.nomics.world/v22/series/Eurostat/bop_gdp6_q"
_DBNOMICS_GDP = "https://api.db.nomics.world/v22/series/Eurostat/namq_10_gdp"


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
    raise RuntimeError(f"DBnomics/Eurostat request failed after {tries} tries: {last}")


def _qkey(period):
    p = period.replace("Q", "-Q") if "-Q" not in period and "Q" in period else period
    y, q = p.split("-Q")
    return (int(y), int(q))


def _qdec(k):
    return round(k[0] + (k[1] - 1) / 4.0, 3)


def _dbnomics_fetch(dataset_base: str, series_code: str) -> dict:
    js = _dbnomics_get(f"{dataset_base}/{series_code}", {"observations": "1"})
    docs = js.get("series", {}).get("docs", [])
    if not docs:
        raise RuntimeError(f"{dataset_base}/{series_code}: no series returned")
    doc = docs[0]
    out = {}
    for period, val in zip(doc.get("period", []), doc.get("value", [])):
        if val is None or period is None:
            continue
        try:
            out[_qkey(period)] = float(val)
        except (TypeError, ValueError):
            continue
    if not out:
        raise RuntimeError(f"{dataset_base}/{series_code}: no usable observations")
    return out


def _resolve(native_dataset: str, dbnomics_base: str, code_template) -> tuple[dict, str, str]:
    """Try NATIVE Eurostat SDMX first (every template x geo combo), then
    the DBnomics mirror (same combos) as a fallback. Returns
    (series_dict, geo_used, source) where source is "native" or
    "dbnomics_mirror" — callers/fetch.py use this to tag provenance and
    apply the right freshness threshold for whichever transport actually
    served the data (native-first policy, TASKnativesources.md)."""
    templates = [code_template] if isinstance(code_template, str) else code_template
    last_err = None
    for template in templates:
        for geo in GEO_ATTEMPTS:
            key = template.format(geo=geo)
            try:
                return X.eurostat_series(native_dataset, key), geo, "native"
            except Exception as e:  # noqa: BLE001
                last_err = e
    for template in templates:
        for geo in GEO_ATTEMPTS:
            key = template.format(geo=geo)
            try:
                return _dbnomics_fetch(dbnomics_base, key), geo, "dbnomics_mirror"
            except RuntimeError as e:
                last_err = e
    raise RuntimeError(f"{templates}: no native or mirror attempt resolved ({GEO_ATTEMPTS}): {last_err}")


def _to_metric(hist: dict, geo: str, source: str) -> dict:
    last = max(hist)
    return {
        "latest": round(hist[last], 1),
        "asOf": f"{last[0]}-Q{last[1]}",
        "history": [{"y": _qdec(k), "v": round(v, 2)} for k, v in sorted(hist.items())],
        "raw": hist,
        "geo": geo,
        "source": source,
    }


def general_govt_debt_pct_gdp() -> dict:
    """Maastricht (gross) debt, general government (S13), % of GDP —
    Eurostat's own headline euro-area ratio."""
    hist, geo, source = _resolve(DS_GGDEBT, _DBNOMICS_GGDEBT, "Q.GD.S13.PC_GDP.{geo}")
    return _to_metric(hist, geo, source)


def central_govt_debt_pct_gdp() -> dict:
    """Maastricht (gross) debt, central government (S1311) ONLY, % of GDP —
    the basis Dalio's Ch.17 table's own note claims (per STATUS.md §32.4,
    live data disagrees — general government is the closer match)."""
    hist, geo, source = _resolve(DS_GGDEBT, _DBNOMICS_GGDEBT, "Q.GD.S1311.PC_GDP.{geo}")
    return _to_metric(hist, geo, source)


def vintage_value(metric: dict, year: int, quarter: int):
    """Read a specific (year, quarter) out of a metric's raw history —
    used to identify the central-vs-general basis AT Dalio's March 2025
    vintage, not at whatever quarter happens to be current today."""
    return metric["raw"].get((year, quarter))


def central_govt_interest_pct_revenue() -> dict:
    """Central government (S1311) interest paid (D41) / total revenue
    (TR), both in MIO_EUR so no GDP denominator is needed. Native/mirror
    resolution is independent per leg (interest, revenue) since a wrong
    guess on one shouldn't block the other if it happens to resolve."""
    interest_hist, geo, isrc = _resolve(DS_GGNFA, _DBNOMICS_GGNFA, [
        "Q.D41.S1311.MIO_EUR.{geo}",
        "Q.S1311.D41.MIO_EUR.{geo}",
    ])
    revenue_hist, _, rsrc = _resolve(DS_GGNFA, _DBNOMICS_GGNFA, [
        f"Q.TR.S1311.MIO_EUR.{geo}",
    ])
    common = interest_hist.keys() & revenue_hist.keys()
    if not common:
        raise RuntimeError("central_govt_interest_pct_revenue: no overlapping quarters")
    ratio = {k: interest_hist[k] / revenue_hist[k] * 100.0 for k in common if revenue_hist[k]}
    if not ratio:
        raise RuntimeError("central_govt_interest_pct_revenue: no valid (nonzero-revenue) quarters")
    source = "native" if isrc == rsrc == "native" else "dbnomics_mirror" if "dbnomics_mirror" in (isrc, rsrc) else isrc
    return _to_metric(ratio, geo, source)


def gdp_eur_millions() -> dict:
    """Nominal GDP, current prices, million euro, quarterly, euro area."""
    hist, geo, source = _resolve(DS_GDP, _DBNOMICS_GDP, [
        "Q.B1GQ.CP_MEUR.SCA.{geo}",
        "Q.CP_MEUR.SCA.B1GQ.{geo}",
        "Q.B1GQ.CP_MEUR.NSA.{geo}",
    ])
    return _to_metric(hist, geo, source)


def current_account_pct_gdp() -> dict:
    """Current-account balance, % of GDP, quarterly, euro area."""
    hist, geo, source = _resolve(DS_BOP, _DBNOMICS_BOP, "Q.PC_GDP.NSA.CA.BAL.EXT_{geo}")
    return _to_metric(hist, geo, source)


def verify() -> bool:
    """Dumps whatever each series resolves to (native, then mirror), so
    the exact schema/source (or exact failure) is visible in the run log."""
    print(f"\n[Eurostat] native + mirror fallback: {DS_GGDEBT}")
    for label, fn in (
        ("general government debt (S13) % GDP", general_govt_debt_pct_gdp),
        ("central government debt (S1311) % GDP", central_govt_debt_pct_gdp),
    ):
        try:
            m = fn()
            print(f"  {label}: {m['latest']}% as of {m['asOf']} (geo={m['geo']}, "
                  f"source={m['source']}, {len(m['history'])} pts)")
            v2025q1 = vintage_value(m, 2025, 1)
            if v2025q1 is not None:
                print(f"    at Dalio's vintage (2025-Q1): {round(v2025q1, 1)}% "
                      f"(book target: 85%, general-vs-central identification)")
        except Exception as e:  # noqa: BLE001
            print(f"  {label}: FAILED (native and mirror both failed): {e}")

    print(f"\n[Eurostat] native + mirror fallback: {DS_GGNFA}")
    try:
        m = central_govt_interest_pct_revenue()
        print(f"  central govt interest / revenue: {m['latest']}% as of {m['asOf']} "
              f"(geo={m['geo']}, source={m['source']})")
    except Exception as e:  # noqa: BLE001
        print(f"  central govt interest / revenue: FAILED: {e}")

    print(f"\n[Eurostat] native + mirror fallback: {DS_BOP}")
    try:
        m = current_account_pct_gdp()
        print(f"  current account % GDP: {m['latest']}% as of {m['asOf']} "
              f"(geo={m['geo']}, source={m['source']})")
    except Exception as e:  # noqa: BLE001
        print(f"  current account % GDP: FAILED: {e}")

    print(f"\n[Eurostat] native + mirror fallback: {DS_GDP}")
    try:
        m = gdp_eur_millions()
        print(f"  nominal GDP: €{m['latest']:,.0f}M as of {m['asOf']} "
              f"(geo={m['geo']}, source={m['source']})")
    except Exception as e:  # noqa: BLE001
        print(f"  nominal GDP: FAILED: {e}")

    return True
