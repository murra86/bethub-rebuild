# Session 139 — DR-025 hedge-classification revisit closed: six-state model confirmed; lay substrate = side + commission (mirroring v2); commission sourced from Betfair per-market MBR; W12.1 grounded, briefs deferred to S140

**Opened:** 2026-05-21 16:44 PDT (Vancouver — temporary
timezone display window active until 2026-06-08; canonical
project zone remains Adelaide per DR-021; ACST equivalent
2026-05-22 09:14 ACST).
**Closed:** 2026-05-21 18:00 PDT (ACST equivalent
2026-05-22 10:30 ACST).
**Wall-clock active session:** ~1h16m.
**Tool routing:** Claude Chat (governance revisit + DR-025
amendment authoring; empirical reads against the live v3
codebase at `/Users/tim/Desktop/Projects/bethub-v3/` and the
live v2 `bethub.db`). No Claude Code dispatch. W12.1 and W15
briefs deferred to S140 (Chat drafts both).
**Governing DRs invoked:** DR-025 (hedge classification —
revisited and amended this session), DR-019 (derive-on-read —
liability stays derived, not stored), DR-032 (canonical bet
record / bet_legs), DR-021 (timestamp anchoring; Vancouver
display override active), DR-026 / architecture.md §A.10
(Betfair canonical for market facts incl. commission rate).

## Anchor

```
# Session-open (Vancouver per temporary instruction):
TZ="America/Vancouver" date "+%Y-%m-%d %H:%M %Z"
# Open output: 2026-05-21 16:44 PDT

# Session-close:
TZ="America/Vancouver" date "+%Y-%m-%d %H:%M %Z"
# Close output: 2026-05-21 18:00 PDT
```

## Pre-flight checks

Session-open ritual ran per `bethub-session-open` skill.
Required reads completed (`current_state.md`,
`standing_instructions.md` in full, `project_context.md`,
`SESSION_138.md`). Pre-flight directory listing: clean root,
13 .md files plus openapi.json, no phantoms.

**Drift-check (Step 5):** clean.
- (a) `current_state.md` "Last updated" 2026-05-21 16:34 PDT
  matched `SESSION_138.md` "Closed:" timestamp.
- (b) `SESSION_138.md` present, non-empty (401 lines).
- (c) `v3_build_picture.md` "Last updated" 2026-05-21 16:34
  PDT — correctly updated at S138 close (W12 → done, W15 →
  in flight). Render condition TRUE; build picture rendered
  at open.
- `.close_out_backups/` held `SESSION_139_opening_prompt.md`
  as expected from S138 close.

## Session shape

A governance-revisit session. Revisited DR-025 (the five-
terminal-plus-one-transient hedge-classification model) per
the standing "revisit before W15 brief drafting" flag, drove
five decision points to resolution, and wrote an amendment to
`decisions.md`. Then grounded the W12.1 lay-balance surgical
fix empirically (v3 derivation code + v2 model). Both briefs
(W12.1, W15) deferred to S140 after a Desktop Commander read
timeout plus the operator's stated context-budget caution
triggered a split (Session 11 lesson — split rather than
push through).

## What was delivered

**1. DR-025 revisit closed — six-state model confirmed.**
The five-terminal-plus-one-transient model
(`hedged` / `hedge_partial` / `hedge_failed` /
`unhedged_deliberate` / `unhedged_oversight` /
`unhedged_unclassified`) stands as-is — no change to states,
auto-classification flow, or settlement+24h auto-resolve.
Operator decisions:
- `unhedged_oversight` kept. Rare but real (busy bursts);
  operator-set-only (no auto-path); it is a label that never
  feeds the balance maths, so retaining it adds no
  calculation or data-capture risk.
- No new state for "lay placed only to convert a free bet" —
  a hedge is a hedge; the cash-vs-free-bet distinction is
  derived from the bet the lay is placed against (carries
  `is_free_bet`), with shared `cycle_id` carrying the
  upstream journey.
- Lay recording mirrors v2: the lay is its own bet record,
  in the same operation as the bet it covers, traceable
  upstream; purpose (turnover vs free bet) derived, not a
  separate state.

