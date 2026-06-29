# Brief — Betfair customer-reference impact & design review (READ-ONLY)

**Drafted:** 2026-06-18 18:24 ACST (Session 163, Claude Chat)
**Completed:** 2026-06-18 18:36 ACST (continuation chat — §5.3
onward; §1–§5.2 unchanged from the S163 draft)
**Executes against:** `bethub-v3` repo at
`/Users/tim/Desktop/Projects/bethub-v3`
**Brief type:** read-only source review (Session 33 precedent) +
inspection discipline (Session 28 — output is a map and an
options analysis, NOT remediation, NOT a verdict enacted in code).
**Output report:**
`dr029/2_4_betfair_streaming/customer_ref_impact_review_report.md`

---

## §1 — What this brief is and is not

This is a **read-only impact-and-design review**. Its job is to
map how four identifiers move through v3 and to lay out the fix
options with their blast radius — so the *next* session can scope a
correct fix on solid ground. It is a single bounded Code session.

**Is:**
- A complete generation-and-consumption map of four identifiers
  (§2) across the v3 codebase.
- Empirical confirmation of the specific risks named in §5.
- A two-option design analysis (unify-and-cap vs decouple) with
  the blast radius, test impact, and risk of each.

**Is NOT:**
- **No code changes.** Not one line. This review touches nothing —
  it reads, traces, and reports.
- Not a fix, not a patch, not a refactor, not a test addition.
- Not a decision: the review presents both options with evidence;
  it does **not** pick one, and it does **not** write the fix
  brief. That is the next Chat session's job, with the operator.
- Surprises are recorded as findings, not acted on.

This review exists because a surgical fix was drafted (S163) and,
on tracing, found to be mis-scoped — it patched one of (at least)
two placement sites and rested on unverified assumptions about
downstream consumers. This review de-risks the real fix.

---

## §2 — Why this work exists, and the four identifiers

Session 162 drove the persistent live-lay 503 to a definitive
Betfair error: `INVALID_INPUT_DATA — customerRef … too long (32
character limit)`. The app sends a 47-char reference; Betfair caps
it at 32.

Session 163 began scoping a surgical fix and, tracing the code,
found the issue is broader than one line:
- The over-long reference is generated in **at least two**
  placement paths, not one.
- The same value is sent to Betfair as both `customerOrderRef`
  **and** the top-level `customerRef`.
- The internal bet-id format is inconsistent (3+ formats observed)
  and the "canonical" format is itself too long to be a Betfair
  reference.
- The references are read back for reconciliation; the blast
  radius of changing their format/length is not yet established.

**The four identifiers this review tracks** (and their Betfair
caps where applicable):
1. `bet_id` — v3-internal bet-record identifier.
2. `customer_order_ref` — per-order Betfair reference
   (`customerOrderRef`, **≤32**). Currently set equal to `bet_id`.
3. `customerRef` — top-level Betfair per-request de-dupe token
   (**≤32**). Currently also set equal to `customer_order_ref`.
4. `customer_strategy_ref` — Betfair strategy label
   (`customerStrategyRef`, **≤15**). Currently the `StrategyTag`
   value; `synthetic_each_way` (18) breaches the cap.

---

## §3 — Pre-reads

**Required (read before tracing):**
- This brief, in full.
- `dr029/2_4_betfair_streaming/placement_failure_diagnostic_report.md`
  — the S162 diagnostic that named the `customerRef` error.
- `dr029/2_4_betfair_streaming/customer_ref_fix_brief.md` — the
  **superseded** S163 fix draft. Read it to understand the
  proposed fix shape the review is pressure-testing; **do not
  execute it.**

**Reference-only (consult as the trace leads):** any file named in
§5; the rest of the `dr029/2_4_betfair_streaming/` report set.

---

## §4 — System access

- **Filesystem:** Mac, `bethub-v3` repo at
  `/Users/tim/Desktop/Projects/bethub-v3`. **READ-ONLY.**
- **No edits, no writes** anywhere in the repo except the single
  output report under the rebuild project (§7). Do not modify any
  `bethub-v3` source, test, or config file.
- **No git state-changing commands.** `git status` / `git diff` /
  `git log` / `git grep` for inspection only — no `add`, `commit`,
  `stash`, `restore`, `checkout`, `reset`.
- **Tests:** do not run the suite for pass/fail; you may *read*
  test files as evidence of intended behaviour (§5). If you want to
  confirm a runtime behaviour, reason from the code rather than
  executing — and if execution is unavoidable, note it as a
  finding and keep it read-only (no fixtures written).
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021.

The §5 anchors below are **starting points from the S163 trace,
not a closed list** — follow the identifiers wherever they lead and
report anything the starting anchors missed.

---

## §5 — Review scope

Five areas. Each produces a section in the report. Anchors are
S163 starting points; the review confirms, corrects, and extends
them.

### §5.1 — Generation map

Find **every** site that creates a `bet_id` and/or a Betfair-bound
reference. For each: the exact format string, the resulting length,
and whether that value reaches Betfair.

