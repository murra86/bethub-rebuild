# Brief — Racing-page + Betfair-modal codebase review

**Type:** Source-code review (read-only). No fixes, no edits.
**Repo:** `bethub-v3` (local Mac).
**Audience:** Claude Code, out-of-session, single bounded run.
**Produces:** one report (path in §13).
**Drafted:** Session 165 (2026-06-19 ACST).

---

## §1 — What this brief is and is not

This is a **read-only source-code review** of the v3 racing
page, the Betfair hedge modal, and the `BetHub.command`
launcher. Code reads the named code, answers the four verify
questions (§6–§9), reviews the launcher lifecycle + backend
throttle/data risk (§11), and maps the impact of the
pre-cutover fixes (§8 fix portion + §10). Code writes **one
report** and changes **no source files**.

It **is**:
- An evidence-gathering pass. Every answer is grounded in
  `file:line` references Code actually read.
- A pre-fix impact map. For the four pre-cutover fixes, Code
  names every file/region a fix would touch and any backend or
  data-layer reach.

It is **not**:
- A fix session. Code edits nothing, fixes nothing, refactors
  nothing. Findings go in the report; remediation is the next
  operator-Claude session's call, then a separate fix brief.
- A scope-creep pass. Only the items named here. Other noted
  deficiencies (layout redesign, hot buttons, modal back-bet
  support, cosmetic alignment) are explicitly out (§14).
- A git operation. The v3 tree is dirty by design; Code touches
  no git state (§14).

Surprises become **findings**, not detours. If something looks
wrong outside the named scope, Code notes it in the report's
findings section and moves on.

---

## §2 — Why this work exists

v3 places real bets live; the placement blocker is cleared
(Session 164). Before the one-way v2→v3 cutover (W16), the
operator did a racing-page run-through and produced a
deficiency list. Session 165 triaged it into pre-cutover
blockers and post-cutover refinements.

Four items can't be classified or briefed from the planning
side without reading the code — they're questions about what
the tool currently does, and the answer is load-bearing
(financial correctness, bet-placement correctness, downstream
analysis keying). Three confirmed pre-cutover fixes also touch
form state, default population, or the data layer in ways that
need their blast radius mapped before a fix brief is written.

This review answers the questions and maps the blast radius, so
the fix briefs that follow are written with full knowledge
instead of blind.

---

## §3 — Pre-reads

Required, in order:

1. This brief, in full.
2. `ui/web/src/routes/Racing.tsx` — the racing page shell
   (filters, race selection, state that the table + panels
   read).
3. `ui/web/src/components/OddsTable.tsx` — the odds grid
   (runner column, BF back/lay, TREND, SOFT ODDS).
4. `ui/web/src/components/HedgeModal.tsx` — the Betfair hedge
   modal (lay/back, auto-calc).
5. `ui/web/src/components/LogBetPanel.tsx` — the log-bet bar at
   screen bottom (odds carry-over, clear).
6. `ui/web/src/components/PromoBar.tsx` — promo selection + the
   per-promo EV display.
7. `ui/web/src/ev/evEngine.ts`, `ev/commission.ts`,
   `ev/softOddsLadder.ts`, `ev/tickLadder.ts` — the EV +
   commission + soft-odds math.
8. `ui/api/routers/racing.py` — the backend racing endpoint
   feeding the page (runner identity, prices).

Reference-only (read if a thread leads there, not required):
`ui/web/src/promos/presets.ts`, `ui/web/src/hooks/
usePriceMemory.ts`, `ui/web/src/api/racing.ts`,
`ui/web/src/api/types.ts`, `clients/betfair_client/`,
`clients/vps_client/`, `domain/promos/`, `domain/pricing/`.

---

## §4 — System access

- **Filesystem:** read-only on `bethub-v3`. Code reads source;
  edits nothing.
