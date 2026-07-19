#!/usr/bin/env python3
"""ONE-OFF DIAGNOSTIC — settle the drift question (see TASKdrifttest.md).

Not part of the build. Recomputes the debt-service / debt-to-revenue matrix
as a full-resolution monthly time series, 2023-01 to present, reusing the
exact numerator/denominator definitions already live in treasury.py and
series.py (no new definitions) but extended with a 4th denominator: CBO's
January 2025 baseline projected total receipts, by fiscal year, applied as
a flat FY/12 monthly step (same technique fetch.py already uses for the
FRED tax-receipts-only denominator's SAAR->monthly conversion).

CBO figures used (direct CBO access — cbo.gov, api.fiscaldata FRED, ALFRED —
is blocked by this session's egress policy; confirmed via
/root/.ccr/README.md's 403/CONNECT diagnostics, not retried per that
policy). Sourced from secondary reporting, cross-checked where possible:

  FY2025: $5,163B — VERIFIED (secondary): a CRFB-style figure appears twice
    independently as "$5.235T actual, $72B (1%) above the $5.163T baseline
    projection" — 5.235 - 0.072 = 5.163 exactly, internally consistent.
    Matches the task brief's own stated ~$5.163T.
  FY2026: $5,524B — ASSUMED: derived from "revenues increase by $361B (7%)
    in 2026" (361/5163 = 6.99% =~ 7%, consistent), not independently
    confirmed against a primary table. Flag accordingly in the write-up.
  FY2023/FY2024: no separate CBO figure used — for already-closed fiscal
    years the Jan-2025 baseline just carries the realised Treasury actual,
    so this script falls back to the same monthly_receipts() actuals used
    for the "total receipts" column. That fallback is itself a finding:
    the CBO-projected column is only informative from FY2025 (Oct 2024) on.

Discarded: a WebSearch synthesis that produced a full FY2023-2030 table
(2023: $4,441B, 2024: $5,082B, 2025: $5,485B, ...) — rejected because it
contradicts the two independently-corroborated numbers above (FY2025
should be $5,163B not $5,485B; FY2024 actual is well-documented near
$4.92T not $5,082B) and is very likely a search-model fabrication rather
than a quoted table. Not used anywhere below.
"""

from __future__ import annotations

import datetime as dt
import sys

import fetch as F
import series as S
import treasury as T

CBO_JAN2025_FY_TOTALS = {
    2025: 5_163e9,
    2026: 5_524e9,
}

WINDOW_START = (2023, 1)
CROSSING_WINDOW = ((2024, 1), (2025, 6))
MAR_2025 = (2025, 3)


def fy_of(ym):
    y, m = ym
    return y + 1 if m >= 10 else y


def build_cbo_projected_monthly(total_receipts_monthly: dict) -> dict:
    out = {}
    for ym, actual in total_receipts_monthly.items():
        fy = fy_of(ym)
        if fy in CBO_JAN2025_FY_TOTALS:
            out[ym] = CBO_JAN2025_FY_TOTALS[fy] / 12.0
        else:
            out[ym] = actual  # closed FY: baseline == realised actual
    return out


def ttm_series_full(numerator: dict, denominator: dict) -> dict:
    """Same TTM=12 trailing-sum ratio math as treasury._ttm_ratio, but keeps
    every month (not just calendar-quarter-end months) — needed to find
    crossing dates and slopes at monthly resolution."""
    months = sorted(set(numerator) & set(denominator))
    out = {}
    for i in range(T.TTM - 1, len(months)):
        window = months[i - T.TTM + 1: i + 1]
        num = sum(numerator[m] for m in window)
        den = sum(denominator[m] for m in window)
        if den:
            out[months[i]] = num / den * 100.0
    return out


def slice_window(series: dict, start=WINDOW_START):
    return {k: v for k, v in series.items() if k >= start}


