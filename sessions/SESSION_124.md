# Session 124 — Pre-W14 coordinated governance update; eight architecture.md + decisions.md edits landed cleanly; DR-027 amendment write timed out under Desktop Commander; close-out deferred to S125

**Opened:** 2026-05-12 06:02 ACST (estimated)
**Closed:** 2026-05-12 ~07:02 ACST (estimated; Desktop
Commander timeout — no clean close timestamp captured)
**Wall-clock:** ~60m elapsed (estimated). Same-workday
open relative to S123 close (05:47 ACST same day, ~15m
gap). S124 ended ungracefully under a Desktop Commander
timeout during the ninth (DR-027 amendment) edit_block
call; close-out ritual did not run.

**This is a retroactive record written at S126
(2026-05-12, three hours after S125 close).** S124
itself did not write a session record because the
session ended under DC timeout. Substrate for this
reconstruction: the S125 opening prompt's narrative
beats (operator-drafted from S124 session memory at the
S124→S125 transition), `sessions/SESSION_125.md` (S125's
own record describing what it found landed from S124),
the eight S124 edits visible on disk in `architecture.md`
+ `decisions.md` (re-read at S125 open and at this
retroactive write), the S126 opening prompt's Phase 3
specification of header text + key narrative beats. No
attempt has been made to reconstruct conversational
ordering or intermediate phrasings — the record captures
what S124 delivered, what didn't land, and what carried
forward, at the same brevity as the rest of the session
journal.

**Tool routing:** Claude Chat. All filesystem operations
via Desktop Commander. Eight edit_block calls landed
across architecture.md + decisions.md before the ninth
(DR-027 amendment) triggered the timeout. No Code
dispatch this session.

**Governing DRs invoked:** DR-021 (Adelaide local time
anchoring). DR-019 (derived state on read — Session 124
amendment written this session, line 470). DR-022
(account / book / account-at-book vocabulary — context
for §A.3 schema). DR-026 (market-context snapshot —
Session 124 amendment written this session, line 794).
DR-027 (two-database architecture / bet-data internal
shape — Session 124 amendment attempted, timed out
mid-write; subsequently landed at S125). DR-030 (v3 repo
layout / module-boundary discipline — Session 124
amendment queued, did not start; subsequently landed at
S125). DR-032 (canonical-reference-layer / two-table bet
record — context for §A.2 spine change). DR-029 (data
layer fit-for-purpose review; closed Session 78) —
referenced for cross-references in the amendment text.

---

## Anchor

**Open:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
→ `2026-05-12 06:02 ACST` (estimated; operator-confirmed
at S125 open as same-workday continuation of S123 close).

**Close:** no clean close timestamp captured. The
Desktop Commander timeout during the DR-027 amendment
edit_block left the session in an ungraceful state; no
close-ritual `date` re-anchor was run. The ~07:02 ACST
close timestamp is estimated from the S125 open anchor
(2026-05-12 07:02 ACST) which the operator opened
shortly after the S124 session became unresponsive.

Same-workday session relative to S123 close. No day-
rollover. No pause-and-resume.

## Pre-flight checks

Drift-check at open held clean per the S124 prompt's
expectations. `current_state.md` last-updated 2026-05-12
05:47 ACST matched S123 close. `sessions/SESSION_123.md`
present (1075 lines). `decisions.md` `grep` returned
zero `Amendment 2026-05-12` hits (expected — S124's
amendments were the first to carry that date stamp).
Rebuild folder root clean: 11 expected `.md` files +
`v3_build_picture.md` (12th); expected directories
(`agent_review/`, `diagrams/`, `dr029/`,
`orchestration_pack/`, `sessions/`, `skills/`,
`.close_out_backups/`).

Required reads completed in order at S124 open per Cat 2:
`current_state.md`, `standing_instructions.md` (full),
`project_context.md`, `sessions/SESSION_123.md`. Plus
session-specific reads named in the S124 prompt for the
eight-finding scope (the relevant DR-019, DR-026,
DR-027, DR-030 anchors plus the architecture.md sections
in scope).

