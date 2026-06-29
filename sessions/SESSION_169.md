# Session 169

**Title:** Pre-cutover plan reshaped — BetLog scoped, the
free-bet work resequenced behind it, after-the-fact manual
entry surfaced as a real cutover need

**Opened:** 2026-06-20 08:24 ACST
**Closed:** 2026-06-20 09:31 ACST
**Tool routing:** Claude Chat only (planning, scoping,
read-only v2 + v3 source grounding, API-availability check).
No Code commission this session.
**Governing DRs:** DR-021 (timestamps), DR-022 (vocab),
DR-027/028 (two-DB boundary — relevant to the capture.db
read path for manual entry), DR-030 (module boundaries),
DR-032 (Betfair canonical / cycle axis), DR-019 (derived
pool balance). Plus the Session 70 free-bet pool lock as the
inherited design substrate.

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"`
  → `2026-06-20 08:24 ACST`
- Close: same command → `2026-06-20 09:31 ACST`

## Pre-flight checks (open ritual)

Drift-check clean: `current_state.md`, `SESSION_168.md`, and
`v3_build_picture.md` all stamped 2026-06-20 08:14 ACST
(S168 close). `.close_out_backups/` held only
`SESSION_169_opening_prompt.md` — no stale prior prompt. No
phantom files at root (`external_api_resources.md` +
`openapi.json` present and legitimate per standing
references). Same-workday open (S168 closed 08:14, S169
opened 08:24 — a ten-minute continuation).

## Session shape

A scoping session that opened to draft the Piece 0 + A
free-bet build brief and productively reshaped the whole
pre-cutover plan instead. The brief drafting got as far as
the locked design and one real operator call (where the
"placed?" confirm lives), which surfaced that v3 has **no
bet-viewing surface at all** — a settled-lost insurance
qualifier vanishes into the data. The operator's call:
build the **BetLog** properly before cutover rather than a
throwaway confirm-worklist, since he's cutting v3 over for
live operational use and must be able to see his book. No
brief was drafted or written this session; the free-bet
brief is **still pending** and now sequenced third.

From there the session: (a) walked v2's bet log to decide
what earns its place in v3; (b) locked the BetLog scope;
(c) surfaced after-the-fact manual bet entry as a separate
real cutover need; (d) ran a read-only API-availability
check that largely dissolved the operator's data-retention
worry. Net: a one-brief plan became a **three-brief
sequence** (BetLog → manual entry → free-bet credit-in),
launcher brief still pending.

**Governance event (structural-drift flag):** the
pre-cutover deliverable plan changed shape this session —
from "draft the Piece 0 + A free-bet brief" (the S168→S169
promoted primary) into a three-brief sequence with BetLog
inserted ahead of it. The free-bet design itself is
unchanged (S168 `free_bet_credit_in_design.md` still
holds); only its operator surface moved (into BetLog) and
its draft order moved (third). Carried forward in the S170
opening prompt.

## What was delivered

1. **BetLog scope — locked**, captured in
   `interface_triage/betlog_scope.md` (new, 87 lines). One
   page, pending + settled together, flat newest-first, no
   manual-settle console (v3 auto-settles + burst-review
   handles exceptions). Filters: account, account-at-book,
   book (recommended, operator to confirm), promo type, date
   range, Pending/Settled/All. Row = selection · side · Free
   marker · stake@odds · state · P&L · book+persona; detail
   (id, exact time, commission, full promo terms, cycle
   chain) tucks in on open. Edit + delete. The insurance
   "placed?" confirm lives here.

2. **v2 bet-log walk-through** — read `BetsPage.jsx`,
   `PendingSettlementTab.jsx` (827 lines — a manual
   settlement console), `SettledHistoryTab.jsx` (356 lines —
   the history/record). Confirmed v2 fuses "see bets" +
   "settle bets"; v3 only needs the former. v2's insurance
   "triggered? Yes/No" is the proven precedent for the v3
   "placed?" confirm.

3. **After-the-fact manual bet entry — surfaced + shaped.**
   A real cutover need (fire-first-log-later in bursts;
   sometimes days later). Shape locked: date → venue → race
   number → runner → link to the Betfair stamp. Treated as a
   separate bet-entry capability, not a BetLog feature
   (brief 2).

4. **API-availability check (read-only) — the finding.**
   Grounded against `external_api_resources.md`, the S39
   probe report, and the §2.8 bet-schema doc:
   - capture.db already holds resulted races with the
     Betfair Win market id + selection id + finish position —
     both picker fields and canonical stamp. **No new
     retention build on our side.**
   - Live Betfair API is only a short post-race window (S39
     probe: ~45 min closed-market readability, then ages
     out) — not a multi-day source.
   - The §2.8 work already designed the "pick a resulted-race
     row, lift its `betfair_market_id`" path.
   - Reading capture.db to fill the picker is the sanctioned
     DR-027/028 reference pattern (no copy).
   - Open: confirm capture.db's retention window (operator
     wants a couple of days) — the first step of brief 2.