- **Database:** read-only if needed (e.g. to see how a runner
  number is stored). Query the live file in place via
  `start_process` Python at
  `/Users/tim/Desktop/Projects/bethub-v3/data/bethub.db` —
  never copy it (DR-013). Most of this review is source-read;
  DB read is only if a provenance thread needs it.
- **Tests:** Code may run the suite to understand behaviour.
  This is a `uv` project — use `uv run pytest` (NOT bare
  `python3 -m pytest`, which fails at collection). Running
  tests is optional and read-only; no test is added or changed.
- **No network / no Betfair calls.** This is a static read of
  code, not a live-system probe.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 for any
  time reference in the report.

---

## §5 — Area map (orient first)

Before answering the questions, Code produces a short map of
the racing-page + modal area: which file owns the filters, the
runner column, the price columns (BF back/lay, TREND, SOFT
ODDS), the promo EV display, the log-bet panel, and the hedge
modal — and where each gets its data (frontend-derived vs from
`racing.py` vs from a client). One small table. This anchors
every later section and surfaces any file the pre-reads missed.

---

## §6 — Question 1: are the promo EV estimates sound?

**Operator concern:** the per-promo EV shown on the race page
drives real betting decisions. If the displayed EV is wrong,
bets get placed off bad numbers. This is the most important
question in the review.

Code traces the EV calculation end-to-end for each promo type
the page shows, starting at the display (`PromoBar.tsx`) back
through `ev/evEngine.ts`, `ev/commission.ts`, and the soft-odds
/ tick ladders, plus `promos/presets.ts` for the per-promo
parameters.

For each promo type, the report states:
- The formula actually implemented (in plain terms + the
  `file:line` of the core calc).
- The inputs it consumes (advertised odds, lay price,
  commission, refund/free-bet parameters) and where each comes
  from.
- Whether the free-bet leg is modelled (the ~70%-of-face
  conversion the operator works to) and at what rate, vs
  hard-coded vs configurable.
- Any assumption that looks unsound, stale, or inconsistent
  with the Strategy-1 insurance-cycle logic (whole cycle =
  original bet + triggered free bet + free-bet outcome).
- Whether the math reconciles with v2's behaviour where a
  regression fixture exists (`ev/__fixtures__/v2_regression.ts`).

**Code does not fix or "correct" the EV.** If something looks
wrong, it's a finding with evidence. The operator decides
whether it's a pre-cutover fix and flags it for the analytics
re-visit.

---

## §7 — Question 2: does the modal hedge amount auto-calc
correctly?

**Operator concern:** the hedge modal's whole job is to take a
position set on the race screen (e.g. a $50 free bet to match,
or a general-turnover hedge) and compute the correct lay (or
back) amount at the **current lay price and commission**. The
operator needs confirmation this actually happens — and that it
recalculates when price or commission changes.

Code traces, in `HedgeModal.tsx` + the `ev/` math it calls:
- How the hedge stake is computed for each hedge type the modal
  supports today (free-bet match; general turnover / standard
  hedge; any other).
- Whether the lay amount auto-calcs from the **live** lay price
  or from a stale/snapshotted price, and whether it
  recalculates on price change.
- Whether commission is applied, at what rate, and where the
  rate comes from (per-account? hard-coded? a default?).
- Free-bet stake-not-returned handling (a free bet pays
  winnings only — the lay-to-match math differs from a
  cash-stake hedge). Report whether the modal models this.
- Whether the modal can currently place a **back** as well as a
  lay (operator noted it looks lay-only). State plainly which
  it supports today and what gating a back-bet would touch —
  this maps the post-cutover "add back-bet" item without doing
  it.

Report states current behaviour as found, with `file:line`
evidence. If the auto-calc is wrong or price-stale, that's a
pre-cutover-critical finding.

---

## §8 — Question 3: runner-number provenance + canonical key

**Operator concern:** the runner column shows doubled,
mismatched numbers (e.g. Rockhampton R1 "1. 2. Heart N Power").
Two numbers are being rendered; the operator suspects one is
Betfair's and one is tool-applied. Mis-reading a runner number
risks laying the wrong selection — and the choice of which
number is canonical affects downstream historical analysis.

