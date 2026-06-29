# Governance review patterns

This file documents recurring governance review patterns for the v3 rebuild project. These are *processes for making decisions*, distinct from the architectural decisions themselves (which live in `decisions.md`).

**Created:** 2026-04-28 (Session 11)

---

## Multi-agent governance review pattern

**Status:** Established review pattern. First scheduled use: Session 14, assessing the data-layer-first sequencing decision (DR-029) and v3 data requirements doc (Session 12 sub-deliverable) before VPS data review begins.

### Why this pattern exists

Claude is a single point of failure in the architecture review. After many sessions of context, Claude becomes anchored on the v3 frame and may underweight or fail to surface concerns that an outside reader would notice. For decisions with high reversal cost or high blind-spot risk, a multi-agent review structure protects against this anchoring.

### When this pattern is used

**Used for:** decisions with high reversal cost or high blind-spot risk. Examples: data-layer-first sequencing (DR-029), build strategy (strangler-fig vs clean break), any DR that codifies discipline (DR-028 was a candidate but was reviewed informally in-session), schema-touching changes that affect prior locked slice work.

**Heuristic:** if Claude says "you should defer to me, this is a software call," that's a signal the decision may warrant a multi-agent review. Software calls are exactly where Claude's anchoring is most likely to be both load-bearing and invisible to Claude.

**Not used for:** routine slice work, vocabulary calls, schema field decisions where iteration with the operator is sufficient.

### Document suite (per review)

| Document | Author | Purpose |
|---|---|---|
| `architecture_current.md` | Claude (current session, or successor) | Descriptive: what's locked, what entities exist, what DRs apply |
| `data_layer_current.md` | Claude (current session, or successor) | Descriptive: what `capture.db` does today, fields, cadence, gaps |
| `decision_under_review.md` | **Operator + Claude collaborative** ("Claude asks, operator tells, Claude records") | Frames the question being assessed, current direction, concerns, alternatives considered. Operator-context-in-the-frame is essential. The collaborative pattern keeps operator-context in the framing while Claude does the recording overhead. |
| `open_questions.md` | Independent agent (fresh Claude session, ChatGPT, or Gemini) | Reads factual + decision documents, surfaces what hasn't been asked, what's been assumed without defence, what's been backgrounded that should be foregrounded |

### Assessment agents (three, independent)

| Role | Agent | Brief |
|---|---|---|
| Software developer | Claude Opus, fresh session, no project context | Technical assessment: soundness of design, integration risks, alternatives |
| Project manager | GPT-5 / GPT-5.1 or Gemini | Sequencing, scope, dependency, risk-management framing |
| Skeptic | Whichever non-Claude model wasn't used for PM | Stress-test the decision; explicitly instructed to challenge rather than validate |

Each gets the same document suite. Each produces an independent assessment.

**Mix model families.** Three Claude sessions share architectural priors and converge; cross-family diversity protects against this.

### Judge

Claude Opus, fresh session, given all three assessments and the document suite. Instructed to *synthesise rather than choose* — surface where the three agents agree, where they disagree and why, what recommendations emerge from the synthesis.

### Cadence and overhead

Multi-agent reviews have real overhead. Setting up four independent sessions, briefing each, collecting outputs, and synthesising is several hours of work per review. Reserved for high-stakes decisions; not run for routine work.

### Decision-under-review collaborative drafting

The `decision_under_review.md` document is drafted in a dedicated operator-Claude session prior to the review. Pattern: "Claude asks, operator tells, Claude records." This keeps operator-context in the framing (which Claude solo-authoring would filter out) while absorbing the writing overhead Claude can carry.

The drafting session uses a template with sections:

1. **What's being decided** — one paragraph in operator-language, not architectural-language.
2. **Why this is being reviewed** — what about this decision is high-reversal-cost or high-blind-spot-risk.
3. **Current direction** — bullet list of the proposed decision and its key components, descriptive not persuasive.
4. **Concerns the operator wants the assessors to weigh** — the honest list of what worries the operator about this decision. Most important section. Operator-authored content; Claude records.
5. **Alternatives considered** — brief list of what was on the table that didn't get chosen, and why each was set aside.
6. **What the operator wants the assessors to produce** — explicit ask: "tell me whether this is sound" vs "tell me what we might be missing" vs "stress-test this and find the failure mode" are different framings; the operator picks.

Target length: one to two pages. Long enough to frame the question fully, short enough that assessment agents can absorb it without losing focus.

### First scheduled use: Session 14

Assessing:

