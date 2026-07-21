# Brief 2 — After-the-fact manual bet entry (v3 build)

**Status:** LOCKED (Session 175) — operator-signed, ready for
Code hand-off. Both open calls resolved: own "Log Past Bet"
nav tab; brief 2 settles won/lost/void only (promo-trigger /
free-bet credit deferred to brief 3, which must cover this
manual path too).
**Type:** build brief — single bounded Claude Code session.
**Serves:** the after-the-fact manual-entry workstream locked in
`betlog_scope.md` ("Manual after-the-fact bet entry"); §2.8
bet-schema "operator picks a resulted-race row" design.
**Builds on:** S169 (manual-entry shape locked), S171 (BetLog
built — the surface a logged bet shows up in), S172
(bets-feed robustness bug + write-path spot-check folded in
here), S173 (capture-store retention confirmed ample), S174
(DR-033 data-source roles; settle-off-Betfair vs manual flag).
**Output report:** `interface_triage/manual_entry_build_report.md`.

---

## §1 — What this brief is and is not

This is a BUILD brief. Code builds the after-the-fact manual
bet-entry capability into v3 end-to-end, against the named
anchors in §5, in a single bounded session.

What it builds (detail in §5):
  - a new read on the VPS-read layer (`vps_client`) that
    resolves a human-picked race (date -> venue -> race
    number) to its Betfair identity + runner set;
  - a "create bet" endpoint on the bets router;
  - settle-at-entry (set the bet's outcome at write time for
    a race that has already run);
  - the bets-feed robustness guard (one malformed row must
    not blank the whole log);
  - the manual-entry screen on the frontend;
  - a write-path spot-check (a manually-entered bet persists
    and shows in BetLog).

Single bounded Code session. If the work does not fit one
session, that is a finding — Code stops and reports it,
rather than continuing past budget. Partial-but-coherent
beats complete-but-lost-coherence.

Surprises become findings in the report, not mid-session
escalations and not scope chases. Code does not ping for
direction mid-flight; it records the surprise and carries on
with what it can.

Remediation of anything surfaced routes to the next
operator-Claude triage session — not into Code's report.
Code reports what it found and did; it does not self-redirect
into fixes outside this brief.

What this brief is NOT:
  - not the free-bet credit-in build (that is brief 3);
  - not the bet-mutation audit log (its own fenced brief,
    after this one);
  - not any change to live / near-time auto-settlement (that
    path stays exactly as built);
  - not any write to the capture store (`vps_client` is
    read-only; this brief adds a read, nothing more).

---

## §2 — Why this work exists

In a hectic Strategy 1 (Safety Net) burst the operator
sometimes fires a bet and misses logging it, or has to walk
away and catch up days later. The operation is "place first,
log later" by necessity — the EV is extracted regardless of
when the bet gets recorded. So v3 must let the operator log a
bet **after the race has run**, occasionally a couple of days
later.

Three findings cleared the path to building this now:

  - **Retention is ample (S173).** The capture store holds
    resulted races ~15.5 months back, nothing pruned — a
    days-late bet always finds its race. The original "how
    much storage / what window" worry does not land on us.
  - **Settlement is solved (S174 / DR-033).** Win/lose
    settles off the bet's Betfair market + selection; that
    join is ~95% solid. The broken finish-position field (the
    placings gap) is analytics-only and is NOT on the path
    here — because the operator settles the bet at entry (the
    race already ran; the outcome is known).
  - **The write path is safe (S172).** v3's delete is
    single-row and fenced; every bet carries a real Betfair
    market id + selection id (NOT NULL), so a logged bet can
    never float free of its event.

This brief wires those findings into a working catch-up flow.

---

## §3 — Pre-reads

Required (read before starting):

  - `interface_triage/betlog_scope.md` — the locked
    manual-entry shape (date -> venue -> race number ->
    runner -> Betfair stamp -> write) and the BetLog surface
    a logged bet appears in.
  - `contracts/vps_client_contract.md` §§1-6, §9, §10 — the
    VPS-read boundary; the six existing surfaces; the
    backward-compatible-addition rule (§10.3) the new lookup
    surface lands under.
  - This brief, in full.

