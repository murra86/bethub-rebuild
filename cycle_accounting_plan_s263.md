# Cycle accounting (worklist 0t-B) — build plan, S263

**Status:** PLAN ONLY — no code changed, no data touched. Commissioned by the
operator ("develop plans and conduct review"); an adversarial review of this
plan follows before anything is built.
**Evidence base:** `bet_integrity_audit_s260.md`, `pl_audit_s260.md`,
`lay_matching_brief.md` (incl. its normative v2 review), live store re-read
2 Aug 2026 (read-only), and the shipped code as of v3 `dd7daec`-era main.
**Acceptance bar (operator, verbatim):** *100% OF CYCLES ACCURATELY TRACKED* —
completeness + correctness: an audit, a repair, and an ongoing check so it
stays there. Acceptance is a reconciliation with a number.

---

## FOR THE OPERATOR — what this plan gets you

**The problem in one sentence:** every bet already belongs to a group (your
insurance bet, the free bet it earned, the hedge on Betfair), but the tool has
no page that shows those groups as complete plays — no list of which plays are
still in flight, no "this play made $X end to end", and until last week the
hedges weren't even landing in the right group.

**What has already been fixed (before this plan):** the hedge-linking bug is
fixed and proven live — every lay placed on 31 Jul and 1 Aug linked itself,
and I re-checked the store today: not one new unlinked hedge since the fix
went in. The 34 old mis-grouped rows have their own approved repair waiting
for your go-ahead; this plan assumes that repair lands first.

**What this plan builds, in order:**
1. **A checker you can run any time** that examines every bet and every group
   and prints one number: what percent of your plays are perfectly grouped.
   That number is the acceptance test — it must say 100%.
