"""FRED series registry and derived-metric computations.

The registry below is the single source of truth for which FRED series we
pull and what we *expect* each to look like. fetch.py --verify checks every
ID against the live FRED metadata and reports mismatches; nothing here is
trusted blindly.

Numbers are never hardcoded — derived metrics are computed from the fetched
observations by the functions at the bottom of this file.

Unit note: several derivations divide one dollar series by another. FRED
reports amounts in "Billions of Dollars", "Millions of Dollars" or plain
"Dollars"; `to_dollars` normalises any of these to base dollars using the
units string returned by the API, so a ratio is correct regardless of the
scale each series happens to use.
"""

from __future__ import annotations

# --- registry ------------------------------------------------------------

# FRED series actively used by the fetcher. --verify checks each one every run.
#
# The brief's full candidate list (13 IDs incl. GFDEBTN, GDPC1, WALCL, CPIAUCSL,
# FEDFUNDS, DGS10, A091RC1Q027SBEA, W006RC1Q027SBEA) was verified once against
# live FRED — all resolved (see the first Update-data run log). Two were dropped
# from active use afterwards:
#   * BOPBCA (current account) is DISCONTINUED on FRED -> replaced by IEABC.
#   * A091/W006 (interest, tax receipts) -> debt service now comes from the
#     Treasury Fiscal Data API on a budget basis (see treasury.py); the tax-only
#     W006 denominator also overstated the ratio.
# `kind`: "level" (dollars) | "percent" (already a rate/percentage).
FRED_SERIES = {
    "FYGFGDQ188S": {"label": "Federal debt held by public as % of GDP", "units": "percent", "freq": "Quarterly", "start": "1966", "kind": "percent"},
    "GDP":    {"label": "GDP (nominal)", "units": "Billions of Dollars", "freq": "Quarterly", "start": "1947", "kind": "level"},
    "TCMDO":  {"label": "Total debt, all sectors", "units": "Millions of Dollars", "freq": "Quarterly", "start": "1945", "kind": "level"},
    "IEABC":  {"label": "Balance on current account", "units": "Millions of Dollars", "freq": "Quarterly", "start": "1960", "kind": "level"},
    "TRESEGUSM052N": {"label": "Total reserves excl. gold", "units": "Millions of Dollars", "freq": "Monthly", "start": "1950s", "kind": "level"},
    "DGS10":  {"label": "10-year Treasury yield", "units": "Percent", "freq": "Daily", "start": "1962", "kind": "percent"},
    "CPIAUCSL": {"label": "CPI (all urban)", "units": "Index 1982-1984=100", "freq": "Monthly", "start": "1947", "kind": "level"},
}

# --- unit normalisation --------------------------------------------------

def to_dollars(value: float, units: str) -> float:
    """Normalise a dollar amount to base dollars using the FRED units string."""
    u = (units or "").lower()
    if "trillion" in u:
        return value * 1e12
    if "billion" in u:
        return value * 1e9
    if "million" in u:
        return value * 1e6
    if "thousand" in u:
        return value * 1e3
    return value  # already in dollars (or unitless — caller's responsibility)


# --- date helpers --------------------------------------------------------

def decimal_year(dt) -> float:
    """datetime.date -> decimal year (mid-quarter granularity is plenty)."""
    return round(dt.year + (dt.month - 1) / 12.0, 3)


