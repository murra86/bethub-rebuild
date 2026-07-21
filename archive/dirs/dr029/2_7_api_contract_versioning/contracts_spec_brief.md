# Brief: contract documentation files — developer-readable specifications

**Status:** drafted Session 77 (2026-05-04 ACST).
**Output paths:**
- `dr029/2_7_api_contract_versioning/vps_client_contract.md` (append §7+)
- `dr029/2_7_api_contract_versioning/betfair_client_contract.md` (append §7+)
**Spec sources (all locked, all on disk):** §2.6 brief, §2.7 brief, §2.9 brief, §2.4 brief.
**Governing DRs:** DR-027, DR-028, DR-029, DR-021.

---

## §1 — What this brief is and is not

**What it is.** A transcription brief. Code reads the locked §2.6 / §2.7 / §2.9 / §2.4 specs and the two existing operator-readable summaries (`vps_client_contract.md` §§1–6 and `betfair_client_contract.md` §§1–6, both on disk), and drafts the developer-readable formal specifications (§7 onward in each file) against those locked shapes.

**What it is not.** Not a design brief. Code does not invent contract surfaces, error semantics, parameter lists, or return shapes. Every typed shape in the developer-readable spec traces back to a named anchor in §2.6 §5.1, §2.7 §2 / §3, §2.9 §6.1, or §2.4. Surprises (a contract surface in the operator-readable summary that has no clear anchor in the locked specs, an inconsistency between two sources, a gap that needs operator-Claude resolution) are findings — Code surfaces them in the report, doesn't resolve them mid-flight.

**Single bounded Code session.** If the work doesn't fit one Code session, that's a finding, not a continuation. Partial-but-coherent beats complete-but-lost-coherence (Session 33 precedent).

**Remediation routes to operator-Claude triage.** Code does not edit the operator-readable summaries (§§1–6 in either file). Code does not edit the locked spec briefs (§2.4, §2.6, §2.7, §2.9). Code appends below the §7+ placeholder in each file and nothing else.

---

## §2 — Why this work exists

Per §2.7 §4.4, each contract documentation file is a single source of truth with two audiences: an operator-readable summary at the top (already drafted Session 77, on disk) and a developer-readable formal specification below. The developer-readable spec is what v3 build proper will read when implementing against the contract, and what future Code sessions will read when adding to or migrating between contract versions.

The two files are required artefacts before v3 build proper begins (per §2.7 §5.4 and DR-029 critical path). After this brief lands, only the DR-029 close-out governance paragraph remains before v3 build proper can start.

The work is transcription rather than design because §2.6 / §2.7 / §2.9 / §2.4 already locked every contract surface, every reason enumeration, every typed envelope shape. Code's job is to render those locked shapes in the formal-spec format that v3 build will consume — Pydantic models (or equivalent), endpoint definitions, full parameter and return-shape specs, full reason-enumeration definitions, Streaming connection lifecycle.

---

## §3 — Pre-reads

Required reads, in order:

1. `dr029/2_7_api_contract_versioning/2_7_api_contract_versioning.md` — §2.7 brief, the versioning discipline source. Especially §2 (`vps_client` v1.0), §3 (`betfair_client` v1.0), §4 (schema-evolution policy).
2. `dr029/2_7_api_contract_versioning/vps_client_contract.md` — operator-readable summary (§§1–6) drafted Session 77. The developer-readable spec must be consistent with what §§1–6 describe.
3. `dr029/2_7_api_contract_versioning/betfair_client_contract.md` — same.
4. `dr029/2_6_settlement_model/2_6_settlement_model.md` — §2.6 brief. Especially §5.1 (settlement-read contract specification — five fields plus three count fields).
5. `dr029/2_9_write_side_coherence/2_9_write_side_coherence.md` — §2.9 brief. Especially §6.1 (`vps_client` and `betfair_client` v1.0 contract surfaces — sports-line query, marketTime read, identifier resolution).
6. `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` — §2.4 brief. Streaming connection shape; cadence parameters are out of scope (Fix 4).

Reference-only — read on demand:

- `architecture.md` §D12 (Betfair as canonical source).
- `decisions.md` DR-027 / DR-028 / DR-019.
- `external_api_resources.md` for Betfair API and Racing API resource pointers.
- `dr029/2_8_bet_schema/2_8_bet_schema.md` for the resolved-at-read derivation discipline (relevant to vps_client out-of-scope §3).

