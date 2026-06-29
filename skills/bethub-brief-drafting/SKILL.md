---
name: bethub-brief-drafting
description: Use when the operator asks Claude Chat to draft a brief that commissions out-of-session Claude Code work in the bethub-rebuild project. Triggers include "draft a brief for Code", "we need a brief for Fix N", "scope this for Code as a brief", "let's write the brief for X", or any close paraphrase that names a Code-bound deliverable. Briefs are locked specifications that Code executes against — single bounded session, named anchors only, no edits outside scope, hard limits explicit, output spec named, what-happens-after stated. Do not use for governance documents, session records, opening prompts, or operator-facing planning artefacts. Bethub-rebuild only.
---

# bethub-brief-drafting

This skill encodes the authoring pattern for briefs that commission out-of-session Claude Code work. It distils the discipline established across Sessions 28 (§2.1 inspection brief), 33 (source-review brief), 35 (Fix 1+2 surgical brief), 36 (Fix 3 surgical brief with dirty-tree handling), and 39 (Saturday API observation probe brief).

A brief is a locked specification. Code reads it once, executes against it end-to-end in a single bounded session, and produces a report. The brief is the contract — Code does what's named, doesn't do what isn't, and surfaces surprises as findings rather than chasing them. The discipline that makes this work lives below.

The skill is **narrow** — it encodes the universal shape and the discipline that travels with every brief, not per-type templates. Each brief Claude drafts adapts the shape to its specific job (inspection looks different from surgical-fix looks different from probe). The judgement of what fits is Claude's, drawing on the precedent sessions when needed.

## When this skill fires

**Triggers (exhaustive — fire on any of these):**

- Operator says "draft a brief for Code", "let's write the brief for X", "scope this for Code", "we need a brief for Fix N", "brief for the next probe", or any close paraphrase naming a Code-bound deliverable.
- Operator says "next we need to commission Code on X" or similar where the implied next step is brief-drafting.
- Operator surfaces a finding from a Code report and asks "what's the next brief?" or "draft the follow-up".

**Does not fire:**

- Operator asks for a session record, an opening prompt, a governance addendum, an operator-facing planning document, or any artefact whose audience is the operator rather than Code.
- Operator is mid-discussion of *whether* Code work is the right next step — that's a routing decision, not a brief-drafting trigger. Wait for the routing call before firing.
- Operator asks for a lightweight scope sketch (one or two paragraphs) rather than a full brief — clarify before assuming brief shape.

When the trigger is ambiguous, ask the operator directly: "Full Code brief, or a lighter scope sketch?" before running the ritual.

## Brief-drafting ritual — step by step

### Step 1 — Confirm what Code is being commissioned to do

Before drafting anything, name the job in one or two sentences. The job names: (a) what Code measures, fixes, or observes; (b) which scope-doc section or finding it serves; (c) what report it produces. If any of those three are unclear, ask the operator before drafting.

This step exists because briefs that drift in scope during drafting are the most expensive failure mode. Naming the job up front anchors every subsequent decision.

### Step 2 — Pre-flight grounding (when needed)

For briefs that name files, line numbers, or specific code anchors, ground them empirically before drafting. Don't assume documented filenames or line ranges are current.

Two precedents:

- **Source-review brief (Session 33)** — pre-flight VPS source-tree probe before drafting, capturing actual file inventory, line counts, supervision config, head-of-file scans. Goal: name files with grounded confidence.
- **Fix 3 brief (Session 36)** — VPS dirty-tree diagnostic before drafting, captured at `dr029/2_1_race_data/vps_drift_check.md`. Goal: surface working-tree state so the brief's hard limits cover real, current dirty regions rather than hypothetical ones.

When pre-flight is needed: surface to the operator that you're running it, run it via Desktop Commander against the live system (VPS via SSH, Mac filesystem direct, live DBs via `start_process` Python at canonical paths — never copy DB files), capture the findings to a referenceable doc if the brief will reference them, then draft.

When pre-flight is not needed: small surgical fixes against well-anchored prior reports (e.g. Session 35's Fix 1+2 brief drew anchors from the source-review report and didn't need fresh probing).

### Step 3 — Choose the brief's structural shape

Briefs share a universal section spine (see "Universal brief shape" below) but the per-brief structure varies. Anchor on the precedent closest to this brief's job:

- **Empirical inspection / measurement** — Session 28's §2.1 inspection brief is the template. Schema-discovery before measurement, time windows, stratification, measurement battery as named §-sections, output is tables-with-prose-scaffolding-only-no-conclusions.
- **Source-code review** — Session 33's source-review brief. Per-area sections each anchored on a specific finding from a prior report. Output is per-area assessment with effort scale + qualitative risk + dependencies, plus an overall read.
- **Surgical fix to a known issue** — Sessions 35 and 36's surgical-fix briefs. Named changes in dependency order, sequencing-within-session call, empirical verification queries pre-and-post, hard limits naming what's NOT in scope (other fixes, schema changes, the named pieces of debt).
- **Direct API or system observation probe** — Session 39's Saturday probe brief. Probe scope sub-sections (markets, time window, cadence, projection shape, rate-limit guard-rails, parallel streams), isolation rules, dedicated output directory, no-mid-probe-escalation discipline.

If the job doesn't fit cleanly into one of these shapes, ask the operator which precedent feels closest before drafting — this is a real decision, not a coin flip.

### Step 4 — Draft the brief in numbered sections

Write the brief end-to-end in one pass at first. Iterate after the operator review (Step 6). Don't try to perfect each section in isolation before moving to the next — the relationships between sections (anchors in one carrying through to verification queries in another) matter as much as the content within each.

The universal section spine, in order:

1. **What this brief is and is not** — measurement / fix / probe / review (named); single bounded Code session; surprises become findings, not blockers; remediation routes to operator-Claude triage, not Code's report.
2. **Why this work exists** — one paragraph linking back to the scope-doc item, prior report, or operator-surfaced finding that made this brief necessary.
3. **Pre-reads** — files Code reads before starting. Lean. Reference-only docs noted but not required-reads.
4. **System access** — VPS / Mac filesystem / live DB / Betfair API. Read-only or read-write explicit. Tunnel restart steps named if relevant. Adelaide local timestamps per DR-021 (timestamp anchoring, Adelaide local time).
5. **Substantive scope sections** — the per-brief shape from Step 3. Numbered §-sections each carrying anchors, named files / line ranges / SQL, and the questions or changes Code is commissioned for. Anchored, specific, no hand-waving.
6. **Sequencing within session** — order in which Code does the work, with dependency reasoning. When a different order would be operationally cleaner, say so and let Code deviate.
7. **Empirical verification** — pre-and-post baseline queries (for fixes) or success/failure criteria (for probes). Code captures both states so the report shows what moved.
8. **Output spec** — single named file at a specific path. Section structure for the report. Length anticipation (rough range, not hard line). What the report does not contain (no recommendations, no overall verdict if the brief is measurement; no scope creep into other fixes if the brief is surgical).
9. **Hard limits** — explicit list of what's NOT in scope. See "Discipline that travels" below; this section is non-negotiable.
10. **What happens after Code's session** — names the next operator-Claude session's triage shape: read the report, surface findings, route to next brief or close-out. Code does not produce the next brief; that's the next session's work.
11. **Cross-references** — the scope doc item, the DRs invoked, the prior report or session record this brief builds on, the parking-lot items the brief excludes.

Section count and titling can adapt — the Session 28 brief had 9 sections, the Session 39 probe brief had 12. Use the spine, don't fight it.

### Step 5 — Surface explicit calls made in the brief

Briefs encode decisions Claude made during drafting. Surface those decisions to the operator at hand-off so they're visible, not buried. Examples from precedent:

- Combine vs split related fixes (Session 35 — combined Fix 1 and Fix 2 into one Code session).
- Sequencing call counter to name-order (Session 35 — Fix 2 before Fix 1).
- Empirical determination over hard-coded values (Session 35 — Code queries `MIN(snapshot_time)` rather than the brief naming a date).
- Output as full report not just diff (Session 35).
- Wait for natural service restart vs manual restart (Session 36).
- In-session vs out-of-session verification carve-out (Session 36 — BSP only verifiable when a market actually transitions OPEN→SUSPENDED).
- Subsuming related probes into a broader brief (Session 33 — two separately-commissioned diagnostic probes folded into the source-review brief).

Surface as a numbered list at hand-off ("Calls I made in the brief, in case you want to redirect any"). Three to seven typical. Operator may accept all, redirect some, or push back on the structural shape — all three are valid responses.

### Step 6 — Operator review

Walk the brief section-by-section per the standing instruction in `standing_instructions.md` Category 1. One section, one round, wait for response. Don't dump the full brief into one message and ask "thoughts?" — that overwhelms.

Six review prompts surface naturally across the walk-through:

- (a) Discipline-rot watch on hard limits — does the no-remediation / no-scope-creep language hold the line firmly enough?
- (b) Pre-reads list — anything missing, anything excess?
- (c) Output spec — section structure tractable for next-session triage?
- (d) Sequencing — order makes sense or surfaces a better order?
- (e) Anything missing from the substantive scope sections that should land in this brief?
- (f) Length — does the brief feel right at this length, or should §-sections tighten?

