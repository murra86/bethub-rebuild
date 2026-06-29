# Pre-W14 codebase review — bethub-v3 inventory
# and drift surfacing — brief

**Locked:** 2026-05-11 22:31 ACST (Session 122).
**Workstream:** Pre-W14 codebase review (new sub-stream
inserted before W14).
**Authoring session:** Session 122 (operator-Claude Chat).
**Execution:** single bounded Claude Code session.
**Output:** `dr029/pre_w14_review/codebase_review_report.md`.

---

## §1 — What this brief is and is not

This brief commissions Claude Code to perform an
**empirical inventory pass** across the entire
`bethub-v3/` codebase, then surface every drift between
(a) `architecture.md` spec, (b) locked DRs in
`decisions.md`, and (c) the actual shipped reality on
disk.

**What this brief commissions:**

- Pillar-by-pillar inventory of `bethub-v3/`: every
  module, every public function, every persisted shape
  (table, column, type).
- DR-by-DR drift inventory: for each locked DR (DR-001
  through DR-032), does the shipped state match? Flag
  every mismatch.
- Missing-from-spec inventory: what does `architecture.md`
  describe that isn't yet on disk in `bethub-v3/`?
- Missing-from-architecture inventory: what's on disk in
  `bethub-v3/` that isn't described in `architecture.md`?

**What this brief does NOT commission:**

- Code changes of any kind. Zero edits to `bethub-v3/`.
  Zero edits to any rebuild folder canonical doc.
- Remediation proposals. Code reports what is, not what
  should be. Triage of any drift is the next
  operator-Claude session's work.
- Fitness judgement. "This is shipped wrong" or
  "this should be refactored" is out of scope.
- Scope creep into W14, W13, W12, or any future build
  work.
- Test execution. Tests are known passing (549) per
  W11.1 close; that's the assumed baseline, not
  something to re-verify.

This is a **read-only inventory pass**, not a fix, not
a probe, not a measurement of capability. Surprises
become findings in the report; remediation decisions
are next-session work.

---

## §2 — Why this work exists