---

## §4 — System access

**Filesystem:** Mac filesystem direct via Desktop Commander. Read-write on the two contract documentation files only. Read-only on every other file.

**Databases:** none. This brief is documentation transcription; no DB queries needed.

**External APIs:** none. The Betfair API and Racing API are referenced in the locked specs; Code reads what the specs say about them, doesn't call them.

**Timestamps:** Adelaide local time per DR-021. The version history table in each file gets a row for this Code session — date format `YYYY-MM-DD`, session tag `Session 77 Code` or equivalent.

---

## §5 — Substantive scope: vps_client developer-readable specification

Append below the `## §7+ — Developer-readable specification` placeholder in `vps_client_contract.md`. Replace the placeholder italic text with the spec proper.

### §5.1 Section structure

The developer-readable spec has these sub-sections, in order:

- **§7 — Overview.** Tech-stack assumption (Python / Pydantic or equivalent). Boundary discipline reminder (one file owns capture.db schema). How developers should read this section.
- **§8 — Typed envelope.** The `fresh / stale / unavailable` envelope shape. Pydantic model (or equivalent). Reason enumeration as a typed enum. Retry-after hint field. Lag indicator field.
- **§9 — Call surfaces (one sub-section per surface).** Six sub-sections per the operator-readable §2:
  - §9.1 Race metadata reads
  - §9.2 Runner metadata reads
  - §9.3 Results reads
  - §9.4 Bracketing reads
  - §9.5 BSP / sp_near / sp_far reads
  - §9.6 Identifier-resolution reads
- **§10 — Versioning mechanics.** Path-based versioning (`/v1/...`). Per-surface version bumping. How v2 surfaces are added. Deprecation warning emission discipline.
- **§11 — Out of scope.** Five categories per operator-readable §3, with formal-spec-level framing (e.g. why no write methods exist on the module, why no sports surfaces exist).

### §5.2 Per-surface format (each §9.x sub-section)

Each call surface sub-section carries:

- **Endpoint path** under `/v1/...`.
- **Call signature** — the Python function name, parameter names with types, return type.
- **Parameter spec** — for each parameter, type, semantics, validation rules, defaults if optional.
- **Return shape** — the Pydantic model (or equivalent) the surface returns. Field-by-field: name, type, semantics, nullability.
- **Failure modes specific to this surface** — which envelope statuses and which reason values apply, with semantics for each. Not every reason applies to every surface; spec the ones that do.
- **Example call and response** — one realistic example per surface, showing call shape and the three envelope statuses in turn.

### §5.3 Anchors

Every typed shape traces back to a named anchor:

- §9.1 Race metadata: §2.9 §6.1 (vps_client contract — race-level fields keyed on Betfair event identifier).
- §9.2 Runner metadata: §2.9 §6.1 same.
- §9.3 Results: §2.9 §6.1 + §2.6 §5.1 for the Betfair-side comparison shape.
- §9.4 Bracketing: §2.9 §6.1 (analytical bracketing reads).
- §9.5 BSP / sp_near / sp_far: §2.9 §6.1 + §2.10 §2 (BSP fix landing zone).
- §9.6 Identifier resolution: §2.9 §6.1 surface (c) — passive sanity check.

If an anchor is missing or ambiguous, that's a finding (per §11 below).

---

## §6 — Substantive scope: betfair_client developer-readable specification

Append below the `## §7+ — Developer-readable specification` placeholder in `betfair_client_contract.md`. Replace the placeholder italic text with the spec proper.

### §6.1 Section structure

- **§7 — Overview.** Tech-stack assumption. Boundary discipline reminder (one file owns Betfair API shape; reads and writes share the module per DR-028). Decoupling from Betfair's own versioning.
- **§8 — Typed envelope.** Same envelope shape as vps_client; reason enumeration extended with Betfair-specific reasons. Read-side and write-side reason enumerations spec'd separately (`betfair_*` vs `betfair_write_*` prefixes).
- **§9 — Read surfaces.** Five sub-sections:
  - §9.1 Operational live-pricing reads
  - §9.2 Settlement reads
  - §9.3 Sports-line query
  - §9.4 Scheduled-time reads
  - §9.5 Identifier-resolution checks
- **§10 — Streaming surface.** §2.4 connection shape. Subscribe / message dispatch / reconnect / heartbeat. Cadence parameters NOT spec'd (Fix 4).
- **§11 — Write surfaces.** Three sub-sections:
  - §11.1 Bet placement
  - §11.2 Bet cancellation
  - §11.3 Bet replacement