Pre-flight directory listing executed; no phantom files
surfaced.

## Session shape

Single-arc session with hard stop on the ninth edit.

**Phase 1 — Open.** Pre-flight clean. Same-workday recap
delivered tight per Cat 1 (S123 closed locking the
eight-finding scope for pre-W14 governance update; S124
picked up the coordinated amendment pass). Required
reads completed. Cat 3 empirical-verification pass on
each DR's current locked text plus the architecture.md
sections in scope (§A.2, §A.3, §A.6, §A.7, §A.9, §C.1)
before any edit fired.

**Phase 2 — Architecture.md edits (six sections).** Six
`Desktop Commander:edit_block` calls in sequence, one
per section. Each followed by inline verify-read per
Cat 3.

1. **§A.2 — mutable bets row + three per-domain event
   log tables.** The spine change. Replaced the original
   unified-event-log framing (one events table carrying
   `bet_placed` / `bet_correction` / `bet_settled` /
   cascade events / FB credit and deployment events /
   etc.) with the shipped reality: bets stored as a row
   with mutable columns, plus three per-domain event
   tables — `cash_flow_events` (W14 ships), `promo_events`
   (W13 ships), `ops_events` (W15 ships). The §A.2 body
   now opens with the "Why per-domain rather than a
   single event log" framing. Closes Findings #1 and #2
   from S123 pre-W14 review.

2. **§A.3 — bets row + bet_legs row schema, Finding #15
   fields expanded.** Schema documentation expanded to
   the full Finding #15 field inventory: `cycle_id`,
   `entry_path`, `strategy_tag`, `price_source`,
   `betfair_bet_id`, `match_status` (MatchStatus enum
   including `PROVISIONAL_PENDING`), `settlement_state`
   (SettlementState enum including `PROVISIONAL`),
   `dead_heat_count`, `removed_runner_count`,
   `unexpected_state_count`, `last_read_market_state`,
   `last_reconciled_at`, `reconciliation_attempts`, plus
   retry timings. Section header updated to reflect the
   schema-not-event-placement framing. A stale duplicate
   §A.3 header was removed during this edit. Closes
   Finding #15.

3. **§A.6 — settlement on mutable bets row, hedge state
   deferred per Finding #8.** Settlement state framing
   moved from "event-log-driven settlement" to
   "settlement transitions write to the mutable
   `settlement_state` column on the bets row, written by
   the auto-settlement worker (W6.5)." Per-bet
   `cash_returned` framed as computed on read, not stored
   as a column. Hedge classification fields deferred per
   Finding #8 (DR-025 hedge revisit flagged for pre-W15
   brief drafting). Closes Findings #4 and #7.

4. **§A.7 — cascades reframed.** Cascade chain
   triggering reframed to fire on bets-row state change
   (mutable column transitions) rather than on event-log
   append. Pattern preserved; substrate changed.

5. **§A.9 — stored-facts list + derivation table.**
   Stored-facts inventory updated to reflect the mutable
   bets row + per-domain event tables spine. Derivation
   table updated to show which facts are stored vs
   computed-on-read under the new spine. Crucially, the
   Location 1 balance formula in §A.9 was written
   correctly here at S124; the contradictory §A.5
   formula was not caught (became propagation Finding F3
   at S125, closed at S126).

6. **§C.1 — new Burst Review section.** New section
   documenting the W8 shipped Burst Review surface
   (operator-facing reconciliation queue, classification
   discipline, the operator's quality-control loop for
   bets the auto-settlement path flagged as
   `PROVISIONAL`). Closes Finding #16.

**Phase 3 — Decisions.md amendments (two of four
intended).**

7. **DR-019 Session 124 amendment** (line 470, written
   via single edit_block). Refines the "derived state on
   read" principle: still load-bearing for aggregates
   (balances, turnover totals, FB inventory, cash flow
   summary views, operation net flow) and cross-entity
   derivations (hygiene status, outcome-vs-warning
   analysis), but per-entity mutable state (per-bet
   lifecycle fields per §A.3) is stored as mutable
   columns on the entity row rather than computed by
   event-chain replay. Documents the acceptable
   tradeoff: personal-operation scale, no external audit
   obligation, reliability rests on worker correctness
   + Betfair settlement truthfulness + operator catches
   via Burst Review. Closes Finding #5.

