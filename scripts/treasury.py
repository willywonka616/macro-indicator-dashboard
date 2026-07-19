"""Treasury Fiscal Data API client (free, no API key).

Provides the budget-basis debt-service ratio:

    interest on the public debt  /  total federal receipts

Both come from Treasury (cash/budget basis), which is the basis Dalio and CBO
use for "interest as a share of revenue" — unlike the FRED NIPA (accrual) basis.

Definition (resolved 2026-07 against Dalio's Ch.17 US table, see STATUS.md §9):
the live ratio uses GROSS interest expense on the total public debt outstanding
(public issues + intragovernmental Government Account Series), matching GAO's
"Schedule of Federal Debt" interest concept — NOT interest on debt held by the
public alone, and NOT the CBO/OMB "net interest, budget function 900" concept.
Cross-checked against real FY2024 figures:
  gross interest $1,126.5B (GAO GAO-25-107138) / receipts $4.9T (CBO) ≈ 23.0%,
  vs. Dalio's book value of 22% — closest of three candidate definitions tried.
`gross_interest_monthly()` is what feeds the live ratio; `net_to_public_interest_monthly()`
(the previous basis) and `net_interest_function900_monthly()` (best-effort,
CBO/OMB's function-900 concept) are kept for the diagnostic matrix printed by
`--verify` and are not used to build data.json.

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
import time
from collections import defaultdict

import requests

BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

# Gross interest on the public debt (marketable + government account series).
INTEREST_ENDPOINT = "/v2/accounting/od/interest_expense"

TTM = 12  # trailing months used to annualise both numerator and denominator


# --- http ----------------------------------------------------------------

def _get_page(url: str, params: dict, tries: int = 4):
    """GET one page with retry/backoff — the Fiscal Data host occasionally
    drops connections mid-run (RemoteDisconnected)."""
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=45)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)  # 1s, 2s, 4s
    raise RuntimeError(f"Treasury request failed after {tries} tries: {last}")


def _get(endpoint: str, params: dict | None = None, max_pages: int = 40):
    params = dict(params or {})
    params.setdefault("format", "json")
    params.setdefault("page[size]", "1000")
    rows, page = [], 1
    while page <= max_pages:
        params["page[number]"] = str(page)
        js = _get_page(BASE + endpoint, params)
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

def _interest_rows():
    """Raw interest_expense rows, fetched once and reused by all three
    numerator variants below."""
    rows = _get(INTEREST_ENDPOINT, {"sort": "record_date"})
    if not rows:
        raise RuntimeError("interest_expense: no rows returned")
    return rows


def _interest_field_keys(rows):
    s = rows[0]
    amtk = _pick(s, ["month_expense_amt"], contains=["month", "amt"],
                 exclude=["fytd", "prior", "fiscal", "year"])
    catk = _pick(s, ["expense_catg_desc", "expense_category_desc"], contains=["cat", "desc"])
    if not amtk:
        raise RuntimeError(f"interest_expense: no month amount field in {list(s)}")
    return amtk, catk


def gross_interest_monthly(rows=None) -> dict:
    """{(year, month): gross interest on total public debt outstanding, $}.

    Sums every category — PUBLIC ISSUES *and* GOVT ACCOUNT SERIES (intragov).
    This is Treasury Account Symbol 20X0550, "Interest on the Public Debt",
    the same concept GAO reports in the annual Schedule of Federal Debt. This
    is the definition the live debt-service ratio uses — see module docstring.
    """
    rows = rows if rows is not None else _interest_rows()
    amtk, _catk = _interest_field_keys(rows)
    monthly = defaultdict(float)
    for row in rows:
        amt = _num(row.get(amtk))
        if amt is not None:
            monthly[_ym(row["record_date"])] += amt
    return {k: v for k, v in monthly.items() if v}


def net_to_public_interest_monthly(rows=None) -> dict:
    """{(year, month): interest on debt held by the public, $}.

    Sums every interest component on PUBLIC ISSUES only — accrued interest,
    amortized discount/premium, savings bonds, misc — excluding GOVT ACCOUNT
    SERIES (intragovernmental interest paid to trust funds). This was the
    live basis before the Ch.17 calibration; kept for the diagnostic matrix.
    """
    rows = rows if rows is not None else _interest_rows()
    amtk, catk = _interest_field_keys(rows)
    monthly = defaultdict(float)
    for row in rows:
        amt = _num(row.get(amtk))
        if amt is None:
            continue
        if catk and "public issue" not in str(row.get(catk, "")).lower():
            continue
        monthly[_ym(row["record_date"])] += amt
    return {k: v for k, v in monthly.items() if v}


# CBO/OMB's "net interest" is budget function 900, a distinct concept (gross
# interest minus interest received, incl. intragovernmental interest income)
# reported in MTS's outlays-by-function table, not in interest_expense.
# mts_table_9 is CONFIRMED live (2026-07-19 run): it's genuinely "Summary of
# Receipts and Outlays by Function", with a "Net Interest" classification_desc
# row ($104.49B for 2026-06, current_month_rcpt_outly_amt). mts_table_5 is
# kept as a fallback for robustness but is a different table (outlays by
# agency) with no function breakdown, so it won't match "net interest" — it's
# dead code in practice unless table_9 changes shape. Diagnostic only; never
# used to build data.json, and never allowed to fail the run.
FUNCTION_OUTLAYS_ENDPOINTS = [
    "/v1/accounting/mts/mts_table_9",  # Summary of Receipts and Outlays by Function
    "/v1/accounting/mts/mts_table_5",  # Outlays of the U.S. Government (fallback, likely unreachable)
]


def net_interest_function900_monthly() -> dict | None:
    """{(year, month): net interest, budget function 900, $} — best-effort.
    Returns None (not an exception) if the endpoint/field can't be found, so
    the diagnostic matrix can print "unavailable" without failing verify()."""
    for ep in FUNCTION_OUTLAYS_ENDPOINTS:
        try:
            rows = _get(ep, {"sort": "record_date"})
            if not rows:
                continue
            s = rows[0]
            classk = _pick(s, ["classification_desc"], contains=["classification", "desc"]) \
                or _pick(s, [], contains=["desc"])
            amtk = _pick(s, ["current_month_outly_amt", "current_month_gross_outly_amt"],
                         contains=["month", "outly", "amt"], exclude=["fytd", "prior", "year"])
            if not (classk and amtk):
                continue
            monthly = defaultdict(float)
            for row in rows:
                desc = str(row.get(classk, "")).lower()
                if "net interest" not in desc:
                    continue
                amt = _num(row.get(amtk))
                if amt is not None:
                    monthly[_ym(row["record_date"])] += amt
            monthly = {k: v for k, v in monthly.items() if v}
            if monthly:
                return monthly
        except Exception:  # noqa: BLE001
            continue
    return None


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

def _ttm_ratio(numerator: dict, denominator: dict) -> dict | None:
    """Trailing-12-month numerator / trailing-12-month denominator, as a %.
    Summing 12 months of each avoids the fiscal-YTD reset and annualises both
    consistently. Returns None if there's insufficient overlap rather than
    raising — callers decide whether that's fatal."""
    months = sorted(set(numerator) & set(denominator))
    if len(months) < TTM:
        return None
    ratio = {}
    for i in range(TTM - 1, len(months)):
        window = months[i - TTM + 1: i + 1]
        num = sum(numerator[m] for m in window)
        den = sum(denominator[m] for m in window)
        if den:
            ratio[months[i]] = num / den * 100.0
    if not ratio:
        return None
    last = max(ratio)
    # coarse history: one point per calendar quarter
    hist = [{"y": round(y + (m - 1) / 12.0, 3), "v": round(v, 2)}
            for (y, m), v in sorted(ratio.items()) if m in (3, 6, 9, 12)]
    return {"latest": round(ratio[last], 1), "asOf": f"{last[0]}-{last[1]:02d}", "history": hist}