- **§12 — Audit-trail discipline.** Structured log entry shape for every write-surface call. Field-by-field. Where the log lands.
- **§13 — Streaming-disconnect-blocks-writes behaviour.** How `betfair_client` enforces it. What v3 sees when blocked.
- **§14 — Versioning mechanics.** Same shape as vps_client §10 plus the Betfair-side decoupling note (most Betfair churn absorbed inside the module without versioning event).
- **§15 — Out of scope.** Five categories per operator-readable §3.

### §6.2 Per-surface format

Same as §5.2 above. Read surfaces, streaming surface, and write surfaces all use the same per-surface format — endpoint path, call signature, parameter spec, return shape, failure modes specific to this surface, example call and response.

Write surfaces additionally spec:
- The audit-log entry produced (structure + example).
- The duplicate-submit debounce window behaviour (for §11.1 placement).

### §6.3 Anchors

- §9.1 Operational live-pricing: §2.9 §6.1 (read surfaces) + §2.4 (Streaming-equivalent shape).
- §9.2 Settlement: §2.6 §5.1 (five fields + three count fields).
- §9.3 Sports-line query: §2.9 §6.1 surface (a).
- §9.4 Scheduled-time: §2.9 §6.1 surface (b).
- §9.5 Identifier check: §2.9 §6.1 surface (c).
- §10 Streaming: §2.4 (entire brief).
- §11 Write surfaces: §2.9 §6.1 (write-side framing) + §2.7 §3.5 (write-side tagging).
- §12 Audit trail: §2.7 §3.5 + Cat 4 single-cycle analysis discipline.
- §13 Streaming-disconnect-blocks-writes: §2.7 §3.4.

If an anchor is missing or ambiguous: finding.

---

## §7 — Sequencing within session

Recommended order:

1. Read all six pre-reads end-to-end before touching either output file. Both contract files are interconnected (shared envelope shape, parallel structure) and reading both specs first prevents drift between the two developer-readable specs.
2. Draft `vps_client_contract.md` §7+ first. Smaller surface (six call surfaces, no write side, no streaming), so it's the cleaner first pass and establishes the envelope/format that `betfair_client` reuses.
3. Draft `betfair_client_contract.md` §7+ second. Reuses the envelope shape from vps_client; adds the Betfair-specific reason extensions, the streaming surface, the write surfaces, the audit-trail discipline.
4. Cross-check the two files for consistency before locking — same envelope shape, same versioning mechanics framing, same out-of-scope discipline framing.
5. Update the version history table in each file with a Session 77 Code row dated today.

Code may deviate if a different order surfaces as operationally cleaner (e.g. drafting both file overviews first, then both envelope sections, then both call-surface sections in parallel — "vertical" rather than "horizontal" sequencing). Either order is fine; consistency between the two files is the goal.

---

## §8 — Empirical verification

**Pre:** Code reads both contract files end-to-end and confirms (a) the §7+ placeholder is the only content below §6 in each file, (b) the §1–§6 operator-readable summary is on disk and complete, (c) the version history table in §6 has the two Session 75 / Session 77 rows shown.

**Post:** Code reads both files end-to-end and confirms (a) §7+ is now substantive (not the placeholder italic), (b) every call surface named in operator-readable §2 has a corresponding sub-section in the developer-readable spec, (c) the version history table has a new row for the Code session, (d) line counts and section counts match the report's claims.

The report records the pre and post line counts of each file plus a per-section line breakdown. The operator-Claude triage session reads the report plus the two files together, so the report's accounting needs to match disk reality.

---

## §9 — Output spec

**Single output file:** `dr029/2_7_api_contract_versioning/contracts_spec_report.md`.

**Section structure:**

- §1 — Summary. What the session did, line counts pre/post for each file, completion status, any findings surfaced.
- §2 — Method. How Code approached the work, whether the recommended sequencing was followed or deviated from, time taken (Adelaide local).
- §3 — vps_client developer-readable spec delivered. Section-by-section summary of what landed in §7+, with line counts per sub-section.
- §4 — betfair_client developer-readable spec delivered. Same.
- §5 — Anchor traceback. For each call surface, the anchor in the locked specs that the developer-readable spec drew on. If any anchor was missing or ambiguous: surface as a finding here, not resolved.
- §6 — Findings. Anything that needed operator-Claude resolution rather than Code resolving it mid-flight. Empty if the transcription was clean.
- §7 — Cross-file consistency check. Confirms envelope shape, versioning framing, out-of-scope discipline are consistent between the two files.
- §8 — Self-assessment. Did the work fit one Code session? Was the brief's anchor coverage sufficient? Any drift risks the next session should know about?