Code determines:
- Exactly which two (or more) number fields render in the
  runner column, in `OddsTable.tsx`, and the data path each
  comes from — back through `racing.py` and the clients to
  origin (Betfair selection metadata vs Racing-API/VPS data vs
  a tool-assigned index).
- What each number means (Betfair runner number / cloth number
  / saddlecloth / barrier / an array index / tool sort order).
- Where they diverge and why (the mismatch source).
- Which field is stable and canonical for **joining to
  downstream historical analysis** (the capture.db analytical
  side) — Code gives a reasoned recommendation, naming the
  trade-offs. This is the canonical-key call the operator will
  confirm.
- For the fix itself (collapse to one correct number): every
  file/region the change would touch, frontend and backend,
  and whether it's display-only or reaches the data the bet
  record is keyed on.

---

## §9 — Question 4: what base price is TREND % calculated on?

**Operator concern:** the TREND column shows a %, but it's
unclear what base price the % is measured against. The operator
is weighing changing it to a line/sparkline later (post-cutover
redesign — NOT in this brief); for now they need to know what
it currently represents.

Code states, from `OddsTable.tsx` + `hooks/usePriceMemory.ts`
(or wherever the trend is computed):
- The exact base the % is calculated against (opening price?
  first observed price this session? previous tick? BSP?).
- The time window / memory model behind it (how far back
  "trend" reaches, when it resets — e.g. on race switch).
- Whether the base survives a race switch or page reload, and
  whether that's the intended behaviour.

Answer only. No redesign — the line/sparkline idea is a
post-cutover item.

---

## §10 — Impact map: the three frontend pre-cutover fixes

For each, Code does **not** fix — it names the exact
file/region the fix lands in, the blast radius (what else reads
the same state), and any backend/data reach. This is what lets
the fix briefs be written cleanly.

**(a) Filters clear each other (`Racing.tsx`).** When all three
code filters (T/G/H) are on and one is clicked, the other two
clear instead of toggling just the clicked one. Code names the
filter-state handler and confirms whether the fix is purely
local toggle logic or whether anything downstream keys off the
filter state. (Frontend-only expected — confirm.)

**(b) SOFT ODDS default (`OddsTable.tsx` / `LogBetPanel.tsx` /
`ev/softOddsLadder.ts`).** The SOFT ODDS column is pre-filled
with the Betfair BACK price; operator wants it blank by
default. Code determines where the prefill is set, whether it's
frontend default or server-driven, and — importantly — whether
anything (EV calc, bet log, the hedge modal) **reads** SOFT
ODDS expecting it to be populated, so a blank default doesn't
silently break a downstream calc.

**(c) Log-bet clear + odds carry-over (`LogBetPanel.tsx` +
`Racing.tsx`).** Two parts: (i) no way to clear the log-bet
data; (ii) selected odds carry over to a new race when a
different race is picked in the sidebar. Code maps the form
state — what's lifted to `Racing.tsx` vs local to the panel,
what does/doesn't reset on race switch, and where a clear
action and a race-switch reset would hook in. Confirms it's
frontend form-state only with no backend reach.

---

## §11 — Launcher lifecycle + backend idle/shutdown risk

**Operator concern (the important one): is there any risk — to
the tool, to Betfair throttling, or to data — in how the
launcher and backend behave across the operator's real
close-patterns?** v2 had problems in this area, so the operator
wants 100% confidence. Plus a secondary annoyance: terminal
windows accumulating.

`BetHub.command` runs one foreground `uvicorn` pinned to port
8787, with a shutdown trap (SIGINT/TERM/HUP/EXIT) that frees the
port, and a stale-port `kill -9` before each start. So closing
the **terminal** stops the server; closing only the **browser**
leaves the server running. The questions below are about what
the *backend* does in those states — which the launcher script
alone can't answer; it needs the app code.

