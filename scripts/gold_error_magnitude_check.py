"""Diagnostic (not shipped): quantify, in GDP points, how far off
`reserves_incl_gold_pct_gdp` currently is because the shipped gold price
(DBnomics-mirrored IMF PCPS, stuck at 2025-06) is stale relative to a
current market estimate. Both keyless alternative sources tested in
gold_altsource_check.py failed (World Bank/DBnomics: only an annual
history+projections series, not the monthly Pink Sheet, with a 2030
*projected* value as its "latest" point; Stooq: blocked by a JS
proof-of-work anti-bot challenge, not retrievable via plain HTTP), so
there's no live current price to swap in — this instead computes the
counterfactual using a manually-supplied current-market estimate, to
report the size of the gap rather than leave it unquantified. Needs
FRED_API_KEY (same secret update-data.yml uses) to pull the real
TRESEGUSM052N/GDP series. Deleted after this round's findings are copied
into STATUS.md.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import fetch as F  # noqa: E402
import gold as G  # noqa: E402
import series as S  # noqa: E402

# User-supplied current-market estimates (2026-07-20), not fetched live —
# both keyless candidate sources failed; see gold_altsource_check.py.
CURRENT_MARKET_PRICE_USD_PER_OZ = 4000.0
PEAK_PRICE_USD_PER_OZ = 5595.0  # ~Jan-2026 peak, for context only


def main():
    print("Fetching live TRESEGUSM052N (reserves excl. gold) and GDP from FRED...")
    tres_units, tres_obs = F.series_obs("TRESEGUSM052N")
    gdp_units, gdp_obs = F.series_obs("GDP")

    print("Fetching live Treasury gold holdings (troy oz)...")
    gold_oz = G.gold_holdings_troy_oz()
    oz_asof = max(gold_oz)
    print(f"  latest gold-oz month: {oz_asof[0]}-{oz_asof[1]:02d}, "
          f"{gold_oz[oz_asof]:,.0f} troy oz")

    print("Fetching live DBnomics-mirrored IMF PCPS gold price (the shipped, "
          "stale source)...")
    price_monthly = G.gold_price_usd_per_oz()
    price_asof = max(price_monthly)
    shipped_price = price_monthly[price_asof]
    print(f"  latest gold-price month: {price_asof[0]}-{price_asof[1]:02d} = "
          f"${shipped_price:,.2f}/oz")

    def compute(gold_value_monthly, label):
        r = S.reserves_incl_gold_pct_gdp(tres_obs, tres_units, gold_value_monthly,
                                          gdp_obs, gdp_units)
        print(f"  [{label}] reserves_incl_gold_pct_gdp: {r['latest']}% of GDP "
              f"as of {r['asOf']}")
        return r

    print("\n=== Baseline: shipped stale price ===")
    shipped_value_monthly = {k: gold_oz[k] * price_monthly[k]
                              for k in gold_oz.keys() & price_monthly.keys()}
    baseline = compute(shipped_value_monthly, f"shipped, {price_asof[0]}-{price_asof[1]:02d} price")

    print("\n=== Counterfactual: current market price substituted at the same "
          f"gold-oz month ({oz_asof[0]}-{oz_asof[1]:02d}) ===")
    counterfactual_monthly = dict(shipped_value_monthly)
    counterfactual_monthly[oz_asof] = gold_oz[oz_asof] * CURRENT_MARKET_PRICE_USD_PER_OZ
    corrected = compute(counterfactual_monthly,
                         f"${CURRENT_MARKET_PRICE_USD_PER_OZ:,.0f}/oz market estimate")

    print("\n=== For context only: at the ~Jan-2026 peak price ===")
    peak_monthly = dict(shipped_value_monthly)
    peak_monthly[oz_asof] = gold_oz[oz_asof] * PEAK_PRICE_USD_PER_OZ
    compute(peak_monthly, f"${PEAK_PRICE_USD_PER_OZ:,.0f}/oz peak estimate")

    gap = corrected["latest"] - baseline["latest"]
    gold_value_gap_usd = (counterfactual_monthly[oz_asof] - shipped_value_monthly[oz_asof])
    print(f"\nGap: shipped ({baseline['latest']}%) vs current-market-corrected "
          f"({corrected['latest']}%) = {gap:+.1f} points of GDP")
    print(f"Underlying gold market-value gap at the same oz holdings: "
          f"${gold_value_gap_usd/1e9:,.1f}B "
          f"(${shipped_price:,.2f}/oz -> ${CURRENT_MARKET_PRICE_USD_PER_OZ:,.0f}/oz, "
          f"same {gold_oz[oz_asof]:,.0f} oz)")


if __name__ == "__main__":
    main()
