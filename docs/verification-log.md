# Verification log — live Actions run output, pasted verbatim

> **Base commit:** `6427d61` (HEAD of `claude/new-session-ldotj8` at write
> time)
> **Written:** 2026-07-19T20:49:52Z UTC
> If `claude/new-session-ldotj8`'s HEAD commit is newer than the SHA above,
> newer run output may exist that this file doesn't reflect — check the
> commit history.

**Stamp-only refresh this pass** — no new run since the drift-test run
quoted below (commit `7599e19`); the two commits since then
(`7ff77c5` §12 findings, `6427d61` diagnostic-script removal) only added
prose and deleted files, so nothing below is out of date — only the
header stamp above is updated to match true HEAD.

**Appended previously** (everything up to and including "Prior investigation
history" is unchanged from the previous write, covering the 3×3 matrix, the
net/on-budget basis, and the total-debt TCMDO-vs-TCMDODNS comparison — see
STATUS.md §3/§9/§11). New this pass: the "Drift test" section below,
covering the monthly-resolution 3×4 matrix recomputed at Dalio's stated
March-2025 vintage, plus a 4th (CBO-projected) denominator — see
STATUS.md §12 for the narrative and the basis-identification conclusion.

**Why this file exists:** a reviewer working only from public blob URLs
cannot open the Actions tab, cannot see job logs, and may be served a
cached copy of any file. Every number this project claims as "live" has to
be provable from a file actually committed to the repo, or it isn't
provable at all to that reviewer. This file is the run output itself, not
a summary of it.

**Claim status: VERIFIED.** Everything below is copied from the actual job
log of a real `workflow_dispatch` run of `update-data.yml`
(`https://github.com/willywonka616/macro-indicator-dashboard/actions`, run
attached to commit `0825467`, committed data as `3ed5858`, 2026-07-19
18:13–18:16 UTC), fetched via the GitHub API and pasted with only two
mechanical edits: per-line ISO timestamps and terminal ANSI color codes
stripped (they add no information and hurt readability), and one very long
line (every series code in the IMF PCPS dataset — 1000 entries, one line)
trimmed to just the `PGOLD`-related entries with an explicit note where
that happened. Nothing else was reworded, reordered, or summarized.

---

## Run output: `python scripts/fetch.py --verify`, then `--force`

```
Run python scripts/fetch.py --verify
python scripts/fetch.py --verify
shell: /usr/bin/bash -e {0}
env:
  pythonLocation: /opt/hostedtoolcache/Python/3.12.13/x64
  PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.12.13/x64/lib/pkgconfig
  Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
  Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
  Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
  LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.13/x64/lib
  FRED_API_KEY: ***

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
    resolved: 136 months, latest 2026-06 = $442.8B

  mts_table_5 'Total On-Budget' / 'Total Off-Budget' cross-check (diagnostic only — investigating whether these describe receipts or outlays; never used to build data.json):
    Total On-Budget: {'current_month_gross_outly_amt': 'null', 'current_month_app_rcpt_amt': 'null', 'current_month_net_outly_amt': '-128723862571.22'}
    Total Off-Budget: {'current_month_gross_outly_amt': 'null', 'current_month_app_rcpt_amt': 'null', 'current_month_net_outly_amt': '8418586984.85'}

  LIVE headline debt-service ratio (net interest to the public / on-budget receipts): 23.1% as of 2026-06 (42 history pts)
  LIVE second-row debt-service ratio (gross interest incl. GAS / on-budget receipts): 29.7% as of 2026-06 (42 history pts)

  Debt-service calibration matrix (Dalio Ch.17 US target: 22%, Mar 2025):
  numerator                         on-budget receipts     tax receipts only        total receipts
  gross (incl. GAS)                              29.7%                 35.0%                 23.0%
  net-to-public (excl. GAS)                      23.1%                 27.8%                 17.9%
  net interest, function 900                     23.0%                 27.8%                 17.8%

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
  all series_codes in dataset: 1000 series total (full list omitted here for length —
  every commodity in PCPS x frequency x {.IX,.PC_CP_A_PT,.PC_PP_PT,.USD}, confirmed present in the raw run log).
  PGOLD-related codes actually present (the ones that matter for this fix): ['A.W00.PGOLD.IX', 'A.W00.PGOLD.PC_CP_A_PT', 'A.W00.PGOLD.PC_PP_PT', 'A.W00.PGOLD.USD', 'M.W00.PGOLD.IX', 'M.W00.PGOLD.PC_CP_A_PT', 'M.W00.PGOLD.PC_PP_PT', 'M.W00.PGOLD.USD', 'Q.W00.PGOLD.IX', 'Q.W00.PGOLD.PC_CP_A_PT', 'Q.W00.PGOLD.PC_PP_PT', 'Q.W00.PGOLD.USD']
  selected series_code: M.W00.PGOLD.USD
  426 observations; latest: 2025-06 = 3351.85857142857 USD/oz

  computed gold market value: $876.5B as of 2025-06 (162 months)
Run python scripts/fetch.py --force
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

Wrote public/data.json — generatedAt 2026-07-19T18:15:56Z
  debt_to_gdp                     99%  (2026-Q1, 225 pts)
  debt_service_to_revenue         23%  (2026-06, 42 pts)
  real_rates                     0.6%  (2026-Q2, 258 pts)
  reserves_to_gdp                3.7%  (2025-Q2, 54 pts)
Run if git diff --quiet -- public/data.json; then
if git diff --quiet -- public/data.json; then
  echo "public/data.json unchanged — nothing to commit."
else
  git config user.name "github-actions[bot]"
  git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
  git add public/data.json
  git commit -m "data: monthly refresh ($(date -u +%Y-%m-%d))"
  git push
fi
shell: /usr/bin/bash -e {0}
env:
  pythonLocation: /opt/hostedtoolcache/Python/3.12.13/x64
  PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.12.13/x64/lib/pkgconfig
  Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
  Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
  Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.13/x64
  LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.13/x64/lib

[claude/new-session-ldotj8 3ed5858] data: monthly refresh (2026-07-19)
 1 file changed, 759 insertions(+), 400 deletions(-)
```