**Additional reads for this section** (beyond §3): `BetHub.command`
(launcher), `ui/api/main.py` (FastAPI startup/shutdown lifespan
hooks), `clients/betfair_client/` (the auth/auto-login provider,
the streaming client, the login-throttle logic), and wherever
the placement **audit sink** lives (currently in-memory).

Code answers, with `file:line` evidence:

**(a) Close-pattern lifecycle map.** For each of the three real
patterns — (i) leave both open, (ii) close browser only / leave
terminal, (iii) close browser + terminal — state what happens to
the uvicorn process, the Betfair auth session, and the streaming
connection.

**(b) Idle-backend behaviour — the throttle question.** With the
browser closed but uvicorn still up, does the backend make *any*
Betfair calls on its own? I.e. is there a background auto-login
refresh timer, a streaming keepalive / auto-resubscribe loop, or
any scheduled polling that fires with no UI driving it — or is it
purely request-driven (no UI → no Betfair traffic)? Name every
timer/loop with cadence and `file:line`. This is the core of the
throttle question.

**(c) Multiple-server / orphan risk.** Confirm the pinned port +
stale-port-clear genuinely guarantees only one live server, and
that a relaunch's `kill -9` actually terminates the *old* Betfair
session and stream rather than leaving an orphan still connected.
Flag any path to two concurrent servers (e.g. the
`BETHUB_LAUNCH_PORT` override) both talking to Betfair in
parallel.

**(d) Throttle-state persistence.** The escalating login throttle
(cool-off 30m→1h→2h→4h, hard kill at 5 consecutive failures) —
is its state in-memory (reset on every process restart) or
persisted across restarts? Critically: can rapid relaunching
reset or defeat the back-off and reproduce the request-hammering
that caused the ~48h v2 Betfair lockout? State plainly.

**(e) Shutdown cleanliness + data risk.** On a clean stop (window
close / Ctrl-C → the SIGTERM trap), does the app cleanly log out
of Betfair and close the stream, or leave a dangling session /
connection that counts against Betfair limits? On an abrupt
`kill -9` (the stale-port-clear path, and the trap's fallback
hard-kill), what in-flight data is lost or at risk — the
in-memory audit sink (known gap), plus any unflushed SQLite/WAL
write or half-written operational state? WAL is crash-safe by
design; confirm nothing relies on a graceful flush to avoid data
loss or corruption.

**(f) Terminal accumulation — cause + lightest fix (map only).**
Identify why windows pile up (Terminal not set to close on clean
exit, or windows left showing a stopped server) and name the
lightest change that would address it **without touching the
risk-bearing shutdown/port logic**. Map the fix; don't build it.

**Risk-grade each finding.** If (b)–(e) surface a real throttle
or data-loss/corruption risk, that's potentially
pre-cutover-critical — flag it prominently, not buried. If
everything is clean (purely request-driven, single server,
crash-safe, clean logout), say so plainly — that's the
confirmation the operator is asking for. Read-only throughout:
the launcher and backend are read, not edited.

---

## §12 — Sequencing within session

1. §5 area map first — orients everything.
2. §6 (EV soundness) and §7 (modal auto-calc) next — the two
   financial/bet-correctness questions, highest stakes.
3. §8 (runner number) — provenance trace + canonical recommend.
4. §9 (TREND base) — quick.
5. §10 (a)(b)(c) impact maps — last; they lean on the area map.
6. §11 launcher lifecycle + backend risk — independent of the
   racing-page read; can run first or last. The throttle/data
   risk questions (b)–(e) are the highest-priority part of the
   whole review alongside §6/§7.

Code may reorder if a thread runs naturally across sections
(e.g. tracing EV and commission together). Keep each section's
answer self-contained in the report regardless of read order.

---

## §13 — Output spec

**One file:** `interface_triage/racing_page_review_report.md`.

Sections mirror this brief: area map; Q1 EV; Q2 modal; Q3
runner number; Q4 trend; impact map (a)(b)(c); launcher
lifecycle + backend risk (§11, with each sub-question answered
and risk-graded); findings; self-assessment. Each answer
carries `file:line` evidence.

