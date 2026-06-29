# Session 117 — V3 build picture re-cut committed; vision.md refreshed end-to-end

**Opened:** 2026-05-11 13:49 ACST
**Closed:** 2026-05-11 14:47 ACST
**Wall-clock:** ~58m active. Same-workday open relative to Session 116 close (13:39 → 13:49; ~10m gap). No pause-and-resume.
**Tool routing:** Claude Chat exclusively. Substrate reads + artefact writes via Desktop Commander. No Code dispatch. Two artefact rewrites (`v3_build_picture.md`, `vision.md`).
**Governing DRs invoked:** DR-021 (Adelaide local time — open and close anchors). DR-030 (v3 repo layout) — load-bearing for W10 storage lift framing. DR-022 (book/account/account-at-book vocabulary) — load-bearing for W11–W15 sub-stream wording. DR-027/028 (cross-DB boundary discipline) — context for the operational-store band. DR-032 (canonical-reference-layer for all bet records) — context for W13 promos cycle linkage.

---

## Anchor

**Open:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-11 13:49 ACST`.
**Close:** same command → `2026-05-11 14:47 ACST`.

Same-workday open relative to Session 116 close (~10m gap). No pause-and-resume.

## Pre-flight checks

Drift-check at open: clean. `current_state.md` last-updated 2026-05-11 13:39 ACST matched Session 116 close. `sessions/SESSION_116.md` present. `v3_build_picture.md` last-updated 2026-05-07 (Session 100) — correctly unchanged at open (Session 116 deliberately deferred picture commit to Session 117).

`.close_out_backups/` held only `SESSION_117_opening_prompt.md` (this session's opener; consumed at open).

Open ritual produced step-narration in operator-facing output (fourth consecutive session — 114 / 115 / 116 / 117). Self-flagged at open. Reinforces the standing sweep candidate that wording-only enforcement of the silent-ritual rule is insufficient and likely needs structural/skill-side intervention.

**Carry-over from operator opening message:** standing_instructions.md re-upload to bethub-rebuild Claude Project knowledge base confirmed — closes the PRIMARY carried operator action across Sessions 115 + 116.

**Mid-session anomaly surfaced and resolved:** during the vision.md update phase, surfaced that the operator's refreshed top-level view document (provided in Session 116 chat as anchor for the Session 117 vision update) was not persisted to disk at Session 116 close. Cat 2 "Persist drafted-but-not-assembled artefact content to scratch" gap — the rule wording covered drafted artefact content but did not cover operator-provided source documents as an adjacent case. Operator returned to Session 116 chat; Session 116's Claude executed recovery (wrote source to `sessions/SESSION_116_source_docs.md`, appended close-out notes to `SESSION_116.md`, flagged a new sweep candidate to broaden the rule). Session 117 then read the source from disk and proceeded with the vision integration.

## Session shape

Two-artefact-commit session with a mid-session pause to remediate a Session 116 close-out gap.

**Phase 1 — Picture re-cut commit (Session 116 sequencing direct to artefact).** Read Session 115 record on demand for W4.1 reconciliation context. Empirically verified W4.1 ship status (`SOFT_BOOK` BetKind, `OPERATOR_TYPED` price source, `log_soft_book_bet` API all present in `bet_entry/v1/`). Inventoried changes — one structural call surfaced (shipped Sessions 100–116 streams: drop from picture per one-session-carry rule, or carry a "Shipped" band). Operator delegated explicitly to Claude's recommendation; recommendation was drop. Proposed new stream table; operator confirmed shape. Wrote full picture rewrite, verified post-write.

**Phase 2 — Source-doc gap caught and remediated.** Vision.md update needed operator's refreshed top-level view text. Surfaced that document lived only in Session 116 chat. Operator returned to Session 116 chat; Session 116's Claude executed Cat 2 persist-to-scratch recovery — wrote source to `sessions/SESSION_116_source_docs.md` (181 lines including header), appended close-out note to `SESSION_116.md` flagging a sweep candidate to broaden the persist-to-scratch rule. Recovery direction was "complete forward" (source was available from chat history; persisting it on-disk was mechanical and unblocked Session 117 cleanly). Session 117 read from disk.

**Phase 3 — Vision.md refresh commit.** Read source document from disk. Proposed 9-section structure integrating operator's refreshed view + the two locked refinements (Q1 surfaces-not-recommends + Betfair price-movement indicators; Q2 binding-constraint reframed to fingerprint-contamination risk) + operationally-important specifics preserved from original 35-line `vision.md` (Betfair UI supplement; humans browse system plans; Constraints section). Drafted from scratch one new section (`## The binding constraint`) on the Q2 framing — names manual switching as the binding constraint, frames cost as a risk class growing with operational volume (not time-overhead), positions RouteHub as the satellite that removes the risk class entirely. Wrote full vision.md rewrite, verified post-write. Surfaced the binding-constraint section to operator for review. Operator confirmed framing landed.

