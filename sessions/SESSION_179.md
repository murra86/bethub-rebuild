# Session 179 — Promo-on-bet + credit-in review triaged; build scoped into two; Build 1 capture list locked; Build 1 brief queued

**Opened:** 2026-06-23 16:34 ACST
**Closed:** 2026-06-23 17:37 ACST
**Duration:** ~1h03m, single calendar day. Same-workday continuation
of S178 (closed 16:19 ACST; S179 opened 16:34, 15 min later).
**Tool routing:** Claude Chat (review triage + build scoping) +
Desktop Commander (governance reads; one live v3 schema read to
ground the Betfair-id question). No Code session this session — the
read-only review ran out-of-session between S178 and S179; this
session triages its report. No DB access.
**Governing DRs invoked:** DR-021 (anchors), DR-032 (Betfair canonical
/ the `promo_instance_id`-on-bet link — the documented-but-unbuilt
field the build serves; Q1 shifts what it documents), DR-033
(data-source roles — placings are the operator's manual flag, which is
what de-risks Area 3), DR-027/028 (cross-DB boundary — the placings
read is a future Piece-B concern, off the cutover path), DR-019
(derived P&L on read), DR-030 (module layering).

---

## Anchor

- Open: `2026-06-23 16:34 ACST` (session-open ritual; same-workday
  continuation of S178's 16:19 close).
- Close: `TZ="Australia/Adelaide" date` → `2026-06-23 17:37 ACST`.

## Pre-flight checks

Open ritual ran clean: drift-check passed (current_state ↔
SESSION_178 ↔ v3_build_picture all matched the 16:19 S178 close);
`.close_out_backups/` held only the S179 opening prompt; rebuild root
clean. Required reads completed in order (current_state,
standing_instructions in full, project_context, SESSION_178, the
S178 review brief). Same-workday tight recap; build picture +
open-items delta skipped as ritual noise on a 15-min continuation.

## Session shape

Two parts. First, the read-and-confirm gate: Code posted its
understanding of the read-only review brief before running; triaged
it against the brief, confirmed it faithful (all seven areas, hard
limits, output spec, sequencing correct), adjudicated the one item
Code kicked up (the S168 free-form/stake-back stance is superseded by
the operator's S178 structured-terms call — confirmed), and released
Code. Second, after Code ran the review out-of-session, triaged the
492-line report: inventory pass, classified each finding by
operational impact, surfaced the operator-relevant ones, settled the
four open questions (two Claude calls, two operator calls), grounded
one premise against the live schema, and locked the build scope into
two builds with Build 1's capture list fixed. Build 1 brief queued to
S180; no brief drafted this session.

## What was delivered

1. **Code's read-and-confirm gate triaged + released.** Code's
   understanding of the review brief was faithful — all seven areas,
   the read-only hard limits, output spec, and sequencing restated
   correctly. The one item Code flagged for the operator (the S168
   design's "free-form / stake-back covers it" stance vs the brief's
   §2 structured-terms mandate) was adjudicated: brief §2 is
   authoritative, the S168 stance superseded by the operator's own
   S178 call. Code's two stated defaults (size both validator options
   without deciding; read v2 for requirements only) matched the brief.
   Released with a ready-to-paste confirmation.

2. **Review report triaged (492 lines, faithful + clean).** Headline:
   both halves are greenfield-on-substrate. **Promo-on-bet not built**
   — no promo column on `bets` (grep-proven), and the `promo_ev_at_log`
   the brief assumed was persisted is silently dropped at the API
   boundary (O1 — corrects the brief's grounding premise). **Credit-in
   not built** — no production path writes a `free_bet_credited` event
   (grep-proven; only the deploy write and the audit log call
   `append_event`). The promo-event log, deploy write, pooled balance
   and inventory read are all built; the promo *attach* and the credit
   *write* are both absent. Settlement seam proven untouched by SHA.

3. **Build splits cleanly into TWO.** **Build 1 — promo-attach
   foundation:** tag each bet with the specific promo, the EV number,
   and the structured promo terms. Ships value alone (promos finally
   persisted/queryable). **Build 2 — credit-in + cycle link:** the
   credit write + read-back framing + the two confirm surfaces + Piece
   A cycle inheritance. Build 2 hard-depends on Build 1 (the confirm
   gate needs a promo on the bet). One session each; not combined.

4. **Area 3 de-risk — the build does NOT wait on the placings fix.**
   The brief worried the refund read-back would be blocked on the
   Racing-API placings backfill. It isn't: per DR-033 (data-source
   roles), place/ordinal settlement is the operator's manual flag — the
   operator supplies "did it place?" at the confirm step, reading the
   settled qualifier off the bet, strictly off `settlement.py`. The
   placings data is only needed for FUTURE auto-surfacing (Piece B,
   deferred). So promo-on-bet + credit-in runs parallel to the placings
   fix, not behind it. Report also flags: do NOT hook the manual-resolve
   path (`apply_manual_operator_resolution`) either — it's inside the
   settlement spine; the credit-in confirm is a separate post-settlement
   promo write.

5. **Operator decisions locked (the four open questions settled).**
   - **Credit amount (Q3 + the supersession tension).** The free bet
     (or cash) = the bet's **stake × the promo's return %** (e.g. a
     50%-back promo on a $50 bet → $25; a 100%-back promo → full
     stake). **No cap in the credit calc** — the operator always bets
     at-or-under the advertised cap, so the cap never changes the
     number; including it would be dead weight. **Caveat banked:** this
     holds *only* while bets stay at-or-under cap; a bet above cap would
     over-state the credit and would need the cap wired back into the
     calc. The cap is still **stored as a promo term** (for analytics),
     just not used in the credit maths. The return % **must** be stored
     and is load-bearing in the calc.
   - **Cash promos IN scope (Q4 / O4).** Cash refunds are in for
     cutover, same logic as free bets. Resolves the cash-credit sibling
     question — both the FB and cash credit-in paths are in scope.
   - **Persist the promo EV number (O1).** The operator's call: keep
     the adjusted/promo EV on the bet — it's important for later
     analytics, and adding it now (on the same Build 1 schema touch
     that adds the promo serial) is near-free vs a separate touch
     later. Goes into Build 1.

6. **Claude's technical calls (settled, not punted).**
   - **Q1 — which table is the serial.** Single-level home = a
     structured extension of the **kind-catalogue table**
     (`promo_template`-level, no run-window), **not** the instance
     table (`promo`), which carries the book + run-window the brief
     puts out of scope. This **shifts what DR-032 documents** (its
     `promo_instance_id` link currently points at the instance table) —
     a DR amendment rides with the Build 1 brief, next session. Code
     leaned the same way (O2).
   - **Q2 — the validator.** Option B: the promo serial doubles as the
     credit's promo reference (no validator relax). Preserves the
     shared cross-field invariant (FB + cash credit twin) and the
     existing inventory plumbing. Caveat for the build: the field is
     *named* `…_instance_id` while pointing at a type/serial — a
     doc/rename question, not a blocker.

7. **Betfair-id question grounded against live schema (own-miss
   corrected).** The operator asked whether the Betfair id is already
   on every bet; an earlier turn had flagged it as an "open question."
   Read `store/schema/bets.py`: the Betfair identity lives on
   **`bet_legs`** — `betfair_market_id`, `betfair_selection_id`,
   plus event/market/selection names, venue, sport — **all NOT NULL**,
   so every bet carries it mandatorily, and both entry paths populate
   it (race screen from its market; Log Past Bet via the Brief 2
   reverse-lookup). The join key to captured market data already
   exists — **nothing to add**. The earlier "open question" framing was
   an overcall; corrected by reading the schema rather than asserting.

**Build 1 capture list (LOCKED this session):** (a) the promo
reference / serial on the bet; (b) the promo EV number; (c) the
structured promo terms — places-refunded (which finishing spots
trigger the refund), free-bet-vs-cash, return %, and the cap stored as
a term (not in the credit calc). Betfair id already handled (on
`bet_legs`). Additive-column pattern; thread both entry paths + both
UIs; reconcile the two existing term representations (TS presets vs
seed JSON — O3) or discard one.

**Open findings routed to the builds (not chased this session):**
- O5 — `_coerce_uuid` falls back to a fresh UUID for non-matching bet
  ids; the credit write must stamp the **real** bet UUID as
  `triggering_bet_id`, or the Piece-A cycle resolve chases a phantom.
  → Build 2 requirement.
- O6 — no once-per-qualifier idempotency for crediting; the two
  confirm surfaces must converge on **one** write keyed to
  `triggering_bet_id`. → Build 2 requirement.
- O7 — `CreditStatus` unused by inventory derivation; write FINALISED
  for Piece 0; latent only if Piece B later leans on provisional
  credits. → Build 2 note.
- O3 — vocabulary drift between the two term representations. → Build 1
  reconciliation requirement.

## Standing-instruction adherence check

- **DR-021 anchoring (Cat 2):** open 16:34 + close 17:37 ACST. ✓
- **Silent session-open (Cat 1):** steps 1–5 silent; same-workday
  tight recap; build picture + open-items delta skipped (15-min
  continuation, ritual noise). ✓
- **Inventory-first cadence on long technical reports (Cat 1, S114):**
  the 492-line report was inventory-passed, each finding classified by
  operational impact; only operator-relevant items surfaced (two-build
  shape, placings de-risk, O1 grounding correction, Q3/Q4 calls). ✓
- **Make-the-call / don't punt (Cat 5):** Q1 + Q2 settled as Claude
  calls; Q3 + Q4 surfaced as operator calls. ✓
- **Don't surface dev-lead calls unless decision/operational angle
  (Cat 1, S163):** Q2 held to a one-line mention (no operator angle);
  Q1's DR-032 touch flagged (governance angle). ✓
- **Empirical verification — don't trust memory (Cat 3):** the
  Betfair-id question was grounded against the live schema rather than
  asserted; an earlier overcall was corrected. ✓
- **Ground "already built" claims (Cat 4, S178):** the review itself
  grounded the brief's `promo_ev_at_log`-persisted premise (found
  false — O1); the Betfair-id claim grounded before any brief lock. ✓