**2. Lay substrate decided (the load-bearing output).** Two
stored fields close the W12 lay-side gap, mirroring v2's
`bets` table: (a) a side tag (LAY/BACK), (b) a commission
rate. Liability is NOT stored — derived on read from matched
price + matched stake + side per DR-019. Grounded
empirically: v2 `bets` carries `side` + `commission` (+401
lay rows, commission 0.06–0.10); v3 store schema has neither
(grep-confirmed). v3 `domain/bets` defines `BetSideTag`,
`Construction`, `HedgeSoftBookStakeKind` enums but does not
persist side; no commission field anywhere; no liability
field. The defined lay maths is unchanged — the substrate
just supplies the two missing read-side inputs.

**3. Commission sourcing decided — Betfair per-market MBR,
not a track table.** The commission rate is Betfair's per-
market base rate (`marketBaseRate`), snapshotted at hedge
entry, 8% fallback. Grounded in v2's current method
(`_get_commission_for_market` in `betfair_sync.py`, reads
`description.marketBaseRate` ÷ 100). **Corrected the
operator's "track table" recollection:** v2's prior table-
based venue/race-type lookup drifted and misclassified some
markets (NSW/ACT thoroughbred, NRL); reading Betfair's
authoritative per-market rate is why rates come out track-
accurate (the Queensland-4% case is simply Betfair's rate
for those markets). Account-level discount tier out of scope
per v2 precedent.

**4. Separation established — balance vs classification.**
Balance correctness depends only on the two-field substrate
(side + commission); it does NOT depend on the hedge-
classification state machine. The two were coupled in the
S138 framing; this revisit established they are separable —
the lay-balance fix needs neither the `hedge_state` column
nor the auto-classification flow.

**5. DR-025 amendment written to `decisions.md`.** Amendment
2026-05-22 (Session 139), appended after DR-025's date line;
original DR-025 text untouched, DR-026 intact. Verified:
amendment body lines 733–747; DR-026 header at 753.

**6. W12.1 grounding done (brief deferred to S140).** Edit
anchors in `workflows/balances/v1/balance_derivation.py`:
- `_read_bet_rows_for_account_at_book` (~L136) — SELECT adds
  `side`, `commission`, `book_or_exchange`.
- `_bet_cash_return` (~L151) — add LAY branch. Standard
  exchange settlement maths: lay win (backed selection
  loses) → +matched_stake × (1 − commission); lay loss →
  −matched_stake × (matched_price − 1); void → 0.
- `_bet_pending_cash_stake` + `_bet_cash_stake_committed`
  (~L202 / L217) — for a lay the committed/reserved cash is
  the liability (stake × (price − 1)), not matched_stake.
- `compute_account_at_book_balance` (~L235) — ensure lay
  rows route through the lay maths.
Substrate columns land in `store/schema/bets.py`; read query
in `store/repositories/bets.py`. Brief instructs Code to
cross-check the implemented lay maths against the
`domain/bets` math-review and surface any mismatch as a
finding.

**7. Dirty-tree state captured for the W12.1 brief.** The v3
working tree is heavily dirty/untracked: the whole W12 build
(`workflows/balances/`, `store/schema/bets.py`,
`store/repositories/bets.py`) is UNTRACKED — shipped, never
committed — alongside modified `clients/betfair_client/*`,
`domain/bets/__init__.py`, `store/__init__.py`, `pyproject
.toml`, `uv.lock`. The W12.1 anchors sit inside this
untracked region (expected — building on W12's output, not
drift). The W12.1 brief carries strict dirty-tree git
discipline: no git operations; edit named anchors only;
`git diff`/`git status` verify only intended changes land.

## Standing-instruction adherence check

