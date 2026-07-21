# Session operations proposal — context retention and burn reduction

**Drafted:** Session 40, 2026-05-01 ACST.
**Status:** PROPOSAL — operator review required before any changes land.
**Author:** Claude (operator-Claude session, Adelaide).
**Scope:** how operator-Claude sessions open, run, and close for the bethub-rebuild project.
**Primary constraint:** context retention. Anything proposed here must demonstrably *retain* established context better than the current approach, not just save tokens. Context loss is the failure mode being solved for; token efficiency is the secondary lever.

---

## 1. The problem in one paragraph

Sessions currently open by reading 50–65K tokens of context (25–32% of the 200K window) before any substantive work begins. That's WIP at 113K, plus the opening prompt, plus 1–2 prior session records, plus 1–3 reference artefacts. The structural driver is that WIP is append-only — every session adds a new "Where we are (Session N)" entry, twenty-six of them now, most duplicating what already exists in `sessions/SESSION_N.md`. The deeper failure mode is more important than the token count: because everything is rendered as prose in flat markdown files, fundamental decisions agreed in earlier sessions can get lost when a long session pushes them out of working memory. Operator has explicitly named this — "we can go through a chat and you've developed something while forgetting this fundamental item we'd agreed upon earlier." The fix has to address that, not just trim bytes.

## 2. What changed in 2026 that's relevant

Some of the structural assumptions baked into how this project has run were correct when established but are now stale. Three things shipped between February and April 2026 that change the design space:

1. **Claude 4.6/4.7 with 1M token context window** is generally available at standard pricing as of March 2026. The 200K window is no longer the binding constraint it was when WIP-as-single-file was designed. (Claude.ai chat interface still uses 200K by default, but the architectural assumption of "every byte costs" has eased.)
2. **Claude Projects** are available on free and paid tiers. Projects let you upload reference documents *once* and they persist across all chats within the Project — they don't re-burn context per session the way "read this file at session open" does. Pro plan gives 40 files per Project plus enhanced retrieval (RAG) over them. *This is the single biggest unused lever for this project.*
3. **Custom Skills** (folder with SKILL.md) are uploadable to Claude.ai under Settings → Capabilities → Skills. They let you encode "how to do X for this project" once and have Claude load the relevant skill on demand based on what you're asking. They compose — Claude can fire multiple skills together. They fire automatically (no `/command` needed in chat).
4. **Memory** (the userMemories block in Claude's context) already carries the substantive shape of this project — Tim, Adelaide, Moose, BetHub v2 + bethub-rebuild, four racing strategies, key decision records. Most of it is currently up-to-date and useful. This is why I can already write you a coherent answer at session open without you re-explaining yourself. **But** Memory is opaque to you, summarised by Claude not authored by you, and you can only edit it indirectly. It's a complement to documents, not a substitute.

The current rebuild folder design was built before any of these shipped widely. Re-architecting around them is the right move.

## 3. The core insight

**The rebuild folder is currently doing two jobs that should be split.**

- **Job A — durable canonical truth.** What's been decided, what's locked, what the architecture is, what the standing instructions are, what's in scope, what's out of scope. This stuff needs to be *referenceable forever*, *easy to update*, and *primary loaded at session open*.
- **Job B — session journal and parking lot.** What happened Session N, what's next, what's parked, what's in-flight, what changed since last time. This stuff needs to be *appendable*, *time-ordered*, and *summarisable* — not necessarily fully read at every session open.

WIP currently does both jobs in one file. That's why it's 113K. Splitting them allows each to be optimised for its actual job.

## 4. Proposed new structure

### 4.1 At the canonical-truth layer (Job A)

These docs become the **Project knowledge base** (uploaded once to Claude Projects, available to every chat in the Project without re-reading per session):

- `vision.md` — what v3 is for. Slow-changing. **(no change)**
- `architecture.md` — v3 architectural design. Slow-changing. **(no change)**
- `decisions.md` — every numbered Decision Record (DR-001 through DR-029+). Append-only-by-DR. **(no change)**
- `governance.md` — close-out protocol, multi-agent review pattern, etc. **(no change)**
- `v3_data_requirements.md` — current scope of v3 day-one data needs. **(no change)**
- `dr029/dr029_scope.md` — active arc scope, locked items per scope item. **(no change)**
- **NEW: `standing_instructions.md`** — extracted from WIP. All the "Standing instruction added Session N" entries plus the operator-instructions-carried-forward list. Becomes the authoritative source of how to run sessions. Updated when a new instruction lands; existing entries amended in-place when superseded. **The forty-or-so standing instructions currently scattered through WIP get organised by category here**: Filesystem discipline, Tool routing, Operator-facing presentation, Close-out protocol, etc. This is the most important new file. It is what stops Claude forgetting fundamental agreements.
- **NEW: `project_context.md`** — extracted from WIP. The "what is this project, who is the operator, what's the project running history" anchor. ~3-5 pages. Essentially the userMemories content but operator-authored, operator-controlled, and version-controlled. Becomes the orientation primer for any fresh session.

These eight files (six existing, two new) become the **Project knowledge base**. Together they're roughly the same total size as today's canonical files plus the extracted parts of WIP — but they don't load per session. They load *once* into the Project and persist.

### 4.2 At the journal layer (Job B)

- **NEW: `current_state.md`** — what's the new WIP. ~10–20 KB target, not 113 KB. Carries:
  - "Where we are right now" (this session and last session, not all 26 historical).
  - Open items (numbered, in/out, gating-status).
  - What's next (the one-row-per-session table — current and upcoming, not historical).
  - Active artefact references (briefs in flight, what they're commissioning, where the report lands).
  - Anything genuinely *current* — not historical.
- **`sessions/`** — unchanged. One short note per session, immutable, append-only-as-sessions-happen. **(no change)**
- **`current_state.md` rotates content into `sessions/SESSION_N.md` at close**, rather than appending session N's "Where we are" into a growing main file.

The session record is the durable historical truth. `current_state.md` is the live working state. They share a cleaner separation than today.

### 4.3 At the per-task layer (skill files)

Three custom skills authored over the next 1–2 sessions:

- **`bethub-session-open` skill** — when operator says "open session N" or starts a new chat in the Project, Claude reads `current_state.md`, the most recent 1–2 session records, names the governing DRs, runs DR-021 timestamp anchor, runs pre-flight directory listing, summarises orientation in <8 sentences. Encodes the entire session-open ritual that's currently re-stated in every opening prompt.
- **`bethub-session-close` skill** — when operator says "close out session N", Claude writes the SESSION_N.md record, updates `current_state.md` (rotating "where we are" historical content into the session record, not appending forever), updates `standing_instructions.md` if any new ones surfaced, generates the next opening prompt as a *short pointer*, runs the close-out verification checklist. Encodes the close-out protocol from `governance.md` plus the open-and-close-out economy directive.
- **`bethub-brief-drafting` skill** — when operator wants a Code brief drafted (Fix 4, Fix 5, future surgical fixes, future probes), Claude knows the brief structure precedent (eight numbered sections, hard-limits, dirty-tree-handling, output target, single-Code-session bound, anything-surprising section). Encodes the pattern that emerged from Session 28, 33, 35, 36, 39 briefs.

Skills fire automatically from operator's natural-language request. No `/command` needed. They load only the relevant skill — no per-session prelude burn.

### 4.4 At the memory layer

userMemories stays as-is but is treated as **augmenting**, not replacing, `project_context.md`. The Memory feature is operator-readable and operator-editable (Settings → Capabilities → Memory). Periodic operator review of Memory lets you correct anything that's drifted from the canonical project state.

## 5. What this looks like at session open

**Today** (Session 40 example):
1. Operator pastes opening prompt.
2. Claude runs DR-021 timestamp anchor.
3. Claude reads WIP (113K).
4. Claude reads SESSION_39 (12K).
5. Claude reads probe brief (33K).
6. Pre-flight directory listing.
7. Orientation summary.
8. ~50–60K tokens consumed before substantive work.

**Proposed** (Session 41 example):
1. Operator opens new chat in **bethub-rebuild Project**.
2. Project knowledge base pre-loads: `vision.md`, `architecture.md`, `decisions.md`, `governance.md`, `v3_data_requirements.md`, `dr029_scope.md`, `standing_instructions.md`, `project_context.md`. Total ~150K-200K tokens but **loaded by Project infrastructure, not consumed from chat context window** — RAG retrieval pulls only relevant bits per question.
3. Operator: "Open Session 41."
4. **`bethub-session-open` skill fires automatically.** Skill reads `current_state.md` (~15K), most recent session record (~12K). Runs DR-021 timestamp anchor. Pre-flight directory listing. Orientation summary.
5. ~25–30K tokens consumed before substantive work. **Half the current burn.**

But the bigger win is that the canonical knowledge base is **always available** without ever being explicitly re-read. If Session 41 surfaces a question about DR-014 or §B.7 of v3_data_requirements, Claude pulls it via Project retrieval — the doc is *there* — not via a fresh `read_file` call.

## 6. What this looks like at session close

**Today** (Session 39 example):
1. Operator: "Close out."
2. Claude writes 6K SESSION_39.md record.
3. Claude appends ~3K "Where we are (Session 39)" entry to WIP — WIP grows from 110K to 113K.
4. Claude generates ~10K opening prompt for Session 40.
5. Total close-out written: ~19K + WIP grows.

**Proposed** (Session 41 example):
1. Operator: "Close out."
2. **`bethub-session-close` skill fires.**
3. Skill writes SESSION_41.md (~6–10K) — durable record.
4. Skill **rotates** content out of `current_state.md` — old "where we are" entries flow into the new session record; `current_state.md` stays at ~15K, doesn't grow.
5. Skill checks if any new standing instructions surfaced — appends to `standing_instructions.md` if so.
6. Skill generates short opening pointer (~1–2K, not 10K) for Session 42 — because the standing context is in the Project, not re-stated in the prompt.
7. WIP no longer exists as a single growing file.

## 7. Migration plan

**This is not done in one session.** Migration is itself work that needs context budget and operator review.

### Phase 1 (Session 41 — probe-triage day)
- Probe takes priority. Migration work fits around it.
- Single small action: create the Project in Claude.ai, name it "bethub-rebuild". Do nothing inside it yet.

### Phase 2 (Session 42 or 43, dedicated meta-session)
- Extract `standing_instructions.md` from WIP (carving out all "Standing instruction added Session N" entries plus the operator-instructions-carried-forward list).
- Extract `project_context.md` from WIP (project background, operator background, naming, vocabulary).
- Create stub `current_state.md` from WIP's "where we are (Session N)" most-recent-entry only, plus open items and what's-next table.
- Upload all eight canonical docs to the Project knowledge base.
- Custom instructions on the Project: brief instructions referencing the standing-instructions file, naming Adelaide local time, naming the operator-facing presentation discipline.
- Author the three skills (`bethub-session-open`, `bethub-session-close`, `bethub-brief-drafting`).
- Test the new flow on a low-stakes session (maybe a Fix 5 brief drafting session).
- WIP itself stays in the rebuild folder during Phase 2 as a fallback. Don't delete until the new flow has proven out across 2–3 sessions.

### Phase 3 (after Phase 2 has stabilised)
- Archive WIP into `sessions/ARCHIVE_work_in_progress_through_session_N.md` (immutable historical reference).
- Delete WIP from rebuild root.
- Update README.md to reflect the new structure.

### Phase 4 (ongoing)
- New standing instructions land in `standing_instructions.md` directly, not in WIP.
- New session records keep landing in `sessions/`.
- `current_state.md` updates per session-close skill behaviour.
- Skills get refined over the next 5–10 sessions as the patterns reveal themselves.

## 8. What this proposal does NOT change

- **Decision records.** DRs continue to be authored in `decisions.md` exactly as today. Numbered, immutable.
- **Active arc artefacts.** `dr029/` directory and its sub-artefacts (briefs, reports, scope) stay exactly where they are.
- **Session records.** `sessions/SESSION_N.md` keeps the same shape and append-only discipline.
- **Governance protocols.** Close-out checklist, pre-flight directory listing, DR-021 timestamp anchor, multi-agent review pattern — all unchanged in substance, just encoded in skills rather than re-stated in opening prompts.
- **Operator-facing presentation discipline.** Short, plain-language, decision-maker-framing — unchanged. Lives in `standing_instructions.md` going forward.

## 9. Risks and trade-offs

- **Migration cost.** Phase 2 is probably a 2–3 hour dedicated session of meta-work. Real cost. Pays back over the next ~10 sessions.
- **Skill-authoring learning curve.** Skills are simple (markdown + YAML frontmatter), but the discipline of writing a *good* description is the load-bearing skill. Anthropic's docs make a strong point: if the description is bad, the skill never fires. We'd start simple and iterate.
- **Project RAG is not perfect.** Retrieval-augmented retrieval can miss context that an operator-Claude session would have caught with a full WIP read. Mitigation: keep `current_state.md` small enough to read in full at every session open, even with the Project. Don't over-rely on retrieval for the live state.
- **Fragmentation risk.** Eight canonical files instead of one WIP could make it harder to find something. Mitigation: README.md becomes the authoritative index. `standing_instructions.md` is organised by category not chronology, so finding "what's the close-out protocol" doesn't require remembering which Session it landed in.
- **Memory drift.** userMemories is summarised by Claude, not authored by you. If it drifts, that's a real risk. Mitigation: periodic operator review of Settings → Memory; keep authoritative truth in the Project knowledge base, not in Memory.
- **You don't currently have skills authored.** That's two new skills (open, close) to write before they can fire. Realistic effort: 1–2 hours per skill, plus iteration over the next few sessions to refine triggers and instructions.

## 10. Why this addresses context retention specifically

The core failure mode operator named: *we agree on something fundamental, then later sessions develop something that contradicts it because the agreement was forgotten.*

Three new structural protections against this:

1. **`standing_instructions.md` is the canonical "do not forget" document.** Loaded into Project knowledge base. Available to every session. Organised by category for findability. When a fundamental agreement lands ("operator-facing presentation discipline" Session 39 / "operational-vs-analytical line discipline" Session 32 etc.), it goes here and stays here. Never gets pushed out by newer entries because it's not a journal — it's an instruction set.
2. **DRs continue to be the agreement-of-record.** When something is *decided* (architectural, vocabulary, scope), it lands as a numbered DR. DRs are immutable and the entire `decisions.md` file is in the Project knowledge base. Memory or chat-context drift can't override a DR — Claude can always pull DR-014 fresh from the Project.
3. **Skills can encode procedural agreements** (how to draft a brief, how to run close-out, how to handle dirty trees). When operator-Claude agreed "honour the dirty git tree per Sessions 35/36/37 pattern," that pattern can be a skill. Future sessions that look at draft briefs will fire that skill automatically — Claude does not have to *remember* the pattern, the skill *is* the pattern.

The current approach trusts WIP-as-single-file to hold all agreements forever. The new approach distributes agreements across three robust layers (DRs, standing instructions, skills), all available without per-session reload.

## 11. Recommendation

Adopt the proposal. Concretely:

- **Now (this session, no further action):** operator reads this document at leisure, marks up, gives feedback.
- **Next session (Session 41):** probe triage takes priority. If time permits, create the Project in Claude.ai as Phase 1.
- **Session 42 or 43:** dedicate to Phase 2 migration. ~2–3 hours.
- **Sessions 44+:** new flow active. Skills get iterated. Old WIP archived once new flow has demonstrated stability over 2–3 sessions.

The probe and Fix 4 / Fix 5 briefs are still the load-bearing v3 work. This proposal is meta-work to make the *next 30 sessions* of that load-bearing work cheaper and more reliable. It pays back, but the payback is not in this session or the next.

## 12. Open questions for operator

- Do you have Claude Pro? (Free tier limits Projects to 5 and caps file count; Pro gives 40 files plus enhanced retrieval.)
- Are you happy uploading the rebuild folder canonical docs to a Claude Project, recognising the tradeoff that Anthropic gets persistent visibility of those files? (Privacy consideration — your rebuild folder isn't currently uploaded anywhere.)
- Any of the above feel wrong, or like it's solving the wrong problem? Operator's read on whether the diagnosis matches your felt experience matters more than my analysis.

---

*End of proposal.*
