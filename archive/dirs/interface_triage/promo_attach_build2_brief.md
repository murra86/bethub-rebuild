# Build 2 — free-bet credit-in + cycle link — Code brief

**Status:** LOCKED — 2026-06-23 (Session 182), operator-approved.
Single bounded Claude Code session. Hard-depends on Build 1 (promo-attach foundation — the bet now
carries `promo_template_id` + `promo_ev_at_log`; the catalogue exposes
each promo's structured terms).

**Repo:** `/Users/tim/Desktop/Projects/bethub-v3` @ `main`
(HEAD `2329604` at brief-draft time; verify live at session start).

---

## §1 — What this brief is and is not

**Is:** a surgical *build* that adds the production write crediting a
free bet (or cash) INTO the system when a settled-lost Safety Net
qualifier with a promo attached is confirmed by the operator to have
finished in the insured spots; plus the once-per-qualifier guard that
keeps the two confirm surfaces from double-crediting; plus the cycle
link so a later-deployed free bet inherits its qualifier's cycle.

**Is not:** a settlement change. The credit write is a promo-event write
in the existing promo-event spine — it reads a settled qualifier off the
bet and never touches `settlement.py`, `apply_manual_operator_resolution`,
or `provisional.py`. It is not the auto-detection of placings (that's the
deferred Piece B, off this critical path). It is not an in-app
catalogue-management UI.

**Single session.** If the work doesn't fit one bounded session, that's a
finding in the report, not a continuation. Surprises become findings, not
mid-session escalations.

---

## §2 — Why this work exists

The S179 review (`promo_attach_credit_in_review_report.md`) split the
promo-on-bet + credit-in work into two builds. Build 1 (promo-attach
foundation) shipped: the single-level catalogue with structured terms,
the promo serial + EV onto the bet, the catalogue-driven pickers. Build 2
is the second half — the credit *write* and the cycle *link* — which the
review found to be greenfield: no production path writes a
`free_bet_credited` event today, and a triggered free bet does not inherit
its qualifier's cycle.

Operationally: when a Safety Net insurance bet loses but the runner
finished in the insured spots (2nd–4th), the book refunds — usually a free
bet, sometimes cash. Today v3 has no way to record that refund landing.
Build 2 lets the operator confirm "yes, it placed" on a settled-lost
qualifier and writes the credit, so the free-bet pool finally fills and
the cycle reads as one unit (qualifier → credit → eventual free-bet
outcome), per the standing single-cycle analysis convention.

The load-bearing design calls were locked at S179 and are not reopened
here: serial lives on the kind-catalogue (`promo_template_id`); the credit
references the promo by that serial (no validator relax — Option B); credit
amount = stake × return % (no cap in the calc; cap is an analytics term);
cash promos are in scope; the EV is persisted (Build 1, done).

## §3 — Pre-reads (lean)

**Required, in order:**

1. This brief.
2. `interface_triage/promo_attach_credit_in_review_report.md` — the S179
   review. Areas 4 (credit write), 5 (confirm surfaces), 3 (read-back
   seam), and the open findings O5/O6/O7 are the spine of this build.
3. `interface_triage/free_bet_credit_in_design.md` — the S168 credit-in
   design (Piece 0 credit-in + Piece A cycle attribution). Read for the
   seam shape; where it conflicts with the S179 locks, the locks win.

**Reference-only (read on need):**

- `interface_triage/promo_attach_build1_brief.md` + its report — what the
  foundation built (the serial + terms now on the bet/catalogue).
- `decisions.md` — DR-032 (amended S180: bet promo link =
  `promo_template_id`), DR-027/028 (two-DB boundary), DR-021 (timestamps).

## §4 — System access

- **Mac filesystem, read-write**, limited to the named anchors in §5.
  Desktop Commander only.
- **Dirty tree is expected.** The working tree carries uncommitted Build 1
  + the free-bet-restore + in-flight `betfair_client` work. Do **not** run
  any git state-changing command (`add`, `commit`, `stash`, `restore`,
  `checkout`, `reset`). Read `git status` at start; edit only named
  anchors; `git diff <file>` after each edit to confirm only intended
  changes; `git status` at close to confirm the dirty-file list is
  unchanged in shape.
- **No DB file copy.** If a DB read is needed for a test fixture, use the
  per-request connection seam the routers already use (the
  `BETHUB_DB_PATH` env-var + `dependency_overrides`), never a file copy.
- **Tests run under `uv run pytest`** (the repo is a `uv` project; bare
  `python3 -m pytest` fails at collection). Frontend: `vitest run` +
  `tsc -b`.
- **Adelaide local timestamps (ACST/ACDT)** for every time reference in
  the report, per DR-021. Credit events stamp `recorded_at`/`occurred_at`
  via the existing `_now_adelaide()` helper.

## §5 — Scope

Six pieces. The core is §5.1 (the write); §5.2–§5.4 wire it to the
operator; §5.5 is the cycle link; §5.6 is tests.

### §5.1 — The credit-in write (`record_free_bet_credit`)

Add a new function in `workflows/promos/v1/` (new module
`fb_credit.py`, or alongside `fb_deployment.py` — Code's call), a
**near-mirror of `record_free_bet_deployment`** (`fb_deployment.py:82`).
It writes one promo event for a triggered credit.

Inputs: the **qualifier bet** (the settled-lost Safety Net bet with a
promo attached) and its attached promo's terms (read from the catalogue
by `promo_template_id`).

The event:

- `event_type = FREE_BET_CREDITED` when the promo's `return_type` is
  `free_bet`; `PROMO_CASH_CREDITED` when `return_type` is `cash`. One
  function, branch on the term. (Cash is in scope per the S179 lock; it
  pulls in the symmetric `PromoCashCreditedPayload`.)
- `credit_source = 'triggered'`.
- `triggering_bet_id` = the **real** qualifier bet UUID (see O5 below).
- `triggering_promo_instance_id` = the bet's `promo_template_id` parsed to
  UUID (Option B — the serial doubles as the reference; **no validator
  change**). The catalogue serials are UUID5 strings, so they parse.
- `amount` = qualifier `stake × return_pct` (no cap applied; cap is a
  stored analytics term only). `Decimal`, > 0.
- `status = CreditStatus.FINALISED` (O7).
- `account_id` / `book_id` / `account_at_book_id` read from the qualifier
  bet — all three are REQUIRED on credit events per the W13 FK matrix
  (`domain/promos` FK matrix ~:592).
- `source = OPERATOR`; timestamps via `_now_adelaide()`.

Written via `PromoStoreAdapter.append_event` — the same sink the deploy
write uses. **No settlement contact.**

**O5 — use the real bet UUID, never a coerced fallback.** The deploy
path's `_coerce_uuid` (`fb_deployment.py:59`) falls back to a *fresh*
`uuid4()` for any bet id that doesn't parse — a silent phantom. The
credit write must NOT reuse that fallback: resolve the qualifier's real
UUID from its `bet_id` (the `bet-<uuid>` form), and if it can't be
parsed, **raise rather than write a phantom-linked credit**. A phantom
`triggering_bet_id` would silently break the §5.5 cycle resolve.

### §5.2 — The shared credit-in endpoint

Add the **first write endpoint** to the existing promos router
(`ui/api/routers/promos.py`, today read-only — `GET /v1/promos/catalogue`).
Add `POST /v1/promos/credit-in`, reusing the router's per-request
connection seam (`get_db_connection` + `BETHUB_DB_PATH` + the
`dependency_overrides` test seam).

Request: the qualifier `bet_id` (and nothing the server can derive
itself — it reads the bet's `promo_template_id`, `strategy_tag`,
`settlement_state`, `stake`, account/book ids server-side). The endpoint
enforces the gate (§5.3), runs the idempotency check (§5.4), and calls
`record_free_bet_credit`. One endpoint, both surfaces call it.

### §5.3 — The two confirm surfaces → one write

Both surfaces ask "did it place in the insured spots?" and, on yes, call
`POST /v1/promos/credit-in`. The **gate** (server-enforced, not just UI):
`strategy_tag = safety_net` ∧ `settlement_state = settled_lost` ∧
`promo_template_id IS NOT NULL`.

- **BetLog** (`ui/web/src/routes/BetLog.tsx:510`): the
  `placed-confirm-scaffold` button is inert today ("Coming soon"). Enable
  it only when the row meets the gate; on click → confirm → credit-in
  call. This is the post-settlement surface (bet logged live, auto-settled
  lost, operator opens the tuck-in later).
- **LogPastBet** (`ui/web/src/routes/LogPastBet.tsx`): when the
  settle-at-entry outcome is `Lost` (`settled_lost`) ∧ strategy is
  `safety_net` ∧ a promo is attached, surface the **same** "placed?"
  question inline at entry and fire the **same** credit-in call.

### §5.4 — Idempotency guard (O6)

The two surfaces must converge on **one** credit per qualifier. Before
writing, check the promo-event log for an existing `FREE_BET_CREDITED` or
`PROMO_CASH_CREDITED` event already stamping this `triggering_bet_id`; if
one exists, return a clean "already credited" response (no second write,
no error-as-failure). Natural key: `triggering_bet_id`. This guard is the
only thing standing between "operator clicks Placed? in BetLog" and
"operator also confirmed it at entry in LogPastBet" both crediting.

### §5.5 — Piece A: cycle inheritance

Today when a free bet is deployed (`ui/api/routers/racing.py`, the
`is_free_bet` + `consumed_credit_event_ids` branch ~:936), the deployed
bet mints a **fresh** cycle (`cycle_id = body.cycle_id or str(uuid4())`,
~:897) and the deploy event's `correlation_id` is that fresh cycle — so
the free bet does NOT join its qualifier's cycle.

Make the deployed free bet **inherit its qualifier's cycle**: resolve the
oldest consumed credit event → its `triggering_bet_id` (stamped by §5.1)
→ that qualifier bet's `cycle_id`, and use that as the deployed bet's
`cycle_id` instead of a fresh uuid4(). §5.1's source-stamp is what makes
this resolvable. If the consumed credit has no resolvable qualifier cycle
(edge case), fall back to today's behaviour (fresh cycle) rather than
failing the deploy.

### §5.6 — Tests

- `record_free_bet_credit`: writes a FREE_BET_CREDITED for a free-bet
  promo and a PROMO_CASH_CREDITED for a cash promo; amount = stake ×
  return_pct; status FINALISED; real `triggering_bet_id`; serial stamped
  as `triggering_promo_instance_id`; raises (not phantom) on an
  unparseable bet id.
- Endpoint + gate: rejects a non-`safety_net` / non-`settled_lost` /
  no-promo bet; accepts the qualifying one.
- Idempotency: a second credit-in for the same qualifier writes nothing
  and reports already-credited.
- Cycle inheritance: a deployed free bet's cycle equals its qualifier's
  cycle.
- **Bet-safety**: `settlement.py` SHA-256 byte-identical start→close.

## §6 — Sequencing within session

1. §5.1 — the write function + O5 (the core; everything depends on it).
2. §5.4 — the idempotency guard (belongs to the write/endpoint).
3. §5.2 — the endpoint (wraps §5.1 + §5.4 + the gate).
4. §5.3 — the two surfaces (call the endpoint).
5. §5.5 — Piece A cycle inheritance (independent of the UI; can slot
   anywhere after §5.1 stamps the trigger).
6. §5.6 — tests throughout, not just at the end.

If a cleaner order surfaces, Code may deviate and say so in the report.

## §7 — Empirical verification (pre and post)

Capture both states so the report shows what moved:

- `settlement.py` SHA-256 — **must be byte-identical** start→close
  (record the hash; current `9e07a75d…40d4a3`). The bet-safety gate.
- Python `uv run pytest -q` count before/after (expect +N from §5.6, 0
  regressions).
- Frontend `vitest run` + `tsc -b` before/after (0 regressions, clean).
- `git status` entry count + HEAD before/after (HEAD unchanged; dirty
  list unchanged in shape; only the named anchors edited/added).
- A round-trip proof: a qualifying settled-lost safety-net bet with a
  promo → credit-in → one credit event with the right amount / type /
  real trigger id / serial; a second call → no write.

## §8 — Output spec

Single file: `interface_triage/promo_attach_build2_report.md`. Sections:
baseline (§0), one per §5 piece built, §7 verification table, findings,
files-touched (complete), self-assessment. ~250–400 lines anticipated;
overshoot only if a finding earns it (flag in self-assessment).

**Does not contain:** recommendations, the next brief, or any scope creep
into Piece B (placings auto-detection), the in-app catalogue UI, or
partial free-bet draw-down.

## §9 — Hard limits (non-negotiable)

- **No settlement contact.** `settlement.py` byte-identical (SHA gate).
  Do not call, branch, or hook `_resolve_settlement_for_bet`
  (`settlement.py:319`) or `apply_manual_operator_resolution`
  (`settlement.py:1128`), and do not touch `ui/api/routers/provisional.py`.
  The credit write reads a *settled* qualifier; it never participates in
  settling one.
- **No fresh-UUID fallback for the trigger id** (O5). The credit's
  `triggering_bet_id` is the real qualifier UUID or the write raises.
- **No validator relax** (Option B). Do not loosen the `triggered`
  cross-field invariant on `FreeBetCreditedPayload` /
  `PromoCashCreditedPayload`.
- **No bets-schema change.** The credit is a promo-*event* write; the
  `promo_events` table already exists. No new column on `bets`.
- **No cap in the credit amount** — stake × return_pct only.
- **No in-app catalogue-management UI**, no partial free-bet draw-down,
  no Piece B placings auto-detection.
- **Dirty-tree git discipline** per §4 — no state-changing git op; edit
  only named anchors.

## §10 — What happens after Code's session

The next operator-Claude session reads
`promo_attach_build2_report.md` and triages: confirm the bet-safety gate
(settlement SHA byte-identical), confirm the round-trip (a qualifying
loss credits once, a repeat doesn't), confirm the deployed free bet
inherits its qualifier's cycle, and surface any findings. Code does not
write the next brief. On a clean triage, the promo-on-bet + credit-in arc
is complete and the sequence moves to the launcher brief → W16 cutover
scoping. Operator live-validation (a real settled-lost qualifier credits
in the launched app) is between-session work.

## §11 — Cross-references

- **Serves:** the S179 review (`promo_attach_credit_in_review_report.md`,
  Areas 3/4/5 + findings O5/O6/O7) and the S168 design
  (`free_bet_credit_in_design.md`, Piece 0 + Piece A).
- **Depends on:** Build 1 (`promo_attach_build1_brief.md` + report) — the
  promo serial + terms on the bet/catalogue.
- **DRs:** DR-032 (promo link = `promo_template_id`, amended S180), DR-021
  (Adelaide timestamps), DR-030 (`ui/` may import `workflows/` + `store/`
  — the endpoint placement). DR-027/028 **not triggered** — single-DB, no
  cross-DB read (placings are off this path).
- **Excludes (parking-lot):** Piece B placings auto-detection; in-app
  catalogue UI; partial free-bet draw-down; the `…_instance_id` field
  rename (semantic-stretch doc question, deferred).

---

*Brief ends. Locked on operator approval; hand to Code as a single
bounded session.*
