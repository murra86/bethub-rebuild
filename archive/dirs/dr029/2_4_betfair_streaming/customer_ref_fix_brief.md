# Brief — Betfair customer-reference compliance fix (customer_order_ref ≤32, customer_strategy_ref ≤15)

**Drafted:** 2026-06-18 16:09 ACST (Session 163, Claude Chat)
**Executes against:** `bethub-v3` repo at
`/Users/tim/Desktop/Projects/bethub-v3`
**Brief type:** surgical fix (Sessions 35/36 precedent) — named
changes only, dirty-tree discipline, empirical pre/post,
bet-safety gate untouched.
**Output report:**
`dr029/2_4_betfair_streaming/customer_ref_fix_report.md`

---

## §1 — What this brief is and is not

This is a **surgical fix** to a single, named root cause found in
Session 162: Betfair rejects every live lay because the reference
string the app tags the order with is longer than Betfair's
limit. It is a single bounded Claude Code session.

**Is:**
- A code fix across four named anchors that makes both Betfair
  reference fields compliant *by construction* and adds a
  send-boundary tripwire so an over-length reference can never
  silently reach Betfair again.
- Read-write on the named anchors only.
- Test-backed: new tests for every change; full suite re-run.

**Is not:**
- Not a redesign of the placement path, the bet-safety gate, the
  streaming transport, or the audit sink.
- Not a schema/migration change, not an enum-*value* change.
- Not a fix for any carried parking-lot item (F1 uncaught-
  transport gap, 200-market over-subscription, audit-sink
  durability, quick-lay modal error surfacing). Those are named
  and excluded in §9.
- Surprises become **findings in the report**, not mid-session
  scope changes. Remediation routes to the next operator-Claude
  triage session, not Code's report.

---

## §2 — Why this work exists

Session 162 drove the persistent live-lay 503 to a single
definitive Betfair error (three diagnostic-only briefs, gate
byte-for-byte unchanged, no bet placed across 5 live runs):

```
APINGException errorCode=INVALID_INPUT_DATA —
"The customerRef for this transaction contains invalid
 characters or is too long (32 character limit)"
```

The app sends `customer_order_ref = "bet-record-" + uuid4()` =
**47 chars**; Betfair caps the per-order reference at **32**.
Betfair rejects the order on arrival; every layer above buried it
under the catch-all `betfair_api_unreachable`, which is what made
it a two-session hunt.

While grounding this brief (Session 163), a **second instance of
the same class** was found one field over: Betfair also caps
`customerStrategyRef` at **15 chars**. The app sends the strategy
tag's value as that reference. Three of the four tags fit
(`safety_net` 10, `price_booster` 13, `sgm_correlated` 14); the
fourth, `synthetic_each_way`, is **18 chars** — so the first live
lay tagged Strategy 4 would reproduce this exact rejection on the
strategy reference.

Operator decision (S163): fix the **whole class**, robustly, in
one pass — both references, plus a tripwire so neither can ever
reach Betfair over-length again.

This unblocks the W17 racing-page live-lay validation gate: after
the fix, the operator re-runs the live $5 lay, which should
place — closing the last operator-side validation before W16
cutover scoping.

---

## §3 — Pre-reads

**Required (read before editing):**
- This brief, in full.
- `dr029/2_4_betfair_streaming/placement_failure_diagnostic_report.md`
  — the diagnostic that named the customerRef error.
- `ui/api/routers/racing.py` — the `place_lay` route (the
  reference origin; anchors in §5).
- `clients/betfair_client/v1/placement.py` — the `place_bet`
  surface and the send boundary where the Betfair request body is
  built (anchors in §5).
- `domain/bets/__init__.py` — the `StrategyTag` enum (§5.3).

**Reference-only (consult if needed, not required):**
- `dr029/2_4_betfair_streaming/placement_visibility_report.md` and
  `streaming_drop_visibility_report.md` — the two prior diagnostic
  layers.
- `dr029/2_4_betfair_streaming/betfair_stream_api_reference.md` —
  on-disk Betfair API reference.

---

## §4 — System access

- **Filesystem:** Mac, `bethub-v3` repo at
  `/Users/tim/Desktop/Projects/bethub-v3`. **Read-write on the §5
  anchors only.**
- **Git working tree is dirty by design** (v3 is fully
  uncommitted). Dirty-tree discipline (§9) is mandatory: **no**
  `git add` / `commit` / `stash` / `restore` / `checkout`
  (file-targeted) / `reset`. Read tree state at session start;
  edit only named anchors; `git diff <file>` after each edit;
  `git status --short` at close must show the same file set plus
  only the intended edits.
  - Note: `ui/api/` is currently **untracked** (`??`) — so
    `racing.py` edits will not appear in `git diff` of a tracked
    file; confirm them by reading the file. `placement.py` is
    **tracked-modified** (`M`) carrying the S162 diagnostic
    logging — preserve all of it; the §5.4 guard is **additive**.
