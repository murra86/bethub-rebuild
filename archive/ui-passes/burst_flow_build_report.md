# Burst-flow redesign — build report (Session 237)

**Built:** 2026-07-09 evening ACST, unattended runner session (operator-confirmed AUTO action from S236 close).
**Design source:** `burst_flow_mock.html` (locked S236) — §1 selection stack + §2 single-pass ⚡ lay→back.
**Repo:** bethub-v3 `7885535` → **`402e5bd`** (one commit, pushed to origin/main, tree clean).
**Suites:** backend **1441 passed** (unchanged — no backend edits); frontend **170 → 183 passed** (+13). `npm run build` green; dist rebuilt with the app confirmed down (only v2 was running).
**Fences held:** `place_lay` and everything under it untouched (the modal's placement call is byte-identical); reconciliation, settlement, credit-engine maths untouched. §2 composes the existing lay door and the existing log-bet door only. No new backend surface (DR-030 respected — the stack reads existing endpoints).

---

## Piece 1 — §1 selection stack (TopBar)

**Outcome: built as mocked.** The person/book dropdowns are gone; the top bar now stacks three rows — person chips, book chips, then the promo rail (unchanged: four primaries + other-promo dropdown + Free bet / No promo / + new, with the dials and FB source panel below as before).

What the chips do:

- **Person row** — one tap arms, re-tap clears. Switching person keeps the armed book when that person also has it (the S236 pairing-persistence rule), otherwise the book clears.
- **Book row** — shows the armed person's registered books; with no person armed it shows every registered book (either-order carried over). Each chip carries the **cash balance underneath**, read from the same log-context endpoint (and cache) the free-bet panel already uses — so "can I even bet here" is answered at a glance. **$0 books fade but stay tappable** (a deposit or bonus can land mid-burst). With no person armed, no balances show (there's no single registration to read them from).
- **Order: most active first, frozen for the day.** The order derives from the bet feed (newest bet's book ranks first; never-used books keep their listing order after) and is computed once per Adelaide calendar day — the day key sits in the cached query key, so chips never reshuffle mid-session. Muscle memory beats perfect ordering at burst pace, per the mock's footnote. Derive-on-read per DR-019 — nothing stored.

**Design calls made (dev territory, no operational consequence):**
- "ACTIVE books" = the registrations the accounts listing returns (same set the old dropdown showed). The listing carries no separate active/inactive flag today; if one arrives later the filter is one line.
- Row label reads "«Name»'s books · most active first, set for the day" so the ordering rule is self-describing on screen.
- Balance fan-out is one small read per registration of the armed person (~5 requests, 30s cache, shared with the FB panel's cache) — no new endpoint, no bulk read added.

## Piece 2 — §2 single-pass ⚡ lay→back (HedgeModal + Racing)

**Outcome: built as mocked.** On a successful lay placement the modal no longer flashes-and-closes (the old 1.5s auto-close is retired); the same box **becomes the back-log card**:

- **Lay result line stays on top** — matched-in-full or partial with the held-still figures from the placement response, exactly as before.
- **Person/book chips arrive preselected** from the armed top-bar context; if the bar isn't armed, from the last logged back this session. Both remain one-tap changeable, with the same pairing rule.
- **Stake prefills from the FB face value** typed for the lay sizing (blank in cash mode per the S210 rule — the operator types the real stake); **odds prefill from the typed soft price**. The usual case is zero-to-two taps then Log.
- **"Log the back"** submits through the **existing log-bet door** (`postLogBet`) with the same payload the confirm card sends: `safety_net` auto-tag when the armed promo is insurance-shaped, free-bet + consumed-credit semantics from the armed FB source, the promo serial, the EV/price snapshot for this runner (same derivation the confirm card stamps, now shared code), an idempotency key, and **no `cycle_id`** — grouping stays derived, per the demotion direction.
- **"skip — log it later"** closes without logging — never blocked. A skipped back still shows as the board's ⚠ unpaired-lay flag and lands in Burst review, unchanged.
- A free-bet back with **no armed source** logs as source-pending (the B3 spend-now-file-later shape) and the card says so — it does not block, unlike the confirm card, because mid-burst the face value was typed in the modal itself. This closes the exact gap that cost the $50 free-bet miss on S236 morning.

**Design calls made:**
- On a logged back the modal closes itself and the race-page confirmation toast carries the summary (same voice as the confirm card's).
- The "last logged back" memory updates from both doors (confirm card and this card) and lives for the session only — it's a preselection nicety, not stored state.
- Hardened the liability-cap read against a throwing/absent browser storage (private mode): the guard now falls back to the default $500 cap instead of erroring. The guard itself is unchanged and cannot be disabled.

## Folded in — plain wording for list-shaped 422s

FastAPI validation errors carry a *list* of details; the error mapper used to fall through them, so BetLog showed the raw "API 422 on PATCH …" line (the resolved bet-26eeb320 class — the stale-backend edit). Those now render as: *"The server refused the values sent: account_at_book_id — Extra inputs are not permitted"* — field by field, plain words. Applies everywhere the shared error mapper is used, not just BetLog.

## Tests

- **TopBar** 11 tests (was 8): chip arming/clearing, balances on chips with $0 dim-but-tappable, feed-recency ordering, pairing persistence across person switches; existing rail/FB/new-promo tests reworked to chip taps.
- **HedgeModal** 17 tests (was 12): the transform (preselected chips, FB-face stake, soft-price odds), the log-the-back payload (no cycle_id, safety_net, consumed credits, EV snapshot), skip-never-logs, source-pending note, cash-blank stake. All 12 pre-existing placement/guard tests still pass — placement behaviour untouched.
- **Racing.flow** 4 tests (was 2): full single-pass end-to-end through the race page (arm bar → ⚡ → place → card preselected → log through the door → toast), and the skip path.
- **errors** +3 tests for the 422 list shape.
- Suite totals: frontend 183 (from 170), backend 1441 (untouched, run green before commit).

## Findings for triage (none block use)

1. **Pre-existing, surfaced by the flow test:** with an insurance→bonus promo armed, ⚡ opens the modal in *free-bet* mode (it keys off the promo's return type). For the S1 cash back that means one extra tap to "cash" before placing. Existing S236 behaviour, not changed under the no-scope-creep rule — worth an operator call on whether insurance-armed should default the modal to cash.
2. Frontend lint has 12 longstanding warnings/errors (fast-refresh export style, setState-in-effect patterns) — unchanged from baseline; lint is not the gate. Left alone.
3. The one-per-day book order resets if the app restarts mid-day (the cache is in-memory). First read after a restart re-derives from the feed — order may differ slightly from the morning's if bets were placed meanwhile. Acceptable per the mock's intent; noted for honesty.

## Live-look checklist (next racing day)

Implemented-not-live until then, per the S189 classification. After **restarting the app** (the running instance predates 5 commits: the 4 from S236 close plus this build):

1. Top bar shows person chips, then book chips with balances; the armed person's most-used book sits first and the order doesn't shuffle during the day.
2. A $0 book chip looks faded but still arms on tap.
3. ⚡ on a runner → place a small lay → the box becomes the back log with person/book already selected, stake/odds prefilled; **Log the back** lands the bet in BetLog with the right promo/tag; the toast confirms.
4. Place a lay and hit **skip** — the board shows the ⚠ unpaired-lay flag as before.
5. Force a 422 (e.g. an edit the server refuses) — the message reads as plain field wording, not "API 422 on…".

Operator triages at next open; the runner stops here.
