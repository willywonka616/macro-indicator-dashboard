"""Diagnostic (not shipped): follow-up on gold_bundesbank_check2.py's full
dataset dump — BBEX3's full name is "ECB euro reference exchange rates,
exchange rates in particular countries, special drawing rights, precious
metals" (truncated in the prior log), a strong candidate for a gold price.
BBK01 ("None" as a name — Bundesbank's general/miscellaneous time-series
flow, which is where BBK01.WT5511 conventionally lives) is the other
candidate. Dumps both datasets' series lists directly (not a q= search,
which 400'd combined with provider_code last round) and filters
client-side for gold/XAU. Deleted after this round's findings are copied
into STATUS.md/docs.
"""

import time

import requests

DBN = "https://api.db.nomics.world/v22"


def _get(url, params=None, tries=2, timeout=15):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)
    raise RuntimeError(f"request to {url} failed after {tries} tries: {last}")


def dump_dataset(code, limit=1000, q=None):
    print(f"\n=== BUBA/{code} — series dump (limit={limit}, q={q!r}) ===")
    try:
        params = {"limit": str(limit), "observations": "1"}
        if q:
            params["q"] = q
        r = _get(f"{DBN}/series/BUBA/{code}", params=params)
        docs = r.json().get("series", {}).get("docs", [])
        print(f"  {len(docs)} series total")
        gold_docs = [d for d in docs
                     if "gold" in str(d.get("series_name", "")).lower()
                     or "gold" in str(d.get("series_code", "")).lower()
                     or "xau" in str(d.get("series_code", "")).lower()]
        print(f"  {len(gold_docs)} match gold/XAU:")
        for d in gold_docs[:20]:
            periods = d.get("period", [])
            values = d.get("value", [])
            print(f"    {d.get('series_code')} ({d.get('series_name')}): "
                  f"{len(periods)} obs, latest {periods[-1] if periods else None} = "
                  f"{values[-1] if values else None}")
        if not gold_docs:
            sample = [(d.get("series_code"), d.get("series_name")) for d in docs][:25]
            print(f"  no gold/XAU match; sample of {min(25, len(docs))} series: {sample}")
    except Exception as e:  # noqa: BLE001
        print(f"  FAILED: {e}")


if __name__ == "__main__":
    dump_dataset("BBEX3", limit=50, q="gold")
    dump_dataset("BBEX3", limit=50, q="XAU")
    dump_dataset("BBEX3", limit=50, q="precious metal")
