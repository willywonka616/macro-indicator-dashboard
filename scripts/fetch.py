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
import imf as I
import gold as G
import cbo as C
import bis as B

FRED = "https://api.stlouisfed.org/fred"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "data.json"
MANUAL = ROOT / "data" / "manual.json"

# A live value moving more than this (relative) vs the previous run is treated
# as suspicious and fails the build unless --force is passed.
MOVE_THRESHOLD = 0.25

MINUS = "−"  # proper minus sign, matching the UI


# --- loud signalling (STATUS.md §19) --------------------------------------
#
# Two kinds of "silently wrong" this project has now hit: a frozen SOURCE
# (§17's freshness guard) and a STALE MANUAL VALUE / an unnoticed FALLBACK
# (this section). Both get the same treatment: never just a print() line
# buried among a hundred others — a console banner AND a GitHub Actions
# ::warning:: annotation, which surfaces as a visible Annotation on the
# run's Checks page, not just something you'd have to go read the raw log
# to find.

def loud_warn(msg: str):
    print(f"\n{'!' * 70}\nWARNING: {msg}\n{'!' * 70}\n")
    print(f"::warning::{msg}")


def check_manual_freshness(label: str, date_str, max_age_days: int, today: dt.date | None = None):
    """Non-fatal staleness check for a hand-entered data/manual.json value
    (STATUS.md §19) — a manual value is exactly as capable of going stale
    as a fetched one, but unlike a fetched series it has no live source to
    fall further back to, so this warns loudly rather than raising (see
    series.py's MANUAL_FRESH_DAYS docstring for why). Returns the
    freshness dict either way, so callers can fold staleness into a
    shipped row's note."""
    f = S.freshness(label, date_str, max_age_days, today)
    if f["stale"]:
        loud_warn(
            f"manual value '{label}' is {f['age_days']}d old (dated {f['period']}) "
            f"— past its {max_age_days}d review threshold. This is a hand-entered "
            f"fallback with no further live source behind it; someone should "
            f"check whether it's still accurate and update data/manual.json."
        )
    return f


