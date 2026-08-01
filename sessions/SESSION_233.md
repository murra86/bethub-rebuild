# SESSION 233 — PROVING-WINDOW DAY 1 RAN LIVE: tick 2 (interlock drill) DONE, gate-3 rider CLOSED, 14 real promo bets logged/reconciled/settled to the cent, two-variant promo discovery, $250 bonus credited — and the soft-book settle door BUILT same day

**Opened:** 2026-07-08 10:00 ACST (fast-path — the headless runner had executed the S233 first action at 20:08 the prior evening: `b6_proving_window_guide.md` written + HELD).
**Closed:** 2026-07-08 ~14:05 ACST, Adelaide-anchored per DR-021. Session ran through the operator's live racing day (racing ~12:00–13:00) and its full close-out.
**Tool routing:** governance Claude Code session on the Mac (native tools). No out-of-session Code brief — the one build (settle door) landed in-session under S227 git autonomy. Store writes via supervised scratchpad scripts through the store adapter / designed write paths (`uv run`), plus the app's own credit-in endpoint.
**Bet-safety:** CLEAN — Claude placed no bets and initiated no Betfair contact. The two interlock-refused lay attempts were the OPERATOR's drill actions through the running app (refused pre-send by design — that was the point). Claude's external reads: VPS Racing API results queries (read-only, creds stayed on the VPS), capture API over the 8400 tunnel (read-only), app/audit logs. The v3 store WAS written — commissioned day-1 close-out work (promo re-points, settlements, credits), all backed up first (`bethub-20260708-preclose-day1.db`), read-back and derived-read verified.
**Governing DRs:** DR-021 (Adelaide anchors), DR-019 (money derives on read — settlements/credits verified via `compute_account_at_book_balance` / `compute_free_bet_inventory`), DR-022 (account/book/account-at-book vocabulary), DR-027/028 (two-database boundary — results read from the capture line + Racing API, never cached into the operational store).

---

## Anchor

- Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-07-08 10:00 ACST`
- Close: same command → `2026-07-08 13:59 ACST` (close-out continued past this anchor)

## Pre-flight

Drift-check clean at open: `current_state.md` 20:05 ≈ S232 close 20:03; `SESSION_232.md` present; fresh runner result (`SESSION_233_opening_prompt_result.md`, 20:13) → fast-path presentation. v3 at `18177e0`, tree clean.

## Session shape

One arc — **gate 9's first live day** — run interactively across the operator's racing day, with the close-out surfacing a promo-truth correction and one commissioned build. Morning: proving-window plan → interlock drill (tick 2). Midday: 14 promo bets narrated live and logged by the operator through the picker (gate-3 rider evidence accumulating bet by bet). Afternoon: results pulled, promo terms discovered wrong (two variants per account at the same book), store corrected end-to-end, all bets settled, bonuses credited, day signed off — and the gap that kept the day from being fully clean (no self-serve soft-book settlement) was built away the same afternoon.

## What was delivered (in order)

1. **Day-1 plan** delivered at operator request (timed steps: pre-racing checks, drill, during-racing watch-items, end-of-day close).
2. **Tick 2 — interlock drill PASSED (11:43–11:45).** Wi-Fi off → two operator lay attempts refused pre-send (`streaming_disconnected`, "Streaming connection unavailable; placement queue paused"), both stamped in `placement-audit.jsonl`, `elapsed_ms=0`, no Betfair contact; feed self-reconnected 0.4 s after Wi-Fi restored (one transient `SUBSCRIPTION_LIMIT_EXCEEDED` on reconnect, self-healed <1 s). Two cosmetic notes: the modal surfaced the refusal as raw "API 503" (parking lot: plain-language label); the health banner can't update while the Mac itself is offline (react-query pauses polling on `navigator.onLine=false`; 20 s `POLL_MS` catches the real feed-drop case — drill artefact, not a live gap).
3. **14 promo bets logged live** (Tim ×6, Sarie ×4, Leigh ×4, all TAB, 6 races at Sandown/Canterbury/Ipswich; two altered stakes $80/$77 on Canterbury R2 logged correctly at alteration). Mid-day balance questions answered from code+store: the picker balance = spendable cash (stakes deduct at logging — verified derivation matched screen exactly); one "missing bet" (Leigh) was a stale page, another (Leigh Ipswich R2) a stale BetLog — data right underneath both times.
4. **Results acquisition chain:** capture line had winner/loser immediately but no finishing positions (placings backfill lags); racenet/punters block server fetches; Chrome extension disconnected → **The Racing API `/v1/australia/meets` route queried from the VPS** (creds stay on-box, read-only) gave official top-3s for all six races.
5. **Promo truth established (operator-led):** TAB ran TWO variants of the run-2nd insurance across the same races — stake-back-in-bonus cap $50 (Tim, Sarie) vs winnings-as-bonus cap $100 (Leigh). Every actual credit fits exactly one variant; 2nd-only confirmed (two 3rd-place runners paid nothing). Actual credits $250: Tim $50+$50, Sarie $50, Leigh $100. (Claude's running tally initially mis-added to $240 — operator caught it.)
6. **Store corrected end-to-end (supervised, backed up, verified):** new catalogue template "Ins 2nd Winnings FB $100" (with an explicit engine-approximation note: credit engine computes stake×`return_pct`; `return_pct=2.0` is exact only at cap-hit — winnings-based credit support parked); all 14 bets re-pointed to the right variant + `strategy_tag=safety_net` via the designed edit path; 14 settlements via the designed settlement write (13 lost, Silent Thinker won +$125); 4 free-bet credits via the app's own credit-in endpoint (amounts computed right: $50/$50/$50/$100). Derived balances exact: Tim $1,192.20, Sarie $1,040.00, Leigh $990.20; FB inventory matches TAB account-for-account. **Operator confirmed all cash + bonus balances against TAB.**
7. **Settle-door build (operator-commissioned Option 1):** `POST /v1/bets/{bet_id}/settle` (won/lost/void; fenced soft-book-only + pending-only; Betfair 422s to the worker lane; terminal/provisional 409) + BetLog `Settle: Won/Lost/Void` buttons (confirm-gated, hidden for Betfair) + money-check visibility (each settle logs the exact line `ops.settlement_review` parses, `reason=operator_manual` — the check's blind spot to non-worker settlements closed for operator settles; regex pinned by test). Red-before proven (9 fail stashed → 9 pass). Suites **1399** backend (+9) / **134** frontend (+2), tsc clean. Dist rebuilt only after the operator confirmed the app was down (S232 lesson applied). Commit **`9de0609`** pushed; tree clean.
8. **Window log created** — `b6_proving_window_log.md` (tick table + day-1 record + operator sign-off verbatim). Day 1 signed off as NOT clean (tick 1 not counted — settlement needed Claude's scripts; promo terms wrong at logging), tick 2 DONE, gate-3 rider CLOSED, tick 3 open (needs a Betfair-lay day).

## Findings / calls of note

- **Promo terms differ per account at the same book** — the day's headline lesson; operator adopted the standing habit (capture terms as EACH account's betslip shows them before first staking a new promo). Standing-instructions Cat 4 entry added this close.
- **v2-on-5000 / v3-on-8787:** first credit-in POSTs went to port 5000 (v2, still system-of-record) and 404'd harmlessly — process note: verify the target app's port before hitting a local API.
- **Results-lag shape:** Betfair result stream answers won/lost fast; exact finishing positions need the Racing API (or patience). Matters for any position-paying promo.
- **Money-check lens gap (now narrowed):** `ops.settlement_review` dates settlements from worker log lines; script-side settlements were invisible to it. Operator settles now emit parseable lines; scripted settles remain out-of-lens (acceptable — scripting soft settles should now be rare).
- **Operator calls:** settle-door build (Option 1); don't chase TAB over the $100 variant-gap (account-hygiene); sign-off wording; day NOT counted as tick 1.
- **Claude calls (Cat 5):** correct-then-settle ordering (re-point templates while pending, settle, then credit); `return_pct=2.0` approximation with in-template warning note over an engine build; BET_SETTLED audit event type parked (closed CHECK contract needs migration — router comment records it); log-line reuse over a new review parser; stray `bethub (1).db-wal` moved to `~/.bethub/backups/` (not deleted).
- **Incident (owned):** Claude's bonus tally said $240 twice; actual $250. Arithmetic slip, caught by the operator; store was correct throughout.

## Standing-instruction adherence check

- **DR-021** all anchors Adelaide ✅. **Cat 1** fast-path open; baby-steps through the live day (one bet/one result per round); tight hand-offs ✅. **Cat 2** first-action gate: S234 session content stated explicitly by the operator at close ("placing free bets using the tool (BetFair modal), converting the bonus bets"); runner first action derived as drafting-only prep + HOLD ✅. **Cat 3** empirical verification throughout (balance question answered from live code+store; promo theory tested against every credit; red-before on the build; every store write read-back + derived-read verified; backup before writes) ✅; scratchpad + `uv run` scripts ✅; git autonomy within guardrails (green tree, descriptive message, push, reported) ✅; **dist rebuilt only with the app confirmed down** — S232's lesson honoured ✅. **Cat 4** live-integration classification kept honest: day 1 NOT ticked clean despite exact reconciliation, because settlement wasn't self-serve; settle door is *implemented-not-live* until first real use ✅. **Cat 5** software calls made and reported plainly ✅.

## Open items

**Closed in S233:** tick 2 (interlock drill); gate-3 rider; day-1 promo/settlement/credit corrections; soft-book settle gap (built — first live use pending); money-check operator-settle visibility; S232 stale `bethub (1).db-wal` phantom.

**New/updated parking-lot:** modal shows raw "API 503" on interlock refusal (plain-language label); pages don't refetch after bet logging (stale-page niggle, bit twice); winnings-based credit-in support (engine computes stake×pct only); BET_SETTLED mutation-audit event type (schema migration); health-banner offline-poll note (cosmetic, documented).

**Carried:** B3 residual R1 (MEDIUM) — watch at the first live partial match, **live opportunity next session** (Betfair lays for FB conversion); the rest of the parking lot per `current_state.md`.

## Session close state

bethub-v3: HEAD **`9de0609`** = origin/main, tree clean, suites **1399 / 134** green, tsc clean, dist rebuilt and consistent (app down). Store: 14 bets settled (13 lost / 1 won), 4 finalised free-bet credits ($250), 10 promo templates (1 new), all balances derived exact and operator-confirmed against TAB. Backups: launch backups + `bethub-20260708-preclose-day1.db` (+ the moved stray WAL). App CLOSED at session end (operator-confirmed before dist rebuild). Rebuild root: `b6_proving_window_log.md` NEW (tick table + day-1 signed record); `b6_proving_window_guide.md` unchanged (runner artefact, presented). No phantom files.

## Forward routing

**S234 session content (operator-stated at close):** placing the $250 of free bets through the tool — TAB free-bet backs logged via the picker (FB draw-down from inventory) paired with **Betfair lays via the HedgeModal** to convert the bonuses to cash. Live-proof surfaces in play: free-bet modal flow first use; first Betfair lays since S228 (→ **tick 3** opportunity when the settlement worker stamps a real lay); first fully-self-serve day (**tick 1** opportunity — settle buttons' first live use for any TAB legs); **R1 (MEDIUM) partial-match watch-item** — lays may partially fill; the park valve should catch anything odd.

**S234 first action (runner, derived — drafting only, then HOLD):** draft a short plain-language prep for the free-bet conversion day — how a free-bet back gets logged (inventory draw-down, conversion maths), the lay pairing through the modal and what the interlock/park valve means for it, the R1 partial-match watch, what settles automatically (Betfair) vs via the new settle buttons (TAB), and how the day's end-of-day check + sign-off should look. Read-only; nothing auto-executes beyond the draft.