*(Note: the "Verifying gold sources" banner and `[gold-price]` label above
still say "DBnomics LBMA price" in the source code's print strings — a
leftover label from before the switch to IMF PCPS that prints a fixed
string rather than a re-derived one. The **behavior** is correct — it hits
`IMF/PCPS`, as the URL on the very next line shows — only the human-readable
banner text is stale. Filed as a loose end, not hidden; see STATUS.md §3.)*

---

## Sanity-band checks (from source, not from a run log — the bands never
tripped, so there is no "band fired" line to quote)

All four live derived values (net debt-service, gross debt-service,
reserves-incl-gold, debt/revenue) landed inside their bands on the run
above, so `fetch.py` never printed a band-violation message. The bands
themselves, read directly from `scripts/fetch.py` at commit `0d1c43f`:

```python
service = T.debt_service_ratio()
if not (10.0 <= service["latest"] <= 40.0):
    raise RuntimeError(...)   # did not fire (23.1% is inside)

gross_service = T.gross_debt_service_ratio()
if not (15.0 <= gross_service["latest"] <= 50.0):
    raise RuntimeError(...)   # did not fire (29.7% is inside)

if not (0.5 <= reserves_incl_gold["latest"] <= 15.0):
    raise RuntimeError(...)   # did not fire (3.7% is inside)

debt_to_revenue = S.debt_to_revenue_pct(...)
if not (200.0 <= debt_to_revenue["latest"] <= 1200.0):
    raise RuntimeError(...)   # did not fire (691.9% is inside)
```

**Claim status: VERIFIED** that these are the exact lines in
`scripts/fetch.py` at commit `0d1c43f` (read directly from the file) and
that the run above completed without any `RuntimeError` firing — the
`Wrote public/data.json` line in the transcript only prints after all four
checks pass; an abort would show a Python traceback and no `Wrote
public/data.json` line instead.

---

## Drift test: matrix recomputed at Dalio's stated vintage (Mar-2025), monthly, 2023-01 → present

