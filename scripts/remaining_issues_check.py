#!/usr/bin/env python3
"""ONE-OFF DIAGNOSTIC for TASKremainingissues.md items 1, 3, 4.

Not part of the build. Three independent checks:
  1. Drift matrix (3 numerators x 4 denominators) on the corrected
     net-of-refunds receipts basis, at Mar-2025 and today.
  2. Gold-price staleness: try querying IMF's own SDMX 3.0 API for PCPS
     directly (not via DBnomics) to see whether IMF itself has newer data
     than DBnomics' mirror, or whether both stop at the same point.
  3. Total-debt "other debt" hypothesis: TCMDO % of GDP minus government
     debt % of GDP (a "non-government debt" proxy), against Dalio's 340%.
"""

from __future__ import annotations

import datetime as dt
import json

import requests

import fetch as F
import series as S
import treasury as T
import gold as G

CBO_JAN2025_FY_TOTALS = {2025: 5_163e9, 2026: 5_524e9}
WINDOW_START = (2023, 1)
MAR_2025 = (2025, 3)


# --- 1. drift matrix, corrected basis --------------------------------------

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


def section_1_matrix():
    print("=" * 78)
    print("1. DRIFT MATRIX, corrected (net-of-refunds) receipts basis")
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

    denominators = {"total (net, shipped)": total}
    if on_budget:
        denominators["on-budget (net, diagnostic)"] = on_budget
    if tax_only:
        denominators["tax receipts only"] = tax_only
    denominators["CBO Jan-2025 projected"] = cbo_projected

    for nlabel, nvals in numerators.items():
        if not nvals:
            print(f"{nlabel}: unavailable\n")
            continue
        print(f"\n{nlabel}:")
        for dlabel, dvals in denominators.items():
            report_cell(dlabel, ttm_series_full(nvals, dvals))

    print("\nShipped ratios (treasury.py functions directly):")
    try:
        r = T.debt_service_ratio()
        print(f"  debt_service_ratio() [headline]: {r['latest']}% as of {r['asOf']}")
        rg = T.gross_debt_service_ratio()
        print(f"  gross_debt_service_ratio() [second row]: {rg['latest']}% as of {rg['asOf']}")
    except Exception as e:  # noqa: BLE001
        print(f"  FAILED: {e}")
    print()


# --- 2. gold staleness: IMF direct vs DBnomics mirror -----------------------

IMF_CANDIDATES = [
    ("api.imf.org SDMX 3.0 (IMF.RES/PCPS, JSON accept)",
     "https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.RES/PCPS/+/M.W00.PGOLD.USD",
     {"c[TIME_PERIOD]": "ge:2024-01"},
     {"Accept": "application/vnd.sdmx.data+json;version=2.0.0"}),
    ("api.imf.org SDMX 3.0 (IMF.RES/PCPS, default accept)",
     "https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.RES/PCPS/+/M.W00.PGOLD.USD",
     {"c[TIME_PERIOD]": "ge:2024-01"},
     {}),
    ("api.imf.org SDMX 3.0 structure probe (dataflow exists?)",
     "https://api.imf.org/external/sdmx/3.0/structure/dataflow/IMF.RES/PCPS",
     {}, {}),
    ("sdmxcentral.imf.org SDMX 2.1 (legacy)",
     "https://sdmxcentral.imf.org/ws/public/sdmxapi/rest/data/IMF,PCPS,1.0/M.W00.PGOLD.USD",
     {"startPeriod": "2024-01"}, {}),
]


def section_2_gold_staleness():
    print("=" * 78)
    print("2. GOLD STALENESS: querying IMF's own PCPS API directly (not via DBnomics)")
    print("=" * 78)

    print("\nDBnomics mirror (current pipeline source), latest observation:")
    try:
        price = G.gold_price_usd_per_oz()
        last = max(price)
        print(f"  latest via DBnomics: {last[0]}-{last[1]:02d} = {price[last]} USD/oz "
              f"({len(price)} observations)")
        dbnomics_latest = last
    except Exception as e:  # noqa: BLE001
        print(f"  FAILED: {e}")
        dbnomics_latest = None

    print("\nDirect IMF API attempts (no key, several candidate endpoints/paths"
          " since the exact current one is unconfirmed):")
    any_success = False
    for label, url, params, headers in IMF_CANDIDATES:
        print(f"\n  [{label}]\n  {url}")
        try:
            r = requests.get(url, params=params, headers=headers, timeout=20)
            print(f"    status: {r.status_code}")
            text = r.text[:800]
            print(f"    body (first 800 chars): {text}")
            if r.status_code == 200:
                any_success = True
        except requests.exceptions.RequestException as e:
            print(f"    FAILED (network): {e}")

    print(f"\nAny direct-IMF endpoint returned 200: {any_success}")
    if dbnomics_latest:
        print(f"DBnomics mirror latest for comparison: {dbnomics_latest[0]}-{dbnomics_latest[1]:02d}")
    print()


# --- 3. total-debt "other debt" hypothesis ----------------------------------

def section_3_total_debt():
    print("=" * 78)
    print("3. TOTAL DEBT 'other debt' hypothesis: TCMDO %GDP minus government %GDP")
    print("=" * 78)
    try:
        gdp_units, gdp_obs = F.series_obs("GDP")
        tcmdo_units, tcmdo_obs = F.series_obs("TCMDO")
        debt_units, debt_obs = F.series_obs("FYGFGDQ188S")

        gdp_q = S.as_quarterly(gdp_obs)
        tcmdo_q = S.as_quarterly(tcmdo_obs)
        debt_q = S.as_quarterly(debt_obs)

        common = sorted(gdp_q.keys() & tcmdo_q.keys() & debt_q.keys())
        if not common:
            print("  no overlapping quarter across all three series")
            return
        q = common[-1]
        gdp_usd = S.to_dollars(gdp_q[q], gdp_units)
        tcmdo_pct = S.to_dollars(tcmdo_q[q], tcmdo_units) / gdp_usd * 100.0
        debt_pct = debt_q[q]
        non_gov_pct = tcmdo_pct - debt_pct
        print(f"  Latest common quarter: {q}")
        print(f"  TCMDO (total debt, all sectors) / GDP: {tcmdo_pct:.1f}%")
        print(f"  FYGFGDQ188S (govt debt held by public) / GDP: {debt_pct:.1f}%")
        print(f"  Non-government-debt proxy (TCMDO - govt): {non_gov_pct:.1f}%")
        print(f"  Dalio's Ch.17 'other debt' target: 340%")
        print(f"  Residual vs. 340%: {non_gov_pct - 340.0:+.1f}pt")
        print(f"  (for comparison, TCMDO itself vs 340%: {tcmdo_pct - 340.0:+.1f}pt)")
    except Exception as e:  # noqa: BLE001
        print(f"  FAILED: {e}")
    print()


def main():
    print(f"Run at {dt.datetime.now(dt.timezone.utc).isoformat()}\n")
    section_1_matrix()
    section_2_gold_staleness()
    section_3_total_debt()
    print("Done.")


if __name__ == "__main__":
    main()
