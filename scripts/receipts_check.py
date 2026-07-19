#!/usr/bin/env python3
"""ONE-OFF DIAGNOSTIC — gross vs net receipts (see TASKreceiptsdenominator.md).

Not part of the build. mts_table_4 exposes three amount fields per row:
current_month_gross_rcpt_amt, current_month_refund_amt,
current_month_net_rcpt_amt (confirmed in docs/review/2026-07-19c-verification.md's
schema dump). treasury.py's monthly_receipts()/off_budget_receipts_monthly()
currently sum the GROSS field (see _pick's candidate-name order). This script
checks that choice against CBO's independently published FY2024/FY2025 totals.
"""

from __future__ import annotations

import datetime as dt

import treasury as T

# CBO published FY totals — FY2024 already cited in STATUS.md §10.2 (GAO/CBO
# cross-check); FY2025 from CBO's Nov-2025 "Summary for Fiscal Year 2025"
# Monthly Budget Review, cross-checked across two independent WebSearch
# results ($5.235T actual, "$72B/1% above the $5.163T Jan-2025 baseline";
# separately, "+$317B/6% over FY2024" -> 4.92 + 0.317 = 5.237, consistent).
CBO_FY_TOTALS = {2024: 4.92e12, 2025: 5.235e12}

MAR_2025 = (2025, 3)


def _field_keys(rows):
    s = rows[0]
    keys = {
        "gross": "current_month_gross_rcpt_amt",
        "refund": "current_month_refund_amt",
        "net": "current_month_net_rcpt_amt",
    }
    for label, k in keys.items():
        if k not in s:
            raise RuntimeError(f"field {k} ({label}) not in mts_table_4 sample row: {list(s)}")
    return keys


def monthly_receipts_basis(rows, classk, amtk):
    """Same grand-total-row detection as treasury.monthly_receipts(), but
    parameterised on which amount field to sum."""
    out = {}
    for row in rows:
        if T._is_total_receipts(str(row.get(classk, ""))):
            amt = T._num(row.get(amtk))
            if amt is not None:
                ym = T._ym(row["record_date"])
                out[ym] = max(out.get(ym, 0.0), amt)
    return out


def off_budget_basis(rows, classk, amtk):
    monthly, matched = {}, set()
    for row in rows:
        desc = str(row.get(classk, "")).strip().lower()
        if desc in T._OFF_BUDGET_FUND_LABELS:
            amt = T._num(row.get(amtk))
            if amt is not None:
                ym = T._ym(row["record_date"])
                monthly[ym] = monthly.get(ym, 0.0) + amt
                matched.add(desc)
    if len(matched) < len(T._OFF_BUDGET_FUND_LABELS):
        return None
    return monthly


def fy_sum(monthly, fy):
    months = [(y, m) for (y, m) in monthly if (y + 1 if m >= 10 else y) == fy]
    if len(months) != 12:
        return None, len(months)
    return sum(monthly[m] for m in months), 12


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


def main():
    print("=" * 78)
    print("RECEIPTS CHECK — gross vs net (TASKreceiptsdenominator.md)")
    print(f"Run at {dt.datetime.now(dt.timezone.utc).isoformat()}")
    print("=" * 78)

    rows = T._receipts_table4_rows()
    keys = _field_keys(rows)
    classk = T._pick(rows[0], ["classification_desc"], contains=["classification", "desc"])

    print("\nField mapping confirmed in mts_table_4 sample row:")
    for label, k in keys.items():
        print(f"  {label}: {k}")

    pipeline_field = T._pick(rows[0], ["current_month_gross_rcpt_amt", "current_month_rcpt_amt"],
                              contains=["month", "rcpt", "amt"],
                              exclude=["fytd", "prior", "year", "outly", "dfct"])
    print(f"\nmonthly_receipts() currently sums: {pipeline_field}")

    latest_date = max(r["record_date"] for r in rows)
    print(f"\nTotal-receipts grand-total row, latest month ({latest_date}):")
    for row in rows:
        if row["record_date"] == latest_date and T._is_total_receipts(str(row.get(classk, ""))):
            g = T._num(row.get(keys["gross"]))
            rf = T._num(row.get(keys["refund"]))
            n = T._num(row.get(keys["net"]))
            gr = None if g is None or rf is None else g - rf
            print(f"  classification_desc: {row.get(classk)!r}")
            print(f"  gross={g}  refund={rf}  net={n}  gross-refund={gr}")

    gross_monthly = monthly_receipts_basis(rows, classk, keys["gross"])
    net_monthly = monthly_receipts_basis(rows, classk, keys["net"])
    off_gross = off_budget_basis(rows, classk, keys["gross"])
    off_net = off_budget_basis(rows, classk, keys["net"])

    print("\n--- FY totals: gross vs net vs CBO published ---")
    for fy in (2024, 2025):
        g, ng = fy_sum(gross_monthly, fy)
        n, nn = fy_sum(net_monthly, fy)
        cbo = CBO_FY_TOTALS[fy]
        print(f"\nFY{fy} (gross months={ng}, net months={nn}), CBO published: ${cbo/1e12:.3f}T")
        if g is not None:
            print(f"  gross total: ${g/1e12:.3f}T  residual {((g - cbo) / cbo * 100):+.1f}%")
        else:
            print("  gross total: incomplete FY in fetched data")
        if n is not None:
            print(f"  net total:   ${n/1e12:.3f}T  residual {((n - cbo) / cbo * 100):+.1f}%")
        else:
            print("  net total: incomplete FY in fetched data")

    print("\n--- on-budget receipts (total minus OASI+DI), latest overlapping month, both bases ---")
    if off_gross and off_net:
        for label, total_m, off_m in (("gross (current)", gross_monthly, off_gross),
                                       ("net (proposed)", net_monthly, off_net)):
            ob = {k: total_m[k] - off_m[k] for k in total_m.keys() & off_m.keys()}
            if ob:
                last = max(ob)
                print(f"  {label:<16} latest {last[0]}-{last[1]:02d} = ${ob[last]/1e9:.1f}B")
    else:
        print("  off-budget unavailable on one or both bases")

    print("\n--- effect on shipped debt-service ratios: gross-basis vs net-basis receipts, TTM ---")
    interest_rows = T._interest_rows()
    numerators = {
        "gross interest": T.gross_interest_monthly(interest_rows),
        "net-to-public interest": T.net_to_public_interest_monthly(interest_rows),
    }
    denominators = {"total receipts (gross, current)": gross_monthly,
                     "total receipts (net, proposed)": net_monthly}
    if off_gross:
        denominators["on-budget (gross, current)"] = {
            k: gross_monthly[k] - off_gross[k] for k in gross_monthly.keys() & off_gross.keys()}
    if off_net:
        denominators["on-budget (net, proposed)"] = {
            k: net_monthly[k] - off_net[k] for k in net_monthly.keys() & off_net.keys()}

    for nlabel, nvals in numerators.items():
        print(f"\n{nlabel}:")
        for dlabel, dvals in denominators.items():
            series = ttm_series_full(nvals, dvals)
            mar25 = series.get(MAR_2025)
            today_k = max(series) if series else None
            today = series.get(today_k) if today_k else None
            if mar25 is None or today is None:
                print(f"  {dlabel:<32} incomplete")
                continue
            print(f"  {dlabel:<32} Mar-2025: {mar25:.1f}%   today ({today_k[0]}-{today_k[1]:02d}): {today:.1f}%")

    print("\nDone.")


if __name__ == "__main__":
    main()
