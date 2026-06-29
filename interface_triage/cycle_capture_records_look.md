# Cycle-capture records-look (Session 167 step zero)

**Anchor:** 2026-06-19 ACST. Step zero before the
cycle-capture brief is drafted, per the S166 close
("a look at what v3's bet records capture today —
whether a free bet already links back to its
originating qualifier, or whether that link must be
built; may surface a small storage-design call").

**Method:** read-only source review of `bethub-v3`
bet-storage layer — `store/schema/bets.py`,
`store/repositories/bets.py`, `ui/api/routers/racing.py`,
`workflows/bet_entry/v1/record_builder.py`,
`ui/web/src/api/racing.ts`, `LogBetPanel.tsx`,
`domain/settlement/`. No DB read, no writes.

---

## Finding 1 — the link mechanism already exists in storage

Every bet row carries a `cycle_id` (NOT NULL) on the
`bets` table (`store/schema/bets.py:21`). Bets that
belong to one cycle share a `cycle_id`
(`domain/bets/__init__.py:142`). The bet-logging API
already accepts a `cycle_id` on the request body —
`None` generates a fresh one, a supplied value is
reused (`racing.py:474` `cycle_id: str | None = None  #
None → fresh`; `racing.py:892` `cycle_id = body.cycle_id
or str(uuid4())`). The record builder treats `cycle_id`
as optional, "omitted = the cycle's first bet"
(`record_builder.py:91,103`).

**Consequence:** linking a triggered free bet to its
originating qualifier needs **no new schema, no
migration**. The storage already supports it. The link
is "pass the qualifier's `cycle_id` when logging the
free bet."

## Finding 2 — the UI never uses the tag (the real gap)

`LogBetPanel.tsx` does not set or pass a `cycle_id` in
its POST body (grep: no `cycle_id`/`cycleId`/post-body
reference in the component; only the API type defs in
`api/racing.ts:214,252,275` and a test fixture carry
it). So in practice **every bet logged today starts a
fresh cycle** — nothing ties a free bet back to its
qualifier. The link is unbuilt at the UI layer.

**Cycle-capture piece A (frontend):** give the operator
a way, when logging a triggered free bet, to tag it to
the parent qualifier's cycle (surface recent
qualifiers / open cycles, pass the chosen `cycle_id`
through the existing API). Frontend + existing
contract; no storage change.

## Finding 3 — realised-conversion column exists but is never populated

`realised_conversion_rate REAL` exists on `bets`
(`store/schema/bets.py:25`, "W5 populates"). In
practice it is **always written NULL** — the record
builder sets `realised_conversion_rate=None`
(`record_builder.py:315,394`); `domain/settlement/` is
an empty stub (`__init__.py` only); no code computes or
writes a real value. Balance derivation only *reads* it
(`balance_derivation.py:142,260`). So the "true 72% vs
65% planning assumption" figure has a home but no
filler.

**Cycle-capture piece B (the storage-design call):**
how does the real conversion get into the record?

- **DECISION (operator, S167): manual entry now,
  auto-at-settlement later.** Operator types the
  realised figure once the free bet's cycle completes.
  Fits the S166 scope line (capture pre-cutover,
  analytics post-cutover) and avoids building
  settlement now. Auto-derivation at settlement is an
  explicit known successor — **the manual field must be
  designed forward-compatible with auto-population**
  (the manual write path must not block settlement from
  later computing the same field). Claude-side design
  constraint to carry into the brief.

## Follow-on deliverable (named)

**Manual-process how-to** — a plain operator-facing
walkthrough of how the operator records the realised
conversion by hand in the meantime. Operator explicitly
asked to be briefed on this. Timing: after the
cycle-capture UI shape is locked (so it describes real
fields/clicks). Operator-facing runbook, not a
Code brief.

---

## Net for the cycle-capture brief

Not a heavy new-schema job — the columns exist. Two
pieces:

- **A — frontend link affordance.** Tag a triggered
  free bet to its qualifier's cycle via the existing
  `cycle_id` API. Frontend-only.
- **B — manual realised-conversion entry.** A capture
  field that writes `realised_conversion_rate`,
  designed forward-compatible with later auto-populate
  at settlement. Reaches bet-record write.

Plus the named follow-on operator how-to once the UI
shape is locked.
