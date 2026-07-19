#!/usr/bin/env python3
"""ONE-OFF DIAGNOSTIC — full re-run of the drift matrix on the corrected
(net-of-refunds, TOTAL) receipts basis, after fixing the gross/net field
bug in treasury.py (see TASKreceiptsdenominator.md, STATUS.md §13).

Not part of the build. Confirms treasury.py's fix directly (monthly_receipts()
now sums current_month_net_rcpt_amt), then recomputes the 3-numerator x
4-denominator matrix (same structure as the prior drift-test round, see
docs/review/2026-07-19c-verification.md) and debt_to_revenue on all four
denominators, on the corrected basis.
"""

from __future__ import annotations

import datetime as dt

import fetch as F
import series as S
import treasury as T

CBO_JAN2025_FY_TOTALS = {2025: 5_163e9, 2026: 5_524e9}
CBO_FY_ACTUALS = {2024: 4.92e12, 2025: 5.235e12}

WINDOW_START = (2023, 1)
MAR_2025 = (2025, 3)


def fy_of(ym):
    y, m = ym
    return y + 1 if m >= 10 else y


def build_cbo_projected_monthly(total_receipts_monthly: dict) -> dict:
    out = {}
    for ym, actual in total_receipts_monthly.items():
        fy = fy_of(ym)
        out[ym] = CBO_JAN2025_FY_TOTALS[fy] / 12.0 if fy in CBO_JAN2025_FY_TOTALS else actual
    return out


def fy_sum(monthly, fy):
    months = [ym for ym in monthly if fy_of(ym) == fy]
    if len(months) != 12:
        return None
    return sum(monthly[m] for m in months)


def ttm_series_full(numerator, denominator):
    months = sorted(set(numerator) & set(denominator))
    out = {}
    for i in range(T.TTM - 1, len(months)):
        window = months[i - T.TTM + 1: i + 1]
        num = sum(numerator[m] for m in window)
        den = sum(denominator[m] for m in window)
        if den:
            out[months[i]] = num / den * 100.0
    return out


def report_cell(label, series):
    win = {k: v for k, v in series.items() if k >= WINDOW_START}
    if not win:
        print(f"  {label:<40} unavailable")
        return
    mar25 = win.get(MAR_2025)
    today_k = max(win)
    today = win[today_k]
    mar25_s = f"{mar25:.1f}%" if mar25 is not None else "n/a"
    print(f"  {label:<40} Mar-2025: {mar25_s}   today ({today_k[0]}-{today_k[1]:02d}): {today:.1f}%")


def main():
    print("=" * 78)
    print("BASIS RE-CHECK — corrected (net, total) receipts, full matrix")
    print(f"Run at {dt.datetime.now(dt.timezone.utc).isoformat()}")
    print("=" * 78)

    total = T.monthly_receipts()
    on_budget = T.on_budget_receipts_monthly()

    print("\n--- confirm the fix: monthly_receipts() FY totals vs CBO published ---")
    for fy in (2024, 2025):
        s = fy_sum(total, fy)
        cbo = CBO_FY_ACTUALS[fy]
        if s is None:
            print(f"  FY{fy}: incomplete in fetched data")
            continue
        print(f"  FY{fy}: ${s/1e12:.3f}T vs CBO ${cbo/1e12:.3f}T  residual {((s-cbo)/cbo*100):+.2f}%")

    rows = T._interest_rows()
    numerators = {
        "gross (incl. GAS)": T.gross_interest_monthly(rows),
        "net-to-public (excl. GAS)": T.net_to_public_interest_monthly(rows),
        "net interest, fn900": T.net_interest_function900_monthly(),
    }

    tax_only = None
    try:
        units, obs = F.series_obs("W006RC1Q027SBEA")
        tax_only = F._quarterly_saar_to_monthly(obs, units)
    except Exception as e:  # noqa: BLE001
        print(f"\ntax-receipts-only denominator unavailable: {e}")

    cbo_projected = build_cbo_projected_monthly(total)

    denominators = {"total receipts (net, shipped)": total}
    if on_budget:
        denominators["on-budget receipts (net, diagnostic)"] = on_budget
    if tax_only:
        denominators["tax receipts only"] = tax_only
    denominators["CBO Jan-2025 projected receipts"] = cbo_projected

    print("\n--- 3 numerators x 4 denominators, monthly TTM, corrected basis ---\n")
    for nlabel, nvals in numerators.items():
        if not nvals:
            print(f"{nlabel}: unavailable\n")
            continue
        print(f"{nlabel}:")
        for dlabel, dvals in denominators.items():
            series = ttm_series_full(nvals, dvals)
            report_cell(dlabel, series)
        print()

    print("--- debt_to_revenue, quarterly, all four denominators, corrected basis ---\n")
    try:
        gdp_units, gdp_obs = F.series_obs("GDP")
        dunits, debt_obs = F.series_obs("FYGFGDQ188S")
        for dlabel, dvals in denominators.items():
            ttm_dollars = T._ttm_sum(dvals)
            if not ttm_dollars:
                print(f"  {dlabel:<40} unavailable")
                continue
            try:
                r = S.debt_to_revenue_pct(debt_obs, gdp_obs, gdp_units, ttm_dollars)
                print(f"  {dlabel:<40} latest ({r['asOf']}): {r['latest']:.0f}%")
            except Exception as e:  # noqa: BLE001
                print(f"  {dlabel:<40} FAILED: {e}")

        debt_q = S.as_quarterly(debt_obs)
        gdp_q = S.as_quarterly(gdp_obs)
        q = (2025, 1)
        if q in debt_q and q in gdp_q:
            debt_usd = debt_q[q] / 100.0 * S.to_dollars(gdp_q[q], gdp_units)
            print(f"\n  Debt held by public, 2025-Q1: ${debt_usd/1e12:.2f}T "
                  f"(Dalio's stated ~$28.9T, ~580% anchor)")
            for dlabel, dvals in denominators.items():
                ttm_dollars = T._ttm_sum(dvals)
                rq = {}
                for (yy, mm), v in ttm_dollars.items():
                    rq[(yy, (mm - 1) // 3 + 1)] = v
                if q in rq:
                    print(f"    {dlabel}: TTM ${rq[q]/1e12:.2f}T -> debt/revenue "
                          f"{debt_usd/rq[q]*100:.0f}%")
    except Exception as e:  # noqa: BLE001
        print(f"  debt_to_revenue comparison FAILED: {e}")

    print("\n--- shipped ratios (treasury.py functions directly) ---")
    try:
        r = T.debt_service_ratio()
        print(f"  debt_service_ratio() [headline, net/total]: {r['latest']}% as of {r['asOf']}")
        rg = T.gross_debt_service_ratio()
        print(f"  gross_debt_service_ratio() [second row, gross/total]: {rg['latest']}% as of {rg['asOf']}")
    except Exception as e:  # noqa: BLE001
        print(f"  FAILED: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