1. **DR-029 data-layer-first sequencing decision.** Whether the architecture pattern (review/extend the data layer to v3 fit-for-purpose before v3 build begins) is sound, whether the scope is right, whether the sequencing inside the review is correct.
2. **The v3 data requirements doc** (Session 12 sub-deliverable from the reconciliation contract write-up).
3. **The bet schema simplification question** (open question on DR-026 amendment and Slice 3 amendment): whether to drop inline snapshot storage and Slice 6 field_size captures in favour of full cross-DB resolution from capture.db.

Decision-under-review document drafted collaboratively in mid-Session-12 or Session-13.

---

## Session close-out protocol

**Status:** Process pattern. In effect from Session 12 onward.

### Why this pattern exists

Session 11's close-out ran approximately 30 minutes with one mid-run failure (`sessions/SESSION_11.md` left unwritten on the first pass; resolved ad-hoc). Two structural causes: (a) close-out was attempted at the end of an already-long session that had crossed major architectural ground, and (b) close-out itself was a sequence of five separate file operations with no atomicity — partial state on failure was the default, not an exception. A third near-miss: phantom work was nearly done on `system_snapshot.md` and `context_index.md` (v2 conventions) before catching that v3's deliberate governance scope does not include those files.

This protocol prevents those failure modes structurally rather than relying on attentiveness. The Session 11 lesson — *split rather than push through* — is the load-bearing principle; the rest is mechanics that make splitting cheap and pushing-through unattractive.

### 1. Pre-flight file-existence verification

Before any close-out work begins, Claude verifies what governance files actually exist in the rebuild folder rather than working from memory of v2 conventions.

The check runs as a single Desktop Commander `start_process` call listing the rebuild folder root and the `sessions/` subfolder. The output establishes the actual scope: which files are written to, which are appended to, which is the active session log being archived.

**v3's governance files (current scope):** `README.md`, `vision.md`, `architecture.md`, `decisions.md`, `governance.md`, `work_in_progress.md`, `session_log.md` (active), `sessions/SESSION_NN.md` (archive), `diagrams/` (separate folder).

**Files that do not exist in v3 and must not be created:** `system_snapshot.md`, `context_index.md`, `STATUS.md`, `CLAUDE.md`. These are v2 conventions. v3 is deliberately leaner. If close-out proposes touching one of these, the proposal is wrong, not the file list.

If a new governance file legitimately needs to exist (as `governance.md` did in Session 11), that is itself an architectural decision warranting an explicit DR-write or session-scope entry — not a quiet creation during close-out.

### 2. Hard session-length signals — split-and-resume by default

The default response to a long session is to split, not push through. The signals below trigger a split decision *before* close-out begins, while there is still context budget to do close-out cleanly.

**Trigger signals (any one is sufficient):**

- **Wall-clock duration** above ~3 hours of active session work, regardless of context window state.
- **Day-rollover** during the session (any session that crosses local midnight ACST).
- **Scratch revision** reaches v2 or higher — indicates the session has produced substantive scope that warrants its own close-out attention rather than being layered on top of further work.
- **Substantive scope change** mid-session — new DRs, amendments to prior locked work, new governance files. Session 11 hit all three of these and tried to push through; that is the failure mode.
- **Operator fatigue** signal — operator explicitly notes tiredness, decision-fatigue, or wanting to wrap.
- **Claude detects context budget tightening** — proactively raise a split, do not silently degrade.

**On a trigger, the response is:**

