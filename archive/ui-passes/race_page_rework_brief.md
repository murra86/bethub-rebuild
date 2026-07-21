# Race-page rework — Code build brief

**Drafted:** 2026-07-08 20:03 ACST, Session 235 (headless runner, first action
auto-executed per S234 close).
**Status:** LOCKED — operator sign-off given at the S235 walkthrough
("Let's do it", 2026-07-09). Read together with **Addendum B** below, which
carries the walkthrough amendments and prevails over §5 where they differ.
**Substrate:** `sessions/SESSION_234.md` §12(b) + Findings + Open items; day-2
record in `b6_proving_window_log.md`. All "as built today" claims grounded
read-only against bethub-v3 at `9de0609` this session (S178 rule); this brief
sweeps the whole logging/promo surface once (S223 one-pass rule) rather than
fixing serially.
**Governing DRs:** DR-019 (money derives on read), DR-021 (Adelaide anchors),
DR-022 (account / book / account-at-book vocabulary), DR-027/028 (two-database
boundary — no new cross-database surface in this brief).

---

## 1. What this brief is and is not

A single bounded Claude Code build session against bethub-v3
(`/Users/tim/Desktop/Projects/bethub-v3`, start from `main` = `9de0609` or
its current descendant — verify clean tree first). It reworks the race-page
logging/promo UX and closes the S234 conversion-day friction list in one
pass. It is a UI + read-path + logging-plumbing build.

It is **not** a money-path build. Placement, reconciliation, settlement, and
credit-engine maths are OUT of the edit surface — §9 fences them by file.
It is **not** the cycle-demotion build — that is a separate held design
(`cycle_demotion_design_note.md`); no cycle machinery is added, removed, or
changed here. Surprises become findings in the report, not chased fixes.
If the work does not fit one session, that is a finding, not a continuation.

## 2. Why this work exists

Proving-window day 2 (S234) ran the money path cleanly — five automatic
worker settlements, all correct to the cent — but the day still needed
supervised corrections, every one traceable to promo/logging UX: a wrong
promo variant picked off dense near-identical buttons, a silent Log Past
Bet save that produced a duplicate, lays invisible after placement, and
safety-net tags the logging flow never sets even though the credit gate
requires them. Tick 1 of gate 9 (one clean self-serve day) is the only
cutover evidence still open, and this friction is what is blocking it. The
operator locked the redesign direction at the S234 close; this brief is
that direction as a buildable contract.

## 3. Pre-reads (required, in order)

1. This brief, end to end, before any edit.
2. `/Users/tim/Desktop/Projects/bethub-rebuild/sessions/SESSION_234.md`
   — §12(b) + Findings (the operational substrate).
3. `/Users/tim/Desktop/Projects/bethub-rebuild/cycle_demotion_design_note.md`
   — context only: explains why NO cycle wiring is wanted in this build.

Reference-only (consult as needed, not required reads):
`/Users/tim/Desktop/Projects/bethub-rebuild/b6_proving_window_log.md` (day-2
record). Code confirms understanding of §1, §5 and §9 in one short message
before the first edit (read-and-confirm gate).

## 4. System access and baseline

- **Read-write:** the bethub-v3 repo only
  (`/Users/tim/Desktop/Projects/bethub-v3`). Frontend
  `ui/web/src/...`, API routers `ui/api/routers/...`, and store
  repositories **read functions only** as permitted in §5. §9 lists the
  no-edit files.
- **Read-only / no-touch:** the operator's live store (`~/.bethub/...`) —
  all testing against test fixtures/scratch DBs; **no Betfair contact of
  any kind; both workers stay OFF; no live app launch against the live
  store.** A dev launch against a scratch store for UI verification is
  fine.
- **Baseline (verify before editing):** clean tree; suites green —
  backend `uv run pytest -q` (baseline 1399 passed at `9de0609`), frontend
  `cd ui/web && npx vitest run` (baseline 134 passed). Record actual
  baseline counts in the report. The repo is a `uv` project — never bare
  `python3`.
- **Git:** standing autonomy (S227 amendment) applies — commit(s) with
  descriptive messages + Claude co-author trailer, push to `origin main`,
  **green tree only**. Never commit a DB or secrets.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 throughout the
  report.

## 5. Substantive scope — the one-pass sweep

