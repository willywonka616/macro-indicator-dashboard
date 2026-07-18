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
    """{(year, month): total gross interest on the public debt, $} — monthly.

    Sums the accrued-interest rows across categories (public issues + GAS) and
    security types; skips amortization/discount memoranda so nothing is
    double-counted.
    """
    rows = _get(INTEREST_ENDPOINT, {"sort": "record_date"})
    if not rows:
        raise RuntimeError("interest_expense: no rows returned")
    s = rows[0]
    amtk = _pick(s, ["month_expense_amt"], contains=["month", "amt"],
                 exclude=["fytd", "prior", "fiscal", "year"])
    groupk = _pick(s, ["expense_group_desc"], contains=["group", "desc"])
    if not amtk:
        raise RuntimeError(f"interest_expense: no month amount field in {list(s)}")

    monthly = defaultdict(float)
    for row in rows:
        amt = _num(row.get(amtk))
        if amt is None:
            continue
        # keep only accrued *interest* groups when the column exists
        if groupk and "interest" not in str(row.get(groupk, "")).lower():
            continue
        monthly[_ym(row["record_date"])] += amt
    return {k: v for k, v in monthly.items() if v}


# Receipts: MTS. Try tables in order; use the row whose classification is the
# grand total of receipts ("Total ... Receipts").
RECEIPTS_ENDPOINTS = [
    "/v1/accounting/mts/mts_table_4",  # Receipts of the U.S. Government
    "/v1/accounting/mts/mts_table_1",  # Summary of Receipts/Outlays
]


def _is_total_receipts(desc: str) -> bool:
    d = desc.lower()
    if "on-budget" in d or "off-budget" in d or "net" in d:
        return False  # want the unqualified grand total, not a sub-total
    return "total" in d and "receipt" in d


def monthly_receipts() -> dict:
    """{(year, month): total federal receipts, $} — monthly (current-month).

    If several "total receipts" rows match in a month (e.g. on/off-budget
    splits slip through), the largest is taken — the grand total.
    """
    last_err = "no endpoints tried"
    for ep in RECEIPTS_ENDPOINTS:
        try:
            rows = _get(ep, {"sort": "record_date"})
            if not rows:
                last_err = f"{ep}: no rows"
                continue
            s = rows[0]
            classk = _pick(s, ["classification_desc"], contains=["classification", "desc"]) \
                or _pick(s, [], contains=["desc"])
            amtk = _pick(s, ["current_month_gross_rcpt_amt", "current_month_rcpt_amt"],
                         contains=["month", "rcpt", "amt"],
                         exclude=["fytd", "prior", "year", "outly", "dfct"])
            if not (classk and amtk):
                last_err = f"{ep}: could not map fields from {list(s)}"
                continue
            out = {}
            for row in rows:
                if _is_total_receipts(str(row.get(classk, ""))):
                    amt = _num(row.get(amtk))
                    if amt is not None:
                        ym = _ym(row["record_date"])
                        out[ym] = max(out.get(ym, 0.0), amt)
            if out:
                return out
            last_err = f"{ep}: no 'Total Receipts' rows matched"
        except Exception as e:  # noqa: BLE001
            last_err = f"{ep}: {e}"
    raise RuntimeError(f"receipts: {last_err}")


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

def _distinct(rows, col, limit=30):
    seen = []
    for r in rows:
        v = r.get(col)
        if v is not None and v not in seen:
            seen.append(v)
        if len(seen) >= limit:
            break
    return seen


def _dump(label, ep, amount_hint):
    """Print an endpoint's schema, its *_desc distinct values, and the latest
    date's rows — the source of truth for field names (API isn't reachable from
    the dev env)."""
    rows = _get(ep, {"sort": "-record_date", "page[size]": "300"}, max_pages=1)
    if not rows:
        print(f"[{label}] {ep}  no rows"); return
    s = rows[0]
    print(f"[{label}] {BASE}{ep}")
    print("  fields:", ", ".join(s))
    for col in [c for c in s if c.endswith("_desc")]:
        print(f"  distinct {col}: {_distinct(rows, col)}")
    latest = s["record_date"]
    amtk = _pick(s, [], contains=amount_hint, exclude=["fytd", "prior", "year"])
    dcol = _pick(s, ["classification_desc", "expense_group_desc"], contains=["desc"])
    print(f"  latest {latest} rows ({dcol} = {amtk}):")
    for r in [r for r in rows if r["record_date"] == latest][:15]:
        print(f"    {r.get(dcol)} = {r.get(amtk)}")


def verify() -> bool:
    """Dump the Treasury schemas and try the ratio. Returns True on success."""
    print("\nVerifying Treasury Fiscal Data endpoints\n")
    ok = True
    try:
        _dump("interest", INTEREST_ENDPOINT, ["month", "amt"])
    except Exception as e:  # noqa: BLE001
        ok = False; print(f"[interest] FAILED: {e}")
    for ep in RECEIPTS_ENDPOINTS:
        try:
            print()
            _dump("receipts?", ep, ["rcpt", "amt"])
        except Exception as e:  # noqa: BLE001
            print(f"[receipts?] {ep} FAILED: {e}")

    try:
        r = debt_service_ratio()
        print(f"\n  computed debt-service ratio: {r['latest']}% "
              f"as of {r['asOf']} ({len(r['history'])} history pts)")
    except Exception as e:  # noqa: BLE001
        ok = False
        print(f"\n  ratio computation FAILED: {e}")
    return ok
