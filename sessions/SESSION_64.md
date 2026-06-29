# Session 64

**Title:** §2.4 brief recovery confirmed clean (operator-side polish complete pre-session); 34-item operator audit pass landed one substantive change (default persistence type LAPSE → PERSIST); `external_api_resources.md` §1 pointer-doc update landed; fresh-eyes review pack authoring deferred to Session 65 along with three standing-instruction evaluations.
**Opened:** 2026-05-03 19:45 ACST
**Closed:** 2026-05-03 20:45 ACST
**Wall-clock:** ~60 min single sitting, same workday continuation of Session 63's 19:26 close (~19 min gap).
**Tool routing:** Claude Chat. No Code routing.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline), DR-021 (timestamp anchoring).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-03 19:45 ACST`.
Close: same command → `2026-05-03 20:45 ACST`.

Same-workday continuation of Session 63's 19:26 close.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- Rebuild root: 11 expected `.md` files + `openapi.json` + `.DS_Store` + `speccy.md` (operator-uploaded snapshot from Session 63 close, expected) + `v3_build_picture.md`.
- `vision copy.md` phantom file flagged at Session 63 close was **absent at Session 64 open** — operator cleaned up between sessions. Logged as silent close-out item.
- `.close_out_backups/` contained `SESSION_64_opening_prompt.md` only (Session 63 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-03 19:26 ACST` matched Session 63 close; `sessions/SESSION_63.md` present (192 lines); `v3_build_picture.md` correctly older than Session 63 close because no streams moved.
- Same-workday tight recap delivered.
- V3 build picture: skipped silently per condition.
- Open-items delta: rendered — one item closed silently (`vision copy.md` phantom file).

## Session shape

Session 64 was an **audit-and-confirm pass on the §2.4 brief, plus a pointer-doc update**. Five rounds of substantive work before close.

Round 1: orientation. Skill ritual ran cleanly. Operator uploaded `speccy.md` (the pre-corruption snapshot) at session start with instruction "this is the file" plus a flag that §10 was dropped for unknown reason during Session 60 assembly.

Round 2: Session 60 outline reconciliation. `conversation_search` confirmed the chat-narration-vs-heading off-by-one — Session 60's drafting narrated each topical section as one ahead of its `##` heading number because front-matter was counted as Block 1. The eleven-content-section count in Session 60's close-out *included* front matter; on disk that's front-matter + ten `##` sections. **Operator subsequently provided the original 18-section outline** as a document upload, which was audited section-by-section against the on-disk file and confirmed: nothing dropped, all 17 topical sections plus front matter accounted for, gap was purely a numbering artefact.

Round 3: 34-item audit pass across six clusters. Operator requested key-assumption surfacing in plain operator/gambling language for confirmation. Six clusters covering connection/auth (§3, §4), subscription shape (§5, §6), live cache and staleness (§7), REST placement and load-bearing gotchas (§9, §15), BSP timing carry-in (§14), rate limits / errors / currency (§12, §16, §17). All confirmed except item 16 — operator pushed back on default persistence type. Substantive exchange: Claude's read was LAPSE-default-with-toggle was structurally safer; operator's read was PERSIST-default for now, may revisit. Locked: PERSIST as default with LAPSE explicit override.

Round 4: drift-check on polish state. Mid-session realisation that the operator had already done the brief polish out-of-session — file was modified at 20:30 ACST (between session open and audit completion), and the on-disk state showed clean §1–§17 numbering, locked-shape header, PERSIST default applied throughout, all inline cross-references updated. **Audit pass had been run as if the brief was unpolished when it was already complete.** Real cost of the misread: ~30 min of audit conversation that confirmed-with-confidence rather than uncovered-new-decisions. The single operator-side change (PERSIST default flip) was the only substantive output of the audit.

Round 5: `external_api_resources.md` §1 pointer-doc update. Two-section addition to §1.1 listing the five on-disk Reference Guide page captures (`placeOrders.md`, `cancelOrders.md`, `replaceOrders.md`, `best_practice.md`, `market_data_request_limits.md`) plus naming the four pages remaining as Path A on-demand fetches. Edit landed cleanly via `Desktop Commander:edit_block`.

Round 6: pivot to fresh-eyes review pack authoring. Two scoping questions surfaced for operator decision (reviewer seat split vs generalist, probe-as-required vs reference-only). Operator instruction: close session, complete in fresh session, with explicit emphasis on context carry-over given the Sessions 60→61→62→63 multi-session governance failure pattern.

## What was delivered

### 1. §2.4 brief audit pass — 34 assumptions confirmed, one change locked

Operator audit confirmed §1–§17 of the brief at the assumption level. Single substantive change surfaced and applied:

- **§9.6 / §16 default persistence type changed from LAPSE to PERSIST.** LAPSE remains an explicit operator override; MARKET_ON_CLOSE remains available for BSP-targeted bets. Flagged "may revisit" — not a permanent lock. Already applied throughout the brief during the operator's out-of-session polish pass.

The audit covered:
- Cluster 1 (connection, authentication): items 1–4 — all confirmed.
- Cluster 2 (subscription shape, field selection, EX_LADDER entitlement open item, order subscription with customerOrderRef tagging): items 5–9 — all confirmed.
- Cluster 3 (in-process cache, two-cache structure, three-tier freshness, no silent fallbacks, dedicated I/O thread): items 10–14 — all confirmed.
- Cluster 4 (REST placement, JSON-RPC over REST, single-retry policy, replaceOrders atomicity gap, updateOrders separate path, prefer-leaving-orders-in-place discipline): items 15–20 — all confirmed except item 16 (PERSIST default).
- Cluster 5 (BSP timing carry-in, the empirical gate, NaN guard, OPEN-but-post-jump partial reconciliation, greyhound asymmetry, phase-aware accessors, 60-second post-CLOSED hold, per-phase publisher cadence): items 21–27 — all confirmed.
- Cluster 6 (rate-limit awareness inside the module, subscription-size guard with deterministic fallback, con=true as v3-side defect, three-tier operator-visible failure surface, plain-English lapse codes, currency conversion at the boundary, currency rate failure non-blocking): items 28–34 — all confirmed.

### 2. §2.4 brief polish — confirmed complete on disk

The brief at `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` is fully polished and locked:

- §11–§17 restored from the seven collapsed `## 11.` headings (operator-side recovery).
- §1–§17 clean numbering applied.
- DRAFT header stripped, locked-shape header applied (Status: Locked, Authored: Sessions 60/61/64, Governing DRs, Source recommendations, Cross-references).
- PERSIST default flip applied throughout (§9.6, §15.7).
- All inline cross-references aligned to new numbering.

The operator did this work between Sessions 63 and 64 plus during Session 64 open (file modified at 20:30 ACST). Confirmed via `grep -n "^## "` and substantive content spot-check.

### 3. `external_api_resources.md` §1 pointer-doc update

Two-section addition to §1.1 (Reference Guide):

- Five on-disk page captures named with their content scope.
- Four pages remaining as Path A on-demand fetches identified.