5. **Auto-settle linkage confirmed structurally safe.** v3
   leg fields (`betfair_market_id`, `betfair_selection_id`)
   are NOT NULL; auto-settle reads them off the bet
   (`settlement.py:356-360`). A logged bet can never float
   free of its event. The operator's linkage worry cannot
   occur in v3.

6. **Pre-cutover sequence resequenced** — three briefs
   (BetLog → manual entry → free-bet credit-in) + the
   pending launcher brief. Captured in `betlog_scope.md` and
   `current_state.md`.

## Standing-instruction adherence check

- **Cat 1 (call-driven surfacing, brevity, decision-maker
  framing):** honoured. Led with the one decision at each
  turn (affordance placement → BetLog-vs-throwaway →
  row-vs-tuck-in → flat-vs-grouped → manual-entry need →
  retention source). "Deserves a little detail" flagged
  before the API-availability finding. Technical detail
  (schema, settlement anchors) led autonomously; only
  operator-territory calls surfaced.
- **Cat 2 (session protocol):** timestamps anchored open +
  close (DR-021). Session record written. Opening prompt
  generated without being asked. Structural-drift flagged
  (one-brief → three-brief resequence) per the close-out
  surfacing rule. Forward routing operator-confirmed.
- **Cat 3 (filesystem + skills):** Desktop Commander used
  exclusively; `bash_tool` not touched. `bethub-session-
  open`, `bethub-brief-drafting`, `bethub-session-close`
  skills each read before use. v2 + v3 source read read-only
  via `start_process`. Writes chunked + verified.
- **Cat 4 (cycle convention, API resources):** the free-bet
  cycle treated as a single unit throughout; reached for
  `external_api_resources.md` for the Betfair API check per
  the standing pointer.
- **Cat 5 (division of labour):** software/architecture
  calls made autonomously (BetLog = viewing surface, manual
  entry = separate bet-entry capability, capture.db as
  source); operational calls put to the operator (manual-
  entry need, lookback window). The "is this mine or Code's"
  routing call (the API check) made and named — Chat's, as a
  scoping read.
- **DR-027/028:** named as the boundary the capture.db read
  path crosses; confirmed the read-by-reference pattern is
  sanctioned, not a violation.
- **Google Drive auto-sync:** not prompted at close.

## Open items

Pointer-only — full detail in `current_state.md`.

**Promoted for Session 170:**
- **Draft the BetLog build brief** for Code, against
  `interface_triage/betlog_scope.md`. S170 primary.

**Carried:**
- **After-the-fact manual entry brief** (brief 2) — opens
  with the capture.db retention check.
- **Free-bet credit-in + cycle attribution brief** (brief 3)
  — S168 design unchanged; surface now lands in BetLog.
- **Launcher brief** (F9 throttle-to-disk + F10 port
  override, consider F12) — still pending, independent.
- Governance: whether to formalise the S168 credit-in design
  as a short DR or Session 70 amendment — operator's call,
  deferred.
- Parking-lot items (unchanged) — see `current_state.md`.

## Open items out

- **Piece 0 + A free-bet build brief as the S169 primary** —
  superseded by the resequence. Not dropped: it became
  brief 3 in the new sequence, design intact. The "draft it
  now" framing closed; "draft it third, after BetLog"
  replaces it. ✅
- **"Placed?" affordance home question** — resolved. It
  lives in BetLog, not a throwaway worklist. ✅
- **Manual-entry data-source / retention-window question** —
  resolved in approach (capture.db, read by reference; no
  new storage), with only the empirical retention number
  left for brief 2. ✅
- **Auto-settle event-linkage worry** — resolved
  (structurally guaranteed by NOT NULL leg ids). ✅

## Session close state

- Rebuild folder root: clean, no phantom files.
- `interface_triage/`: one new file this session
  (`betlog_scope.md`, 87 lines). S168's three files
  unchanged.
- `standing_instructions.md`: untouched this session (no new
  instructions surfaced). KB re-upload still pending
  operator-side (carried from S163 — unchanged).
- `v3_build_picture.md`: updated at this close (Interface
  refinement milestone moved — free-bet build → BetLog,
  with the three-brief sequence noted).
- `.close_out_backups/`: holds `SESSION_170_opening_
  prompt.md` after this close (S169 prompt removed).

## Forward routing

**S170 drafts the BetLog build brief** for Code, against
`interface_triage/betlog_scope.md`. Then brief 2 (manual
entry, opening with the capture.db retention check) and
brief 3 (free-bet credit-in, surface in BetLog). Launcher
brief remains pending. **Confirmed with operator** — the
operator directed "check api availability, record, then
close," explicitly endorsing the resequence and the close
here. No committed cutover date; ready beats rushed.
