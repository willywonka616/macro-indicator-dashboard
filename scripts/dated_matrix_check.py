#!/usr/bin/env python3
"""ONE-OFF DIAGNOSTIC — two properly-dated grids (Mar-2025 and today), on the
corrected net-of-refunds receipts basis, printed side by side in the same
numerator x denominator grid layout treasury.py's verify() uses (which only
prints latest-TTM values under a misleading "Mar 2025" header — fixed
separately in treasury.py, see STATUS.md §15). Reuses the round-c
(TASKdrifttest.md) drift_test.py logic, not re-derived.

Not part of the build. Confirms or revises STATUS.md §13's conclusion with
unambiguous, correctly-labelled evidence.
"""

from __future__ import annotations

import datetime as dt

import fetch as F
import treasury as T

CBO_JAN2025_FY_TOTALS = {2025: 5_163e9, 2026: 5_524e9}
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


def print_grid(title, numerators, denominators, at_month):
    print(f"\n  {title}")
    den_labels = list(denominators)
    print(f"  {'numerator':<30}" + "".join(f"{d:>22}" for d in den_labels))
    for nlabel, nvals in numerators.items():
        cells = []
        for dlabel in den_labels:
            dvals = denominators[dlabel]
            series = ttm_series_full(nvals, dvals) if nvals else {}
            if at_month == "latest":
                key = max(series) if series else None
            else:
                key = at_month if at_month in series else None
            cells.append(f"{series[key]:.1f}%" if key is not None else "n/a")
        print(f"  {nlabel:<30}" + "".join(f"{c:>22}" for c in cells))


def main():
    print("=" * 78)
    print("DATED MATRIX CHECK — Mar-2025 vs today, corrected (net) receipts basis")
    print(f"Run at {dt.datetime.now(dt.timezone.utc).isoformat()}")
    print("=" * 78)

    rows = T._interest_rows()
    numerators = {
        "gross (incl. GAS)": T.gross_interest_monthly(rows),
        "net-to-public (excl. GAS)": T.net_to_public_interest_monthly(rows),
        "net interest, fn900": T.net_interest_function900_monthly(),
    }
    total = T.monthly_receipts()
    on_budget = T.on_budget_receipts_monthly()
    tax_only = None
    try:
        units, obs = F.series_obs("W006RC1Q027SBEA")
        tax_only = F._quarterly_saar_to_monthly(obs, units)
    except Exception as e:  # noqa: BLE001
        print(f"tax-receipts-only denominator unavailable: {e}")
    cbo_projected = build_cbo_projected_monthly(total)

    denominators = {"total receipts": total}
    if on_budget:
        denominators["on-budget receipts"] = on_budget
    if tax_only:
        denominators["tax receipts only"] = tax_only
    denominators["CBO Jan-2025 projected"] = cbo_projected

    print_grid("GRID 1 of 2 — AT MARCH 2025 (Dalio's stated vintage), TTM ending 2025-03:",
                numerators, denominators, MAR_2025)
    print_grid("GRID 2 of 2 — AT TODAY (latest available TTM):",
                numerators, denominators, "latest")

    # find the actual "today" month used, for the record
    any_series = ttm_series_full(numerators["gross (incl. GAS)"], denominators["total receipts"])
    if any_series:
        latest = max(any_series)
        print(f"\n  'today' = {latest[0]}-{latest[1]:02d} (TTM window ending that month)")

    print("\nDone.")


if __name__ == "__main__":
    main()