- **Plain-language / lead-with-the-call / brevity (Cat 1):** triage in
  plain gambling terms, one operator decision per round. ✓
- **`create_file` banned / verify every write (Cat 3):** all close
  writes via `Desktop Commander:write_file`; verified at Step 11. ✓

## Open items

Pointer-only — full live list in `current_state.md`.

## Open items out (closed / resolved S179)

- **Triage Code's review report + scope the build** — DONE. Report
  triaged; build scoped into two; Build 1 capture list locked. ✅
- **Run the Code review session (operator-side)** — DONE; the report
  exists and was triaged. ✅
- **The four report open questions (Q1–Q4)** — all settled: Q1
  (kind-catalogue table = Claude call), Q2 (Option B serial-as-ref =
  Claude call), Q3 (stake × return %, no cap in calc = operator), Q4
  (cash in scope = operator). ✅
- **O1 (promo EV dropped)** — RESOLVED by decision: persist the EV on
  the bet in Build 1. ✅
- **Betfair-id-on-bet question** — RESOLVED empirically: already on
  `bet_legs`, NOT NULL, both paths. Nothing to build. ✅

## New items in (S179)

- **Draft the Build 1 brief (promo-attach foundation)** for Code —
  S180 primary; the `bethub-brief-drafting` skill fires. Scope locked
  this session.
