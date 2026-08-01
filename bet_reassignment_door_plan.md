# Reassign-bet-to-correct-account — build plan v3.1 (S254) — ✅ BUILT & SHIPPED

**Status: BUILT, VERIFIED, DEPLOYED — 26 Jul 2026 (S254).** Commits:
`b230eab` (A: standing defences + sweeps), `cf2c691` (B: composed-correction
module), `31d6c66` (C: reassign door + migration), plus a final-review
polish commit. `bet_reassigned` migration RUN on the live store 17:32
(backup `bethub-PRE-s254-reassign-migration-20260726-173221.db`).
Acceptance: the real Leigh/Tim incident replayed on the pre-fix backup
(straight + crash-resumed) matches the executed fix's money surfaces to
the cent, append-only. Final whole-system review (4 reviewers): money path
CONFIRMED SOUND; operability findings fixed same-day. Executive summary:
`reassign_build_executive_summary.md`. DO NOT re-commission this build.
Sections below are the as-built spec of record (◆ = review-mandated pins).

Original v3.1 status line, for the record: passed the focused adversarial
review (3 reviewers, all SOUND_WITH_ISSUES; pins applied, marked ◆);
reviewer confidence ~85–90%. Review record §8. Operator decisions §7.

## 1. What the review rounds established (load-bearing facts)
1. The re-credit step needs a NEW sibling correction verb — the credit-in
   door's locked once-per-qualifier guard counts revoked credits by
   contract and stays byte-untouched (operator: no exceptions).
2. Kate/Leigh 18 Jul is CLOSED — double-draw, corrected 19 Jul; the
   mandatory pre-flight (§3b) exists because v2's wrong prescription for it
   would have silently double-funded a $50 bet with $100 of face.
3. The existing S236 move arm (`PATCH /v1/bets/{id}`) has a crude
   substring closure guard (since 9 Jul) but an empty-diff audit, no CAS,
   and a **live Betfair-target hole** (refuses Betfair as source only;
   `bets.py:1023` vs `:1032-1070`) — reachable today; §4a patches it ahead
   of everything.
4. Mid-composition crash states need a durable journal; writer idempotency
   results are ambiguous and `already_credited` provably returns the wrong
   credit on resume.
5. Both real incidents were promo-spine shapes — the composed-correction
   module (B) is the real fixer; the endpoint (C) serves the future clean
   bet-move shape.
6. Deploy re-sourcing is achievable APPEND-ONLY (restore + re-deploy) —
   proven by the serviceability sim reproducing the executed Leigh/Tim fix
   to the cent. No in-place promo_events UPDATE anywhere in this build.

## 2. Deliverables and sittings (◆ realistic estimate: 3–5 sittings total)
**A. Pre-door fixes — FIRST SITTING, own deploy (~1 sitting).** §4. The
Betfair-target hole is reachable today; A is standalone-safe (verified).
**B. Composed-correction module (~1.5–2 sittings).** §3.
**C. Reassign endpoint + migration + BetLog door (~1.5–2 sittings).** §5.

## 3. B — the composed-correction module