**Length:** roughly 200–400 lines. Range, not hard line — exceeds reasonably if findings are substantive.

**The report does not contain:** recommendations for next steps (that's the operator-Claude triage session's job), edits to the operator-readable summaries (out of scope), edits to any of the locked specs (out of scope), proposed v2 contract shapes (speculative; out of scope).

---

## §10 — Hard limits

Non-negotiable. Code does not:

- Edit the operator-readable summaries (§§1–6) in either contract file. Append-below-§7-only.
- Edit the locked spec briefs (§2.4, §2.6, §2.7, §2.9, §2.10). Read-only.
- Edit any other file in the rebuild folder.
- Invent contract surfaces not named in operator-readable §2 of either file.
- Invent error semantics, reason enumerations, parameter types, or return shapes not anchored in the locked specs. If an anchor is missing or ambiguous, that's a finding for §6 of the report, not a Code resolution.
- Propose changes to the versioning policy (§2.7 §4). The policy is locked.
- Touch v2 of either contract speculatively. v1.0 only.
- Propose v3 module implementations. The developer-readable spec is the contract; v3 build proper implements against it later.
- Edit the §2.10 inventory writeup or any other DR-029 deliverable.
- Run any DB query, API call, or external network operation. This brief is documentation transcription only.
- Touch the named pieces of debt being carried into v3 (no test coverage, no migration framework, monolithic orchestrator). Out of scope.
- Continue past one Code session if the work doesn't fit. Surface as a finding.

---

## §11 — What happens after Code's session

The next operator-Claude session (likely Session 78, possibly Session 79 if Session 78 is deferral-shaped) reads `contracts_spec_report.md` plus the two updated contract files end-to-end. Triage shape:

- Confirm the developer-readable specs are consistent with the operator-readable summaries and with the locked specs.
- Resolve any findings Code surfaced.
- Update the version history table in each file if any operator-Claude resolution edits land.
- Lock both contract documentation files as v1.0 complete. This closes the `Contract documentation files` stream in `v3_build_picture.md`.

After the contract documentation files lock, only the DR-029 close-out governance paragraph remains before v3 build proper begins. That paragraph is likely Session 79 or 80 work.

Code does not write the next brief. The operator-Claude session decides what (if anything) needs follow-up briefing — most likely no follow-up brief is needed because the transcription should land cleanly.

---

## §12 — Cross-references

**Scope:** DR-029 critical path — contract documentation files (per §2.7 §5.4) plus close-out governance paragraph remaining before v3 build proper.

**Governing DRs:**
- DR-027 (the two-database architecture decision).
- DR-028 (the cross-database integration boundary discipline). Load-bearing for the one-file module boundary in both contracts.
- DR-029 (the data-layer fit-for-purpose review before v3 build — active arc).
- DR-021 (timestamp anchoring, Adelaide local time).

**Locked specs this brief draws on:**
- §2.4 (Betfair Streaming connection shape).
- §2.6 (settlement model — §5.1 settlement-read shape).
- §2.7 (API contract versioning — versioning discipline + write-side tagging).
- §2.9 (write-side bet-entry coherence — §6.1 contract surfaces).
- §2.10 (external analytics scan inventory — named first wave of backward-compatible additions in operator-readable §5).

**Excluded from scope (parking-lot items explicitly named):**
- Auth flow implementation (carry-forward; lands in betfair_client_contract.md §7+ developer-readable section but the spec shape is what Code drafts, not the implementation itself).
- Rate-limit budget allocation (carry-forward; v3 build proper operational tuning, not contract shape).
- Cadence parameters for Streaming (Fix 4, post-DR-029).
- Soft-book operational layer (deferred to a future DR; no `softbook_client` contract in v3 day-one).
- Sports analytical capability (out per `dr029_scope.md` principle 1.3).

**Precedent briefs:** Session 33's source-review brief is the closest shape (per-area sections, each anchored to specific findings). Sessions 35 / 36 surgical-fix briefs informed the hard-limits discipline.