8. **DR-026 Session 124 amendment** (line 794, written
   via single edit_block). Bounds the at-log-time
   market-context snapshot scope to the fields already
   defined in DR-026 plus the Session 11 amendment (best
   back / lay prices + sizes, total matched, snapshot
   timestamp, stale flag, `bf_snapshot_unavailable`,
   `bf_snapshot_aligned_to_placement`,
   `late_scratch_between_snapshot_and_log`). Explicit
   lock: no additional market-context snapshot fields
   added to the bets row. Closes Finding #3.

**Phase 4 — DR-027 amendment attempt (DC timeout).**
Ninth `edit_block` call attempted against decisions.md
at what would have become line 836 (after the DR-019 +
DR-026 amendments). The amendment text was substantial
(~50 lines: header through reliability list through
"does NOT change" cross-references). Mid-write, Desktop
Commander hung — approximately 4 minutes of no response
per the S125 prompt's reconstruction — before the
session became unresponsive enough that the operator
opened a fresh S125 chat to recover.

**Post-timeout verification (at S125 open, not at
S124):** `grep -n "Amendment 2026-05-12" decisions.md`
returned exactly two hits — DR-019 line 470, DR-026
line 794 — confirming no partial DR-027 amendment
landed. Either the edit_block call had not yet begun
writing to disk when the timeout occurred, or it had
completed but the tool-result return path hung. Either
way, decisions.md was in a clean post-DR-026-amendment
state, not partially corrupted.

**Phase 5 — Ungraceful close.** Close-out ritual did
not execute. No SESSION_124.md written. No
`current_state.md` rotation. No `v3_build_picture.md`
timestamp bump or stream-status update. No S125
opening prompt generation. The operator drafted the
S125 opening prompt manually from S124 session memory,
scoping the remaining items (DR-027 amendment, DR-030
amendment, contract relocation, verify-every-write
pass, close-out paperwork) for S125 to pick up.

## Structural drift surfaced this session

**Coordinated eight-item update could not complete in
one session under DC operating constraints.** The S124
prompt's plan assumed all eight items would land in
sequence. The DR-027 amendment edit_block (~50 lines
including verbatim `old_string` + `new_string`) pushed
Desktop Commander past its stable operating envelope
for single-shot writes. The threshold is empirical: the
six architecture.md edits (which were not trivially
small) landed cleanly; the DR-019 amendment (smaller
than DR-027) landed; the DR-026 amendment (smaller
again) landed; DR-027 at ~50 lines did not. The S125
recovery split DR-027 into two ~25-line edit_blocks and
both landed cleanly. The empirical threshold sits
somewhere between ~30 lines and ~50 lines per single
edit_block call.

**Carry-forward implications captured:**

- **S125 carry-out trigger** wrote in the proactive
  split-DR-027-into-two-chunks guidance, which executed
  cleanly.
- **S126 close** is queuing a candidate standing
  instruction at Cat 3 — pre-execution advisory for
  tasks that may exceed tool / context limits, surfaced
  by the operator this session.

**Other structural drift (not visible at S124,
discovered retroactively at S125 integrity check):**
the spine change at §A.2 propagated drift into
architecture.md §A.0 (reading-order line), §A.4 (promo
+ credit chains), §A.5 (cash flow Location 1 formula —
contradicted the §A.9 derivation), §B.1.4 (sports
auto-settlement vocabulary), §B.1.5 (sports bet record
shape and reference to nonexistent bet event log),
decisions.md DR-023 body, v3_data_requirements.md
auto-settlement paragraph. These were not in S124's
scope and would not have been catchable in S124's
forward pass (the propagation drift is only visible
after the spine change lands; before it lands, the
references still point at coherent if outdated
framing). S125's comprehensive integrity check surfaced
the full ~8-spot propagation drift; S126 closed it
mechanically.

