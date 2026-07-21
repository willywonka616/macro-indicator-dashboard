/* ------------------------------------------------------------------ *
 *  Hand-written equation content for the "ƒx" button on each metric row.
 *
 *  TASK-equation-button.md is the source for every formula and Dalio
 *  quote here — transcribed from How Countries Go Broke, Ch. 3, "The
 *  Mechanics in Numbers and Equations" (pp. 69-73). Nothing below is
 *  reconstructed from memory or invented; a row this project has no book
 *  equation for gets a plain, honestly-labelled definition instead of a
 *  forced fit into Dalio's notation.
 *
 *  Keyed by metric `key` (matches data.json's vitals[].key and
 *  panels[].rows[].key) — a row without an entry here simply shows no
 *  button (see EquationButton.jsx).
 *
 *  What's NOT here: src/asOf/tag. Those come from data.json's row.terms
 *  (or a single-row fallback built from row.src/asOf/tag) at render
 *  time, in EquationButton.jsx — this file only holds the maths and its
 *  prose, which don't change month to month. The tag vocabulary is still
 *  changing (manual_price was added recently, more may follow), so
 *  hardcoding a tag or src string here would go stale the next time the
 *  pipeline's fallback behaviour changes.
 *
 *  Shape of an entry:
 *    kind: "derived" | "observed"
 *    definition: string | EquationLine   (EquationLine = Array<string | {num, den}>)
 *    formula?: { label: string, lines: EquationLine[], prose?: string }
 *    formulaNote?: string   (used instead of `formula` when a row shares
 *                            another row's formula rather than repeating it)
 *    caveats?: string[]
 * ------------------------------------------------------------------ */

const REVENUE_PROJECTION_PROSE =
  "i = interest rate, g = income growth rate, t = the time period in question — Dalio's own notation (Ch. 3 footnote).";