Nine numbered items. Each gives the grounded "as built today" (with
anchors at `9de0609`) and the required behaviour. Component-level
implementation shape is Code's call unless a behaviour is named as
required.

### 5.1 Top-bar log flow (account → account-at-book → promo rail → runner-click + confirm)

**As built today:** `ui/web/src/routes/Racing.tsx:73` renders
`PromoBar` above the odds table and `LogBetPanel` in a side/log column.
The promo bar (`ui/web/src/components/PromoBar.tsx:37`) builds one button
per catalogue row labelled only `item.name` (`PromoBar.tsx:90`), in array
order, no recency; clicking attaches `promo_template_id` + EV config but
prefills no stake (the cap feeds only EV maths, `Racing.tsx:174`). The log
panel (`ui/web/src/components/LogBetPanel.tsx:73`) collects account, book,
odds, stake, free-bet selection, and POSTs to `/api/v1/racing/bets`
(`LogBetPanel.tsx:262-286`) — it **never sends `strategy_tag`** even
though the payload type accepts it (`ui/web/src/api/racing.ts:231`) and
the server forwards it verbatim (`ui/api/routers/racing.py:930`, request
model `:500`). Selection comes from a runner-row LOG click
(`OddsTable.tsx:378-385`).

**Required behaviour:**
1. The logging flow moves to a top bar with this order: **account →
   account-at-book → promo rail**. Account and account-at-book selections
   persist across races (they already do — keep that).
2. **Promo rail, recency-informed:** promo buttons for the selected
   account-at-book's book, ordered by most-recently-used at that book
   first (derive recency from existing bet reads — e.g. the bet feed's
   `promo_template_id` per account-at-book; a small additive read-only
   API/store query is permitted). Unused promos follow in catalogue order.
3. **Shape-first picking:** button labels lead with the promo SHAPE —
   refund positions × return type (e.g. "2nd → Bonus", "2nd/3rd → Cash") —
   with the template name secondary. The S234 wrong-variant incident came
   from near-identical name-first labels; shape is what must be right at
   logging (day-2 finding: with stake ≤ cap the credit maths is
   cap-independent). The **cap is typed off the slip**: show the catalogue
   cap as the editable default, operator confirms/overrides from what the
   betslip actually says.
4. **Stake prefilled from the promo** (its cap/max-stake), editable.
5. **`safety_net` auto-set at logging:** when the attached promo is
   insurance-shaped (insured positions present), the log payload carries
   `strategy_tag: "safety_net"` automatically. This closes the S234
   credit-gate/logging-flow disagreement (the credit-in gate at
   `ui/api/routers/promos.py:216-230` requires the tag; the flow never set
   it). The tag must be visible on the confirm step. The gate itself is
   NOT edited.
6. **Runner-click + confirm:** with account/aab/promo armed, clicking a
   runner opens a compact confirm (runner, odds, stake, promo shape,
   account-at-book) — one action to log. **Saturday anchor: 18 identical
   promo bets across a day must reduce to one rail tap + 18 runner-click +
   confirm actions.** Free-bet logging (inventory selection) stays
   available in the same flow.
7. A clear success confirmation on every log (bet registered, visible in
   the activity board per §5.2).

### 5.2 Race activity board (bottom panel)

**As built today:** nothing shows bets on the selected race — no component
calls the bet feed from the racing route, `LogContextResponse` is
per-account aggregate only (`ui/web/src/api/racing.ts:149-159`), and the
feed filters have no market/race dimension (`ui/web/src/api/bets.ts:98-110`).

**Required behaviour:** the bottom panel (where `LogBetPanel` lived)
becomes an always-visible **race activity board**: every bet on the
selected race — soft-book backs and Betfair lays, all accounts — with
side, account-at-book, stake, odds, promo shape, match state, settlement
state. Needs an additive **read-only** market-scoped bet read; the store
already pairs by `bet_legs.betfair_market_id`
(`store/repositories/bets.py:1009-1029` is the existing pattern —
extending the feed filter or adding a sibling read function is Code's
call; read path only). The board refreshes after every mutation (§5.8)
and carries the **unpaired-lay flag**: a LAY on the market with no BACK on
the same market+selection (or the reverse where a promo/FB context makes
a lay expected) renders with a visible flag. Display-level derivation
only — no stored state, no cycle machinery.

### 5.3 Kill the Betfair account picker