1. Stop the in-flight task at the current logical boundary (don't abandon mid-edit).
2. Capture remaining open items into the active `session_log.md` under "Open items carrying to next session."
3. Run the close-out protocol *now*, with full context budget for it.
4. Open the next session fresh for the carried work.

**Pushing through is the exception, not the default.** Push-through is appropriate only when the remaining task is genuinely trivial and the close-out is itself simple (no new DRs, no new files, no scratch promotion). Session 11's close-out met none of those conditions and tried anyway.

### 3. Scripted promotion via single Python script

When close-out involves promoting scratch content to canonical files (the Session 11 case — five files updated: `decisions.md`, `governance.md`, `work_in_progress.md`, `sessions/SESSION_05.md`, `sessions/SESSION_07.md`), the operations run as a single Python script via `Desktop Commander:start_process`, not as five separate tool calls.

**Script structure:**

```python
# scratch_promote.py — single-run, fail-loud
import shutil
from pathlib import Path
from datetime import datetime

REBUILD = Path("/Users/tim/Desktop/Projects/bethub-rebuild")
SESSION_N = NN  # set per session
TS = "YYYY-MM-DD HH:MM ACST"  # from system clock at script-write time

# 1. Backup every file to be modified to a temp folder, keyed by timestamp.
# 2. Apply all modifications in memory; write only after all succeed.
# 3. Move active session_log.md to sessions/SESSION_NN.md.
# 4. Verify each target file exists at expected size after write.
# 5. Print a manifest of what changed; non-zero exit on any failure.
```

**Properties the script must have:**

- **All-or-nothing.** Either every file is updated or none are. Partial promotion is the Session 11 failure mode.
- **Backups before writes.** Every target file is copied to `.close_out_backups/SESSION_NN/` before modification. Backups stay until confirmed clean by the next session's open.
- **Verification after writes.** Each target file's existence and approximate size is checked post-write. Mismatch fails the script loudly, not silently.
- **Idempotent re-run.** If the script fails mid-run, re-running it from clean state produces the same outcome. No "half-applied" detection needed because half-applied state is prevented by the all-or-nothing property.
- **Manifest output.** Final stdout is a one-screen manifest: which files were modified, line-count delta per file, archive-move confirmation.

The script is written fresh per session (the modifications differ each time) but follows this template. It is not committed as a permanent tool because the modifications are not parameterisable — each session's promotions are bespoke.

**For trivial close-outs** (no scratch promotion, just session_log archive + work_in_progress update), the scripted-promotion overhead is not warranted. The threshold: if close-out modifies more than two files, use the script.

### 4. Recovery procedure for partial-state failures

Despite §3's all-or-nothing property, failures still happen — script crashes mid-run, network or filesystem hiccup, operator interrupts. The recovery procedure assumes the worst case: governance files are in mixed state, the active session log may or may not be archived, backups may or may not be complete.

**Step 1 — Establish what state the world is actually in.**

Run a single Python `start_process` that:

- Lists the rebuild folder root and `sessions/` (what files exist).
- For each governance file in scope, reports last-modified timestamp and current line count.
- Confirms whether `.close_out_backups/SESSION_NN/` exists and what's in it.
- Confirms whether `session_log.md` (active) still exists and whether `sessions/SESSION_NN.md` exists.

Output is a state snapshot. Do not modify anything yet.

**Step 2 — Decide direction: complete forward, or roll back.**

- **Complete forward** when: most of the work is done, the remaining changes are well-defined, and re-running the failed step is straightforward.
- **Roll back** when: state is unclear, multiple files are in inconsistent shape, or the operator prefers a clean slate. Restore from `.close_out_backups/SESSION_NN/`, re-run the close-out script from scratch.

When in doubt, roll back. Rolling back is cheap; cleaning up half-applied state is expensive and error-prone.

**Step 3 — Execute the chosen direction, then verify.**

After completion: re-run the state-snapshot from Step 1. Confirm the world matches expectations (all target files modified, archive moved, active log gone). If the snapshot still shows mixed state, escalate to operator before proceeding.

**Step 4 — Document the failure briefly.**

Add a short note to the just-archived session log under a "Close-out notes" section: what failed, what recovery direction was taken, what to watch for at next session open. This is one paragraph, not a post-mortem.

### Pre-close-out checklist

Before invoking the close-out script, verify:

- [ ] System date confirmed via bash per DR-021 (already in the session-open routine but re-verified at close because sessions can span days).
- [ ] All in-flight tool calls completed; nothing in pending state.
- [ ] Pre-flight file-existence check (§1) run; target file list is correct.
- [ ] No phantom files in scope (`system_snapshot.md`, `context_index.md`, etc.).
- [ ] Scratch content (if any) reviewed and confirmed ready to promote.
- [ ] Open items list compiled — what carries to which future session.
- [ ] Close-out script written, dry-run mentally, target file list matches §1's check.

If any checklist item is uncertain, the right move is to surface the uncertainty, not to proceed.


---

## Future review patterns

Other review patterns may be added to this file as they are established. Examples that have been discussed but not yet formalised:

- **Per-extension governance check** during DR-029 data review execution: scope, expected impact on `capture.db` schema, expected impact on the data API contract, expected impact on v3's `vps_client` interface — before each significant change.

These will be documented here when they enter active use.


---

## Final data-layer lock review (DR-029 close-out)

**Anchored:** 2026-05-04 ACST. Closed Session 78.

The data-layer fit-for-purpose review established by DR-029 (the
data layer is reviewed and brought to v3 fit-for-purpose before
v3 build begins, locked Session 11 / 2026-04-28) is closed. Both
integration-module contracts are locked at v1.0 — `vps_client`
(the read interface against `capture.db`, anchored on §2.6 §5.1
plus §2.9 §6.1) and `betfair_client` (the operational interface
against the Betfair Exchange and Streaming APIs, anchored on
§2.4 plus §2.6 §5.1 plus §2.9 §6.1 plus §2.7 §3). Versioning
discipline is locked at §2.7 (path-based, per-surface bumping,
backward-compatible additions in-place, breaking changes via
new version only, 90-day deprecation window provisional).

The gate is cleared. v3 build proper is unblocked.

The arc ran across Sessions 11–78 with active execution from
Session 27 onward (DR-029 scope locked) through Session 78
(contract documentation files locked v1.0). The remaining items
captured in Sections 4 and 5 below are non-gating — debt and
deferred capability carried forward by deliberate choice, not
unfinished review work.

### What DR-029 set out to do

DR-029 was locked Session 11 (2026-04-28) as the gate between v2
operational state and v3 build proper. The decision rested on
two named risks surfaced during Slices 1–6 scoping work:

- **Discipline rot at build time** — under bet-logging pressure,
  the path of least resistance could be to add ad-hoc capture or
  denormalisation in v3 in violation of DR-028 (the cross-database
  integration boundary discipline). Locking the data layer first
  makes that path-of-least-resistance unavailable structurally.

- **Building against a moving contract** — v3 building while
  `capture.db` is itself being extended for v3's needs (sports
  markets, NZ, cadence tuning, BSP coverage) produces integration
  bugs that compound. Sequencing the contract lock before v3
  build eliminates the moving-target failure mode.