## What was delivered

**Eight items landed on disk at S124 close** (all
verified at S125 open via re-read):

Architecture.md (six sections):

1. **§A.2** — mutable bets row + per-domain event log
   tables spine.
2. **§A.3** — bets row + bet_legs row schema with
   Finding #15 fields enumerated; stale duplicate
   header removed.
3. **§A.6** — settlement on mutable bets row; hedge
   state deferred.
4. **§A.7** — cascades reframed to fire on bets-row
   state change.
5. **§A.9** — stored-facts list + derivation table
   updated under the new spine. Location 1 balance
   formula written correctly here (the contradicting
   §A.5 formula was the S125-discovered F3
   propagation, closed at S126).
6. **§C.1** — new Burst Review section (W8 shipped
   surface documentation).

Decisions.md (two of four intended amendments):

7. **DR-019 Session 124 amendment** at line 470 —
   refining derived-state-on-read for per-entity
   mutable state.
8. **DR-026 Session 124 amendment** at line 794 —
   bounding at-log-time market-context snapshot scope.

**What did NOT land at S124:**

- DR-027 Session 124 amendment (timed out mid-write;
  landed at S125 line 836 via two-chunk split).
- DR-030 Session 124 amendment (queued, did not start;
  landed at S125 line 1071).
- Contract file relocation (`vps_client_contract.md`
  and `betfair_client_contract.md` from
  `dr029/2_7_api_contract_versioning/` to
  `bethub-v3/contracts/`) — queued, did not run;
  completed at S125.
- Verify-every-write pass across all S124 edits — did
  not run; completed at S125 open.
- Close-out paperwork (SESSION_124.md, current_state.md
  rotation, v3_build_picture.md timestamp bump, S125
  opening prompt generation) — did not run.
  SESSION_124.md retroactive at S126 (this file);
  current_state.md rotated at S125 close;
  v3_build_picture.md updated at S125 close; S125
  opening prompt drafted manually by operator.