If the operator says "go with your recommendations" (or close paraphrase) — Session 35 / Session 36 precedent — accept and lock the brief without working through the six prompts individually. The standing default is operator drives review depth, not Claude.

If the operator pushes back on shape (Session 39's three operator-driven pivots — Saturday timing reframed, projection rotation replaced with combined call, Racing API parallel stream added) — accept the redirection, redraft the affected sections, re-walk. Pivots like these are the operator doing their job; don't defend the first draft against substantive challenge.

### Step 7 — Lock the brief

Once operator approves, write the final brief to the rebuild folder via `Desktop Commander:write_file` or `projects-filesystem:write_file`. Verify post-write via `read_file` to confirm landed correctly (line count + spot-check on a key section). Capture line count, byte count, SHA256 prefix in the session record at close.

The brief is now the contract. Operator hands it off to Code in a separate out-of-session run.

### Step 8 — Forward routing for the next operator-Claude session

The next session reads Code's report, triages findings, decides next brief or arc-close. Surface this in the closing summary or in the session-close opening-prompt artefact. Naming the triage shape protects against drift — the next session knows what it's reading the report *for*.

## Universal brief shape

Every bethub-rebuild Code brief carries these elements regardless of type:

- **Numbered sections** with descriptive titles. The numbering is load-bearing — Code reads briefs end-to-end and the number anchors are the sturdy reference points (operator-Claude can later say "the §5.3 anchor" or "Code's §H finding" with no ambiguity).
- **Pre-reads**, lean. Required-reads listed first, reference-only docs noted but not required.
- **System access** named explicitly — read-only or read-write, what filesystem / DB / API, what tunnel or SSH path. Adelaide local timestamps per DR-021.
- **Substantive scope sections** with file references, line ranges, SQL queries, or specific questions. Anchored.
- **Empirical verification** — pre-and-post baselines for fixes, success/failure criteria for probes, expected output shape for inspections.
- **Output spec** — single named file at a specific path. Section structure named. Length anticipation. Explicit list of what the output does not contain.
- **Hard limits** — non-negotiable list of what's NOT in scope.
- **What happens after** — names the next operator-Claude session's job. Code does not write the next brief.
- **Cross-references** — scope doc item, DRs invoked, prior reports, parking-lot items excluded.

## Discipline that travels with every brief

These are non-negotiable. They appear in every brief, adapted to context but never omitted.

### Hard limits — what's NOT in scope

Brief §9 (or wherever the hard-limits section lands) names everything Code is forbidden from doing. The default exclusions:

- **Other fixes / scope items** — name them and exclude them. Session 35's brief named-and-excluded Fixes 3 and 4; Session 36's brief named-and-excluded the venue-harmonisation fix.
- **Schema changes** — for surgical fixes that don't intentionally change schema. Session 36 named-and-excluded schema changes despite touching `storage/database.py` (the fix added a dataclass field, not a column).
- **Named pieces of debt** — no test coverage, no migration framework, monolithic orchestrator file. These are tracked in the DR-029 close-out governance paragraph; surgical fixes don't try to fix them.
- **Remediation in measurement / inspection briefs** — Code reports findings, doesn't propose fixes. Session 28's brief was explicit on this.
- **Scope creep into other §2.x items** — same scope doc, different work.
- **Operator escalation mid-session** — for probes especially. Code runs end-to-end, surfaces findings in the report, doesn't ping operator-Claude mid-flight asking for direction.

### Single bounded Code session

Briefs explicitly state: this is a single Code session. If the work doesn't fit, that's a finding, not a continuation. Session 33's source-review brief named this in §7: "If review needs more than one Code session, Code surfaces that as a finding rather than continuing past budget. Partial-but-coherent review beats complete-but-lost-coherence."

### Named anchors only

Code edits only the file regions named in the brief. No drift into adjacent code "while we're here". Surgical-fix briefs (Sessions 35, 36) made this explicit. The discipline is what protects the dirty-tree state when present.

### Dirty-tree handling (when working tree is dirty)

If the system being modified has a dirty git working tree, the brief carries explicit hard limits on git operations:

- No `git add`, `git commit`, `git stash`, `git restore`, `git checkout` (file-targeted), `git reset`.
- Read working-tree state at session start.
- Edit only named anchors.
- After each edit, run `git diff <file>` to confirm only intended changes were added.
- At session close, run `git status` to confirm dirty file list unchanged.

Session 36's Fix 3 brief established this pattern. Pre-flight diagnostic captured the dirty-tree state at `dr029/2_1_race_data/vps_drift_check.md`; brief's §10 named the operator's in-flight work explicitly so Code knew the dirty regions weren't drift.

If dirty regions intersect the brief's edit anchors, the brief calls that out and either redirects the anchors or names the conflict for operator-Claude resolution before Code starts.

### Output spec — single file, structured, length-anticipated

Briefs name the exact output path (e.g. `dr029/2_1_race_data/inspection_report.md`), the section structure, and a rough length range. Code produces one file; operator-Claude reads one file in the next session. Multi-file outputs add coordination overhead with no benefit at this scale.

Length range protects against over-production (Code writing 1500 lines when 400 was expected) and under-production (Code writing 80 lines for a report that needed 300). Range, not hard line — Code reasonably exceeds when the work warrants it, but flagged in the report's self-assessment section.

### Output paths are absolute, anchored at the rebuild folder root

Every path the brief specifies — output report path, pre-read paths, anchor file paths, scratch paths — must be **absolute**, anchored at `/Users/tim/Desktop/Projects/bethub-rebuild/...` (or `/Users/tim/Desktop/Projects/bethub-v3/...` when the path genuinely lives in the v3 codebase, e.g. test files Code is editing). Never relative.

The failure mode this prevents: Code's working directory when executing build briefs is the v3 repo (`/Users/tim/Desktop/Projects/bethub-v3/`), because that's where it runs pytest, ruff, import-linter, and module edits. A brief that names its output as `dr029/w4_bet_entry/housekeeping_report.md` (relative) resolves at the v3 repo root, not the rebuild folder where the brief itself lives. The mirrored path inside the v3 repo (when one exists, or when Code creates it) means the path is *valid*, just pointing somewhere unexpected — silent mis-routing, no error message.

Substrate: Session 98 open ritual — Code shipped the housekeeping report at `bethub-v3/dr029/w4_bet_entry/housekeeping_report.md` instead of `bethub-rebuild/dr029/w4_bet_entry/housekeeping_report.md`. Caught at pre-flight directory listing (rebuild folder showed no report); recovery cost minutes, not hours, because the open ritual checks for it. Catching at brief-drafting prevents the mis-route entirely.

The discipline applies to:

- **Output report path** — the §8 (or wherever) named output file.
- **Pre-read paths** — every file in the §3 pre-reads list.
- **Anchor file paths** — every file referenced in §5 substantive scope sections.
- **Verification query paths** — DB files, log files, scratch files for empirical verification.
- **Scratch / temporary paths** — `/tmp/script.py` style paths are absolute by construction; the discipline still names them in full.

When a brief touches files genuinely inside the v3 codebase (test files, source modules, contract docs that live there), use `/Users/tim/Desktop/Projects/bethub-v3/...` absolute paths for those too. The point is unambiguity, not rebuild-folder favouritism.

### Read-only on databases unless explicitly read-write

Default is read-only. Read-write briefs (Sessions 35, 36 surgical fixes) name read-write access explicitly and limit it to the named anchors.

### Adelaide local timestamps per DR-021

DR-021 (timestamp anchoring, Adelaide local time) propagates from the brief into the report. Brief specifies Adelaide local timestamps (ACST/ACDT) for every time-of-day reference in the report.

## Operator review pattern

The Session 35 / Session 36 precedent: surgical-fix briefs and other tightly-anchored briefs often pass with "go with your recommendations" — operator delegates because the brief is grounded in a prior report they've already reviewed.

The Session 39 precedent: probe briefs and other scope-defining briefs benefit from real review and may need operator-driven pivots — section-by-section walk-through with a single section per round is the default cadence.

Default to walking the operator through section-by-section unless they signal "lock it" early. Don't dump the full brief into one message.

## Negative scope

This skill does not:

- Write governance documents (decisions.md amendments, DR drafts) — different artefact, different audience.
- Write session records or opening prompts — those have their own skills (`bethub-session-close`).
- Write operator-facing planning documents (the session_operations_proposal-shaped artefacts) — those are operator-Claude collaboration, not Code commissions.
- Lock briefs without operator approval. The brief is a contract; the operator signs it before hand-off.
- Generate the next brief ahead of Code's report. Each brief follows from the prior report; speculative chained briefs are scope drift.
- Cover non-bethub-rebuild work.

## Reference

Canonical source for the discipline encoded above:

- `standing_instructions.md` Category 3 (filesystem / tooling discipline), Category 4 (governance discipline), Category 5 (operator–Claude division of labour).
- `governance.md` (close-out protocol, multi-agent review pattern).
- Precedent sessions: 28 (§2.1 inspection brief), 33 (source-review brief), 35 (Fix 1+2 surgical brief), 36 (Fix 3 surgical brief), 39 (Saturday probe brief). Plus 29, 32, 34, 37, 38 (the operator-Claude triage sessions that read the resulting Code reports — useful precedent for what a triage session looks like that the brief is feeding into).

When this skill needs updating, the updates land here. Standing instructions and governance docs remain canonical for the cross-cutting discipline.
