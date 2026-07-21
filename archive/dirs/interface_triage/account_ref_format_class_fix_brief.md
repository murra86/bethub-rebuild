# BRIEF — Close the account-reference format class (SURGICAL FIX, READ-WRITE)

**File:** `interface_triage/account_ref_format_class_fix_brief.md`
**Drafted:** S186 · 2026-06-25 ACST · LOCKED on operator
approval.
**Repo under fix:** `/Users/tim/Desktop/Projects/bethub-v3`
@ `main` (HEAD `2329604`, 69 dirty entries — baseline confirmed
S186 open).
**Builds on:** `account_ref_surface_review_report.md` (the locked
surface — every anchor below is drawn from it and re-confirmed
live at S186 open).

---

## §1 — What this brief is and is not

A SURGICAL FIX, executed in a single bounded Claude Code
session, READ-WRITE but limited to the exact anchors named in
§5. It closes the account-reference format-mismatch class that
F2 opened and the review proved complete: retype the three
account refs (`account_id` · `book_id` · `account_at_book_id`)
from `UUID` to `str`-verbatim at every site the review found,
flip the F2-seeded test fixtures to hex, and add the mandatory
per-path FK-on regression guards.

Code applies ONLY the named changes. No drift into adjacent
code "while we're here". Surprises become findings in the
report, not edits and not mid-session pings — with ONE
exception: the §5.0 baseline-drift stop gate (if the repo has
moved since the review, Code stops and reports rather than
fixing against stale line numbers). Code does NOT re-run the
review; the surface is locked. Code does NOT draft any
follow-up brief.

## §2 — Why this work exists

F2 (`account_id_normalization_report.md`) closed the promo
WRITE path — the three refs now store verbatim as operational
hex (`uuid4().hex`, 32-char, dashless) on the promo spine,
FK-safe and proven. But F2 surfaced two open edges, and the
S186-target review (`account_ref_surface_review_report.md`)
proved them complete and bounded: the same three refs are still
typed `UUID` in **exactly three modules**, which re-dashes them
on read/serialise so the account pool and balance DISPLAY still
fail against real hex accounts. In operator terms: when you pick
an account to log a bet against, and when you mark an insurance
bet triggered and expect to see the credited free bet held
against that account, the tool queries the wrong ID shape and
comes back empty. The credit WRITE is already correct (F2); it
is the SEEING it that is broken.

The review's verdict: **minimal-holistic** — retype all in-scope
sites to `str`-verbatim + per-path FK-on regression guards, no
new shared cross-domain type (the shared canonical type stays
parked as post-cutover hardening, a DR-030 call). All three
escalation triggers were NO-HIT (frontend already sends hex →
the fix is backend-only; every column is already `TEXT` → no
schema change; the surface is small/uniform/bounded → no shared
type needed now). This brief executes that fix to close the
class before W16 cutover scoping.

The one structural finding that shapes sequencing: the cash_flow
fix and the balance-read fix are COUPLED through shared
cross-domain tests (F2 seeded them dashed deliberately). They
MUST land together — fixing one without the other re-creates the
mismatch.

## §3 — Pre-reads (in order)

Required (read and confirm understanding before any edit):

- `interface_triage/account_ref_surface_review_report.md` — THE
  anchor. The complete surface map (§A), the per-site treatment
  verdict (§B), the frontend trace (§C), the altitude verdict
  (§D), the coupling finding (§B-note / §D). Every change in §5
  below is drawn from it.
- `interface_triage/account_ref_surface_review_brief.md` — the
  review contract: the boundary discipline (which UUIDs are
  spine-owned and STAY UUID), the in-scope-vs-excluded line.
- `interface_triage/account_id_normalization_report.md` — the F2
  report. The proven retype-to-passthrough pattern this fix
  mirrors mechanically, and the F2-seeded dashed test fixtures
  this fix must flip (F-E in that report).

Reference-only (consult if needed, not required end-to-end):

- `account_id_normalization_brief.md` (the F2 contract).
- Governing DRs: DR-030 (module boundary — why no shared type),
  DR-027/028 (two-database), DR-021 (Adelaide time), settlement
  byte-identity.

## §4 — System access

- Mac filesystem, direct. Repo
  `/Users/tim/Desktop/Projects/bethub-v3` @ `main`
  (HEAD `2329604`).
- READ-WRITE, limited to the named anchors in §5. Every other
  file is read-only.
- Dirty working tree is expected (~69 git entries). Code runs NO
  git state-changing command (no add/commit/stash/restore/
  checkout/reset). At close, the dirty list is unchanged EXCEPT
  for the named-anchor files in §5. Confirm via `git status`
  start and close.
