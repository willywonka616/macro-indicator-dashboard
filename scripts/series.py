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
    # 220d, not the ~5 months a naive "quarterly" guess suggests: FRED dates
    # quarterly macro series (GDP, FYGFGDQ188S, TCMDO, IEABC) to the START
    # of the quarter, not the release date. Right before the NEXT quarter's
    # release, a perfectly healthy series is legitimately ~200 days past its
    # own date-stamp (observed live: 2026-01-01 at 200d old, still current,
    # the morning before the Q2 print — see docs/review/). 220d gives a
    # little headroom above that observed real-world maximum.
    "Quarterly": 220,
    "Annual": 400,
}

# IMF COFER publishes quarterly but is documented as running "a quarter or
# two" behind even when healthy (imf.py's own docstring) — a longer
# legitimate lag than the generic Quarterly threshold above allows for, so
# it gets its own explicit threshold rather than being exempted outright
# (TASKgoldpricefreshness.md: "set the threshold to match" the known lag,
# don't just skip the check). Even at 270d (~9 months, well past "a quarter
# or two"), COFER still failed this live (565d, frozen at 2025-Q1) — a
# second genuinely frozen source, not a threshold-calibration artifact.
COFER_FRESH_DAYS = 270

# TRESEGUSM052N ("Total Reserves excluding Gold") is IMF/BOP-sourced
# international reserves data, not a domestic FRED series — it runs a
# real, longer lag than CPI/DGS10 even when healthy (observed live: 141d,
# still the genuinely latest print). Its own threshold, same reasoning as
# COFER above, rather than the generic 60d Monthly bucket which is
# calibrated to domestic series like CPIAUCSL.
TRESEGUS_FRESH_DAYS = 180

# --- manual-value freshness (STATUS.md §19) -------------------------------
#
# A hand-entered value with a date is exactly as capable of going stale as
# a fetched one — the freshness guard above only ever checked FETCHED
# series. These thresholds extend the same idea to data/manual.json's own
# dated fields, which are just as capable of silently drifting out of date
# once nobody's looking. Unlike require_fresh() (which raises and kills the
# build for a dead LIVE source with a healthy fallback available), staleness
# here is checked with the non-raising `freshness()` and only WARNED on —
# these values are already the fallback of last resort; failing the build
# over their own staleness would take the whole site down over a metadata
# gap, the opposite of "degrade rather than break" (see fetch.py's gold/
# COFER fallback comments). The warning must still be impossible to miss —
# see fetch.py's loud_warn(), which emits both a console banner and a
# GitHub Actions ::warning:: annotation.

# The manual gold price stands in for a live monthly source — it should be
# reviewed at least as often as that source would naturally update, so it
# gets the same cadence as the live Monthly threshold it replaces, not a
# longer one.
GOLD_MANUAL_PRICE_FRESH_DAYS = FRESHNESS_DAYS_BY_FREQ["Monthly"]

# manual.json's `reserveCurrency.cbReserves` is a hand-entered snapshot of
# the same IMF COFER series COFER_FRESH_DAYS already governs — same cadence
# reasoning applies when it's the one actually shipped (COFER's live fetch
# failed and this manual snapshot is standing in for it).
CBRESERVES_MANUAL_FRESH_DAYS = COFER_FRESH_DAYS

# The catch-all: manual.json's top-level `lastChecked` is the implicit date
# for every manual value that has no `asOf` of its own (most of them — see
# STATUS.md §19 for the full audit of which). 180d (~6 months) is a review
# cadence, not a data cadence — these are mostly slow-moving context figures
# (TIC holder shares, CBO's projection, market-cap shares), so this exists
# to catch "nobody has looked at manual.json in a long time," not to imply
# the underlying figures update on any particular schedule.
MANUAL_FRESH_DAYS = 180


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