- **Tests:** this repo is a `uv` project. Run the suite with
  **`uv run pytest -q`** (NOT bare `python3 -m pytest` — system
  python lacks `httpx`; S160 lesson). Baseline at session start is
  **1018** passing.
- **No live Betfair calls.** All verification is local /
  test-only. The live $5 lay is the operator's, after this session
  (§10).
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 for every
  time reference in the report.

---

## §5 — Substantive scope (the named changes)

Four changes. The shape: the **join key is made compliant by
construction** (never transformed at the boundary, because it must
match what is stored on the bet record); the **strategy label is
mapped to a compliant short form**; and a **send-boundary
tripwire** validates both so nothing over-length can ever reach
Betfair silently again.

### §5.1 — Compliant order-reference generation (`racing.py`)

**Anchor:** `ui/api/routers/racing.py`, the `place_lay` route,
line ~981:
```python
bet_id = body.bet_id or f"bet-record-{uuid4()}"
```

**Change:** replace the generated default with a Betfair-compliant
form via a small module-level helper. Design (locked):

- Prefix constant `_BETFAIR_REF_PREFIX = "bhl-"` (BetHub-lay; keeps
  orders recognisable as BetHub-originated in the Betfair
  statement / order history).
- Token = `uuid4().hex` truncated to **24** hex chars
  (`_BETFAIR_REF_TOKEN_LEN = 24`; 96 bits of randomness —
  collision-safe at the operator's volume).
- Total = 4 + 24 = **28 chars** (≤32 with deliberate headroom so
  the format can flex without re-breaching the cap).

```python
_BETFAIR_REF_PREFIX = "bhl-"
_BETFAIR_REF_TOKEN_LEN = 24

def _generate_lay_bet_id() -> str:
    return f"{_BETFAIR_REF_PREFIX}{uuid4().hex[:_BETFAIR_REF_TOKEN_LEN]}"
```
Then: `bet_id = body.bet_id or _generate_lay_bet_id()`.

**Invariant preserved:** `bet_id` is BOTH stored as the lay bet
record id (lines ~1036/1069/1084) AND sent as `customer_order_ref`
(line ~990). It stays a single round-tripped value — the
reconciliation join (Betfair echoes `customerOrderRef` ==
stored `bet_id`) is preserved by construction. Do not split it
into two values.

### §5.2 — Validate caller-supplied `bet_id` (`racing.py`)

**Anchor:** same route. `body.bet_id: str | None` can be supplied
by the caller (the quick-lay modal). Today it is normally `None`
(route generates), but a supplied over-length value would
reproduce the bug.

**Change:** if `body.bet_id is not None and len(body.bet_id) > 32`,
reject with the route's standard client-error (HTTP 422) **before**
calling `place_bet`, with a message naming the cause (e.g.
`"bet_id exceeds Betfair customer-reference limit (32 chars)"`).
Use the existing error-raising convention already in this router
(match the surrounding pattern; do not invent a new error shape).

The generated-default path needs no validation — §5.1 guarantees
≤32.

### §5.3 — StrategyTag → Betfair strategy-reference map (`betfair_client`)

**Anchor:** `domain/bets/__init__.py` defines `StrategyTag`
(values: `safety_net`, `price_booster`, `sgm_correlated`,
`synthetic_each_way`). The enum **values are not changed** (they
are stored on bet records — changing them is out of scope and has
blast radius).

**Change:** add a Betfair-format mapping + normaliser in the
**`betfair_client` v1 layer** (Betfair-format concerns belong
here, not in `domain`; import `StrategyTag` downward per DR-030 —
module layout / imports-downward). Place it in a small
placement-adjacent location (Code's call: a `_refs.py` sibling, or
within `placement.py` near the body build — keep it cohesive).

Explicit, exhaustive map to ≤15-char references:

| StrategyTag          | Betfair strategy ref | len |
|----------------------|----------------------|-----|
| `SAFETY_NET`         | `safety_net`         | 10  |
| `PRICE_BOOSTER`      | `price_booster`      | 13  |
| `SGM_CORRELATED`     | `sgm_correlated`     | 14  |
| `SYNTHETIC_EACH_WAY` | `synth_each_way`     | 14  |

Provide a normaliser usable at the send boundary that accepts the
**string value** currently threaded through `place_bet`
(`customer_strategy_ref: str | None`) and returns the compliant
≤15-char ref:

- `None` → `None` (unchanged).
- A known full StrategyTag value → its mapped short ref (only
  `synthetic_each_way` actually changes; the other three map to
  themselves).
- Make the map **exhaustive over the enum** — a future tag with no
  mapping must fail loudly (raise) in tests/dev rather than
  silently sending a wrong/over-length ref. (A test asserts every
  `StrategyTag` member has a mapping ≤15 chars.)

The bet record continues to store the full `strategy_tag` value
(the `strategy_tag=` argument to the bet write is unchanged) —
only the Betfair-bound `customer_strategy_ref` is shortened. Zero
blast radius on stored data.

### §5.4 — Send-boundary tripwire (`placement.py`)

**Anchor:** `clients/betfair_client/v1/placement.py`, where the
Betfair request `body` dict is built (the block containing
`"customer_order_ref": customer_order_ref` and
`"customer_strategy_ref": customer_strategy_ref`, ~lines 205–213).

**Change (additive — the S162 diagnostic logging and the existing
envelope/return branches are preserved byte-for-byte):**

1. Apply the §5.3 normaliser to `customer_strategy_ref` before it
   goes into `body`.
2. **Validate both references before the POST**, as a final
   chokepoint every placement flows through:
   - `customer_order_ref` length > 32 → **fail fast locally**:
     return a refusal write-envelope consistent with the existing
     refusal path (reuse an existing refusal reason if one fits;
     add a narrowly-named reason such as `customer_ref_invalid`
     only if needed — if added, name it in the report) and emit a
     WARNING log naming the reference and the cause, mirroring the
     existing S162 visibility lines. **Do not POST to Betfair.**
   - normalised `customer_strategy_ref` length > 15 → same
     fail-fast treatment.
3. The order-ref tripwire **must not silently truncate** the order
   reference — it is the reconciliation join key; truncation would
   break the round-trip. It validates and refuses; §5.1/§5.2
   guarantee it never fires in normal operation (it is a tripwire,
   not a transformer).

This guard is **separate from and does not modify the bet-safety
gate** (the never-place-a-lay-via-profit-target rule and the
stake/price/liability envelope). See §9.

---

## §6 — Sequencing within session

Dependency order (Code may deviate if a cleaner order emerges, but
this is the natural sequence):

1. **§5.3** — define the StrategyTag map + normaliser first
   (no dependencies; everything else can reference it).
2. **§5.1** — order-ref generator in `racing.py`.
3. **§5.2** — caller-supplied `bet_id` validation in `racing.py`
   (small, same file as §5.1).
4. **§5.4** — boundary tripwire in `placement.py` (consumes the
   §5.3 normaliser).
5. Tests for each (§7), then the full `uv run pytest -q` re-run.

---

## §7 — Empirical verification (pre and post)

Capture both states in the report so the fix is shown, not
asserted.

**Pre (at session start):**
- Confirm the generated default today is 47 chars
  (`len("bet-record-" + uuid4().hex-with-hyphens)` — show the
  construction and length).
- List `StrategyTag` members with value lengths; confirm
  `synthetic_each_way` = 18 (> 15).
- `uv run pytest -q` baseline = 1018 passing.

**Post (after the changes + new tests):**
- `_generate_lay_bet_id()` returns a 28-char ref with the `bhl-`
  prefix; show 3 sample outputs; assert ≤32 and uniqueness across
  many calls.
- Round-trip preserved: the value sent as `customer_order_ref`
  equals the value stored as the lay bet record `bet_id` (one test
  asserts identity end-to-end on the lay path).
- Caller-supplied `bet_id` > 32 → route returns 422, **no**
  `place_bet`/Betfair call (test).
- Strategy map: every `StrategyTag` → ≤15-char ref;
  `synthetic_each_way` → `synth_each_way`; map exhaustive over the
  enum (test); unknown/unmapped value raises (test).
- Boundary tripwire: over-length `customer_order_ref` → local
  refusal envelope + WARNING, **no POST** (test); over-length
  normalised `customer_strategy_ref` → same (test).
- **Bet-safety gate unchanged:** the existing gate tests stay
  green; show that the gate condition + the write envelope are
  byte-for-byte unchanged (diff evidence in the report).
- `uv run pytest -q` post = 1018 + N passing (N = new tests; state
  N and the final count).

---

## §8 — Output spec

**Single file:**
`dr029/2_4_betfair_streaming/customer_ref_fix_report.md`.

**Sections:**
1. Summary — what changed, in four lines.
2. Pre-state (the §7 baselines).
3. Per-change detail (§5.1–§5.4) — what was edited, where, the
   final diff per anchor.
4. Tests added — name each + what it proves.
5. Post-state (the §7 post checks) + final suite count.
6. Bet-safety attestation — explicit statement + diff evidence
   that the gate condition and envelope are unchanged.
7. Dirty-tree attestation — `git status --short` at start vs
   close; confirm same file set + only intended edits; no git
   state-changing commands run.
8. Findings / surprises (if any) — for next-session triage, not
   acted on.
9. Self-assessment — anything over/under the brief; anything Code
   would flag.

**Length anticipation:** ~150–300 lines. Not a hard line (per the
length-bends-to-detail standing rule) — but this is a tight
surgical fix; if the report runs long, say why in §9 of the
report.

**The report does NOT contain:** recommendations on the carried
parking-lot items, scope into other §2.x work, or any proposal
beyond the four named changes. Findings are named for triage, not
remediated.

---

## §9 — Hard limits (non-negotiable)

**Bet-safety gate — DO NOT TOUCH.** The hard rule carried from
v2's HedgeModal (NEVER place a lay via a profit-target order type)
and the stake/price/liability gate condition + write envelope are
**byte-for-byte unchanged**. This gate has refused every lay
across 5 live runs (S162) with the condition + envelope provably
unchanged across three diagnostic briefs — preserve that. The
§5.4 tripwire is a **separate, additive** reference-length guard;
it does not read, modify, reorder, or wrap the bet-safety gate.

**Preserve the S162 diagnostic logging.** `placement.py` carries
the drop/placement/failure-diagnostic logging from S162. The §5.4
guard is additive; do not remove, reorder, or alter the existing
WARNING lines or the existing envelope/return branches.

**No enum-value changes.** `StrategyTag` *values* in
`domain/bets/__init__.py` stay exactly as-is. §5.3 adds a mapping
*beside* the enum; it does not edit the enum.

**No schema / migration changes.** Do not add DB columns or
migrations. Adding a single narrowly-named refusal *reason* (§5.4)
is permitted only if no existing reason fits, and must be named in
the report.

**Named anchors only.** Edit only: `ui/api/routers/racing.py`
(§5.1, §5.2), the `betfair_client` v1 strategy-ref location
(§5.3), `clients/betfair_client/v1/placement.py` (§5.4), and the
corresponding test files. No drift into adjacent code "while
we're here."

**No git state-changing commands.** No `add` / `commit` / `stash`
/ `restore` / `checkout` (file-targeted) / `reset`. Read-only git
inspection (`status`, `diff`) only.

**Out of scope — named and excluded** (carried parking-lot; not
this brief): F1 uncaught-transport gap (connect/HTTP error → 500
not 503); 200-market over-subscription
(`SUBSCRIPTION_LIMIT_EXCEEDED`); in-memory audit-sink durability;
quick-lay modal generic-error surfacing; streaming hardening
(F3 keepAlive / F5 INVALID_CLOCK / F4 on-screen warning).

**Single bounded session.** If the work doesn't fit one session,
that's a finding, not a continuation. Partial-but-coherent beats
complete-but-lost-coherence.

---

## §10 — What happens after Code's session

Code produces `customer_ref_fix_report.md` and stops. The next
operator-Claude (Chat) session:
1. Triages the report (inventory-first; bet-safety attestation +
   round-trip + suite count are the load-bearing checks).
2. If clean → the **operator re-runs the live $5 lay** through
   `BetHub.command`; with compliant references it should now
   place. That closes the W17 racing-page operator-validation gate
   (and the accounts-setup $5-lay gate).
3. After the lay proves out → the carried robustness/cleanup items
   sequence (F1 transport gap, 200-market over-subscription,
   audit-sink durability), and W16 cutover scoping becomes the
   next routing decision.

Code does **not** write the next brief or run the live lay.

---

## §11 — Cross-references

- **Root cause:** S162 — `placement_failure_diagnostic_report.md`
  (+ `placement_visibility_report.md`,
  `streaming_drop_visibility_report.md`).
- **Workstream:** W17 (racing market pages) live-lay validation
  gate; accounts-setup $5-lay validation.
- **DR-032** (Betfair canonical reference layer + auto-login) —
  the auth/placement path this fix sits on.
- **DR-030** (v3 module layout / imports-downward) — governs the
  §5.3 strategy-ref map home (`betfair_client`, importing
  `StrategyTag` downward from `domain`).
- **DR-019** (derived state on read) — the lay bet-record write
  the route performs on success (balances/liability derive).
- **DR-021** (Adelaide timestamps) — report time references.
- **Bet-safety hard rule** — v2 HedgeModal carry; the
  carry-forward sensitivity flag in `current_state.md`.

---

**End of brief.**