- **Cat 1 silent open-ritual — PARTIAL (again).** No numbered
  step headers, but connective narration remained ("I'll run
  the open ritual…", "Anchor captured. Now the required
  reads."). Same shape as S138. Streak not re-established;
  S140 open is the next watch point.
- **Cat 1 calendar-calibrated recap** — honoured (same-
  workday, tight; ~10-min gap from S138 close).
- **Cat 1 build-picture conditional render** — honoured
  (rendered at open; streams moved at S138 close). 19
  consecutive clean S120–S139.
- **Cat 1 plain-language operator framing** — honoured
  (lay/commission in real gambling terms; no schema-speak).
- **Cat 1 escalate-to-detail-only-when-warranted** —
  honoured (flagged "this deserves a little detail" before
  the substrate findings).
- **Cat 1 over-surfacing pullback** — honoured late: showed
  the full amendment text for review, operator declined to
  read it, corrected immediately to a four-bullet "what you
  need to know + decisions required" summary.
- **Cat 3 empirical-verification-before-asserting** — strong.
  v2 lay recording verified against live `bethub.db`;
  commission method verified against v2 source (operator's
  track-table recollection corrected); v3 schema gap grep-
  confirmed; balance derivation read directly before
  specifying anchors.
- **Cat 3 governance-artefact edit discipline** — honoured.
  Re-read DR-025 live before amending; verified post-write.
- **Cat 5 make-software-calls-don't-punt** — honoured (#3
  substrate and #5 sequencing called, not punted).
- **Cat 2 timestamp anchors / required reads / pre-flight /
  drift-check** — honoured.
- **Split-rather-than-push (Session 11)** — honoured: DC
  read timeout + context caution → deferred briefs to S140.

## Open items in (carry to S140)

- **W12.1 lay-balance brief drafting — PRIMARY S140.**
  Surgical fix; grounding complete (anchors, lay settlement
  maths, substrate columns, dirty-tree discipline above).
  Standalone Code brief; may precede W15.
- **W15 ops-log brief drafting — S140, after W12.1.** Two
  housekeeping folds carry: explicit `workflows-independent`
  import-linter carve-out; `.venv/bin/python` 3.12 anchor in
  the Code opening prompt.
- **Vancouver timezone override** — active through
  2026-06-08; revert to Adelaide anchors at first open on or
  after that date.

## Open items out (closed S139)

- **DR-025 hedge-classification revisit** — closed; six-state
  model confirmed; amendment written to `decisions.md`.
- **Lay substrate decision** — locked (side + commission;
  commission from Betfair MBR; liability derived).

## Carry-forward sensitivity

- **Cat 1 silent open-ritual** — partial again (connective
  narration); S140 watch point. Promotion-to-encoded-rule
  candidacy still weakened.
- **Cat 1 build-picture render** — 19 consecutive clean.
- **Cat 3 empirical verification** — strong instance
  (commission-sourcing recollection corrected against v2
  source).
- **Desktop Commander flakiness** — one ~4-min read timeout
  this session (recovered by close). Watch at S140.

## Session close state

- **`decisions.md`** — DR-025 amendment added (lines
  733–747). Only governance file substantively edited this
  session. **Operator-side action: re-upload `decisions.md`
  to the bethub-rebuild Project knowledge base** (it is a
  canonical KB doc per `project_context.md` §6; local disk
  copy is now ahead of the KB copy).
- **`current_state.md`** — rotated to S139 close.
- **`v3_build_picture.md`** — W12 dropped (one-session carry
  expired); W12.1 added; W15 next-milestone updated.
- **Rebuild root:** 13 .md files plus openapi.json
  (unchanged count).
- **`.close_out_backups/`:** `SESSION_140_opening_prompt.md`
  (stale `SESSION_139_opening_prompt.md` swept).
- **`sessions/`:** this file (`SESSION_139.md`).
- **v3 codebase:** unchanged this session (read-only
  grounding reads). Dirty/untracked state noted above.
- **Project knowledge base:** `decisions.md` edited → flagged
  for re-upload above.

## Forward routing

**Confirmed with operator** — S139 closed the DR-025 revisit
and wrote the amendment. S140 drafts the **W12.1 lay-balance
brief first** (small, fully grounded this session), then the
**W15 ops-log brief**. Operator confirmed close-out after a
Desktop Commander read timeout plus context-budget caution;
agreed to defer brief drafting to S140 on a fresh budget
rather than push a large brief through a flaky tool — the
clean split rather than push-through.

## Close-out notes

~1h16m. A clean governance-revisit session: closed the long-
standing DR-025 before-W15 flag and wrote the amendment. The
standout was the empirical digging — it corrected the
commission-sourcing approach (Betfair per-market MBR, not the
static track table the operator recalled; the v2 lesson) and
surfaced the separation finding (the lay-balance fix needs
only side + commission, not the hedge-classification state
machine, so W12.1 runs independently of W15). Briefs deferred
to S140 after a DC timeout — split rather than push (Session
11 lesson). Cat 1 silent-open-ritual remains the one self-
flagged drift. No structural drift; one DR amendment (locked
text untouched, appended note only).