Reference-only (consult as needed, not required reads):

  - `decisions.md` DR-033 (data-source roles), DR-027/028
    (two-database boundary), DR-019 (derived P&L on read),
    DR-032 (Betfair canonical reference).
  - `workflows/bet_entry/v1/record_builder.py` — the
    hand-logged-bet builder this reuses.

---

## §4 — System access

  - **v3 repo (Mac, read-write):**
    `/Users/tim/Desktop/Projects/bethub-v3`. Code edits only
    the anchors named in §5. The repo may have a dirty working
    tree — see dirty-tree discipline in §9.
  - **capture store (VPS, READ-ONLY, via `vps_client`):** the
    new lookup surface reads `capture.db` through `vps_client`
    only — never raw SQLite, never a copy. Tunnel/SSH per the
    existing `vps_client` connection path. No write of any
    kind to `capture.db` (§9 hard limit).
  - **Tests:** `uv run pytest` (the repo is a `uv` project on
    Python 3.12; bare `python3` is 3.11 and fails collection).
    Frontend: `npm run build` / `tsc -b` / vitest as the
    existing suites use.
  - **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 for
    every time-of-day reference in the report.

---

## §5 — The build

Six pieces, built in the order below (sequencing reasoning in
§6). Each names its anchors. "Anchor" = the existing file/region
Code reads or extends; line numbers are as-found at draft time
and may have shifted — Code confirms against the live file.

### §5.1 — New VPS-read surface: race lookup by human fields

**The gap.** `vps_client/v1` today exposes six read surfaces
(`race_metadata`, `race_runners`, `runner_metadata`, `results`,
`bracketing`, `starting_price`, `identity_resolve`) — all keyed
on Betfair's own identifiers (`event_id`, or
`market_id`+`selection_id`). None take human-friendly fields
and return the race's Betfair identity. Manual entry needs
exactly that reverse lookup.

**Build.** Add a new read surface to `clients/vps_client/v1/`
(new module, e.g. `race_lookup.py`; export via the package
`__init__.py` alongside the existing surfaces). It serves a
**cascading picker** — each step reads the store's own values so
the operator never free-types a venue (see venue-matching note
below). Suggested surface shape (Code may refine call count):

  - list meetings/venues that ran on a given date;
  - list races (number + jump time + code) for a chosen
    date+venue;
  - resolve a chosen date+venue+race-number to: the Betfair
    `event_id`, the Betfair **Win** `market_id`, and the runner
    set (`selection_id`, name, barrier, scratching status).

Returns the standard typed envelope (`fresh`/`stale`/
`unavailable` with the closed reason set) per contract §8.
`genuine_absence` covers "no such race in the store"; the
frontend renders that cleanly (no match — pick again).

**Venue-matching discipline (load-bearing).** The recurring
venue-harmonisation gremlin (venue strings not aligning across
sources) is sidestepped structurally: the picker is driven
*from the store's own values* — the operator selects from the
list the lookup returns, so every match is an exact match
against strings the store holds, never a free-typed guess. Do
not add fuzzy venue matching; if a race is genuinely absent,
return `genuine_absence` and let the operator re-pick.

**Read-only (non-negotiable).** This surface only reads. It
leans on the solid part of the store (the human-fields ->
`market_id`/`selection_id` pairing, ~95% present), NOT the
broken finish-position field. No write path of any kind is
added to `vps_client` (§9 hard limit).

**Contract update.** Append the new surface to
`contracts/vps_client_contract.md` as a new `§9.7` (same
per-surface format as §9.1-§9.6) and add a dated line to the
§6 version-history table — a backward-compatible addition per
§10.3 (new endpoint alongside existing; no version bump). This
keeps the contract and the code in sync, as the existing §9
surfaces were authored.

### §5.2 — New "create bet" endpoint on the bets router

**Anchor.** `ui/api/routers/bets.py` (~525 lines) currently
serves GET `list_bets_feed` (~L375), PATCH `edit_bet_endpoint`
(~L464), DELETE `delete_bet_endpoint` (~L518). There is no
create endpoint — add one (POST) alongside these.

