# Manual entry build report — Brief 2 (v3 build)

**Session:** single bounded Claude Code session, 2026-06-23 (Adelaide
local, ACST). Start ~13:0x ACST, close ~13:13 ACST.
**Brief:** `interface_triage/manual_entry_build_brief.md` (LOCKED S175).
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3` @ `main` (HEAD
`2329604`).
**Outcome:** all six §5 pieces built, tested green, end-to-end
round-trip confirmed. Zero regressions. Settlement seam proven
byte-identical. No work deferred for non-fit reasons.

This report records what was found and done. It contains no
recommendations and names no next brief (per §8 / §10) — findings route
to the next operator-Claude triage session.

---

## §1 — Summary of what was built

Six pieces, built in §6 dependency order:

| # | Piece | Status | Primary anchor |
|---|---|---|---|
| §5.1 | VPS race-lookup surface + contract §9.7 | ✅ | `clients/vps_client/v1/race_lookup.py` (new) |
| §5.2 | "create bet" POST endpoint | ✅ | `ui/api/routers/bets.py` |
| §5.3 | settle-at-entry | ✅ | record_builder + create endpoint |
| §5.4 | bets-feed robustness guard | ✅ | `ui/api/routers/bets.py` → `list_bets_feed` |
| §5.5 | "Log Past Bet" frontend screen | ✅ | `ui/web/src/routes/LogPastBet.tsx` (new) |
| §5.6 | write-path spot-check | ✅ | round-trip test (below) |

No deviation from the §6 sequence was needed.

---

## §2 — Test baselines (before / after)

### Python (`uv run pytest`)

- **Before:** `1092 passed, 4 warnings` (6.47s).
- **After:** `1128 passed, 4 warnings` (5.99s).
- **Delta:** +36 tests, all new and passing; **0 failures, 0
  regressions**. The 4 warnings are pre-existing (`HTTP_422_*`
  deprecation in `ui/api/routers/__init__.py`, plus an anyio
  deprecation) — not introduced here.

New Python tests (36):
- `tests/clients/vps_client/v1/test_race_lookup.py` — 11 (picker
  surfaces + read-only proof).
- `tests/ui/api/test_bets_manual_create.py` — 15 (create endpoint,
  settle-at-entry, failure modes, lookup HTTP bridge, §5.6 round-trip).
- `tests/workflows/bet_entry/v1/test_record_builder_manual.py` — 9
  (sibling builder unit tests).
- `tests/ui/api/test_bets_robustness.py` — 1 (§5.4 guard).

### Frontend (`tsc -b` / `vitest`)

- **Before:** `tsc -b` clean (exit 0); vitest `15 files / 99 tests`.
- **After:** `tsc -b` clean (exit 0); vitest `16 files / 103 tests`.
- **Delta:** +1 file (`LogPastBet.test.tsx`), +4 tests, all passing;
  **0 regressions**. (Note: the BetHub memory line about "2 pre-existing
  vitest failures" refers to a *different* project — this v3 suite was
  fully green before and after.)

### Settlement seam — proven unchanged (§7)

`workflows/bet_entry/v1/settlement.py` SHA-256, before **and** after the
session:

```
9e07a75d3ab85741d5c3346521dbca25d09da632bd1140fcdb6550e55840d4a3
```

Byte-identical. The auto-settle worker lives entirely inside
`settlement.py` (a repo-wide grep for `auto.settle` /
`settlement_worker` / `run_settlement` / `settle_pending` /
`SettlementWorker` matches only that file), so this single hash covers
the whole auto-settlement path. `clients/betfair_client/v1/placement.py`
also unchanged (`fad6c280…`). Live / near-time settlement was not
touched.

### Read-only proof — capture.db (§7)

The §9.7 surface reads `capture.db` exclusively through the shared
`open_connection()` helper, which opens the SQLite engine with
`mode=ro&uri=true` (`clients/vps_client/v1/_connection.py:44`) — writes
are structurally impossible on that connection. Proven two ways in
`test_race_lookup.py`:
- `test_surface_is_read_only_connection` — an `INSERT` issued on the
  read-only connection raises `OperationalError`.
- `test_no_write_sql_in_source` — the module source contains no
  `insert`/`update`/`delete` SQL and no `shutil`/`copyfile` (no copy of
  the DB file).

### Architecture contracts (`uv run lint-imports`)

`5 kept, 0 broken`. The new `ui → clients.vps_client` and
`ui → workflows.bet_entry` imports on the bets router sit within the
existing DR-030 layering (the router already imported `workflows.balances`
and `clients.betfair_client` via `racing.py`).

---

## §3 — What was built, per piece (final anchors)

### §5.1 — VPS race-lookup surface (`§9.7`)

**New module:** `clients/vps_client/v1/race_lookup.py`. Exported via
`clients/vps_client/v1/__init__.py` alongside the existing six surfaces.
Three reads, all returning the standard typed envelope
(`fresh`/`unavailable`):

- `list_meetings(race_date)` (`race_lookup.py:222`) — venues that ran on
  a date.
- `list_races(race_date, venue)` (`race_lookup.py:259`) — races (number +
  jump time + code + win market id) for a date+venue.
- `resolve_race(race_date, venue, race_number)` (`race_lookup.py:297`) —
  resolves to `event_id` + Win `market_id` + runner set
  (`ResolvedRace`, `race_lookup.py:114`; each `ResolvedRunner` carries
  selection_id / name / barrier / scratched).

**Venue-matching discipline:** the picker is driven from the store's own
values (each step lists what the store holds; the operator selects).
Date matched via SQLite `date(race_date) = date(:race_date)` (robust to
both `YYYY-MM-DD` and ISO-datetime storage); venue matched **exactly**
(`venue = :venue`). No fuzzy matching — a `morphettville` (lower-case)
query against a stored `Morphettville` returns `genuine_absence`, tested.

**Contract update:** appended `§9.7` to
`contracts/vps_client_contract.md` in the same per-surface format as
§9.1–§9.6, plus a dated `§6` version-history line (2026-06-23, "Brief 2
Code (manual entry)"). Backward-compatible addition per §10.3 — no
version bump.

### §5.2 — "create bet" POST endpoint

**Anchor:** `ui/api/routers/bets.py`.
- `POST /api/v1/bets` → `create_manual_bet_endpoint`
  (`bets.py:742`), `status_code=201`, `response_model=BetFeedItem`.
- Request model `ManualBetCreateRequest` (`bets.py:218`,
  `extra="forbid"`).
- DI provider `get_capture_db_path` (`bets.py:83`) — reads
  `BETHUB_CAPTURE_DB_PATH`; test-overridable. Defined **inside the
  named anchor** (not `racing.py`) to keep the edit within §5.2's file.

**Flow:** the endpoint **re-resolves the canonical Betfair stamp
server-side** via §9.7 (`resolve_race`) rather than trusting
client-supplied canonical fields. It then (a) cross-checks the client's
`betfair_win_market_id` against the re-resolve (409 on mismatch —
defends a stale picker), (b) confirms the chosen `selection_id` is in the
resolved runner set (404 if not), (c) builds the leg Set-B snapshot from
the store-authoritative data, (d) builds the settled record, (e)
persists via the **shared** adapter + write path, (f) reads back and
renders the `BetFeedItem`.

**Lookup HTTP bridge (necessary addition — see Findings F1):** three
GET endpoints in the same anchor expose §9.7 to the browser, driving the
§5.5 picker — `lookup_meetings_endpoint` (`bets.py:664`),
`lookup_races_endpoint` (`bets.py:677`), `lookup_race_endpoint`
(`bets.py:691`).

**Build decision (§5.2 — named, as required):** I chose **option (b),
a sibling `build_manual_bet_record`**, over option (a) extending
`build_soft_book_bet_record`. Rationale:
- `build_soft_book_bet_record` hard-codes the record without a
  settlement state and `SoftBookRecordInputs` lacks both a `side` field
  and a settlement field — the two things the manual payload adds (brief
  §5.2 lists `side` back/lay; §5.3 the terminal outcome). Extending it
  would mean threading new params through a function the orchestrator
  calls on every soft-book log.
- The sibling leaves the orchestrator's heavily-exercised soft-book
  builder **byte-unchanged** (lower regression risk against 1092
  existing tests) while still honouring "reuse the existing write path,
  do not invent a parallel one": the manual builder reuses the shared
  validators (`_validate_strategy_tag`, `_validate_free_bet_invariants`,
  `_resolve_id`), the same `LegSnapshot` / `BetLeg` / `BetRecord`
  shapes, the same `bet_store_adapter.to_rows`, and the same
  `SQLiteBetRecordStorage.write_bet_record` INSERT path. The *record
  assembly* is a sibling; the *write path* is shared.

`ManualBetRecordInputs` (`record_builder.py:422`) /
`build_manual_bet_record` (`record_builder.py:498`).

### §5.3 — settle-at-entry

The create flow sets `settlement_state` directly to the operator-chosen
terminal outcome (`SETTLED_WON` / `SETTLED_LOST` / `VOIDED`) at write
time. `build_manual_bet_record` validates the state is terminal and
raises `BetRecordBuilderError` (→ 422) on `PENDING`/`PROVISIONAL`; the
request model's `Literal["settled_won","settled_lost","voided"]` also
rejects non-terminal values at the schema layer (422). P&L is derived on
read (DR-019) — nothing stored. Verified: won (back, 20 @ 3.0) → +40;
lost → −20; void → 0 (commission is a lay-only deduction in the existing
derivation, so a won back bet carries no commission haircut — see F4).

The live / near-time path is untouched: a bet logged at/near race-time
still enters `PENDING` and auto-settles off Betfair exactly as built. No
edit to `settlement.py` or the auto-settle worker.

### §5.4 — bets-feed robustness guard

**Anchor:** `ui/api/routers/bets.py` → `list_bets_feed`
(`bets.py:451`), the `for row, legs in rows` loop. The page-as-a-unit
list comprehension was replaced with a per-row `try/except` around
`_to_feed_item` (`bets.py:357`): one malformed row is **skipped and
flagged** — `logger.exception(...)` with the real server-side error and
the offending `bet_id` — and the good rows still render. `total` is left
unadjusted (it reflects DB matches, not successful serialisations; the
skip is surfaced in the log, not by silently shrinking the count). Test
induces a row-level failure and asserts the feed returns 200 with the
good rows and an ERROR log naming the poison `bet_id`.

### §5.5 — "Log Past Bet" screen

**New route + nav tab** (not a feature inside BetLog — its own surface,
per locked scope). `ui/web/src/App.tsx`: nav link **"Log Past Bet"**
(LOCKED S175 label) + `Route path="/log-past-bet"`. Component
`ui/web/src/routes/LogPastBet.tsx` + `.module.css`:
- A three-step **cascading picker** driven by §5.1 via TanStack Query
  (each step enabled only once the prior is chosen; choosing an upstream
  value resets downstream): date → venue (from the lookup list) → race →
  runner. No free-typed venue. Scratched runners and market-less races
  are disabled options.
- Bet metadata mirroring the hand-logged field set (account → book via
  `fetchAccountListing`, side, stake, price, strategy tag, free-bet
  marker + conversion).
- A **won / lost / void** settle-at-entry toggle.
- On submit, `POST` to §5.2; on success the bet is written settled and
  the success line shows the new `bet_id` + state. Plain, light-theme
  styling consistent with the existing screens. `LogBetPanel.tsx` was
  referenced for field shapes only — not reused.

**API client:** `ui/web/src/api/bets.ts` gained the lookup + create
functions and types (`fetchMeetings`, `fetchRaces`, `resolveRace`,
`createManualBet`; `MeetingSummary` / `RaceSummary` / `ResolvedRace` /
`ManualBetCreateRequest`).

### §5.6 — write-path spot-check (round-trip)

`test_create_persists_settled_and_appears_in_feed` enters a days-old
bet end-to-end through the real router over a real on-disk SQLite store
(plus a real capture-db fixture for the §9.7 re-resolve):

1. `POST /api/v1/bets` for Morphettville R5 on 2026-06-20, runner
   "Adelaide Flyer", won @ 3.0 — logged on 2026-06-20 (two days after the
   simulated race), Adelaide-local `placed_at`.
2. **201**; the row persists with `settlement_state=settled_won`, its
   Betfair leg ids (`betfair_market_id=1.111111111`,
   `betfair_selection_id=50001`), venue, and derived P&L +40.
3. `GET /api/v1/bets` then returns it (`total=1`, the created `bet_id`,
   `settled_won`) — i.e. it renders in the BetLog feed.

This closes the S172 "does a never-matched / hand-made bet persist and
show" question for the manual path.

---

## §4 — Findings / surprises

**F1 — Lookup needed an HTTP bridge (in-anchor addition).** §5.1 is a
Python `vps_client` surface; the browser cannot call it directly, yet
§5.5 requires the picker be "driven by §5.1". Bridging them needs HTTP.
I added three thin GET endpoints (`/api/v1/bets/lookup/{meetings,races,
race}`) **inside the §5.2 anchor** (`ui/api/routers/bets.py`), the
router that already owns the manual-entry create flow — keeping the
edit within a named anchor rather than spinning up a new router file.
Terminal "no data" reasons (absence / outside-window) render as an empty
list (picker shows "pick again"); transient transport failures surface
503. Flagged because it is an addition beyond the literal "one POST
endpoint" wording of §5.2, made because the picker cannot exist without
it.

**F2 — `EntryPath.MANUAL_LOG` already existed.** Brief §5.2 says to "add
a new `EntryPath` enum value for after-the-fact manual entry (backward-
compatible enum addition)". It was already present and reserved in
`domain/bets/__init__.py` (`MANUAL_LOG = "manual_log"`, alongside
`SPORTS_SCREEN` / `FREE_BET_LEDGER`). No enum addition was needed; the
manual builder reuses it. No edit to `domain/bets/__init__.py` resulted.

**F3 — `SettlementState` + `BetRecord.settlement_state` already
supported settle-at-entry; no domain or schema change.** The §5.3 anchor
(`SettlementState`) already carried `SETTLED_WON` / `SETTLED_LOST` /
`VOIDED`, `BetRecord.settlement_state` already existed (Optional), and
`bet_store_adapter.to_rows` + `write_bet_record` already persisted it
(plus `side` / `commission`). So §5.3 was a pure *usage* of existing
types — **no edit to `domain/bets/__init__.py`, no edit to
`store/repositories/bets.py`, no migration.** (The `BetRecord.
settlement_state` docstring notes "the orchestrator populates at
write-time in W7"; the manual path now also populates it at write-time,
which is in scope here and consistent with that field's intent.)

**F4 — Commission is a lay-only deduction in the read-side P&L.** In
`workflows/balances/v1/balance_derivation.py`, the 8% commission
fallback applies only on the Betfair-lay branch; a won **back** bet's
cash return is `matched_stake × price` with no commission haircut (net
P&L = winnings). This is the existing, deliberate v3 behaviour — noted
only because a manual back bet's P&L therefore shows the gross winnings
(e.g. 20 @ 3.0 won → +40, not +36.80). Not changed.

**F5 — capture.db has no Betfair `event_id`; `event_id == win_market_id`.**
As the existing §9.1/§9.2 surfaces document (W1 Finding F1), `capture.db`
keys races on `races.betfair_win_market_id`, not a Betfair `event_id`.
The §9.7 surface follows the same convention: `ResolvedRace.event_id`
and `ResolvedRace.win_market_id` carry the same value. Downstream this is
harmless — the leg stamp needs the Win `market_id` + `selection_id`, and
both are present.

**F6 — Retention window: §9.7 uses the siblings' 365-day cap.** The
brief notes retention is ample (~15.5 months). The existing
`vps_client` surfaces classify dates older than `CAPTURE_WINDOW_DAYS =
365` as `NOT_IN_CAPTURE_WINDOW`; §9.7 keeps the same 365-day constant
for consistency rather than introducing a second threshold. This
comfortably covers the "couple of days late" use case and does not
contradict the ~15.5-month physical retention. Noted, not changed (a
threshold change would be a cross-surface decision, out of scope here).

**F7 — Leg role for a manual bet is derived from `book_or_exchange`.**
A standalone manual bet is a single leg; the builder sets
`leg_role=HEDGE` when `book_or_exchange == "betfair"` else `SOFT_BOOK`.
This is cosmetic for settlement (which keys off the leg's Betfair ids
regardless of role) but keeps the role honest in BetLog. Named as a
small implementation choice within §5.2's latitude.

**Nothing was dropped for non-fit.** The session completed all six
pieces with budget to spare; there is no partial work to carry.

---

## §5 — Dirty-tree status at close (§9)

The v3 working tree was dirty at start and remains dirty — as the brief
anticipated. Per the operator's pre-edit decision ("proceed — expected
substrate"), I applied the operational dirty-tree discipline throughout:
read `git status` at start; **no** `git add`/`commit`/`stash`/`restore`/
`checkout`/`reset`; `git diff <file>` after edits to tracked files; and
`git status` at close.

**Tracked-file change set, start vs close:** grew by **exactly one
file** — `clients/vps_client/v1/__init__.py` — which is my intended
§5.1 export addition (verified: the diff is only the new
`race_lookup` imports + `__all__` entries, nothing else). All other
tracked-modified files (`.importlinter`, the seven `betfair_client/v1/*`
files, `domain/bets/__init__.py`, `pyproject.toml`, `store/__init__.py`,
three betfair test files, `tests/conftest.py`, `uv.lock`) were already
dirty at session start from in-flight betfair_client work and were **not
touched** by me — their diffs are byte-identical to session start.

**The one dirty §5 anchor was navigated around, not edited.**
`domain/bets/__init__.py` (the §5.3 `SettlementState` anchor) was dirty
at start (an empty→full authoring of the whole domain module). Because
its enum values and the `BetRecord.settlement_state` field already
existed (F2/F3), I did not need to edit it — and did not. Its close-state
diff is the same 383-insertion authoring as at start, with no
contribution from this session. So no dirty region intersecting a §5
anchor was disturbed.

**New files I added** live inside already-untracked directories
(`ui/`, `tests/ui/`, `tests/workflows/`) so they appear under those
directory entries in `git status`, plus two that appear individually
because their parent dirs are tracked:
- `clients/vps_client/v1/race_lookup.py`
- `tests/clients/vps_client/v1/test_race_lookup.py`
- `ui/api/routers/bets.py` (edited — untracked dir)
- `workflows/bet_entry/v1/record_builder.py` (edited — untracked dir)
- `ui/web/src/routes/LogPastBet.tsx` + `.module.css` + `.test.tsx`
- `ui/web/src/App.tsx`, `ui/web/src/api/bets.ts` (edited)
- `contracts/vps_client_contract.md` (edited — untracked)
- `tests/ui/api/test_bets_manual_create.py`,
  `tests/ui/api/test_bets_robustness.py`,
  `tests/workflows/bet_entry/v1/test_record_builder_manual.py`

No `capture.db` file was written or copied at any point.

---

## §6 — Files touched (complete list)

**Production (edited / new):**
- `clients/vps_client/v1/race_lookup.py` — **new** (§5.1 surface).
- `clients/vps_client/v1/__init__.py` — edited (export §9.7).
- `contracts/vps_client_contract.md` — edited (§9.7 + §6 history line).
- `workflows/bet_entry/v1/record_builder.py` — edited (sibling builder
  §5.2/§5.3).
- `ui/api/routers/bets.py` — edited (create POST + lookup GETs + §5.4
  guard + capture-db DI).
- `ui/web/src/api/bets.ts` — edited (lookup + create client).
- `ui/web/src/routes/LogPastBet.tsx` + `LogPastBet.module.css` —
  **new** (§5.5 screen).
- `ui/web/src/App.tsx` — edited (nav tab + route).

**Tests (new):**
- `tests/clients/vps_client/v1/test_race_lookup.py`
- `tests/ui/api/test_bets_manual_create.py`
- `tests/ui/api/test_bets_robustness.py`
- `tests/workflows/bet_entry/v1/test_record_builder_manual.py`
- `ui/web/src/routes/LogPastBet.test.tsx`

**Deliberately NOT touched:** `workflows/bet_entry/v1/settlement.py`
(seam, hash-proven), the auto-settle worker (inside settlement.py),
`clients/betfair_client/v1/placement.py`, `domain/bets/__init__.py`,
`store/repositories/bets.py` (no migration needed). No promo/refund flag
added (brief 3). No audit log (own brief).