2. **A repair path** for anything the checker still finds after the 34-row
   repair (today's data suggests: nothing, or very little).
3. **A standing line in your daily money check**: the same number every day,
   plus a list of plays still in flight, plus a flag the day anything drifts.
   Flags only — nothing ever blocks a bet.
4. **The view**: a "group by play" switch on BetLog, so a play shows all its
   bets together with one profit number — even when it spans two days —
   plus whether it is still open. My recommendation on where it lives is
   below; the call is yours.
5. **The last profit-figure tidy-ups** from the S260 audit — including
   removing the one input box that could silently understate a bonus win if
   anything were ever typed into it.

**What does not change:** no stake, price, result, or per-bet profit figure.
Your rule stands everywhere: an unused bonus is never counted as profit until
it is converted to cash. Your 2 Aug decision stands: banked bonus cash is
cash, one P&L figure.

**Confidence: HIGH** that this reaches 100% and keeps it there — the hard
part (why hedges never linked) is already fixed and live-proven, the store
today holds zero new drift, and the remaining work is counting, showing, and
guarding, not changing money. **Two open decisions are yours** (when a play
counts as "finished", and where the view lives) — recommendations given,
neither blocks the first build phase.

**Next step:** adversarial review of this plan, then build in the phase order
of §8.

---

# Technical plan

## 0. Current-state deltas this plan builds on (all verified 2 Aug)

| Delta | Verified how |
|---|---|
| Forward lay-linker LIVE (0t-A, v3 `6c0e287`+`1f3a7f5`); 61/61 replay | Store re-read: **zero** lays placed after 30 Jul sit in a back-less cycle — the linker held through two race days |
| 34-row historical repair PROPOSED (32 stranded lays + 2 mis-linked FBs), separate stream, operator confirmation pending | `lay_matching_brief.md` §3 + v2 review; **this plan assumes it lands first** and takes cycle coherence to ~99% |
| Bonus-winnings credits auto-bank on Won, `source=SYSTEM` | `workflows/promos/v1/auto_credit.py` (1b part c); Burst Review auto-lane is the review path, undo is the correction path |
| Operator decision 2 Aug: **bonus cash IS cash — one P&L figure** | `BetLog.tsx:1689` comment + `pnl_all_in` live (`bets.py::_period_stats` folds window promo cash, `occurred_at`-scoped, finalised + non-superseded) |
| Corrections keep original economic dates | The 2 Aug Bet365 rounding corrections: `recorded_at` 06:15 2 Aug, window scoping reads `occurred_at` |
| Per-template `credit_rounding` term exists | `auto_credit.py:148` → `credit_kwargs_for_kind(credit_rounding=…)` |
| FB face value never in P&L until converted | Operator-locked; verified structurally in `pl_audit_s260.md` area 3 — this plan preserves it in every new figure |

Live store snapshot (2 Aug, read-only): **466 bets, 339 cycles**, composition
back-only 224 · back+FB+lay 45 · **lay-only 32** (the repair's population,
unchanged) · back+FB-no-lay 31 · goodwill FB+lay 4 · FB-only 3 · 10 cycles
span >1 date · 17 promo-cash credits, **all 17 carrying `triggering_bet_id`**
(cycle attribution needs no schema change) · 1 `free_bet_expired` event
(Sarie-Ladbrokes $10 goodwill, 1 Aug — the concrete case behind the
closed-cycle question) · 1 legitimately two-lay cycle (`87957d21`, one lay
**voided** — void-and-replace) · 0 cycles with two cash backs · 5 legless
manual bets (4 sports, 1 conditioning).

Key structural facts carried forward:
- There is **no cycles table and no stored cycle state** — `cycle_id` is a
  NOT-NULL grouping string on `bets`. This plan keeps it that way (state is
  derived, §1.3).
- There is **no `settled_at` column** (pl_audit "CANNOT VERIFY" item) — close
  dates use a proxy (§1.4).
- Cycles legitimately span **markets** (qualifier on race A, FB on race B),
  **accounts and persons** (lays on one Betfair account, backs across 4
  account_ids — review L6: never scope pairing by identity), and **dates**.

## 1. The cycle-as-a-set model

### 1.1 Origin classes

Every cycle has exactly one **root**, which defines its class:

| Class | Root | How recognised from data |
|---|---|---|
| **Qualifier-rooted** | one cash BACK (promo-tagged or plain) | the only `is_free_bet=0` non-LAY member |
| **Goodwill-rooted** | one deployed FB whose funding credit has **no** `triggering_bet_id` | `resolve_inherited_cycle` returned None by design — a fresh cycle is CORRECT here (e.g. the Sarie-Ladbrokes $30s, the Allbets $100) |
| *(future, if it ever occurs)* standalone LAY intentionally unhedged-back | — | none exist; treated as a defect unless operator-assigned |

The audit must **class goodwill-rooted cycles as coherent**, not as "FB with
no qualifier" — 7 such cycles exist today and are correct.

### 1.2 Membership rules — "the right cycle", operationally

A bet is **in the right cycle** iff its class's rule holds:

1. **Cash BACK** (incl. manual/sports/conditioning): roots its own cycle.
   Right by construction; constraint: **at most one cash BACK per cycle**
   (0 violations today).
2. **Deployed FB**: its cycle **must equal** the re-derivation
   `resolve_inherited_cycle(consumed credit events)` — oldest consumed
   credit (FIFO by `recorded_at`) → `triggering_bet_id` → that qualifier's
   `cycle_id`; or a fresh cycle iff no credit carries a triggering bet
   (goodwill). This is recomputable from `promo_events` independently of the
   stored `cycle_id` — exactly the audit's Check 2, now a standing rule.
3. **LAY**: its cycle must hold ≥1 non-LAY bet on the same
   (`betfair_market_id`, `betfair_selection_id`) — via `bet_legs` — and a
   cycle holds **at most one non-voided LAY per selection** (the voided-lay
   exemption is required: `87957d21` is a legitimate void-and-replace).
   A LAY alone in its cycle while a back exists on the same
   market+selection elsewhere = a **stranded lay** (the D8 class).
4. **Legless manual bets** (`bet_code` sports/conditioning, no `bet_legs`
   row): single-bet cycles, coherent; excluded from all lay-pairing rules
   (they are invisible to leg joins — the audit must count them explicitly
   rather than silently skip).

**No-splits rule (set-level):** no two cycles may hold the two halves of one
play — operationally, no lay-only cycle whose matching back (same
market+selection, lay-before-back within the pairing window) lives in
another cycle, and no deployed FB in a different cycle from the one rule 2
derives. **No-orphans rule:** every bet carries a non-empty `cycle_id`
(schema-enforced; audited anyway).

A **cycle is accurately tracked** iff every member passes its rule, no
outside bet belongs to it under those rules, and its composition is one of
the coherent shapes. Note "no lay" is a coherent shape — laying is optional
(FBs sometimes ride unhedged); the 30-minute FB-missing-lay watchdog remains
the *timeliness* flag and is not a membership defect.

### 1.3 State semantics — open/closed (DERIVED, never stored)

**A cycle is OPEN iff value is still in flight:**
- any member bet unsettled (`settlement_state` NULL/pending/provisional), or
- any **live** FB credit rooted in the cycle — a `free_bet_credited` whose
  triggering bet is a member and whose supersession chain has **no terminal**
  (not consumed, not revoked, not expired).

**Otherwise CLOSED.** No stored column, no migration, no write path: state is
a read over `bets` + `promo_events`. A late credit, a redeploy, or a late
lay pairing **reopens the cycle automatically** because the derivation
re-evaluates — this is why deriving beats storing (an insurance loser whose
book pays a surprise credit two days later needs no operator action to
reopen; the credit-gap lane remains the "is one owed?" backstop, exactly as
today).

**The operator's closed-cycle question — FB expired unused / revoked unused
(THE CALL IS THE OPERATOR'S; recommendation below):**

- **Option A (RECOMMENDED): the terminal event closes the cycle.** An
  expired or revoked-unused credit is a terminal on its chain, so the cycle
  closes on that event's date, at the money that actually moved (the
  qualifier's loss stands; the face value contributes nothing — consistent
  with the locked FB rule). The view marks it **"bonus expired unused"** so
  it reads as what happened, not as an ordinary loss. Live example: the
  Sarie-Ladbrokes $10 (1 Aug) closes 1 Aug at $0.00 with the marker.
- **Option B: hold open until operator dismissal.** Rejected on friction
  grounds: it grows the in-flight list forever and adds a click per expiry
  for information the terminal event already carries.
- Same rule for **never-deployed revoked** credits (2 exist). A credit
  still **live in hand** keeps the cycle OPEN (value genuinely in flight —
  matches the "Bonus bets in hand" tile).

### 1.4 Cross-date cycles and the close-date proxy

Cycles are date-free sets; **dates enter only at the aggregation/view
layer**. The cycle-complete figure attributes a cycle's whole net to its
**close date** := max(member `placed_at` dates, terminal promo-event
`occurred_at` dates). This is a proxy — the store has no `settled_at` —
and it is honest for this operation: racing settles minutes after the jump,
so a member's settle date ≈ its placement date, and credit terminals carry
true `occurred_at` (corrections keep economic dates, so the proxy survives
corrected history). The limitation is documented on the surface (a bet
placed 23:5x that settles after midnight books to placement day — same
behaviour every existing figure has today). Adding a real `settled_at` is a
larger, separate decision (§9.5); nothing in this plan depends on it.

### 1.5 Cycle-complete net ("all-in")

`cycle_net_all_in = Σ bet_net_pnl(member, commission_share)` over settled
members **+ Σ finalised, non-superseded promo-CASH credits whose
`triggering_bet_id` is a member** (the 2 Aug bonus-cash-is-cash decision
carried to cycle level — today both `CycleChain.Net` and the money check's
cycle nets omit this term; pl_audit area 7 flagged exactly this). All 17
live cash credits attribute cleanly via `triggering_bet_id`. Account-anchored
cash credits with no triggering bet attribute to **no cycle** — correct:
book generosity, not a play (they already reach the all-in P&L via the
window term). FB face value appears nowhere, deployed FB winnings arrive as
the FB bet's own `bet_net_pnl` — both unchanged.

Commission shares come from the existing whole-store
`lay_commission_by_bet` read (a market's sibling lays can sit outside the
cycle) — same derivation `settlement_review` uses today; no new arithmetic.

## 2. THE AUDIT — `ops/cycle_audit.py` (the acceptance number)

A new read-only ops command on the `settlement_review` conventions
(`mode=ro`, never writes, never blocks):

    uv run python -m ops.cycle_audit            # full population, no windows
    uv run python -m ops.cycle_audit --verbose  # violation list by bet/cycle id

**Population: every bet, every cycle, no date window** — windows are how 32
defects hid behind "1". For each bet it recomputes the §1.2 expected cycle
from raw data (promo events for FBs, legs+timing for lays) and diffs against
the stored `cycle_id`; for each cycle it classifies composition.

**Coherent classes:** qualifier-only (any settle state) · qualifier+FB(±lay)
· goodwill-rooted FB(±lay) · plain/manual single-bet · void-and-replace
shapes (voided members + replacements).
**Defect classes (each with its sanctioned fix named in the output):**

| # | Defect | Detection | Sanctioned fix |
|---|---|---|---|
| C1 | Stranded lay (lay-only cycle, matching back elsewhere) | rule 3 + cross-cycle probe | `ops/repair_lay_cycles.py` batch / BetLog assign-cycle |
| C2 | Mis-inherited FB (stored ≠ derived qualifier cycle) | rule 2 re-derivation | assign-cycle (audited move) |
| C3 | Two live (non-voided) lays on one selection in one cycle | rule 3 | assign-cycle split |
| C4 | Two cash backs in one cycle | rule 1 | assign-cycle split |
| C5 | FB with no live funding | existing `list_source_pending_spends` | credit doors / burst review |
| C6 | Orphan/empty `cycle_id` | direct scan | assign-cycle |
| C7 | Cash credit whose triggering bet is missing | promo scan | `ops.correct_promo_chain` |

**The output ends with the acceptance number:**

    CYCLES: 339 · ACCURATELY TRACKED: 305 · 90.0%
    BETS IN COHERENT CYCLES: 432 / 466 (92.7%)
    DEFECTS: C1×32 C2×2   (violation ids follow with --verbose)

Acceptance for 0t-B = this command printing **100.0% on both lines** against
the live store (Phase 7), and the daily invariant (§4) holding it there.
Both percentages print because the operator's bar is cycles, while bets are
the honest denominator when a single cycle holds many bets.

The classifier lives in a **workflows module**
(`workflows/bet_entry/v1/cycle_audit.py` alongside `cycle_pairing.py`), so
the ops command and the daily check import ONE copy — no drift between "the
audit" and "the invariant" (the S259 lockstep lesson applied to itself).

## 3. THE REPAIR — what remains after the 34-row fix

The 34-row repair (separate stream, operator gate: app quiet + backup, FBs
first, raw UPDATE + `bet_edited` in one `BEGIN IMMEDIATE`, identical
before/after snapshot as the no-money-moved proof) takes the store to ~99%.
**This plan's own repair scope is whatever Phase 1 still finds**, expected
small or zero:

1. **Nothing new since the linker shipped** — verified today: zero
   post-30-Jul stranded lays. The 32+2 are exactly the proposed repair's
   population.
2. **Goodwill-rooted LF/F cycles are NOT defects** — they are fixed by the
   *model* (§1.1 classification), not by moving data. The audit stops
   miscounting them; no rows move.
3. **Any residue the post-repair audit run surfaces** goes through existing
   sanctioned paths only: the BetLog assign-cycle control for single moves;
   an extension of the `repair_lay_cycles.py` batch pattern (dry-run
   default, `--apply`, one txn, per-row audit event) if a batch class
   appears; `ops.correct_promo_chain` / `ops.correct_promo_selection` for
   credit-side faults. **No new repair machinery is built speculatively** —
   Phase 2 sizes to Phase 1's findings, and may legitimately be empty.

Repair invariant (from the 0t-A review, kept): repairs move `cycle_id`
ONLY; per-bet `bet_net_pnl` and the store total are snapshot-asserted
byte-identical before/after on a DB copy.

## 4. THE ONGOING INVARIANT — a section in the daily money check

`ops/settlement_review.py` gains one section, **CYCLE ACCOUNTING**, fed by
the same shared classifier (read-only, whole store, no window — the
acceptance number must be windowless or drift older than a window hides):

    CYCLE ACCOUNTING
      All 339 cycles accurately tracked (100.0%).      ← the daily number
      OPEN CYCLES (3):
        9274169d — opened 30 Jul, 3 bets — FB $10 in hand (Tim@TAB)
        …
      ⚑ <any new defect, one line, naming its fix control>

- **Flags inform, never block** (standing friction rule): no placement,
  settle, or credit path ever consults cycle coherence to refuse. The two
  hard interlocks that already exist (the assign-cycle control's one-lay
  fence; the linker's L3 fence) are unchanged — they are write-side contract
  checks, not this invariant.
- Defect lines follow the CYCLE PAIRING WATCH pattern: capped at 5 with an
  "…and N older" count; any **real-money shape** (C5/C7) prints uncapped,
  per the 0t-A F1 lesson.
- The existing CYCLE PAIRING WATCH (30-day worklist window) and the
  FB-missing-lay 30-minute grace flag **remain** — they are the operator's
  timely worklist; the new section is the completeness guarantee behind
  them. The audit-vs-worklist split mirrors `UNPAIRED_LAY_LOOKBACK_DAYS`
  vs `CANDIDATE_LOOKBACK_SECONDS`: windows for attention, no windows for
  truth.
- OPEN CYCLES is the worklist's missing "which cycles are still in flight"
  list, derived per §1.3, each line saying what is outstanding (pending
  member / FB in hand).

## 5. THE VIEW — where cycles-as-a-set lives (operator's call)

| Option | For | Against |
|---|---|---|
| **(a) BetLog "group by cycle" toggle — RECOMMENDED** | The operator already lives in BetLog (date presets, filters, per-row CycleChain exists); one switch turns the feed into cycle cards; smallest new surface | The feed query needs a cycle-expansion step |
| (b) Own "Cycles" tab | A standing in-flight board | A second place to look for the same rows; most of its value is already delivered by the daily check's OPEN CYCLES list |
| (c) Burst Review section | Right for REPAIR worklists (pairing lane already there — and it stays) | Wrong for browsing history: Burst Review is a review queue, not a ledger |

**Recommendation: (a)**, plus the §4 OPEN CYCLES list in the daily check;
(c) keeps only its repair lanes; (b) only if (a) proves insufficient in use.

Behaviour of (a), whichever home is chosen:
- **Window rule:** a cycle appears when ANY member (or attributed credit)
  falls in the filtered window, and it renders **WHOLE** — out-of-window
  members shown with their own dates, visually distinguished. This kills
  the "insurance days look artificially negative" attribution problem
  (pl_audit area 5): the qualifier's day shows the finished play, not a
  bare −$50.
- Each card: origin class · state chip (**Open** / **Closed <date>** /
  **Closed — bonus expired unused**) · members via the existing CycleChain
  renderer · **all-in net** (§1.5). The period strip is UNCHANGED (the 2 Aug
  one-figure decision already landed there); the cycle view adds the
  cycle-complete reading, it does not add a third headline.

## 6. Remaining P&L-review scope — (a)(b)(c)(e)(f)(g)

(d) is **RESOLVED** by the 2 Aug operator decision + the shipped
`pnl_all_in` strip; its only residue is the cycle-level promo-cash term,
folded into §1.5/Phase 4. Item by item against the S260 audit, re-verified
in current code today:

- **(a) `bet_net_pnl`** — SOUND (0/332 mismatches). Remaining: **D1** —
  the conversion input still exists (`LogPastBet.tsx:104/257/602`,
  placeholder 0.65) and still multiplies realised FB winnings via
  `_bet_cash_return`. Fix: remove the form field AND fence the multiplier
  out of realised P&L; red test asserts a won FB with a conversion rate set
  still reports full winnings; assert-no-live-rows-change (all 61+ FB rows
  have both columns NULL). `realised_conversion_rate` stays a dormant
  documented column (no write path exists).
- **(b) commission** — SOUND (4 days to the cent). Remaining: **D2** —
  single-bet echoes still compute share-less nets (verified today:
  `bets.py:1358` feed-item without shares; `:3672` `pnl_now`); thread the
  existing `_lay_commission_shares` through the ~7 echo sites + corrections
  `pnl_now` + reassign `pnl_delta`. **D10** — market netting still excludes
  Betfair BACK bets (`_is_settled_cash_lay`); latent (0 such rows), fix
  with a synthetic-market red test. Rounding *mode* stays covered by the
  watchdog funds identity (nothing to build).
- **(c) free-bet treatment** — SOUND on all three arms; nothing remaining
  beyond D1. The locked rule is preserved in every new figure this plan
  adds (§1.5).
- **(e) Balances self-check** — keep the check (it genuinely catches filter
  lockstep + state-vocabulary drift), **relabel** to claim only what it
  proves ("Both money reads agree — this checks the tool against itself,
  not against your accounts"). **D3** — `book_correction` ledger
  adjustments are excluded from the headline P&L along with
  `day_0_opening` (one event type, two meanings; −$0.01 today, unbounded
  in principle): split by reason and include `book_correction` — operator
  decision §9.4 because it changes the headline.
- **(f) cycle netting** — arithmetic SOUND (0/12); membership is Phases
  1–3; the missing promo-cash term lands in Phase 4 on **both** surfaces
  (`CycleChain` and the money check's cycle nets) via the shared
  derivation, in lockstep by construction.
- **(g) the S231 haircut rules — the decision, presented cleanly
  (operator's call, §9.3):**
  - *What exists:* FB conversion 65% is already in code, in the right
    place (`evEngine.ts DEFAULT_FB_CONVERSION_RATE`, forward EV only).
    The **$6–$10 band ~3pt haircut** and the **flagged-EV-never-firm**
    rule exist only in governance.
  - *Option CODIFY (recommended):* band-conditional correction in
    `evEngine.ts` at the same point the 65% applies (all screens read
    through `racePortfolio.prepareBet`, so one copy propagates), carried
    into `promo_ev_at_log` so haircut-vs-realised can be reviewed later;
    flagged-EV firmness implemented as presentation only (non-firm band,
    no point value, warn-never-block). Effort S. Benefit: the rule the
    operator bets by is the rule the screen shows; today $6–$10 screen
    EVs read ~3pts optimistic against S231's own validation.
  - *Option GOVERNANCE-ONLY:* zero code; the operator keeps applying it
    by eye; the known optimism stays on screen and in `promo_ev_at_log`.
  - *Either way:* **never in realised P&L** — `bet_net_pnl`, cycle nets,
    and Balances report money that moved, full stop (the audit's area-8
    wall stands).
- **Also on the fix list (from the same audit):** **D4** FB inventory
  ignores credit `status` (add the status filter to
  `compute_free_bet_inventory` — lockstep with the cash side); **D5**
  "MANUAL CREDITS TODAY" ignores status/supersession (verified still true
  in `settlement_review._manual_credits_for` — add both filters, mark
  superseded rows instead of listing them bare); **D7** unify "money at
  risk" on the liability-aware derivation (BetLog `pending_stake` is
  requested-stake-based and lay-blind; a single pending lay would split
  the two figures $456 vs $38).

## 7. Red-before test plan

Every phase lands red-first; the live store (a read-only copy) is itself a
fixture.

1. **Classifier/audit (Phase 1):** fixture stores seeded with exactly one
   defect each — C1 stranded lay, C2 mis-inherited FB, C3 double live lay,
   C4 double cash back, C5 unfunded FB, C7 dangling cash credit — each
   must produce exactly its class line and drop the percentage; a golden
   fixture (qualifier+FB+lay, a goodwill LF cycle, a void-and-replace
   two-lay cycle, a legless sports bet) must read 100.0% — the
   void-and-replace and goodwill shapes are the regression traps that
   would false-flag first. **Live replay:** against a pre-repair copy the
   command must report exactly C1×32 C2×2 (the audit's census, adjusted
   for post-audit bets); against a post-repair copy, 100.0%.
2. **Repair residue (Phase 2, if any):** per the 0t-A pattern — dry-run
   prints moves and writes nothing (assert store hash unchanged); apply
   moves `cycle_id` only; per-bet P&L + store total byte-identical;
   every `bet_edited` has before == after.
3. **Invariant (Phase 3):** golden store → the 100% line and no ⚑; each
   seeded defect → one line naming its fix; cap behaviour (6 defects → 5
   lines + "…and 1 older"); C5/C7 never capped; the section renders on a
   store missing promo tables (older-store guard, like every existing
   sweep).
4. **State + all-in net (Phase 4):** pending member → OPEN; live credit in
   hand → OPEN; consumed→deployed→settled → CLOSED at proxy date; expired
   unused → CLOSED at expiry `occurred_at` with the marker (fixture =
   the Sarie-Ladbrokes shape); late credit on a closed cycle → derivation
   reads OPEN again with no write. All-in net: cycle holding a Bet365-style
   banked credit includes it to the cent; rejected/superseded credits
   excluded; FB face value asserted absent; commission shares match the
   `settlement_review` derivation on a mixed win/loss market.
5. **View (Phase 5):** vitest — toggle groups the feed; a 2-date cycle
   filtered to day 1 renders whole with day-2 members distinguished; state
   chips render all three readings; `npm run build` (tsc) is the gate,
   vitest does not typecheck.
6. **P&L fixes (Phase 6):** D1 — a won FB with conversion=0.65 set reports
   full winnings (fails today); D2 — corrections `pnl_now` equals the
   BetLog net for a won lay on a commission-rebate market (differs by
   $3.26 today); D4 — a provisional FB credit is not counted available
   (fails today); D5 — a superseded manual credit is marked (fails
   today); D7 — a pending lay shows liability in both figures (fails
   today); D10 — a winning Betfair BACK on a market with a losing lay
   nets commission correctly (fails today). D3/(g) only if their
   decisions are GO.
7. **Acceptance (Phase 7):** the reconciliation run — `ops.cycle_audit`
   on the live store prints 100.0% / 100.0%; the daily check carries the
   same number; both recorded in the 0t-B close-out report with the
   violation count at zero. This is the operator's number.

## 8. Phased build sequence + effort

Assumes the 34-row repair (separate stream) has landed. Adversarial review
at implementation is already directed; each phase is independently
shippable and read-only until Phase 5 (the only user-facing surface
change) — the money-write surface is never touched.

| Phase | What ships | Effort |
|---|---|---|
| **1** | Shared classifier module + `ops/cycle_audit.py` printing the acceptance number; live pre/post-repair replay recorded. **Plus D1** (one-field removal + fence — the only latent money-misstatement, cheapest first) | ~1 session (M) |
| **2** | Repair of Phase-1 residue via sanctioned paths — sized to findings, possibly **nil** | ≤0.25 session (S) |
| **3** | CYCLE ACCOUNTING section in the daily money check: the number, OPEN CYCLES, defect flags (never block) | ~0.5 session (S–M) |
| **4** | Derived state + close-date proxy + all-in cycle net in the shared module; wired into `CycleChain` and the money check's cycle nets | ~0.75 session (M) |
| **5** | The view per the operator's §9.2 choice (recommended: BetLog group-by-cycle toggle, whole-cycle window rule, state chips) | ~1 session (M, frontend + `npm run build`) |
| **6** | Remaining P&L fixes: D2, D4, D5, D7, D10, self-check relabel; D3 and (g) if their decisions are GO | ~0.75 session (M, many small) |
| **7** | Acceptance reconciliation run + close-out report (`pl_audit` fix-list closure + the number) | ~0.25 session (S) |

Total ≈ 4–4.5 sessions. Order rationale: 1→2→3 reach the number and pin it
(the operator's bar) before anything is rendered; 4→5 build meaning and
view on membership that is already trusted; 6 rides behind because every
item is latent or display-only at today's data (audit-verified); 7 is the
bar itself. If a race day intervenes, the boundary after any phase is a
safe stop.

## 9. OPERATOR DECISIONS (only genuinely yours)

1. **When does a play with an unused bonus count as finished?** A bonus
   that expires or is revoked before being used: close the play on that
   event's date at the money that actually moved, marked "bonus expired
   unused" (recommended — Option A, §1.3); or hold the play open until
   you dismiss it by hand (Option B). A late surprise credit reopens the
   play automatically under either option.
2. **Where the cycle view lives:** BetLog "group by play" switch
   (recommended), its own tab, or a Burst Review section (§5). The daily
   check's in-flight list arrives regardless.
3. **The S231 haircut rules:** put the $6–$10 ~3pt haircut into the EV
   screens so the number you see is the number you bet by (recommended),
   or leave it as a rule you apply by eye (§6g). Either way it never
   touches recorded profit.
4. **Book corrections in the headline P&L:** watchdog cent-truings are
   real money the exchange moved; include them in the Balances headline
   (recommended; today the difference is one cent) or keep excluding
   them (§6e, D3).
5. **Exact finish dates (minor, default = proxy):** the tool has no
   stored settle timestamp; plays will be dated by their last action
   (right for racing, which settles same-day). Say the word only if you
   want statement-grade dating some day — it is a bigger, separate build
   and nothing here depends on it.

Decisions 1–2 gate Phase 4–5 detail only; **Phase 1 can start on review
sign-off with none of them answered.**

---
*Plan produced read-only: one file written (this one); no code, no data, no
config touched. DB reads were short `mode=ro`/`-readonly` queries against
the closed app's store.*

## Adversarial planning review (S263) — SAFE WITH FIXES; amendments NORMATIVE

Core verified sound (FB membership genuinely re-derivable from deploy
payloads; the pre-repair replay is a real falsifiability anchor;
flags never block; the decision list is clean; Phase-3 cost trivial;
"135-line noise" fear refuted — 0 open cycles under §1.3 today).
1. F1 HIGH — lay correctness must RE-DERIVE via the forward-linker
   rule (anchor lay placed_at, ≤30s, order-consistent bijection);
   same-market/selection membership alone cannot fail on a
   cross-paired Sir Myka. Ambiguous cases print "coherent —
   operator-confirmed", never silently pass.
2. F2 HIGH — the four 2-Aug replacement credits carry occurred_at =
   correction time (they PREDATE the occurred_at fix — known one-off,
   recorded S263), so the strip books $114.88 to 2 Aug while cycle
   close-dates would book it to 1 Aug: correct §0's delta table; NEW
   OPERATOR DECISION — gated 4-row re-true of those dates vs accept
   the one-day boundary quirk; and specify whether attributed credit
   occurred_at joins the §1.4 close-date max.
3. F3 MED — the closed-cycle exemplar is wrong-class (the Sarie $10 is
   goodwill, never deployed, roots NO cycle): restate Option A on a
   triggered credit; state goodwill invisibility explicitly and get
   operator sign-off (also the review's sharpest Q3 — does the daily
   check need a goodwill-in-hand/expired line?).
4. F4 MED — total taxonomy: add an UNCLASSIFIED-composition defect
   class counted AGAINST 100%, seeded red.
5. F5 MED — one supersession walk only (state derivation calls the
   inventory walk); pull D4 ahead of Phase 4.
6. F6 LOW-MED — pre-explain 74.2%→90.0% (same defects, different
   denominator convention) in the audit output.
7. F7 LOW — re-derive all counts/anchors at build time (8 not 10
   cross-date cycles; several line cites moved).
8. F8 — TIMING-RESOLVED: the two no-hedge acknowledgements DO exist
   (73d8cc66/fcc6d6ed, recorded 08:06 2 Aug; the review read raced
   the build). Surviving piece: the close-out cross-lists settled
   unhedged FBs against the ack table.
9. F9 LOW — one footer line reconciling cycle cards vs the window
   strip on the toggle view.
Builder's three pre-Phase-1 questions recorded in the review (ambiguous
-pairing accounting; replacement-credit dates; goodwill visibility).
