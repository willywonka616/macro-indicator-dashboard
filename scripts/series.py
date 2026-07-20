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

import datetime as _dt

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
# TCMDO vs TCMDODNS (2026-07, see STATUS.md §9): tried switching TCMDO
# ("All Sectors; Debt Securities and Loans", Fed Z.1) to TCMDODNS ("Domestic
# Nonfinancial Sectors; Debt Securities and Loans") on the hypothesis that
# excluding the financial sector's own intra-system borrowing would close a
# gap against Dalio's Ch.17 "other debt" row (340%). Live result: TCMDODNS =
# 256.7% of GDP, TCMDO = 362.6% — the swap moved the WRONG direction and
# made the gap much worse (-83pts vs +23pts). Reverted to TCMDO, which is
# not a match either, but is the closer of the two by a wide margin. Kept
# as the reported case study of a reasoned hypothesis that live data
# refuted — see STATUS.md §9 for what "other debt" more plausibly means.
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


# --- freshness guard -------------------------------------------------------

# A dead/frozen source still returns a plausible NUMBER — the sanity bands
# elsewhere in this pipeline check magnitude, not date, so a stale-but-in-band
# value (like the gold price stuck at 2025-06 for a year+) sails through
# every other guard silently. This checks dates instead. Thresholds are set
# per cadence with real headroom above the source's normal publication lag
# (so a routine delay never trips it) but well short of "the source died
# months ago" (so that DOES trip it). See TASKgoldpricefreshness.md.
FRESHNESS_DAYS_BY_FREQ = {
    "Daily": 20,      # FRED daily series (DGS10): a few business days' lag is normal
    "Monthly": 60,     # a monthly series is normally current within 30-45 days
    "Quarterly": 150,  # ~5 months — covers normal release lag with headroom
    "Annual": 400,
}

# IMF COFER publishes quarterly but is documented as running "a quarter or
# two" behind even when healthy (imf.py's own docstring) — a longer
# legitimate lag than the generic Quarterly threshold above allows for, so
# it gets its own explicit threshold rather than being exempted outright
# (TASKgoldpricefreshness.md: "set the threshold to match" the known lag,
# don't just skip the check).
COFER_FRESH_DAYS = 270


def _period_to_date(period) -> _dt.date:
    """Normalise any of this pipeline's 'asOf'/period representations to a
    date, for freshness comparisons: a real date, a (year, month) tuple, or
    a string — 'YYYY-MM', 'YYYY-Qn', or 'YYYY'."""
    if isinstance(period, _dt.date):
        return period
    if isinstance(period, tuple) and len(period) == 2:
        y, m = period
        return _dt.date(y, m, 1)
    s = str(period)
    if "-Q" in s:
        y, q = s.split("-Q")
        return _dt.date(int(y), (int(q) - 1) * 3 + 1, 1)
    if len(s) == 7 and s[4] == "-":
        y, m = s.split("-")
        return _dt.date(int(y), int(m), 1)
    if len(s) == 4 and s.isdigit():
        return _dt.date(int(s), 1, 1)
    return _dt.date.fromisoformat(s)


def freshness(label: str, period, max_age_days: int, today: _dt.date | None = None) -> dict:
    """{"label", "period", "date", "age_days", "max_age_days", "stale"} —
    used both to print an at-a-glance freshness line in --verify and to
    decide whether to raise via require_fresh below."""
    today = today or _dt.date.today()
    d = _period_to_date(period)
    age = (today - d).days
    return {"label": label, "period": str(period), "date": d, "age_days": age,
            "max_age_days": max_age_days, "stale": age > max_age_days}


def require_fresh(label: str, period, max_age_days: int, today: _dt.date | None = None) -> dict:
    """Raises if `period` is older than `max_age_days` — a dead/frozen
    source, not just a normally-lagged one. Callers that already have a
    manual-value fallback (gold price, COFER) catch this the same way they
    catch any other fetch failure; callers with no fallback (the core FRED
    series, Treasury debt-service) let it propagate and fail the run loudly,
    per this project's fail-loudly convention (exit non-zero, no partial
    write — see fetch.py's atomic_write)."""
    f = freshness(label, period, max_age_days, today)
    if f["stale"]:
        raise RuntimeError(
            f"freshness guard: {label} latest observation is {f['period']} "
            f"({f['age_days']}d old, today {today or _dt.date.today()}) — exceeds "
            f"the {max_age_days}d threshold for this series' cadence. The source "
            f"is likely dead or frozen, not just running a normal lag."
        )
    return f


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
    """Total reserves EXCLUDING gold as a percentage of nominal GDP."""
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


def reserves_incl_gold_pct_gdp(reserves_obs, reserves_units, gold_value_usd_monthly,
                               gdp_obs, gdp_units):
    """Total reserves INCLUDING gold at market value, as a percentage of GDP.

    `gold_value_usd_monthly` is a pre-computed {(y,m): USD} dict from
    gold.gold_market_value_usd() — gold holdings (troy oz) x a live price.
    Reconciles to Dalio's Ch.17 US figure (3% of GDP); reserves excl. gold
    alone (reserves_pct_gdp, above) understates this because the US holds a
    large gold stock that FRED's TRESEGUSM052N series excludes by definition.
    """
    res_m = as_monthly(reserves_obs)
    combined_m = {}
    for k in res_m.keys() & gold_value_usd_monthly.keys():
        combined_m[k] = to_dollars(res_m[k], reserves_units) + gold_value_usd_monthly[k]
    res_q = {}
    for (y, m), v in combined_m.items():
        res_q[(y, (m - 1) // 3 + 1)] = v
    gdp = as_quarterly(gdp_obs)
    ratio = {}
    for k in res_q.keys() & gdp.keys():
        denom = to_dollars(gdp[k], gdp_units)
        if denom:
            ratio[k] = res_q[k] / denom * 100.0
    if not ratio:
        raise RuntimeError("reserves_incl_gold_pct_gdp: no overlapping quarters")
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


def debt_to_revenue_pct(debt_pct_obs, gdp_obs, gdp_units, revenue_ttm_dollars):
    """Debt held by the public, as a percentage of trailing-12-month
    on-budget receipts — Dalio's Ch.3 preferred framing (debt against what
    government can actually collect, not against GDP, which it can't
    spend). No new series: debt$ = FYGFGDQ188S (%) x GDP ($); the quarterly
    debt stock is divided by revenue_ttm_dollars, a monthly {(y,m): $} TTM
    sum from treasury.py (collapsed to quarterly, last month of quarter) —
    the same trailing-12-month smoothing the debt-service rows use, since
    receipts swing far more with the tax calendar than GDP or the debt
    stock do. Same on-budget-receipts denominator as both debt-service
    rows (see provenance.revenueDefinition).
    """
    debt_pct_q = as_quarterly(debt_pct_obs)
    gdp_q = as_quarterly(gdp_obs)
    rev_q = {}
    for (y, m), v in revenue_ttm_dollars.items():
        rev_q[(y, (m - 1) // 3 + 1)] = v
    ratio = {}
    for k in debt_pct_q.keys() & gdp_q.keys() & rev_q.keys():
        gdp_usd = to_dollars(gdp_q[k], gdp_units)
        debt_usd = debt_pct_q[k] / 100.0 * gdp_usd
        if rev_q[k]:
            ratio[k] = debt_usd / rev_q[k] * 100.0
    if not ratio:
        raise RuntimeError("debt_to_revenue_pct: no overlapping quarters")
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