def quarter_key(dt):
    return (dt.year, (dt.month - 1) // 3 + 1)


def q_decimal(qkey) -> float:
    y, q = qkey
    return round(y + (q - 1) / 4.0, 3)


def q_label(qkey) -> str:
    y, q = qkey
    return f"{y}-Q{q}"


def as_quarterly(obs):
    """[(date, value)] -> {qkey: value} keeping the last obs in each quarter."""
    out = {}
    for dt, v in obs:
        out[quarter_key(dt)] = v  # obs are ascending, so last wins
    return out


def as_monthly(obs):
    """[(date, value)] -> {(y,m): value} keeping the last obs in each month."""
    out = {}
    for dt, v in obs:
        out[(dt.year, dt.month)] = v
    return out


# --- history shaping -----------------------------------------------------

def quarterly_history(qseries: dict):
    """{qkey: value} -> sorted [{"y": decimalYear, "v": value}]."""
    return [{"y": q_decimal(k), "v": round(v, 3)} for k, v in sorted(qseries.items())]


# --- derived metrics -----------------------------------------------------
# Each returns {"latest": float, "asOf": "YYYY-Qn", "history": [{y,v}]}.

def _latest(qseries: dict):
    k = max(qseries)
    return qseries[k], q_label(k)


# Debt service vs revenue is computed on a budget basis from the Treasury
# Fiscal Data API — see treasury.py. (The old FRED NIPA-basis version used
# interest payments / current tax receipts.)


def reserves_pct_gdp(reserves_obs, reserves_units, gdp_obs, gdp_units):
    """Total reserves (excl. gold) as a percentage of nominal GDP."""
    res_m = as_monthly(reserves_obs)
    # collapse monthly reserves to quarterly (last month of quarter present)
    res_q = {}
    for (y, m), v in res_m.items():
        res_q[(y, (m - 1) // 3 + 1)] = v
    gdp = as_quarterly(gdp_obs)
    ratio = {}
    for k in res_q.keys() & gdp.keys():
        denom = to_dollars(gdp[k], gdp_units)
        if denom:
            ratio[k] = to_dollars(res_q[k], reserves_units) / denom * 100.0
    latest, asof = _latest(ratio)
    return {"latest": round(latest, 1), "asOf": asof, "history": quarterly_history(ratio)}


def total_debt_pct_gdp(tcmdo_obs, tcmdo_units, gdp_obs, gdp_units):
    """Total debt, all sectors, as a percentage of nominal GDP."""
    d = as_quarterly(tcmdo_obs)
    gdp = as_quarterly(gdp_obs)
    ratio = {}
    for k in d.keys() & gdp.keys():
        denom = to_dollars(gdp[k], gdp_units)
        if denom:
            ratio[k] = to_dollars(d[k], tcmdo_units) / denom * 100.0
    latest, asof = _latest(ratio)
    return {"latest": round(latest, 1), "asOf": asof, "history": quarterly_history(ratio)}


def current_account_pct_gdp_3yr(ca_obs, ca_units, gdp_obs, gdp_units, annualized_ca: bool):
    """Current account as % of GDP, 3-year (12-quarter) trailing average.

    GDP is a seasonally-adjusted annual rate. If the current-account series
    is *not* itself annualised (the usual BOPBCA convention), each quarter is
    annualised as a trailing 4-quarter sum before dividing. --verify prints
    the CA units/adjustment so this assumption can be confirmed against FRED.
    """
    ca = as_quarterly(ca_obs)
    gdp = as_quarterly(gdp_obs)
    keys = sorted(ca.keys() & gdp.keys())
    quarterly_ratio = {}
    for idx, k in enumerate(keys):
        gdp_usd = to_dollars(gdp[k], gdp_units)
        if not gdp_usd:
            continue
        if annualized_ca:
            ca_annual = to_dollars(ca[k], ca_units)
        else:
            # trailing 4-quarter sum -> annual flow
            window = keys[max(0, idx - 3): idx + 1]
            if len(window) < 4:
                continue
            ca_annual = sum(to_dollars(ca[w], ca_units) for w in window)
        quarterly_ratio[k] = ca_annual / gdp_usd * 100.0

    # 3-year (12q) trailing average of the quarterly ratio
    ks = sorted(quarterly_ratio.keys())
    avg = {}
    for idx, k in enumerate(ks):
        window = ks[max(0, idx - 11): idx + 1]
        if len(window) < 12:
            continue
        avg[k] = sum(quarterly_ratio[w] for w in window) / len(window)
    latest, asof = _latest(avg)
    return {"latest": round(latest, 1), "asOf": asof, "history": quarterly_history(avg)}


def real_10y_rate(dgs10_obs, cpi_obs):
    """10-year Treasury yield minus trailing 12-month CPI inflation."""
    # DGS10 daily -> monthly (last obs in month)
    y10 = as_monthly(dgs10_obs)
    cpi = as_monthly(cpi_obs)
    infl = {}
    for (yr, m), v in cpi.items():
        prev = cpi.get((yr - 1, m))
        if prev:
            infl[(yr, m)] = (v / prev - 1.0) * 100.0
    real = {}
    for k in y10.keys() & infl.keys():
        real[k] = y10[k] - infl[k]
    # collapse to quarterly for display / latest
    real_q = {}
    for (yr, m), v in real.items():
        real_q[(yr, (m - 1) // 3 + 1)] = v
    latest, asof = _latest(real_q)
    return {"latest": round(latest, 2), "asOf": asof, "history": quarterly_history(real_q)}