The review's lock target was a **versioned and documented
contract**, not a feature-complete schema. Locked v1.0 means
contract shape and versioning discipline are settled — the call
signatures, the data shapes returned, the staleness and
unavailability signals, the schema-evolution policy. It does
not mean the field set is exhaustive or the schema is frozen
against future additions. Backward-compatible additions to the
contract remain available as workflow validation surfaces new
needs during v3 build proper.

Two architectural anchors framed the review's scope. **DR-027**
(the two-database architecture decision) splits operational
state — owned by v3's operational store — from analytical /
source data — owned by `capture.db` on the VPS. **DR-028** (the
cross-database integration boundary discipline) forbids caching,
denormalisation, and second integration points across that
boundary, allowing only reference-by-identifier as the cross-DB
join mechanism. Both DRs hold load-bearing throughout the
contracts locked here — the one-file boundary at `vps_client`
is DR-028 made operational; the read-only-against-capture
posture is DR-027 made operational.

A third architectural axis — operational vs analytical line
discipline (Cat 4 of standing instructions) — runs through
every contract surface. The operational line is `betfair_client`
direct: live pricing, bet entry, real-time burst-window state.
The analytical line is `vps_client` against `capture.db`: BSP
archives, market-curve bracketing, post-hoc review, model
calibration. The two lines query the same Betfair API at
different cadences, consistent by construction modulo lag. The
asymmetry — racing has both lines, sports has operational-only
— is locked architecturally rather than emerging accidentally.

### What was actually delivered

Pointer-only summary. Per-stream detail lives in the dr029/
folder's per-§ artefacts and in `decisions.md`; this section
records the closure list, not the substance.

- **§2.1 Race-side data fit-for-purpose verification** —
  closed-with-known-debt-named Session 34 after empirical
  source-review against `capture.db`. Surgical-fix arc executed
  Sessions 35–37 (Fixes 1+2 result-population + nightly-backfill
  rework; Fix 3 BSP / sp_near / sp_far write-back). Saturday
  2026-05-02 API observation probe ran direct against the Betfair
  `MarketBook` API to resolve the post-suspension SP-trading
  question Fix 3 left empirically inert; probe results land into
  Fix 4 (cadence design) and §2.10 (external analytics scan) as
  non-gating quality work. Fix 5 (venue harmonisation +
  retroactive race-key merge) and Fix 4 (cadence brief drafting)
  carry forward as named non-gating items per Section 5.

- **§2.2 Sports operational layer — Betfair direct** — closed
  Session 38. Specified into `architecture.md` under the
  `## Operational layer — Betfair direct` section (B.0 framing
  plus B.1.1–B.1.7 sports subsections covering sports page
  source, bet entry via operator-typed line + 11-line ladder,
  favourite inference for handicap markets, auto-settlement with
  Betfair-direct canonical and public-archive fallback at 90
  minutes, sports bet record shape, SGM and specialist markets
  out-of-scope v3-day-one, cadence note tracked-and-open).

- **§2.3 Periodic-only API pattern reframed on operational vs
  analytical axis** — closed alongside §2.4. The pattern is
  reaffirmed for the analytical consumer path (`vps_client`
  against `capture.db`) and explicitly carved out for operational
  consumers, which use the Streaming spec at §2.4 instead.