**What surfaced retroactively at S125** (caused by
S124's spine change but not in S124's scope, not
catchable in S124's forward pass):

- F1: architecture.md §A.0 reading-order line referenced
  the pre-S124 section descriptions.
- F2: architecture.md §A.4 promo and credit chains
  referenced `bet_placed.payload.*` and `bet_settled.*`
  fields (no such events under the new spine).
- F3: architecture.md §A.5 Location 1 balance formula
  referenced `bet_placed.cash_stake_amount` and
  `bet_settled.cash_returned_to_book` — directly
  contradicted §A.9's correct derivation.
- F4: architecture.md §B.1.4 sports auto-settlement
  decision logic used the old three-state
  `finalised` / `voided` / `provisional` vocabulary
  rather than the four shipped enums.
- F5: architecture.md §B.1.5 incorrectly listed
  settlement state in the "What's not stored on the bet
  record" paragraph.
- F6: architecture.md §B.1.5 referenced "the bet event
  log" with `bet_logged` / `bet_settled` / `bet_voided`
  event types — none exist under the new spine.
- F7: decisions.md DR-023 body line 635 — stale
  "computed on read from the event log."
- F8: v3_data_requirements.md line 74 — auto-settlement
  paragraph used `bet_settled` event framing + old
  vocabulary.
- C1 (cosmetic): decisions.md DR-030 §Scope text did
  not note relocation completion.

S125 surfaced these as the integrity-check output and
deferred resolution to S126; S126 closed them
mechanically.

## Standing-instruction adherence check

Retroactive assessment, limited because the session
ended under DC timeout. What's certain from the on-disk
evidence + the S125 prompt's reconstruction:

- **Cat 1 silent session-open ritual** — operator-
  confirmed clean at S124 open per the S125 prompt's
  open-ritual notes.
- **Cat 1 calendar-calibrated recap** — same-workday
  recap held at S124 open (S123 closed 15m earlier on
  the same calendar date).
- **Cat 1 drift-check** — held at S124 open.
- **Cat 2 timestamp anchor** — held (06:02 ACST).
- **Cat 2 required reads** — held at S124 open.
- **Cat 2 pre-flight directory listing** — held.
- **Cat 2 governing DRs named in orientation** — held
  (DR-019, DR-026, DR-027, DR-030 named in opening
  brief per the eight-finding scope).
- **Cat 3 empirical-verification-before-editing** —
  held throughout the eight landed edits. Verifiable
  post-hoc: re-reads at S125 open and at this S126
  retroactive write both confirm the eight edits
  reference the right anchors and cross-references.

- **Cat 3 `create_file` banned** — held (all writes via
  Desktop Commander edit_block).
- **Cat 3 verify-every-write** — partially held. Each
  individual edit had the standard edit_block inline
  verify (the tool's return surface shows the edited
  region post-write). The global verify-every-write
  pass at end-of-session did not execute due to the DC
  timeout; ran at S125 open instead.
- **Cat 3 REPL discipline** — N/A this session (no
  Python invocations).
- **Cat 3 dry-run multi-target mechanical edits** —
  N/A (each edit was single-target via edit_block with
  verbatim `old_string`).
- **Cat 4 DR-027 / DR-028 cross-database boundary
  discipline** — held. The DR-027 amendment text
  (attempted at S124, landed at S125) explicitly named
  what the amendment does NOT change, including the
  cross-DB boundary and DR-028's forbidden patterns.
- **Cat 5 software-questions-are-Claude's** — held
  throughout. No technical-shape calls punted to
  operator.

**Carry-out trigger fired:** DC timeout during DR-027
amendment edit_block. Standard recovery routing: S125
opens, drift-check confirms partial-state bounded
(eight-or-zero per edit_block transaction semantics; no
mid-edit corruption), remaining items rescoped for
S125. Played out as expected.

## Open items in / out

Pointer-only — full items live in
`sessions/SESSION_123.md` (S123 pre-W14 review triage)
and `sessions/SESSION_125.md` (S125 carry).

**Open items in (rolled forward from S123 close):**

All eight findings from S123 pre-W14 codebase review,
locked as S124's scope:

- Finding #1, #2 — DR-027 amendment needed for bet-data
  internal shape.
- Finding #3 — DR-026 amendment needed for snapshot
  scope.
- Finding #4, #7 — architecture.md §A.6 settlement
  framing + cascades.
- Finding #5 — DR-019 amendment needed.
- Finding #8 — hedge classification (parked for pre-W15
  brief drafting; not in-scope this session).
- Finding #12, #14 — DR-030 amendment needed for repo
  layout clarifications.
- Finding #13 — contract file relocation.
- Finding #15 — architecture.md §A.3 schema expansion.
- Finding #16 — architecture.md §C.1 Burst Review
  section.

**Closed in S124 (eight items):**

- Findings #4, #7 (architecture.md §A.6, §A.7).
- Finding #5 (DR-019 amendment).
- Finding #3 (DR-026 amendment).
- Finding #15 (architecture.md §A.3).
- Finding #16 (architecture.md §C.1).
- Plus the §A.2 spine change closing Findings #1/#2's
  architectural substrate (though the DR-027 amendment
  itself did not land — see below).
- Plus the §A.9 stored-facts list + derivation table
  update.