Edit landed via `Desktop Commander:edit_block` cleanly. Verified post-write.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday tight recap delivered.
- **Cat 1 (V3 build picture conditional render)** — skipped silently per condition.
- **Cat 1 (open-items delta)** — rendered per condition (one item closed silently between sessions).
- **Cat 1 (drift-check)** — done at open. All three checks matched. **Did not catch operator-side polish work that had already been applied** — surfaced mid-session at Round 4 rather than at open. Substrate input for the drift-check methodology gap open item.
- **Cat 1 (short responses, plain language)** — held in audit clusters; each cluster was 4–7 items in plain operator language.
- **Cat 1 (decision-maker framing)** — held. Audit clusters led with the assumption to confirm; reasoning followed only on Round 4 when operator pushed back on the default-persistence flip.
- **Cat 1 (don't drift to alternatives when operator clear)** — held on the operator's PERSIST-default decision (Claude pushed back once with reasoning, accepted operator call, locked it).
- **Cat 1 (unwind shorthand)** — held throughout. DRs cited with bracketed reminders; "§2.4", "Fix 4", "BSP", "burst window", strategy numbers all unwound.
- **Cat 1 (line-break rendering for review content)** — n/a; no review-block content.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held in clusters. Operator-language gambling vocabulary throughout (cycles, in-running, drifters, queue position, edge evaporation).
- **Cat 1 (escalate to detail only when warranted)** — held. The PERSIST-default pushback was flagged as deserving detail before delivering it.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored.
- **Cat 2 (pre-flight directory listing)** — done at open. **Did not flag `speccy.md` as a phantom on first pass** — was treated as expected from Session 63 close. Re-flagged at close as needing operator-side cleanup post-recovery.
- **Cat 2 (Desktop Commander default)** — held.
- **Cat 2 (write_file vs create_file gotcha)** — n/a.
- **Cat 2 (REPL discipline)** — n/a; no scripts written this session. The operator-side polish pass between sessions handled the mechanical-edit work.
- **Cat 2 (verify empirically — don't trust memory)** — held in Round 4 (re-checked file modification time, heading state, cross-reference consistency before accepting that polish was complete).
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 3 (external API resources reach-for)** — n/a substantively; the §1.1 update was operator-targeted not Claude-consuming.
- **Cat 4 (DR-027/028 invoked)** — named at open. Cross-database boundary not engaged substantively.
- **Cat 4 (operational/analytical line discipline)** — held in audit; the brief is operational-line specific.
- **Cat 4 (Betfair-as-canonical-source extension)** — n/a.
- **Cat 5 (software questions are Claude's)** — held on the LAPSE-vs-PERSIST default debate (proposed software-shaped reasoning, operator made the call as the operational decision-maker).

**No new standing instructions surfaced or edited this session.** The three candidates from Sessions 62 + 63 remain logged for evaluation — deferred to Session 65 per operator close instruction.

## Open items in (carried forward + new)

New from Session 64:

- **`speccy.md` phantom file at rebuild root** — operator-uploaded snapshot from Session 63, used as the recovery source. Recovery is complete; file is no longer needed. Operator-side cleanup between sessions.
- **§2.4 brief audit complete; one change locked (PERSIST default).** No further audit needed — the brief is fully reviewed at the assumption level.

Carry-forward (unchanged structure from Session 63):

- **§2.4 Fix 4 fresh-eyes review pack authoring** — Session 65 primary deliverable. Two scoping questions for operator decision at Session 65 open: (a) reviewer seat split (split-seats with Claude on PM/coherence + Grok on skeptic, vs both on generalist fit-for-purpose), (b) probe report inclusion (required-reading vs reference-only with note in orienting prompt).
- **§2.4 Fix 4 fresh-eyes review** — triggers post-pack-authoring. Two reviewers: fresh Claude session + Grok via multi-agent review pattern in `governance.md`.
- **(Session 62) Draft-persistence standing instruction evaluation** — operator decides at Session 65.
- **(Session 63) Mechanical-edit dry-run discipline standing instruction evaluation** — operator decides at Session 65.
- **(Session 63) Structural-drift surfacing at session close standing instruction evaluation** — operator decides at Session 65. Highest-leverage given multi-session blast radius substrate.
- **§2.5 soft-book interface contract** — partial input from probe Q5; BetWatch vendor candidate as parallel-track.
- **§2.10 external analytics scan** — substantially fed by probe; inventory write-up remaining.
- **WIP §16** — VPS in-flight work. Unchanged.
- **Pending architectural extension (Session 42)** — "Betfair as canonical source" extending to all bet records.
- **Fix 9 (Racing API re-fetch)** — non-gating quality work.
- **Fix 10 (`has_subscription_sync` flag desync root-cause)** — non-gating.
- **Three-row collision per-row triage** — non-gating.
- **Low-confidence match review** — non-gating.
- **Durable Fix 8 merge tooling** — Fix 8 report §8.5 recommendation.
- **Session numbering slip in probe brief** — cosmetic.
- **EX_LADDER entitlement question** — operator-side homework; possible DR. Restated in §2.4 §18.3.
- **Drift-check methodology gap** — substrate expanded by Session 64's "did not catch operator-side polish at open" miss.
- **`bethub-analytical` project awaiting activation** — operator decision pending.
- **Post-DR-029 monitoring layer (smaller scope)** — parked.
- **§2.1 BSP-fix code finding (c) — stale `client.py:189` docstring** — non-gating.
- **§2.1 BSP-fix code finding (d) — Sunday discovery returned 71 Betfair WIN markets but 106 active races** — substrate input for §2.5.
- **§2.1 BSP timing observation — open-but-post-jump BSP reachability** — substantively addressed in §2.4 §13.2 / §13.3 (the empirical gate plus partial-reconciliation discipline). Closes at fresh-eyes review completion.
- **BetWatch contacted re: API service and book coverage** — awaiting response.
- **Betfair API membership tiers — investigate.** Operator-side homework.
- **Reference Guide pages remaining to fetch (4 of 9 on disk).** Path A on-demand. Listed in updated `external_api_resources.md` §1.1.
- **PASSIVE bet-delay model handling** — flagged in §2.4 §15.4 as v3.1+ capability.

## Open items out

Closed this session:

- **§2.4 brief polish + structure-align with §2.3 template.** Operator-side recovery complete; brief is locked.
- **§2.4 brief audit pass.** 34 assumptions confirmed; one change locked (PERSIST default).
- **`external_api_resources.md` §1 update.** Pointer to `dr029/2_4_betfair_streaming/reference_guide/` folder + four-pages-remaining note added.
- **`vision copy.md` phantom file at rebuild root.** Operator removed between sessions.

## Session close state

- **Rebuild folder root:** 11 `.md` files + `openapi.json` + `.DS_Store` + `speccy.md` (flagged for operator cleanup) + `v3_build_picture.md`. All directories present.
- **`current_state.md`:** updated by close ritual to reflect Session 65 forward routing.
- **`v3_build_picture.md`:** **not updated.** §2.4 stream remains `in flight` until fresh-eyes review completes. Stream count unchanged at 8.
- **`standing_instructions.md`:** **not updated.** Three candidate instructions remain logged for Session 65 evaluation.
- **`dr029/2_4_betfair_streaming/2_4_betfair_streaming.md`:** **locked and clean.** §1–§17 numbered correctly, locked-shape header applied, PERSIST default applied throughout, cross-references aligned.
- **`external_api_resources.md`:** §1.1 updated with Reference Guide on-disk capture pointer plus remaining-pages note.
- **`sessions/`:** Session 64 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 64 opening prompt removed at close; Session 65 opening prompt to be written.
- **Project knowledge base:** unchanged.
- **VPS state:** unchanged this session.
- **`/tmp/`:** scratch scripts from prior sessions remain (`check_state.py`, `fix_8_merge_execution.py`, etc.). Self-cleanup on macOS reboot. Not governance state.

## Forward routing

**Confirmed with operator at close:** "Close out the session please and we will complete in a fresh session. Please be sure to carry over the required context so there is a seamless transition between sessions, this failure to carry over the draft document has cost a couple of hours of clean up."

**Session 65 primary deliverable: fresh-eyes review pack authoring + three standing-instruction evaluations.**

The two scoping questions surfaced at the end of Session 64 are the first decisions Session 65 makes:

1. **Reviewer seat split vs generalist.** Sessions 20-26's four-seat pattern doesn't fit two-reviewer parallel review. Two options:
    - **Split seats**: Claude gets PM/coherence seat, Grok gets skeptic seat. Differentiated signal.
    - **Both generalist**: each reviewer runs broad-spectrum "is this fit-for-purpose," operator triages findings against each other.
    - Claude's read at Session 64 close: split seats. Operator decides at Session 65 open.

2. **Probe report inclusion.** The probe is substrate for §13/§14 (BSP timing carry-in). Two options:
    - **Required reading**: reviewer reads the probe before the brief. Risks burning context on substrate they may not need.
    - **Reference-only with note in orienting prompt**: "if you want to verify probe-driven claims in §13/§14, here's the source." Lighter context cost.
    - Claude's read at Session 64 close: reference-only with note. Operator decides at Session 65 open.

After scoping decisions land, Session 65 authors:

- **Orienting prompt** (~150–250 words) — what the brief is, what the reviewer's seat is, what good/bad findings look like, where to go for substrate.
- **Same pack to both reviewers** (per Session 62's confirmed shape) — orienting prompt + the locked brief at `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` + reference-only context (probe report, §2.3 artefact for cross-reference shape, `governance.md` multi-agent review pattern).

Plus three standing-instruction evaluations, in order of leverage:

- **Structural-drift surfacing at session close** (Session 63 candidate, highest-leverage). Substrate: would have prevented the §11 gap at its origin (Session 60 close) rather than catching downstream symptoms.
- **Mechanical-edit dry-run discipline** (Session 63 candidate). Substrate: Session 63's faulty renumber script.
- **Draft-persistence convention** (Session 62 candidate). Substrate: Sessions 60→61→62 drafts living only in chat history.

After Session 65 closes the §2.4 stream (review pack ready, reviewers commissioned, instructions evaluated), the next active stream is **§2.5 soft-book interface contract** unless operator-side input from BetWatch lands first.

**Out of scope for Session 65:** §2.5 / §2.6 / §2.7 / §2.8 / §2.9 / §2.10. Anything outside fresh-eyes review pack authoring + three standing-instruction evaluations.

**Operator-side actions between sessions:**

1. **Delete `speccy.md` from rebuild folder root** — recovery snapshot is no longer needed; brief is fully restored on disk.
2. **(Optional, low priority)** Investigate Betfair API membership tiers.
3. **(Optional)** Awaiting BetWatch response on book coverage and API access.
4. **(Optional)** Review `bethub-analytical/README.md` — decide on activation timing.

## Close-out notes

Per the operator's explicit instruction at close — "Please be sure to carry over the required context so there is a seamless transition between sessions, this failure to carry over the draft document has cost a couple of hours of clean up" — this session record and the Session 65 opening prompt are written with extra care to context carry-over. The Sessions 60→61→62→63 multi-session governance gap (silent renumber from 18-outline to 11-assembly, then faulty renumber script, then operator-side recovery) cost roughly two hours of operator time to clean up. The mitigation in this close-out:

- **Forward routing is fully named** — both scoping questions for the review pack are written explicitly so Session 65 doesn't need to re-derive them from chat memory.
- **Session 65 opening prompt names the locked brief path explicitly** plus the three reference-only context files for the review pack so context loading is unambiguous.
- **No drafts living only in chat history this session** — all substantive output (the audit confirmation, the PERSIST flip, the pointer-doc edit) is on disk in canonical artefacts.
- **The standing-instruction candidates are queued in order of leverage** in this record, so Session 65's evaluation order is locked.

The drift-check methodology open item gained substrate this session: the open ritual did not catch the operator-side polish work that had already been applied between Sessions 63 and 64. Session 65's drift-check methodology evaluation should consider this.