- **§2.4 Betfair Streaming spec** — closed in
  `dr029/2_4_betfair_streaming/`. Connection lifecycle,
  authentication, subscription patterns (market data + order
  subscription on one connection), reconnection behaviour,
  message handling, rate-limit handling, cache shape. Cadence
  parameters (subscribe interval, reconnect backoff, heartbeat
  threshold) deferred to Fix 4 — the spec is the connection
  shape, not the timing.

- **§2.5 Soft-book operational layer** — deferred Session 69.
  See `dr029/dr029_scope.md` §3.11 for the formal deferral and
  Section 5 below for the trigger conditions on returning to
  scope. v3 day-one ships with typed-price entry only; no
  `softbook_client`, no live soft-book read, no operational
  soft-book layer.

- **§2.6 Settlement model — race path** — closed Session 74.
  Two-source agreement discipline (Betfair Win + Racing API
  result, finalised vs provisional). Sports path re-specified
  per principle 1.3 of the scope doc (Betfair-direct canonical,
  public-archive fallback) and locked alongside §2.2.

- **§2.7 API contract versioning** — closed Session 75.
  Path-based versioning, per-surface bumping, backward-compatible
  additions in-place, breaking changes via new version only,
  90-day deprecation window (provisional v1.0 default; revisit
  triggered on first observed migration friction). Both
  contract documentation files (`vps_client_contract.md` +
  `betfair_client_contract.md`) locked v1.0 complete Session 78
  after operator-Claude triage of the Session 77 Code report.

- **§2.8 Bet-schema reframing on operational vs analytical
  axis** — closed Session 72. Minimal at-placement decision-context
  fields stored on the bet record (immutable); everything else
  resolved at read time via `vps_client` analytical reads or
  `betfair_client` for current-market reference. Soft-book
  typed-price path absorbed Session 69 from former §2.5.

- **§2.9 Write-side bet-entry coherence** — closed Session 73.
  Three surfaces specified: sports line specification at bet
  entry, placement-time sanity check, identifier-resolution
  sanity check (passive boundary check at first analytical-line
  read, framed as `capture.db` ingestion-fault surface).

- **§2.10 External analytics environmental scan** — closed
  Session 76. Time-boxed scan of fields available but not
  currently captured. Three buckets per the scope: bucket 1
  (cheap-capture additions worth pulling — backward-compatible
  additions to `betfair_client` and `vps_client` per §14.4 of the
  Betfair contract), bucket 2 (expensive or upstream-blocked,
  parked with re-evaluation triggers), bucket 3 (already
  captured, no action).

The contract documentation files (`vps_client_contract.md` and
`betfair_client_contract.md`) were drafted Session 77 (operator-
readable summaries §§1–6) and Session 77 Code (developer-readable
specs §7+ via the `contracts_spec_brief.md` Code-bound brief),
then triaged and locked v1.0 Session 78. The two files are the
load-bearing artefacts of the gate clearance; everything else in
this section is the substrate that fed into them.

### The three pieces of named debt being carried forward

DR-029 explicitly cleared the gate **with known debt named**.
The closure call at Session 34 (the §2.1 close) named three
pieces of structural debt that were not blockers to gate-
clearance but are real and operationally visible. Each is named
here so v3 build proper inherits the debt knowingly, not
silently.

#### Debt 1 — No test coverage

The current data-layer pipeline (`capture.db` ingestion, the
scrapers, the orchestrator file, the `vps_client` consumer paths
in v2) has no automated test coverage. v2 was built fast under
operational pressure; tests were never added. The data-layer
review confirmed empirically that the pipeline behaves correctly
in practice (Session 18's check that v2's `capture.db` SSH
tunnel had been unreachable for six days with zero operational
impact is the most pointed example), but "behaves correctly in
practice" and "is verifiably correct against a regression test
harness" are different operational postures.

**Why it didn't block gate-clearance.** The contract surfaces
are locked structurally, the boundary discipline is locked
structurally, and the typed-envelope unavailable enumeration
forces v3 modules to handle every failure mode the pipeline can
produce explicitly. Test coverage protects against regression
across change events; the data-layer is changing slowly enough
post-DR-029 that absence of tests is a quality concern, not a
correctness concern.

**What triggers it returning to scope.** First scheduled
operational change to the pipeline that touches a load-bearing
surface (e.g. Fix 4 cadence design lands, or the §2.10 bucket-1
field captures land) — at that point a regression test harness
becomes load-bearing for the change itself, and adding the
harness is the natural sequencing. Tests are not a separate
backlog item; they ride alongside the next significant pipeline
change.

#### Debt 2 — No migration framework