def debt_service_ratio() -> dict:
    """Trailing-12-month GROSS interest / trailing-12-month total receipts, as
    a percentage — the live basis for "debt service vs revenue". See the
    module docstring for why gross (not net-to-public) was adopted."""
    ratio = _ttm_ratio(gross_interest_monthly(), monthly_receipts())
    if ratio is None:
        raise RuntimeError("debt_service_ratio: fewer than 12 overlapping months")
    return ratio


def debt_service_matrix(tax_receipts_monthly: dict | None = None) -> dict:
    """The 3 numerator x 2 denominator diagnostic matrix used to calibrate
    against Dalio's Ch.17 book value (22%, US, March 2025 snapshot). Not used
    to build data.json — printed by --verify only. `tax_receipts_monthly` is
    optional (fetch.py supplies it from FRED W006RC1Q027SBEA, the original
    brief's narrower denominator) so this module stays FRED-independent when
    called without it.

    Returns {(num_label, den_label): ratio_dict_or_None, ...}.
    """
    rows = _interest_rows()
    numerators = {
        "gross (incl. GAS)": gross_interest_monthly(rows),
        "net-to-public (excl. GAS)": net_to_public_interest_monthly(rows),
        "net interest, function 900": net_interest_function900_monthly(),
    }
    denominators = {"total receipts": monthly_receipts()}
    if tax_receipts_monthly:
        denominators["tax receipts only"] = tax_receipts_monthly

    matrix = {}
    for nlabel, nvals in numerators.items():
        for dlabel, dvals in denominators.items():
            matrix[(nlabel, dlabel)] = _ttm_ratio(nvals, dvals) if nvals else None
    return matrix


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


def verify(tax_receipts_monthly: dict | None = None) -> bool:
    """Dump the Treasury schemas, try the live ratio, and print the 3x2
    debt-service diagnostic matrix. Returns True on success (the matrix
    itself is diagnostic and never fails the run — see debt_service_matrix)."""
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
    for ep in FUNCTION_OUTLAYS_ENDPOINTS:
        try:
            print()
            _dump("outlays-by-function?", ep, ["outly", "amt"])
        except Exception as e:  # noqa: BLE001
            print(f"[outlays-by-function?] {ep} FAILED: {e}")

    try:
        r = debt_service_ratio()
        print(f"\n  LIVE debt-service ratio (gross interest / total receipts): "
              f"{r['latest']}% as of {r['asOf']} ({len(r['history'])} history pts)")
    except Exception as e:  # noqa: BLE001
        ok = False
        print(f"\n  ratio computation FAILED: {e}")

    print("\n  Debt-service calibration matrix (Dalio Ch.17 US target: 22%, Mar 2025):")
    try:
        matrix = debt_service_matrix(tax_receipts_monthly)
        den_labels = sorted({d for _, d in matrix})
        print(f"  {'numerator':<30}" + "".join(f"{d:>22}" for d in den_labels))
        for nlabel in ["gross (incl. GAS)", "net-to-public (excl. GAS)", "net interest, function 900"]:
            cells = []
            for dlabel in den_labels:
                r = matrix.get((nlabel, dlabel))
                cells.append(f"{r['latest']}%" if r else "unavailable")
            print(f"  {nlabel:<30}" + "".join(f"{c:>22}" for c in cells))
    except Exception as e:  # noqa: BLE001
        print(f"  matrix computation FAILED (diagnostic only, not fatal): {e}")
    return ok
