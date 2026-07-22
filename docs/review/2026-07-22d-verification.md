# Verification log, review round `2026-07-22d` — a real quarter-bucketing bug, found and fixed

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-22c-verification.md` (round c, base
> commit `46c168a`, the decoupled gold-value row). Every review pass gets
> its own new file under `docs/review/` — check STATUS.md's "current
> review-round files" note (top of file) for whichever round is actually
> current when you're reading this.
>
> **Base commit:** `174f680` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §3 below, after the
> `quarterly_last()` fix)
> **Written:** 2026-07-22T07:55:00Z UTC

**What prompted this round:** the user noticed "Reserves incl. gold
(market)" reading 5.1% — higher than recent months, despite gold's price
having fallen — and reasoned correctly that a ratio can't rise on a
falling numerator unless the denominator's basis changed. Asked for a
month-by-month table (gold price, gold $ value, GDP $ with units/vintage,
resulting %) across the last several runs, specifically to check whether
GDP's units or vintage were consistent.

## 1. GDP's own basis: checked directly, found consistent

Added a permanent diagnostic to `fetch.py`'s `verify()` printing GDP's and
`TRESEGUSM052N`'s raw FRED values, units, and vintages directly (this
project had never printed GDP's raw dollar figure anywhere before — only
its %-of-GDP derivatives). Live CI output:
```
GDP units (from FRED metadata): 'Billions of Dollars'
  2025-04-01: 30485.729 (Billions of Dollars) -> $30.486T
  2025-07-01: 31098.027 (Billions of Dollars) -> $31.098T
  2025-10-01: 31422.526 (Billions of Dollars) -> $31.423T
  2026-01-01: 31865.721 (Billions of Dollars) -> $31.866T
```
Same units string, same `S.to_dollars()` conversion, every quarter. GDP's
own basis was NOT the bug — but the user's underlying instinct (something
had an inconsistent basis) turned out to be correct anyway, just pointing
at the wrong series.

**Claim status: VERIFIED** — read directly from live CI, not assumed.

## 2. The actual bug: quarter-bucketing, not GDP

`reserves_incl_gold_pct_gdp()` (`scripts/series.py`) collapsed a monthly
dict into quarters via:
```python
for (y, m), v in combined_m.items():
    res_q[(y, (m - 1) // 3 + 1)] = v
```
`combined_m` was built from `res_m.keys() & gold_value_usd_monthly.keys()`
— a set intersection, whose iteration order Python does not guarantee is
chronological. This assumption ("last one written wins, and it's the
latest month") only actually holds for a dict built directly from an
ascending observation list.

**Reproduced directly, outside any network call:**
```python
res_m = {(y, m): 1.0 for y in range(1950, 2027) for m in range(1, 13) if (y, m) <= (2026, 3)}
gold_m = {(y, m): 1.0 for y in range(1968, 2027) for m in range(1, 13) if (y, m) <= (2026, 7)}
combined_m = {k: res_m[k] + gold_m[k] for k in res_m.keys() & gold_m.keys()}
res_q = {}
for (y, m), v in combined_m.items():
    res_q[(y, (m - 1) // 3 + 1)] = (y, m)
# res_q[(2026, 1)] == (2026, 1)  <- January, not the intended March
```
Tested with three differently-sized gold-price dicts (LBMA-, World-Bank-,
and mirror-shaped date ranges) — all three produced the same wrong
answer, January, confirming the bug doesn't depend on which price source
is active.

A SECOND function had the identical pattern: `real_10y_rate()`, feeding
the shipped "Real 10-year rate (10y − CPI)" row. Found by grep for the
same anti-pattern (`for (y, m), v in ... .items(): ...[(y, (m-1)//3+1)] =
...`) across `series.py`, not by accident.

**Claim status: VERIFIED** — reproduced directly with realistic key sets;
no live network access needed to confirm the bug itself.

## 3. The fix, and live confirmation

Added `quarterly_last()`: explicitly compares month numbers, no
dependence on iteration order. Routed every quarter-bucketing call site
through it (`reserves_pct_gdp`, `reserves_incl_gold_pct_gdp`,
`real_10y_rate`, `debt_to_revenue_pct` — the last one was already safe via
an explicit `sorted()` upstream, routed through anyway for
defense-in-depth). Added a regression test reproducing the exact bug
shape and asserting the fix picks March for 2026-Q1.

**Before the fix** (run `29900861697`, buggy `series.py`, LBMA leg
active): the new diagnostic block (written correctly from the start, so
it never had this bug) printed `2026-Q1 (gold priced as of 2026-03):
... -> 4.539%`, while the row ACTUALLY SHIPPED that same run read `5.1%`
— the new diagnostic and the real shipped computation disagreed with each
other, live, in the same run. That disagreement is itself direct proof
the shipped function was wrong (a working diagnostic and a buggy
production function computing different answers from identical inputs).

**After the fix** (run `29901538886`, committed as `174f680`, this
round's base commit): both agree.
```
2025-Q2 (gold priced as of 2025-06): gold price $3,287.45/oz, gold value $859.7B, reserves+gold $1104.3B, GDP $30.486T -> 3.622%
2025-Q3 (gold priced as of 2025-09): gold price $3,825.30/oz, gold value $1000.3B, reserves+gold $1244.8B, GDP $31.098T -> 4.003%
2025-Q4 (gold priced as of 2025-12): gold price $4,367.80/oz, gold value $1142.2B, reserves+gold $1385.4B, GDP $31.423T -> 4.409%
2026-Q1 (gold priced as of 2026-03): gold price $4,608.35/oz, gold value $1205.1B, reserves+gold $1446.4B, GDP $31.866T -> 4.539%
```
The "priced as of" column now matches the quarter label in every row —
it did NOT before this fix (silently "2026-Q1" while pricing off
January).

Shipped `public/data.json` (`174f680`):
```json
{"key": "reserves_to_gdp", "display": "4.5%", "asOf": "2026-Q1", ...}
```
Matches the corrected breakdown exactly (4.539% rounds to 4.5%).

**Claim status: VERIFIED** — two live CI runs (before/after the fix), not
mocks; both the diagnostic output and the actual shipped `data.json` read
directly.

## 4. Local verification

New regression test in the scratchpad mock-test suite, using the same
realistic differently-sized-dict shape that triggered the bug:
```
quarterly_last() regression: correctly picked the true latest month (March) for 2026-Q1
```
Full existing suite (every prior round's assertions) still passes
unchanged — this fix only changes WHICH month gets selected, not the
shape of any row's output, so no other assertion was affected.

## 5. What this round did not chase further

`real_10y_rate`'s specific before/after values were not tabulated (the
user's question was about reserves specifically) — only confirmed the row
recomputes without error and now carries `asOf: "2026-Q2"`. A future round
revisiting the "Real 10-year rate" row's own history should treat any
prior committed value as unverified against this bug, the same way this
round treats every prior `reserves_incl_gold` figure.