## What was delivered

1. **`v3_build_picture.md` re-cut committed.** Forward-only stream table replacing the Session-100 cut: W10 storage lift → W11–W15 operational-store sub-streams (accounts/account-at-book per DR-022, balances, promos, transactions, ops log) → W17 racing market pages → W16 cutover (re-sequenced after W17) → W18 sports market pages (parked) + P1 / P2 (parked, unchanged from Session 100). Sessions 100–116 shipped scope dropped from the picture per the one-session-carry rule: W3 contract work, W4 BetfairAdapter, W4.1 soft-book typed-price entry path, W6 as-shipped broader-sync match-state reconciliation, W6.1 sub-stream, W6.5 settlement-state reconciliation, W7 as-shipped web layer skeleton, W8 as-shipped burst-review queue UI, W9 settlement-side worker — full shipped history lives in session records. Top-matter parenthetical names the Session 115 W6 label-drift framing. Operator-redline notes refreshed with new redline candidates (W11–W15 collapse-vs-expand; W17 dependency narrowing; W16/W17 numbering oddity). Stream model preamble updated from "Eight workstreams" to "Nine workstreams" with the new band content. "Last updated" stamp at substantive-work time (14:21 ACST) bumped to close timestamp (14:47 ACST) per close-skill Step 6.

2. **`vision.md` refreshed end-to-end.** Original 35 lines → new 97 lines. Sections in order: What BetHub is / The operation BetHub serves / Why BetHub exists / What BetHub does (with new bullet for racing market pages with true-EV + promotional-EV display + Betfair price-movement indicators; closing paragraph adding surfaces-not-recommends framing per Q1) / Non-negotiables / **The binding constraint (new section, Q2 fingerprint-contamination framing, positions RouteHub as risk-class-removal not time-saver)** / The constellation (with operator's note that satellite sections are placeholders, expanded as each tool becomes the active build) / What BetHub is not (with two preserved current-vision specifics — Betfair UI supplement, humans browse system plans — plus Q1's explicit "not a real-time trade-suggestion engine") / The test of scope / Constraints (preserved from current vision — single operator, v2 stays running, operator cannot read/write code, operator-tax-to-near-zero success metric). Promo-scheduler held to standalone per Session 116 Q1 lock — not in constellation, not in vision.

3. **Session 116 Cat 2 close-out gap caught and recovered post-session.** The operator's refreshed top-level view document — provided in Session 116 chat as anchor for the Session 117 vision update — was not persisted to disk at Session 116 close. Cat 2 "Persist drafted-but-not-assembled artefact content to scratch" was scoped around drafted artefact content; operator-provided source documents pasted in chat as anchor for downstream work are an adjacent case not covered by the existing wording. Recovery executed in Session 116 chat: source document persisted to `sessions/SESSION_116_source_docs.md` (181 lines), close-out notes appended to `SESSION_116.md` explaining the recovery and flagging a sweep candidate to broaden the rule. Recovery direction was "complete forward." Sweep candidate joins this session's close-out queue.

4. **Operator action carry closed.** Standing_instructions.md re-upload to bethub-rebuild Claude Project knowledge base — confirmed at session open. Closes the PRIMARY carried operator action that had been outstanding across Sessions 115 + 116 (the file with the Cat 2 workstream-label / build-picture coherence rule added Session 115 is now reflected in the project KB).

## Structural-drift surfacing

