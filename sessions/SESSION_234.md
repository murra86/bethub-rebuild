# SESSION 234 — FREE-BET CONVERSION DAY RAN LIVE: TICK 3 BANKED (five automatic worker settlements), R1 PARTIAL MATCH SEEN LIVE AND HANDLED, $162.53 cash extracted from $210 of bonuses — and the day's frictions produced an operator-locked UI/flow redesign direction

**Opened:** 2026-07-08 16:26 ACST (fast-path — the headless runner executed the S234 first action at 14:04: `b6_fb_conversion_day_prep.md` written + HELD).
**Closed:** 2026-07-08 19:57 ACST, Adelaide-anchored per DR-021.
**Tool routing:** governance Claude Code session on the Mac (native tools). No out-of-session Code brief. Store writes were supervised corrections through designed doors wherever one existed (PATCH edit endpoint, credit-in endpoint, `record_free_bet_deployment` via `uv run` script) and guarded single-row SQL where none existed (promo re-point, cycle joins, duplicate delete, cash-event removal) — every write batch backed up first, read-back + derived-read verified.
**Bet-safety:** CLEAN — Claude placed no bets and initiated no Betfair contact. All lays were the operator's, through the app's HedgeModal (interlock live, stream subscribed). Claude's external surface: the app's own local API (read + designed writes), the live store (supervised corrections, backed up), app/audit logs. Settlement of Betfair legs was the WORKER's (that was the point — tick 3).
**Governing DRs:** DR-021 (Adelaide anchors), DR-019 (money derives on read — every correction verified via `log-context`/derived balances), DR-022 (account/book/account-at-book vocabulary), DR-027/028 (two-database boundary — race-lookup reads via the capture bridge, nothing cached into the operational store).

---

## Anchor

- Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-07-08 16:26 ACST`
- Close: same command → `2026-07-08 19:57 ACST`

## Pre-flight

Fast-path open (fresh runner result 14:11 > S233 close 14:05). Pre-bet verification run at operator request before first stake: app healthy on 8787 serving the `9de0609` dist (served index.html md5 = disk), both workers running+healthy, stream `subscribed`, FB inventory exact ($250: Tim 2×$50 / Sarie $50 / Leigh $100), cash balances exact to the S233 sign-off, zero pending bets.

## Session shape

One arc — **gate 9 day 2, the conversion day** — run interactively across the operator's evening racing (~16:45–18:50), with Claude verifying every leg on the live read path as it landed, correcting promo/bookkeeping issues in-flight under supervision, and the close converting the day's frictions into an operator-locked redesign direction. The operator also ran an unplanned second strand: a Kate @ PointsBet insurance-qualifier session (10 bets), which surfaced most of the day's findings.

## What was delivered (in order)

1. **Pre-bet all-clear** (operator-requested): five live checks green before the first stake.
2. **Conversion 1 — Tim/Sesh (Belmont):** $50 FB back @ 9.0 won +$400; lay $38.39 @ 10.5 auto-settled −$364.71 by the worker (**first automatic real-lay settlement — tick 3 evidence opens**). Operator's first live Settle button press (Won) landed exactly (`reason=operator_manual` in the money-check lens). Net +$35.29 (70.6%).
3. **Conversion 2 — Tim/Bettors Hope (Bathurst):** **R1 (MEDIUM) partial match occurred live** — lay $42.84 filled $4.57 at placement; operator held per guidance; fill completed on Betfair; the recon sweep updated matched to full; worker auto-settled +$39.41. **R1's live look is banked: reconciliation handled partial→full correctly; the park valve was never needed.** Net +$39.41 (78.8%).
4. **Conversion 3 — Leigh/Exquisite Taste:** $100 FB back @ 17.0 lost; lay $86.86 @ 18.5 auto-settled +$79.91 (79.9% — best of day).
5. **Conversion 4 — Kate/Vermont (Redcliffe):** the in-day-earned $10 FB (see 7) converted: back lost, lay auto-settled +$7.92. **Five worker settlements total, all correct-money — tick 3 comprehensively evidenced.**
6. **Kate @ PointsBet insurance strand (operator-initiated):** 10 qualifiers ($50 Shimonoseki won +$225; $10 Juan Bandito won +$34; 8 losers incl. two late $50s). Two triggers: Solar Flare (2nd → $10) and Velocity Miranda (2nd → $10, credited clean through the proper door first time).
7. **Wrong-variant incident (Solar Flare) — found, corrected, lesson banked:** operator intended the FB 2nd variant but the bet carried "Ins $50 Cash 2nd" (dense near-identical picker labels; picker code verified clean — attaches exactly what's pressed; the max-stake box is display-only). The trigger therefore credited **$10 CASH** instead of a $10 FB. Correction under supervision (backed up): cash event deleted, bet re-pointed to the FB variant + `safety_net` tag set via the designed PATCH, credit re-issued through `POST /v1/promos/credit-in` ($10 FB), balances exact after. Also: with stake ≤ cap the credit maths is variant-cap-independent — **shape (positions × return type) is what must be right at logging; the cap only binds when stake > cap.** This insight anchors the promo-picker redesign.
8. **Log Past Bet first live use — double-entry incident:** the operator's form submission DID register but showed no confirmation (stale-page class); believing it failed, a second entry went in via Claude through the same door. Duplicate detected in the close-loop map and deleted (guarded, backed up). Findings: the door works, but (a) no visible save confirmation, (b) no FB inventory draw-down (deploy event written manually via `record_free_bet_deployment` script), (c) no cycle linkage (joined manually).
9. **Cycle joins + labels squared in-session** (operator asked mid-day, not deferred to close): all four conversion cycles completed to 3 legs (qualifier → FB back → lay); duplicate removed; `safety_net` set on all 10 Kate qualifiers via the designed PATCH; `credit-gaps` watchdog verified seeing them. Cycle groupings table rendered for the operator — confirmed "all correct".
10. **Results self-serve commitment:** from the next session Claude calls win/lose + trigger status from the Betfair/place-market result rather than asking the operator (greyhound place data flagged as the honest gap).
11. **Day fully closed:** zero unsettled bets, manual queue EMPTY, `ops.settlement_review` run clean, all balances derived exact: Tim@TAB $1,592.20, Tim@BetFair $2,927.26, Sarie@TAB $1,040.00 (+$50 FB carried), Leigh@TAB $990.20, Kate@PointsBet $1,151.50. **Conversions: $210 of bonuses → $162.53 cash (77.4%), well above the 65% assumption.**
12. **Design direction LOCKED by operator at close** (S235 drafts from this — see Forward routing): (a) **cycle demotion** — stop storing/regulating cycle groupings, derive chains on read from the promo-event links (qualifier→credit→deployment already in the store) + market/selection lay pairing; deep cycle analytics belong to the analytical layer via data capture (DR-027-consistent); free-form FB logging (account/aab at will) with inventory enforcement + promo attach unchanged (the real money guards). (b) **Race-page rework** — kill the bottom log panel; top bar = account → account-at-book → promo (recency-informed rail; Saturday shape: 18 identical promo bets = runner-click + confirm), stake prefilled from the promo; bottom of page becomes an always-visible **race activity board** (replaces runner-flag idea); kill the Betfair account picker in the modal (sole account reality); modal hand-off collapses into the same top-bar flow (absorbs the earlier popup decision); BetLog displays round to 2dp (store keeps exact).

## Findings / calls of note

- **Tick 1 NOT claimed for day 2** (honest classification): settlement was fully self-serve (buttons + worker) and the operator logged everything, but the day needed Claude-supervised store corrections (wrong variant, credit re-book, duplicate, cycle joins) — a clean day means none of those. The corrections trace to promo-UX and past-bet-door gaps, not money-path failures; the redesign targets exactly this.
- **Modal lays orphan their cycles** (HedgeModal sends no cycle_id) — root of the day's stitching; mooted by the cycle-demotion direction.
- **Credit-in gate requires `safety_net` tag but the race-page logging flow never sets it** — every qualifier landed untagged; the watchdog was blind until tags were set. Redesign folds the tag into promo attach.
- **`credit-gaps` watchdog over-lists by design** (every lost qualifier with no credit; can't know placings) — needs a dismiss affordance.
- **Stale pages bit again** (×2 today: Log Past Bet silent save; race pages not refetching) — now upgraded from niggle to redesign input.
- **`realised_conversion_rate` never populated** on conversions — likely tied to cycle linkage; moot under demotion, watch in the redesign.
- **Float display artifact** (`10.000000000000002`) in BetLog — 2dp display rounding agreed.
- **Claude calls (Cat 5):** guarded single-row SQL only where no designed door existed; deploy-event script reused the app's own `record_free_bet_deployment`; duplicate resolved by deleting the unlinked row (the survivor carries the deploy event + cycle); selection-name normalised to numbered form at operator request.
- **Operator calls:** no lay on straight-EV insurance bets (his idiom "laid" = staked at the book); don't build mid-live-day; cycle joins done in-session rather than at close; design items 1–6 as recorded above; no more betting after ~18:50.

## Standing-instruction adherence check

- **DR-021** all anchors Adelaide ✅. **Cat 1** fast-path open; live-day baby steps (one leg per round); tight hand-offs; design talk deferred to close as agreed ✅. **Cat 2** first-action gate: operator stated "Do the close and drafts on open" — S235 first action confirmed as drafting the two artefacts then HOLD ✅. **Cat 3** empirical verification throughout (every leg verified on the live read path; balances reconciled to the cent at each step; picker code read before blaming the click; backups before every store-write batch: `solarflare-repoint`, `kate-credit-correction`, `mbkc-manual-log`, `cycle-joins` in `~/.bethub/backups/`) ✅; scratchpad + `uv run` script for the deploy event ✅; no git writes (no code changed — `9de0609` clean throughout) ✅. **Cat 4** live-integration honesty: tick 3 claimed on five real worker settlements; tick 1 explicitly NOT claimed; watchdog's design limits stated plainly ✅; S233 promo-terms rule applied (variant verified against the operator's slip description before settling anything on it) ✅. **Cat 5** software calls made and reported plainly; the cycle-demotion recommendation argued with the operator's own evidence ✅.
- **Sweep-the-class note (Cat 4, S223 rule):** today's promo/UX gaps were surfaced across the day rather than in one pre-sweep — acceptable because each was caught before money booked wrong, but the S235 brief should sweep the whole logging/promo surface once rather than fix serially.

## Open items

**Closed in S234:** tick 3 (five automatic settlements); R1 MEDIUM (partial match seen live, handled correctly — downgrade to closed-watch); the four conversion cycles + all labels; Solar Flare wrong-variant + wrong-currency credit; MBKC duplicate; Kate's two trigger credits; the day's money (zero unsettled, queue empty).

**New (absorbed into the S235 redesign scope unless noted):** race-page rework + promo rail (design LOCKED, brief to draft); cycle demotion (design note to draft); Log Past Bet save confirmation + FB draw-down + inventory hook; watchdog dismiss; 2dp display; Betfair picker removal; safety_net-at-logging; race activity board. Standalone: greyhound/harness place-result coverage for the results-self-serve commitment.

**Carried:** Sarie's $50 FB (operator converts when he chooses); the parking lot per `current_state.md` (stale-page items now subsumed by the redesign).

## Session close state

bethub-v3: HEAD `9de0609` = origin/main, tree clean, **no code changes this session**. Store: 33 lifetime bets, all settled; 4 complete 3-leg conversion cycles; FB inventory $50 (Sarie only); balances as §11 above, manual queue empty, `ops.settlement_review` clean. Backups: 4 new pre-write backups in `~/.bethub/backups/`. App: running at close (operator to shut down; no dist work pending). Rebuild root: no new artefacts this session (day 2 record lands in `b6_proving_window_log.md` at this close); no phantom files.

## Forward routing

**S235 first action (operator-confirmed: "Do the close and drafts on open" — drafting only, then HOLD):** draft TWO artefacts from this record's §12 design lock:
1. **`cycle_demotion_design_note.md`** — derive-don't-store cycles: what the store keeps (promo-event chain, inventory enforcement, promo attach), what derives on read (chain views), what moves to the analytical layer (cycle P&L via capture), what gets deleted/ignored (cycle_id regulation, inheritance logic), and the two named guards that stay (unpaired-lay flag, lost-qualifier watchdog).
2. **`race_page_rework_brief.md`** — one Code build brief: top-bar log flow (account → aab → promo recency rail → runner-click + confirm, stake prefill, safety_net auto-tag, shape-first promo picking with cap-off-the-slip), race activity board (bottom panel), modal hand-off into the same flow + kill Betfair account picker, Log Past Bet save confirmation + FB draw-down, watchdog dismiss, 2dp display rounding, stale-page refetch sweep, "API 503" plain-language label. Money-path edit surface: NONE (fence it explicitly).

Both HELD for operator review — nothing auto-executes beyond the drafts. The operator may also run Sarie's $50 conversion any day; results self-serve commitment applies from S235.