**As built today:** the picker is NOT inside the HedgeModal — it is a
separate `BetfairAccountPicker` gate component (`Racing.tsx:379-484`)
that renders before the modal whenever no `hedgeAccountAtBookId` is set,
listing account-at-books at Betfair-flagged books (`is_betfair` heuristic,
`ui/api/routers/racing.py:811-820`). The lay endpoint takes
`account_at_book_id` for the record write only — credentials come from
the single injected Betfair client (`racing.py:1051-1069`, one client, no
per-account credential lookup).

**Required behaviour:** when exactly ONE Betfair account-at-book exists
(today's sole-account reality), auto-select it and never show the picker —
⚡ goes straight to the HedgeModal. Zero Betfair account-at-books keeps
the existing red "none registered" message. **If a second Betfair
account-at-book ever registers, the picker returns automatically** — the
component is bypassed, not deleted.

### 5.4 Modal hand-off into the same flow

**As built today:** on a placed lay the modal shows a result line and
auto-closes (`HedgeModal.tsx:543-555`, close at `:251-255`); the parent
lifts a frozen matched/unmatched banner and pre-selects the runner in the
log panel (`Racing.tsx:348-363`). **No query invalidation happens at
all** on placement, and the modal sends no link to any originating bet
(`PlaceLayRequest` allows `cycle_id`/`bet_id`; the modal omits both —
correct under the demotion direction: do NOT start sending them).

**Required behaviour:** the placement result drops into the same top-bar
flow and the activity board: on success the modal closes, the board
refreshes and shows the new lay immediately (with its matched/partial
state), and the relevant queries invalidate (§5.8). The frozen banner
retires in favour of board presence. Partial matches keep their current
plain wording. This absorbs the S234 popup decision and the unlogged-lay
concern — an unpaired lay is visible and flagged on the board (§5.2)
rather than tracked by a stored link.

### 5.5 Log Past Bet — save confirmation + FB inventory draw-down

**As built today:** `ui/web/src/routes/LogPastBet.tsx:45` POSTs to
`/api/v1/bets` and on success sets a small text line, resets a few fields,
performs **no query invalidation** — the S234 silent-save duplicate came
from exactly this. The backend manual-create endpoint
(`ui/api/routers/bets.py:1105-1243`) accepts `is_free_bet` but has **no**
`consumed_credit_event_ids` field and never writes a deployment event —
confirmed: a free bet logged here leaves its credit sitting in inventory
(S234 needed a manual script).

**Required behaviour:**
1. **Unmistakable save confirmation** — a persistent success panel naming
   the bet (id, selection, stake, outcome) that survives until the next
   action; the form state makes it impossible to believe the save failed.
   Guard against the double-submit shape (the existing idempotency-key
   pattern on the race-page path is the reference).
2. **FB inventory draw-down:** when `is_free_bet`, the form offers the
   account-at-book's free-bet inventory (same source as the race-page
   panel, `GET /api/v1/racing/log-context`) and sends
   `consumed_credit_event_ids`; the endpoint gains the field and calls the
   **existing** `record_free_bet_deployment`
   (`workflows/promos/v1/fb_deployment.py:82-169`) exactly as the
   race-page path does (`ui/api/routers/racing.py:955-964` is the pattern,
   including its non-fatal warning on failure). **Plumbing a call to the
   existing writer is in scope; editing `fb_deployment.py` internals is
   NOT** (§9).
3. Query invalidation after save and after the optional credit-in
   side-effect (§5.8).

### 5.6 `credit-gaps` dismiss affordance

**As built today:** `GET /v1/promos/credit-gaps`
(`ui/api/routers/promos.py:312-340` → `credit_gap.py:64-131`) lists every
lost safety-net qualifier with no credit; it over-lists by design (it
cannot know finishing positions), has **no dismiss/acknowledge
mechanism**, and has **no UI surface anywhere**.

