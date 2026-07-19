# Verification log, review round `2026-07-19d` — live Actions run output, pasted verbatim

> **This file is frozen as of the round below and is not edited in place.**
> Prior rounds: `docs/review/2026-07-19c-verification.md` (round c, base
> commit `b25f8a6`) and earlier commits under the retired
> `docs/verification-log.md` path (see its tombstone stub). Every review
> pass gets its own new file under `docs/review/` — check STATUS.md's
> "current review-round files" note (top of file) for whichever round is
> actually current when you're reading this.
>
> **Base commit:** `76362af` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> run quoted below)
> **Written:** 2026-07-19T21:30:00Z UTC

**What changed this round (see STATUS.md §13 for the full writeup):**
`treasury.py`'s `monthly_receipts()` had been summing GROSS receipts
(`current_month_gross_rcpt_amt`) instead of receipts net of refunds
(`current_month_net_rcpt_amt`) — a ~7% overstatement, checked live against
CBO's published FY2024 ($4.920T) and FY2025 ($5.235T) totals. Fixed, and
the shipped debt-service/debt-to-revenue denominator switched from
on-budget receipts to TOTAL receipts (net of refunds) on definitional
grounds. This file is the actual `workflow_dispatch` run of
`update-data.yml` that produced the corrected `public/data.json` —
`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29704235465`,
job `88238405832`, 2026-07-19 21:22-21:26 UTC, committed as `76362af`.
Copied verbatim from the job log via the GitHub API, with only per-line
ISO timestamps and terminal ANSI color codes stripped, and one very long
line (every series code in the IMF PCPS dataset — 1000 entries, one line)
trimmed to just the `PGOLD`-related entries with an explicit note where
that happened — same two mechanical edits as every prior round's file.
Nothing else was reworded, reordered, or summarized.

**Claim status: VERIFIED.**

---

## Run output: `python scripts/fetch.py --verify`, then `--force`

