"""Eurostat government finance statistics + balance of payments, via
DBnomics (TASKeuroarea.md).

Source: DBnomics (https://db.nomics.world), which mirrors Eurostat's raw
SDMX datasets as simple JSON — the same free, stable aggregator already
used for IMF COFER (imf.py) and BIS (bis.py). Series codes follow
Eurostat's own dot-separated dimension order, e.g.
`Q.GD.S13.PC_GDP.EA20` = quarterly, Maastricht (gross) debt, general
government, percent of GDP, euro area (20 members, current composition).

**Honest limitation, same as bis.py**: this dev sandbox cannot reach
db.nomics.world (or ec.europa.eu) directly, so the exact dimension codes
below are best-effort — confirmed by web research where possible (the
`Q.<na_item>.<sector>.<unit>.<geo>` shape and `S13`/`S1311`/`EA20` codes
are real, sourced from DBnomics' own published example series), but NOT
verified against a live response the way FRED series are. Every function
degrades cleanly (raises, caller falls back to manual) and `verify()`
dumps whatever the first live CI run actually returns, so a wrong guess
is visible in a job log, not silently wrong in shipped data.

**Central vs general government** (TASKeuroarea.md §3's "big one"): Dalio's
Ch.17 table's debt figure is central-government only; Eurostat's own
headline euro-area ratio is general government (sector S13). Central
government alone is sector S1311. Both are fetched and compared at his
March 2025 vintage against his 85% — see fetch.py's build_eur() and
STATUS.md's EUR section for which basis was actually adopted.
"""

from __future__ import annotations

import time

import requests

GEO_ATTEMPTS = ["EA20", "EA19"]  # EA20 = current composition (Croatia joined 2023);
# EA19 kept as a fallback for datasets not yet updated to the new aggregate.

DATASET_GGDEBT = "https://api.db.nomics.world/v22/series/Eurostat/gov_10q_ggdebt"
DATASET_GGNFA = "https://api.db.nomics.world/v22/series/Eurostat/gov_10q_ggnfa"
DATASET_BOP = "https://api.db.nomics.world/v22/series/Eurostat/bop_gdp6_q"
DATASET_GDP = "https://api.db.nomics.world/v22/series/Eurostat/namq_10_gdp"


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
    raise RuntimeError(f"DBnomics/Eurostat request failed after {tries} tries: {last}")


def _qkey(period):
    """DBnomics quarterly periods look like '2025-Q1' (occasionally '2025Q1')."""
    p = period.replace("Q", "-Q") if "-Q" not in period and "Q" in period else period
    y, q = p.split("-Q")
    return (int(y), int(q))


def _qdec(k):
    return round(k[0] + (k[1] - 1) / 4.0, 3)


def _fetch_series(dataset_base: str, series_code: str) -> dict:
    """{(year, quarter): value} ascending, for one fully-qualified DBnomics
    series code. Raises if the code doesn't resolve or has no observations."""
    js = _get(f"{dataset_base}/{series_code}", {"observations": "1"})
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


def _first_that_resolves(dataset_base: str, code_template) -> tuple[dict, str]:
    """Try each GEO_ATTEMPTS code in order (EA20 then EA19) for one or more
    candidate dimension-order templates, return (series_dict, geo_used) for
    the first that resolves. `code_template` is a single "{geo}"-templated
    string, or a list of them tried in order (DBnomics series codes are
    positional, not named, so a wrong dimension ORDER — not just a wrong
    GEO — is a real failure mode worth covering defensively, same
    "several plausible pairs, first success wins" pattern as bis.py)."""
    templates = [code_template] if isinstance(code_template, str) else code_template
    last_err = None
    for template in templates:
        for geo in GEO_ATTEMPTS:
            code = template.format(geo=geo)
            try:
                return _fetch_series(dataset_base, code), geo
            except RuntimeError as e:
                last_err = e
    raise RuntimeError(f"{templates}: no attempt resolved ({GEO_ATTEMPTS}): {last_err}")


def _to_metric(hist: dict) -> dict:
    last = max(hist)
    return {
        "latest": round(hist[last], 1),
        "asOf": f"{last[0]}-Q{last[1]}",
        "history": [{"y": _qdec(k), "v": round(v, 2)} for k, v in sorted(hist.items())],
        "raw": hist,
    }


def general_govt_debt_pct_gdp() -> dict:
    """Maastricht (gross) debt, general government (S13), % of GDP —
    Eurostat's own headline euro-area ratio."""
    hist, geo = _first_that_resolves(DATASET_GGDEBT, "Q.GD.S13.PC_GDP.{geo}")
    out = _to_metric(hist)
    out["geo"] = geo
    return out


def central_govt_debt_pct_gdp() -> dict:
    """Maastricht (gross) debt, central government (S1311) ONLY, % of GDP —
    the basis Dalio's Ch.17 table actually uses (per the book's own note
    that government debt is central-government only)."""
    hist, geo = _first_that_resolves(DATASET_GGDEBT, "Q.GD.S1311.PC_GDP.{geo}")
    out = _to_metric(hist)
    out["geo"] = geo
    return out


