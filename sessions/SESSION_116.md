# Session 116 — Vision re-anchor against ship state; refinement verdict landed; re-cut sequenced W10–W18

**Opened:** 2026-05-11 12:38 ACST
**Closed:** 2026-05-11 13:39 ACST
**Wall-clock:** ~1h active session work. New-workday open relative to Session 115 close (Sunday 19:22 → Monday 12:38; ~17h overnight gap). Same-workday close.
**Tool routing:** Claude Chat exclusively. Substrate reads via Desktop Commander. No Code dispatch. No artefact commits — out of scope per Session 115's forward routing.
**Governing DRs invoked:** DR-021 (Adelaide local time — open and close anchors). DR-027, DR-028 (cross-DB boundary discipline — context only). DR-030 (v3 repo layout) — context for the operational-store missing scope. DR-022 (book/account/account-at-book vocabulary) — context for the re-cut sub-streams.

---

## Anchor

**Open:** `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-11 12:38 ACST`.
**Close:** same command → `2026-05-11 13:39 ACST`.

New-workday open relative to Session 115 close. No pause-and-resume.

## Pre-flight checks

Drift-check at open: clean. `current_state.md` last-updated 2026-05-10 19:22 ACST matched Session 115 close. `sessions/SESSION_115.md` present. `v3_build_picture.md` last-updated 2026-05-07 (Session 100) — unchanged correctly (stale labels deliberately held off until post-vision re-cut commits).

