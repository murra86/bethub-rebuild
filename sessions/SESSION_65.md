# Session 65

**Title:** §2.4 fresh-eyes review pack assembled (consolidated sanctioned reference document + orienting prompt) plus two new standing instructions added (Cat 2 structural-drift surfacing + Cat 3 dry-run multi-target mechanical edits); third candidate confirmed already-in-place from Session 64.
**Opened:** 2026-05-03 20:57 ACST
**Closed:** 2026-05-03 21:29 ACST
**Wall-clock:** ~32 min substantive single sitting, same-workday continuation of Session 64's 20:45 close (~12 min gap).
**Tool routing:** Claude Chat. No Code routing.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-database integration boundary discipline), DR-021 (timestamp anchoring).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-03 20:57 ACST`.
Close: same command → `2026-05-03 21:29 ACST`.

Same-workday continuation of Session 64's 20:45 close.

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- Rebuild root: 11 expected `.md` files + `openapi.json` + `.DS_Store` + `speccy.md` (operator carry-forward cleanup, still present at open) + `v3_build_picture.md`. All directories present.
- `.close_out_backups/` contained `SESSION_65_opening_prompt.md` only (Session 64 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-03 20:45 ACST` matched Session 64 close; `sessions/SESSION_64.md` present (221 lines); `v3_build_picture.md` correctly older than Session 64 close because no streams moved.
- Same-workday tight recap delivered.
- V3 build picture: skipped silently per condition.
- Open-items delta: skipped silently per condition.

## Session shape

Session 65 was an **assembly + governance session**: one substantive deliverable (the §2.4 fresh-eyes review pack) and one governance pass (three standing-instruction candidate evaluations). Six rounds of work plus close.

Round 1: orientation. Skill ritual ran cleanly. Two scoping questions surfaced from Session 64's close — reviewer seat shape (split vs generalist) and probe-report inclusion (required vs reference-only).

Round 2: scoping question collapse. Operator pushed back on Claude's framing ("what do you think?"), Claude provided directional reads (split seats; reference-only). Operator then introduced a meaningful pivot: the review pack should instruct reconciliation against Betfair sanctioned materials and Racing API materials directly, with the same prompt going to both reviewers. This collapsed the seat-split question (same prompt to both) and changed the probe-report question (probe drops out — the reviewers' reference frame is Betfair-external, not BetHub-internal).

Round 3: pack shape decision. Operator further pivoted to a two-document-plus-prompt structure for each reviewer to minimise effort. Decision: assemble all sanctioned material into a single consolidated reference document, plus the locked brief, plus the orienting prompt. The consolidated reference document becomes durable beyond this review (useful for §2.7 API contract versioning and post-v3 operational debugging).

Round 4: between-session capture list and assembly start. Claude listed the four Reference Guide pages the operator needed to capture between sessions (`updateOrders`, `Login & Session Management`, `Betting Enums`, `Betting Exceptions`) with file naming convention. Assembly of the consolidated reference document started in parallel: front matter + structural skeleton, then concatenation of the on-disk Streaming API reference (986 lines) and five captured Reference Guide pages (`placeOrders`, `cancelOrders`, `replaceOrders`, `best_practice`, `market_data_request_limits`), with four placeholder sections clearly flagged for the missing pages.

Round 5: Section 3 (Racing API) scoping question + assembly. Operator chose §2.4-relevant scope only (option b) over full Racing API summary (option a). Section 3 assembled: endpoint catalogue limited to AUS meets/races/results, plus identity-reconciliation note for the Betfair-Racing API mapping that the brief implicitly depends on. Section 4 (cross-reference index) followed: a table mapping every §2.4 brief section to the most relevant reference material in Sections 1-3.

Round 6: orienting prompt drafting + standing-instruction evaluations. Prompt drafted with severity-tagged finding format, four-section output structure, single-pass constraint. Operator added Betfair Developer Forum and Betfair GitHub as additional sanctioned sources. Locked at 134 lines. Then three standing-instruction candidates evaluated in order of leverage: (1) structural-drift surfacing at session close — added to Cat 2 close-out actions; (2) dry-run multi-target mechanical edits — added to Cat 3 filesystem and tooling discipline; (3) draft-persistence convention — confirmed already-in-place from Session 64's edit, no new work needed.

## What was delivered

### 1. Consolidated sanctioned reference document

`dr029/2_4_betfair_streaming/review_pack/sanctioned_reference.md` — 1,737 lines, four sections:

