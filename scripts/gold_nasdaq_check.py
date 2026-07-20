"""Diagnostic (not shipped): TASKgoldpricefreshness.md step 1.4 — check
whether Nasdaq Data Link's LBMA/GOLD dataset is reachable without an API
key (low-volume anonymous access is sometimes allowed on free datasets).
If it needs a key, that's reported plainly rather than silently adding a
new GitHub secret — a new secret needs the user's action. Deleted after
this round's findings are copied into STATUS.md/docs.
"""

import time

import requests


def _get(url, params=None, tries=3, timeout=25):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            return r  # don't raise_for_status — we want to see 401/403 bodies too
        except requests.exceptions.RequestException as e:  # noqa: PERF203
            last = e
            if i < tries - 1:
                time.sleep(2 ** i)
    raise RuntimeError(f"request to {url} failed after {tries} tries: {last}")


def main():
    print("=== Nasdaq Data Link (ex-Quandl), LBMA/GOLD — no-key attempt ===")
    urls = [
        ("CSV, no key", "https://data.nasdaq.com/api/v3/datasets/LBMA/GOLD.csv", {}),
        ("JSON, no key, limit=5", "https://data.nasdaq.com/api/v3/datasets/LBMA/GOLD.json",
         {"limit": "5"}),
    ]
    for label, url, params in urls:
        try:
            r = _get(url, params=params)
            print(f"\n  [{label}] GET {r.url}")
            print(f"  status: {r.status_code}, content-type: {r.headers.get('content-type')}")
            print(f"  first 500 chars: {r.text[:500]!r}")
        except Exception as e:  # noqa: BLE001
            print(f"\n  [{label}] FAILED: {e}")


if __name__ == "__main__":
    main()
