# Verification log, review round `2026-07-23c` — MSPD parsing closed

> **This file is frozen as of the round below and is not edited in place.**
> Prior round: `docs/review/2026-07-23b-verification.md` (round b, base
> commit `5d8826a`, government borrowing need live). Every review pass
> gets its own new file under `docs/review/` — check STATUS.md's
> "current review-round files" note (top of file) for whichever round is
> actually current when you're reading this.
>
> **Base commit:** `6613635` (HEAD of `claude/new-session-ldotj8` when this
> file was written — the `data: monthly refresh` commit produced by the
> live `update-data.yml` run documented in §1 below)
> **Written:** 2026-07-23T15:40:00Z UTC

**What this round covers:** `TASKmspdparsing.md` — a small, bounded
follow-up to round b. One hypothesis to test (aggregation-level
duplication: subtotal/total rows at multiple hierarchy levels
interleaved with detail rows, explaining the ~2.9x MSPD gap found in
round b). If it held, the two "— if rollover problems" stress rows would
unlock. **It did not hold.** No shipped row changed this round; the
outcome is a closed investigation, recorded honestly rather than a
forced fix.

## 1. The test, live

Live-tested via `workflow_dispatch` on commit `863286a`, committed as
`6613635`. Read directly from the CI job log, not assumed:

```
MSPD aggregation-level-duplication hypothesis test (TASKmspdparsing.md):
  record_date 2026-06-30: 888 rows total — 886 detail (real CUSIP) + 2 aggregate (null CUSIP)
  aggregate rows by security_class1_desc:
    'Federal Financing Bank': 1 row(s) — [{'security_class1_desc': 'Federal Financing Bank',
      'security_class2_desc': 'null', 'outstanding_amt': '3590.9655', 'issued_amt': '3590.9655'}]
    'Total Marketable': 1 row(s) — [{'security_class1_desc': 'Total Marketable',
      'security_class2_desc': 'null', 'outstanding_amt': '31085831.2471383', 'issued_amt': '31004212.4255'}]
  sum(outstanding_amt), DETAIL rows only: 90,375,417
  sum(outstanding_amt), ALL rows (detail + aggregate): 121,464,840
  'Total Marketable' row's own outstanding_amt: 31,085,831
  ratio, detail-only / Total Marketable: 2.9073 (success = ~1.00)
  ratio, all-rows / Total Marketable: 3.9074
```

**Classification-field dump (this round's acceptance criterion 1):**
splitting all 888 rows by whether `security_class2_desc` is a real
CUSIP-like string (detail) or `'null'` (aggregate) found only **2**
aggregate rows total — one "Federal Financing Bank" line (a distinct,
tiny $3.6B loan-facility total, not a per-class subtotal pattern) and
the one already-known grand "Total Marketable" row. There is no
per-security-class subtotal tier for the other ~6 classes (Bills, Notes,
Bonds, TIPS, FRNs) at all.

**Ratio before/after filtering**: before (round b, naive individual-rows
sum): ~2.9074x. After (this round, detail-only, excluding both aggregate
rows): **2.9073x** — statistically identical, not an improvement. The
hypothesis predicted this ratio would drop toward ~1.00; it didn't move
at all.

**Claim status: VERIFIED (disconfirmed)** — read directly from the CI
job log, not assumed or reconstructed from documentation.

## 2. Outcome: closed per the task's own instruction

TASKmspdparsing.md's own "If it doesn't [hold]" clause: *"Stop. Record
the eliminated hypothesis alongside the reopening one, keep both rows
manual, and note that MSPD parsing is closed after bounded
investigation. Do not open a new hypothesis."* Followed exactly:

- `data/manual.json`'s `borrowing_need_stress` and
  `borrowing_need_projected_stress` rows now cite both eliminated
  hypotheses (CUSIP reopening, round b; aggregation-level duplication,
  this round) inline.
- No third hypothesis was opened. The real cause of the ~2.9x gap
  remains genuinely unexplained — recorded as a closed, bounded
  investigation, not left as an open-ended puzzle.
- No shipped row changed. `borrowing_need`/`borrowing_need_projected`
  (round b) still ship live; the two stress rows were already manual
  and remain so.

**Claim status: VERIFIED** — read directly from the committed
`data/manual.json` and `public/data.json`.

## 3. Z-score wall: verified byte-identical

Same diff method as every prior round (`(label, z)` tuples, in order,
both gauges, against the pre-round-28 `data/manual.json`) — unchanged.
This round touched no `z` field at all (the only `data/manual.json`
edits were the two stress rows' `note` text).

**Claim status: VERIFIED.**

## 4. Local + browser verification

Local mock test suite re-run unchanged (no new assertions needed — this
round shipped no new live row, only a diagnostic function and two note
edits); all existing assertions still pass, including the borrowing-need
sanity-band test from round b. `npm run build` clean. No frontend change
this round (the two stress rows' displayed `note` text updates
automatically from `data/manual.json` through the existing `book`-schema
rendering — no `GaugeRow.jsx`/`equations.js` change needed).

## 5. Bundle size

Not applicable — no frontend files changed this round.