**Build.** A POST endpoint that accepts the manual-entry
payload and writes one bet. The payload carries:

  - the resolved Betfair identity from §5.1 (`event_id`, Win
    `market_id`, the chosen runner's `selection_id`) — this is
    the canonical leg stamp, NOT NULL;
  - bet metadata the operator supplies: `account_at_book_id`,
    `book_or_exchange`, side (back/lay), `requested_stake` /
    `matched_stake`, price, `strategy_tag` (nullable),
    `is_free_bet` (+ conversion rate when true), `placed_at`
    (the original race date/time the operator is logging for);
  - the **settle-at-entry outcome** (see §5.3).

**Reuse the existing write path — do not invent a parallel
one.** Build the record through the hand-logged-bet builder
(`workflows/bet_entry/v1/record_builder.py` —
`build_soft_book_bet_record` / `SoftBookRecordInputs` at ~L157/
L337 is the closest existing shape: operator-supplied fields, a
`LegSnapshot` carrying the Betfair ids, `MatchStatus.FINAL_FULL`
default with partial-match override). Persist via
`store/repositories/bets.py` -> `write_bet_record` (~L545, the
`INSERT INTO bets` + `INSERT INTO bet_legs` path). Manual entry
resolves its own fresh `cycle_id` (a standalone bet/cycle, not
sharing a hedge's cycle).

**Build decision left to Code (name it in the report):**
whether to (a) extend `build_soft_book_bet_record` to accept a
non-default settlement state + a new entry-path value, or (b)
add a sibling `build_manual_bet_record`. Either is fine; the
constraint is that the Betfair leg ids come from §5.1 and the
settlement state comes from operator input (§5.3). Add a new
`EntryPath` enum value for after-the-fact manual entry
(backward-compatible enum addition).

### §5.3 — Settle-at-entry

**Anchor.** `domain/bets/__init__.py` -> `SettlementState`
(~L107): `PENDING` (default at entry), `SETTLED_WON`,
`SETTLED_LOST`, `VOIDED` (plus `PROVISIONAL`).

**Build.** Because the race has already run when the operator
logs the bet, the create flow (§5.2) sets `settlement_state`
directly to the operator-chosen terminal outcome —
`SETTLED_WON` / `SETTLED_LOST` / `VOIDED` — at write time,
instead of leaving it `PENDING`. P&L is derived on read
(DR-019), so no stored P&L to compute here — the settled state
plus stake/price/commission is enough for the existing
read-side derivation to produce the right number.

**Live / near-time path is untouched.** A bet logged at or
near race-time still goes in `PENDING` and auto-settles off
Betfair exactly as built. Settle-at-entry is an additional
capability for the days-late case, not a change to the live
flow. Code does not touch `settlement.py` or the
auto-settlement worker.

**Out of scope here (LOCKED S175):** capturing whether a Safety
Net runner placed 2nd-4th and triggered a refund/free bet.
Brief 2 settles the original bet's own outcome only —
won/lost/void. The promo-trigger question ("did this fire a
free bet? credit it") is built once, at settlement, in brief 3
(free-bet credit-in), and wired to BOTH entry points: the live
"Placed?" hook already scaffolded in BetLog AND this brief's
manual settle-at-entry screen. No promo/refund flag is added
here — it would be an orphan (nothing in v3 yet consumes it).
See §10 for the brief-3 carry-forward note.

### §5.4 — Bets-feed robustness guard

**Anchor.** `ui/api/routers/bets.py` -> `_to_feed_item`
(~L281), called in the `list_bets_feed` loop (~L431, `for row,
legs in rows`). Today the feed serialises the page as a unit:
if one row fails to construct server-side, the **entire list
500s** and BetLog goes blank (the S172 bug — root cause
unpinned because the offending rows were gone, but the
fragility is structural).

**Build.** Isolate per-row construction: wrap each
`_to_feed_item` call so one bad row is **skipped and flagged**
(logged with the real server-side error + the offending
`bet_id`) rather than killing the whole feed. The feed returns
the good rows; the operator sees their log instead of a blank
screen. Surface the real error server-side for diagnosis (not
swallowed). This belongs in brief 2 because manual entry is
exactly what creates hand-made rows that could trip
serialisation — it is the natural home for the guard.

### §5.5 — The manual-entry screen (frontend)

**Anchors.** `ui/web/src/App.tsx` (routes ~L52-57, nav links
~L27-39); existing routes `ui/web/src/routes/` (Racing,
Provisional, BetLog, Accounts, Health); existing live log-bet
component `ui/web/src/components/LogBetPanel.tsx` (the
near-time logging panel on the Racing screen — reference for
field shapes, NOT the surface to reuse).

**Build.** A new route + screen for after-the-fact entry — its
own surface, NOT a feature inside BetLog (the locked scope is
explicit: manual "Add Bet" is a bet-entry capability, it only
lived on v2's bet-log page by habit). Add a new nav tab
labelled **"Log Past Bet"** (LOCKED S175) with its own route.
The screen:

  - a **cascading picker** driven by §5.1: pick date -> pick
    venue (from the list the lookup returns) -> pick race
    number -> pick runner. No free-typed venue.
  - the bet metadata fields (account-at-book, side, stake(s),
    price, strategy tag, free-bet marker + conversion) — mirror
    the field set the hand-logged builder already expects.
  - the **settle-at-entry** control: won / lost / void.
  - on submit, POST to §5.2; on success, the bet is written
    settled and appears in BetLog.

Plain, functional, consistent with the existing screens'
styling (no new design system; there is no theme-token layer
yet — dark theme is parked, out of scope here).

### §5.6 — Write-path spot-check

**Build.** Confirm empirically that a manually-entered bet
writes and persists correctly and shows in BetLog: enter a
days-old bet end-to-end, confirm the row lands in the
operational store with its Betfair leg ids + settled state,
and confirm it renders in the BetLog feed. This closes the
S172 "does a never-matched / hand-made bet persist" question.
Capture the round-trip in the report.

---

## §6 — Sequencing within the session

Dependency order:

1. **§5.1 VPS race-lookup surface** first — everything
   downstream needs the resolved Betfair identity it returns.
   Build + test it in isolation against the live store (read-
   only) before wiring anything to it.
2. **§5.2 create endpoint** + **§5.3 settle-at-entry** next —
   the write path, consuming §5.1's output. Build together;
   settle-at-entry is a property of the create flow.
3. **§5.4 robustness guard** — independent of §5.1-§5.3; can
   land any time, but do it before §5.6 so the spot-check
   exercises the hardened feed.
4. **§5.5 frontend screen** — consumes §5.1 (picker) and §5.2
   (submit). After the backend is green.
5. **§5.6 write-path spot-check** last — exercises the whole
   chain end-to-end.

If a cleaner order emerges, Code may deviate and say so in the
report.

---

## §7 — Empirical verification

  - **Test baseline.** Capture `uv run pytest` counts (pass/
    fail) before and after; frontend `tsc -b` clean + vitest
    counts before and after. Zero regressions in the existing
    suites is the bar. New tests for the lookup surface, the
    create endpoint, settle-at-entry, and the robustness guard.
  - **Settlement seam untouched — prove it.** The
    live-settlement path (`workflows/bet_entry/v1/settlement.py`)
    and the placement path must be byte-identical where not in
    scope. Confirm via hash or diff that the auto-settlement
    code did not change (precedent: BetLog build proved the
    settlement/placement seam byte-identical).
  - **End-to-end round-trip (§5.6).** Log a real days-old race
    bet through the screen; confirm it persists settled with
    its Betfair leg ids and renders in BetLog.
  - **Lookup read-only proof.** Confirm the new `vps_client`
    surface issues only reads against `capture.db` (no
    INSERT/UPDATE/DELETE; no copy of the DB file).

---

## §8 — Output report spec

Single file: `interface_triage/manual_entry_build_report.md`.

Structure:
  - what was built, per §5 piece, with final file/line anchors;
  - the build decision from §5.2 (which builder path) named;
  - test baselines before/after (Python + frontend) + the
    settlement-seam-unchanged proof;
  - the §5.6 round-trip result;
  - any findings / surprises (incl. anything that did not fit);
  - dirty-tree status at close (§9) if the tree was dirty.

Rough length 300-500 lines (BetLog build report was ~568). Not
a hard cap — overshoot if detail is load-bearing, flag if so.
The report contains NO recommendations and NO next-brief — that
is the next operator-Claude session's job (§10).

---

## §9 — Hard limits (non-negotiable)

  - **No writes to `capture.db`.** `vps_client` stays
    read-only; §5.1 adds a read surface only. No INSERT/UPDATE/
    DELETE, no copy of the DB file.
  - **No change to live / near-time auto-settlement.**
    `settlement.py` and the auto-settle worker are untouched;
    prove it (§7).
  - **Not brief 3.** No free-bet credit-in build, no cycle-
    attribution surface, no "placed?" confirm wiring beyond the
    inert scaffold BetLog already carries.
  - **Not the audit log.** No bet-mutation audit log here (its
    own fenced brief, after this one).
  - **No schema migrations beyond what the create path needs.**
    The bet/leg schema already supports this (NOT-NULL Betfair
    ids, settlement-state field exist). New `EntryPath` enum
    value is a backward-compatible addition; flag if anything
    more is needed rather than expanding silently.
  - **Named anchors only.** Edit only the regions in §5. No
    drift into adjacent code "while we're here."
  - **Dirty-tree discipline (if the v3 tree is dirty):** read
    `git status` at start; no `git add/commit/stash/restore/
    checkout/reset`; after each edit `git diff <file>` to
    confirm only intended changes; at close `git status` to
    confirm the dirty-file list is unchanged bar the intended
    edits. If a dirty region intersects a §5 anchor, stop and
    surface it as a finding before editing.
  - **No mid-session operator escalation.** Findings go in the
    report; Code runs end-to-end.

---

## §10 — What happens after Code's session

The next operator-Claude (Chat) session reads
`manual_entry_build_report.md`, triages findings in plain
operational language, surfaces any operator calls, and routes
forward. Code does not write the next brief.

Expected forward sequence after this lands clean:
  - **bet-mutation audit log** — its own fenced brief
    (append-only, decoupled, never inside the bet-write
    transaction);
  - **brief 3 — free-bet credit-in** (the S168 design; its
    surface lands inside BetLog; depends on BetLog existing).
    **Carry-forward (LOCKED S175): brief 3 must wire its
    promo-trigger / free-bet-credit question to BOTH the live
    "Placed?" hook AND this brief's manual settle-at-entry
    screen** — one settlement-time question, both entry paths.
    Do not let the manual path be forgotten when brief 3 is
    drafted.
  - **launcher brief** (F9 in-memory back-off -> disk, F10 port
    override, rebuild-if-source-newer) — independent;
  - then **W16 cutover** scoping.

Separately on the roster (not this brief, not blocking
cutover): the Racing-API placings **backfill + nightly
results-sync fix** (recover Mar-Jun placings; stop the gap
reopening) — its own Code brief, carrying the DR-027/028
re-read trigger because it is a VPS-side write.

---

## §11 — Cross-references

  - **Scope:** `interface_triage/betlog_scope.md` (manual
    after-the-fact entry shape); §2.8 bet-schema
    "operator-picks-a-resulted-race-row" design.
  - **DRs:** DR-033 (data-source roles — Betfair settles,
    Racing API enriches; place refunds manual), DR-027/028
    (two-database boundary — `vps_client` read-only), DR-019
    (derived P&L on read), DR-032 (Betfair canonical
    reference), DR-021 (Adelaide timestamps).
  - **Contract:** `contracts/vps_client_contract.md` §9 (the
    six existing surfaces; §5.1 adds §9.7), §10.3
    (backward-compatible-addition rule).
  - **Prior sessions:** S169 (manual-entry shape locked), S171
    (BetLog built), S172 (robustness bug + write-path
    spot-check folded here; delete path proven safe), S173
    (retention ample), S174 (DR-033; settle-off-Betfair vs
    manual flag; placings gap is analytics-only).
  - **Excluded (parking-lot / other briefs):** free-bet
    credit-in (brief 3), bet-mutation audit log (own brief),
    dark theme (parked), launcher hardening (own brief),
    placings backfill + nightly-fix (own brief).