**`v3_build_picture.md` structural change this session:** full streams table replacement. Old table held W4.1 / W5 / W6 / W7 / W8 / P1 / P2 (Session 100 cut). New table holds W10 / W11 / W12 / W13 / W14 / W15 / W16 / W17 / W18 / P1 / P2. Not a renumber-style drift (W10–W18 are fresh labels per Session 116's re-cut, not renames of existing W-numbers). The shipped Sessions 100–116 scope dropped from the picture entirely per the one-session-carry rule. Structural change is intentional and reflects Session 115's W6 label-drift discovery + Session 116's vision re-anchor verdict. Carried into Session 118 opening prompt for visibility.

**`vision.md` structural change this session:** 35 lines → 97 lines, full rewrite. Section structure changed: original was {What this is for / Four jobs / Priority among the four / What this system is NOT / Constraints}; new is {What BetHub is / The operation BetHub serves / Why BetHub exists / What BetHub does / Non-negotiables / The binding constraint / The constellation / What BetHub is not / The test of scope / Constraints}. The "Four jobs" enumerated framing dissolved into the new "What BetHub does" + "Non-negotiables" sections; Job 3 ("Surface decisions in real time") explicitly dropped per Q1. Carried into Session 118 opening prompt.

## Standing-instruction adherence check

- **Cat 1 silent session-open ritual** — *violated*. Step-headers ("Step 1 — Timestamp anchor", "Step 2 — Required reads") appeared in operator-facing text at session 117 open. Fourth consecutive session (114 / 115 / 116 / 117). Self-flagged at open. Reinforces existing sweep candidate.
- **Cat 1 V3 build picture conditional render at open** — held (skip-silent; no stream movement Session 116, per intent).
- **Cat 1 open-items delta — conditional** — held. Surfaced concisely with closed/new/resolved-this-open split.
- **Cat 1 plain-language operational framing** — held throughout. Binding-constraint section written in operator-facing language (manual switching, fingerprint contamination, AdsPower / MiFi / desktop browser slip-ups). DR numbers cited with bracketed plain-language reminders.
- **Cat 1 tighten default response register further** — held. Pre-write inventories were tight (single round per artefact). Post-write surfacing was concise.
- **Cat 1 escalate to detail only when warranted** — held. No explicit "this deserves detail" flags needed; operator was in flow and reviewed surfaces directly.
- **Cat 1 call-driven surfacing during section-by-section drafting** — held. Both artefacts surfaced their structural shape pre-write as a single inventory round + post-write review note. Per Cat 1 "propose structure, start writing, bring it for review" — not section-by-section walkthrough because the operator-relevant calls were structural (whole-artefact level), not per-section.
- **Cat 1 inventory-first cadence on long technical reports** — N/A this session (no long technical reports triaged).
- **Cat 1 don't drift to alternatives when operator has been clear** — held. Operator was clear on the two artefact commits; both landed without scope drift.
- **Cat 1 unwind internal shorthand** — held. DR-030 unwrapped as "v3 repo layout"; DR-022 as "book/account/account-at-book vocabulary"; DR-027/028 as "two-database boundary discipline"; DR-032 as "canonical-reference-layer for all bet records"; Q1/Q2 as "surfaces-not-recommends" / "binding-constraint reframe"; W-numbers with plain-language descriptors at every mention.
- **Cat 1 render review content with hard line wraps** — held. The binding-constraint excerpt surfaced for operator review (per operator's explicit request mid-session) was rendered with ~60-char wraps per Cat 1.
- **Cat 2 timestamp anchor** — open 13:49 ACST and close 14:47 ACST both anchored via `Desktop Commander:start_process`. Re-anchored at 14:21 ACST for the `v3_build_picture.md` "Last updated" stamp during substantive work.
- **Cat 2 Desktop Commander default** — held throughout. All reads + writes via Desktop Commander. No `str_replace` reflex caught this session; sweep candidate from S115/S116 carries unchanged.
- **Cat 2 re-validate queued work-items at execution time** — held. Both queued items (picture re-cut, vision update) re-validated mid-session against current artefact state. Picture re-cut required W4.1 ship-status empirical check that wasn't in the Session 116 queue — re-validation surfaced the need and resolved it. Vision update surfaced the missing source document — re-validation triggered the Cat 2 gap discovery + recovery.
- **Cat 2 workstream-label / build-picture coherence at session close (Session 115 rule)** — held. The labels W10/W11/W12/W13/W14/W15/W16/W17/W18 committed to the picture this session match Session 116's re-cut text exactly. No mid-session label drift. Shipped Sessions 100–116 scope dropped from the picture rather than renamed.
- **Cat 2 persist-to-scratch (drafted-but-not-assembled artefact content)** — verified at close. No operator-provided source documents pasted this session. No drafted-but-not-assembled artefact content this session (both artefacts fully written to disk during substantive work). Rule does not fire this session. The Session 116 gap that prompted the in-session recovery is captured in `SESSION_116.md` close-out notes + the sweep candidate joining this session's queue.
- **Cat 2 structural-drift surfacing** — held. Both artefact structural changes (picture full streams-table replacement; vision section-shape rewrite) explicitly flagged in the session record's "Structural-drift surfacing" section and carried into Session 118 opening prompt.
- **Cat 3 empirical verification before editing governance artefacts** — held. `v3_build_picture.md` re-read in full at open (orientation read). `vision.md` re-read in full at open. Both edits drafted against the live file state, not against memory. Session 115 read on demand mid-session for W4.1 reconciliation context.
- **Cat 3 `create_file` ban; verify every write** — held. Both writes via `Desktop Commander:write_file`. Both verified post-write via `Desktop Commander:read_file`.
- **Cat 3 dry-run multi-target mechanical edits before write** — held implicitly. Both edits were full rewrites with pre-write inventory surfaced to operator. Dry-run-equivalent met.
- **Cat 5 software calls don't punt** — held. The "drop shipped streams from picture" structural call: surfaced with recommendation; operator delegated explicitly to Claude; Claude executed. The "should the binding constraint be a dedicated section" call: Claude's call, executed. The "W11–W15 as five sub-stream rows vs one bundle row" call: Claude's call (chose five sub-stream rows per Session 116 sub-stream language), executed.
- **Cat 5 cosmetic calls default to Claude's pick** — N/A this session.

## Open items in (carry-forward)

Pointer-only — full list lives in `current_state.md` "Open items" section after rotation.

**New from Session 117 (PRIMARY for Session 118):**

- **W10 storage lift brief drafting.** First brief of v3 build proper's operational-store band. Scope: lift bet-entry-workflow-local `storage.py` plus successive W6/W6.5/W9 schema extensions to top-level `store/` per DR-030 (v3 repo layout). Unblocks W11–W15. Brief drafted in Session 118; Code dispatch follows. Reference precedents: Session 101 W3 contract-work brief (most recent brief precedent); Session 84 W2 brief drafting (call-driven surfacing cadence reference); locked briefs in `dr029/`.

**Carried forward (pending operator action):**

- **Operator action (NEW PRIMARY this carry):** re-upload `vision.md` to the bethub-rebuild Claude Project knowledge base. `vision.md` lives in the Project KB per `project_context.md` §6 ("slow-changing canonical truth"); the Session 117 refresh (35 lines → 97 lines) means the KB version is now stale relative to disk. Pattern matches Session 115's standing_instructions.md re-upload carry-forward.

**Carried forward (sweep candidates, lower priority):**

- **Cat 1 silent session-open ritual wording insufficient (carried from S114/S115/S116, +S117 data point).** Four consecutive sessions with step-narration in operator-facing text despite Session-114-tightened wording. Pattern: wording-only enforcement isn't holding. Structural/skill-side intervention likely needed (move silent-ritual responsibility from instruction wording into a checklist inside `bethub-session-open` skill itself, or similar). Held for next dedicated sweep.
- **Cat 2 / Cat 3 `str_replace` reflex extends `create_file` failure mode pattern (carried from S115/S116).** No new instances this session. Held for sweep.
- **Cat 2 broaden persist-to-scratch rule to cover operator-provided source documents (NEW from Session 116 recovery).** Current Cat 2 rule wording covers "drafted-but-not-assembled artefact content"; operator-provided source documents pasted in chat as anchor for downstream work are an adjacent case. Two possible wording shapes: (a) extend the existing rule to cover both classes; (b) add a separate explicit pre-close checklist item for "any source documents pasted into chat this session." Held for next dedicated sweep.

**Carried forward (optional / parking-lot):**

- **(Optional)** review W3 + W4 + W4.1 + W6 + W6.1 + W6.5 + W7 + W8 + W9 Code-shipped state. Shipped scope dropped from picture; full state inspection remains optional.
- **(Optional)** run a real `get_account_funds()` Betfair call at low risk.
- **(Lower priority, parking-lot)** Betfair API membership tier investigation — awaiting BetWatch response.

**Carry-forward operational (Sessions 108 / 109 carry):**

- Settings-area cadence follow-up brief — open; waits on operational experience.
- Greyhound operational constraint verification — open.
- `betfair_adapter.py` single-file mypy cleanup — low priority.

## Open items out (closed Session 117)

- **Commit re-cut to `v3_build_picture.md`** — closed end-to-end. Full streams table replaced with Session 116's W10/W11–W15/W17/W16/W18 sequence + P1/P2 parked. Shipped Sessions 100–116 scope dropped.
- **Update `vision.md`** — closed end-to-end. Refreshed top-level view integrated with Q1 + Q2 refinements + Betfair indicators + operationally-important specifics preserved.
- **Operator action: re-upload `standing_instructions.md` to bethub-rebuild Claude Project knowledge base** — closed (confirmed at session open).

## Session close state

- **Rebuild folder root:** structurally unchanged. `v3_build_picture.md` substantively rewritten this session; `vision.md` substantively rewritten this session. Other governance files untouched.
- **`current_state.md`:** rotated at this close. "Last updated" → 2026-05-11 14:47 ACST.
- **`sessions/SESSION_117.md`:** written (this file).
- **`sessions/SESSION_116.md`:** unchanged this session (the post-close close-out notes appended during Session 117's mid-session recovery were written from the Session 116 chat, not by Session 117).
- **`sessions/SESSION_116_source_docs.md`:** unchanged this session (created by Session 116's post-close recovery; read here at Phase 3).
- **`v3_build_picture.md`:** rewritten at 14:21 ACST during substantive work; "Last updated" stamp bumped to 14:47 ACST at this close per close-skill Step 6.
- **`vision.md`:** rewritten during substantive work (97 lines).
- **`standing_instructions.md`:** untouched this session.
- **`.close_out_backups/`:** `SESSION_117_opening_prompt.md` deleted (consumed at session 117 open). `SESSION_118_opening_prompt.md` written.
- **Project knowledge base:** `vision.md` re-upload pending (Session 117 refresh). `standing_instructions.md` is current (re-uploaded at session 117 open). All other canonical docs current.

## Forward routing

**Confirmed with operator: close session here. Session 118 opens on operator's schedule to start drafting the W10 storage lift brief.**

Session 118 primary work: **draft the W10 storage lift brief.** Scope: lift bet-entry-workflow-local `storage.py` plus successive W6/W6.5/W9 schema extensions to top-level `store/` per DR-030 (v3 repo layout). Unblocks W11–W15. Brief drafted in Session 118 via call-driven section-by-section surfacing; Code dispatch staged for between-session execution after lock.

Reference precedents for brief drafting:

- Session 101 W3 contract-work brief — most recent precedent.
- Session 84 W2 brief drafting — call-driven surfacing cadence reference.
- Locked briefs in `dr029/` — pattern precedents from earlier arcs.

**Out of scope for Session 118 (unless brief drafting lands fast):**

- W11–W15 brief drafting (sub-streams depend on W10 storage lift completing first).
- W17 racing market pages brief drafting (downstream of W11–W15).
- New standing-instruction work (three accumulated sweep candidates wait for a dedicated sweep).
- Code dispatch for anything other than the W10 brief.

**Possible Session 118 shapes:**

- **Clean brief draft + Code dispatch staged.** W10 brief drafted section-by-section per call-driven surfacing; locked at session close; Code dispatch staged for between-session execution.
- **Brief drafting expands.** W10 brief surfaces material scope questions (e.g. schema migration handling for the lift, write-side coherence across the move, whether to lift schema columns as-is or rationalise during the lift). If material questions surface, Session 118 may close on a partial brief with the rest carried to Session 119.
- **Sweep session pivot.** If the three accumulated sweep candidates (Cat 1 silent ritual wording; Cat 2/Cat 3 `str_replace` reflex; Cat 2 persist-to-scratch broadening) feel pressing, Session 118 may pivot to a dedicated sweep before W10 brief drafting begins. Operator's call at Session 118 open.