Known starting anchors:
- `ui/api/routers/racing.py:981` — lay route,
  `f"bet-record-{uuid4()}"` (47).
- `workflows/bet_entry/v1/orchestrator.py:743` — hedge/bet-entry,
  `f"bet-record-{uuid.uuid4()}"` (47).
- `ui/api/routers/racing.py:877` — bets POST route,
  `"bet-" + str(uuid5(...))` (40). Does this reach Betfair, or is
  it record-only?
- `workflows/bet_entry/v1/record_builder` `_resolve_id` —
  documented as `f"bet-{uuid4()}"` (40); the "canonical" format.

Deliver: a table of every generation site × format × length ×
reaches-Betfair? × notes.

### §5.2 — Betfair-bound consumption map

Find every site that places one of the references into a Betfair
request (place / cancel / replace / current-orders queries). For
each, name which Betfair field it populates and that field's cap.

Known starting anchors (all `clients/betfair_client/v1/`):
- `_translation.py` (~326–330) — assigns `customerOrderRef`,
  `customerStrategyRef`, and `customerRef`; confirm `customerRef`
  is set from `customer_order_ref` (the field S162 flagged).
- `placement.py`, `cancellation.py`, `replacement.py`,
  `current_orders.py`, `_audit.py`, `_stream_parser.py`,
  `consumer.py`, `streaming.py`; and
  `workflows/bet_entry/v1/betfair_adapter.py`.

Deliver: for each reference, the full list of Betfair fields it
feeds and the binding cap (32 / 32 / 15).

### §5.3 — Read-back & reconciliation consumption

This is the risk the operator flagged: shortening a reference
could break something that reads it back. Find **every** site
that reads a Betfair reference off a response and *acts* on it —
matches, joins, settles, audits, or stores it for later match.

Known starting anchors (`clients/betfair_client/v1/` unless
noted):
- `current_orders.py` — captures `customerOrderRef` /
  `customerStrategyRef` off the currentOrders response.
- `settlement.py` — does settlement match orders back via any
  reference, or purely by Betfair bet id?
- `_audit.py` — does the audit trail key off any reference?
- `consumer.py` / `_stream_parser.py` — does the order stream
  carry references that get matched to internal records?
- `workflows/bet_entry/v1/betfair_adapter.py` — does the adapter
  map a read-back reference onto an internal record?

The two specific questions:
1. Does any path take a Betfair-returned `customerStrategyRef`
   and reverse-map it to a `StrategyTag`? (If so, shortening
   `synthetic_each_way` → a ≤15 form breaks it.) S163 found none
   but did not exhaustively confirm.
2. Does reconciliation depend on the outbound
   `customer_order_ref` equalling the stored `bet_id` *exactly*?
   (If so, decoupling them needs a stored mapping.)

Deliver: for each read-back site — what it does with the
reference (pass-through / match / join / settle / audit-only),
and an explicit **yes/no** on whether changing the outbound
reference's format or length breaks it.

### §5.4 — Internal `bet_id` format & consumers

`bet_id` is also an internal record key, independent of Betfair.
Inventory:
- Every format `bet_id` takes (S163 saw ≥3: `bet-record-{uuid}`
  47, `bet-{uuid5}` 40, `bet-{uuid4}` 40).
- Every place `bet_id` is **persisted** — which tables/columns
  in the schema. Read `store/schema/` source; do **not** read
  row data.
- Every place `bet_id` is **parsed** or its format assumed —
  especially `fb_deployment.py` stripping the `bet-` prefix to
  recover a UUID. What breaks if the prefix changes? What
  already silently fails today? (S163: the `bet-record-` ids
  already fail that parse and fall back to a random UUID.)
- Any joins / foreign keys keyed on `bet_id` across bets /
  orders / settlement / audit.

Deliver: format inventory; persistence map (tables/columns);
every consumer that assumes a format or prefix, with what breaks
under Option A and Option B.

### §5.5 — Two-option design analysis (the payload)

With §5.1–§5.4 mapped, lay out both fixes concretely. This is
**not** a recommendation — present both, with evidence, so the
next session and the operator decide on solid ground.

**Option A — Unify-and-cap.** Make every Betfair-bound id ≤32 at
all generation sites; keep `bet_id` == `customer_order_ref` ==
`customerRef`. Shorten `customer_strategy_ref` values to ≤15.
Report: every generation site that must change; whether any
already-stored `bet_id` becomes "illegal" and whether that
matters (any orders already placed under the old format?); test
impact (which tests assert the 47/40-char shape); residual
conceptual debt (id and reference stay fused — the tension that
prompted this review is contained, not resolved).

**Option B — Decouple.** `bet_id` keeps its natural internal
form (no Betfair cap); a separate ≤32 `betfair_ref` is generated
per order and stored on the bet/order record so reconciliation
round-trips. Report: where the new field lives (a schema change
— name it, do **not** write it); the new mapping that
reconciliation reads; every read-back site that must switch from
matching `bet_id` to matching `betfair_ref`; test impact;
migration question for any in-flight/historical orders; the
larger blast radius weighed against the cleaner separation.