Each pre-cutover fix area (§8 fix portion, §10 a/b/c) ends with
a one-line **touch-list** (files/regions a fix would modify)
and a **frontend-only / reaches-backend** tag, so the next
session can bucket and brief fast.

**Length:** roughly 300–550 lines. Longer is fine if evidence
warrants (flag in self-assessment); don't pad.

**The report does NOT contain:** fixes, diffs, "corrected"
code, recommendations on whether to cut over, or any redesign.
For Q3's canonical-key it gives a reasoned recommendation (that
one's a named deliverable); everywhere else it reports current
behaviour + findings and leaves the call to the operator.

---

## §14 — Hard limits (non-negotiable)

- **Read-only. No source edits, no fixes, no refactors.** Not
  one line of `.tsx`, `.ts`, or `.py` changes.
- **No git operations.** The v3 tree is dirty/in-flight by
  design. Code reads working-tree state at start, touches no
  git state — no `add`, `commit`, `stash`, `restore`,
  `checkout`, `reset`. At close, `git status` shows the dirty
  file list unchanged.
- **Bet-safety untouched.** `workflows/bet_entry/…/placement.py`
  (the bet-safety gate) is not modified. It may be read if a
  thread leads there, but the gate stays byte-for-byte intact.
- **No new tests, no changed tests.** Running the existing
  suite read-only (via `uv run pytest`) is allowed; adding or
  editing tests is not.
- **No scope creep.** Out of scope and not to be touched:
  table layout/alignment redesign, account hot buttons, stake
  hot buttons, modal cash/free-bet alignment, adding back-bet
  capability, size-at-best-price column, the TREND line/
  sparkline redesign. Several are *mapped* (Q2 names what a
  back-bet would touch) but none are built.
- **Single bounded session.** If the review needs more than one
  Code session, that's a finding — partial-but-coherent beats
  complete-but-lost-coherence. Don't run past budget.
- **No operator ping mid-session.** Run end-to-end; surface
  everything in the report.

---

## §15 — What happens after Code's session

Code produces the report and stops. The next operator-Claude
(Chat) session:
1. Reads `racing_page_review_report.md` from disk.
2. Walks the four answers with the operator — confirms the
   EV soundness verdict, the modal auto-calc verdict, the
   canonical runner-number choice, and the TREND base.
3. Finalises the pre-/post-cutover buckets now that blast
   radius is known (a verify item may move buckets on what's
   found).
4. Commissions the actual **fix brief(s)** for the confirmed
   pre-cutover set — separate briefs, Code-bound. This review
   does not produce them; speculative chained briefs are drift.

---

## §16 — Cross-references

- **Streams:** Interface refinement (the pre-cutover deficiency
  triage gating W16 cutover) — §5–§10; and Launch / packaging
  (the `BetHub.command` launcher lifecycle) — §11.
- **Feeds:** W16 (v2→v3 cutover) — must-fix interface items
  cleared before cutover scoping. DR-027/028 (the two-database
  split + integration boundary) re-read trigger when cutover
  scoping begins — not this brief.
- **DRs in play:** DR-013 (DB read discipline — read in place,
  never copy), DR-021 (Adelaide timestamps), DR-030 (v3 module
  boundaries — relevant if Q3/Q-impact threads cross the
  client/ui boundary), DR-032 (Betfair canonical reference layer
  + auto-login / login-throttle — the §11 backend-risk surface;
  read-only here).
- **Session record:** SESSION_165 (this triage).
- **Excluded (parking lot, not this brief):** quick-lay modal
  error-reason surfacing, F1 uncaught-transport gap,
  200-market over-subscription, streaming hardening (F3/F4/F5).
  Note: §11(e) *surfaces and risk-grades* the in-memory
  audit-sink data-loss-on-shutdown — but the durability **fix**
  stays parked; this review only reports the risk.

---

*End of brief.*