def vintage_value(metric: dict, year: int, quarter: int):
    """Read a specific (year, quarter) out of a metric's raw history —
    used to identify the central-vs-general basis AT Dalio's March 2025
    vintage, not at whatever quarter happens to be current today (same
    "pair at the same vintage" discipline as fetch.py's TCMDO/GDP check)."""
    return metric["raw"].get((year, quarter))


def central_govt_interest_pct_revenue() -> dict:
    """Central government (S1311) interest paid (D41) / total revenue
    (TR), both in MIO_EUR so no GDP denominator is needed — the euro-area
    equivalent of the US debt-service-to-revenue construction."""
    interest_hist, geo = _first_that_resolves(DATASET_GGNFA, [
        "Q.D41.S1311.MIO_EUR.{geo}",
        "Q.S1311.D41.MIO_EUR.{geo}",
    ])
    revenue_hist = _fetch_series(DATASET_GGNFA, f"Q.TR.S1311.MIO_EUR.{geo}")
    common = interest_hist.keys() & revenue_hist.keys()
    if not common:
        raise RuntimeError("central_govt_interest_pct_revenue: no overlapping quarters")
    ratio = {k: interest_hist[k] / revenue_hist[k] * 100.0 for k in common if revenue_hist[k]}
    if not ratio:
        raise RuntimeError("central_govt_interest_pct_revenue: no valid (nonzero-revenue) quarters")
    out = _to_metric(ratio)
    out["geo"] = geo
    return out


def gdp_eur_millions() -> dict:
    """Nominal GDP, current prices, million euro, quarterly, euro area —
    the denominator ECB's own RAS reserves dataset needs (unlike the debt
    and current-account rows above, ECB doesn't publish reserves as a
    ready-made %GDP ratio, so this pipeline divides itself, same as the
    US's TRESEGUSM052N / GDP construction)."""
    hist, geo = _first_that_resolves(DATASET_GDP, [
        "Q.B1GQ.CP_MEUR.SCA.{geo}",
        "Q.CP_MEUR.SCA.B1GQ.{geo}",
        "Q.B1GQ.CP_MEUR.NSA.{geo}",
    ])
    out = _to_metric(hist)
    out["geo"] = geo
    return out


def current_account_pct_gdp() -> dict:
    """Current-account balance, % of GDP, quarterly, euro area — for the
    3-year moving average (computed by the caller, same as the US's
    current_account_pct_gdp_3yr)."""
    hist, geo = _first_that_resolves(DATASET_BOP, "Q.PC_GDP.NSA.CA.BAL.EXT_{geo}")
    out = _to_metric(hist)
    out["geo"] = geo
    return out


def verify() -> bool:
    """Dumps whatever each best-effort series code actually returns, so the
    exact schema (or exact failure) is visible in the run log — same
    non-fatal, always-True pattern as bis.py/imf.py's verify()."""
    print(f"\n[Eurostat] {DATASET_GGDEBT}")
    for label, fn in (
        ("general government debt (S13) % GDP", general_govt_debt_pct_gdp),
        ("central government debt (S1311) % GDP", central_govt_debt_pct_gdp),
    ):
        try:
            m = fn()
            print(f"  {label}: {m['latest']}% as of {m['asOf']} (geo={m['geo']}, {len(m['history'])} pts)")
            v2025q1 = vintage_value(m, 2025, 1)
            if v2025q1 is not None:
                print(f"    at Dalio's vintage (2025-Q1): {round(v2025q1, 1)}% "
                      f"(book target: 85%, general-vs-central identification)")
        except Exception as e:  # noqa: BLE001
            print(f"  {label}: FAILED: {e}")

    print(f"\n[Eurostat] {DATASET_GGNFA}")
    try:
        m = central_govt_interest_pct_revenue()
        print(f"  central govt interest / revenue: {m['latest']}% as of {m['asOf']} (geo={m['geo']})")
    except Exception as e:  # noqa: BLE001
        print(f"  central govt interest / revenue: FAILED: {e}")

    print(f"\n[Eurostat] {DATASET_BOP}")
    try:
        m = current_account_pct_gdp()
        print(f"  current account % GDP: {m['latest']}% as of {m['asOf']} (geo={m['geo']})")
    except Exception as e:  # noqa: BLE001
        print(f"  current account % GDP: FAILED: {e}")

    print(f"\n[Eurostat] {DATASET_GDP}")
    try:
        m = gdp_eur_millions()
        print(f"  nominal GDP: €{m['latest']:,.0f}M as of {m['asOf']} (geo={m['geo']})")
    except Exception as e:  # noqa: BLE001
        print(f"  nominal GDP: FAILED: {e}")

    return True