**For both options, deliver:**
- A blast-radius table: files touched, tests touched, schema
  touched (y/n), reconciliation paths touched, single biggest
  risk.
- An explicit answer to: does this option still leave the
  `customerStrategyRef` 15-cap (Strategy 4) unsolved? Both fixes
  must close it — name how, under each.
- A short comparison framing the real trade: A is smaller and
  unblocks the $5 lay sooner but keeps id≡ref fused; B is more
  surface and a schema change but resolves the conflict
  structurally. State the trade; do not pick.

If the trace shows the two options collapse into one (e.g.
decouple is *forced* because a consumer cannot tolerate a
shortened `bet_id`), say so plainly — that is the single most
valuable finding this review can produce.

---

## §6 — Sequencing within the session

Recommended order (Code may deviate and say why):
1. **§5.1 generation map** first — establishes the id universe.
2. **§5.2 Betfair-bound consumption** — where the ids hit caps.
3. **§5.4 internal `bet_id` consumers** — needs §5.1's inventory.
4. **§5.3 read-back / reconciliation** — the highest-value risk
   confirmation; do it with the §5.2 + §5.4 maps in hand.
5. **§5.5 options analysis** last — it depends on all four maps.

## §7 — Completeness criteria (how Code knows it's done)

This is a review, so "verification" means coverage, not
pass/fail. The map is complete when:
- Every generation site is grounded by a repo-wide search, not
  just the named anchors — grep for `uuid4`, `uuid5`, `"bet-"`,
  `customerRef`, `customerOrderRef`, `customerStrategyRef`,
  `customer_order_ref`, `customer_strategy_ref`.
- Every Betfair field assignment for the three caps (32/32/15)
  is traced to source.
- Every read-back site carries an explicit breaks-y/n verdict.
- Both options have a complete blast-radius table.

Anything Code cannot fully confirm goes in the report as an
explicit open item — never papered over.

## §8 — Output spec

**Single file:**
`dr029/2_4_betfair_streaming/customer_ref_impact_review_report.md`

Sections mirror §5.1–§5.5, plus a §0 executive map (one
paragraph + the four-identifier table) and a closing
"Open items / could-not-confirm" section. Tables welcome.
**Length:** roughly 250–500 lines; flag in a self-assessment
line if materially exceeded.

**Does NOT contain:** a chosen option; a fix; any diff, patch,
or code change; a verdict beyond presenting evidence. Code may
add one clearly-labelled "reviewer's observation" note if it
feels strongly — observation, not decision — but neutral
presentation is the default.

## §9 — Hard limits

- **READ-ONLY.** No edits to any `bethub-v3` source, test, or
  config file. The only file written is the output report under
  `bethub-rebuild`.
- **No git mutation** — no `add` / `commit` / `stash` /
  `restore` / `checkout` / `reset`. Inspection-only `git
  status` / `diff` / `log` / `grep` are fine.
- **No fix, patch, refactor, test addition, or schema change** —
  not even the "obvious" one. Option B's schema field is *named*
  in the report, never written.
- **Does not pick an option** and **does not write the fix
  brief.** That is the next Chat session, with the operator.
- **No scope creep** into other §2.x items or other DR-029 work.
- **No mid-session operator escalation** — run end-to-end;
  surface uncertainties as report findings.
- **Single bounded Code session.** If it won't fit, that's a
  finding — a partial-but-coherent map beats a complete-but-
  incoherent one.
- **Database:** prefer reading schema from `store/schema/`
  source. If a live-schema check is unavoidable, use
  `start_process` Python against the live file, **schema only** —
  never copy the db, never read row content.
- **Bet-safety gate** (5 live runs, no bet placed) is untouched
  and must stay so — this review changes nothing, but Code must
  not perturb it even while tracing.
- Adelaide local timestamps per DR-021.

## §10 — What happens after Code's session

The next Claude Chat session (triage):
1. Reads `customer_ref_impact_review_report.md` end-to-end.
2. Surfaces the §5.5 options and blast radius to the operator.
3. Operator + Claude make the unify-vs-decouple call — the
   "most robust, long-term" steer applies, now with evidence
   under it.
4. Claude drafts the actual fix brief — **superseding**
   `customer_ref_fix_brief.md` — scoped to **both** placement
   sites and the strategy-ref cap, per the chosen option.
5. Code executes the fix; operator re-runs the live $5 lay.

Code does **not** write that fix brief. This review feeds it.

## §11 — Cross-references

- **Scope doc:** `2_4_betfair_streaming.md` (§2.4 Betfair
  Streaming).
- **Superseded-as-input:** `customer_ref_fix_brief.md` — the
  S163 surgical draft, pressure-tested here, not executed.
- **Prior reports:** `placement_failure_diagnostic_report.md`
  (S162 — named the `customerRef` 503),
  `placement_visibility_report.md`.
- **DRs:** DR-021 (timestamp anchoring, Adelaide local time).
- **Parking lot (excluded):** broader `bet_id` scheme
  harmonisation beyond what the chosen fix needs; sports-path
  (W18) placement; cutover (W16).

---

*End of brief.*