Per `TASKdrifttest.md`: a diagnostic, not a feature — nothing ships from it
except the findings recorded here and in STATUS.md §12. Runs
`scripts/drift_test.py` (temporary, removed after this pass — see STATUS.md
§12), which reuses `treasury.py`/`series.py`'s numerator and denominator
definitions unchanged, extended with a 4th denominator: CBO's January 2025
baseline projected total receipts (by fiscal year, applied as a flat FY/12
monthly step — FY2025 $5,163B, FY2026 $5,524B; sourcing/confidence for
those two figures is in the script's module docstring, quoted below).
Copied verbatim from the `push`-triggered run attached to commit `7599e19`
(`https://github.com/willywonka616/macro-indicator-dashboard/actions/runs/29702780297`,
job `88234569970`, 2026-07-19 20:34–20:35 UTC), with only per-line ISO
timestamps stripped.

```
==============================================================================
DRIFT TEST — matrix recomputed at book vintage (Mar-2025) + monthly, 2023-01..present
Run at 2026-07-19T20:34:49.173651+00:00
==============================================================================

CBO Jan-2025 baseline FY totals used (see module docstring for sourcing/confidence):
  FY2025: $5163.0B
  FY2026: $5524.0B

--- 3 numerators x 4 denominators, monthly TTM ratio, 2023-01 -> present ---

gross (incl. GAS):
  on-budget receipts
    Mar-2025: 29.4%   today (2026-06): 29.7%   min: 19.1%  max: 29.7%   slope: +3.11 pt/yr
    does not cross 22% in 2024-01..2025-06 — closest approach: 26.1% at 2024-01
  total receipts
    Mar-2025: 22.3%   today (2026-06): 23.0%   min: 15.0%  max: 23.0%   slope: +2.33 pt/yr
    crosses 22% in 2024-01..2025-06 at: 2024-12, 2025-04
  CBO Jan-2025 projected receipts
    Mar-2025: 21.8%   today (2026-06): 24.9%   min: 15.0%  max: 24.9%   slope: +2.88 pt/yr
    crosses 22% in 2024-01..2025-06 at: 2025-04
  tax receipts only
    Mar-2025: 37.6%   today (2026-03): 35.0%   min: 24.3%  max: 37.6%   slope: +3.38 pt/yr
    does not cross 22% in 2024-01..2025-06 — closest approach: 33.4% at 2024-01

net-to-public (excl. GAS):
  on-budget receipts
    Mar-2025: 23.4%   today (2026-06): 23.1%   min: 13.2%  max: 23.4%   slope: +2.91 pt/yr
    crosses 22% in 2024-01..2025-06 at: 2024-07
  total receipts
    Mar-2025: 17.8%   today (2026-06): 17.9%   min: 10.4%  max: 17.9%   slope: +2.20 pt/yr
    does not cross 22% in 2024-01..2025-06 — closest approach: 17.8% at 2025-03
  CBO Jan-2025 projected receipts
    Mar-2025: 17.4%   today (2026-06): 19.4%   min: 10.4%  max: 19.4%   slope: +2.63 pt/yr
    does not cross 22% in 2024-01..2025-06 — closest approach: 18.9% at 2025-04
  tax receipts only
    Mar-2025: 29.9%   today (2026-03): 27.8%   min: 16.7%  max: 29.9%   slope: +3.50 pt/yr
    does not cross 22% in 2024-01..2025-06 — closest approach: 25.8% at 2024-01

net interest, fn900:
  on-budget receipts
    Mar-2025: 23.2%   today (2026-06): 23.0%   min: 13.0%  max: 23.2%   slope: +2.94 pt/yr
    crosses 22% in 2024-01..2025-06 at: 2024-08
  total receipts
    Mar-2025: 17.6%   today (2026-06): 17.8%   min: 10.2%  max: 17.8%   slope: +2.22 pt/yr
    does not cross 22% in 2024-01..2025-06 — closest approach: 17.6% at 2025-03
  CBO Jan-2025 projected receipts
    Mar-2025: 17.2%   today (2026-06): 19.3%   min: 10.2%  max: 19.3%   slope: +2.65 pt/yr
    does not cross 22% in 2024-01..2025-06 — closest approach: 18.8% at 2025-04
  tax receipts only
    Mar-2025: 29.7%   today (2026-03): 27.8%   min: 16.5%  max: 29.7%   slope: +3.55 pt/yr
    does not cross 22% in 2024-01..2025-06 — closest approach: 25.5% at 2024-01

--- debt_to_revenue, quarterly, against Dalio's ~580% (Mar-2025) / ~700% (10yr) anchor ---

  on-budget receipts                               latest (2026-Q1): 692%
  total receipts                                   latest (2026-Q1): 536%
  CBO Jan-2025 projected receipts                  latest (2026-Q1): 589%
  tax receipts only                                latest (2026-Q1): 873%

  Debt held by public, 2025-Q1: $28.93T (task's stated estimate: ~$28.9T)
    on-budget receipts: TTM $4.05T -> debt/revenue 714%
    total receipts: TTM $5.34T -> debt/revenue 542%
    CBO Jan-2025 projected receipts: TTM $5.46T -> debt/revenue 530%
    tax receipts only: TTM $3.17T -> debt/revenue 912%

--- known partial result cross-check (net interest / total receipts, TTM) ---
  Mar-2025: 17.8% (task's stated estimate: ~18.9%)
  today (2026-06): 17.9% (task's stated estimate: ~17.9%)

--- FY2024 gross interest / CBO FY2025-projected receipts hypothesis ---
  FY2024 gross interest (actual, summed): $1133.0B (task's stated estimate: ~$1,126.5B)
  / CBO Jan-2025 FY2025 projected receipts $5163.0B = 21.9% (task's stated estimate: ~21.8%)

Done.
```

**Claim status: VERIFIED** — copied from the actual job log of the run
named above, fetched via the GitHub API, mechanically stripped of
timestamps only. See STATUS.md §12 for the reading of these numbers
(which outcome-table row from `TASKdrifttest.md` they match, and the
basis-identification conclusion).

---

## Prior investigation history (condensed — full detail in STATUS.md)

Two earlier rounds of live investigation aren't re-pasted verbatim here to
keep this file focused on the current state; they're documented with their
own evidence in STATUS.md:
- **STATUS.md §3** (gold price source): three failed DBnomics/LBMA URL
  attempts (all genuine 404s, root-caused to LBMA restricting its public
  data in late 2025), then the switch to IMF PCPS, then a PGOLD-variant
  selection bug (picked the `.IX` index instead of `.USD` level on the
  first live PCPS attempt) and its fix.
- **STATUS.md §9/§11** (total debt): the TCMDODNS hypothesis, tried and
  refuted this pass (256.7% vs. TCMDO's 362.6%, further from Dalio's 340%
  target, not closer) — the comparison itself is in the run output above.