```
Verifying 7 FRED series against the live API

ID                 OK  FREQ       UNITS                        START        TITLE
---------------------------------------------------------------------------------
FYGFGDQ188S        yes Q          Percent of GDP               1970-01-01   Federal Debt Held by the Public as Perce
GDP                yes Q          Billions of Dollars          1947-01-01   Gross Domestic Product
TCMDO              yes Q          Millions of U.S. Dollars     1945-10-01   All Sectors; Debt Securities and Loans; 
IEABC              yes Q          Millions of Dollars          1999-01-01   Balance on current account
TRESEGUSM052N      yes M          Millions of Dollars          1950-12-01   Total Reserves excluding Gold for United
DGS10              yes D          Percent                      1962-01-02   Market Yield on U.S. Treasury Securities
CPIAUCSL           yes M          Index 1982-1984=100          1947-01-01   Consumer Price Index for All Urban Consu

All FRED series resolved. Review units/frequency above.

Verifying Treasury Fiscal Data endpoints

[interest] https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/interest_expense
  fields: record_date, expense_catg_desc, expense_group_desc, expense_type_desc, month_expense_amt, fytd_expense_amt, src_line_nbr, record_fiscal_year, record_fiscal_quarter, record_calendar_year, record_calendar_quarter, record_calendar_month, record_calendar_day
  distinct expense_catg_desc: ['INTEREST EXPENSE ON PUBLIC ISSUES', 'INTEREST EXPENSE ON GOVT ACCOUNT SERIES']
  distinct expense_group_desc: ['ACCRUED INTEREST EXPENSE', 'AMORTIZED DISCOUNT', 'AMORTIZED PREMIUM', 'SAVINGS BONDS', 'MISCELLANEOUS INTEREST EXPENSE', 'CASH BASIS GAS PAYMENTS', 'ACCRUAL BASIS GAS EXPENSE']
  distinct expense_type_desc: ['Treasury Notes', 'Treasury Bonds', 'Inflation Protected Securities (TIPS)', 'Int. Expense Inflation Compensation (TIPS)', 'Treasury Floating Rate Notes (FRN)', "Domestic Series - C/I's & Demand Deposits", 'Foreign Series - C/I, Notes & Bonds', 'REA Series', "State & Local Government-C/I's, Notes & Bonds", 'Matured Debt', 'Treasury Bills', 'Treasury Inflation Protected Securities (TIPS)', 'Domestic Series Bonds', 'Foreign Series Bills', 'Foreign Series Notes & Bonds', 'Series E and EE', 'Series H and HH', 'Series I', 'Other', 'Limited Payability', 'Recertified Agency Payments', 'Premium Collected on Issues', 'Premium Paid on Redemptions', 'Discount Collected on Redemptions', 'Discount Deferred on Redemptions', 'Accrued Interest Collected on Issues', 'Interest Payments', 'Inflation Compensation', 'Restoration of Interest', 'Zero Coupon Bonds Amortized Discount']
  latest 2026-06-30 rows (expense_group_desc = month_expense_amt):
    ACCRUED INTEREST EXPENSE = 41950999755.25
    ACCRUED INTEREST EXPENSE = 15040575946.16
    ACCRUED INTEREST EXPENSE = 414524224.99
    ACCRUED INTEREST EXPENSE = 19569925865.75
    ACCRUED INTEREST EXPENSE = 2184028996.06
    ACCRUED INTEREST EXPENSE = 506455.23
    ACCRUED INTEREST EXPENSE = 0.00
    ACCRUED INTEREST EXPENSE = 0.00
    ACCRUED INTEREST EXPENSE = 243714333.34
    ACCRUED INTEREST EXPENSE = 0.00
    AMORTIZED DISCOUNT = 20216564508.68
    AMORTIZED DISCOUNT = 921765621.29
    AMORTIZED DISCOUNT = 243638927.27
    AMORTIZED DISCOUNT = 161139766.63
    AMORTIZED DISCOUNT = 5454036.88

[receipts?] https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/mts/mts_table_4
  fields: record_date, parent_id, classification_id, classification_desc, current_month_gross_rcpt_amt, current_month_refund_amt, current_month_net_rcpt_amt, current_fytd_gross_rcpt_amt, current_fytd_refund_amt, current_fytd_net_rcpt_amt, prior_fytd_gross_rcpt_amt, prior_fytd_refund_amt, prior_fytd_net_rcpt_amt, table_nbr, src_line_nbr, print_order_nbr, line_code_nbr, data_type_cd, record_type_cd, sequence_level_nbr, sequence_number_cd, record_fiscal_year, record_fiscal_quarter, record_calendar_year, record_calendar_quarter, record_calendar_month, record_calendar_day
  distinct classification_desc: ['Federal Insurance Contributions Act Taxes', 'Self-Employment Contributions Act Taxes', 'Adjustments Attributable to Prior Years-FICA', 'Adjustments Attributable to Prior Years-SECA', 'Total -- Federal Disability Insurance Trust Fund', 'Receipts from Railroad Retirement Board', 'Total -- Federal Hospital Insurance Trust Fund', 'Rail Pension and Supplemental Annuity', 'Social Security Equivalent Account', 'Total -- Employment and General Retirement', 'Deposits by States', 'Federal Unemployment Taxes', 'Total -- Other Retirement', 'Excise Taxes:', 'Miscellaneous Excise Taxes', 'Airport and Airway Trust Fund', 'Highway Trust Fund', 'Black Lung Disability Trust Fund', 'Individual Income Taxes', 'Withheld', 'Presidential Election Campaign Fund', 'Other', 'Total -- Individual Income Taxes', 'Corporation Income Taxes', 'Social Insurance and Retirement Receipts:', 'Employment and General Retirement:', 'Federal Old-Age and Survivors Insurance Trust Fund:', 'Adjustments Attrbutable to Prior Years-SECA', 'Total -- Federal Old-Age and Survivors Insurance Trust Fund', 'Federal Disability Insurance Trust Fund:']
  latest 2026-06-30 rows (classification_desc = current_month_gross_rcpt_amt):
    Federal Insurance Contributions Act Taxes = 17293000000.00
    Self-Employment Contributions Act Taxes = 1448000000.00
    Adjustments Attributable to Prior Years-FICA = -952244895.17
    Adjustments Attributable to Prior Years-SECA = -232602385.43
    Total -- Federal Disability Insurance Trust Fund = 17556152719.40
    Federal Insurance Contributions Act Taxes = 33746000000.00
    Self-Employment Contributions Act Taxes = 3959000000.00
    Receipts from Railroad Retirement Board = 684100000.00
    Adjustments Attributable to Prior Years-FICA = -14160187685.82
    Adjustments Attributable to Prior Years-SECA = 8832936645.63
    Total -- Federal Hospital Insurance Trust Fund = 33061848959.81
    Rail Pension and Supplemental Annuity = 346596176.88
    Social Security Equivalent Account = -408352442.79
    Total -- Employment and General Retirement = 153952106321.05
    Deposits by States = 775349264.15

[receipts?] https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/mts/mts_table_1
  fields: record_date, parent_id, classification_id, classification_desc, current_month_gross_rcpt_amt, current_month_gross_outly_amt, current_month_dfct_sur_amt, table_nbr, src_line_nbr, print_order_nbr, line_code_nbr, data_type_cd, record_type_cd, sequence_level_nbr, sequence_number_cd, record_fiscal_year, record_fiscal_quarter, record_calendar_year, record_calendar_quarter, record_calendar_month, record_calendar_day
  distinct classification_desc: ['March', 'April', 'May', 'June', 'Year-to-Date', 'September', 'FY 2026', 'October', 'November', 'December', 'January', 'February', 'FY 2025', 'July', 'August', 'FY 2024']
  latest 2026-06-30 rows (classification_desc = current_month_gross_rcpt_amt):
    March = 384862602035.79
    April = 837342690993.51
    May = 335512183227.42
    June = 495761481568.70
    Year-to-Date = 4151409628325.36
    September = 543663073176.70
    Year-to-Date = 5234616472030.91
    FY 2026 = null
    October = 404371348973.70
    November = 336001720156.98
    December = 484384015539.25
    January = 560051900583.17
    February = 313121685246.84
    FY 2025 = null
    October = 326770236058.10

[outlays-by-function?] https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/mts/mts_table_9
  fields: record_date, parent_id, classification_id, classification_desc, current_month_rcpt_outly_amt, current_fytd_rcpt_outly_amt, prior_fytd_rcpt_outly_amt, table_nbr, src_line_nbr, print_order_nbr, line_code_nbr, data_type_cd, record_type_cd, sequence_level_nbr, sequence_number_cd, record_fiscal_year, record_fiscal_quarter, record_calendar_year, record_calendar_quarter, record_calendar_month, record_calendar_day
  distinct classification_desc: ['Medicare', 'Income Security', 'Social Security', 'Veterans Benefits and Services', 'Administration of Justice', 'General Government', 'Net Interest', 'Undistributed Offsetting Receipts', 'Total', 'Receipts', 'Individual Income Taxes', 'Corporation Income Taxes', 'Social Insurance and Retirement Receipts:', 'Employment and General Retirement', 'Unemployment Insurance', 'Net Outlays', 'National Defense', 'Miscellaneous Receipts', 'Transportation', 'Community and Regional Development', 'Education, Training, Employment, and Social Services', 'Health', 'Natural Resources and Environment', 'Agriculture', 'Commerce and Housing Credit', 'Other Retirement', 'Excise Taxes', 'Estate and Gift Taxes', 'Customs Duties', 'International Affairs']
  latest 2026-06-30 rows (classification_desc = current_month_rcpt_outly_amt):
    Medicare = 103468801709.98
    Income Security = 44758192389.46
    Social Security = 146737369071.60
    Veterans Benefits and Services = 34728873816.50
    Administration of Justice = 8760071148.10
    General Government = -1501170352.45
    Net Interest = 104490682743.68
    Undistributed Offsetting Receipts = -9199824503.27
    Total = 616066757155.07
    Receipts = null
    Individual Income Taxes = 283146831936.70
    Corporation Income Taxes = 69536652912.03
    Social Insurance and Retirement Receipts: = null
    Employment and General Retirement = 153951919603.48
    Unemployment Insurance = 800628657.83

[outlays-by-function?] https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/mts/mts_table_5
  fields: record_date, parent_id, classification_id, classification_desc, current_month_gross_outly_amt, current_month_app_rcpt_amt, current_month_net_outly_amt, current_fytd_gross_outly_amt, current_fytd_app_rcpt_amt, current_fytd_net_outly_amt, prior_fytd_gross_outly_amt, prior_fytd_app_rcpt_amt, prior_fytd_net_outly_amt, table_nbr, src_line_nbr, print_order_nbr, line_code_nbr, data_type_cd, record_type_cd, sequence_level_nbr, sequence_number_cd, record_fiscal_year, record_fiscal_quarter, record_calendar_year, record_calendar_quarter, record_calendar_month, record_calendar_day
  distinct classification_desc: ['Federal Emergency Management Agency:', 'Water and Science:', 'Department of Justice:', 'Corps of Engineers:', 'National Science Foundation:', 'Other', 'Total--Interest Received by Trust Funds', 'Rents and Royalties on the Outer Continental Shelf Lands', 'Sale of Major Assets', 'Total--Undistributed Offsetting Receipts', 'Total Outlays', 'Total On-Budget', 'Total Off-Budget', 'Total Surplus (+) or Deficit (-)', 'Legislative Branch:', 'Natural Resources Conservation Service:', 'Rural Housing Service:', 'Social Services Block Grant', 'Credit Accounts:', 'Indian Affairs:', 'Department of Labor:', 'Community Service Employment for Older Americans', "Office of Workers' Compensation Programs:", 'Payment to Foreign Service Retirement and Disability Fund', 'Federal Aviation Administration:', 'Bureau of the Fiscal Service:', 'Taxpayer Services', 'Interest on the Public Debt:', 'National Service Life', 'Multilateral Assistance:']
  latest 2026-06-30 rows (classification_desc = current_month_gross_outly_amt):
    Federal Emergency Management Agency: = null
    Water and Science: = null
    Department of Justice: = null
    Corps of Engineers: = null
    National Science Foundation: = null
    Other = -47678995.62
    Total--Interest Received by Trust Funds = -69675229114.59
    Rents and Royalties on the Outer Continental Shelf Lands = null
    Sale of Major Assets = null
    Total--Undistributed Offsetting Receipts = -77719746908.70
    Total Outlays = 754365172803.93
    Total On-Budget = 634752191162.22
    Total Off-Budget = 119612981641.71
    Total Surplus (+) or Deficit (-) = null
    Total On-Budget = null

  On-budget receipts (total minus OASI+DI trust fund receipts):
    resolved: 136 months, latest 2026-06 = $374.8B

  mts_table_5 'Total On-Budget' / 'Total Off-Budget' cross-check (diagnostic only — investigating whether these describe receipts or outlays; never used to build data.json):
    Total On-Budget: {'current_month_gross_outly_amt': 'null', 'current_month_app_rcpt_amt': 'null', 'current_month_net_outly_amt': '-128723862571.22'}
    Total Off-Budget: {'current_month_gross_outly_amt': 'null', 'current_month_app_rcpt_amt': 'null', 'current_month_net_outly_amt': '8418586984.85'}

  LIVE headline debt-service ratio (net interest to the public / total receipts, net of refunds): 19.6% as of 2026-06 (42 history pts)
  LIVE second-row debt-service ratio (gross interest incl. GAS / total receipts, net of refunds): 25.1% as of 2026-06 (42 history pts)

  Debt-service calibration matrix (Dalio Ch.17 US target: 22%, Mar 2025):
  numerator                         on-budget receipts     tax receipts only        total receipts
  gross (incl. GAS)                              33.3%                 35.0%                 25.1%
  net-to-public (excl. GAS)                      25.9%                 27.8%                 19.6%
  net interest, function 900                     25.8%                 27.8%                 19.5%

Total-debt series comparison (Dalio Ch.17 US 'other debt' target: 340%):
  TCMDO: 362.6% of GDP as of 2026-01-01 (GDP as of 2026-01-01) <- used for 'Total debt' row
  TCMDODNS: 256.7% of GDP as of 2026-01-01 (GDP as of 2026-01-01) (diagnostic only, not used — see series.py)

Verifying IMF COFER via DBnomics (non-fatal — manual fallback on failure)

[cofer] https://api.db.nomics.world/v22/series/IMF/COFER (FREQ=Q, REF_AREA=W00)
  23 series; codes: ['Q.W00.RAXGFXARAUDRT_PT', 'Q.W00.RAXGFXARAUD_USD', 'Q.W00.RAXGFXARCADRT_PT', 'Q.W00.RAXGFXARCAD_USD', 'Q.W00.RAXGFXARCHFRT_PT', 'Q.W00.RAXGFXARCHF_USD', 'Q.W00.RAXGFXARCNYRT_PT', 'Q.W00.RAXGFXARCNY_USD', 'Q.W00.RAXGFXAREURORT_PT', 'Q.W00.RAXGFXAREURO_USD', 'Q.W00.RAXGFXARGBPRT_PT', 'Q.W00.RAXGFXARGBP_USD', 'Q.W00.RAXGFXARJPYRT_PT', 'Q.W00.RAXGFXARJPY_USD', 'Q.W00.RAXGFXAROCRT_PT', 'Q.W00.RAXGFXAROC_USD', 'Q.W00.RAXGFXARRT_PT', 'Q.W00.RAXGFXARUSDRT_PT', 'Q.W00.RAXGFXARUSD_USD', 'Q.W00.RAXGFXAR_USD', 'Q.W00.RAXGFXURRT_PT', 'Q.W00.RAXGFXUR_USD', 'Q.W00.RAXGFX_USD']
  computed USD share: 57.7% as of 2025-Q1 (105 pts)

Verifying gold sources (Treasury holdings + DBnomics LBMA price; non-fatal — manual fallback on failure)

[gold-holdings] https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/gold_reserve
  fields: record_date, facility_desc, form_desc, location_desc, fine_troy_ounce_qty, book_value_amt, src_line_nbr, record_fiscal_year, record_fiscal_quarter, record_calendar_year, record_calendar_quarter, record_calendar_month, record_calendar_day
  distinct facility_desc: ['Mint Held Gold - Deep Storage', 'Mint Held Gold - Working Stock', 'Federal Reserve Bank Held Gold']
  distinct form_desc: ['Gold Bullion', 'Gold Coins']
  distinct location_desc: ['Denver, CO', 'Fort Knox, KY', 'West Point, NY', 'All Locations- Coins, blanks, miscellaneous', 'Federal Reserve Banks - NY Vault', 'Federal Reserve Banks - Display']
  latest 2026-06-30 rows:
    {'record_date': '2026-06-30', 'facility_desc': 'Mint Held Gold - Deep Storage', 'form_desc': 'Gold Bullion', 'location_desc': 'Denver, CO', 'fine_troy_ounce_qty': '43853707.279', 'book_value_amt': '1851599995.81', 'src_line_nbr': '1', 'record_fiscal_year': '2026', 'record_fiscal_quarter': '3', 'record_calendar_year': '2026', 'record_calendar_quarter': '2', 'record_calendar_month': '06', 'record_calendar_day': '30'}
    {'record_date': '2026-06-30', 'facility_desc': 'Mint Held Gold - Deep Storage', 'form_desc': 'Gold Bullion', 'location_desc': 'Fort Knox, KY', 'fine_troy_ounce_qty': '147341858.382', 'book_value_amt': '6221097412.78', 'src_line_nbr': '2', 'record_fiscal_year': '2026', 'record_fiscal_quarter': '3', 'record_calendar_year': '2026', 'record_calendar_quarter': '2', 'record_calendar_month': '06', 'record_calendar_day': '30'}
    {'record_date': '2026-06-30', 'facility_desc': 'Mint Held Gold - Deep Storage', 'form_desc': 'Gold Bullion', 'location_desc': 'West Point, NY', 'fine_troy_ounce_qty': '54067331.379', 'book_value_amt': '2282841677.17', 'src_line_nbr': '3', 'record_fiscal_year': '2026', 'record_fiscal_quarter': '3', 'record_calendar_year': '2026', 'record_calendar_quarter': '2', 'record_calendar_month': '06', 'record_calendar_day': '30'}
    {'record_date': '2026-06-30', 'facility_desc': 'Mint Held Gold - Working Stock', 'form_desc': 'Gold Coins', 'location_desc': 'All Locations- Coins, blanks, miscellaneous', 'fine_troy_ounce_qty': '2783218.656', 'book_value_amt': '117513614.74', 'src_line_nbr': '4', 'record_fiscal_year': '2026', 'record_fiscal_quarter': '3', 'record_calendar_year': '2026', 'record_calendar_quarter': '2', 'record_calendar_month': '06', 'record_calendar_day': '30'}
    {'record_date': '2026-06-30', 'facility_desc': 'Federal Reserve Bank Held Gold', 'form_desc': 'Gold Bullion', 'location_desc': 'Federal Reserve Banks - NY Vault', 'fine_troy_ounce_qty': '13376987.724', 'book_value_amt': '564805851.07', 'src_line_nbr': '5', 'record_fiscal_year': '2026', 'record_fiscal_quarter': '3', 'record_calendar_year': '2026', 'record_calendar_quarter': '2', 'record_calendar_month': '06', 'record_calendar_day': '30'}
    {'record_date': '2026-06-30', 'facility_desc': 'Federal Reserve Bank Held Gold', 'form_desc': 'Gold Bullion', 'location_desc': 'Federal Reserve Banks - Display', 'fine_troy_ounce_qty': '1993.321', 'book_value_amt': '84162.40', 'src_line_nbr': '6', 'record_fiscal_year': '2026', 'record_fiscal_quarter': '3', 'record_calendar_year': '2026', 'record_calendar_quarter': '2', 'record_calendar_month': '06', 'record_calendar_day': '30'}
    {'record_date': '2026-06-30', 'facility_desc': 'Federal Reserve Bank Held Gold', 'form_desc': 'Gold Coins', 'location_desc': 'Federal Reserve Banks - NY Vault', 'fine_troy_ounce_qty': '73452.066', 'book_value_amt': '3101307.82', 'src_line_nbr': '7', 'record_fiscal_year': '2026', 'record_fiscal_quarter': '3', 'record_calendar_year': '2026', 'record_calendar_quarter': '2', 'record_calendar_month': '06', 'record_calendar_day': '30'}
    {'record_date': '2026-06-30', 'facility_desc': 'Federal Reserve Bank Held Gold', 'form_desc': 'Gold Coins', 'location_desc': 'Federal Reserve Banks - Display', 'fine_troy_ounce_qty': '377.434', 'book_value_amt': '15936.11', 'src_line_nbr': '8', 'record_fiscal_year': '2026', 'record_fiscal_quarter': '3', 'record_calendar_year': '2026', 'record_calendar_quarter': '2', 'record_calendar_month': '06', 'record_calendar_day': '30'}

[gold-price] https://api.db.nomics.world/v22/series/IMF/PCPS (bare dump)
  all series_codes in dataset: [... 1000 entries trimmed, PGOLD-related only shown ...] ['A.W00.PGOLD.IX', 'A.W00.PGOLD.PC_CP_A_PT', 'A.W00.PGOLD.PC_PP_PT', 'A.W00.PGOLD.USD', 'M.W00.PGOLD.IX', 'M.W00.PGOLD.PC_CP_A_PT', 'M.W00.PGOLD.PC_PP_PT', 'M.W00.PGOLD.USD', 'Q.W00.PGOLD.IX', 'Q.W00.PGOLD.PC_CP_A_PT', 'Q.W00.PGOLD.PC_PP_PT', 'Q.W00.PGOLD.USD']
  selected series_code: M.W00.PGOLD.USD
  426 observations; latest: 2025-06 = 3351.85857142857 USD/oz

  computed gold market value: $876.5B as of 2025-06 (162 months)
##[group]Run python scripts/fetch.py --force
python scripts/fetch.py --force
shell: /usr/bin/bash -e {0}
env:
  pythonLocation: /opt/hostedtoolcache/Python/3.12.13/x64
  PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.12.13/x64/lib/pkgconfig
  Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
  Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
  Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
  LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.13/x64/lib
  FRED_API_KEY: ***
##[endgroup]
Wrote public/data.json — generatedAt 2026-07-19T21:26:05Z
  debt_to_gdp                     99%  (2026-Q1, 225 pts)
  debt_service_to_revenue         20%  (2026-06, 42 pts)
  real_rates                     0.6%  (2026-Q2, 258 pts)
  reserves_to_gdp                3.7%  (2025-Q2, 54 pts)

```

