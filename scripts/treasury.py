"""Treasury Fiscal Data API client (free, no API key).

Provides two budget-basis debt-service ratios, both from Treasury
(cash/budget basis, the basis Dalio and CBO use for "interest as a share of
revenue" — unlike FRED's NIPA/accrual basis):

    NET interest to the public   /  total receipts (net of refunds)   (headline)
    GROSS interest incl. GAS     /  total receipts (net of refunds)   (second row)

Definition, revised 2026-07 twice in the same day (see STATUS.md §9/§12/§13
for the full calibration history, including two retractions):

`debt_service_ratio()` (the headline `debt_service_to_revenue` vital) uses
NET interest to the public (`net_to_public_interest_monthly()`) over TOTAL
receipts, net of refunds (`monthly_receipts()`) — not on-budget receipts,
the immediately-prior basis, and not gross receipts, a field-selection bug
in every basis tried before this pass.

**The receipts field bug (fixed this pass, see STATUS.md §13):**
`mts_table_4`'s "Total -- Receipts" row carries three amount fields per
month: `current_month_gross_rcpt_amt`, `current_month_refund_amt`,
`current_month_net_rcpt_amt` (gross − refund = net, confirmed live). Every
previous version of this module summed the GROSS field. Checked against
CBO's independently published FY totals, gross overshoots by ~7% in both
FY2024 ($5.265T vs. CBO's $4.920T) and FY2025 ($5.617T vs. CBO's $5.235T);
NET matches both to within rounding (FY2024 $4.919T, FY2025 $5.235T exact).
"Federal revenue" in every standard published figure (CBO, OMB, Treasury
summaries) means net-of-refunds receipts — `monthly_receipts()` and
`off_budget_receipts_monthly()` now sum `current_month_net_rcpt_amt`.

**The on-budget-vs-total denominator question (also revisited this pass):**
the immediately-prior basis divided by ON-BUDGET receipts (total minus
OASI+DI trust fund receipts), chosen mainly because it landed close to
Dalio's 22% — which the receipts-field bug above made an artifact of an
inflated (gross) total-receipts denominator, not a real match. With the
field bug fixed, no numerator/denominator combination lands near 22% at
Dalio's March-2025 vintage (closest: gross ÷ total, 23.9%, still ~2pt off
— see STATUS.md §13). With "closeness to 22%" no longer a live
consideration, TOTAL receipts is used going forward on definitional
grounds instead: it's the denominator every standard published
interest-to-revenue figure (CBO, OMB, GAO) actually uses, whereas the
on-budget/off-budget split is a budget-*process* artifact (2 U.S.C. 622(7)
governs what counts toward statutory budget-enforcement totals, not which
revenue is economically available to pay interest — Treasury commingles
on- and off-budget cash in the same general account). `on_budget_receipts_monthly()`
is kept for the diagnostic matrix (`debt_service_matrix()`) but is no
longer the shipped denominator.

Both debt-service rows and `debt_to_revenue` (fetch.py) now share the same
TOTAL, net-of-refunds receipts denominator — recorded once in
`provenance.revenueDefinition`.

`gross_interest_monthly()`, `net_to_public_interest_monthly()`, and
`net_interest_function900_monthly()` are the three numerator candidates;
`monthly_receipts()`, `on_budget_receipts_monthly()`, and the FRED-sourced
tax-receipts-only series (fetch.py) are the three denominator candidates in
the diagnostic matrix — all now net-of-refunds where they read from
`mts_table_4`.

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

import series as S

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


def monthly_receipts(rows=None) -> dict:
    """{(year, month): total federal receipts, NET of refunds, $} — monthly
    (current-month).

    Sums `current_month_net_rcpt_amt`, not `current_month_gross_rcpt_amt`
    (a bug in every earlier version of this function — see the module
    docstring: gross overshoots CBO's published FY totals by ~7%, net
    matches them almost exactly). "Federal receipts"/"federal revenue" in
    every standard published figure (CBO, OMB, Treasury) means net of
    refunds.

    If several "total receipts" rows match in a month (e.g. on/off-budget
    splits slip through), the largest is taken — the grand total.
    `rows` lets a caller that already fetched mts_table_4 (the first, usual
    RECEIPTS_ENDPOINTS entry) reuse it instead of fetching again; passing it
    skips the multi-endpoint fallback, since the caller already knows which
    endpoint the rows came from.
    """
    last_err = "no endpoints tried"
    for ep in RECEIPTS_ENDPOINTS if rows is None else [RECEIPTS_ENDPOINTS[0]]:
        try:
            r = rows if rows is not None else _get(ep, {"sort": "record_date"})
            if not r:
                last_err = f"{ep}: no rows"
                continue
            s = r[0]
            classk = _pick(s, ["classification_desc"], contains=["classification", "desc"]) \
                or _pick(s, [], contains=["desc"])
            amtk = _pick(s, ["current_month_net_rcpt_amt", "current_month_rcpt_amt"],
                         contains=["month", "rcpt", "amt"],
                         exclude=["fytd", "prior", "year", "outly", "dfct", "gross", "refund"])
            if not (classk and amtk):
                last_err = f"{ep}: could not map fields from {list(s)}"
                continue
            out = {}
            for row in r:
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


def _receipts_table4_rows():
    """Raw mts_table_4 rows, fetched once and reused by monthly_receipts()
    and off_budget_receipts_monthly() so the on-budget denominator doesn't
    double the number of HTTP calls."""
    rows = _get(RECEIPTS_ENDPOINTS[0], {"sort": "record_date"})
    if not rows:
        raise RuntimeError(f"{RECEIPTS_ENDPOINTS[0]}: no rows returned")
    return rows


# Off-budget receipts are, by statute (2 U.S.C. 622(7)), Social Security's
# two trust funds only — OASI and DI — not Medicare (which is on-budget
# despite also being a trust fund). mts_table_4's own classification_desc
# already carries unambiguous grand-total lines for both, confirmed live:
# "Total -- Federal Old-Age and Survivors Insurance Trust Fund" and
# "Total -- Federal Disability Insurance Trust Fund" (see
# docs/review/2026-07-19c-verification.md). On-budget receipts = total
# receipts minus those two lines. This is preferred over mts_table_5's
# "Total On-Budget" / "Total Off-Budget" rows (which an earlier task flagged
# for investigation): table 5's own fields are all outlay-shaped
# (current_month_gross_outly_amt, current_month_app_rcpt_amt = agency
# *offsetting* receipts, not total federal receipts) — its "Total
# On-Budget" almost certainly describes on-budget OUTLAYS or the on-budget
# deficit/surplus, not on-budget RECEIPTS. verify() still probes table 5
# and prints what it finds, purely as a cross-check, but does not use it to
# build the denominator.
#
# NOTE (2026-07, see STATUS.md §13): on_budget_receipts_monthly() is no
# longer the shipped debt-service/debt-to-revenue denominator — that's now
# monthly_receipts() (TOTAL receipts). Kept here as a diagnostic-matrix
# candidate only (debt_service_matrix(), verify()).
_OFF_BUDGET_FUND_LABELS = (
    "total -- federal old-age and survivors insurance trust fund",
    "total -- federal disability insurance trust fund",
)


def off_budget_receipts_monthly(rows=None) -> dict | None:
    """{(year, month): OASI + DI trust fund receipts, NET of refunds, $} —
    best-effort. Returns None (not an exception) if the two labelled totals
    can't be found, so on_budget_receipts_monthly() can report
    "unavailable" rather than silently using a wrong number."""
    try:
        r = rows if rows is not None else _receipts_table4_rows()
        s = r[0]
        classk = _pick(s, ["classification_desc"], contains=["classification", "desc"])
        amtk = _pick(s, ["current_month_net_rcpt_amt", "current_month_rcpt_amt"],
                     contains=["month", "rcpt", "amt"],
                     exclude=["fytd", "prior", "year", "outly", "dfct", "gross", "refund"])
        if not (classk and amtk):
            return None
        monthly = defaultdict(float)
        matched_labels = set()
        for row in r:
            desc = str(row.get(classk, "")).strip().lower()
            if desc in _OFF_BUDGET_FUND_LABELS:
                amt = _num(row.get(amtk))
                if amt is not None:
                    monthly[_ym(row["record_date"])] += amt
                    matched_labels.add(desc)
        # Only trust the result if BOTH labelled funds were found at least
        # once — a partial match (e.g. OASI renamed) would understate
        # off-budget receipts and silently corrupt on-budget receipts too.
        if len(matched_labels) < len(_OFF_BUDGET_FUND_LABELS):
            return None
        return {k: v for k, v in monthly.items() if v}
    except Exception:  # noqa: BLE001
        return None


def on_budget_receipts_monthly() -> dict | None:
    """{(year, month): on-budget total receipts, $} — best-effort.
    = total receipts − (OASI + DI trust fund receipts). Returns None if
    either input is unavailable, so debt_service_matrix can show
    "unavailable" instead of a wrong number."""
    try:
        rows = _receipts_table4_rows()
        total = monthly_receipts(rows)
        off_budget = off_budget_receipts_monthly(rows)
        if not off_budget:
            return None
        out = {k: total[k] - off_budget[k] for k in total.keys() & off_budget.keys()}
        return {k: v for k, v in out.items() if v}
    except Exception:  # noqa: BLE001
        return None


def _table5_on_budget_probe() -> dict:
    """Diagnostic only (verify() cross-check, never used to build data.json):
    dumps whatever mts_table_5's "Total On-Budget" row's three numeric
    fields actually contain, so a live run can confirm or refute the
    hypothesis that they represent receipts rather than outlays."""
    out = {}
    try:
        rows = _get("/v1/accounting/mts/mts_table_5", {"sort": "-record_date", "page[size]": "300"}, max_pages=1)
        if not rows:
            return {"error": "no rows"}
        s = rows[0]
        classk = _pick(s, ["classification_desc"], contains=["classification", "desc"])
        latest = s["record_date"]
        for row in rows:
            if row["record_date"] != latest:
                continue
            desc = str(row.get(classk, "")).strip().lower()
            if desc in ("total on-budget", "total off-budget"):
                out[row.get(classk)] = {
                    k: row.get(k) for k in row
                    if k.startswith("current_month_") and k != "current_month_dfct_sur_amt"
                }
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
    return out


# --- TTM dollar sums (not ratios) — feeds debt_to_revenue ----------------

def _ttm_sum(monthly: dict) -> dict:
    """{month: trailing-12-month dollar sum}. Same window as _ttm_ratio's
    numerator/denominator, but returns the raw annualised dollar figure
    instead of a ratio — needed to build debt/revenue, which divides a
    dollar debt STOCK by a dollar revenue FLOW, not two ratios."""
    months = sorted(monthly)
    if len(months) < TTM:
        return {}
    out = {}
    for i in range(TTM - 1, len(months)):
        window = months[i - TTM + 1: i + 1]
        out[months[i]] = sum(monthly[m] for m in window)
    return out


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
    """Trailing-12-month NET interest to the public / trailing-12-month
    TOTAL receipts (net of refunds), as a percentage — the live basis for
    the headline "debt service vs revenue" vital. See the module docstring
    for why net (not gross) interest and TOTAL, net-of-refunds receipts
    (not gross receipts, not on-budget) were adopted."""
    total = monthly_receipts()
    if not total:
        raise RuntimeError("debt_service_ratio: total receipts unavailable "
                            "(see monthly_receipts / --verify)")
    ratio = _ttm_ratio(net_to_public_interest_monthly(), total)
    if ratio is None:
        raise RuntimeError("debt_service_ratio: fewer than 12 overlapping months")
    return ratio


def gross_debt_service_ratio() -> dict:
    """Trailing-12-month GROSS interest (incl. intragovernmental GAS) /
    trailing-12-month TOTAL receipts (net of refunds) — the second,
    explicitly-labelled debt-service row. Same denominator as
    debt_service_ratio() (one revenue definition across the page, see
    STATUS.md §13/provenance)."""
    total = monthly_receipts()
    if not total:
        raise RuntimeError("gross_debt_service_ratio: total receipts unavailable")
    ratio = _ttm_ratio(gross_interest_monthly(), total)
    if ratio is None:
        raise RuntimeError("gross_debt_service_ratio: fewer than 12 overlapping months")
    return ratio


def revenue_ttm_dollars() -> dict:
    """{(year, month): trailing-12-month TOTAL receipts, net of refunds, $}
    — the raw dollar flow (not a ratio), for debt_to_revenue which divides
    a debt dollar STOCK by this revenue dollar FLOW. Same total-receipts
    denominator as both debt-service rows (one revenue definition across
    the page)."""
    total = monthly_receipts()
    if not total:
        raise RuntimeError("revenue_ttm_dollars: total receipts unavailable")
    ttm = _ttm_sum(total)
    if not ttm:
        raise RuntimeError("revenue_ttm_dollars: fewer than 12 overlapping months")
    return ttm


def debt_service_matrix(tax_receipts_monthly: dict | None = None) -> dict:
    """The 3 numerator x 3 denominator diagnostic matrix used to calibrate
    against Dalio's Ch.17 book value (22%, US, March 2025 snapshot). Not used
    to build data.json — printed by --verify only. `tax_receipts_monthly` is
    optional (fetch.py supplies it from FRED W006RC1Q027SBEA, the original
    brief's narrower denominator) so this module stays FRED-independent when
    called without it. "on-budget receipts" (total minus OASI+DI trust fund
    receipts, see on_budget_receipts_monthly) is included when it resolves;
    shown as "unavailable" for every numerator in that column if not.

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
    on_budget = on_budget_receipts_monthly()
    if on_budget:
        denominators["on-budget receipts"] = on_budget

    matrix = {}
    for nlabel, nvals in numerators.items():
        for dlabel, dvals in denominators.items():
            matrix[(nlabel, dlabel)] = _ttm_ratio(nvals, dvals) if (nvals and dvals) else None
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
    """Dump the Treasury schemas, try the live ratio, and print the 3x3
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

    print("\n  On-budget receipts (total minus OASI+DI trust fund receipts):")
    try:
        ob = on_budget_receipts_monthly()
        if ob:
            last = max(ob)
            print(f"    resolved: {len(ob)} months, latest {last[0]}-{last[1]:02d} = "
                  f"${ob[last]/1e9:.1f}B")
        else:
            print("    unavailable — OASI/DI trust fund total-receipts labels not both found "
                  "(see mts_table_4 dump above for what's actually there)")
    except Exception as e:  # noqa: BLE001
        print(f"    FAILED: {e}")

    print("\n  mts_table_5 'Total On-Budget' / 'Total Off-Budget' cross-check "
          "(diagnostic only — investigating whether these describe receipts "
          "or outlays; never used to build data.json):")
    probe = _table5_on_budget_probe()
    if "error" in probe:
        print(f"    FAILED: {probe['error']}")
    elif not probe:
        print("    no 'Total On-Budget'/'Total Off-Budget' rows found in the latest period")
    else:
        for label, fields in probe.items():
            print(f"    {label}: {fields}")

    max_days = S.FRESHNESS_DAYS_BY_FREQ["Monthly"]
    try:
        r = debt_service_ratio()
        f = S.freshness("net debt-service ratio", r["asOf"], max_days)
        fresh_s = "STALE" if f["stale"] else "ok"
        print(f"\n  LIVE headline debt-service ratio (net interest to the public / "
              f"total receipts, net of refunds): {r['latest']}% as of {r['asOf']} "
              f"({len(r['history'])} history pts) — freshness: {f['age_days']}d old, "
              f"{max_days}d threshold, {fresh_s}")
    except Exception as e:  # noqa: BLE001
        ok = False
        print(f"\n  headline ratio computation FAILED: {e}")

    try:
        rg = gross_debt_service_ratio()
        f = S.freshness("gross debt-service ratio", rg["asOf"], max_days)
        fresh_s = "STALE" if f["stale"] else "ok"
        print(f"  LIVE second-row debt-service ratio (gross interest incl. GAS / "
              f"total receipts, net of refunds): {rg['latest']}% as of {rg['asOf']} "
              f"({len(rg['history'])} history pts) — freshness: {f['age_days']}d old, "
              f"{max_days}d threshold, {fresh_s}")
    except Exception as e:  # noqa: BLE001
        ok = False
        print(f"  gross-row ratio computation FAILED: {e}")

    print("\n  Debt-service calibration matrix, LATEST TTM values (each cell is a")
    print("  trailing-12-month ratio ending at its own most recent overlapping month,")
    print("  NOT dated to Mar-2025 — compare against Dalio's Ch.17 US target, 22% at")
    print("  his March-2025 vintage; see --verify's dated Mar-2025-vs-today section,")
    print("  or docs/review/, for values actually AT that date):")
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
