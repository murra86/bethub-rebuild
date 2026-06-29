# Session 164

**Title:** customerRef fix executed, triaged clean, and PROVEN
LIVE — three real lays placed against live Betfair, no 503; the
S149 placement blocker is cleared. Last operator-validation gate
before the W16 v2→v3 cutover decision is done. Next gate before
cutover: an operator-led interface run-through to classify noted
deficiencies as pre- vs post-cutover.
**Opened:** 2026-06-18 19:27 ACST
**Closed:** 2026-06-18 20:38 ACST
**Tool routing:** Claude Chat (read-and-confirm triage of Code's
brief read-back; triage of Code's fix report; live-log triage;
session governance). One Claude Code commission executed
out-of-session this session (the locked fix brief v2).
**Governing DRs:** DR-032 (Betfair canonical reference layer +
auto-login — the placement path), DR-029 §2.4 (Betfair
Streaming), DR-030 (v3 module boundaries — import linter),
DR-021 (timestamp anchoring), DR-013 (DB read discipline).

---

## Anchor

- Open: `TZ=Australia/Adelaide date` → 2026-06-18 19:27 ACST.
- Close: `TZ=Australia/Adelaide date` → 2026-06-18 20:38 ACST.

Same-evening continuation of S163 (closed 19:17); the open ran
the full ritual clean (drift-check passed — current_state,
SESSION_163, and build-picture all stamped 19:17 at S163 close;
root clean).

## Pre-flight checks

Open ritual clean. Drift-check passed: `current_state.md`
last-updated and `SESSION_163.md` "Closed:" both 19:17 ACST;
`v3_build_picture.md` updated at S163 close (streams moved);
`.close_out_backups/` held only the S164 opening prompt (no
stale S163 prompt). Root: 11 expected `.md` + `v3_build_picture`
+ `external_api_resources` + `openapi.json`; all expected dirs
present; no phantom files.

## Session shape

An execution-and-proof session. It opened teed up to hand the
locked customerRef fix brief to Code; in practice it ran the
full arc end-to-end in one sitting: triaged Code's read-and-
confirm read-back against the locked brief (faithful — go),
triaged Code's completed fix report (clean), and then — after
the operator ran the live test — triaged the live launcher log
showing the fix working against real Betfair. The session's
primary objective (clear the last validation gate) was not just
met but proven on live money.

The session closed on a forward-routing decision raised by the
operator: before W16 cutover scoping proper, the operator wants
to refine interface deficiencies they have already noted, on the
reasoning that cutover is a one-way switch (v2 retires, no
fallback) and any daily-efficiency or capability loss carried in
lands directly on live operation — most of which is Strategy 1
(Safety Net), ~95% of profit, running through this exact lay
screen. Claude agreed with the direction but bounded it: fix
only deficiencies that cost real speed or capability on
Strategy 1's daily path before cutover; everything else (polish,
Strategy 2–4 items) follows after. The operator chose to close
for the night and do an interface run-through tomorrow morning
to build a formal list for pre-/post-cutover classification.

## What was delivered

1. **Triage of Code's read-and-confirm read-back (go).** Before
   Code touched anything it returned its understanding of the
   locked brief. Checked line-by-line against
   `customer_ref_fix_brief_v2.md` — faithful on every anchor and
   value (the `bh-`+26-hex = 29-char scheme, both placement
   sites, the strategy-tag shortening, the length guard, the
   test set), and it correctly understood it was executing the
   locked Option B decision, not reopening it. Cleared to
   execute.