**Claim status: VERIFIED** — copied from the actual job log of the run
named above. The 3×3 debt-service matrix embedded in the output (numerator
× on-budget/tax-only/total-receipts columns) is the diagnostic matrix,
computed on the now-corrected (net-of-refunds) receipts throughout —
compare against `docs/review/2026-07-19c-verification.md`'s matrix (same
structure, gross-receipts basis) to see the effect of the fix directly.

---

## Receipts field check + corrected-basis 3×4 matrix (`scripts/receipts_check.py`, `scripts/basis_recheck.py`)

Two diagnostics ran earlier the same session, before and after the
`treasury.py` fix, to (1) confirm the gross-vs-net field bug against CBO's
published FY totals and (2) recompute the full 3×4 matrix (adding the 4th
CBO-projected column) and `debt_to_revenue` on all four denominators once
fixed. Both scripts have since been removed (diagnostic only, per
`TASKreceiptsdenominator.md`); their combined output is pasted verbatim
below — copied from
`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29704148981`,
job `88238174157`, 2026-07-19 21:19-21:20 UTC (commit `6e91927`, before the
`treasury.py` fix landed at `534ad4a` — this run computed both gross and
net bases independently inside the diagnostic scripts themselves, not by
calling the not-yet-fixed `treasury.py` functions, so its "net (proposed)"
/ "net, shipped" columns already show the post-fix numbers).

