# Moved — see `docs/review/`

This file used to be regenerated in place on every review pass. That broke
for reviewers whose fetch tool caches by URL and can't see edits to a path
it already fetched — a rewritten file at the same old path was invisible
to a repeat reviewer.

Starting 2026-07-19, every review round gets its own new file instead,
under `docs/review/`, named `YYYY-MM-DDx-verification.md` (and the
matching `YYYY-MM-DDx-values.md` for headline values), where `x` is a
letter disambiguating multiple rounds on the same date. Old rounds are
left in place, not overwritten.

**Current round:** `docs/review/2026-07-19c-verification.md` —
`docs/review/2026-07-19c-values.md`. Check STATUS.md's "current review
round" note (top of file) for whichever round is actually current when
you're reading this, since a newer one may exist since this stub was
written.

This file's own prior content (everything through the 2026-07-19 drift-test
round) is preserved in `git log -- docs/verification-log.md` and, verbatim,
in `docs/review/2026-07-19c-verification.md`.