**Required behaviour:** give the watchdog a visible surface (BetLog or an
equivalent operator-visited spot — Code's call) with a per-item
**dismiss**. Dismissal is durable across restarts and display-layer only:
it must not alter credit-in eligibility (the gate and
`record_free_bet_credit` are untouched), and dismissed items must remain
retrievable (an "include dismissed" toggle or equivalent). Persistence via
the existing `promo_journey_annotation` event type referencing the
qualifier bet is the suggested shape (additive event write, no schema
change); if that proves wrong in practice, choose another **no-new-table**
route and record the call in the report.

### 5.7 BetLog 2dp display rounding (store exact)

**As built today:** `money()`/`signedMoney()` already round
(`ui/web/src/routes/BetLog.tsx:51-62`), but raw floats render at the
inline price `@ {bet.matched_price}` (`BetLog.tsx:433`) and the FB
conversion display (`BetLog.tsx:470-472`) — the S234
`10.000000000000002` artifact.

**Required behaviour:** sweep ALL money/price/rate displays across BetLog,
the racing surfaces, and the new activity board to sensible fixed display
precision (money 2dp; prices/rates to their conventional precision).
**Display only — stored values stay exact; no write-path rounding.**

### 5.8 Stale-page refetch sweep

**As built today (grounded mutation→invalidation matrix):**
- HedgeModal lay placement: **invalidates nothing** (`Racing.tsx:348-363`).
- Log Past Bet create + credit-in: **invalidates nothing**
  (`LogPastBet.tsx:174-208`).
- Race-page log bet: invalidates only `['racing','log-context']`
  (`Racing.tsx:230-232`).
- BetLog edit/delete/settle/credit-in: clean — invalidates `['betlog']`
  (`BetLog.tsx:323-325`).

**Required behaviour:** one pass over EVERY mutation on the logging/promo
surface (including the new flows this brief adds) ensuring each
invalidates all queries whose data it changes — accounts/balances,
log-context, bet feeds, the activity board, FB inventory. Produce the
complete after-state mutation→invalidation matrix in the report. This is
the S223 sweep-the-class discipline applied to the stale-page class that
has now bitten four times.

### 5.9 Plain-language error labels ("API 503")

**As built today:** there is no literal "503" string in the source — the
raw text is assembled by `ApiError` in `ui/web/src/api/client.ts:82-88`
as `` `API ${status} on ${method} ${path}` `` and surfaced verbatim by the
prices banner (`Racing.tsx:262-266`), the HedgeModal error line
(`HedgeModal.tsx:541`), and panel error lines.

**Required behaviour:** map API errors to plain operator language at the
display layer, keeping the technical detail available secondarily. Two
named cases: a prices/feed 5xx reads like "Prices are unavailable — the
app can't reach its data feed right now"; a lay refused by the safety
interlock (the streaming-disconnected 503 seen in the tick-2 drill) reads
like "Placement refused — the live Betfair feed is down, so the safety
interlock blocked this lay." The interlock wording must stay truthful to
the actual refusal reason. Frontend mapping only — no API/status-code
changes.

## 6. Sequencing within session

Suggested order (Code may deviate where operationally cleaner, saying so
in the report): **5.2 activity board read-path first** (other items hang
UI off it) → 5.1 top-bar flow → 5.4 modal hand-off → 5.3 picker bypass →
5.5 Log Past Bet → 5.6 watchdog surface + dismiss → 5.7 rounding sweep →
5.8 invalidation sweep last-but-verified-throughout (each item adds its
own invalidations as it lands; 5.8 is the final audit pass) → 5.9 error
labels. Commit in coherent chunks; every commit green.

## 7. Empirical verification

- **Pre:** record clean tree + suite baselines (backend `uv run pytest -q`,
  frontend `npx vitest run`) before the first edit.
- **Per item:** tests for the new behaviours — at minimum: the safety_net
  auto-tag lands on insurance-shaped promo logs and NOT on others; the
  market-scoped bet read returns exactly the market's bets; the
  Log Past Bet draw-down writes a deployment event superseding the chosen
  credit (assert via `compute_free_bet_inventory` before/after on a
  fixture store); dismiss hides/persists/restores without touching
  credit-in eligibility; rounding is display-only (stored value asserted
  exact); the invalidation matrix items each have a regression guard where
  the test harness supports it.
- **Post:** full suites green; final counts vs baseline in the report.
- **Live-proof honesty (S189 rule):** everything here is
  implemented-not-live until the operator's next racing day exercises it.
  The report classifies each item accordingly and names what the live
  look must confirm.

## 8. Output spec

One report:
`/Users/tim/Desktop/Projects/bethub-rebuild/race_page_rework_report.md`
(absolute path — NOT inside the v3 repo). Sections: per-scope-item
outcome (built / deviated / blocked, with anchors), the §5.8 after-matrix,
design calls made, suite counts pre/post, commits (hashes + messages),
findings & surprises, self-assessment against §9. Anticipated length
250–450 lines; exceed only where load-bearing. The report contains no
recommendations for new scope — routing is the next Chat session's job.

## 9. Hard limits — **MONEY-PATH EDIT SURFACE: NONE**

Non-negotiable. Code must NOT edit any of the following (read for
understanding is fine):

- **Placement:** `clients/betfair_client/` (all of it),
  `workflows/bet_entry/v1/orchestrator.py`, `record_builder.py`,
  `staking.py`, `bet_store_adapter.py`; the lay endpoint's placement logic
  (`ui/api/routers/racing.py` `place_lay` — its guards, order construction
  and Betfair interaction). §5.3's change lives in the frontend picker
  gate, not in placement.
- **Reconciliation:** `workflows/bet_entry/v1/reconciliation.py`,
  `ui/api/reconciliation_worker.py`, and the match-status store writers in
  `store/repositories/bets.py`.
- **Settlement:** `workflows/bet_entry/v1/settlement.py`,
  `ui/api/settlement_worker.py`, `ops/settlement_review.py`,
  `update_settlement_state` and sibling store writers, and the operator
  settle door's fencing (`ui/api/routers/bets.py:862-931`).
- **Credit-engine maths:** `workflows/promos/v1/fb_credit.py`,
  `fb_deployment.py`, `promo_derivations.py`, `credit_gap.py`'s gate
  logic, `promo_store_adapter.py`,
  `workflows/balances/v1/balance_derivation.py`, and the credit-in
  endpoint's gate (`ui/api/routers/promos.py:190-304`).
- **Named permitted exceptions (plumbing, not maths):** (a) the manual
  bet endpoint gaining `consumed_credit_event_ids` and CALLING the
  existing `record_free_bet_deployment` (§5.5); (b) additive read-only
  query functions in store repositories for §5.2/§5.1-recency; (c) an
  additive `promo_journey_annotation` write path for §5.6 dismissals;
  (d) the credit-gaps ENDPOINT may gain an include/exclude-dismissed
  parameter without touching gate logic.

Also out of scope: **any cycle-machinery change** (no cycle_id wiring,
stitching, or removal — the demotion design is held separately); **schema
changes / new tables / migrations**; the streaming stack; the launcher;
v2 anywhere; the VPS; EV engine maths; promo catalogue seed data; every
parking-lot item not named in §5. **No Betfair contact, workers OFF, live
store untouched, no bets of any kind.** If any §5 item cannot be built
without crossing this fence, STOP that item and record it as a finding.
Dist rebuild (`npm run build`) only with the app down, per established
practice.

## 10. What happens after Code's session

The next Chat session triages
`/Users/tim/Desktop/Projects/bethub-rebuild/race_page_rework_report.md`
(inventory-first per Cat 1), surfaces operator-relevant findings in plain
language, and routes: live-proof on the operator's next racing day — which
is also the standing tick-1 attempt, since this build targets exactly the
friction that has kept days 1–2 from being clean. Code does not write the
next brief.

## 11. Cross-references

- `sessions/SESSION_234.md` §12(b) (design lock), Findings, Open items.
- `cycle_demotion_design_note.md` (companion held design — explains the
  no-cycle-wiring stance).
- `b6_proving_window_log.md` day-2 record; `b6_scope.md` gate 9 / tick 1.
- DR-019, DR-021, DR-022, DR-027/028.
- Standing rules exercised: S178 ground-already-built (done in drafting);
  S223 one-pass sweep (§5.8 and this brief's shape); S189
  live-integration honesty (§7); S227 git autonomy (§4).
- Parking-lot items absorbed here: "API 503" label; stale-page refetch;
  watchdog dismiss; BetLog 2dp; Betfair picker removal; Log Past Bet
  confirmation + draw-down; safety_net-at-logging.

---

## Addendum B — S235 walkthrough amendments (operator-agreed, LOCKED)

_Added 2026-07-09 09:41 ACST after the operator walkthrough of both drafts.
These amendments were agreed item-by-item with the operator and prevail
over §5 where they differ. Everything else in the brief stands unchanged,
including all of §9's money fence._

### B1. §5.1 top-bar flow — concrete spec (supersedes §5.1 req 1/4/6)

One bar, left to right: **[person ▾] [book ▾] │ promo rail │ [Free bet]
[No promo]**. Book select shows only that person's account-at-books. The
armed state (person + aab + promo) persists across races until changed;
any element can be re-tapped independently mid-day.

**Two-click logging (operator-confirmed over one-click):** runner-click
opens a compact **confirm card** — runner, odds, stake (pre-filled from
the armed promo's cap, editable), the promo SHAPE, person@book, and the
auto-set `safety_net` tag visibly indicated — with a single **Log**
action. The card is the wrong-variant catch point; no logging path skips
it.

### B2. §5.1 — new-promo card (new requirement)

A **+ new** affordance on the rail opens one small card with exactly two
categories — **refund-if-placed** and **bonus-on-winnings** — plus their
dials (refund positions; return as cash or bonus; cap). Save creates the
catalogue template for the selected book and arms it immediately. No
free-form promo builder. Backend: an additive create endpoint for promo
templates is **in scope** (plumbing — a catalogue INSERT through the
existing template shape; no engine/maths edits). Per the day-1
per-account-variant lesson, the card copy nudges: "as shown on THIS
account's betslip".

### B3. §5.1 — free-bet mode: spend-now-file-later (new requirement)

Free-bet mode on the bar lists the account-at-book's banked bonuses PLUS
one standing option: **"bonus not banked yet"** (operator types the face
value). Selecting it logs the bet as a free bet with **no**
`consumed_credit_event_ids` — representable today with no schema change —
and the bet surfaces as *source-pending* in the burst review (B5). A
mid-burst spend must never block on settlement or banking. Log Past Bet
(§5.5) gains the same option.

### B4. Board + one-tap settle-and-bank (§5.2 refinement + new)

The activity board is **minimal and glanceable**: one compact line per
position (side, person@book, stake@odds, promo shape, state), colour for
state, detail only on tap. Additionally each lost-qualifier line (and its
BetLog equivalent) offers a one-tap **"Lost — placed, bonus landed"**
action that composes the two EXISTING doors in sequence — the settle
endpoint (`POST /v1/bets/{id}/settle`, lost) then credit-in
(`POST /v1/promos/credit-in`) — UI composition only; neither endpoint's
logic is edited. A plain "Lost" (no bonus) and "Won" stay one tap each.

### B5. Burst review — end-of-session reconciliation screen (new item 5.10)

One screen (route or BetLog view — Code's call) showing, for the session:
(a) unsettled soft-book bets with the settle actions; (b) free-bet spends
with no deployment event yet (*source-pending*, from B3); (c) banked-but
-unspent credits; (d) the credit-gaps backstop list with per-item dismiss
(§5.6 folds in here as the backstop, not a flow gate). **Pairing:** a
source-pending spend and an available credit at the same account-at-book
with matching face value pair on one tap — writing the deployment event
through the EXISTING `record_free_bet_deployment` door (§9 exception (a)
extends to this call site); ambiguous cases are listed, never guessed.
Acceptance: a full conversion-day shape (qualifiers, mid-burst FB spends,
late banking) reconciles to zero flags in one pass on a fixture store.

### B6. Placings auto-check — PARKED (retracts part of §5.6's future)

No results-data placing checks in this build (the placings linkage does
not exist on the operational line; day-1 finding). The operator is the
trigger; B4/B5 make banking instant and reconciliation cheap. Revisit
when the placings capture project lands.

### B7. §9 — additional named permitted exceptions (plumbing, not maths)

(e) UI composition of the existing settle + credit-in endpoints (B4);
(f) an additive promo-template create endpoint (B2); (g) the burst-review
read queries (source-pending spends = free-bet bets minus deployment
events — read-side derivation only). The rest of §9 stands verbatim;
`fb_deployment.py`, `fb_credit.py`, settlement and placement internals
remain no-edit.

### B8. Sequencing (replaces §6 order)

5.2 board read-path → B1 top-bar flow + confirm card → B2 new-promo card
→ B3 FB pending-source → 5.4 modal hand-off → 5.3 picker bypass → B4
settle-and-bank → B5 burst review → 5.5 Log Past Bet → 5.7 rounding →
5.8 invalidation audit → 5.9 error labels. Partial-but-coherent remains a
finding, not a failure; if the session budget forces a cut, cut from the
tail, never mid-item.
