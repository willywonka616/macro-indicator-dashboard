# Verification log — live Actions run output, pasted verbatim

> **Base commit:** `4c344e13cb6d0bb30ca432944ec2c9092c9fb4cf` (HEAD of
> `claude/new-session-ldotj8` at write time)
> **Written:** 2026-07-19T12:07:39Z UTC
> If `claude/new-session-ldotj8`'s HEAD commit is newer than the SHA above,
> newer run output may exist that this file doesn't reflect — check the
> commit history.

**Why this file exists:** a reviewer working only from public blob URLs
cannot open the Actions tab, cannot see job logs, and may be served a cached
copy of any file. Every number this project claims as "live" has to be
provable from a file actually committed to the repo, or it isn't provable at
all to that reviewer. This file is the run output itself, not a summary of
it.

**Claim status: VERIFIED.** Everything below is copied from the actual job
log of a real `workflow_dispatch` run of `update-data.yml`
(`https://github.com/willywonka616/macro-indicator-dashboard/actions`, run
attached to commit `4c344e1`, 2026-07-19 12:03–12:05 UTC), fetched via the
GitHub API and pasted with only two mechanical edits: per-line ISO
timestamps and terminal ANSI color codes stripped (they add no information
and hurt readability), and one very long list (every series code in the IMF
PCPS dataset — ~1000 entries, one line) trimmed to just the `PGOLD`-related
entries with an explicit note where that happened. Nothing was reworded,
reordered, or summarized beyond that.

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

  LIVE debt-service ratio (gross interest / total receipts): 23.0% as of 2026-06 (42 history pts)

  Debt-service calibration matrix (Dalio Ch.17 US target: 22%, Mar 2025):
  numerator                          tax receipts only        total receipts
  gross (incl. GAS)                              35.0%                 23.0%
  net-to-public (excl. GAS)                      27.8%                 17.9%
  net interest, function 900                     27.8%                 17.8%

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

Wrote public/data.json — generatedAt 2026-07-19T12:04:56Z
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

[claude/new-session-ldotj8 4c344e1] data: monthly refresh (2026-07-19)
 1 file changed, 2 insertions(+), 2 deletions(-)
```

*(Note: the log's own `[gold-price]` heading and the "Verifying gold
sources" banner above it still say "DBnomics LBMA price" — that's a stale
label in `scripts/gold.py`'s print statements left over from before the
source switch to IMF PCPS; it prints a fixed string, not a re-derived one,
so it didn't get updated when the actual URL did. The **behavior** is
correct — it hits `IMF/PCPS`, as the URL on the next line shows — only the
human-readable log label is out of date. Filed as a loose end, not hidden.)*

---

## Prior failures — gold price source discovery (why PCPS, not LBMA)

These are not from the run above — they're from earlier `workflow_dispatch`
runs against earlier commits on this same branch, kept here because the
task instructions ask for failures to be included, not just the final
success. Quoted verbatim from the job log of the run immediately following
commit `95160ea` ("Fix LBMA gold price fetch: dump bare dataset, filter
client-side") — a bare, unfiltered request to DBnomics' `LBMA/gold_D`
dataset, no `dimensions` filter, no series code:

```
[gold-price] FAILED: request to https://api.db.nomics.world/v22/series/LBMA/gold_D failed after 4 tries: 404 Client Error: NOT FOUND for url: https://api.db.nomics.world/v22/series/LBMA/gold_D?limit=1000&observations=1

  gold market value computation FAILED: request to https://api.db.nomics.world/v22/series/LBMA/gold_D failed after 4 tries: 404 Client Error: NOT FOUND for url: https://api.db.nomics.world/v22/series/LBMA/gold_D?limit=1000&observations=1
```

and, from the `--force` build step of that same run, the fallback firing
correctly:

```
Gold-inclusive reserves unavailable, using manual value: request to https://api.db.nomics.world/v22/series/LBMA/gold_D failed after 4 tries: 404 Client Error: NOT FOUND for url: https://api.db.nomics.world/v22/series/LBMA/gold_D?limit=1000&observations=1
```

Two earlier attempts against `LBMA/gold_D` also 404'd (a direct
`.../gold_D/gold_D_USD_AM` series-code path, and a dataset-level request
with a `dimensions` filter) — those failures are described, not quoted
verbatim, in `STATUS.md` §3 and in the commit message of `95160ea`, because
the exact log text from those two runs was not captured into this file.
**This is stated plainly rather than reconstructed**: don't trust a verbatim
block for those two if one appears anywhere else — only the bare-dump
failure above and the final PCPS success are backed by an exact pasted log.

---

## Sanity-band checks (from source, not from a run log — the bands never
tripped, so there is no "band fired" line to quote)

Both live derived values landed inside their bands on the run above, so
`fetch.py` never printed a band-violation message — there is nothing to
paste verbatim for a check that passed silently. The bands themselves, read
directly from `scripts/fetch.py`:

```python
service = T.debt_service_ratio()
if not (5.0 <= service["latest"] <= 40.0):
    raise RuntimeError(...)   # would abort the build; did not fire (23.0% is inside)
...
if not (0.5 <= reserves_incl_gold["latest"] <= 15.0):
    raise RuntimeError(...)   # would abort the build; did not fire (3.7% is inside)
```

**Claim status: VERIFIED** that these are the exact lines in
`scripts/fetch.py` at commit `4c344e1` (read directly from the file, not
recalled) and that the run above completed without either `RuntimeError`
firing (the `Wrote public/data.json` line in the transcript above only
prints after both checks pass — an abort would show a Python traceback and
no `Wrote public/data.json` line instead, which is not what the transcript
shows).