`.close_out_backups/` held only `SESSION_116_opening_prompt.md` (this session's opener; consumed at open).

Open ritual produced step-narration in operator-facing output (third consecutive session — Sessions 114 + 115 + 116). Self-flagged at top of session as continuing evidence the existing Cat 1 silent-ritual wording isn't suppressing the pattern. Reinforces the Session 115 sweep candidate.

## Session shape

Strategic re-anchor session via operator-led top-level view, mapped against `vision.md` and current ship state.

**Phase 1 — Operator's top-level view.** Operator opened by providing a refreshed draft of BetHub's top-level operational and strategic view. Document covered: what BetHub is (operational hub for multi-persona promo extraction); the operation it serves; non-negotiables; the constellation (BetHub core; RouteHub planned; AccountCare and Analytics following; edge-generators and scraper VPS further out); test of scope ("if every satellite disappeared, could you still run the operation from BetHub alone?").

**Phase 2 — Vision vs ship state mapping.** Reviewed the new draft against original `vision.md` (35 lines) and current shipped workstreams. Verdict: vision held, refinement not rabbit hole. The new draft sharpens the gap-map and adds three new things — constellation framing; test of scope; five named non-negotiables. Two subtler shifts surfaced as yes/no calls: decision-support framing dropped (Job 3 "Surface decisions in real time" removed); binding-constraint statement gone (5×5=25min framing).

**Phase 3 — Operator calls on the two yes/nos.**

- **Q1 (recommends vs surfaces):** locked as surfaces, not recommends. Three pieces inside — keep v2's true-EV + promotional-EV display on racing pages; add Betfair price-movement indicators on selections (racing first; sports later if feasible); promo-scheduler at `~/Desktop/Projects/promo-scheduler/` stays standalone, not v3 scope.
- **Q2 (binding-constraint statement):** locked as included, with sharper why. Time-overhead framing (5×5=25min) updated to fingerprint-contamination risk from manual-switching errors — the AdsPower / Wi-Fi / desktop-browser slip-ups operator has experienced or near-experienced.

**Phase 4 — Ship state verification surfaced bigger gap.** Verified via `Desktop Commander:list_directory` that v3's web layer today has only two routes: `Health` (system status) and `Provisional` (the W8 burst-review queue UI). No racing pages, no sports pages, no market views, no EV display. All racing-betting UI lives only on v2. The Session 115 re-cut draft (W10–W16) built the data layer but not the operator-facing pages — cutover in W16 was technically impossible as drafted.

**Phase 5 — Re-cut sequenced.** Updated the re-cut to W10–W18:

- **W10** storage lift to top-level `store/` (DR-030 fix; unblocks everything).
- **W11–W15** operational-store sub-streams (accounts/account-at-book per DR-022, balances, promos, transactions, ops log).
- **W17** racing market pages (port v2's true-EV + promotional-EV display; add Betfair price-movement indicators; redesign where new features need to land, retain v2 structure where it works).
- **W16** cutover from v2 (sequenced *after* W17, not before).
- **W18** sports market pages (parked).

**Phase 6 — Verdict landed.** Operator's Session 115 close-out question — refinement or rabbit hole? — answered: **refinement, with one governance lesson.** The W3–W9 shipped work was correct (built the Betfair-truth pillar — bet entry, reconciliation, settlement). What was missed was the operator-facing surface and the book-at-account operational store. Both gaps now visible and the drafted re-cut covers them. The governance lesson is the W6 label drift propagating thirteen sessions before being caught — rabbit hole in the *bookkeeping*, not the build direction. The Cat 2 close-out rule added Session 115 is the fix.

## What was delivered

1. **Vision held — verdict landed.** The Session 115 refinement-vs-rabbit-hole question answered: refinement. Build direction was right; governance bookkeeping was the rabbit hole, and the Session 115 Cat 2 rule fixes recurrence.

2. **Two operator calls locked on vision refinements.** Q1: BetHub surfaces inputs, doesn't recommend (with three specific pieces inside). Q2: include the binding-constraint statement, updated to fingerprint-contamination framing. Both will land in `vision.md` next session.

3. **Operational gap surfaced and addressed in the re-cut.** v3's web layer has only Health and Provisional routes today; no racing or sports pages, no EV display, no Betfair indicators. Identified as a missing workstream beyond the operational store, added to the re-cut as W17 (racing pages) and W18 (sports pages, parked). W16 (cutover) re-sequenced to land *after* W17, since cutover requires racing pages to be usable.

4. **Re-cut sequenced W10–W18 with explicit ordering.** W10 storage lift first → W11–W15 operational-store sub-streams → W17 racing market pages → W16 cutover → W18 sports market pages. Not committed to `v3_build_picture.md` this session (out of scope per Session 115 forward routing); waits on Session 117.

5. **Operator's updated top-level view document received.** Provided in chat at session open as the strategic anchor. Not yet committed to any artefact; intent is to land it in `vision.md` next session alongside the refinements above.

6. **Promo-scheduler classified.** Folder confirmed at `~/Desktop/Projects/promo-scheduler/` with proper standalone structure (brief_parser, race_fetcher, schedule_builder, html_renderer). Stays standalone — not in v3 scope at this stage; not added to the constellation as a satellite.

## Standing-instruction adherence check

- **Cat 1 silent session-open ritual** — *violated*. Step-headers ("Step 1 — Timestamp anchor (DR-021)", "Step 2 — Required reads in order") appeared in operator-facing text. Third consecutive session (114, 115, 116). Self-flagged at session open. Reinforces existing sweep candidate that wording-only enforcement is insufficient.
- **Cat 1 V3 build picture conditional render at open** — held (skip-silent; no stream movement since Session 100, by intent).
- **Cat 1 open-items delta — conditional** — held. Surfaced concisely at open: closed/new/none-overdue split.
- **Cat 1 plain-language operational framing** — held. Vision-vs-ship-state walked in plain operator language; pillars framed as "Betfair-truth" and "book-at-account-truth"; gap-map presented as ASCII table; verdict framed as "refinement, with one governance lesson."
- **Cat 1 tighten default response register further** — held. Most responses small-to-medium. One slightly longer triage response (mapping vision to ship state) but content was inventory-shaped and necessary; opt-in implicit via operator's "Can you please review this with reference to our original vision document."
- **Cat 1 escalate to detail only when warranted** — held. Explicitly flagged "this deserves it" before the longer vision-vs-ship-state response.
- **Cat 1 call-driven surfacing during section-by-section drafting** — N/A this session (no artefact drafting).
- **Cat 1 inventory-first cadence on long technical reports** — held. The vision-vs-ship-state mapping walked as inventory (held/new/dropped framing; gap-map table).
- **Cat 1 don't drift to alternatives when operator has been clear** — held. Operator was clear on the session's strategic shape (top-level view → match to vision); no drift to alternative work shapes.
- **Cat 1 unwind internal shorthand** — held. DR-030 unwrapped as "the v3 repo layout decision"; DR-022 as "book/account/account-at-book vocabulary"; W6/W7/W8 as their as-shipped meanings; W10–W18 with plain-language descriptors at every mention.
- **Cat 1 render review content with hard line wraps** — N/A (no fenced review blocks this session).
- **Cat 2 timestamp anchor** — open 12:38 ACST and close 13:39 ACST both anchored via `Desktop Commander:start_process`.
- **Cat 2 Desktop Commander default** — held throughout. All filesystem reads via Desktop Commander.
- **Cat 2 re-validate queued work-items at execution time** — held. The Session 115 queued item ("read vision in full, walk through with current ship state") re-validated mid-session against operator's revised framing ("top-level operational and strategic view first, then match back to vision"); proceeded with operator's framing rather than forcing the queued order.
- **Cat 2 workstream-label / build-picture coherence at session close (new from Session 115)** — held. No new workstream labels were *committed* to `v3_build_picture.md` this session (the re-cut proposal named W10–W18 but the picture wasn't updated; the proposal stays in chat history and current_state.md until Session 117 commits it). The existing labels mentioned (W3 through W9) were used in their as-shipped meanings. Skip-silent on the picture itself; surfacing on current_state.md.
- **Cat 3 empirical verification before editing governance artefacts** — N/A (no governance artefact edits this session).
- **Cat 3 `create_file` ban; verify every write** — held. No file writes this session except those at close-out.
- **Cat 5 software calls don't punt** — held. The W17 sequencing call (racing pages before cutover, not after) was Claude's call; the W10–W18 ordering was Claude's call; the "port v2 structure, redesign where new features land" UI approach was Claude's call. All framed as software calls with brief justification, not as operator-facing yes/no.
- **Cat 5 cosmetic calls default to Claude's pick** — N/A this session.

## Open items in (carry-forward)

Pointer-only — full list lives in `current_state.md` "Open items" section after rotation.

**New from Session 116 (PRIMARY for Session 117):**

- **Commit re-cut to `v3_build_picture.md`** — W10 storage lift; W11–W15 operational-store sub-streams (accounts/account-at-book per DR-022, balances, promos, transactions, ops log); W17 racing market pages; W16 cutover (re-sequenced to after W17); W18 sports market pages (parked). Includes W4.1 status reconciliation per Session 115 draft.
- **Update `vision.md`** with refinements: (a) replace original Job 3 "Surface decisions in real time" framing — BetHub surfaces inputs, operator decides; (b) add Betfair price-movement indicators as a named feature for racing pages; (c) keep binding-constraint statement but reframe from time-overhead (5×5=25min) to fingerprint-contamination risk from manual-switching errors; (d) integrate operator's updated top-level view content (constellation framing; non-negotiables; test of scope) where it strengthens the existing vision shape. Promo-scheduler does not enter `vision.md` — remains standalone, not in constellation.

**Carried forward (pending operator action):**

- **Operator action (PRIMARY this carry):** re-upload `standing_instructions.md` to the bethub-rebuild Claude Project knowledge base. Same item carried from Session 115 (Cat 2 rule on workstream-label / build-picture coherence; file at 154 lines, hash `6da08bfff747`). No new edits this session.

**Carried forward (sweep candidates, lower priority):**

- **Cat 1 silent session-open ritual wording insufficient.** Sessions 114, 115, 116 all produced step-narration in operator-facing text despite the Session 114 tightening. Wording-only enforcement isn't holding. Likely needs structural/skill-side intervention (move silent-ritual responsibility from instruction wording into a checklist inside `bethub-session-open` skill itself, or similar). Held for next dedicated sweep.
- **Cat 2 / Cat 3 `str_replace` reflex extends the `create_file` failure mode pattern.** Held for next dedicated sweep.

**Carried forward (optional / parking-lot):**

- **(Optional)** review W3 + W4 + W6 + W6.1 + W6.5 + W7 + W8 + W9 Code-shipped state.
- **(Optional)** run a real `get_account_funds()` Betfair call at low risk.
- **(Lower priority, parking-lot)** Betfair API membership tier investigation — awaiting BetWatch response.

**Carry-forward operational (Sessions 108 / 109 carry):**

- Settings-area cadence follow-up brief — open; waits on operational experience.
- Greyhound operational constraint verification — open.
- `betfair_adapter.py` single-file mypy cleanup — low priority.

## Open items out (closed Session 116)

- **`vision.md` re-read against current ship state** — closed end-to-end. Operator's two yes/no calls locked. Refinement-vs-rabbit-hole verdict landed (refinement with governance lesson). Vision update itself sits in Session 117 (commit work).
- **Refinement-vs-rabbit-hole question from Session 115** — closed. Verdict: refinement, with the W6 label drift as the governance lesson the Session 115 Cat 2 rule already addresses.

## Session close state

- **Rebuild folder root:** structurally unchanged. No governance file edits this session.
- **`current_state.md`:** rotated at this close. "Last updated" → 2026-05-11 13:39 ACST.
- **`sessions/SESSION_116.md`:** written (this file).
- **`v3_build_picture.md`:** untouched. Re-cut commit deferred to Session 117 per Session 115 forward routing.
- **`vision.md`:** untouched. Refinements committed Session 117.
- **`.close_out_backups/`:** `SESSION_116_opening_prompt.md` deleted (consumed at session 116 open). `SESSION_117_opening_prompt.md` written.
- **Project knowledge base:** `standing_instructions.md` re-upload still pending (Session 115 Cat 2 edit). All other canonical docs current.

## Forward routing

**Confirmed with operator: close session here. Session 117 opens on operator's schedule with two artefact commits as primary deliverables.**

Session 117 primary work:

1. **Commit re-cut to `v3_build_picture.md`** — W10 storage lift; W11–W15 operational-store sub-streams; W17 racing market pages; W16 cutover (re-sequenced to after W17); W18 sports market pages (parked). W4.1 status reconciliation included.

2. **Update `vision.md`** — incorporate operator's updated top-level view content (constellation framing, non-negotiables, test of scope) plus the two locked refinements (BetHub surfaces inputs operator decides; binding-constraint reframed to fingerprint-contamination risk). Add Betfair price-movement indicators as named feature for racing pages.

**Out of scope for Session 117 (unless commits land fast):**

- New standing-instruction work (Session 115 + 116 sweep candidates wait for a dedicated sweep).
- Brief drafting for W10 / W11–W15 / W17.
- Code dispatch.

**Possible Session 117 shapes:**

- **Two clean commits.** `v3_build_picture.md` and `vision.md` both land; session closes with both artefacts updated and the Session 117 close-out then sets up Session 118 to start drafting W10 (storage lift brief).
- **Vision drafting expands into a longer conversation.** Operator's updated top-level view document is rich enough that integrating it into `vision.md` may surface further refinements or trade-offs. If the conversation widens, the build-picture commit may slip to Session 118.
- **One commit + carry.** `v3_build_picture.md` lands (smaller surface; mechanical from this session's sequencing), `vision.md` carries to Session 118 for fuller treatment.

---

## Close-out notes (added post-close 2026-05-11)

**Recovery from partial-state close-out failure.** Session 116 close missed the Cat 2 "Persist drafted-but-not-assembled artefact content to scratch" rule. The operator's refreshed top-level view document — provided in Session 116 chat as the strategic anchor for the `vision.md` update queued for Session 117 — was summarised in this record (Phase 1; What was delivered §5) but the document text itself was not persisted to disk.

Session 117 opened against `current_state.md` + `SESSION_116.md` + `vision.md` (original 35 lines) and surfaced the gap immediately on starting the vision-update commit: needed the source document text to integrate accurately, found only a summary. Operator queried in the Session 116 chat window whether the refinements had been captured.

**Recovery direction:** complete forward (the operator's source document was available from Session 116 chat history; persisting it to disk as a scratch file is mechanical and unblocks Session 117 cleanly).

**Recovery executed:** source document text written to `sessions/SESSION_116_source_docs.md` (post-close 2026-05-11). This close-out note appended to this session record. `current_state.md` left unmodified to avoid cross-chat drift while Session 117 is in flight. Session 117 chat already has the source text via operator's paste; the on-disk persistence is governance trail rather than active unblocker.

**Lesson:** Cat 2 "Persist drafted-but-not-assembled artefact content to scratch" applies to *any* session that locks-in-chat operator-provided source material as the anchor for downstream work — not only dr029 brief-drafting sessions. The Session 116 close-out pre-close checklist did not catch this because the rule is phrased around drafted artefact content; operator-provided source documents are an adjacent case. Worth a sweep candidate to broaden the rule wording, or alternatively to expand the pre-close checklist with an explicit "any source documents pasted into chat this session" item. Held for next dedicated sweep.