`capture.db` schema changes (additions, refactors, retirement)
have no migration framework. Today's operational pattern is
manual SQL applied via Desktop Commander start_process, with the
operator and Claude reviewing each change pre-flight. The
pattern works at current change cadence (low; bounded by §2.7's
versioning discipline) but does not scale to higher-frequency
change.

**Why it didn't block gate-clearance.** §2.7's versioning
discipline (path-based, per-surface bumping, backward-compatible
additions in-place) is the protective layer — `capture.db`
schema additions are backward-compatible by default, breaking
changes route to a new contract version, and migration scope is
small per change. The absence of an automated framework is a
manageable manual cost at v3 day-one's expected change cadence,
not a structural blocker.

**What triggers it returning to scope.** Either of: (a) two
breaking-change cycles run within a 90-day window, indicating
the manual pattern is straining; or (b) v3 build proper surfaces
operational reasons to extend `capture.db` more frequently than
expected. Both are observable triggers — the operator and Claude
will see the friction before the pattern breaks down.

#### Debt 3 — Monolithic orchestrator file

The VPS-side orchestrator file (`racing-data-capture/orchestrator.py`
and adjacent files) is large and monolithic. Code's source-review
report at `dr029/2_1_race_data/source_review_report.md` confirmed
the file is **coherent** despite its size — internal contracts
compose cleanly, scrapers tidy, storage layer clean — which is
why surgical-fix routing was chosen over rebuild routing at
Session 34. But "coherent monolith" is still a monolith, and
future operational work against it carries higher cognitive cost
than against a properly factored layout.

**Why it didn't block gate-clearance.** The boundary that
matters for v3's correctness is `vps_client`'s contract against
v3's modules, not the internal organisation of the VPS-side
orchestrator. v3 reads `capture.db` through the locked contract;
how `capture.db` is populated upstream is an operational
concern, not a v3-build concern.

**What triggers it returning to scope.** The first operational
change that touches three or more orchestrator-file regions in
a single brief — at that scale, factoring the file into separate
modules pre-change is cheaper than navigating the monolith
during the change. Smaller surgical fixes (one or two regions)
remain viable against the existing structure.

These three pieces are named to v3 build proper as **inherited
known debt**. They are not regrets. They are the deliberate
choice the gate-clearance call made: clear the gate now, carry
the debt forward visibly, return to each piece on a defined
trigger rather than letting any of them silently expand into
larger problems.

### What's deferred — and what triggers each returning to scope

Distinct from the named debt in Section 4, this section captures
capability that DR-029 deliberately did not build. Each item is
a shape the architecture explicitly leaves room for; none is
gating v3 build proper.

#### Deferred capability 1 — Operational soft-book layer (§2.5)

Deferred Session 69 per `dr029/dr029_scope.md` §3.11. v3 day-one
ships with typed-price entry only — operator types the price
they took at the soft book, v3 records it. No `softbook_client`
module, no live soft-book read.

**Why deferred, not built.** Soft-book operational live pricing
is not one feature. It is several distinct consumer surfaces —
best-promo-odds for racing insurance (Strategy 1), best-odds for
general turnover, multi-book scan for price boosters (Strategy
2), SGM-correlated views for Strategy 3, same-race-multi views
for emerging strategies — each wanting a different aggregation,
a different operator surface, a different consumer workflow.
The strategies that would dictate those surfaces are still being
discovered through running operations. Specifying an interface
contract before consumer surfaces are known means guessing at
shape — exactly the v2-shaped over-engineering DR-029 exists
to prevent.

**Trigger conditions for returning to scope** (any of the
following surfaces a fresh DR scoping the operational soft-book
layer):

- Strategy 2 (Price Booster) volume reaches a level where multi-
  book scan is operationally useful rather than aspirational.
- Strategy 3 (Correlated Friction) begins running and surfaces
  concrete same-game-multi pricing surface requirements.
- Strategy 4 (Synthetic Each-Way) execution begins and surfaces
  concrete value-betting price-comparison requirements.
- Operator surfaces a different concrete requirement from running
  operations.

BetWatch parallel-track vendor research carries forward as
operator-side homework informing the future DR. No longer gating.

#### Deferred capability 2 — §2.10 bucket-2 re-evaluation

The §2.10 external analytics scan separated cheap-capture
candidates (bucket 1, integrated into the contracts as
backward-compatible additions) from expensive or upstream-
blocked candidates (bucket 2, parked with re-evaluation
triggers). Bucket 2 items are not built into v3 day-one but are
named with the conditions under which they'd return to scope.

**Trigger conditions per bucket-2 item.** Logged in the §2.10
brief; substrate carries forward as a discrete open item. The
load-bearing discipline is that bucket 2 is **explicitly** the
deferral bucket, not an implicit "we forgot about these"
backlog. Re-evaluation runs when the named trigger surfaces, not
on a calendar cadence.