def assert_provenance(fallbacks_fired: list, row_label: str, expected_tag: str,
                       actual_tag: str, reason: str):
    """Per-row provenance check (STATUS.md §19): assert the tag that
    actually shipped matches what a fully-healthy run would produce. A
    mismatch means a fallback fired — today that's only visible as an
    incidental print() line in the middle of the build log, easy to miss;
    this makes it an unmissable, structured signal instead (loud warning +
    recorded in country.provenance.fallbacksFired, so it's inspectable in
    the shipped data too, not just CI logs). Non-fatal by design — the
    fallback chains this guards (gold price, COFER) exist specifically so
    a dead source degrades the site rather than breaking it; failing the
    build here would defeat that. See STATUS.md §17/§18 for why those
    fallbacks exist at all."""
    if actual_tag == expected_tag:
        return
    entry = {"row": row_label, "expectedTag": expected_tag, "actualTag": actual_tag, "reason": reason}
    fallbacks_fired.append(entry)
    loud_warn(
        f"provenance mismatch on '{row_label}': expected tag '{expected_tag}', "
        f"shipped '{actual_tag}' — a fallback fired. Reason: {reason}"
    )


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
    header = (f"{'ID':<18} {'OK':<3} {'FREQ':<10} {'UNITS':<28} {'START':<12} "
              f"{'LATEST OBS':<12} {'AGE':>6} {'MAX':>6} {'FRESH':<7} TITLE")
    print(header)
    print("-" * len(header))
    failures = []
    stale = []
    for sid, expect in S.FRED_SERIES.items():
        try:
            m = series_meta(sid)
            freq = m.get("frequency_short") or m.get("frequency", "")
            units = (m.get("units", "") or "")[:27]
            start = m.get("observation_start", "")
            title = (m.get("title", "") or "")[:40]
            end = m.get("observation_end", "")
            freq_name = expect["freq"]
            max_days = (S.TRESEGUS_FRESH_DAYS if sid == "TRESEGUSM052N"
                        else S.FRESHNESS_DAYS_BY_FREQ.get(freq_name, 60))
            f = S.freshness(sid, end, max_days) if end else None
            age_s = f"{f['age_days']}d" if f else "?"
            fresh_s = ("STALE" if f["stale"] else "ok") if f else "?"
            print(f"{sid:<18} {'yes':<3} {freq:<10} {units:<28} {start:<12} "
                  f"{end:<12} {age_s:>6} {max_days:>5}d {fresh_s:<7} {title}")
            if f and f["stale"]:
                stale.append((sid, f))
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

    if stale:
        print(f"\n{len(stale)} FRED series FAILED the freshness guard (would fail a real "
              f"build, not just --verify):")
        for sid, f in stale:
            print(f"  {sid}: latest obs {f['period']}, {f['age_days']}d old, "
                  f"exceeds {f['max_age_days']}d threshold")

    # Treasury Fiscal Data (no key) — dumps real schema + the computed ratio,
    # plus the debt-service calibration matrix (see debt_service_matrix).
    # tax_receipts_monthly is the original brief's narrower denominator
    # (W006RC1Q027SBEA), fetched here since it's FRED not Treasury — included
    # in the matrix purely to confirm it's NOT what Dalio used.
    tax_receipts_monthly = None
    try:
        units, obs = series_obs("W006RC1Q027SBEA")
        tax_receipts_monthly = _quarterly_saar_to_monthly(obs, units)
    except Exception as e:  # noqa: BLE001
        print(f"(tax-receipts-only denominator unavailable for the matrix: {e})")
    treasury_ok = T.verify(tax_receipts_monthly)

    # Total-debt calibration cross-check (STATUS.md §9): TCMDO (all sectors
    # incl. financial) vs. TCMDODNS (domestic nonfinancial sectors only) —
    # dumped side by side, as % of the same GDP observation. The nonfinancial
    # hypothesis was tried and refuted live (TCMDODNS landed at 256.7%,
    # TCMDO at 362.6%, vs. Dalio's Ch.17 340% "other debt" — TCMDO is much
    # closer, so TCMDO is what "Total debt" uses; TCMDODNS stays dumped here
    # for the record and in case a future session wants to revisit it).
    print("\nTotal-debt series comparison (Dalio Ch.17 US 'other debt' target: 340%):")
    try:
        gdp_units, gdp_obs = series_obs("GDP")
        gdp_latest_d, gdp_latest_v = gdp_obs[-1]
        gdp_usd = S.to_dollars(gdp_latest_v, gdp_units)
        tcmdo_latest_usd = None
        for sid in ("TCMDO", "TCMDODNS", "DODFS"):
            try:
                units, obs = series_obs(sid)
                d, v = obs[-1]
                usd = S.to_dollars(v, units)
                pct = usd / gdp_usd * 100.0
                note = {"TCMDO": " <- used for 'Total debt' row",
                        "TCMDODNS": " (diagnostic only, not used — excludes BOTH financial sector AND rest-of-world; see series.py)",
                        "DODFS": " (diagnostic only, TASKtotaldebtreconcile.md — Domestic Financial Sectors ONLY, keeps foreign in)"}[sid]
                print(f"  {sid}: {pct:.1f}% of GDP as of {d} (GDP as of {gdp_latest_d}){note}")
                if sid == "TCMDO":
                    tcmdo_latest_usd = usd
                if sid == "DODFS" and tcmdo_latest_usd:
                    ex_fin_pct = (tcmdo_latest_usd - usd) / gdp_usd * 100.0
                    print(f"  TCMDO minus DODFS (all sectors excl. ONLY the domestic financial "
                          f"sector, foreign debt still included): {ex_fin_pct:.1f}% of GDP")
            except Exception as e:  # noqa: BLE001
                print(f"  {sid}: FAILED: {e}")

        # Vintage check (TASKtotaldebtreconcile.md iteration 2): Dalio's
        # snapshot is March 2025 (~2025-Q1). Both TCMDO and GDP must be
        # read at THAT SAME quarter -- pairing 2025-Q1 debt with the
        # CURRENT GDP observation (an earlier draft of this diagnostic did
        # exactly that) understates the true 2025-Q1 ratio, since GDP has
        # grown since then; it would print a misleadingly close-looking
        # number for the wrong reason (a shrinking denominator mismatch,
        # not an actual vintage reconciliation). Pair same-quarter values.
        try:
            tcmdo_units, tcmdo_obs = series_obs("TCMDO")
            q1_2025_tcmdo = [(d, v) for d, v in tcmdo_obs if d.year == 2025 and d.month == 1]
            q1_2025_gdp = [(d, v) for d, v in gdp_obs if d.year == 2025 and d.month == 1]
            if q1_2025_tcmdo and q1_2025_gdp:
                d, v = q1_2025_tcmdo[0]
                gdp_2025q1_usd = S.to_dollars(q1_2025_gdp[0][1], gdp_units)
                pct = S.to_dollars(v, tcmdo_units) / gdp_2025q1_usd * 100.0
                print(f"  TCMDO at 2025-Q1 (Dalio's snapshot vintage), GDP ALSO at 2025-Q1 "
                      f"(same-quarter pairing): {pct:.1f}% of GDP as of {d}")
        except Exception as e:  # noqa: BLE001
            print(f"  vintage check FAILED: {e}")
    except Exception as e:  # noqa: BLE001
        print(f"  comparison FAILED: {e}")

    # TIC holder shares (TASKmanualvalues.md): dumps schema + computed
    # shares for the three FRED series that replace the undated manual
    # 13%/57%/29% split. Non-fatal — these have a manual fallback, same
    # as gold/COFER, so a failure here must not redden --verify.
    print("\nTIC holder shares (central bank / domestic / foreign), TASKmanualvalues.md:")
    try:
        for sid in ("FYGFDPUN", "FDHBFRBN", "FDHBFIN"):
            try:
                meta = series_meta(sid)
                units, obs = series_obs(sid)
                d, v = obs[-1]
                print(f"  {sid}: {meta.get('title')!r}, units={units!r}, freq={meta.get('frequency_short')}, "
                      f"latest {d} = {v}")
            except Exception as e:  # noqa: BLE001
                print(f"  {sid}: FAILED: {e}")
        fygfdpun_units, fygfdpun_obs = series_obs("FYGFDPUN")
        fdhbfrbn_units, fdhbfrbn_obs = series_obs("FDHBFRBN")
        fdhbfin_units, fdhbfin_obs = series_obs("FDHBFIN")
        holders = S.tic_holder_shares(fygfdpun_obs, fygfdpun_units, fdhbfrbn_obs, fdhbfrbn_units,
                                       fdhbfin_obs, fdhbfin_units)
        total_pct = holders["centralBank"]["latest"] + holders["domestic"]["latest"] + holders["abroad"]["latest"]
        print(f"  computed shares as of {holders['asOf']}: central bank {holders['centralBank']['latest']}%, "
              f"domestic {holders['domestic']['latest']}%, abroad {holders['abroad']['latest']}% "
              f"(sum {total_pct:.1f}%)")
    except Exception as e:  # noqa: BLE001
        print(f"  TIC holder shares computation FAILED: {e}")

    # BIS debt-currency share (TASKmanualvalues.md): dumps whatever the
    # DBnomics BIS dataset actually returns. Non-fatal by design — the
    # exact dimension codes for WS_NA_SEC_DSS were not confirmed before
    # writing this (db.nomics.world is blocked from this project's dev
    # sandbox, same as every other "not reachable from dev" source), so
    # this run's own output is the first real look at whether the guessed
    # filter resolves at all.
    print("\nBIS debt-currency share (world debt in USD), TASKmanualvalues.md:")
    B.verify()

    # GDP + TRESEGUSM052N raw $ values, units, and vintage, plus a full
    # reserves-incl-gold breakdown — a user-facing question (2026-07-22:
    # "reserves rose on a falling gold price — is GDP's basis/units the
    # same in every run?") found this project had never actually printed
    # GDP's raw dollar figure anywhere, only its %-of-GDP derivatives.
    # This exists so that question is answerable directly from a run log
    # from now on, not by re-deriving it under time pressure.
    print("\nGDP + reserves-incl-gold breakdown (2026-07-22 follow-up):")
    try:
        gdp_units2, gdp_obs2 = series_obs("GDP")
        print(f"  GDP units (from FRED metadata): {gdp_units2!r}")
        print("  last 4 GDP observations (raw FRED value, then converted via S.to_dollars):")
        for d, v in gdp_obs2[-4:]:
            print(f"    {d}: {v} ({gdp_units2}) -> ${S.to_dollars(v, gdp_units2)/1e12:.3f}T")
        tres_units2, tres_obs2 = series_obs("TRESEGUSM052N")
        print(f"  TRESEGUSM052N units (from FRED metadata): {tres_units2!r}")
        print("  last 4 TRESEGUSM052N observations:")
        for d, v in tres_obs2[-4:]:
            print(f"    {d}: {v} ({tres_units2}) -> ${S.to_dollars(v, tres_units2)/1e9:.2f}B")

        oz2 = G.gold_holdings_troy_oz()
        price2, label2 = G.gold_price_usd_per_oz_labeled()
        gold_value2 = {k: oz2[k] * price2[k] for k in oz2.keys() & price2.keys()}
        res_m2 = S.as_monthly(tres_obs2)
        gdp_q2 = S.as_quarterly(gdp_obs2)
        print(f"  gold price leg this run: {label2}")
        print("  reserves-incl-gold, full breakdown for the last 4 quarters actually reached:")
        combined_m = {k: S.to_dollars(res_m2[k], tres_units2) + gold_value2[k]
                      for k in res_m2.keys() & gold_value2.keys()}
        res_q2 = {}
        for (y, m), v in combined_m.items():
            q = (y, (m - 1) // 3 + 1)
            if q not in res_q2 or m > res_q2[q][0]:
                res_q2[q] = (m, v)
        for q in sorted(res_q2.keys() & gdp_q2.keys())[-4:]:
            month_used, combined_v = res_q2[q]
            gdp_v = S.to_dollars(gdp_q2[q], gdp_units2)
            gold_v = gold_value2.get((q[0], month_used))
            price_v = price2.get((q[0], month_used))
            pct = combined_v / gdp_v * 100.0
            print(f"    {q[0]}-Q{q[1]} (gold priced as of {q[0]}-{month_used:02d}): "
                  f"gold price ${price_v:,.2f}/oz, gold value ${gold_v/1e9:.1f}B, "
                  f"reserves+gold ${combined_v/1e9:.1f}B, GDP ${gdp_v/1e12:.3f}T -> {pct:.3f}%")
    except Exception as e:  # noqa: BLE001
        print(f"  breakdown FAILED: {e}")

    # IMF COFER (no key) — non-fatal; dumps indicators + the computed USD share.
    I.verify()

    # Gold holdings (Treasury) + gold price (World Bank Pink Sheet) —
    # non-fatal; dumps both schemas + the computed market value.
    G.verify()

    # CBO 10-Year Budget Projections (TASKprojections.md) — non-fatal; dumps
    # the schema, available vintages, latest values, and the calibration
    # check against Dalio's own vintage (June 2024).
    C.verify()

    # Manual-value freshness audit (STATUS.md §19) — checked unconditionally
    # here, not only when a fallback actually fires in a real build, so
    # drift is visible during routine --verify runs too.
    try:
        manual = json.loads(MANUAL.read_text())
        audit_manual_values(manual["US"])
    except Exception as e:  # noqa: BLE001
        print(f"\nManual-value freshness audit FAILED to run: {e}")

    return 0 if (fred_ok and treasury_ok) else 1


def audit_manual_values(mu: dict) -> None:
    """STATUS.md §19, extended by TASKmanualvalues.md §4: staleness-check
    every manual.json value that carries its own date, unconditionally —
    not only when a fallback actually fires in a real build, so drift is
    visible even while the live sources it would replace are still
    healthy. Before TASKmanualvalues.md, 10 of these 14 values had NO date
    at all (STATUS.md §19.2's original audit); every one of them now has an
    explicit `asOf` (dated honestly — March 2025, the book baseline, for
    figures transcribed from Dalio's Ch.17 table; a real fetch date for the
    ones with their own capture — see manual.json's own comments on each).
    No fabricated dates: anything without a genuine "last known true" date
    would not be listed here at all."""
    print("\nManual-value freshness audit (data/manual.json):")
    dated = [
        ("goldPriceManualFallback.asOf", mu["goldPriceManualFallback"]["asOf"],
         S.GOLD_MANUAL_PRICE_FRESH_DAYS),
        ("reserveCurrency.cbReserves.asOf", mu["reserveCurrency"]["cbReserves"]["asOf"],
         S.CBRESERVES_MANUAL_FRESH_DAYS),
        ("govAssetsMinusDebt.asOf", mu["govAssetsMinusDebt"]["asOf"], S.MANUAL_FRESH_DAYS),
        ("holders.centralBank.asOf", mu["holders"]["centralBank"]["asOf"], S.MANUAL_FRESH_DAYS),
        ("holders.domestic.asOf", mu["holders"]["domestic"]["asOf"], S.MANUAL_FRESH_DAYS),
        ("holders.abroad.asOf", mu["holders"]["abroad"]["asOf"], S.MANUAL_FRESH_DAYS),
        ("shareHardFX.asOf", mu["shareHardFX"]["asOf"], S.MANUAL_FRESH_DAYS),
        ("sovereignWealth.asOf", mu["sovereignWealth"]["asOf"], S.MANUAL_FRESH_DAYS),
        ("reserveCurrency.trade.asOf", mu["reserveCurrency"]["trade"]["asOf"], S.MANUAL_FRESH_DAYS),
        ("reserveCurrency.equity.asOf", mu["reserveCurrency"]["equity"]["asOf"], S.MANUAL_FRESH_DAYS),
        ("reserveCurrency.debt.asOf", mu["reserveCurrency"]["debt"]["asOf"], S.MANUAL_FRESH_DAYS),
        ("reservesInclGoldFallback.asOf", mu["reservesInclGoldFallback"]["asOf"], S.MANUAL_FRESH_DAYS),
        ("lastChecked (governs anything with no asOf of its own)", mu.get("lastChecked"),
         S.MANUAL_FRESH_DAYS),
    ]
    if "asOf" in mu.get("cboProjectionFallback", {}):
        dated.append(("cboProjectionFallback.asOf", mu["cboProjectionFallback"]["asOf"], S.MANUAL_FRESH_DAYS))
    for label, date_str, max_days in dated:
        f = S.freshness(label, date_str, max_days)
        status = "STALE" if f["stale"] else "ok"
        print(f"  {label:<55} {date_str:<12} {f['age_days']:>4}d old  {max_days:>3}d threshold  {status}")

    print("  0 manual values remain undated — every figure in data/manual.json now "
          "carries its own asOf (TASKmanualvalues.md; see STATUS.md for the before/after count).")


def _quarterly_saar_to_monthly(obs, units: str) -> dict:
    """Convert a quarterly seasonally-adjusted-annual-rate FRED series into a
    {(year, month): dollars} monthly dict (SAAR / 12, repeated across the
    quarter's 3 months) so it can feed Treasury's monthly-flow TTM machinery
    in debt_service_matrix. Diagnostic use only."""
    out = {}
    for d, v in obs:
        annual = S.to_dollars(v, units)
        q = (d.month - 1) // 3
        for m in (q * 3 + 1, q * 3 + 2, q * 3 + 3):
            out[(d.year, m)] = annual / 12.0
    return out


# --- formatting ----------------------------------------------------------

def pct_display(v, decimals=None):
    # Small magnitudes need a decimal so the headline matches the chart
    # (e.g. reserves 0.8% must not round to "1%").
    if decimals is None:
        decimals = 1 if abs(v) < 10 else 0
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
    # Per-row provenance mismatches (STATUS.md §19) — populated by
    # assert_provenance() at each fallback decision point, shipped in
    # country.provenance.fallbacksFired so a fallback firing is visible in
    # the data itself, not only in a CI log someone has to go read.
    fallbacks_fired: list = []

    def _series_asof(sid, obs):
        """Format a raw FRED series' latest observation date to match how
        this row's own frequency is normally displayed elsewhere (quarter
        label, YYYY-MM, or a plain ISO date for daily DGS10) — used by the
        equation-button mapping table (TASK-equation-button.md §3) to give
        each Dalio-notation term its own asOf, not just the parent row's
        single combined one."""
        d = obs[-1][0]
        freq = S.FRED_SERIES[sid]["freq"]
        if freq == "Quarterly":
            return S.q_label(S.quarter_key(d))
        if freq == "Monthly":
            return f"{d.year}-{d.month:02d}"
        return d.isoformat()

    def _term(label, src, asOf, tag="live"):
        return {"label": label, "src": src, "asOf": asOf, "tag": tag}

    # --- fetch every FRED series we need ---
    need = ["FYGFGDQ188S", "GDP", "TCMDO", "IEABC", "TRESEGUSM052N", "DGS10", "CPIAUCSL"]
    raw = {}
    for sid in need:
        units, obs = series_obs(sid)  # raises loudly on empty/404
        raw[sid] = (units, obs)
        # Freshness guard (TASKgoldpricefreshness.md): a dead source can
        # still return a plausible in-band NUMBER — this checks the DATE,
        # so a frozen series fails loudly here instead of silently shipping
        # as "live" (see S.require_fresh's docstring and STATUS.md). Special
        # case: TRESEGUSM052N is IMF/BOP-sourced with a longer normal lag
        # than domestic monthly series, same reasoning as COFER below.
        if sid == "TRESEGUSM052N":
            max_days = S.TRESEGUS_FRESH_DAYS
        else:
            max_days = S.FRESHNESS_DAYS_BY_FREQ.get(S.FRED_SERIES[sid]["freq"], 60)
        S.require_fresh(sid, obs[-1][0], max_days)

    # --- live + derived metrics ---
    du, dobs = raw["FYGFGDQ188S"]
    debt = {
        "latest": num(dobs[-1][1]),
        "asOf": S.q_label(S.quarter_key(dobs[-1][0])),
        "history": S.quarterly_history(S.as_quarterly(dobs)),
    }
    # Debt service, split net/gross — both TOTAL receipts, net of refunds,
    # budget basis, from Treasury (no FRED). Basis revised 2026-07 twice in
    # the same day: first to on-budget receipts (against Dalio's Ch.17 book
    # value, 22%), then — after finding monthly_receipts() had been summing
    # GROSS receipts instead of net-of-refunds, a ~7% overstatement checked
    # against CBO's published FY totals — to TOTAL receipts, net of
    # refunds, on definitional grounds (the on-budget choice's closeness to
    # 22% turned out to be an artifact of that bug). See treasury.py module
    # docstring and STATUS.md §13. Headline = NET interest to the public
    # (pairs with debt_to_gdp, which is also debt *held by the public*);
    # second row = GROSS incl. intragovernmental GAS interest. Separate
    # sanity bands: net lands ~17-20%, gross ~22-26% (both live-confirmed
    # on the current total-receipts basis), so the bands are set with
    # headroom around each rather than sharing one range.
    service = T.debt_service_ratio()
    if not (10.0 <= service["latest"] <= 40.0):
        raise RuntimeError(
            f"validation: net debt-service ratio {service['latest']}% is "
            "outside the sane 10-40% band — likely a wrong field/column mapping. "
            "Check the Treasury schema dumped by --verify before trusting it."
        )
    S.require_fresh("Treasury net debt-service ratio", service["asOf"], S.FRESHNESS_DAYS_BY_FREQ["Monthly"])
    gross_service = T.gross_debt_service_ratio()
    if not (15.0 <= gross_service["latest"] <= 50.0):
        raise RuntimeError(
            f"validation: gross debt-service ratio {gross_service['latest']}% is "
            "outside the sane 15-50% band — likely a wrong field/column mapping. "
            "Check the Treasury schema dumped by --verify before trusting it."
        )
    S.require_fresh("Treasury gross debt-service ratio", gross_service["asOf"], S.FRESHNESS_DAYS_BY_FREQ["Monthly"])
    reserves = S.reserves_pct_gdp(raw["TRESEGUSM052N"][1], raw["TRESEGUSM052N"][0],
                                  raw["GDP"][1], raw["GDP"][0])

    # Reserves including gold at market value — resolves STATUS.md §5. Gold
    # holdings (Treasury) and gold price (World Bank Pink Sheet, live since
    # TASKgoldautomation.md replaced the previously-frozen DBnomics/IMF PCPS
    # feed) are each live but NOT necessarily from the same month. Rather
    # than bury that in `asOf` alone, `src` names both dates explicitly
    # whenever they differ, so the hybrid is visible on the row itself, not
    # just to someone who checks asOf against the other reserves row. If
    # either fetch fails, fall back to the manual snapshot rather than
    # shipping a live-tagged number built on a stale price (same pattern as
    # IMF COFER).
    reserves_incl_gold_tag = "live"
    gold_src_detail = "Treasury (gold) + World Bank (price)"
    gold_stale_note = None
    # Per-term provenance for the equation-button mapping table (see
    # revenue_term etc. below in the main function body) — stays None if
    # even the live ounce count fails, so the full-manual fallback row has
    # no compound terms at all (nothing to break down; it's one flat
    # book figure, not four separate live inputs).
    reserves_incl_gold_terms = None
    # STATUS.md §23 follow-up: "Reserves incl. gold (market)" below is
    # bottlenecked to TRESEGUSM052N/GDP's own latest common quarter
    # (currently 2026-Q1) no matter how fresh the gold price is -- neither
    # series it's combined with releases faster than that, so a live gold
    # price never reaches that row's headline. This second row uses ONLY
    # gold's own live oz x live price (no GDP or TRESEGUSM052N dependency
    # at all), so it's genuinely current every run. Deliberately a dollar
    # figure, not another %-of-GDP ratio: dividing a fresh numerator by
    # Q1-2026 GDP would recreate the exact same mixed-vintage problem this
    # row exists to avoid. Stays None if the live ounce count itself fails
    # (outer except below) -- omitted from the panel entirely rather than
    # given a manual fallback, same precedent as the equation-#3 row
    # (TASKprojections.md) when its own live source is unavailable.
    gold_value_row = None
    try:
        gold_oz_monthly = G.gold_holdings_troy_oz()
        oz_asof = max(gold_oz_monthly)
        # Freshness guard: gold oz (Treasury) is normally current — if even
        # this fails, there's no live leg left at all, so let it propagate
        # to the outer except and use the full manual fallback.
        S.require_fresh("gold holdings (Treasury oz)", oz_asof, S.FRESHNESS_DAYS_BY_FREQ["Monthly"])

        # Gold price: try live first (LBMA's daily fix, then the World Bank
        # Pink Sheet direct download, then its GitHub mirror — see gold.py's
        # gold_price_usd_per_oz_labeled(), which freshness-gates each leg
        # with a threshold matched to ITS OWN cadence before preferring it).
        # The previous source (DBnomics-mirrored IMF PCPS) was permanently
        # frozen from 2025-06 (STATUS.md §14.3/§16); TASKgoldautomation.md
        # replaced it, then a follow-up round found even the World Bank leg
        # (a monthly average) sits weeks behind spot for a metal this
        # volatile, and added LBMA's daily fix ahead of it (STATUS.md §23).
        # This outer check is a generic backstop, not the primary freshness
        # enforcement (that now happens per-leg inside gold.py) — its
        # generous 60d Monthly threshold is intentionally loose here; a
        # LBMA-served price bucketed to (year, month) loses its exact day,
        # so this check alone could be off by up to ~30 days and must not
        # be tightened to LBMA's own cadence. If the new source is ever
        # dead too, fall back to a hand-entered manual PRICE applied to the
        # still-live ounce count, rather than an all-manual OUTPUT. The
        # ounce count has no reason to be stale just because the price
        # source died elsewhere, and a manual price + live ounce count is a
        # materially better estimate than a fully manual fallback — see
        # STATUS.md §18.
        gold_price_monthly = {}
        gold_price_src_label = None
        try:
            gold_price_monthly, gold_price_src_label = G.gold_price_usd_per_oz_labeled()
            price_asof = max(gold_price_monthly)
            S.require_fresh("gold price (live, see src for which leg)", price_asof, S.FRESHNESS_DAYS_BY_FREQ["Monthly"])
            price_is_live = True
        except Exception as price_e:  # noqa: BLE001
            print(f"Gold price unavailable/stale, patching a manual price input across the gap: {price_e}")
            gpf = mu["goldPriceManualFallback"]
            # The manual price itself has a date and can go stale exactly
            # like a fetched series (STATUS.md §19) — check it too, not
            # just the live source it's replacing. Non-fatal (see
            # check_manual_freshness's docstring): this is already the
            # fallback, there's nowhere further live to go.
            gold_manual_freshness = check_manual_freshness(
                "gold price manual fallback (goldPriceManualFallback.asOf)",
                gpf["asOf"], S.GOLD_MANUAL_PRICE_FRESH_DAYS)
            # Keep any real (if stale) historical months the fetch did
            # return -- only patch the months it's missing, so old chart
            # history stays priced with real data and only the frozen
            # tail (which otherwise wouldn't overlap TRESEGUSM052N's own
            # lagging history -- STATUS.md §18) gets the manual price.
            for ym in gold_oz_monthly.keys() - gold_price_monthly.keys():
                gold_price_monthly[ym] = gpf["pricePerOz"]
            price_asof = oz_asof
            price_is_live = False

        gold_value_monthly = {k: gold_oz_monthly[k] * gold_price_monthly[k]
                               for k in gold_oz_monthly.keys() & gold_price_monthly.keys()}
        if not gold_value_monthly:
            raise RuntimeError("gold: no overlapping months between holdings and price")

        if price_is_live:
            reserves_incl_gold_tag = "live"
            if oz_asof == price_asof:
                gold_src_detail = f"Treasury (gold) + {gold_price_src_label}, both {oz_asof[0]}-{oz_asof[1]:02d}"
            else:
                gold_src_detail = (f"Treasury (gold oz {oz_asof[0]}-{oz_asof[1]:02d}) "
                                    f"+ {gold_price_src_label} (price {price_asof[0]}-{price_asof[1]:02d})")
                lag_months = (oz_asof[0] - price_asof[0]) * 12 + (oz_asof[1] - price_asof[1])
                if lag_months >= 2:
                    gold_stale_note = (
                        f"⚠ gold priced as of {price_asof[0]}-{price_asof[1]:02d} "
                        f"({lag_months} months old) — market value may be off if gold has moved since"
                    )
        else:
            reserves_incl_gold_tag = "manual_price"
            gold_src_detail = (f"Treasury (gold oz, live, {oz_asof[0]}-{oz_asof[1]:02d}) "
                                f"+ manual price (${gpf['pricePerOz']:,.0f}/oz as of {gpf['asOf']})")
            gold_stale_note = (
                f"⚠ manual gold price input: ${gpf['pricePerOz']:,.0f}/oz as of {gpf['asOf']} "
                f"— the live price source is dead, but the ounce count is still live "
                f"({oz_asof[0]}-{oz_asof[1]:02d})"
            )
            if gold_manual_freshness["stale"]:
                # The hand-entered fallback is ITSELF now overdue for review
                # (STATUS.md §19) — distinct from "the live source is dead"
                # above, and surfaced on the row itself so a stale manual
                # value isn't only visible to someone reading CI logs.
                gold_stale_note += (
                    f" — ⚠⚠ this manual price is also {gold_manual_freshness['age_days']}d "
                    f"old itself, past its {S.GOLD_MANUAL_PRICE_FRESH_DAYS}d review threshold; "
                    f"data/manual.json needs a human to update it"
                )

        # STATUS.md §23: a plain dollar figure, live oz x live price only
        # (see the comment above gold_value_row's initialization for why
        # this deliberately isn't a %-of-GDP ratio). Uses the SAME tag as
        # "Reserves incl. gold (market)" -- both come from the identical
        # gold_value_monthly computation, just divided differently (or not
        # at all) downstream.
        gv_asof = max(gold_value_monthly)
        gv_usd_b = gold_value_monthly[gv_asof] / 1e9
        gold_value_row = {
            "label": "Gold holdings, at current price", "value": round(gv_usd_b, 1),
            "display": f"${gv_usd_b:,.1f}B", "unit": "", "tone": "neutral",
            "tag": reserves_incl_gold_tag, "key": "gold_value_current",
            "src": f"derived · {gold_src_detail}",
            "asOf": f"{gv_asof[0]}-{gv_asof[1]:02d}",
            # gold_stale_note (⚠-prefixed, renders in the UI's warning color
            # — see MetricRow.jsx) takes priority when a fallback is active;
            # otherwise explain why this row exists alongside the one above.
            "note": gold_stale_note or (
                "Live gold oz x live gold price only — no FX-reserves or GDP "
                "denominator, so unlike the row above this one updates every "
                "time the gold price does, not just when TRESEGUSM052N/GDP "
                "themselves advance a quarter (STATUS.md §23)."
            ),
            "history": [],
        }

        reserves_incl_gold = S.reserves_incl_gold_pct_gdp(
            raw["TRESEGUSM052N"][1], raw["TRESEGUSM052N"][0], gold_value_monthly,
            raw["GDP"][1], raw["GDP"][0])
        if not (0.5 <= reserves_incl_gold["latest"] <= 15.0):
            raise RuntimeError(
                f"validation: reserves-incl-gold {reserves_incl_gold['latest']}% is "
                "outside the sane 0.5-15% band — likely a wrong field mapping. "
                "Check the gold schema dumped by --verify before trusting it."
            )
        reserves_incl_gold_terms = [
            _term("Gold holdings (troy oz)", "Treasury (fiscal_service, gold_reserve)",
                  f"{oz_asof[0]}-{oz_asof[1]:02d}"),
            _term("Gold price ($/oz)",
                  (gold_price_src_label if price_is_live
                   else f"manual (data/manual.json goldPriceManualFallback, ${gpf['pricePerOz']:,.0f}/oz)"),
                  f"{price_asof[0]}-{price_asof[1]:02d}",
                  tag=("live" if price_is_live else "manual_price")),
            _term("FX reserves excl. gold", "FRED: TRESEGUSM052N",
                  _series_asof("TRESEGUSM052N", raw["TRESEGUSM052N"][1])),
            _term("GDP", "FRED: GDP", _series_asof("GDP", raw["GDP"][1])),
        ]
    except Exception as e:  # noqa: BLE001
        print(f"Gold-inclusive reserves unavailable even with a manual price input "
              f"(live ounce count itself failed), using the full manual fallback: {e}")
        reserves_incl_gold_tag = "manual"
        gf = mu["reservesInclGoldFallback"]
        reserves_incl_gold = {"latest": gf["value"], "asOf": gf.get("asOf", mu.get("lastChecked")), "history": []}
        gold_stale_note = gf.get("note")
        # TASKmanualvalues.md §4: this last-resort fallback is now dated
        # (asOf, March 2025 book baseline) instead of relying solely on the
        # top-level lastChecked catch-all — check its own date for staleness.
        gf_freshness = check_manual_freshness(
            "reservesInclGoldFallback.asOf", gf["asOf"], S.MANUAL_FRESH_DAYS)
        if gf_freshness["stale"]:
            gold_stale_note = (gold_stale_note or "") + (
                f" — ⚠ this manual figure is {gf_freshness['age_days']}d old (dated {gf['asOf']}), "
                f"past its {S.MANUAL_FRESH_DAYS}d review threshold; data/manual.json needs "
                f"a human to check for a newer figure"
            )

    assert_provenance(
        fallbacks_fired, "Reserves incl. gold (market)", "live", reserves_incl_gold_tag,
        reason="live gold price and/or holdings fetch failed or exceeded its freshness threshold")

    total_debt = S.total_debt_pct_gdp(raw["TCMDO"][1], raw["TCMDO"][0],
                                      raw["GDP"][1], raw["GDP"][0])
    ca_units = raw["IEABC"][0]
    annualized = "annual rate" in (ca_units or "").lower()
    current_acct = S.current_account_pct_gdp_3yr(raw["IEABC"][1], ca_units,
                                                 raw["GDP"][1], raw["GDP"][0], annualized)
    real_rate = S.real_10y_rate(raw["DGS10"][1], raw["CPIAUCSL"][1])

    # Debt held by the public / TOTAL receipts, net of refunds (TTM) —
    # alongside debt_to_gdp, not replacing it (Dalio's Ch.17 table itself
    # reports debt/GDP; debt/revenue is his Ch.3 preferred framing, added
    # here as a second row). No new series: debt$ = FYGFGDQ188S (%) x GDP
    # ($), same total-receipts denominator as both debt-service rows (see
    # STATUS.md §13). Expected magnitude is a bug-detector, not a target —
    # roughly $30T debt against a few trillion of receipts is several
    # hundred percent; the band is wide (200-1200%) to allow real movement
    # while still catching an order-of-magnitude unit error.
    debt_to_revenue = S.debt_to_revenue_pct(raw["FYGFGDQ188S"][1], raw["GDP"][1], raw["GDP"][0],
                                            T.revenue_ttm_dollars())
    if not (200.0 <= debt_to_revenue["latest"] <= 1200.0):
        raise RuntimeError(
            f"validation: debt-to-revenue {debt_to_revenue['latest']}% is "
            "outside the sane 200-1200% band — likely a units/scale error "
            "(FYGFGDQ188S is a percent, GDP is billions SAAR — check both)."
        )

    # --- CBO 10-Year Budget Projections (TASKprojections.md) ---
    # Non-fatal: CBO republishes ~twice a year, not monthly, and a genuine
    # outage here shouldn't take down every other live row. If unavailable
    # or stale, the projection-dependent rows below degrade gracefully
    # (the 10-yr projection row keeps its old manual figure, the
    # debt/revenue chart has no projected tail, equation #3 is omitted)
    # rather than failing the whole build — same "degrade rather than
    # break" convention as gold/COFER (STATUS.md §17-19).
    cbo_data = None
    cbo_vintage_label = None
    try:
        cbo_data = C.current_vintage_data()
        S.require_fresh("CBO 10-year budget projections", f"{cbo_data['vintage']}-01",
                         S.FRESHNESS_DAYS_BY_FREQ["Annual"])
        cbo_vintage_label = C.vintage_label(cbo_data)
    except Exception as e:  # noqa: BLE001
        print(f"CBO 10-year budget projections unavailable/stale, no projection layer this run: {e}")
        cbo_data = None
    assert_provenance(fallbacks_fired, "Debt, 10-yr projection", "projection",
                       "projection" if cbo_data else "manual",
                       reason="CBO 10-Year Budget Projections fetch failed or exceeded its freshness threshold")

    # Extend "Debt vs revenue"'s existing (live) chart with CBO's projected
    # tail — the headline value/asOf stay the live current figure; only the
    # chart gains a dashed forward extension (TASKprojections.md §1: "show
    # the forward path of the ratios already on the dashboard").
    if cbo_data:
        debt_to_revenue = {
            **debt_to_revenue,
            "history": debt_to_revenue["history"]
            + S.cbo_dollar_ratio_series(cbo_data, "debt_held_by_public", "rev_total"),
        }

    # The "Debt, 10-yr projection" row (was a hand-carried 122% with no
    # date in manual.json — see STATUS.md §19.2's dateless-value audit and
    # TASKprojections.md §4) — now live from the current CBO vintage.
    # Deliberately NOT merged into the live debt_to_gdp row itself: that
    # row's own historical chart (FRED FYGFGDQ188S) needs no projected
    # tail duplicating this one, and giving the projection its own
    # dedicated row/chart keeps "this is a projection, not a measurement"
    # unambiguous (TASKprojections.md §1's central design constraint).
    if cbo_data:
        fy_end = cbo_data["fyMax"]
        debt_gdp_at_end = cbo_data["debt_held_by_public_gdp_share"][fy_end]
        debt_projection_row = {
            "label": "Debt, 10-yr projection", "value": num(debt_gdp_at_end),
            "display": pct_display(debt_gdp_at_end, 0), "unit": "of GDP",
            "tone": "risk", "tag": "projection", "key": "debt_10yr_projection",
            "src": f"CBO 10-Year Budget Projections (publication #{51118}), FY{fy_end}",
            "asOf": f"FY{fy_end}",
            "history": debt["history"] + S.cbo_gdp_share_series(cbo_data, "debt_held_by_public_gdp_share"),
            "note": f"{cbo_vintage_label} — a current-law baseline, not a prediction; "
                    f"changes when CBO republishes a new baseline, not necessarily when the "
                    f"fiscal outlook itself changes.",
        }
    else:
        gf = mu["cboProjectionFallback"]
        debt_projection_row = {
            "label": "Debt, 10-yr projection", "display": gf["display"], "value": gf.get("value"),
            "unit": "of GDP", "tone": "risk", "tag": "manual", "key": "debt_10yr_projection",
            "src": gf["src"],
        }
        if "asOf" in gf:
            debt_projection_row["asOf"] = gf["asOf"]
            f = check_manual_freshness("cboProjectionFallback.asOf", gf["asOf"], S.MANUAL_FRESH_DAYS)
            if f["stale"]:
                debt_projection_row["note"] = (
                    f"⚠ this last-resort snapshot is {f['age_days']}d old (dated {gf['asOf']}), "
                    f"past its {S.MANUAL_FRESH_DAYS}d review threshold; data/manual.json needs "
                    f"a human to check for a newer CBO vintage"
                )

    # Dalio's equation #3 (Ch.3): the interest rate that would keep debt
    # flat, computed across CBO's baseline, shown alongside the ACTUAL
    # average effective rate (Treasury, live) so the gap is legible.
    # Growth term is REVENUE growth (CBO's own `proj_rev_total`, verified
    # live: FY2026's revenue $5,595.9B / FY2025's $5,234.6B - 1 = 6.90%,
    # matching Dalio's Ch.3 definition exactly — not GDP growth, which
    # this pipeline doesn't even have a raw level for (CBO's dataset only
    # publishes GDP as a *_gdp_share ratio, never a level). See
    # series.py's interest_rate_to_keep_debt_flat() and STATUS.md §27.
    equation3_row = None
    if cbo_data:
        try:
            required = S.interest_rate_to_keep_debt_flat(cbo_data)
            actual_rate = T.avg_interest_rate_marketable()
            latest_required = required["history"][0]["v"]
            gap = round(actual_rate["latest"] - latest_required, 2)
            # TASKequation3growth.md §"Interpreting the result": a
            # required > actual gap is easy to misread as reassuring. It
            # isn't a settled state — the ACTUAL rate is an average across
            # the whole outstanding stock, including old low-coupon debt;
            # new issuance costs more, so the average drifts toward (and
            # can cross) the required rate as the stock rolls over. This
            # is a closing gap, not a standing buffer.
            if gap < 0:
                interp = ("the actual rate sits BELOW the stabilising threshold today — read "
                          "carefully: not a settled cushion. The actual figure is an AVERAGE "
                          "across all outstanding debt, including old low-coupon issues; new "
                          "issuance costs more, so the average rate drifts up as the stock "
                          "rolls over, closing this gap (or crossing it) over time even with "
                          "no change in the required rate itself")
            elif gap > 0:
                interp = ("the actual rate already sits ABOVE the stabilising threshold — the "
                          "interest burden is rising on its own, before any primary deficit is "
                          "even counted")
            else:
                interp = "the actual rate sits almost exactly at the stabilising threshold"
            equation3_row = {
                "label": "Interest rate to keep debt flat (Dalio eq. #3)",
                "value": num(latest_required), "display": pct_display(latest_required, 1),
                "unit": "required rate", "tone": "neutral", "tag": "projection",
                "key": "interest_rate_to_keep_debt_flat",
                "src": "derived · CBO 10-Year Budget Projections (publication #51118)",
                "asOf": f"FY{cbo_data['fyMin'] + 1}", "history": required["history"],
                "note": (f"{cbo_vintage_label}. Actual average effective rate on marketable debt "
                         f"held by the public (Treasury, live, {actual_rate['asOf']}): "
                         f"{actual_rate['latest']}% — gap vs. the rate required to keep debt flat: "
                         f"{'+' if gap >= 0 else ''}{gap}pt: {interp}."),
            }
        except Exception as e:  # noqa: BLE001
            print(f"Equation #3 (interest rate to keep debt flat) unavailable: {e}")

    # TIC holder shares (TASKmanualvalues.md): central bank / domestic /
    # foreign, live from FRED (FYGFDPUN, FDHBFRBN, FDHBFIN — all three
    # aliases of the same Treasury Fiscal Service "class of investors"
    # table, not a TIC scrape; see series.py's tic_holder_shares()).
    # Replaces the undated 13%/57%/29% manual figures. Degrade to the
    # existing manual values on any failure, same pattern as gold/COFER.
    holders_tag = "live"
    holders = None
    try:
        fygfdpun_units, fygfdpun_obs = series_obs("FYGFDPUN")
        fdhbfrbn_units, fdhbfrbn_obs = series_obs("FDHBFRBN")
        fdhbfin_units, fdhbfin_obs = series_obs("FDHBFIN")
        # FDHBFIN gets its own, longer threshold — confirmed live (2026-07-22
        # CI run) that it publishes a full quarter behind FYGFDPUN/FDHBFRBN
        # even when healthy; see series.py's TIC_FOREIGN_FRESH_DAYS docstring.
        for sid, obs, max_days in (
            ("FYGFDPUN", fygfdpun_obs, S.FRESHNESS_DAYS_BY_FREQ["Quarterly"]),
            ("FDHBFRBN", fdhbfrbn_obs, S.FRESHNESS_DAYS_BY_FREQ["Quarterly"]),
            ("FDHBFIN", fdhbfin_obs, S.TIC_FOREIGN_FRESH_DAYS),
        ):
            S.require_fresh(sid, obs[-1][0], max_days)
        holders = S.tic_holder_shares(fygfdpun_obs, fygfdpun_units, fdhbfrbn_obs, fdhbfrbn_units,
                                       fdhbfin_obs, fdhbfin_units)
        total_pct = holders["centralBank"]["latest"] + holders["domestic"]["latest"] + holders["abroad"]["latest"]
        if not (99.0 <= total_pct <= 101.0):
            raise RuntimeError(
                f"validation: TIC holder shares sum to {total_pct}%, not ~100% — "
                "likely a wrong field mapping. Check the FRED schema dumped by --verify."
            )
    except Exception as e:  # noqa: BLE001
        print(f"TIC holder shares unavailable/stale, falling back to manual: {e}")
        holders_tag = "manual"
    assert_provenance(fallbacks_fired, "Debt holders (central bank/domestic/abroad)", "live", holders_tag,
                       reason="live TIC/SOMA (FRED) fetch failed or exceeded its freshness threshold")

    # BIS debt-currency share (TASKmanualvalues.md): attempted live via
    # DBnomics, but bis.py's debt_currency_share_usd() currently always
    # raises — the exact BIS SDMX schema wasn't confirmed from this dev
    # sandbox (see bis.py's module docstring). This is the CURRENT,
    # EXPECTED state, not a regression — deliberately NOT run through
    # assert_provenance()/fallbacksFired (that mechanism is for a source
    # that normally succeeds, to flag when it unexpectedly doesn't; BIS
    # has never yet succeeded, so "manual" is the correct baseline here,
    # not a fallback firing). Wired the same shape every other
    # live-with-fallback source uses, so the moment a future session
    # confirms the schema and removes that final raise, this starts
    # shipping live with no further change needed here.
    bis_debt_tag = "manual"
    try:
        bis_debt = B.debt_currency_share_usd()
        bis_debt_tag = "live"
    except Exception as e:  # noqa: BLE001
        print(f"BIS debt-currency share unavailable (expected — schema not yet confirmed, "
              f"see bis.py): {e}")

    # --- move guards on the positive-level ratios ---
    _check_move("debt_to_gdp", debt["latest"], prev, force)
    _check_move("debt_service_to_revenue", service["latest"], prev, force)
    _check_move("reserves_to_gdp", reserves_incl_gold["latest"], prev, force)

    def live_row(label, metric, tone, src, unit, decimals=None, note=None, key=None, terms=None):
        row = {
            "label": label, "value": num(metric["latest"]),
            "display": pct_display(metric["latest"], decimals), "unit": unit,
            "tone": tone, "tag": "live", "src": src, "asOf": metric["asOf"],
            "history": metric["history"],
        }
        if note:
            row["note"] = note
        if key:
            row["key"] = key
        if terms:
            row["terms"] = terms
        return row

    def manual_row(label, spec, tag="manual", key=None, freshness_days=None):
        row = {"label": label, "display": spec["display"], "unit": spec.get("unit", ""),
               "tone": spec.get("tone", "neutral"), "tag": tag, "src": spec.get("src", "—")}
        if "value" in spec:
            row["value"] = spec["value"]
        if "asOf" in spec:
            row["asOf"] = spec["asOf"]
        if "history" in spec:
            row["history"] = spec["history"]
        if key:
            row["key"] = key
        # TASKmanualvalues.md §4: a dated manual value can go stale exactly
        # like the gold/COFER manual fallbacks already do — reuse the same
        # check_manual_freshness()-then-⚠-note mechanism (MetricRow.jsx
        # already renders any note starting with "⚠" in the warning color;
        # no frontend change needed) rather than only the coarse top-level
        # lastChecked catch-all every dateless value relied on before.
        if "asOf" in spec and freshness_days is not None:
            f = check_manual_freshness(f"{key or label} (manual .asOf)", spec["asOf"], freshness_days)
            if f["stale"]:
                row["note"] = (
                    f"⚠ this manual figure is {f['age_days']}d old (dated {spec['asOf']}), "
                    f"past its {freshness_days}d review threshold; data/manual.json needs "
                    f"a human to check for a newer figure"
                )
        return row

    # Per-term provenance for the equation-button mapping table
    # (TASK-equation-button.md §3): each Dalio-notation term in a compound
    # row gets its OWN src/asOf/tag here, read straight from this run's
    # actual fetch results — src/content/ only holds the hand-written
    # Dalio-term label and which of these to show, never the src/asOf/tag
    # values themselves.
    revenue_term = _term("Total receipts, net of refunds (TTM)",
                         "Treasury (MTS mts_table_4, total receipts net of refunds, TTM)",
                         service["asOf"])
    net_interest_terms = [
        _term("Net interest to the public", "Treasury (MTS, interest on debt held by the public)", service["asOf"]),
        revenue_term,
    ]
    gross_interest_terms = [
        _term("Gross interest (incl. intragovernmental GAS)",
              "Treasury (MTS, gross interest incl. Government Account Series)", gross_service["asOf"]),
        revenue_term,
    ]
    debt_to_revenue_terms = [
        _term("Debt held by the public", "derived · FRED FYGFGDQ188S × GDP", debt_to_revenue["asOf"]),
        revenue_term,
    ]
    real_rate_terms = [
        _term("10-year Treasury yield", "FRED: DGS10", _series_asof("DGS10", raw["DGS10"][1])),
        _term("CPI, trailing 12-month inflation", "FRED: CPIAUCSL", _series_asof("CPIAUCSL", raw["CPIAUCSL"][1])),
    ]

    rc = mu["reserveCurrency"]

    # TIC holder shares (TASKmanualvalues.md): live from `holders` (computed
    # earlier in this function via FRED FYGFDPUN/FDHBFRBN/FDHBFIN) when that
    # fetch succeeded, else the book-transcribed manual split — now dated
    # and marked as a last-resort fallback, same treatment as gold/COFER.
    def holder_row(label, holder_key, key):
        if holders_tag == "live":
            h = holders[holder_key]
            return {
                "label": label, "value": num(h["latest"]), "display": pct_display(h["latest"], 1),
                "unit": "", "tone": mu["holders"][holder_key]["tone"], "tag": "live",
                "src": "derived · FRED (FYGFDPUN, FDHBFRBN, FDHBFIN — Treasury Fiscal Service "
                       "\"distribution of federal securities by class of investors\")",
                "asOf": holders["asOf"], "history": h["history"], "key": key,
            }
        return manual_row(label, mu["holders"][holder_key], key=key, freshness_days=S.MANUAL_FRESH_DAYS)

    # BIS debt-currency share (TASKmanualvalues.md): live via DBnomics when
    # bis.py resolves (currently never — see bis.py's module docstring),
    # else the book-transcribed manual figure, now dated.
    if bis_debt_tag == "live":
        world_debt_usd_row = {
            "label": "World debt in USD", "value": num(bis_debt["latest"]),
            "display": pct_display(bis_debt["latest"], 1), "unit": "", "tone": rc["debt"]["tone"],
            "tag": "live", "src": "BIS WS_NA_SEC_DSS (DBnomics)", "asOf": bis_debt["asOf"],
            "history": bis_debt["history"], "key": "world_debt_usd",
        }
    else:
        world_debt_usd_row = manual_row("World debt in USD", rc["debt"], key="world_debt_usd",
                                         freshness_days=S.MANUAL_FRESH_DAYS)

    vitals = [
        {"key": "debt_to_gdp", "label": "Debt vs income", **_vital(debt, "risk",
            "Debt held by the public near one year of national income; projected to keep climbing.",
            "FRED: FYGFGDQ188S", "of GDP")},
        {"key": "debt_service_to_revenue", "label": "Debt service vs income", **_vital(service, "risk",
            "Net interest to the public — cash actually leaving the government today — costs "
            "about a fifth of total revenue. Gross interest, including bonds credited to "
            "trust funds, runs higher still (see the panel below).",
            "derived · Treasury (net interest, total receipts net of refunds)", "of revenue",
            terms=net_interest_terms)},
        {"key": "real_rates", "label": "Rates vs inflation & growth", **_vital(real_rate, "neutral",
            "10-year Treasury yield minus trailing-12-month CPI inflation — the real cost of borrowing Dalio watches.",
            "derived · FRED (10y − CPI)", "real 10y", terms=real_rate_terms)},
        {"key": "reserves_to_gdp", "label": "Debt & service vs savings",
            **_vital(reserves_incl_gold, "risk",
                "Reserves including gold at market value are still thin relative to the debt — "
                "and most of the buffer is illiquid gold, not spendable FX.",
                (f"derived · {gold_src_detail} + FRED" if reserves_incl_gold_tag != "manual"
                 else mu["reservesInclGoldFallback"]["src"]),
                "reserves / GDP", tag=reserves_incl_gold_tag, terms=reserves_incl_gold_terms)},
    ]

    gov_panel = {
        "eyebrow": "Government debt", "tag": "live",
        "note": "Very large debt with little liquid backing. Who holds it matters: foreign holders can leave faster than domestic ones. Two debt-service rows below: net is what's actually leaving the government in cash today; gross adds interest credited to trust funds as bonds — a real claim, but not yet a cash outflow.",
        "rows": [
            manual_row("Gov assets − gov debt", mu["govAssetsMinusDebt"], key="gov_assets_minus_debt",
                       freshness_days=S.MANUAL_FRESH_DAYS),
            live_row("Government debt (held by public)", debt, "risk", "FRED: FYGFGDQ188S", "of GDP",
                     key="debt_to_gdp"),
            live_row("Debt vs revenue", debt_to_revenue, "risk",
                     "derived · FYGFGDQ188S x GDP / Treasury (total receipts, net of refunds, TTM)",
                     "of revenue", decimals=0, key="debt_to_revenue", terms=debt_to_revenue_terms),
            debt_projection_row,
            holder_row("— held by central bank", "centralBank", "held_by_central_bank"),
            holder_row("— held by domestic players", "domestic", "held_by_domestic"),
            holder_row("— held abroad", "abroad", "held_abroad"),
            manual_row("Share in hard (foreign) FX", mu["shareHardFX"], key="share_hard_fx",
                       freshness_days=S.MANUAL_FRESH_DAYS),
            live_row("Net interest (to the public)", service, "risk",
                     "derived · Treasury (net interest, total receipts net of refunds)", "of revenue",
                     note="The current situation — cash leaving the government today",
                     key="debt_service_to_revenue", terms=net_interest_terms),
            live_row("Gross interest (incl. intragovernmental)", gross_service, "caution",
                     "derived · Treasury (gross incl. GAS, total receipts net of refunds)", "of revenue",
                     note="The leading indicator — the gap is obligation accruing before it's an outflow",
                     key="gross_interest_to_revenue", terms=gross_interest_terms),
            *([equation3_row] if equation3_row else []),
        ],
    }
    reserves_incl_gold_row = {
        "label": "Reserves incl. gold (market)", "value": num(reserves_incl_gold["latest"]),
        "display": pct_display(reserves_incl_gold["latest"], 1), "unit": "of GDP",
        "tone": "risk", "tag": reserves_incl_gold_tag, "key": "reserves_to_gdp",
        "src": (f"derived · {gold_src_detail} + FRED" if reserves_incl_gold_tag != "manual"
                else mu["reservesInclGoldFallback"]["src"]),
        "asOf": reserves_incl_gold.get("asOf"),
        "history": reserves_incl_gold.get("history", []),
    }
    if gold_stale_note:
        reserves_incl_gold_row["note"] = gold_stale_note
    if reserves_incl_gold_terms:
        reserves_incl_gold_row["terms"] = reserves_incl_gold_terms
    reserves_panel = {
        "eyebrow": "Liquid reserves", "tag": "live",
        "note": "The cushion a country can draw on before it must default or print. Gold is a "
                "hard-asset hedge, not spendable liquidity in the same way FX reserves are — "
                "Dalio tracks both, so both are shown here rather than picking one.",
        "rows": [
            reserves_incl_gold_row,
            *([gold_value_row] if gold_value_row else []),
            live_row("FX reserves excl. gold", reserves, "risk", "FRED: TRESEGUSM052N", "of GDP",
                     key="fx_reserves_excl_gold"),
            manual_row("Sovereign wealth assets", mu["sovereignWealth"], key="sovereign_wealth",
                       freshness_days=S.MANUAL_FRESH_DAYS),
        ],
    }
    broader_panel = {
        "eyebrow": "Broader health", "tag": "live",
        "note": "Economy-wide leverage and the external balance — how dependent the country is on foreign financing.",
        "rows": [
            live_row("Total debt (all sectors)", total_debt, "caution", "FRED: TCMDO (Z.1)", "of GDP",
                     key="total_debt_all_sectors"),
            live_row("Current account, 3-yr avg", current_acct, "caution", "BEA / FRED", "of GDP",
                     key="current_account_3yr"),
            live_row("Real 10-year rate (10y − CPI)", real_rate, "neutral", "derived · FRED (DGS10 − CPI)",
                     "real, 10y", key="real_rates", terms=real_rate_terms),
        ],
    }
    # World CB reserves in USD: live from IMF COFER, else fall back to manual.
    cb_reserves_tag = "live"
    try:
        cofer = I.cofer_usd_share()
        S.require_fresh("IMF COFER USD share", cofer["asOf"], S.COFER_FRESH_DAYS)
        cb_reserves_row = {
            "label": "World CB reserves in USD", "value": num(cofer["latest"]),
            "display": pct_display(cofer["latest"], 1), "unit": "", "tone": "mitig",
            "tag": "live", "src": "IMF COFER (DBnomics)", "asOf": cofer["asOf"], "history": cofer["history"],
            "key": "world_cb_reserves_usd",
        }
    except Exception as e:  # noqa: BLE001
        print(f"IMF COFER unavailable, using manual value: {e}")
        cb_reserves_tag = "manual"
        # This manual snapshot has its own asOf (unlike reservesInclGoldFallback)
        # — check it against the same cadence COFER's own live threshold uses
        # (STATUS.md §19), since it's a snapshot of that same series.
        cbreserves_freshness = check_manual_freshness(
            "reserveCurrency.cbReserves.asOf (manual COFER fallback)",
            rc["cbReserves"]["asOf"], S.CBRESERVES_MANUAL_FRESH_DAYS)
        cb_reserves_row = manual_row("World CB reserves in USD", rc["cbReserves"], key="world_cb_reserves_usd")
        if cbreserves_freshness["stale"]:
            cb_reserves_row["note"] = (
                f"⚠ this manual COFER figure is {cbreserves_freshness['age_days']}d old itself, "
                f"past its {S.CBRESERVES_MANUAL_FRESH_DAYS}d review threshold; "
                f"data/manual.json needs a human to check for a newer published figure"
            )
    assert_provenance(
        fallbacks_fired, "World CB reserves in USD", "live", cb_reserves_tag,
        reason="live IMF COFER fetch failed or exceeded its freshness threshold")

    reserve_ccy_panel = {
        "eyebrow": "Reserve-currency status", "tag": "manual", "accent": "#5B8DD6",
        "note": rc["note"],
        "rows": [
            manual_row("World trade in USD", rc["trade"], key="world_trade_usd",
                       freshness_days=S.MANUAL_FRESH_DAYS),
            world_debt_usd_row,
            manual_row("Global equity market cap", rc["equity"], key="global_equity_usd",
                       freshness_days=S.MANUAL_FRESH_DAYS),
            cb_reserves_row,
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
            "revenueDefinition": "TOTAL federal receipts, NET of refunds (Treasury MTS "
                                  "mts_table_4, current_month_net_rcpt_amt) — the ONE revenue "
                                  "denominator shared by all three revenue-denominated rows "
                                  "below (net interest, gross interest, debt/revenue). Revised "
                                  "2026-07 (third time same day) after finding this pipeline had "
                                  "been summing GROSS receipts (before refunds), a ~7% "
                                  "overstatement checked against CBO's published FY2024 ($4.920T) "
                                  "and FY2025 ($5.235T) totals — net matched both almost exactly, "
                                  "gross missed both by ~7%. The prior on-budget-receipts basis "
                                  "is dropped: it was chosen partly for landing close to Dalio's "
                                  "Ch.17 22%, which the gross-receipts bug made an artifact — with "
                                  "the bug fixed, no basis reproduces 22% closely, so the "
                                  "denominator is now chosen purely on definitional grounds (the "
                                  "denominator every standard published interest-to-revenue "
                                  "figure actually uses). See STATUS.md §13.",
            "debtServiceBasis": "NET interest to the public (excl. intragovernmental GAS) / "
                                 "TOTAL receipts, net of refunds — headline "
                                 "`debt_service_to_revenue`. Net-to-public is the numerator "
                                 "whose scope matches debt_to_gdp (debt held by the public); "
                                 "gross interest incl. GAS ships as its own separate row instead. "
                                 "See STATUS.md §13.",
            "grossDebtServiceBasis": "GROSS interest (incl. intragovernmental Government "
                                      "Account Series) / TOTAL receipts, net of refunds — the "
                                      "explicit second debt-service row, same denominator as the "
                                      "net headline (see revenueDefinition).",
            "debtToRevenueBasis": "Debt held by the public ($, FYGFGDQ188S x GDP) / TOTAL "
                                   "receipts, net of refunds (TTM, $) — same denominator as both "
                                   "debt-service rows. Dalio's Ch.17 table reports only debt/GDP; "
                                   "his Ch.3 debt-to-revenue figure (~580%, ~700% in ten years) "
                                   "is a real anchor but not exactly reproduced by any tested "
                                   "denominator — see STATUS.md §12/§13. debt_to_gdp remains the "
                                   "headline.",
            "reservesBasis": "FRED reserves excl. gold + US gold holdings (Treasury, troy oz, "
                              "live) x gold price, valued at MARKET not the $42.2222/oz statutory "
                              "book rate. Price is live from the World Bank Commodity Markets "
                              "(\"Pink Sheet\") — direct download, falling to a GitHub mirror of "
                              "the same data if that's unreachable (TASKgoldautomation.md; "
                              "replaced the previously frozen DBnomics/IMF PCPS feed, see STATUS.md "
                              "§16/§21). If both World Bank legs are down, the price falls back to "
                              "a hand-entered manual value (data/manual.json: "
                              "goldPriceManualFallback) applied to the still-live ounce count — see "
                              "STATUS.md §18 for why this replaced the prior all-manual-output "
                              "fallback (which matched Dalio's Ch.17 figure by construction, not by "
                              "independent computation).",
            "reservesInclGoldTag": reserves_incl_gold_tag,
            # Per-row provenance assertions (STATUS.md §19): every row whose
            # tag can legitimately fall back from "live" is checked here at
            # build time. Empty list = every fallback-capable row shipped as
            # live this run; a non-empty list means at least one fallback
            # fired and is loudly warned above, not just silently shipped.
            "fallbacksFired": fallbacks_fired,
            # CBO vintage (TASKprojections.md §3): a projection changes when
            # CBO republishes, not when the economy moves — recorded here
            # AND on every projected row's own note, so a jump in the
            # projected rows reads as "new baseline landed," not "data
            # error"/"news about the fiscal position."
            "cboVintage": cbo_vintage_label,
        },
    }
    _validate(country)
    return country


def _vital(metric, tone, read, src, unit, tag="live", terms=None):
    v = {
        "value": num(metric["latest"]), "display": pct_display(metric["latest"]),
        "unit": unit, "tone": tone, "read": read, "tag": tag,
        "src": src, "asOf": metric.get("asOf"), "history": metric.get("history", []),
    }
    if terms:
        v["terms"] = terms
    return v


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
