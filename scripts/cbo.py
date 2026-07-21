"""CBO 10-Year Budget Projections client — TASKprojections.md.

CBO has no REST API for its baseline projections; the task's own brief
assumed downloadable xlsx files from cbo.gov and said to "verify the
current URLs and file formats rather than assuming." Doing so found a
better source than the one assumed: CBO's own machine-readable data
mirror, `US-CBO/cbo-data` on GitHub — an official CBO product ("for use
by programmers, AI agents, and automated systems," per its README), not
a third party. It publishes exactly the dataset needed (`ten_year_budget`,
publication #51118) as clean, versioned, long-format CSVs — one file per
vintage, named `annual_fy_<YYYY-MM>.csv` — with a documented `schema.json`
alongside them. This is used instead of scraping cbo.gov's xlsx files.

Verified against three independently-known facts before trusting it (see
STATUS.md for the full record):
  * vintage 2024-06's FY2034 debt/GDP = 122.4% — Dalio's own stated figure
    (his book footnote 20 cites CBO; task file's own calibration target).
  * vintage 2025-01's FY2035 debt/GDP = 118.5% — matches the task file's
    own stated "January 2025 outlook projected 118% by 2035."
  * vintage 2026-02's FY2026 debt/GDP = 100.6% (~101%) and FY2036 = 120.2%
    (~120%) — matches independently reported figures for the current
    (February 2026) baseline.

cbo.gov itself is not reachable from this project's dev sandbox (proxy
policy denial, same as github.io earlier this session) — but
raw.githubusercontent.com and api.github.com ARE reachable from a normal
CI runner's unrestricted network, the same asymmetry every other
"not reachable from the dev environment" source in this project has
(see treasury.py's module docstring). verify() dumps the live schema and
values so any drift is caught in the first CI run, per that same
convention.
"""

from __future__ import annotations

import csv
import io
import re

import requests

import series as S

GITHUB_API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
REPO = "US-CBO/cbo-data"
DATASET_DIR = "data/budget/ten_year_budget"

VINTAGE_RE = re.compile(r"^annual_fy_(\d{4}-\d{2})\.csv$")

# The handful of ten_year_budget variables this feature actually uses —
# see schema.json (dumped in verify()) for the full field list. Levels are
# billions of dollars; *_gdp_share fields are already a percentage of GDP
# (no separate GDP series needed for those rows).
FIELDS = {
    "debt_held_by_public_gdp_share": "proj_debt_held_by_public_gdp_share",
    "debt_held_by_public": "proj_debt_held_by_public",
    "debt_held_by_public_begin": "proj_debt_held_by_public_begin",
    "rev_total": "proj_rev_total",
    "rev_total_gdp_share": "proj_rev_total_gdp_share",
    "outlays_total": "proj_outlays_total",
    "outlays_net_interest": "proj_outlays_net_interest",
    "outlays_net_interest_gdp_share": "proj_outlays_net_interest_gdp_share",
    "primary_deficit": "proj_primary_deficit",
    "debt_avg_interest_rate": "proj_debt_avg_interest_rate",
}


def _get_json(url: str, tries: int = 4):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, timeout=30, headers={"Accept": "application/vnd.github+json"})
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                import time
                time.sleep(2 ** i)
    raise RuntimeError(f"GitHub API request failed after {tries} tries: {url}: {last}")


def _get_text(url: str, tries: int = 4) -> str:
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return r.text
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                import time
                time.sleep(2 ** i)
    raise RuntimeError(f"raw.githubusercontent.com request failed after {tries} tries: {url}: {last}")


def list_vintages() -> list[str]:
    """Every available vintage string ("YYYY-MM"), oldest first — found by
    listing the dataset directory via the GitHub Contents API, not
    hardcoded, so a newly-published CBO vintage is picked up automatically
    without a code change."""
    items = _get_json(f"{GITHUB_API}/repos/{REPO}/contents/{DATASET_DIR}")
    vintages = []
    for item in items:
        m = VINTAGE_RE.match(item.get("name", ""))
        if m:
            vintages.append(m.group(1))
    if not vintages:
        raise RuntimeError(f"no annual_fy_<vintage>.csv files found in {DATASET_DIR}")
    return sorted(vintages)


def fetch_vintage(vintage: str) -> dict:
    """{field_key: {fiscal_year_int: value}} for one vintage, plus the
    fiscal-year range actually present — used both for the current
    vintage (the live projection rows) and for a named historical vintage
    (STATUS.md §9's calibration targets, e.g. "2024-06", at Dalio's own
    vintage)."""
    url = f"{RAW}/{REPO}/main/{DATASET_DIR}/annual_fy_{vintage}.csv"
    text = _get_text(url)
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise RuntimeError(f"CBO vintage {vintage}: empty CSV")
    wanted = set(FIELDS.values())
    out: dict[str, dict[int, float]] = {k: {} for k in FIELDS}
    fys: set[int] = set()
    for row in rows:
        var = row.get("variable")
        if var not in wanted:
            continue
        m = re.match(r"^FY(\d{4})$", row.get("date", ""))
        if not m:
            continue
        fy = int(m.group(1))
        try:
            val = float(row["value"])
        except (TypeError, ValueError):
            continue
        key = next(k for k, v in FIELDS.items() if v == var)
        out[key][fy] = val
        fys.add(fy)
    missing = [k for k, d in out.items() if not d]
    if missing:
        raise RuntimeError(f"CBO vintage {vintage}: fields not found: {missing}")
    return {"vintage": vintage, "fyMin": min(fys), "fyMax": max(fys), **out}