```
==============================================================================
RECEIPTS CHECK — gross vs net (TASKreceiptsdenominator.md)
==============================================================================

Field mapping confirmed in mts_table_4 sample row:
  gross: current_month_gross_rcpt_amt
  refund: current_month_refund_amt
  net: current_month_net_rcpt_amt

monthly_receipts() currently sums: current_month_gross_rcpt_amt

Total-receipts grand-total row, latest month (2026-06-30):
  classification_desc: 'Total -- Social Insurance and Retirement Receipts'
  gross=155529920773.74  refund=21056106.18  net=155508864667.56  gross-refund=155508864667.56
  classification_desc: 'Total -- Miscellaneous Receipts'
  gross=3217880635.11  refund=2515344.34  net=3215365290.77  gross-refund=3215365290.77
  classification_desc: 'Total -- Receipts'
  gross=563801628771.0  refund=68040147202.3  net=495761481568.7  gross-refund=495761481568.7

--- FY totals: gross vs net vs CBO published ---

FY2024 (gross months=12, net months=12), CBO published: $4.920T
  gross total: $5.265T  residual +7.0%
  net total:   $4.919T  residual -0.0%

FY2025 (gross months=12, net months=12), CBO published: $5.235T
  gross total: $5.617T  residual +7.3%
  net total:   $5.235T  residual -0.0%

--- on-budget receipts (total minus OASI+DI), latest overlapping month, both bases ---
  gross (current)  latest 2026-06 = $442.8B
  net (proposed)   latest 2026-06 = $374.8B

--- effect on shipped debt-service ratios: gross-basis vs net-basis receipts, TTM ---

gross interest:
  total receipts (gross, current)  Mar-2025: 22.3%   today (2026-06): 23.0%
  total receipts (net, proposed)   Mar-2025: 23.9%   today (2026-06): 25.1%
  on-budget (gross, current)       Mar-2025: 29.4%   today (2026-06): 29.7%
  on-budget (net, proposed)        Mar-2025: 32.2%   today (2026-06): 33.3%

net-to-public interest:
  total receipts (gross, current)  Mar-2025: 17.8%   today (2026-06): 17.9%
  total receipts (net, proposed)   Mar-2025: 19.0%   today (2026-06): 19.6%
  on-budget (gross, current)       Mar-2025: 23.4%   today (2026-06): 23.1%
  on-budget (net, proposed)        Mar-2025: 25.6%   today (2026-06): 25.9%

Done.
==============================================================================
BASIS RE-CHECK — corrected (net, total) receipts, full matrix
==============================================================================

--- confirm the fix: monthly_receipts() FY totals vs CBO published ---
  FY2024: $4.919T vs CBO $4.920T  residual -0.03%
  FY2025: $5.235T vs CBO $5.235T  residual -0.01%

--- 3 numerators x 4 denominators, monthly TTM, corrected basis ---

gross (incl. GAS):
  total receipts (net, shipped)            Mar-2025: 23.9%   today (2026-06): 25.1%
  on-budget receipts (net, diagnostic)     Mar-2025: 32.2%   today (2026-06): 33.3%
  tax receipts only                        Mar-2025: 37.6%   today (2026-03): 35.0%
  CBO Jan-2025 projected receipts          Mar-2025: 22.5%   today (2026-06): 24.9%

net-to-public (excl. GAS):
  total receipts (net, shipped)            Mar-2025: 19.0%   today (2026-06): 19.6%
  on-budget receipts (net, diagnostic)     Mar-2025: 25.6%   today (2026-06): 25.9%
  tax receipts only                        Mar-2025: 29.9%   today (2026-03): 27.8%
  CBO Jan-2025 projected receipts          Mar-2025: 17.9%   today (2026-06): 19.4%

net interest, fn900:
  total receipts (net, shipped)            Mar-2025: 18.9%   today (2026-06): 19.5%
  on-budget receipts (net, diagnostic)     Mar-2025: 25.4%   today (2026-06): 25.8%
  tax receipts only                        Mar-2025: 29.7%   today (2026-03): 27.8%
  CBO Jan-2025 projected receipts          Mar-2025: 17.7%   today (2026-06): 19.3%

--- debt_to_revenue, quarterly, all four denominators, corrected basis ---

  total receipts (net, shipped)            latest (2026-Q1): 576%
  on-budget receipts (net, diagnostic)     latest (2026-Q1): 760%
  tax receipts only                        latest (2026-Q1): 873%
  CBO Jan-2025 projected receipts          latest (2026-Q1): 589%

  Debt held by public, 2025-Q1: $28.93T (Dalio's stated ~$28.9T, ~580% anchor)
    total receipts (net, shipped): TTM $4.99T -> debt/revenue 580%
    on-budget receipts (net, diagnostic): TTM $3.71T -> debt/revenue 780%
    tax receipts only: TTM $3.17T -> debt/revenue 912%
    CBO Jan-2025 projected receipts: TTM $5.31T -> debt/revenue 545%

--- shipped ratios (treasury.py functions directly) ---
  debt_service_ratio() [headline, net/total]: 19.6% as of 2026-06
  gross_debt_service_ratio() [second row, gross/total]: 25.1% as of 2026-06

Done.
```

**Claim status: VERIFIED** — copied from the actual job logs of the two
runs named above (`29703925309`/`88237568913` for the field check,
`29704148981`/`88238174157` for the basis re-check), fetched via the
GitHub API, timestamps stripped only. The "shipped ratios" line at the
end matches the production run's own `LIVE headline`/`LIVE second-row`
lines earlier in this file exactly (19.6% / 25.1%), confirming the
diagnostic and the actual shipped code agree.