export const equations = {
  // ---- Government debt panel + matching vitals ----

  debt_to_gdp: {
    kind: "observed",
    definition:
      "Federal debt held by the public, as a percentage of GDP — a directly published FRED series (FYGFGDQ188S). Not computed from other inputs by this pipeline.",
    caveats: [
      "Dalio's own Ch. 3 equations are written in terms of debt ÷ revenue, not debt ÷ GDP — GDP isn't a resource the government can draw on, only its actual cash flows are. See the “Debt vs revenue” row for his preferred framing.",
    ],
  },

  debt_to_revenue: {
    kind: "derived",
    definition: [{ num: "Debt held by the public", den: "Total receipts, net of refunds (TTM)" }],
    formula: {
      label: "Dalio's projection formula — how this evolves, not what's shown",
      lines: [
        [
          { num: "Future Debt", den: "Future Revenue" },
          "=",
          { num: "Future Expenses Excl. Interest − Future Revenue", den: "Current Revenue × (1 + g)" },
          "+ Current Debt × (1 + i)",
        ],
      ],
      prose: REVENUE_PROJECTION_PROSE,
    },
    caveats: [
      "This is Dalio's indicator #1 and his preferred framing (Ch. 3): debt against what government can actually collect, not against GDP, which it can't spend.",
      "The chart's dashed tail (TASKprojections.md) is CBO's own 10-year baseline for this same ratio — a current-law projection, not this pipeline's forecast. It changes when CBO republishes, not when the fiscal position itself changes.",
    ],
  },

  gov_assets_minus_debt: {
    kind: "observed",
    definition:
      "Government assets minus government debt, as a percentage of GDP — a manually hand-entered figure, not computed live by this pipeline.",
  },

  debt_10yr_projection: {
    kind: "observed",
    definition:
      "Debt held by the public as a percentage of GDP, at the end of CBO's published 10-year baseline window — CBO's own figure, not computed by this pipeline (see the “Debt vs revenue” row above for the pipeline's derived Ch. 3 framing).",
    caveats: [
      "Live from CBO's current-law baseline (TASKprojections.md) — a benchmark assuming no change in law, not a prediction of what will happen. Changes when CBO republishes a new baseline (roughly twice a year), not necessarily when the fiscal outlook itself changes.",
      "Reproduces Dalio's own stated 122%-in-10-years figure almost exactly if computed at his book's vintage (June 2024 CBO baseline) — see STATUS.md §9. The currently-displayed figure uses the latest vintage instead, which is expected to differ from his book value.",
    ],
  },

  interest_rate_to_keep_debt_flat: {
    kind: "derived",
    definition:
      "The interest rate that would hold debt flat relative to income, computed for every fiscal year in CBO's 10-year baseline — this row is inherently forward-looking end to end, not a current measurement with a projected extension.",
    formula: {
      label: "Dalio's equation #3 (Ch. 3) — every term from CBO's own baseline",
      lines: [
        [
          "Interest Rate Required to Keep Debt Flat", "=", "Revenue Growth", "−",
          { num: "Future Expenses Excl. Interest − Future Revenue", den: "Starting Debt Level" },
        ],
      ],
      prose:
        "His rule of thumb: with no primary deficit, debt stays flat relative to income when i = g. When i > g, existing debt compounds faster than income and the burden rises regardless of new borrowing — he calls this the single most important variable in the calculation.",
    },
    caveats: [
      "Diagnostic by design: compare the plotted required rate against the row's own note, which states the ACTUAL average effective rate on marketable debt (Treasury, live) — the gap between them is how far from stabilising the debt currently is, not a number to read on its own.",
      "Every term is CBO's own published baseline (Revenue Growth, the primary deficit, and the starting debt level) — nothing here is extrapolated, fitted, or a scenario output.",
    ],
  },

  held_by_central_bank: {
    kind: "observed",
    definition:
      "Share of federal debt held by the Federal Reserve / central bank — a manually hand-entered figure from Treasury TIC data.",
  },
  held_by_domestic: {
    kind: "observed",
    definition:
      "Share of federal debt held by domestic, non-central-bank holders — a manually hand-entered figure from Treasury TIC data.",
  },
  held_abroad: {
    kind: "observed",
    definition:
      "Share of federal debt held by foreign holders — a manually hand-entered figure from Treasury TIC data.",
  },
  share_hard_fx: {
    kind: "observed",
    definition:
      "Whether the government's own debt is denominated in a hard foreign currency it doesn't control — a manually hand-entered fact, not a computed figure.",
  },

  debt_service_to_revenue: {
    kind: "derived",
    definition: [{ num: "Net interest to the public", den: "Total receipts, net of refunds (TTM)" }],
    formula: {
      label: "Dalio's projection formula — how this evolves, not what's shown",
      lines: [
        [
          { num: "Future Debt Service", den: "Future Revenue" },
          "=",
          { num: "Future Interest Costs + Future Principal Payments", den: "Current Revenue × (1 + g)" },
        ],
        ["Future Interest Costs", "=", "Future Debt Level × Average Effective Interest Rate on Debt"],
        ["Future Principal Payments", "=", "Future Debt Level × Share of Debts Coming Due"],
      ],
      prose: REVENUE_PROJECTION_PROSE,
    },
    caveats: [
      "Dalio's debt service is interest PLUS principal payments. This row (and the gross-interest row below it) is interest only — a component of his measure, not the whole of it.",
    ],
  },

  gross_interest_to_revenue: {
    kind: "derived",
    definition: [
      { num: "Net interest + interest credited to government accounts (GAS)", den: "Total receipts, net of refunds (TTM)" },
    ],
    formulaNote:
      "Shares the same projection formula as the net-interest row above — Dalio's Ch. 3 debt-service equation doesn't distinguish net from gross; that split is this pipeline's own addition, to separate cash actually leaving today from a claim that's still accruing.",
    caveats: [
      "Interest only, not interest plus principal — see the net-interest row's caveat.",
      "The gap between net and gross is interest credited to government trust funds as additional bonds, not cash paid out. It's a real claim building up, not yet a cash outflow.",
    ],
  },

  // ---- Liquid reserves panel + matching vital ----

  reserves_to_gdp: {
    kind: "derived",
    definition: [
      "Reserves incl. gold, % of GDP =",
      { num: "(FX reserves excl. gold) + (Gold holdings in troy oz × Gold price)", den: "GDP" },
    ],
    formula: {
      label: "Dalio's projection formula — how this evolves, not what's shown",
      lines: [
        [
          { num: "Future Debt", den: "Future Savings" },
          "=",
          { num: "Current Expenses Excl. Interest − Current Revenue", den: "Current Savings + Expected Savings" },
          "+ Current Debt × (1 + i)",
        ],
        [
          { num: "Future Debt Service", den: "Future Savings" },
          "=",
          { num: "Future Interest Costs + Future Principal Payments", den: "Current Savings + Expected Savings" },
        ],
      ],
      prose: REVENUE_PROJECTION_PROSE,
    },
    caveats: [
      "Dalio flags this indicator as inexact himself: a surplus can either add to reserves or pay down debt, and which one a government chooses changes where the improvement shows up.",
    ],
  },

  fx_reserves_excl_gold: {
    kind: "derived",
    definition: [{ num: "Total reserves excluding gold (FRED TRESEGUSM052N)", den: "GDP" }],
    caveats: [
      "This is the FX-only component of Dalio's indicator #4 (debt vs. savings/reserves) — see “Reserves incl. gold” above for the fuller measure, which adds gold at market value.",
    ],
  },

  sovereign_wealth: {
    kind: "observed",
    definition:
      "Whether the country holds a sovereign wealth fund of meaningful size — a manually hand-entered fact, not a computed figure.",
  },

  // ---- Broader health panel ----

  total_debt_all_sectors: {
    kind: "derived",
    definition: [{ num: "Total debt, all sectors (FRED TCMDO, Fed Z.1)", den: "GDP" }],
    caveats: [
      "Not one of Dalio's four numbered Ch. 3 indicators — those are all specifically about GOVERNMENT debt. This row is broader (all sectors: government, household, corporate, financial), shown for the economy-wide leverage picture, not as a reproduction of a book equation.",
    ],
  },

  current_account_3yr: {
    kind: "derived",
    definition: ["Current account balance ÷ GDP, 3-year (12-quarter) trailing average"],
    caveats: [
      "Not one of Dalio's four numbered Ch. 3 indicators — this tracks external financing dependence, a related but separate concern from the domestic debt-service maths above.",
    ],
  },

  real_rates: {
    kind: "derived",
    definition: ["10-year Treasury yield − trailing 12-month CPI inflation"],
    formula: {
      label: "Dalio's related indicator — the rate needed to keep debt flat, not the number shown",
      lines: [
        [
          "Interest Rate Required to Keep Debt Flat",
          "=",
          "Revenue Growth −",
          { num: "Future Expenses Excl. Interest − Future Revenue", den: "Starting Debt Level" },
        ],
      ],
      prose:
        "His rule of thumb: with no primary deficit, debt stays flat relative to income when i = g. When i > g, existing debt compounds faster than income and the burden rises regardless of new borrowing — he calls this the single most important variable in the calculation.",
    },
    caveats: [
      "Dalio's framing compares nominal interest rates to nominal income growth (i vs. g). This row compares the 10-year yield to CPI inflation instead — a different comparison. Real rate vs. growth would be closer to his test; both are informative, but they aren't the same thing.",
    ],
  },

  // ---- Reserve-currency status panel ----

  world_trade_usd: {
    kind: "observed",
    definition:
      "Share of world trade invoiced/settled in USD — a manually hand-entered figure from SWIFT/BIS data.",
    caveats: [
      "Dalio treats the reserve-currency shares (this row and the three below it) as observed facts, not something derived from a formula in Ch. 3.",
    ],
  },
  world_debt_usd: {
    kind: "observed",
    definition: "Share of world debt issuance denominated in USD — a manually hand-entered figure from BIS data.",
  },
  global_equity_usd: {
    kind: "observed",
    definition:
      "Share of global equity market capitalization denominated in USD — a manually hand-entered figure from market data.",
  },
  world_cb_reserves_usd: {
    kind: "observed",
    definition:
      "Share of global central-bank reserves held in USD — from IMF COFER, live when available, else the latest actually-published figure hand-entered as a fallback.",
  },
};