def find_crossings(series: dict, target: float, lo, hi):
    months = sorted(m for m in series if lo <= m <= hi)
    crossings = []
    prev = None
    for m in months:
        v = series[m]
        if prev is not None:
            pm, pv = prev
            if (pv - target) == 0 or (pv - target) * (v - target) < 0:
                crossings.append(m)
        prev = (m, v)
    closest = min(months, key=lambda m: abs(series[m] - target)) if months else None
    return crossings, closest


def fmt_ym(ym):
    return f"{ym[0]}-{ym[1]:02d}"


def annual_slope(series: dict):
    months = sorted(series)
    if len(months) < 2:
        return None
    first, last = months[0], months[-1]
    years = (last[0] - first[0]) + (last[1] - first[1]) / 12.0
    if years <= 0:
        return None
    return (series[last] - series[first]) / years


def report_cell(label, series):
    win = slice_window(series)
    if not win:
        print(f"  {label:<48} unavailable")
        return
    mar25 = win.get(MAR_2025)
    today_k = max(win)
    today = win[today_k]
    lo, hi = min(win.values()), max(win.values())
    crossings, closest = find_crossings(win, 22.0, *CROSSING_WINDOW)
    slope = annual_slope(win)
    mar25_s = f"{mar25:.1f}%" if mar25 is not None else "n/a (no Mar-2025 point)"
    print(f"  {label}")
    print(f"    Mar-2025: {mar25_s}   today ({fmt_ym(today_k)}): {today:.1f}%   "
          f"min: {lo:.1f}%  max: {hi:.1f}%   slope: {slope:+.2f} pt/yr" if slope is not None else
          f"    Mar-2025: {mar25_s}   today ({fmt_ym(today_k)}): {today:.1f}%   min: {lo:.1f}%  max: {hi:.1f}%")
    if crossings:
        print(f"    crosses 22% in 2024-01..2025-06 at: {', '.join(fmt_ym(m) for m in crossings)}")
    else:
        cs = f"{series[closest]:.1f}% at {fmt_ym(closest)}" if closest else "n/a"
        print(f"    does not cross 22% in 2024-01..2025-06 — closest approach: {cs}")