#### Deferred capability 3 — Fix 4 cadence design

**Closed Session 113.** Brief drafted Session 112, calibrated
by Code, report triaged Session 113. Six `streaming.py` cadence
constants locked at §-section citations; `_connection.py`
rate-limit defaults verified within Betfair's documented
ceilings. Detail in Sessions 80–81 (probe + trade-off
resolution), 112 (brief), 113 (triage); artefacts at
`dr029/2_4_betfair_streaming/fix_4_cadence_calibration_brief.md`
and `…_report.md`.

#### Deferred capability 4 — Fix 5 venue harmonisation

**Closed Session 46.** Detail in Session 46 record.

#### Deferred capability 5 — Periodic data-layer fitness re-verification

The gate cleared by DR-029 is "fit for purpose at this point in
v3's lifetime", not "fit for all time". v3's operational
requirements will evolve as strategies mature, as bookmaker
relationships shift, and as new data sources surface. The
contracts' versioning discipline (§2.7) handles incremental
change; periodic fitness re-verification handles structural
drift.

**Trigger conditions for re-verification.** Any of: (a) twelve
months elapsed since DR-029 close (calendar trigger — earliest
re-verification 2027-05-04 ACST); (b) two or more contract-
surface version bumps within a 180-day window, indicating the
data layer is changing structurally rather than incrementally;
(c) v3 build proper surfaces a v3-side requirement that the
contracts cannot serve via backward-compatible addition.

The re-verification is a fresh DR-029-style review, not a
refactor — assess fitness against current v3 requirements,
identify any gaps, scope the resolution, lock the next-version
contracts.

#### Deferred capability 6 — Race-level consolidated EV (post-v3 analytics)

Raised Session 109 (2026-05-08). Post-v3 analytics enhancement
sitting in the P1/P2 post-build analytics band of the v3 build
picture. BetHub today shows EV per individual bet; on multi-promo
days where the operator places multiple bets on the same race,
the per-bet view hides the race-level picture — combined exposure,
outcome shape, worst-case and best-case net P&L, per-runner
sensitivity (if runner X finishes 1st/2nd/3rd, where does the
combined position land). The per-runner sensitivity is the
operationally load-bearing piece — it supports live decisions when
the market moves on a fourth runner and the operator needs to
read existing exposure shape before adding more.

**What it is, framed correctly.** Portfolio construction over a
race, not a hedging recommender — the operator stacks positive-EV
bets that share a race, and variance reduction is a side effect
rather than the goal. Each bet stands on its own EV merit at
entry; the consolidator describes the combined position after
the fact. The maths is arithmetic on top of probabilities the
calibrated Harville already produces — no new modelling required.
Same maths family as Strategy 3 (SGM correlated friction); shared
infrastructure question is open for future scoping.

**Why deferred, not built.** Three reasons. (a) v3 build picture
is locked on operational core; this is analytics, post-build.
(b) Depends on calibrated Harville exponents — exponent fitting
is an outstanding workstream against the harville_calibration.csv
substrate. (c) Natural fit for the post-build analytics scan once
v3's data model has stabilised under live load.

**Trigger conditions for returning to scope** (any of the
following routes the build-out):

- Calibrated Harville exponents land (the dependency clears).
- v3 data model proves stable in production after first weeks of
  operational use.
- Operator runs a multi-promo-on-one-race day and surfaces a
  concrete pain point the per-bet view doesn't address.
- Strategy 3 SGM correlation work activates and the shared-
  infrastructure question forces a routing decision.

Open scoping questions captured: does v3 data model already key
bets to a race ID, or is that an inferred join (horse + meeting +
date)? Does the existing promo evaluator handle position-conditional
payout logic, or does it assume win/place binary? Is this a live-
session dashboard, a post-race review tool, or both (affects
performance budget)? Interaction with Strategy 3 SGM work — shared
infrastructure or parallel builds?

#### Deferred capability 7 — Audit-trail surface for settlement transitions

Raised Session 109 (2026-05-08) at W8 triage. The §2.6
settlement-race contract specifies that manual provisional →
terminal-state transitions should be audit-trailed alongside
whatever the settlement-read state was at the time of operator
action, so post-hoc review can reconstruct what the operator saw
and what they decided. W8 v1 ships the operator-action half of
this contract but not the queryable-history half: the operator's
reason text and transition timestamp are emitted to the worker
logger as INFO lines, the bet record's `last_reconciled_at` and
`reconciliation_attempts` counters update via the shared
bookkeeping substrate, but there is no audit table, no per-
transition history, no per-action operator ledger.

