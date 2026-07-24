# CLAUDE.md

Standing context for any Claude session working on this repo. `STATUS.md`
is the detailed, round-by-round log (read it too — this file is the
short, load-bearing rules that don't change often); this file is what
every session should inherit without having to re-derive it.

## What this project is

A live dashboard of Ray Dalio's sovereign debt-risk indicators (*How
Countries Go Broke*, Ch. 17): raw metrics fetched live from public
sources, merged with his frozen March-2025 Z-score model output from
`data/manual.json`, built into `public/data.json` by `scripts/fetch.py`,
rendered by a country-agnostic React app (`src/`). See `README.md` for
the architecture diagram and setup steps.

## Standing rules

1. **Never merge to `main` or open a PR without explicit user approval.**
   Develop on the assigned branch; push there only.

2. **The Z-score wall.** Dalio's Z-scores (`data/manual.json`'s
   `govGauge`/`cbGauge` `z` fields, and `headline`) are his proprietary,
   unpublished model output — **never recompute, approximate, or infer
   them**. Verify this holds after every round with an actual diff of
   `(label, z)` tuples against the pre-round file, not an assertion.

3. **Native sources are the default; DBnomics is a convenience cache.**
   (TASKnativesources.md, 2026-07-24 — see STATUS.md §33 for the full
   writeup.) Three incidents forced this: gold's PCPS mirror frozen,
   IMF COFER 568 days stale, and the euro-area series 380-480 days stale
   — in every case the actual upstream (Eurostat/ECB/IMF/FRED-equivalent)
   was fine and only the DBnomics mirror had rotted. Concretely:
   - Reach for a native SDMX/REST endpoint first (`scripts/sdmx.py` is
     the shared client for Eurostat/ECB; each source module tries native,
     falls back to DBnomics only if native genuinely doesn't resolve).
   - DBnomics is acceptable as a fallback ONLY with a freshness threshold
     no looser than one real publication cycle for that series — not a
     generously loose number "just in case." A frozen mirror that still
     returns a plausible-looking value is the exact failure mode this
     guards against; the threshold is the only thing standing between a
     frozen mirror and a silently wrong "live" tag.
   - When you can't confirm a native endpoint resolves (this dev sandbox
     can't reach most of these hosts directly — see below), two
     structured attempts, then document honestly and stop. Don't guess a
     third time; don't leave it unattempted either.

4. **This dev sandbox cannot reach most external data hosts directly**
   (FRED, Treasury Fiscal Data, CBO's GitHub mirror, DBnomics, Eurostat,
   ECB, IMF, gold sources — same asymmetry every time: GitHub Actions CI
   has full internet, this sandbox doesn't). The workflow that actually
   works:
   - Write the integration defensively — non-fatal, degrades to the next
     fallback (native → mirror → manual) rather than crashing the build.
   - Add real diagnostic output to the module's own `verify()` (dumps
     schema/response, not just success/failure).
   - Web research (`WebSearch`/`WebFetch`) to ground guesses in real,
     confirmed URLs/formats before writing code — cheaper than blind
     trial-and-error, and every source integrated this way in this repo
     started from at least one real confirmed example.
   - Push, trigger `workflow_dispatch`, read the actual job log
     (`mcp__github__get_job_logs` — save large logs to a file and slice
     with Python; the raw tool result is usually too big to read whole).
     This is the real test. Never write "confirmed" or "VERIFIED" in
     `STATUS.md`/`docs/review/` without having actually read that log.

5. **Provenance is load-bearing, not decoration.** Every shipped row
   carries a tag (`live` / `native` / `dbnomics_mirror` / `manual` /
   `projection` / `manual_price`) and, for anything derived, a `src`
   string naming the actual source — not a generic label that would be
   wrong once the underlying transport changes (this bit us once: COFER's
   `src` field said "IMF COFER (DBnomics)" unconditionally even after
   native-first sourcing was added — now it's built from the actual
   `source` the fetch returned). `fallbacksFired` in each country's
   `provenance` records every place a fallback fired this run, not just
   the ones that happened to get noticed.

6. **Bounded investigation, not open-ended guessing.** When a schema is
   genuinely unconfirmed after a couple of reasoned attempts (BIS's
   `WS_NA_SEC_DSS` dimension codes, ECB `RAS`'s exact SDMX key), stop,
   document exactly what was tried and what's still unknown, and ship the
   manual fallback. A future session with new information can pick it up
   — don't leave a vague TODO, and don't guess a tenth time hoping to get
   lucky.

7. **New `docs/review/<round>-{values,verification}.md` every round**,
   never edited in place (a reviewer's fetch tool caches by URL). Update
   `STATUS.md`'s top pointer block to the new round. Claims in both are
   marked VERIFIED (you ran it / read the log) or ASSUMED (inferred,
   not checked) — see `STATUS.md`'s "Meta" section for the full
   discipline.

8. **Before shipping anything uncertain**: local mock test with
   synthetic data covering the golden path AND the degrade-to-fallback
   path (a test that only exercises the happy path won't catch a
   fallback silently never firing), `npm run build` clean, and — for
   frontend changes — an actual Playwright screenshot, not just "the
   code looks right." Restore `public/data.json` to its committed state
   afterward if you swapped in synthetic data for a screenshot; check
   `git status --short public/data.json` is clean before moving on.
