#!/usr/bin/env python3
"""Fetch public debt-risk series from FRED and build public/data.json.

Usage:
    python scripts/fetch.py --verify     # check every FRED ID, print a table, exit
    python scripts/fetch.py              # verify (light) + fetch + build data.json
    python scripts/fetch.py --force      # build even if a value jumped past the guard

Design goals (from the brief):
  * No hardcoded figures — live numbers come from FRED, model/manual numbers
    from data/manual.json.
  * Fail loudly — empty/404 series, or a value that moved more than
    MOVE_THRESHOLD vs the last run, exits non-zero so the CI run goes red.
  * Never write partial output over a good file — the new data.json is built
    and validated fully in memory, then written atomically via os.replace.

Requires the FRED_API_KEY environment variable (a GitHub secret in CI).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import requests

import series as S
import treasury as T

FRED = "https://api.stlouisfed.org/fred"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "data.json"
MANUAL = ROOT / "data" / "manual.json"

# A live value moving more than this (relative) vs the previous run is treated
# as suspicious and fails the build unless --force is passed.
MOVE_THRESHOLD = 0.25

MINUS = "−"  # proper minus sign, matching the UI


# --- FRED client ---------------------------------------------------------

def _key() -> str:
    k = os.environ.get("FRED_API_KEY")
    if not k:
        sys.exit("ERROR: FRED_API_KEY is not set (add it as a GitHub secret).")
    return k


def fred_get(path: str, **params):
    params = {"api_key": _key(), "file_type": "json", **params}
    last = None
    for i in range(4):  # retry transient drops: 1s, 2s, 4s
        try:
            r = requests.get(f"{FRED}/{path}", params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            last = e
            if i < 3:
                time.sleep(2 ** i)
    raise RuntimeError(f"FRED request {path} failed after 4 tries: {last}")


def series_meta(series_id: str) -> dict:
    data = fred_get("series", series_id=series_id)
    seriess = data.get("seriess") or []
    if not seriess:
        raise RuntimeError(f"{series_id}: no metadata returned")
    return seriess[0]


def series_obs(series_id: str):
    """Return (units, [(date, value)] ascending, missing skipped)."""
    meta = series_meta(series_id)
    data = fred_get("series/observations", series_id=series_id, sort_order="asc")
    obs = []
    for o in data.get("observations", []):
        v = o.get("value", ".")
        if v in (".", "", None):
            continue
        try:
            obs.append((dt.date.fromisoformat(o["date"]), float(v)))
        except ValueError:
            continue
    if not obs:
        raise RuntimeError(f"{series_id}: no usable observations")
    return meta.get("units", ""), obs


def search_suggestions(text: str, n: int = 3):
    try:
        data = fred_get("series/search", search_text=text, limit=n,
                        order_by="popularity", sort_order="desc")
        return [(s["id"], s.get("title", "")) for s in data.get("seriess", [])[:n]]
    except Exception:
        return []


# --- verification (brief step 2) -----------------------------------------

def verify() -> int:
    print(f"Verifying {len(S.FRED_SERIES)} FRED series against the live API\n")
    header = f"{'ID':<18} {'OK':<3} {'FREQ':<10} {'UNITS':<28} {'START':<12} TITLE"
    print(header)
    print("-" * len(header))
    failures = []
    for sid, expect in S.FRED_SERIES.items():
        try:
            m = series_meta(sid)
            freq = m.get("frequency_short") or m.get("frequency", "")
            units = (m.get("units", "") or "")[:27]
            start = m.get("observation_start", "")
            title = (m.get("title", "") or "")[:40]
            print(f"{sid:<18} {'yes':<3} {freq:<10} {units:<28} {start:<12} {title}")
        except Exception as e:
            failures.append((sid, expect, str(e)))
            print(f"{sid:<18} {'NO':<3} -- FAILED: {e}")

    fred_ok = not failures
    if failures:
        print("\n" + "=" * 60)
        print(f"{len(failures)} series failed to resolve:")
        for sid, expect, err in failures:
            print(f"\n  {sid}  ({expect['label']}) — {err}")
            for cand_id, cand_title in search_suggestions(expect["label"]):
                print(f"      candidate: {cand_id}  {cand_title}")
        print("\nFix the IDs in scripts/series.py, then re-run --verify.")
    else:
        print("\nAll FRED series resolved. Review units/frequency above.")

    # Treasury Fiscal Data (no key) — dumps real schema + the computed ratio.
    treasury_ok = T.verify()

    return 0 if (fred_ok and treasury_ok) else 1


# --- formatting ----------------------------------------------------------

def pct_display(v, decimals=0):
    q = round(v, decimals)
    s = f"{abs(q):.{decimals}f}"
    return (MINUS if q < 0 else "") + s + "%"


def num(v):
    return round(v, 3)


# --- build ---------------------------------------------------------------

def _prev_values():
    """{key: value} of live numeric values from the existing data.json, for the
    move guard. Missing/seed file -> empty (first run is exempt)."""
    if not OUT.exists():
        return {}
    try:
        prev = json.loads(OUT.read_text())
        if prev.get("meta", {}).get("seed"):
            return {}
        out = {}
        us = prev.get("countries", {}).get("US", {})
        for v in us.get("vitals", []):
            if v.get("tag") == "live" and isinstance(v.get("value"), (int, float)):
                out[v["key"]] = v["value"]
        return out
    except Exception:
        return {}


def _check_move(key, new_val, prev, force):
    old = prev.get(key)
    if old is None or old == 0:
        return
    rel = abs(new_val - old) / abs(old)
    if rel > MOVE_THRESHOLD and not force:
        sys.exit(
            f"ERROR: {key} moved {rel:.0%} ({old} -> {new_val}), over the "
            f"{MOVE_THRESHOLD:.0%} guard. Re-run with --force if this is real."
        )


def build_us(manual: dict, force: bool) -> dict:
    mu = manual["US"]
    prev = _prev_values()

    # --- fetch every FRED series we need ---
    need = ["FYGFGDQ188S", "GDP", "TCMDO", "IEABC", "TRESEGUSM052N"]
    raw = {}
    for sid in need:
        units, obs = series_obs(sid)  # raises loudly on empty/404
        raw[sid] = (units, obs)

    # --- live + derived metrics ---
    du, dobs = raw["FYGFGDQ188S"]
    debt = {
        "latest": num(dobs[-1][1]),
        "asOf": S.q_label(S.quarter_key(dobs[-1][0])),
        "history": S.quarterly_history(S.as_quarterly(dobs)),
    }
    # Debt service vs revenue — budget basis, from Treasury (no FRED).
    service = T.debt_service_ratio()
    if not (5.0 <= service["latest"] <= 40.0):
        raise RuntimeError(
            f"validation: Treasury debt-service ratio {service['latest']}% is "
            "outside the sane 5-40% band — likely a wrong field/column mapping. "
            "Check the Treasury schema dumped by --verify before trusting it."
        )
    reserves = S.reserves_pct_gdp(raw["TRESEGUSM052N"][1], raw["TRESEGUSM052N"][0],
                                  raw["GDP"][1], raw["GDP"][0])
    total_debt = S.total_debt_pct_gdp(raw["TCMDO"][1], raw["TCMDO"][0],
                                      raw["GDP"][1], raw["GDP"][0])
    ca_units = raw["IEABC"][0]
    annualized = "annual rate" in (ca_units or "").lower()
    current_acct = S.current_account_pct_gdp_3yr(raw["IEABC"][1], ca_units,
                                                 raw["GDP"][1], raw["GDP"][0], annualized)

    # --- move guards on the positive-level ratios ---
    _check_move("debt_to_gdp", debt["latest"], prev, force)
    _check_move("debt_service_to_revenue", service["latest"], prev, force)
    _check_move("reserves_to_gdp", reserves["latest"], prev, force)

    def live_row(label, metric, tone, src, unit, decimals=0):
        return {
            "label": label, "value": num(metric["latest"]),
            "display": pct_display(metric["latest"], decimals), "unit": unit,
            "tone": tone, "tag": "live", "src": src, "asOf": metric["asOf"],
            "history": metric["history"],
        }

    def manual_row(label, spec, tag="manual"):
        row = {"label": label, "display": spec["display"], "unit": spec.get("unit", ""),
               "tone": spec.get("tone", "neutral"), "tag": tag, "src": spec.get("src", "—")}
        if "value" in spec:
            row["value"] = spec["value"]
        if "asOf" in spec:
            row["asOf"] = spec["asOf"]
        if "history" in spec:
            row["history"] = spec["history"]
        return row

    rr = mu["realRatesAssessment"]
    rc = mu["reserveCurrency"]

    vitals = [
        {"key": "debt_to_gdp", "label": "Debt vs income", **_vital(debt, "risk",
            "Debt held by the public near one year of national income; projected to keep climbing.",
            "FRED: FYGFGDQ188S", "of GDP")},
        {"key": "debt_service_to_revenue", "label": "Debt service vs income", **_vital(service, "risk",
            "Interest alone eats roughly a fifth of federal revenue — before principal.",
            "derived · Treasury (budget basis)", "of revenue")},
        {"key": "real_rates", "label": "Rates vs inflation & growth", "value": None,
            "display": rr["display"], "unit": rr.get("unit", "real rates"), "tone": rr.get("tone", "neutral"),
            "read": rr["read"], "tag": "model", "src": "Dalio assessment", "asOf": mu["baseline"]},
        {"key": "reserves_to_gdp", "label": "Debt & service vs savings", **_vital(reserves, "risk",
            "Almost no liquid buffer (no sovereign wealth), so little protection if demand for the debt drops.",
            "derived · FRED / IMF", "reserves / GDP")},
    ]

    gov_panel = {
        "eyebrow": "Government debt", "tag": "live",
        "note": "Very large debt with little liquid backing. Who holds it matters: foreign holders can leave faster than domestic ones.",
        "rows": [
            manual_row("Gov assets − gov debt", mu["govAssetsMinusDebt"]),
            live_row("Government debt (held by public)", debt, "risk", "FRED: FYGFGDQ188S", "of GDP"),
            manual_row("Debt, 10-yr projection", mu["cboProjection"]),
            manual_row("— held by central bank", mu["holders"]["centralBank"]),
            manual_row("— held by domestic players", mu["holders"]["domestic"]),
            manual_row("— held abroad", mu["holders"]["abroad"]),
            manual_row("Share in hard (foreign) FX", mu["shareHardFX"]),
            live_row("Government interest", service, "risk", "derived · Treasury", "of revenue"),
        ],
    }
    reserves_panel = {
        "eyebrow": "Liquid reserves", "tag": "live",
        "note": "The cushion a country can draw on before it must default or print. The US has very little.",
        "rows": [
            live_row("FX reserves", reserves, "risk", "IMF / FRED", "of GDP"),
            manual_row("Sovereign wealth assets", mu["sovereignWealth"]),
        ],
    }
    broader_panel = {
        "eyebrow": "Broader health", "tag": "live",
        "note": "Economy-wide leverage and the external balance — how dependent the country is on foreign financing.",
        "rows": [
            live_row("Total debt (all sectors)", total_debt, "caution", "FRED Z.1", "of GDP"),
            live_row("Current account, 3-yr avg", current_acct, "caution", "BEA / FRED", "of GDP"),
        ],
    }
    reserve_ccy_panel = {
        "eyebrow": "Reserve-currency status", "tag": "manual", "accent": "#5B8DD6",
        "note": rc["note"],
        "rows": [
            manual_row("World trade in USD", rc["trade"]),
            manual_row("World debt in USD", rc["debt"]),
            manual_row("Global equity market cap", rc["equity"]),
            manual_row("World CB reserves in USD", rc["cbReserves"]),
        ],
    }

    country = {
        "name": mu["name"], "baseline": mu["baseline"],
        "headline": {
            "govLT": {**mu["headline"]["govLT"], "source": "model"},
            "cbLT": {**mu["headline"]["cbLT"], "source": "model"},
            "shortTerm": {**mu["headline"]["shortTerm"], "source": "model"},
        },
        "vitals": vitals,
        "panels": [gov_panel, reserves_panel, broader_panel, reserve_ccy_panel],
        "govGauge": {**mu["govGauge"], "source": "model"},
        "cbGauge": {**mu["cbGauge"], "source": "model"},
        "redFlags": mu["redFlags"],
        "provenance": {
            "modelSnapshot": mu.get("modelSnapshot"),
            "manualLastChecked": mu.get("lastChecked"),
            "currentAccountAnnualizedInput": annualized,
        },
    }
    _validate(country)
    return country


def _vital(metric, tone, read, src, unit):
    return {
        "value": num(metric["latest"]), "display": pct_display(metric["latest"]),
        "unit": unit, "tone": tone, "read": read, "tag": "live",
        "src": src, "asOf": metric["asOf"], "history": metric["history"],
    }


def _validate(country: dict):
    """Guard against partial/garbage output before it can overwrite a good file."""
    live = [v for v in country["vitals"] if v.get("tag") == "live"]
    if len(live) < 3:
        raise RuntimeError("validation: expected >=3 live vitals, refusing to write")
    for v in live:
        if not isinstance(v.get("value"), (int, float)):
            raise RuntimeError(f"validation: live vital {v['key']} has no numeric value")
        if len(v.get("history", [])) < 2:
            raise RuntimeError(f"validation: live vital {v['key']} has no history")


def atomic_write(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)  # atomic on POSIX
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main():
    ap = argparse.ArgumentParser(description="Fetch FRED data and build public/data.json")
    ap.add_argument("--verify", action="store_true", help="verify FRED IDs and exit")
    ap.add_argument("--force", action="store_true", help="bypass the value-move guard")
    args = ap.parse_args()

    if args.verify:
        sys.exit(verify())

    manual = json.loads(MANUAL.read_text())
    country = build_us(manual, args.force)
    payload = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "meta": {"seed": False, "schema": 1},
        "countries": {"US": country},
    }
    atomic_write(OUT, payload)
    print(f"Wrote {OUT.relative_to(ROOT)} — generatedAt {payload['generatedAt']}")
    for v in country["vitals"]:
        if v.get("tag") == "live":
            print(f"  {v['key']:<26} {v['display']:>8}  ({v['asOf']}, {len(v['history'])} pts)")


if __name__ == "__main__":
    main()