**◆3.0 The composition itself (was underspecified).** v1 handles the
FB wrong-account shape (both real incidents). Canonical step sequence:
`pre-flight → journal → [restore + revoke, atomic] → correction-credit →
bets-account move → re-fund deploy(s)`.
- Bets-account move comes BEFORE the re-fund deploy (the deploy guard
  checks the bet's CURRENT account — wrong order fails every resume).
- The §3b live-face-vs-stake computation RE-RUNS inside the deploy step's
  transaction (a deploy landing between pre-flight and final step must be
  caught at commit time).
- The correction-credit→deploy window is an ACCEPTED, journal-visible
  transient (credit live on the correct account; a concurrent spend makes
  the composition's deploy fail loud; sweep (e) catches an unfunded bet).
- Bet-move audit while C is unbuilt: `bet_edited` + from/to triplet in
  notes (the executed-fix pattern); no backfill when C ships.
- Consumed-deploy re-sourcing = restore + re-deploy (append-only, §1.6).
- Invocation surface v1: guided operator runner
  (`uv run python -m ops.correct_promo_chain <bet> <target>`), journal-
  backed, confirm-prompted, app up. A UI surface is a follow-on if
  frequency justifies it (self-serve priority noted; the common clean-move
  case is what C's button serves).

**3a. New writer: correction-context credit (sibling verb; the credit-in
door and its locked contract stay byte-untouched). ◆Four binding pins:**
1. The correction credit is a **NEW ROOT event** — `supersedes_event_id`
   NULL, never a superseder of the revoke terminal (the fb_restore-literal
   shape silently vanishes face value cross-account: the inventory walk is
   account-scoped and skips supersession-carrying roots). Lineage = the
   REPLACED credit's event_id in the existing payload `reference` field +
   notes; `credit_source` stays `triggered`. Zero walker/schema/payload-
   model changes — hand-traced clean through the inventory walk both same-
   and cross-account.
2. Stamps `correlation_id` = **qualifier uuid** (as both credit-in writers
   do) — NOT fb_restore's deploy-correlation behaviour, which makes the
   credit invisible to every future guard read (production fixtures
   774a6af1/001b3c92 are the regression anchors).
3. Guard runs under **BEGIN IMMEDIATE taken before its reads** (reuse the
   `_lock_guard_window` pattern) — closes the concurrent double-correction
   race that the root shape's index exemption would otherwise allow.
4. Guard checks **EVERY credit for the qualifier** (triggering_bet_id scan
   across credit events, not correlation-lookup-only): refuse if none
   exist (credit-in's job); allow ONLY if every chain terminates
   `free_bet_revoked`. Invariant preserved: at most one live credit per
   qualifier, ever. **v1 scope: FB chains only**; cash-chain corrections
   (terminal = rejected cash credit) are a named follow-on.

**3b. Mandatory pre-flight** (before any composition AND re-asserted
inside the deploy step): all deploys naming the bet split live/superseded;
refuse if the composition would leave live drawn face > bet stake.

**◆3c. Durable composition journal — concrete spec.** New table via
`store/schema/composition_journal.py`, `CREATE TABLE IF NOT EXISTS`
(additive — no CHECK-rebuild trap): composition_id PK, bet_id, from/to
triplets, planned_steps JSON with **PRE-GENERATED event_ids**, per-step
completed_at, status IN (planned/in_progress/done/abandoned), reason,
created_at. Each step's journal UPDATE happens **inside that step's own
BEGIN IMMEDIATE** (same DB file — no committed-step/stale-journal window);
resume trusts the journal absolutely ("did step N land" = PK lookup on the
pre-generated id, never a writer's idempotency answer). `abandoned` is an
operator terminal with mandatory reason. ◆Sweep (f): non-terminal journal
rows older than a threshold surface in the daily money check.
A `settlement_state` re-check runs inside every step; change aborts to
operator review.

**3d. Atomicity.** Restore+revoke adjacent and atomic: one connection,
◆`PRAGMA foreign_keys=ON` BEFORE `BEGIN IMMEDIATE` (SQLite no-ops the
pragma inside a txn), both events built via domain models and serialized
through the module-level `_event_to_row` (verified payload-generic for
restore + revoke shapes), raw-inserted, one commit — the executed fix's
production-tested pattern. Transient composition states are covered by
sweeps ◆(c) and (e) plus the journal.

**3e. Runbook (post-commit anomaly, app up):** FREEZE the module (do NOT
restore a file backup — organic writes since the anomaly would be lost) →
CAPTURE (journal step ids, sweep rows, balances/inventory/orphans) →
COMPENSATE append-only (restore/revoke the new events; inverse bet move
from the audit trail) → RE-VERIFY → UNFREEZE. File restore = app-down last
resort with the write-loss window named.

## 4. A — pre-door fixes (first sitting, own deploy; all standalone-safe)
a. **Existing S236 door: refuse Betfair as TARGET book** (pure new 422 on
   a confirmed hole; source-side refusal already exists).
b. **`list_source_pending_spends` ignores superseded deploys** —
   ◆with a VOID exemption: bets `settlement_state='voided'` (or deploys
   superseded by a void-reason restore) are excluded, else legitimately
   voided FB bets false-positive (proven on `bet-a5f3cfb2`; pinned by
   test).
c. **Standing sweeps in the daily money check** (daily + post-door):
   (a) deploy-vs-bet account, superseded-aware; (b) chain-account
   coherence; (c) credit-vs-triggering-bet account, chain-terminal-aware;
   (d) `book_or_exchange == lower(books.name)`; (e) superseded-aware
   orphan sweep with the same void exemption as 4b; ◆(f) stale journal
   rows (once B exists). ◆Golden values for (b)/(c)/(e) pre-computed on
   the audit copy BEFORE writing the sweeps (red-before); (a) naive=1/
   aware=0 and (d) 0/290 already verified.

## 5. C — endpoint + migration + door (clean same-book bet-move shape)
- `POST /v1/bets/{bet_id}/reassign-account` {target_account_at_book_id,
  expected_from_account_at_book_id, ◆expected_settlement_state, reason}.
  CAS on the from-triplet ◆AND settlement_state (else the confirmed P&L
  delta can be stale), asserted in-txn; 409 on mismatch. ◆Target ==
  current → 409 with clear message, no write (one behaviour, not two).
  Explicit busy_timeout + retry-or-503. Same-book only (cross-book =
  future item behind the stamp policy). ◆Betfair-lane refusal restated in
  this door (same-book Betfair→Betfair move refused: an exchange bet is a
  placed order).
- Eligibility closure: superseded-aware, over chain + payload bet refs;
  ◆computed on the txn connection post-BEGIN (not before). Pinned by a
  test on the real `bet-3b84ec36` row. Refusals name blocking ids.
  Multi-credit deploys refused.
- Audit: `bet_reassigned` row raw-INSERTed inside the same BEGIN
  IMMEDIATE as the bets UPDATE, payload via domain model +
  `_event_to_row` (verified generic for new payload types once
  registered); never the adapter on the txn connection. ◆Every raw-insert
  connection: `PRAGMA foreign_keys=ON` before BEGIN. Migration-not-run
  fails closed (CHECK rolls the txn back).
- Migration prerequisites: DDL CHECK rebuild (precedent transfers; keep
  column order — `INSERT INTO … SELECT *`; distinct rename target); domain
  enum + `BetReassignedPayload` in the union + `_FK_REQUIRED_BY_EVENT_TYPE`
  + ◆`PAYLOAD_BY_EVENT_TYPE` (write path never consults it — reads would
  500 while writes succeed; the round-trip test must READ BACK through the
  adapter) + the `_new_audit_event` union annotation; explicit app-down
  one-shot `apply_migrations` run verified against `sqlite_master` +
  row-count + `integrity_check`; daily-check assertion that the live
  schema names `bet_reassigned`.
- `GET /v1/bets/{bet_id}/reassign-preview`: closure (superseded-flagged),
  verdict, blocking ids, per-account P&L delta.
- Single path: strip the account/book move from the PATCH edit surface.
- Delta-asserts: full-content violation tuples on the txn connection.
- UI: replaces the S236 dropdowns in the BetLog edit expander; invalidates
  BetLog + Balances + promo lists.

## 6. Tests (red-before; ◆fixtures pinned)
◆Fixtures: pre-fix shape = the chmod-444 backup
`~/.bethub/backups/bethub-PRE-leightim-EXEC-20260726-110903.db`; current
shape = the S254 audit copy; golden allowed-case for the correction verb =
the real revoke-terminal chain `98c79d35 → 23cfae56`; guard-blindness
regressions = restore credits `774a6af1`/`001b3c92`; void exemption =
`bet-a5f3cfb2`.
Full list: migration round-trip + not-run-fails-closed + schema-drift;
same-book moves unsettled + settled; CAS mismatch (account AND settlement)
409; target==current 409; double-submit; A→B racing A→C; SQLITE_BUSY;
closure rules pinned on both real bets (NOTE, corrected at build: the
original "3b84ec36 ALLOWED" pin was written under the orphan
misdiagnosis — the bet is LIVE-FUNDED, so the correct verdict is
REFUSED naming exactly its live deploy `6202dcc6`, routing to the
composed tool; the shape that must stay MOVABLE is a
superseded-deploy-with-live-continuation, pinned synthetically);
pre-fix Leigh/Tim shape REFUSED; re-credit-guard fail-loud; ◆concurrent double-correction
(two threads, one qualifier — exactly one live credit survives);
◆commit-then-crash resume (verb committed, journal not — resume refuses
loudly); pre-flight refuses live-face>stake; phantom spend mid-composition
fails the deploy loud; crash at every journal boundary + journal-keyed
resume; settlement-void racing a composition; sweeps (a)–(f) goldens;
◆readers-ignore-superseded-deploys with the reader set enumerated
(`list_source_pending_spends` asserted; inventory/journey walkers exempt
by design — chain-based, not deploy-scan); preview round-trip;
`bet_reassigned` READ-BACK through the adapter.

## 7. Operator decisions — ALL RESOLVED (S254)
1. No locked-rule exceptions — sibling correction verb (§3a), normal door
   untouched. 2. Same-book-only v1 CONFIRMED. 3. Freebie credits out of
   app-up scope (goodwill-credit door, worklist 0j rider, is the home).
4. Settled bets movable CONFIRMED (risks reviewed: retro balance shifts,
   post-distribution basis — accepted with the P&L confirm +
   reversibility). Standing: self-serve in-tool corrections are the
   workflow priority; settled-bet DETAIL edits (e.g. stake) are a separate
   worklist item, not this build.

## 8. Review record
v1 in-place UPDATE → retired (premise refuted; refused both real
incidents). v2 composition-via-existing-writers → retired (re-credit
unbuildable; Kate/Leigh premise false; closure supersession-blind; phantom
window; no journal; S236 bypass + live Betfair-target hole; serviceability
sim: correct-to-the-cent WITH guard bypass, and v2's Kate/Leigh
prescription double-funds). v3 → final focused review (3 agents): all
SOUND_WITH_ISSUES; pins applied in this v3.1 (◆): root-shape correction
credit + correlation stamp + guard lock + all-chains guard; §3.0 step
sequence + invocation + B-audit answer; journal DDL/lifecycle/staleness;
void exemptions; PAYLOAD_BY_EVENT_TYPE + read-back test; closure/CAS
in-txn; foreign_keys-before-BEGIN; settlement CAS; Betfair same-book
refusal; fixtures + goldens; realistic 3–5 sitting estimate with A first.
Reviewer confidence: ~85–90% rigorous-permanent-fix, conditional on these
pins — now applied.