2. **Triage of `customer_ref_fix_report.md` (clean).** Read the
   342-line report from disk (not the chat summary). All four §5
   changes landed as briefed, re-grounded by grep (tree had
   moved off the brief's line numbers). Tests 1018 → 1028, +10
   fully accounted, zero failures, zero regressions. import-
   linter 5 kept / 0 broken (the shared helper needed no
   `.importlinter` change — `clients` sits below both `ui` and
   `workflows.bet_entry`). No git mutation (dirty set 61 → 62,
   single delta = the authorised new helper file). Bet-safety
   gate byte-for-byte preserved (`placement.py` never opened).
   Three findings (F1 pre-existing in-flight ruff debt left
   alone; F2 customerRef==customerOrderRef belt-and-suspenders
   note; F3 helper kept private, imported directly) — all
   consequence-free code-tidiness; nothing operator-facing.

3. **Live validation — PROVEN.** The operator launched v3 via
   `BetHub.command` (live mode), streaming reached SUBSCRIBED at
   startup, and placed three real lays. All three confirmed by
   Betfair as `POST /api/v1/racing/lay → 200 OK` with real bet
   ids and the new short reference visibly doing its job:
   - `bh-10bccb7eac8840709661a481de` → bet 432648975139
   - `bh-d6b318d715f44a33a75d2620ba` → bet 432649004404
   - `bh-5ff0ab39c8ae4973818c037656` → bet 432649081786
   No `customerRef … 32 character limit` 503. The S162-named,
   S149-blocking placement failure is cleared. (Startup still
   shows the known non-fatal `SUBSCRIPTION_LIMIT_EXCEEDED` =
   >200-market over-subscription, immediately recovered —
   parked cleanup, unchanged.)

4. **Forward-routing decision — interface refinement precedes
   cutover scoping.** Operator-raised and Claude-agreed: an
   interface-deficiency triage gates W16 cutover scoping. S165
   consolidates the operator's formal run-through list and
   classifies each item pre- vs post-cutover against the bar
   "does it cost real speed or capability on Strategy 1's daily
   path?" No code or scope change this session — a routing
   decision only.

## Standing-instruction adherence check

- **Cat 1 brevity / decision-framing** — held; triages led with
  the verdict (go / clean / gate cleared), detail deferred.
- **Cat 1 don't-surface-dev-lead-calls (added S163)** — honoured:
  the three report findings (F1/F2/F3) were named as
  consequence-free and not enumerated for review; only the
  operationally-relevant facts (bet-safety gate preserved, the
  live-test Terminal heads-up) were surfaced.
- **Cat 1 inventory-first on long technical reports** — the
  342-line fix report was triaged inventory-first, each finding
  classified for operational impact (all nil).
- **Cat 1 escalate-to-detail-when-warranted** — used once, on
  the interface-refinement-before-cutover question (flagged
  "this deserves a little detail" before the sequencing
  rationale).
- **Cat 2 timestamp anchors (DR-021)** — open + close anchored
  ACST.
- **Cat 2 always-provide-opening-prompt** — S165 prompt produced
  this close.
- **Cat 2 always-provide-Code-session-prompt (added S163)** — the
  ready-to-paste Code prompt was available from the S164 opening
  prompt; the operator ran Code without needing to ask.
- **Cat 3 Desktop Commander exclusive; verify every write** — all
  reads/writes via DC; report read from disk, not trusted from
  chat summary.
- **Cat 5 make-the-call / dev-lead territory** — the read-back
  and report triages were Claude's dev-lead checks, not punted
  to the operator; only the live-money note and the cutover-
  sequencing call were surfaced.
- **Silent close ritual (Cat 1)** — this close ran silent;
  single post-verify line + the two between-session flags.

## Open items out (closed this session)

- **Execute `customer_ref_fix_brief_v2.md`** — Code executed it
  end-to-end; report triaged clean. ✅
- **Triage `customer_ref_fix_report.md`** — done; clean. ✅
- **Operator live $5 lay validation** — done; three live lays
  placed and Betfair-confirmed, no 503. The last operator-
  validation gate before W16 cutover is cleared. ✅
- **Bet-safety preservation at the fix** — verified in report
  (`placement.py` untouched) and held live (lays placed only on
  the operator's deliberate action). ✅

## Open items (carried — pointer to current_state.md)

- **Interface-deficiency triage (S165 primary).** Operator
  builds a formal run-through list tomorrow; S165 classifies
  pre- vs post-cutover. Gates W16 cutover scoping.
- **W16 v2→v3 cutover scoping** — now downstream of the
  interface triage. DR-027/028 re-read trigger when it begins.
- **Live unmatched lays** — the three S164 test lays were
  unmatched (`matched=0.0`) and sit as real exposure in the live
  market; operator to pull/manage as they see fit (operator-side,
  not a build item).
- All S162/S163 parking-lot items unchanged (F1 uncaught-
  transport gap; 200-market over-subscription; in-memory audit-
  sink durability; streaming hardening F3/F5/F4; quick-lay modal
  error-reason surfacing; the `_coerce_uuid`/`_safe_uuid` latent
  degrade — now self-healed by the clean `bet_id`, confirm at
  next relevant touch; the longer parking lot).

## Session close state

- **Rebuild folder root:** clean, no phantom files.
- **`dr029/2_4_betfair_streaming/`:** holds the superseded v1
  brief, the impact-review brief + report, fix brief v2, and now
  `customer_ref_fix_report.md` (the executed-fix report). All on
  disk.
- **`bethub-v3`:** fix code-complete and proven live. Tree
  remains dirty/in-flight by design (no git mutation this arc);
  the single new file is `clients/betfair_client/v1/
  _customer_ref.py`.
- **`.close_out_backups/`:** S165 opening prompt written; stale
  S164 prompt removed.
- **Project knowledge base:** `standing_instructions.md` was
  edited at S163 and still needs the manual re-upload if not yet
  done (operator-side; flagged below). No new standing-
  instruction edits this session.

## Forward routing — CONFIRMED WITH OPERATOR

S165 does NOT open straight onto W16 cutover scoping. The
operator will do an interface run-through tomorrow morning and
bring a formal list of noted deficiencies. S165 consolidates
that list (plus anything already in the parking lot / session
records), and classifies each item as a **pre-cutover blocker**
or a **post-cutover refinement**, against the bar: *does it cost
real speed or capability on Strategy 1's daily path?* Pre-cutover
blockers get scoped/briefed; post-cutover items are logged and
deferred. W16 cutover scoping proper follows once the pre-cutover
set is cleared. Operator confirmed close for the night.

## Pending operator-side action

- **Re-upload `standing_instructions.md`** to the bethub-rebuild
  Claude Project knowledge base if not already done since S163
  (edited at S163: two new instructions). Drive auto-syncs the
  local folder; the Project KB copy needs the manual refresh.
- **Manage the three live unmatched lays** — real exposure in
  the live market; pull or leave as desired.