def current_vintage_data() -> dict:
    """The latest published vintage's data — the one used to build every
    live projection row. Freshness (STATUS.md TASKprojections.md §3) is
    checked by the caller against the vintage's own month, at the ~400d
    Annual threshold (S.FRESHNESS_DAYS_BY_FREQ["Annual"]) — CBO republishes
    roughly twice a year (Jan/Feb and mid-year), not monthly."""
    vintages = list_vintages()
    latest = vintages[-1]
    data = fetch_vintage(latest)
    data["isLatest"] = True
    return data


def vintage_label(data: dict) -> str:
    """A factual, data-derived vintage description for display on every
    projected row (TASKprojections.md §3: "Show the vintage on every
    projected row in the UI, not just in provenance") — built from the
    vintage string and the fiscal-year range actually present in the
    fetched file, not a guessed report title."""
    y, m = data["vintage"].split("-")
    month_name = ["", "January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"][int(m)]
    return (f"CBO 10-Year Budget Projections, {month_name} {y} baseline "
            f"(FY{data['fyMin']}–FY{data['fyMax']}, current law)")


# --- verification ----------------------------------------------------------

def verify() -> None:
    """Non-fatal: dumps the schema, the available vintages, and the latest
    vintage's key values — printed by --verify, never used to build
    data.json directly (see fetch.py, which calls current_vintage_data()
    separately and lets a real failure there propagate normally)."""
    print("\nVerifying CBO 10-Year Budget Projections (US-CBO/cbo-data GitHub mirror)")
    try:
        schema = _get_json(f"{GITHUB_API}/repos/{REPO}/contents/{DATASET_DIR}/schema.json")
        import base64
        schema_json = base64.b64decode(schema["content"]).decode()
        import json as _json
        schema_d = _json.loads(schema_json)
        print(f"  dataset: {schema_d.get('dataset')} (publication #{schema_d.get('publication_id')})")
        print(f"  source: {schema_d.get('source_url')}")
    except Exception as e:  # noqa: BLE001
        print(f"  schema.json FAILED to load: {e}")

    try:
        vintages = list_vintages()
        print(f"  available vintages: {vintages}")
        latest = vintages[-1]
        data = fetch_vintage(latest)
        print(f"  latest vintage: {latest}  (FY{data['fyMin']}-FY{data['fyMax']})")
        print(f"  {vintage_label(data)}")
        f = S.freshness("CBO 10-year budget projections", f"{latest}-01", S.FRESHNESS_DAYS_BY_FREQ["Annual"])
        fresh_s = "STALE" if f["stale"] else "ok"
        print(f"  freshness: {f['age_days']}d old, {S.FRESHNESS_DAYS_BY_FREQ['Annual']}d threshold, {fresh_s}")
        end_fy = data["fyMax"]
        print(f"  debt/GDP at end of window (FY{end_fy}): "
              f"{data['debt_held_by_public_gdp_share'][end_fy]:.1f}%")
        print(f"  debt/revenue at end of window (FY{end_fy}): "
              f"{data['debt_held_by_public'][end_fy] / data['rev_total'][end_fy] * 100:.1f}%")
        print(f"  CBO's own assumed avg interest rate on debt (FY{end_fy}): "
              f"{data['debt_avg_interest_rate'][end_fy]:.2f}%")
    except Exception as e:  # noqa: BLE001
        print(f"  FAILED: {e}")

    # Calibration targets (STATUS.md §9): Dalio's own vintage, June 2024.
    try:
        cal = fetch_vintage("2024-06")
        fy10 = cal["fyMin"] + 10
        debt_gdp = cal["debt_held_by_public_gdp_share"].get(fy10)
        debt_rev = (cal["debt_held_by_public"][fy10] / cal["rev_total"][fy10] * 100
                    if fy10 in cal["debt_held_by_public"] and fy10 in cal["rev_total"] else None)
        print(f"\n  Calibration (Dalio's own vintage, 2024-06, FY{fy10} = 10y out from FY{cal['fyMin']}):")
        print(f"    debt/GDP: {debt_gdp:.1f}%  (book: 122%)")
        if debt_rev is not None:
            print(f"    debt/revenue: {debt_rev:.1f}%  (book: ~700%)")
    except Exception as e:  # noqa: BLE001
        print(f"  calibration-vintage check FAILED: {e}")
