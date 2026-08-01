# SESSION 261 — Fri 31 Jul 2026 evening (informal)

Cross-reference record, created at S263 (1 Aug) so the chronological
session trail doesn't skip a number. S261 ran informally and filed its
records at the point of work rather than here.

## Stream 1 — promo-pilot built (for the Sat 1 Aug pilot day)

Standalone TAB promo-EV tool at `~/Desktop/Projects/promo-pilot`:
reads BetHub read-only (GETs on 127.0.0.1:8787, zero BetHub changes),
live page with a BET NOW strip at EV ≥ 8% for brief-assigned races.
EV engine is a 1:1 port of BetHub's own, parity-proven against the
actual TS engine. Full record: `promo-pilot/BUILD_NOTES.md`; operator
checklist `promo-pilot/RUNBOOK_SATURDAY.md`; memory
`bethub-promo-pilot-tool`.

Addendum, Sat 1 Aug morning (pre-racing): 3-reviewer adversarial
review — verdict: the EV arithmetic is exactly right; every real
defect is in the inputs it trusts or how BET NOW presents it. Operator
rules for the day issued. The TAB→EV path was live-proven 07:45
(14/14 early races full-field). Same morning, 08:02, the BET NOW
strip itself was REMOVED in code (backup
`page.py.bak-20260801-betnow-strip`) and replaced with a per-race hot
count that suppresses itself once the race jumps — fixing the
review's worst presentation defect ("BET NOW survives the jump");
that change went unrecorded until the S263 review found it. Recorded
in the same memory and in the BUILD_NOTES 1 Aug addendum.

## Stream 2 — Router/SIM gateway: Kate lane incident + safeguards

Kate's lane went down after her provider swapped her SIM (now
Vodafone, same carrier as Sarie — operator ruled the shared carrier
NOT a linkage risk; do not re-raise). Two contamination safeguards
built, tested and LIVE on the Pi; a live pull-the-router test proved a
dead router does NOT silently fall back onto another SIM lane. Full
detail: memory `router-sim-proxy-gateway` (S261 entries). The rigorous
remainder is worklist **0w** (scheduled Sun 2 Aug; alerting first —
the Pi currently has no way to email anyone).

## Session-open checks

All green this session. The S260 capture-resilience deploy was still
armed at close — it fired 04:27 ACST the next morning and passed every
check (verified S263; see `SESSION_260.md` postscript).