- Tests run under **`uv run pytest`** (the repo is a `uv`
  project; bare `python3 -m pytest` fails at collection — Cat 3).
- `settlement.py` (`workflows/bet_entry/v1/settlement.py`, SHA
  `9e07a75d…40d4a3`) is NOT touched — byte identity, confirmed
  pre and post.
- Adelaide local timestamps (ACST/ACDT) per DR-021 for every
  time reference in the report.

## §5 — Substantive scope (the fix, in dependency order)

The uniform treatment at every defect site is identical to the
proven F2 fix: **retype `UUID` → `str`, drop the `UUID(...)`
read-wrap and the `str(...)` write-wrap, pass the operational-
store TEXT (hex) through verbatim.** No site needs a different
treatment. Spine-owned UUIDs are NOT touched (see §9).

### §5.0 — Baseline confirmation gate (STOP condition)

Before any edit, confirm the repo is where the review left it:

- `git rev-parse HEAD` == `2329604aa80b34937a24644ea2eb18477749be85`
- `git status --porcelain | wc -l` == `69`
- `settlement.py` SHA-256 begins `9e07a75d…`
- spot-confirm three anchors still read as the review states:
  `ui/api/routers/racing.py:714` (`account_at_book_id: UUID`),
  `workflows/balances/v1/balance_derivation.py:147`
  (`(str(account_at_book_id),)`),
  `workflows/cash_flow/v1/cash_flow_store_adapter.py:344`
  (`account_id=str(event.account_id)…`).

If ANY of these has drifted, **STOP** — that is a finding (line
numbers stale), report it, and do not fix against a moved tree.
This is the one sanctioned mid-session stop.

### §5.1 — cash_flow retype (C1) — land WITH §5.2

`domain/cash_flow/__init__.py`
- 409–411: `account_id` / `book_id` / `account_at_book_id`
  `UUID | None` → `str | None` (root type).
- LEAVE as `UUID`: `event_id` (405), `parent_event_id` (412),
  `supersedes_event_id` (413), `correlation_id` (416) —
  spine-owned.

`workflows/cash_flow/v1/cash_flow_store_adapter.py`
- 119, 136, 153: list-query params `UUID` → `str`.
- 195–197: `latest_non_superseded_by_scope` params `UUID` → `str`.
- 312–316: READ — drop `UUID(row.account_id/…)` re-wrap; pass
  the hex TEXT through. LEAVE `event_id`/`parent_event_id`/
  `supersedes_event_id`/`correlation_id` re-wraps as `UUID`.
- 344–348: WRITE — drop `str(event.account_id/…)`; pass the hex
  through. (This is the latent F2-class write bug.) LEAVE the
  `*_event_id` / `correlation_id` `str()` casts.

`store/repositories/cash_flow.py`
- **NO change.** The `str(...)` query sinks (224/241/258,
  336–342) are format-agnostic — they correctly stringify
  whatever they receive, which becomes hex once callers pass
  `str`. Touching them is out of scope.

### §5.2 — balance_derivation retype (C2) — land WITH §5.1

`workflows/balances/v1/balance_derivation.py`
- 112: `AccountAtBookBalance.account_at_book_id` `UUID` → `str`
  (output model → hex JSON).
- 128 + 147: `_read_bet_rows_for_account_at_book(...)` param
  `UUID` → `str`. The existing `str(account_at_book_id)` wrapper
  at 147 becomes a harmless `str(str)` no-op — leave it or drop
  it, Code's call; the substantive change is the param type.
- 392: `compute_account_at_book_balance(account_at_book_id)`
  param `UUID` → `str` (the hub that fans out to cash_flow,
  promo, bets, inventory).
- 496–497 + 510: `_list_account_at_book_ids_for_holder(account_id)`
  param `UUID` → `str`.
- 512: drop `UUID(row[0])` re-wrap — return the hex TEXT
  directly.
- 517: `compute_account_holder_cash_holding(account_id)` param
  `UUID` → `str` (latent — no router yet; retype anyway so the
  class is not re-seeded).
- 481 / 580 / 589: `AccountHolderCashHolding.account_holder_id`,
  `BookNetFlow.book_id`, `AccountNetFlow.account_id` output
  models `UUID` → `str` (latent outputs → hex JSON).
- 656 / 667–680 / 685–692: `by_account: dict[UUID, …]` keyed by
  `event.account_id`, and the `AccountNetFlow(account_id=…)`
  construction → `str` keys/values (latent net-flow).