**Carried forward to S125 (as S125 prompt's scope):**

- DR-027 Session 124 amendment (closes Findings #1, #2
  at DR level — substrate landed at S124 §A.2, but the
  DR-027 amendment text itself did not). Closed at S125.
- DR-030 Session 124 amendment (closes Findings #12,
  #14). Closed at S125.
- Contract file relocation (closes Finding #13). Closed
  at S125.
- Verify-every-write pass on the eight S124 edits.
  Completed at S125 open.
- Close-out paperwork (SESSION_124.md retroactive +
  current_state.md rotation + v3_build_picture.md
  timestamp bump + S125 opening prompt). Close-out
  components landed across S125 close + this S126
  retroactive write.

**Discovered retroactively at S125 (propagation
findings F1–F8 + cosmetic C1):**

Eight downstream propagation findings caused by the
S124 spine change propagating into sections not in the
original eight-item scope, plus one cosmetic. All
mechanical reframing. Closed at S126. Detailed
enumeration in `sessions/SESSION_125.md` and
`sessions/SESSION_126.md` (when written).

**Carry-forward sensitivities (unchanged through S124):**

- Hedge classification (Finding #8 from S123) — parked
  for pre-W15 brief drafting.
- §2.4 Fix 4 cadence design dependency (Finding #3
  from S123) — independent sequencing.

## Session close state (ungraceful)

The session ended under Desktop Commander timeout
during the DR-027 amendment edit_block call. No
close-ritual steps executed. State at the point of
unresponsiveness:

- **rebuild folder root:** as at S123 close — 11
  expected `.md` files + `v3_build_picture.md` +
  expected directories. No new files written this
  session beyond the eight in-place edits.
- **`sessions/`:** SESSION_124.md absent (written
  retroactively at S126; this file).
- **`current_state.md`:** unchanged, last-updated
  timestamp still 2026-05-12 05:47 ACST (S123 close).
- **`v3_build_picture.md`:** unchanged, last-updated
  timestamp still S123 close.
- **`.close_out_backups/`:** `SESSION_124_opening_
  prompt.md` written at S123 close still present
  (this artefact carried forward as a stale backup
  through to S126 open, where it was swept).
- **`bethub-v3/contracts/`:** placeholder directory
  with empty `__init__.py`; relocation pending S125.
- **`dr029/2_7_api_contract_versioning/`:** contract
  files (`vps_client_contract.md`,
  `betfair_client_contract.md`) still present at
  pre-relocation paths.

**Decisions.md final state at S124 close:** two
`Amendment 2026-05-12` blocks landed (DR-019 line 470,
DR-026 line 794); DR-027 body unchanged at lines 800ish
through 830ish; no DR-027 or DR-030 amendment text on
disk.

**Architecture.md final state at S124 close:** all six
section edits landed. The stale §A.3 header duplicate
(carried forward from a pre-S124 edit run) was removed
during the §A.3 expansion edit.

## Forward routing

Recovery handled at S125 open via the operator-drafted
S125 opening prompt. S125 picked up:

1. DR-027 Session 124 amendment (split into two ~25-line
   edit_blocks per carry-out trigger).
2. DR-030 Session 124 amendment (single edit, with
   "relocation completed at S125" wording per the
   reorder-pick decision).
3. Contract file relocation (single `mv`).
4. Verify-every-write pass across all S124 + S125 work.

S125 also surfaced (via operator-pivoted integrity
check) the eight propagation findings + one cosmetic
not in S124's scope. S125 closed cleanly with
propagation tail deferred to S126.

S126 closed the propagation tail and wrote this
retroactive SESSION_124.md record.

**Pre-W14 governance update stream effective scope:**

- S123 lock: 8 items.
- S124 close: 8 items in flight; 8 landed (six
  architecture.md sections + DR-019 + DR-026
  amendments).
- S125 close: original 8-item scope closed end-to-end
  across S124 + S125; 8 propagation findings + 1
  cosmetic surfaced as effective scope expansion.
- S126 close: stream `done`; 17 effective items closed
  end-to-end across S124 + S125 + S126.

**This retroactive record is itself a deliverable of
the stream's closing arc** — without it the eight-item
S124 work would be unattributed (current_state.md and
v3_build_picture.md reference S124 work as substrate,
but no session record described the work in S124's own
voice). The retroactive write closes that paperwork
gap.

---

**Record honesty:** this is a reconstruction, not a
contemporaneous record. The on-disk evidence is firm
(eight edits are visible and verifiable); the
conversational substrate (operator instructions during
the session, intermediate phrasings, mid-session
decisions) is not preserved and is not reconstructed
here. The forward-routing decisions captured above are
the ones inferable from the S125 prompt's substrate and
the S125 session record.
