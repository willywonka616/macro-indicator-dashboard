"""Treasury Fiscal Data API client (free, no API key).

Provides the budget-basis debt-service ratio:

    interest on the public debt  /  total federal receipts

Both come from Treasury (cash/budget basis), which is the basis Dalio and CBO
use for "interest as a share of revenue" — unlike the FRED NIPA (accrual) basis.

The Fiscal Data host is not reachable from the build's dev environment, so the
exact column names can't be introspected there. Two safeguards make that safe:
  * verify() dumps each endpoint's real fields + latest values in --verify, so
    any wrong field name is visible in the first CI run.
  * field detection is adaptive (tries known names, then patterns), and the
    caller sanity-checks the resulting ratio before it can be written.

Docs: https://fiscaldata.treasury.gov/api-documentation/
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

import requests

BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# Gross interest on the public debt (marketable + government account series).
INTEREST_ENDPOINT = "/v2/accounting/od/interest_expense"
# Summary of receipts, outlays and the surplus/deficit — has "Total Receipts".
RECEIPTS_ENDPOINT = "/v1/accounting/mts/mts_table_1"

TTM = 12  # trailing months used to annualise both numerator and denominator


# --- http ----------------------------------------------------------------

def _get(endpoint: str, params: dict | None = None, max_pages: int = 40):
    params = dict(params or {})
    params.setdefault("format", "json")
    params.setdefault("page[size]", "1000")
    rows, page = [], 1
    while page <= max_pages:
        params["page[number]"] = str(page)
        r = requests.get(BASE + endpoint, params=params, timeout=40)
        r.raise_for_status()
        js = r.json()
        rows.extend(js.get("data", []))
        meta = js.get("meta", {})
        total_pages = int(meta.get("total-pages") or meta.get("total_pages") or 1)
        if page >= total_pages:
            break
        page += 1
    return rows


# --- field detection -----------------------------------------------------

def _num(x):
    try:
        return float(str(x).replace(",", "").replace("$", ""))
    except (TypeError, ValueError):
        return None


def _pick(sample: dict, names, contains=None, exclude=()):
    for n in names:
        if n in sample:
            return n
    if contains:
        for k in sample:
            kl = k.lower()
            if all(t in kl for t in contains) and not any(e in kl for e in exclude):
                return k
    return None


def _ym(record_date: str):
    d = dt.date.fromisoformat(record_date)
    return (d.year, d.month)


# --- monthly series ------------------------------------------------------

def monthly_interest() -> dict:
    """{(year, month): total gross interest on the public debt, $} — monthly."""
    rows = _get(INTEREST_ENDPOINT, {"sort": "record_date"})
    if not rows:
        raise RuntimeError("interest_expense: no rows returned")
    s = rows[0]
    datek = _pick(s, ["record_date"], contains=["record", "date"])
    amtk = _pick(s, ["month_expense_amt", "interest_expense_amt"],
                 contains=["month", "amt"], exclude=["fytd", "prior", "fiscal", "year"])
    catk = _pick(s, ["expense_category_desc", "expense_type_desc", "classification_desc"],
                 contains=["desc"])
    if not (datek and amtk and catk):
        raise RuntimeError(f"interest_expense: could not map fields from {list(s)}")

    totals, comps = {}, defaultdict(float)
    for row in rows:
        amt = _num(row.get(amtk))
        if amt is None:
            continue
        ym = _ym(row[datek])
        cat = str(row.get(catk, "")).lower()
        if "total" in cat and "interest" in cat:
            totals[ym] = amt                 # explicit total row wins
        elif "total" not in cat:
            comps[ym] += amt                 # else sum the components
    out = {ym: totals.get(ym, comps.get(ym)) for ym in set(totals) | set(comps)}
    return {k: v for k, v in out.items() if v}


def monthly_receipts() -> dict:
    """{(year, month): total federal receipts, $} — monthly (current-month)."""
    rows = _get(RECEIPTS_ENDPOINT, {"sort": "record_date"})
    if not rows:
        raise RuntimeError("mts_table_1: no rows returned")
    s = rows[0]
    datek = _pick(s, ["record_date"], contains=["record", "date"])
    classk = _pick(s, ["classification_desc"], contains=["classification", "desc"]) \
        or _pick(s, [], contains=["desc"])
    amtk = _pick(s, ["current_month_rcpt_outly_amt", "current_month_gross_rcpt_amt"],
                 contains=["current", "month", "amt"], exclude=["fytd", "prior", "year"])
    if not (datek and classk and amtk):
        raise RuntimeError(f"mts_table_1: could not map fields from {list(s)}")

    out = {}
    for row in rows:
        if "total receipts" in str(row.get(classk, "")).lower():
            amt = _num(row.get(amtk))
            if amt is not None:
                out[_ym(row[datek])] = amt
    if not out:
        raise RuntimeError("mts_table_1: no 'Total Receipts' rows matched")
    return out


# --- derived metric ------------------------------------------------------

def debt_service_ratio() -> dict:
    """Trailing-12-month interest / trailing-12-month receipts, as a percentage.

    Returns {"latest": float, "asOf": "YYYY-MM", "history": [{y, v}]}.
    Summing 12 months of each avoids the fiscal-YTD reset and annualises both
    consistently.
    """
    interest = monthly_interest()
    receipts = monthly_receipts()
    months = sorted(set(interest) & set(receipts))
    if len(months) < TTM:
        raise RuntimeError("debt_service_ratio: fewer than 12 overlapping months")

    ratio = {}
    for i in range(TTM - 1, len(months)):
        window = months[i - TTM + 1: i + 1]
        num = sum(interest[m] for m in window)
        den = sum(receipts[m] for m in window)
        if den:
            ratio[months[i]] = num / den * 100.0

    last = max(ratio)
    # coarse history: one point per calendar quarter
    hist = [{"y": round(y + (m - 1) / 12.0, 3), "v": round(v, 2)}
            for (y, m), v in sorted(ratio.items()) if m in (3, 6, 9, 12)]
    return {"latest": round(ratio[last], 1), "asOf": f"{last[0]}-{last[1]:02d}", "history": hist}


# --- verification --------------------------------------------------------

def verify() -> bool:
    """Dump each endpoint's schema + latest values, and try the computation.
    Returns True on success. Printed output is the source of truth for the
    real field names (the API can't be introspected from the dev env)."""
    print("\nVerifying Treasury Fiscal Data endpoints\n")
    ok = True
    for name, ep in [("interest", INTEREST_ENDPOINT), ("receipts", RECEIPTS_ENDPOINT)]:
        try:
            rows = _get(ep, {"sort": "-record_date", "page[size]": "3"}, max_pages=1)
            if not rows:
                raise RuntimeError("no rows")
            print(f"[{name}] {BASE}{ep}")
            print("  fields:", ", ".join(rows[0].keys()))
            print("  latest record:", rows[0])
        except Exception as e:  # noqa: BLE001
            ok = False
            print(f"[{name}] {ep}  FAILED: {e}")

    try:
        r = debt_service_ratio()
        print(f"\n  computed debt-service ratio: {r['latest']}% "
              f"as of {r['asOf']} ({len(r['history'])} history pts)")
    except Exception as e:  # noqa: BLE001
        ok = False
        print(f"\n  ratio computation FAILED: {e}")
    return ok