- **DR-032 amendment** rides with the Build 1 brief (the
  `promo_instance_id` link target shifts from the instance table to the
  kind-catalogue serial).

## Session close state

- **Rebuild root:** clean, no new files at root. No phantom files.
- **`current_state.md`:** rotated to S179 close (17:37 ACST);
  Where-we-are = review triaged, build scoped into two, Build 1 capture
  list locked; What's-next = S180 drafts the Build 1 brief.
- **`v3_build_picture.md`:** Interface-refinement stream next-milestone
  moved (review brief "LOCKED + handed to Code" → "review TRIAGED;
  build scoped into two; Build 1 brief (promo-attach foundation) drafts
  next session"); updated + timestamp bumped.
- **`standing_instructions.md`:** not edited this session (no new
  instruction surfaced). S178's pending re-upload to the Project KB
  still stands.
- **`.close_out_backups/`:** `SESSION_180_opening_prompt.md` written;
  stale `SESSION_179_opening_prompt.md` removed.
- **Operator-side actions flagged:** (a) re-upload
  `standing_instructions.md` to the Project KB (carryover from S178);
  (b) carry-overs below.

## Forward routing (confirmed with operator)

Operator confirmed close after the routing recommendation (close S179,
queue the Build 1 brief, draft it fresh next session). **S180 drafts
the Build 1 brief (promo-attach foundation)** for Code via the
`bethub-brief-drafting` skill. Locked scope: promo serial + EV number +
structured terms (places-refunded, FB-vs-cash, return %, cap-as-term)
onto the bet; single-level home = the kind-catalogue table; reconcile
the two term representations; additive-column pattern; thread both
entry paths + both UIs; the DR-032 amendment rides with the brief.
**Build 2 (credit-in + cycle link)** follows Build 1 (hard dependency).
The **Racing-API placings backfill + nightly results-sync fix** runs
**parallel** — confirmed NOT a blocker for the promo-on-bet + credit-in
build (it's the future auto-surfacing enabler, Piece B). Post-build
sequence unchanged: launcher brief (F9/F10 + F12 +
rebuild-if-source-newer) → W16 cutover scoping. Forward routing
confirmed.