- **Section 1 — Betfair Streaming API:** full reference inserted from on-disk capture (986 lines).
- **Section 2 — Betfair Exchange REST API (Reference Guide):** five captured pages on disk inserted (placeOrders, cancelOrders, replaceOrders, best_practice, market_data_request_limits) plus four placeholder sections flagged for operator capture between sessions (updateOrders, Login & Session Management, Betting Enums, Betting Exceptions).
- **Section 3 — Racing API (§2.4-relevant scope):** endpoint catalogue limited to AUS meets/races/results, schemas for Race / Runner / Meet, identity-reconciliation note for Betfair-Racing API mapping.
- **Section 4 — Cross-reference index:** table mapping every §2.4 brief section to relevant reference material in Sections 1-3.

The document includes provenance notes for each captured source plus an explicit Confluence access note (the Betfair developer docs sit behind an anonymous-access wall; on-disk captures are the canonical reference for this review).

### 2. Orienting prompt

`dr029/2_4_betfair_streaming/review_pack/orienting_prompt.md` — 134 lines, locked. Single prompt to both reviewers (Claude fresh session + Grok session) per the multi-agent review pattern in `governance.md`. Key elements:

- **Task framing:** reconcile every substantive design choice in the brief against Betfair's sanctioned developer materials and The Racing API's documented surface. Not a "is the direction right" review — that's settled.
- **Inputs named:** locked brief + consolidated reference document + the prompt itself.
- **Additional sanctioned sources:** Betfair Developer Forum (`forum.developer.betfair.com`) and Betfair GitHub organisation (`github.com/betfair`) as anonymously-reachable cross-references for community-discovered API quirks and implementation-pattern reference.
- **Output format:** four-section markdown — substantive findings (severity-tagged BLOCKING / SIGNIFICANT / MINOR), gaps, sections reviewed without findings, notes for operator.
- **Constraints:** single pass, specific brief-section + reference-section citations required, plain operator language, findings only (no redrafts).

### 3. Two new standing instructions added to `standing_instructions.md`

**Cat 2 close-out actions, immediately after draft-persistence:**

> Surface structural-drift in the session record. If an in-session decision changed the structure of a governance artefact — renumbering, schema shift, file split, assembly choice diverging from the original spec, content collapsed or expanded across section boundaries — the session record's "What was delivered" section must explicitly flag the change as a governance event. The opening prompt for the next session must carry the flag forward alongside routing direction. Substrate: Sessions 60→61's silent renumber from 18-outline to 11-assembly created the §11 gap that propagated through three sessions and cost ~2 hours of operator recovery time.

**Cat 3 filesystem and tooling discipline, immediately after REPL discipline:**

> Dry-run multi-target mechanical edits before write. When running scripted edits that touch more than one location in a file or more than one file via pattern-matching (renumbers, mass find/replaces, regex substitutions, structural reshapes), produce a diff or proposed-changes summary for operator review before writing to the canonical artefact. The diff names every change site so the operator can confirm none of them are collisions, accidental matches, or cascade artefacts. Single-target edits via `edit_block` (one specific old_string → one specific new_string in one specific place) are exempt — the substitution is visibly literal in the tool call. Substrate: Session 63's renumber script ran cleanly with no Python error but cascaded across seven section headings, all sub-sections, and every inline cross-reference because the regex was stateless across descending passes.

**Operator-side action:** `standing_instructions.md` needs re-uploading to the bethub-rebuild Claude Project knowledge base.

### 4. Candidate 3 (draft-persistence convention) confirmed closed-by-prior-session