- Boundary: 535 (`cf_adapter.list_by_account`) and 431
  (`promo_adapter.list_by_account_at_book`) are SINKS fixed by
  the param retypes above — no separate change.

### §5.3 — racing `/log-context` retype (C3) — rides on §5.2

`ui/api/routers/racing.py`
- 714: `get_log_context(account_at_book_id: UUID)` query param
  `UUID` → `str`. **This alone makes the pool display** — the
  frontend already sends hex verbatim (review §C); no `Query`
  validation change needed beyond the type.
- 399: `LogContextResponse.account_at_book_id` `UUID` → `str`
  (response consistency — hex, not dashed).
- LEAVE as `UUID` (spine-owned / bet-id): `credit_event_id`
  (381), `source_promo_instance_id` / `source_template_id`
  (386–387), `consumed_credit_event_ids` (492), idempotency
  `uuid5` / `UUID(candidate)` (884/833). LEAVE
  `LogBetRequest.account_at_book_id` (484 → 918) — already `str`,
  correct.

### §5.4 — Test-seed migration (the coupling consequence)

F2 deliberately seeded the cross-domain balance tests as dashed
`str` BECAUSE cash_flow was still `UUID` (F2 report F-E). The
moment §5.1 retypes cash_flow to hex-`str`-verbatim, those seeds
must flip to **hex** or the shared tests re-create the mismatch.

- `test_balance_derivation.py`, `test_balance_lay_branch.py`
  (and any other cross-domain balance/cash_flow test carrying a
  dashed account-ref seed): flip the seeded `account_id` /
  `book_id` / `account_at_book_id` fixtures from dashed to hex
  (`uuid4().hex`).
- This is part of THIS change, in the SAME session — not a
  follow-up. It is the mechanical reason C1 and C2 are coupled.
- Find them empirically (grep the test tree for dashed-UUID
  account-ref seeds) rather than trusting this list to be
  exhaustive; the review named two, there may be more.

### §5.5 — Per-path FK-ON regression guards (MANDATORY)

The real anti-recurrence lever (review §D) — not optional. Each
guard runs with SQLite `foreign_keys = ON` against a REAL hex
account, pinning the format at the live boundary:

- **(a) cash_flow write guard** — a cash_flow write under
  `foreign_keys = ON` against a hex `accounts_at_book` PK
  succeeds (proves the latent write bug stays dead — the bug
  was `str(UUID)` dashed vs hex PK with the FK constraint
  present).
- **(b) racing `/log-context` guard** — `/log-context` returns
  a NON-EMPTY pool for a hex account-at-book (proves F-A stays
  fixed end-to-end — the operator's "log against this account"
  path).