def quarterly_last(monthly: dict) -> dict:
    """{(y,m): value} -> {(y,q): value}, keeping the value from the LATEST
    month actually present in each quarter — chosen explicitly by
    comparing month numbers, not by dict iteration order.

    2026-07-22 bug fix: `reserves_incl_gold_pct_gdp` and `real_10y_rate`
    used to bucket a monthly dict into quarters by iterating `.items()`
    and unconditionally overwriting `out[(y,q)] = v` for every month
    seen — correct ONLY if that iteration order happens to be
    chronological. It reliably was for a dict built directly from an
    ascending `[(date, value)]` list (insertion order = calendar order),
    but NOT for a dict built from a SET INTERSECTION of two other dicts'
    keys (`a.keys() & b.keys()`) — Python does not guarantee that
    iterates in any particular order, let alone calendar order. Confirmed
    live and reproduced locally: for a real 2026-Q1 key set, this
    silently picked January over the intended March in every case
    tested, regardless of which underlying source dict was used — a
    real correctness bug, not a source-freshness or GDP-vintage issue
    (see STATUS.md §25). Every quarter-bucketing call site now goes
    through this one deterministic function instead of re-implementing
    the same fold inline, so this class of bug can't recur silently.
    """
    best_month = {}
    out = {}
    for (y, m), v in monthly.items():
        q = (y, (m - 1) // 3 + 1)
        if q not in best_month or m > best_month[q]:
            best_month[q] = m
            out[q] = v
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
    res_q = quarterly_last(res_m)  # collapse monthly reserves to quarterly (last month of quarter present)
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
    res_q = quarterly_last(combined_m)
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


def tic_holder_shares(total_obs, total_units, fed_obs, fed_units, foreign_obs, foreign_units):
    """TASKmanualvalues.md — replaces the undated `holders.*` manual shares
    (13% / 57% / 29%) with a live three-way split of Federal Debt Held by
    the Public: central bank (Fed/SOMA), foreign, and domestic (the
    residual). All three inputs are FRED aliases of the SAME underlying
    Treasury Fiscal Service table (OFS-1, "Distribution of Federal
    Securities by Class of Investors") — not a TIC scrape, a cleaner
    same-source path found by checking rather than assuming the task's
    brief (which pointed at ticdata.treasury.gov directly):
      - `FYGFDPUN` — Federal Debt Held by the Public (the denominator)
      - `FDHBFRBN` — Federal Debt Held by Federal Reserve Banks (central bank)
      - `FDHBFIN`  — Federal Debt Held by Foreign and International Investors
    `domestic` is computed as the residual (100 - central - foreign), per
    the task's own instruction, not fetched as its own series (there
    isn't one — "domestic, non-Fed" is definitionally a residual, not a
    directly published figure).
    """
    total = as_quarterly(total_obs)
    fed = as_quarterly(fed_obs)
    foreign = as_quarterly(foreign_obs)
    central_h, domestic_h, foreign_h = {}, {}, {}
    for k in total.keys() & fed.keys() & foreign.keys():
        denom = to_dollars(total[k], total_units)
        if not denom:
            continue
        central_pct = to_dollars(fed[k], fed_units) / denom * 100.0
        foreign_pct = to_dollars(foreign[k], foreign_units) / denom * 100.0
        central_h[k] = central_pct
        foreign_h[k] = foreign_pct
        domestic_h[k] = 100.0 - central_pct - foreign_pct
    if not central_h:
        raise RuntimeError("tic_holder_shares: no overlapping quarters across all three series")
    c_latest, asof = _latest(central_h)
    f_latest, _ = _latest(foreign_h)
    d_latest, _ = _latest(domestic_h)
    return {
        "asOf": asof,
        "centralBank": {"latest": round(c_latest, 1), "history": quarterly_history(central_h)},
        "domestic": {"latest": round(d_latest, 1), "history": quarterly_history(domestic_h)},
        "abroad": {"latest": round(f_latest, 1), "history": quarterly_history(foreign_h)},
    }


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
    # revenue_ttm_dollars is already chronologically ordered (built via
    # sorted() in treasury.py's _ttm_sum), so this was never actually
    # exposed to the quarterly_last() bug — routed through it anyway for
    # defense-in-depth, so correctness here doesn't depend on that
    # invariant holding forever in treasury.py.
    rev_q = quarterly_last(revenue_ttm_dollars)
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
    real_q = quarterly_last(real)  # collapse to quarterly for display / latest
    latest, asof = _latest(real_q)
    return {"latest": round(latest, 2), "asOf": asof, "history": quarterly_history(real_q)}


# --- CBO projections (TASKprojections.md) --------------------------------
# Every function below reads only CBO's own published baseline (see
# cbo.py) — no extrapolation, no fitted models, no scenario output. A
# fiscal-year point is placed at FY + 8/12 (~Sept 30, the federal fiscal
# year-end) so it lines up sensibly on the same decimal-year x-axis as the
# calendar-quarter live series it extends.

def _fy_decimal(fy: int) -> float:
    return round(fy + 8 / 12.0, 3)


def cbo_gdp_share_series(cbo_data: dict, field_key: str, projected_only: bool = True) -> list:
    """[{"y", "v", "projected": True}, ...] from a CBO `*_gdp_share` field
    (already a percentage of GDP — CBO publishes the ratio directly, no
    division needed here). `projected_only=True` (the default) skips the
    vintage's own first fiscal year, which schema.json documents as
    "actual (realized)," not a CBO projection — that year overlaps what
    the live FRED-sourced series already shows, so including it here
    would be a duplicate point, not a genuine extension."""
    series = cbo_data[field_key]
    fy_min = cbo_data["fyMin"]
    return [
        {"y": _fy_decimal(fy), "v": round(series[fy], 2), "projected": True}
        for fy in sorted(series) if not (projected_only and fy <= fy_min)
    ]


def cbo_dollar_ratio_series(cbo_data: dict, numerator_key: str, denominator_key: str,
                             projected_only: bool = True) -> list:
    """Same shape as cbo_gdp_share_series, for a ratio of two CBO
    dollar-level fields that CBO doesn't already publish as its own
    `*_gdp_share` field — e.g. debt held by the public ÷ total revenue,
    Dalio's Ch.3-preferred debt/revenue framing, which CBO's own tables
    don't carry as a single published ratio."""
    num, den = cbo_data[numerator_key], cbo_data[denominator_key]
    fy_min = cbo_data["fyMin"]
    out = []
    for fy in sorted(num.keys() & den.keys()):
        if projected_only and fy <= fy_min:
            continue
        if den[fy]:
            out.append({"y": _fy_decimal(fy), "v": round(num[fy] / den[fy] * 100.0, 2), "projected": True})
    return out


def interest_rate_to_keep_debt_flat(cbo_data: dict) -> dict:
    """Dalio's Ch.3 equation #3 — computed for every projected fiscal year
    in CBO's baseline, entirely from CBO's own published figures:

        i_required = Revenue Growth
                     − (Future Expenses Excl. Interest − Future Revenue)
                       ─────────────────────────────────────────────────
                                    Starting Debt Level

    "Future Expenses Excl. Interest − Future Revenue" is CBO's own
    `proj_primary_deficit`, sign-flipped (that field is negative for a
    deficit; verified live to equal exactly
    `outlays_total − outlays_net_interest − rev_total`, to the dollar, in
    every fiscal year checked — see STATUS.md). "Starting Debt Level" is
    CBO's own `proj_debt_held_by_public_begin`, not a prior-year lookup
    into `proj_debt_held_by_public` — avoids an off-by-one at the first
    projected year and uses the field CBO itself designed for this. Every
    term is CBO's baseline; nothing here is fitted, extrapolated, or a
    scenario output (TASKprojections.md §1: "Do not build: our own
    forecasts").

    Diagnostic by design (TASKprojections.md §1): the caller compares this
    series against the ACTUAL average effective rate on the debt
    (treasury.avg_interest_rate_marketable(), live) — the gap between them
    is "how far from stabilising the debt currently is," Dalio's own
    framing (i = g keeps debt flat with no primary deficit).

    "Revenue Growth" (TASKequation3growth.md) is genuinely REVENUE growth
    — `growth` below is computed from `cbo_data["rev_total"]`
    (CBO's own `proj_rev_total`), NOT nominal GDP growth. Confirmed live
    (2026-07, 2026-02 vintage): FY2026 revenue $5,595.9B / FY2025's
    $5,234.6B − 1 = 6.90%, matching Dalio's Ch.3 definition (debt measured
    against income/revenue, the same basis the debt/revenue row uses) —
    not GDP, which this pipeline doesn't even carry a raw dollar level
    for (CBO's own dataset publishes GDP only as a `*_gdp_share` ratio of
    other fields, never as its own level). This distinction matters under
    CBO's current-law baseline specifically: expiring tax provisions are
    assumed to lapse, which raises projected revenue faster than
    projected GDP for a stretch of years, so the two growth rates
    genuinely diverge here, not just in principle.
    """
    fy_min, fy_max = cbo_data["fyMin"], cbo_data["fyMax"]
    rev = cbo_data["rev_total"]
    begin_debt = cbo_data["debt_held_by_public_begin"]
    primary_deficit = cbo_data["primary_deficit"]
    out = []
    for fy in range(fy_min + 1, fy_max + 1):
        if fy not in rev or (fy - 1) not in rev or fy not in begin_debt or fy not in primary_deficit:
            continue
        growth = (rev[fy] / rev[fy - 1] - 1.0) * 100.0
        gap = -primary_deficit[fy] / begin_debt[fy] * 100.0  # (expenses excl. interest − revenue) / starting debt
        out.append({"y": _fy_decimal(fy), "v": round(growth - gap, 2), "projected": True})
    if not out:
        raise RuntimeError("interest_rate_to_keep_debt_flat: no computable fiscal years")
    return {"history": out}