Session 64's edit added the draft-persistence convention to Cat 2 close-out actions (the "Persist drafted-but-not-assembled artefact content to scratch" bullet). Session 65 evaluation confirmed: wording is good, scope is right, no revision needed. Recorded as closed in this session record so future sessions don't re-evaluate.

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday tight recap delivered.
- **Cat 1 (V3 build picture conditional render)** — skipped silently per condition.
- **Cat 1 (open-items delta)** — skipped silently per condition.
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. One operator request mid-session for plain language on candidate 3 — Claude delivered plainly without re-explaining the entire substrate.
- **Cat 1 (decision-maker framing)** — held. Each scoping question led with the decision; reasoning followed only when warranted.
- **Cat 1 (don't drift to alternatives when operator clear)** — held when operator pivoted twice (sanctioned materials shape, two-document-plus-prompt shape). Claude reflected back the pivot and proceeded.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders.
- **Cat 1 (escalate to detail only when warranted)** — held. Standing-instruction evaluations 1 and 2 flagged as deserving detail; candidate 3 was deliberately compressed because it's already-in-place.
- **Cat 1 (line-break rendering for review content)** — held on the orienting prompt draft.
- **Cat 1 (default to luddite-analyst-gambler brevity)** — held in scoping rounds.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored.
- **Cat 2 (pre-flight directory listing)** — done at open and close.
- **Cat 2 (Desktop Commander default)** — held. One `str_replace` failure self-corrected to `Desktop Commander:edit_block`. Surfaced inline as the path-namespace gotcha that's documented in Cat 3 — Claude noted the correction and proceeded.
- **Cat 2 (write_file vs create_file gotcha)** — n/a; only `write_file` and `edit_block` used for canonical artefacts.
- **Cat 2 (REPL discipline — write-script-to-/tmp + start_process)** — held. Two scripts written to `/tmp/` (`replace_section_3.py`, `replace_section_4.py`) plus one shell script (`assemble_sanctioned_reference.sh`).
- **Cat 2 (Persist drafted-but-not-assembled artefact content to scratch)** — n/a; no in-flight drafts deferred at close. The orienting prompt and reference document were both assembled directly to canonical paths during the session, not deferred.
- **Cat 2 (Surface structural-drift in the session record)** — newly authored this session. Self-applied: this session did not change the structure of any governance artefact (the brief was not edited, the existing standing instructions were not restructured), so no structural-drift event surfaces in the "What was delivered" section above. The two new standing instructions are additive, not structural changes.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 3 (external API resources reach-for)** — held. `external_api_resources.md` was the source for Section 1 references in the consolidated reference document.
- **Cat 3 (Dry-run multi-target mechanical edits before write)** — newly authored this session. Self-applied: the two `replace_section_3.py` and `replace_section_4.py` scripts were single-target edits (one specific old block → one specific new block in one specific file) and so are exempt from the dry-run requirement per the instruction's own scope. The shell-script concatenation was append-only, not pattern-matching, also exempt.
- **Cat 4 (DR-027/028 invoked)** — named at open. Cross-database boundary not engaged substantively.
- **Cat 4 (operational/analytical line discipline)** — held. The Section 3 Racing API summary explicitly distinguished operational-line vs analytical-line context for the reviewer.
- **Cat 4 (Betfair-as-canonical-source extension)** — n/a.
- **Cat 5 (software questions are Claude's)** — held in scoping decisions and assembly choices. Operator made the routing call on sanctioned-materials shape (their decision); Claude proposed and confirmed software-shaped detail (assembly path, file structure, prompt format).

**Self-applied check on the two new standing instructions:** both held in this session by virtue of the work shape. The instructions begin to apply binding starting at Session 66.

## Open items in (carried forward + new)

New from Session 65:

- **§2.4 fresh-eyes review pack** — assembled but not yet shippable. Four placeholder sections in Section 2 of `sanctioned_reference.md` await operator-captured Reference Guide pages. Once captured (operator has the pages downloaded; slot-in is Session 66's first work), the pack ships to both reviewers.
- **`standing_instructions.md` re-upload to Claude Project knowledge base** — operator-side action between sessions.

Carry-forward (unchanged structure from Session 64 unless noted):

- **§2.4 Fix 4 fresh-eyes review** — triggers post-pack-shipping (i.e. after Session 66's slot-in completes the pack and operator dispatches to reviewers).
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
- **EX_LADDER entitlement question** — operator-side homework; possible DR.
- **Drift-check methodology gap** — substrate unchanged this session.
- **`bethub-analytical` project awaiting activation** — operator decision pending.
- **Post-DR-029 monitoring layer (smaller scope)** — parked.
- **§2.1 BSP-fix code finding (c) — stale `client.py:189` docstring** — non-gating.
- **§2.1 BSP-fix code finding (d) — Sunday discovery returned 71 Betfair WIN markets but 106 active races** — substrate input for §2.5.
- **§2.1 BSP timing observation — open-but-post-jump BSP reachability** — substantively addressed in §2.4 §13.2 / §13.3. Closes at fresh-eyes review completion.
- **BetWatch contacted re: API service and book coverage** — awaiting response.
- **Betfair API membership tiers — investigate.** Operator-side homework.
- **Reference Guide pages remaining to fetch (4 of 9 on disk).** Operator has captured between sessions; slot-in is Session 66's first work.
- **PASSIVE bet-delay model handling** — flagged in §2.4 §15.4 as v3.1+ capability.

## Open items out

Closed this session:

- **§2.4 fresh-eyes review pack authoring** — both files assembled on disk. Pack ships once Section 2 placeholders are populated (Session 66's first work).
- **(Session 62) Draft-persistence standing instruction evaluation** — confirmed already-in-place from Session 64; closed by prior session.
- **(Session 63) Mechanical-edit dry-run discipline standing instruction evaluation** — added to Cat 3 of `standing_instructions.md`.
- **(Session 63) Structural-drift surfacing at session close standing instruction evaluation** — added to Cat 2 of `standing_instructions.md`.
- **`speccy.md` phantom file at rebuild root** — operator deleted between Session 64 close and Session 65 close.

## Session close state

- **Rebuild folder root:** 11 `.md` files + `openapi.json` + `.DS_Store` + `v3_build_picture.md`. `speccy.md` deleted by operator. All directories present.
- **`current_state.md`:** updated by close ritual to reflect Session 66 forward routing.
- **`v3_build_picture.md`:** **not updated.** §2.4 stream remains `in flight` until fresh-eyes review completes. Stream count unchanged at 8.
- **`standing_instructions.md`:** **updated.** Two new instructions added (Cat 2 structural-drift, Cat 3 dry-run). Operator action: re-upload to Project knowledge base.
- **`dr029/2_4_betfair_streaming/2_4_betfair_streaming.md`:** unchanged. Locked.
- **`dr029/2_4_betfair_streaming/review_pack/sanctioned_reference.md`:** **new file.** 1,737 lines, four placeholder sections in Section 2 awaiting Session 66 slot-in.
- **`dr029/2_4_betfair_streaming/review_pack/orienting_prompt.md`:** **new file.** 134 lines, locked.
- **`external_api_resources.md`:** unchanged.
- **`sessions/`:** Session 65 record written by close ritual (this file).
- **`.close_out_backups/`:** Session 65 opening prompt removed at close; Session 66 opening prompt to be written.
- **Project knowledge base:** standing_instructions.md needs re-upload.
- **VPS state:** unchanged this session.
- **`/tmp/`:** scratch scripts from this session (`assemble_sanctioned_reference.sh`, `replace_section_3.py`, `replace_section_4.py`) plus prior-session scratch remain in place. Self-cleanup on macOS reboot. Not governance state.

## Forward routing

**Confirmed with operator at close:** "I have deleted speccy.md from the hard drive, so that is complete. I've downloaded the extra reference material. Let's do that as the first thing. It's session 66."

**Session 66 primary deliverable: complete the §2.4 review pack and ship to reviewers.**

Sequence:

1. **First work:** slot the operator-captured Reference Guide pages into `dr029/2_4_betfair_streaming/reference_guide/` (operator places them there or Claude reads from operator's downloads location and writes them in), then replace the four placeholder sections in `sanctioned_reference.md` Section 2 with the captured content. Verify Section 2 cross-reference index entries still match.
2. **Final pack verification:** read both `sanctioned_reference.md` and `orienting_prompt.md` end-to-end to confirm consistency.
3. **Dispatch to reviewers:** operator handles sending to fresh Claude session and Grok session (operator-side action; Claude doesn't dispatch).
4. **Begin §2.5 soft-book interface contract drafting** — once the pack is shipped, the next active stream is §2.5 unless BetWatch input lands first.

**Out of scope for Session 66:** §2.6 / §2.7 / §2.8 / §2.9 / §2.10. Anything outside the pack completion + §2.5 brief drafting kickoff.

**Operator-side actions between sessions:**

1. **Re-upload `standing_instructions.md`** to the bethub-rebuild Claude Project knowledge base (two new instructions added this session).
2. **Place the four captured Reference Guide pages** in `dr029/2_4_betfair_streaming/reference_guide/` if not already there, with file names: `updateOrders.md`, `login_session_management.md`, `betting_enums.md`, `betting_exceptions.md`.
3. **(Optional, low priority)** Investigate Betfair API membership tiers.
4. **(Optional)** Awaiting BetWatch response on book coverage and API access.
5. **(Optional)** Review `bethub-analytical/README.md` — decide on activation timing.

## Close-out notes

Clean close. Two new standing instructions landed; review pack core deliverables on disk; operator-side captures already done before Session 65 close (the only thing left is mechanical slot-in, which is Session 66's first work).

The two new standing instructions self-applied this session — neither was triggered binding because (a) no structural changes were made to governance artefacts, and (b) all scripted edits this session were single-target via `edit_block`, exempt from the dry-run requirement. The instructions begin binding at Session 66.

Session 64's lesson on context carry-over held: the §2.4 brief stayed locked and untouched through the session, all substantive output landed on disk in canonical paths, no drafts living only in chat history.