Operator-Claude Session 122 surfaced an architectural
drift during W12 brief scoping. The drift, in plain
language: `architecture.md` §A.2 ("Event log — the
spine") describes v3's bet-data as living in **a single
event log table** with `bet_placed`, `bet_settled`,
`bet_correction` as separate immutable events. DR-027
(Session 19 lock) reinforces that framing. But DR-032
(Session 42 lock) supersedes with a **two-table shape —
bet record + bet legs** — and the shipped code
(Sessions 100–116) matches DR-032, not the
architecture.md spec.

That's one drift we know about. The concern is that
120+ sessions of build work has produced several more
drifts that haven't surfaced because no one's done a
full inventory pass against `architecture.md` and the
locked DRs. Before W14 (cash-flow event log) commissions
build work that depends on assumptions about what's
already shipped, we need a ground-truth baseline.

This brief commissions that baseline.

---

## §3 — Pre-reads

**Required reads in order:**

1. `architecture.md` — full read. The spec being
   measured against.
2. `decisions.md` — full read. Every locked DR (DR-001
   through DR-032). Cite each by number when
   referencing.
3. `v3_data_requirements.md` — full read. The data-side
   spec.
4. `project_context.md` — orientation primer for the
   operator domain context.
5. `dr029/dr029_scope.md` — DR-029 scope items, for the
   §2.x reference markers used in `architecture.md`.

**Reference-only (read on demand as the inventory
surfaces specific questions):**

- `dr029/w11_accounts/w11_accounts_brief.md` and report
  — most recent shipped pillar.
- `dr029/w11_accounts/w11_1_brief.md` and report —
  surgical-rename follow-up; tests now live at
  `tests/store/repositories/`.
- `dr029/w10_storage_lift/` — preceding storage-lift
  work.
- W4 / W6 / W6.5 / W9 briefs and reports under `dr029/`
  — the bet pillar's shipped scope. Read on demand
  when a finding needs precedent.
- Session records `SESSION_100.md` through
  `SESSION_121.md` — recent shipped state. Read on
  demand when a finding needs precedent.
- `vps_client_contract.md` and `betfair_client_contract.md`
  (rebuild folder root) — client contracts at v1.0.

---

## §4 — System access

- **Mac filesystem read-only** on
  `/Users/tim/Desktop/Projects/bethub-v3/`.
- **Mac filesystem read-only** on
  `/Users/tim/Desktop/Projects/bethub-rebuild/` for
  canonical docs.
- **No DB writes.** No `bethub-v3/` schema changes.
  No data writes anywhere.
- **No git operations.** No `git add`, `git commit`,
  `git stash`, `git restore`, `git checkout`,
  `git reset`. Working tree is dirty per W11/W11.1
  ship state — leave it as-is.
- **No external API calls.** No Betfair. No VPS.
  No `capture.db` reads.
- **No tests run.** Test gates are not in scope.
- **Adelaide local timestamps per DR-021** for every
  time reference in the report.

---

## §5 — Substantive scope

### §5.1 — Bet pillar inventory

**Files to inventory:**

- `bethub-v3/domain/bets/__init__.py` and any module(s)
  within.
- `bethub-v3/store/schema/bets.py` — every column on
  `bets` and `bet_legs` tables. Type, nullable, default,
  comment column-by-column.
- `bethub-v3/store/repositories/bets.py` — every public
  method. Signature, return type, what it persists,
  what it reads.
- `bethub-v3/workflows/bet_entry/v1/` — every module
  (`betfair_adapter.py`, `bet_store_adapter.py`,
  `models.py`, `orchestrator.py`, `pricing.py`,
  `reconciliation.py`, `record_builder.py`,
  `settlement.py`, `staking.py`).
- `bethub-v3/domain/pricing/` and
  `bethub-v3/domain/settlement/` — pricing and
  settlement payout computation paths.

**For each module, name three things:**

1. What it does (1–2 sentences).
2. What it persists (table writes / event emissions /
   nothing).
3. What it exposes publicly (functions a balance
   derivation could call).

**Specific questions to answer in the bet-pillar
inventory:**

- (a) What's the public path from `bets.settlement_state`
  → cash returned per bet? Name the function, file,
  line range. Is it called directly or via the
  workflow orchestrator?
- (b) Is `bets.realised_conversion_rate` populated
  anywhere in the shipped code? If so, by which
  module — i.e., did W5 ship?
- (c) Are there any event-log scaffolding files
  anywhere in `bethub-v3/` — e.g., an `events.py`
  module, an `event_log` table, an append-only
  persistence pattern? Empirically verify.
- (d) Does `bet_legs` carry any state that's mutable
  post-placement, or is it write-once?
- (e) Does the DR-026 market-context snapshot land
  on `bets` columns as spec'd, or somewhere else
  (or not at all)?

### §5.2 — Account pillar inventory

**Files to inventory:**

- `bethub-v3/domain/accounts/__init__.py`
- `bethub-v3/store/schema/accounts.py` — all tables,
  all columns.
- `bethub-v3/store/repositories/accounts.py` — every
  public method.

**Specific questions:**

- (a) Does the accounts pillar match DR-022 (the
  account / book / account-at-book vocabulary)? Are
  all three entities tabled?
- (b) Does `bets.account_at_book_id` (FK on `bets`)
  point at a real `account_at_book` primary key on
  the shipped accounts pillar? (DR-032 §1.)
- (c) Any drift between the account pillar's shipped
  shape and `architecture.md` §A.1 (entity
  references)?

### §5.3 — Clients inventory

**Files to inventory:**

- `bethub-v3/clients/betfair_client/` — every module,
  every public function.
- `bethub-v3/clients/vps_client/` — every module,
  every public function.

**Specific questions:**

- (a) Is the contract surface stable / locked?
  `vps_client_contract.md` and
  `betfair_client_contract.md` are at v1.0 per
  Sessions 76–80. Does the shipped code match those
  contracts? Surface any drift between contract
  spec and shipped public surface.
- (b) Are there any client methods exposed beyond
  what the contract documents?
- (c) Cross-DB integration boundary — does the
  shipped code respect DR-028 (no caching, no
  denormalisation, no second integration point)?

### §5.4 — Reconciliation and settlement pillar

**Files to inventory:**

- `bethub-v3/workflows/bet_entry/v1/reconciliation.py`
- `bethub-v3/workflows/bet_entry/v1/settlement.py`
- `bethub-v3/domain/settlement/`

**Specific questions:**

- (a) Reconciliation gap detection — is there a
  function that computes "expected book balance" vs
  "actual book balance" yet? If not, document the
  gap. (`architecture.md` §A.9 names this surface.)
- (b) Settlement payout computation — name the
  function the balance derivation will need to call.
  Signature, return type, dependencies. Where it
  lives.
- (c) Settlement-state mutation path — when does
  `bets.settlement_state` get written? By which
  module?
- (d) Hedge state — is hedge classification per
  DR-025 shipped? Where does it live? If not
  shipped, document the gap.
- (e) Were W6 (reconciliation), W6.5 (settlement
  state), W9 (last-read market state) all shipped
  per their briefs, or is there partial state?

### §5.5 — UI surface

**Files to inventory:**

- `bethub-v3/ui/api/` — every endpoint.
- `bethub-v3/ui/web/` — every page / component.
- `bethub-v3/workflows/burst_review/` — what's
  shipped.

**Specific questions:**

- (a) Are there any balance-display surfaces
  already shipped? Where do they read from?
- (b) What state does the UI read from `bethub-v3`
  vs from `capture.db`?
- (c) Reconciliation gap surface — shipped or not?
- (d) Burst review scaffold — what's shipped vs
  what's spec'd in `architecture.md`?

### §5.6 — Operations, contracts, config

**Files to inventory:**

- `bethub-v3/ops/` — every module.
- `bethub-v3/contracts/` — every contract file.
- `bethub-v3/pyproject.toml` — dependency list.
- `bethub-v3/.importlinter` — contracts enforced.

**Specific questions:**

- (a) DR-006 (operations log first-class) — is there
  an `ops_log` table, an `ops_log` module, anything?
  If not, document the gap.
- (b) DR-030 (repo layout / module-boundary
  discipline) — do the contracts in `.importlinter`
  match the module boundaries on disk? Are all five
  contracts kept (per W11.1 close: 5 / 0)?
- (c) DR-031 (tech stack) — is SQLAlchemy Core in
  use anywhere, or is the shipped code all raw
  `sqlite3`? (W11 brief §3.2 flagged the divergence;
  confirm it's still divergent.)
- (d) Pydantic v2 usage — load-bearing per DR-031;
  confirm domain models use Pydantic v2 patterns.

### §5.7 — Tests inventory

**Files to inventory:**

- `bethub-v3/tests/` — every test module, what it
  covers.

**Specific questions:**

- (a) Per-pillar test coverage: bet pillar, account
  pillar, clients, reconciliation, settlement, UI,
  ops. How many tests per pillar?
- (b) Are there any test gaps in shipped pillars —
  e.g., bet placement has no settlement test, or
  vice versa?
- (c) Test scaffolding: fixtures, conftest patterns,
  integration vs unit split. Where do fixtures live?
- (d) Are W11 / W11.1 tests at the correct paths
  per the surgical rename (`tests/store/repositories/
  test_accounts_*.py`)?

### §5.8 — DR drift inventory

For **each locked DR** in `decisions.md` (DR-001
through DR-032), produce a row in a drift table:

- DR number + title.
- One-line summary of what the DR locks.
- Shipped-reality status: **match**, **divergent**,
  or **N/A** (DR is forward-looking and not yet
  applicable, or is a principle without a shipped
  surface to compare against).
- If **divergent**: cite the `architecture.md` line
  / DR line on one side, and the shipped file /
  line on the other side. **Both sides cited.**

This is the primary drift-surfacing section. It will
be long (32 DRs); that's expected.

**Known starting drifts the report will catch:**

- DR-027 ("single event log carrying bet_placed /
  bet_correction / bet_settled / ...") vs DR-032
  ("two-table shape: bet record + bet legs") vs
  shipped reality (bets table with mutable state
  columns). Three-way drift to document explicitly.
- DR-031 (SQLAlchemy Core locked) vs shipped raw
  `sqlite3` (W11 brief §3.2). Document path forward
  is deferred per W10 brief §10.2 / DR-029 close-out.

### §5.9 — Missing-from-spec inventory

What does `architecture.md` describe that isn't yet
on disk in `bethub-v3/`? For each missing item:

- `architecture.md` section / line reference.
- Plain-language description of what's missing
  (e.g., "cash-flow event log table per §A.5").
- Whether the gap is **build pending** (W14, W13,
  W15 etc. — known forward work) or **drift**
  (something dropped through the cracks).

**Specific items to check for (non-exhaustive — Code
should find more):**

- Cash-flow event log table(s) per §A.5.
- Promo event log table(s) per §A.4.
- AccountCare event log entries (warning_raised /
  warning_cleared) per §A.4.
- Operation net flow derivation per §A.5.
- Balance derivation read-side (Location 1 —
  per-account-at-book; Location 2 — per-custodian
  cash holding).
- Reconciliation gap per book — surface and
  computation per §A.9.
- Ops log first-class storage per DR-006.
- Hedge state classification per DR-025.
- Cascade chains per §A.7.
- Promo journey annotation per §A.4 / Q1.
- Free bet expired / revoked / deployed event types
  per §A.4.

### §5.10 — Missing-from-architecture.md inventory

What's on disk in `bethub-v3/` that isn't described
in `architecture.md`? This catches drift in the
other direction — code shipped without spec update.

For each item:

- Shipped file / table / module.
- Plain-language description of what it does.
- Spec section it should plausibly belong to (e.g.,
  "should land in §A.2 if it's a persisted bet
  field" or "should land in §A.8 if it's a
  cross-DB integration").

---

## §6 — Sequencing within the Code session

Work pillar-by-pillar before crossing into DR drift
before crossing into missing-from-spec. Order:

1. §5.1 bet pillar.
2. §5.2 account pillar.
3. §5.3 clients.
4. §5.4 reconciliation / settlement.
5. §5.5 UI surface.
6. §5.6 operations / contracts / config.
7. §5.7 tests.
8. §5.8 DR drift inventory (every DR).
9. §5.9 missing-from-spec inventory.
10. §5.10 missing-from-architecture inventory.

Code can deviate from this order if a finding in one
pillar requires checking a later pillar to verify. Name
any deviation in the report.

---

## §7 — Empirical verification

Every finding in the report must cite:

- The shipped file (absolute path), line range.
- The architecture.md / DR / spec source it's being
  measured against (file + line).

No findings based on memory or assumption. Code reads
both sides before declaring drift.

- **For tables:** every column listed with type,
  nullable, default. `PRAGMA table_info(<table>)`
  output captured verbatim.
- **For modules:** every public function with full
  signature, captured from the source.
- **For DRs:** the DR number, the locked sentence
  (quoted from `decisions.md`), the shipped reality
  cited side-by-side.

---

## §8 — Output spec

**Single file at:** `dr029/pre_w14_review/
codebase_review_report.md`

**Section structure:** 1:1 with §5 above (§5.1 →
§5.10), plus a §11 summary of drift findings ranked
by severity, plus a §12 self-assessment per the
brief-drafting convention.

**Length anticipation:** 600–1000 lines is the
realistic range given breadth. Likely closer to
1000. Code should not tighten by collapsing verbatim
PRAGMA / function-signature output — the empirical
fidelity is the point.

**What the report does NOT contain:**

- Remediation proposals. No "this should be fixed
  by..." or "the right next step is...". Findings
  only.
- Fitness judgement. No "this is wrong" — only
  "this is shipped, this is spec'd, they differ."
- Scope creep. No work on W14 / W13 / W12 scope,
  no `architecture.md` edits, no DR edits.
- Conclusions. No overall verdict on whether the
  codebase is healthy. Inventory + drift surfacing
  only.

---

## §9 — Hard limits

### §9.1 — Operating principle

Single bounded Code session. Read-only across the
entire `bethub-v3/` codebase and the rebuild folder
canonical docs. Surprises become findings in the
report. No mid-session escalation. If the scope is
unexpectedly large, Code surfaces the partial state
as a finding rather than continuing past budget —
partial-but-coherent inventory beats complete-but-
lost-coherence.

### §9.2 — No code changes anywhere

Zero edits to `bethub-v3/`. Zero edits to any
rebuild folder canonical doc. Read-only across both.

### §9.3 — No remediation, no fixes, no scope creep

Code does not propose fixes. Code does not act on
findings. Code does not commission follow-up work
in the report — the next operator-Claude session
does that. Code does not work on W14 / W13 / W12
scope, even tangentially.

### §9.4 — No Alembic, no debt-fixing

Per W11 brief §10.2 / DR-029 close-out, Alembic
adoption is deferred. This brief does not adopt,
propose, or scope Alembic. Same applies to the
three pieces of v3 named debt (no test coverage,
no migration framework, monolithic orchestrator
file) — Code documents what's shipped, doesn't fix.

### §9.5 — Operational guardrails

- No git operations of any kind.
- No DB writes anywhere.
- No external API calls.
- No tests run (test gates are 549 passing per
  W11.1 close; that's the assumed baseline).
- No log file inspection beyond what's needed to
  inventory `ops/`.
- All timestamps in the report in Adelaide local
  time per DR-021.

---

## §10 — What happens after Code's session

The next operator-Claude session reads the codebase
review report end-to-end. Triage shape:

- Surface drift findings to the operator in plain
  language, ranked by operational severity.
- Decide for each material drift: clean up
  `architecture.md` to match shipped, OR fix
  shipped to match `architecture.md`, OR document
  the asymmetry as a permanent design call.
- Surface what's-missing-from-spec items: route
  each to the appropriate workstream (cash-flow
  events → W14, promo events → W13, balance
  derivation → W12, ops log → W15, etc.).
- Surface what's-missing-from-architecture items:
  queue `architecture.md` updates as a separate
  governance task.
- THEN draft W14 brief against ground-truth.

Triage outcomes shape the W14 brief. The pre-W14
review's purpose is to make the W14 brief drafted
against reality, not against drift-laden spec.

---

## §11 — Cross-references

- `architecture.md` — the spec being measured against
  (full read in §3).
- `decisions.md` — DR-001 through DR-032 (full read
  in §3).
- `v3_data_requirements.md` — data-side spec (full
  read in §3).
- `project_context.md` — operator orientation
  primer (full read in §3).
- `dr029/dr029_scope.md` — §2.x reference markers
  (read for cross-references).
- `dr029/w11_accounts/` — most recent shipped pillar
  precedent (reference-only).
- `dr029/w10_storage_lift/` — preceding storage-lift
  work (reference-only).
- `vps_client_contract.md` and
  `betfair_client_contract.md` (rebuild root) —
  client contracts at v1.0 (reference-only).
- W4 / W6 / W6.5 / W9 briefs and reports —
  bet-pillar shipped scope (read on demand).
- Session records `SESSION_100.md` through
  `SESSION_121.md` — recent shipped state (read on
  demand).

**Parking-lot items excluded from this brief:**

- Any W14 / W13 / W12 build scope.
- Any `architecture.md` edits.
- Any DR edits or new DR drafts.
- Any code changes in `bethub-v3/`.
- Test execution.
- Alembic adoption work (deferred per W10 brief
  §10.2 / DR-029 close-out).
