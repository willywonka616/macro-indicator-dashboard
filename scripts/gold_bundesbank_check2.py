"""Diagnostic (not shipped): follow-up on gold_bundesbank_check.py — the
keyword-filtered dataset search ('gold'/'price'/'metal'/'precious' in the
dataset NAME) missed the real dataset, since Bundesbank likely files
precious-metal prices under an exchange-rate or external-sector dataset
name that doesn't contain those words. Dumps every BUBA dataset name so
the right one can be found by eye, then searches within likely
candidates for any series with 'gold'/'xau' in its own series name/code
(not just the dataset name). Deleted after this round's findings are
copied into STATUS.md/docs.
"""

import time

import requests

DBN = "https://api.db.nomics.world/v22"


def _get(url, params=None, tries=3, timeout=25):
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


def main():
    r = _get(f"{DBN}/datasets/BUBA")
    datasets = r.json().get("datasets", {}).get("docs", [])
    print(f"provider BUBA: {len(datasets)} datasets, full list:")
    for d in datasets:
        print(f"  {d.get('code'):<10} {d.get('name')}")

    # Try a query-string search (q=gold) across the whole provider at once,
    # if DBnomics' API supports a cross-dataset series search — cheaper
    # than guessing which of 50 datasets to open individually.
    print("\nCross-dataset simple-search attempt (q=gold, no dataset filter):")
    try:
        r = _get(f"{DBN}/series", params={"provider_code": "BUBA", "q": "gold",
                                           "limit": "20", "observations": "1"})
        docs = r.json().get("series", {}).get("docs", [])
        print(f"  -> {len(docs)} series")
        for doc in docs[:15]:
            periods = doc.get("period", [])
            values = doc.get("value", [])
            print(f"    {doc.get('dataset_code')}/{doc.get('series_code')} "
                  f"({doc.get('series_name')}): {len(periods)} obs, "
                  f"latest {periods[-1] if periods else None} = {values[-1] if values else None}")
    except Exception as e:  # noqa: BLE001
        print(f"  cross-dataset search FAILED: {e}")

    print("\nCross-dataset simple-search attempt (q=XAU, no dataset filter):")
    try:
        r = _get(f"{DBN}/series", params={"provider_code": "BUBA", "q": "XAU",
                                           "limit": "20", "observations": "1"})
        docs = r.json().get("series", {}).get("docs", [])
        print(f"  -> {len(docs)} series")
        for doc in docs[:15]:
            periods = doc.get("period", [])
            values = doc.get("value", [])
            print(f"    {doc.get('dataset_code')}/{doc.get('series_code')} "
                  f"({doc.get('series_name')}): {len(periods)} obs, "
                  f"latest {periods[-1] if periods else None} = {values[-1] if values else None}")
    except Exception as e:  # noqa: BLE001
        print(f"  cross-dataset search FAILED: {e}")


if __name__ == "__main__":
    main()