- **(c) conversion-scenario guard** — the operator's §4 hinge:
  with a free-bet credit recorded against a hex account-at-book,
  `compute_account_at_book_balance` returns that credited free
  bet (proves the "see the credited free bet held against the
  account" path the fix exists to restore).

Place guards beside the existing balance/cash_flow/racing test
modules; name them clearly as format-class regression guards.

## §6 — Sequencing within session

1. **§5.0 baseline gate** — confirm HEAD / dirty count /
   settlement SHA / three anchors. STOP if drifted.
2. **§5.1 cash_flow + §5.2 balance_derivation TOGETHER** — the
   coupled change. Retype both before running any cross-domain
   test.
3. **§5.4 test-seed migration** — flip the dashed seeds to hex
   in the same breath (the tests bind C1 and C2).
4. **§5.3 racing `/log-context`** — rides on C2; retype after.
5. **§5.5 guards** — add the three FK-on regression guards.
6. **Full suite** — `uv run pytest`. The ~10 known F-A
   read-path-caller failures (the ones the review brief named as
   the F-A surfacing, NOT a regression) must now PASS, the three
   new guards pass, and nothing else regresses.

A cleaner order Code discovers is fine; the load-bearing
constraint is only that C1+C2+the seed-flip move as one unit
before tests run, and the baseline gate comes first.

## §7 — Empirical verification (pre-and-post)

Capture BOTH states in the report so it shows what moved:

- **Pre:** `uv run pytest` on the balance / cash_flow / racing
  test modules, showing the ~10 F-A failures red; plus a query
  or test showing `/log-context` returns EMPTY for a real hex
  account-at-book.
- **Post:** the same battery green; `/log-context` returns a
  NON-EMPTY pool for the hex account; the three §5.5 guards
  pass; full `uv run pytest` shows no new failures.
- **settlement.py** SHA-256 byte-identical pre and post
  (`9e07a75d…40d4a3`).
- **`git status`** dirty list unchanged except the named-anchor
  files (the `domain/cash_flow`, `cash_flow_store_adapter`,
  `balance_derivation`, `racing.py`, and the touched test
  modules).

## §8 — Output spec

Single file:
`/Users/tim/Desktop/Projects/bethub-rebuild/interface_triage/account_ref_format_class_fix_report.md`

Sections:
- **Baseline** — HEAD, dirty count, settlement SHA (pre/post),
  the §5.0 gate result.
- **§A — Changes applied** — per site, file:line, the operation,
  before → after form (UUID → str). Grouped C1 / C2 / C3.
- **§B — Test-seed migration** — which test fixtures flipped
  dashed → hex; how Code found them (the grep), final list.
- **§C — Regression guards** — the three guards added, file:line,
  and pass results.
- **§D — Pre/post verification** — the failing→passing battery,
  the `/log-context` empty→non-empty result, full-suite result.
- **§E — What was NOT touched** — spine-owned UUIDs, settlement
  byte-identity, schema (no DDL), the cash_flow repo `str()`
  sinks.
- **Self-assessment** — coverage, any anchor that drifted,
  confidence, anything not provable in one session.

Anticipated ~200–350 lines. The report contains NO scope creep
into other fixes, NO next-brief draft, NO schema change, NO
"ship it" beyond the verified-green state.

## §9 — Hard limits (non-negotiable)

- READ-WRITE only at the §5 anchors. No drift into adjacent
  code, no opportunistic refactor.
- `settlement.py` byte-identical (SHA `9e07a75d…40d4a3`). No
  contact with `settlement.py`, `apply_manual_operator_resolution`,
  or the `provisional.py` settlement path.
- **Spine-owned UUIDs STAY UUID — do not retype:** `event_id`,
  `parent_event_id`, `supersedes_event_id`, `correlation_id`,
  `promo_id`, `promo_template_id`, `credit_event_id`,
  `source_promo_instance_id`, `source_template_id`,
  `consumed_credit_event_ids`, idempotency `uuid5`/`UUID(...)`.
  Misclassifying one of these as in-scope is the failure mode.
- **NO schema change** — every PK/FK column is already `TEXT`;
  the fix stores hex verbatim with zero DDL.
- **NO git state-changing ops** (add/commit/stash/restore/
  checkout/reset). Dirty list unchanged except the named-anchor
  files.
- **Do NOT re-litigate** the promo spine (F2 — correct/proven)
  or the operational store (correct). The ~10 F-A read-path test
  failures are the known surfacing, NOT broken promo work.
- **`store/repositories/cash_flow.py` — NO change** (the `str()`
  sinks are already correct).
- Single bounded session. Over-budget = a finding, not a
  continuation.
- No mid-session escalation EXCEPT the §5.0 baseline-drift STOP.
  Everything else surfaces in the report.
- `uv run pytest`, never bare `python3` (Cat 3).

## §10 — What happens after Code's session

The next operator-Claude session reads
`account_ref_format_class_fix_report.md`, confirms the class is
closed — the failing→passing battery green, the three FK-on
guards in place, settlement byte-identical, dirty list clean
except named anchors — and routes forward to the **pre-cutover
live-validation sweep** and **W16 cutover scoping**. The shared
canonical account-ref type stays parked (post-cutover hardening,
a DR-030 call). Code does NOT draft the next brief.

## §11 — Cross-references

- Surface: `account_ref_surface_review_report.md` +
  `account_ref_surface_review_brief.md` (interface_triage).
- F2: `account_id_normalization_report.md` + `_brief.md` (the
  proven retype pattern + the seeded test fixtures).
- DRs: DR-030 (module boundary — why the shared type is parked),
  DR-027/028 (two-database), DR-021 (Adelaide time), settlement
  byte-identity.
- Arc: W16 cutover — this closes the last credit-in display edge
  before cutover scoping.
- Parking: shared canonical account-ref type (post-cutover
  hardening, the review's "full-holistic" option, not pulled
  forward).
- Operational throughline (`operator_workflow_map.md`): the live
  half of this fix restores the §3 Log Bet account-context pull,
  the §4 conversion hinge ("mark triggered → see the credited
  free bet held against the account"), and the §5 end-of-day
  "use all the free bets so none sit dormant" pass. The fix does
  NOT touch the EV column, the odds-mirroring path, or
  settlement — the operator's highest risk surface (map signals
  3 & 4) is separate work.

---
*End of brief. LOCKED S186 2026-06-25 ACST.*