def main():
    print("=" * 78)
    print("DRIFT TEST — matrix recomputed at book vintage (Mar-2025) + monthly, 2023-01..present")
    print(f"Run at {dt.datetime.now(dt.timezone.utc).isoformat()}")
    print("=" * 78)

    rows = T._interest_rows()
    numerators = {
        "gross (incl. GAS)": T.gross_interest_monthly(rows),
        "net-to-public (excl. GAS)": T.net_to_public_interest_monthly(rows),
        "net interest, fn900": T.net_interest_function900_monthly(),
    }

    t4rows = T._receipts_table4_rows()
    total_receipts = T.monthly_receipts(t4rows)
    on_budget = T.on_budget_receipts_monthly()
    cbo_projected = build_cbo_projected_monthly(total_receipts)

    tax_only = None
    try:
        units, obs = F.series_obs("W006RC1Q027SBEA")
        tax_only = F._quarterly_saar_to_monthly(obs, units)
    except Exception as e:  # noqa: BLE001
        print(f"tax-receipts-only denominator unavailable: {e}")

    denominators = {"on-budget receipts": on_budget, "total receipts": total_receipts,
                     "CBO Jan-2025 projected receipts": cbo_projected}
    if tax_only:
        denominators["tax receipts only"] = tax_only

    print("\nCBO Jan-2025 baseline FY totals used (see module docstring for sourcing/confidence):")
    for fy, v in sorted(CBO_JAN2025_FY_TOTALS.items()):
        print(f"  FY{fy}: ${v/1e9:.1f}B")

    print("\n--- 3 numerators x 4 denominators, monthly TTM ratio, 2023-01 -> present ---\n")
    for nlabel, nvals in numerators.items():
        if not nvals:
            print(f"{nlabel}: unavailable\n")
            continue
        print(f"{nlabel}:")
        for dlabel, dvals in denominators.items():
            if not dvals:
                print(f"  {dlabel:<48} unavailable")
                continue
            series = ttm_series_full(nvals, dvals)
            report_cell(dlabel, series)
        print()

    # --- debt_to_revenue trajectory against Dalio's ~580% anchor ---
    print("--- debt_to_revenue, quarterly, against Dalio's ~580% (Mar-2025) / ~700% (10yr) anchor ---\n")
    try:
        units, gdp_obs = F.series_obs("GDP")
        gdp_obs_ = gdp_obs
        gdp_units = units
        dunits, debt_obs = F.series_obs("FYGFGDQ188S")
        for dlabel, dvals in denominators.items():
            if not dvals:
                continue
            ttm_dollars = T._ttm_sum(dvals)
            if not ttm_dollars:
                print(f"  {dlabel:<48} unavailable (insufficient TTM overlap)")
                continue
            try:
                r = S.debt_to_revenue_pct(debt_obs, gdp_obs_, gdp_units, ttm_dollars)
            except Exception as e:  # noqa: BLE001
                print(f"  {dlabel:<48} FAILED: {e}")
                continue
            print(f"  {dlabel:<48} latest ({r['asOf']}): {r['latest']:.0f}%")
        # explicit Mar-2025 point + raw dollar cross-check ($28.9T claim)
        debt_q = S.as_quarterly(debt_obs)
        gdp_q = S.as_quarterly(gdp_obs_)
        q = (2025, 1)  # Mar-2025 falls in 2025-Q1
        if q in debt_q and q in gdp_q:
            debt_usd = debt_q[q] / 100.0 * S.to_dollars(gdp_q[q], gdp_units)
            print(f"\n  Debt held by public, 2025-Q1: ${debt_usd/1e12:.2f}T (task's stated estimate: ~$28.9T)")
            for dlabel, dvals in denominators.items():
                if not dvals:
                    continue
                ttm_dollars = T._ttm_sum(dvals)
                rq = {}
                for (yy, mm), v in ttm_dollars.items():
                    rq[(yy, (mm - 1) // 3 + 1)] = v
                if q in rq:
                    print(f"    {dlabel}: TTM ${rq[q]/1e12:.2f}T -> debt/revenue "
                          f"{debt_usd/rq[q]*100:.0f}%")
    except Exception as e:  # noqa: BLE001
        print(f"  debt_to_revenue comparison FAILED: {e}")

    print("\n--- known partial result cross-check (net interest / total receipts, TTM) ---")
    net_total = ttm_series_full(numerators["net-to-public (excl. GAS)"], total_receipts)
    if MAR_2025 in net_total:
        print(f"  Mar-2025: {net_total[MAR_2025]:.1f}% (task's stated estimate: ~18.9%)")
    if net_total:
        today_k = max(net_total)
        print(f"  today ({fmt_ym(today_k)}): {net_total[today_k]:.1f}% (task's stated estimate: ~17.9%)")

    print("\n--- FY2024 gross interest / CBO FY2025-projected receipts hypothesis ---")
    gross = numerators["gross (incl. GAS)"]
    fy2024_months = [(y, m) for (y, m) in gross if fy_of((y, m)) == 2024]
    if len(fy2024_months) == 12:
        fy2024_gross = sum(gross[m] for m in fy2024_months)
        cbo_fy2025 = CBO_JAN2025_FY_TOTALS[2025]
        print(f"  FY2024 gross interest (actual, summed): ${fy2024_gross/1e9:.1f}B "
              f"(task's stated estimate: ~$1,126.5B)")
        print(f"  / CBO Jan-2025 FY2025 projected receipts ${cbo_fy2025/1e9:.1f}B "
              f"= {fy2024_gross/cbo_fy2025*100:.1f}% (task's stated estimate: ~21.8%)")
    else:
        print(f"  FY2024 incomplete in fetched data ({len(fy2024_months)}/12 months) — skipping")

    print("\nDone.")


if __name__ == "__main__":
    sys.exit(main())