**What's missing in two pieces.** First, a persisted record of
every settlement transition (auto or manual) with operator reason
when manual, transition source state, target state, timestamp.
Second, a persisted snapshot of the worker's last MarketSettlement
read on the bet record — which is currently impossible because
the W6.5 ship doesn't persist `last_read_market_state` on the
bet record (the API surfacing payload field is always None at
v1). Closing the contract therefore needs a W6.5-side substrate
change as well as the new audit table; it is not a single-file
cleanup brief.

**Why deferred, not built.** v3 day-one ops works without it.
The worker log file is the v1 substrate for "what did I do and
why?" — queryable by grep rather than SQL. Whether that gap
actually bites operator workflow only resolves under real ops
use. Closing the gap before feeling it is the literal shape of
premature optimisation: the operator doesn't yet know which
shape of audit query they'll actually want, and the brief that
closes the contract reaches across two named anchors (audit
table + W6.5 substrate change) — better scoped with concrete
operator pain in hand.

**Trigger conditions for returning to scope** (any of the
following routes the build-out):

- First ops cycle in which the operator reaches for transition
  history and the log file substitute proves insufficient.
- A specific reconciliation question surfaces post-hoc that
  needs the settlement-read snapshot to answer.
- A second contract-surface change to the bet record forces
  revisiting `last_read_market_state` persistence regardless,
  at which point the audit table piggy-backs cheaply.

The current substrate is the W8 ship plus worker INFO logs in
`logs/worker.log` (or wherever the LOG handler is routed in the
deployed config). That is the operational substitute until a
trigger condition lands.

### Closing

DR-029 closes here. v3 build proper is the next arc — the
build picture in `v3_build_picture.md` re-cuts from DR-029
streams to v3 build workstreams (data layer, operational core,
live pricing, settlement, analytics, session ops) at the next
session that opens v3-build-proper work. The contracts locked
this session are the load-bearing artefacts the build executes
against; the named debt and deferred capability above are the
material the operator and Claude carry into v3 build with eyes
open.


---

## Open and close-out economy (added 29-April by Tim)


**Standing directive — open and close-out economy.**

**Principle.** The rebuild folder is the source of truth. `work_in_progress.md`, `sessions/SESSION_NN.md`, `decisions.md`, and `governance.md` carry persistent state. Opening prompts and close-outs are pointers to those files, not summaries of them. Restating file contents in conversational text is duplication — it costs context, it costs operator reading time, and it drifts from the canonical source.

**Opening prompts — format.** The next-session opening prompt produced at close-out is a pointer document. Target length ~150 words. It contains, in order:

1. One line: session number, anchor-time directive (DR-021), pre-flight directory listing directive.
2. One line: ordered list of files to read. No descriptions, no line counts, no per-file summaries — the files describe themselves.
3. One line: which DRs to focus on within `decisions.md`, if any.
4. One line: "Honour all standing instructions in WIP." Do not restate them.
5. Session scope in order, one line per item. No re-justification of choices already locked.
6. Stop-early condition if applicable.
7. Backup-cleanup directive for the prior session's backup folder.

What an opening prompt does **not** contain: restatements of standing instructions, document descriptions, locked-decision recaps, multi-paragraph narrative context, or open-item lists across 3+ future sessions. Standing instructions live in WIP. Locked decisions live in `decisions.md` and the prior `SESSION_NN.md`. Future open items live in WIP's open-items section. The opening prompt points; the files inform.

**Close-out narration — format.** During close-out:

- One line before any multi-edit pass naming the edits planned ("Applying N edits to WIP: [list]").
- One line after the pass confirming completion and verification ("All N applied; verifying.").
- No per-edit running commentary. No restatement of what each edit changed — the edits themselves are the record.
- State-snapshot diagnosis: maximum two sentences. Decision and action, not reasoning out loud. Detailed reasoning belongs in `SESSION_NN.md` if it's worth preserving.

**Closing summary — when to omit.** If an opening prompt for the next session has been produced, do not also produce a closing summary covering files written, backups taken, and items carrying forward. Pick one artifact. The opening prompt is canonical because the next session consumes it; the closing summary is read once. Operator may request a closing summary explicitly; otherwise omit.

**Standing-instruction additions.** When a new standing instruction is added to WIP during a session, the opening prompt for the next session does not quote it. The next session reads WIP. The only exception: if the new instruction changes how the opening prompt itself should be interpreted (rare), flag its existence in one line ("New standing instruction at WIP §X — read before proceeding").

**Operator override.** The operator may at any time request a longer opening prompt, full closing summary, or verbatim restatement of standing instructions for a specific session. This directive sets the default, not a ceiling.
