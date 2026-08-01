# SESSION 235 — REDESIGN DRAFTED, WALKED THROUGH, LOCKED, AND **BUILT IN ONE ARC**: the race-page rework brief (incl. Addendum B) executed end to end by Code — 12/12 items, no fence findings, suites 1399→1418 / 134→160, seven commits pushed — tick 1's named friction is now implemented-not-live

**Opened:** 2026-07-08 20:03 ACST (fast-path — the headless runner auto-executed the S234 first action: both redesign artefacts drafted + HELD; an independent verification pass added Addendum A to the demotion note at 20:35).
**Closed:** 2026-07-09 11:05 ACST, Adelaide-anchored per DR-021.
**Tool routing:** headless runner (drafts, 2026-07-08 evening) → operator walkthrough in governance chat (2026-07-09 morning, Addendum B amendments recorded on both artefacts at 09:41) → **out-of-session Claude Code build session on bethub-v3** (09:42–10:26, executing the LOCKED brief) → governance close (this record).
**Bet-safety:** CLEAN — no bets placed, no Betfair contact of any kind, both workers OFF throughout, live store (`data/bethub.db`, `~/.bethub/`) untouched. All build verification ran on tmp-path fixture stores; the app was never launched (it was confirmed DOWN before the one permitted `npm run build`).
**Governing DRs:** DR-021 (Adelaide anchors), DR-019 (money derives on read — nothing in the build stores derived state; the unpaired-lay flag and source-pending list are display/read derivations), DR-022 (vocabulary), DR-027/028 (no new cross-database surface), DR-030 (routers thin; new derivations in `workflows/promos/v1/burst_review.py`).

---

## Anchor

- Open: headless runner stamp `2026-07-08 20:03 ACST` (S234 close 19:57).
- Close: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-07-09 11:05 ACST`.

## Session shape

Three beats. (1) The runner drafted the two S234-locked artefacts and HELD them (`cycle_demotion_design_note.md`, `race_page_rework_brief.md`), plus a same-evening independent verification pass (demotion note Addendum A: single-spend is read-enforced, write-door hardening proposed → routed to the demotion build). (2) The operator walked both drafts next morning and agreed the direction item-by-item — walkthrough outcomes recorded as Addendum B on both files (two-click confirm card over one-click; the new-promo card; spend-now-file-later + burst review; placings auto-check PARKED; §9 exceptions e–g; the B8 build order) — and signed the brief off ("Let's do it"). (3) A Code build session executed the brief END TO END the same morning.

## What was delivered (build session, bethub-v3 `9de0609` → `51b62f7`, pushed)

All twelve B8 items **BUILT**, none cut, zero money-fence findings. Full detail (per-item anchors, §5.8 after-matrix, design calls, live-look checklist, §9 self-assessment) in **`race_page_rework_report.md`** (ends `<!-- RACE PAGE REWORK COMPLETE -->`). Headlines:

1. **5.2 Race activity board** — market-scoped bets read (additive `betfair_market_id` filter through the shared store SQL + `GET /v1/bets?market_id=`); always-visible bottom panel, one compact line per position, display-derived **unpaired-lay flag** and partial-lay state.
2. **B1 top-bar flow + confirm card** — [person][book] │ shape-first, recency-informed promo rail │ [Free bet][No promo][+ new]; runner-click opens the confirm card (stake prefilled from the cap and typed off the slip; **safety_net auto-set on insurance-shaped promos only, visible as a chip**); persistent success confirmation. Saturday shape: rail tap once, then runner-click + confirm per bet.
3. **B2 new-promo card** — two categories only, dials, per-account-betslip nudge; additive `POST /v1/promos/templates` (catalogue INSERT through the existing adapter door); save arms immediately.
4. **B3 spend-now-file-later** — "bonus not banked yet" logs a free bet with no consumed credits; surfaces as *source-pending*; a mid-burst spend never blocks.
5. **5.4 modal hand-off** — placement drops into the flow (board refresh + toast); frozen banner retired; still no cycle link sent.
6. **5.3 picker bypass** — sole Betfair account-at-book auto-selects (⚡ straight to the modal); picker returns automatically at 2+; component bypassed, not deleted.
7. **B4 one-tap settle-and-bank** — "Lost — placed, bonus landed" composes the EXISTING settle + credit-in doors (board, BetLog, burst review).
8. **B5 burst review** — new `/burst-review` screen: unsettled soft-book bets / source-pending spends with **pairing through the existing `record_free_bet_deployment` door** (single match = one tap; ambiguous = listed, never guessed) / banked-unspent credits / the credit-gaps backstop with per-item dismiss + include-dismissed toggle. **Acceptance PASSED:** a full conversion-day fixture reconciles to zero flags in one pass (backend test).
9. **5.6 watchdog dismiss** — durable via one additive `promo_journey_annotation` event; display-layer only; **test-proven not to touch credit-in eligibility**.
10. **5.5 Log Past Bet** — unmistakable persistent "Bet saved" panel; FB inventory draw-down through the endpoint's new `consumed_credit_event_ids` → existing deployment writer (non-fatal warning contract; proven via `compute_free_bet_inventory` before/after); B3 option; double-submit guarded UI-side.
11. **5.7 rounding** — display-only 2dp across BetLog/racing/board (the `10.000000000000002` class closed; stored values asserted exact).
12. **5.8 + 5.9** — one central invalidation sweep covering all 12 mutation sites (the lay-placement and Log-Past-Bet invalidate-nothing holes closed; the provisional manual-queue resolve broadened too); plain-language error labels with both named cases test-pinned (prices feed-down; streaming-disconnected interlock wording kept truthful).

**Suites:** backend 1399 → **1418**, frontend 134 → **160** (LogBetPanel/PromoBar suites retired with their components; coverage re-homed and net grown). Green at every commit. Dist rebuilt with the app down — **the next launch serves the new UI.**

## Findings / calls of note

- **Nav rename:** "Burst review" now names the new reconciliation screen; the W8 provisional park queue is relabelled **"Manual queue"** (route unchanged). The operator should expect this on next launch.
- **Report residuals (all LOW):** Log Past Bet has no server-side idempotency key (would need fenced `record_builder.py`; UI-guarded instead — F3); burst-review credits section fans out one log-context read per account-at-book (fine at 13 pairings — F4); pair-spend inherits the known Addendum-A write-door softness (single-spend read-enforced; UI only offers available credits; hardening rides the demotion build — F6).
- **Toolchain lesson (F1):** vitest does not typecheck — one missed TS type surfaced only at `npm run build` (fixed in-session, commit 7). Treat `npm run build` as the frontend gate in future briefs.
- **Additive API shape changes:** credit-gaps rows gain `dismissed`; `BetFeedItem` gains optional `warnings` (manual-create advisories). Both additive.
- **Demotion note untouched by the build** (as designed): direction agreed at the walkthrough; the demotion build (incl. Addendum-A single-spend write-time hardening) routes as its own brief whenever the operator wants it. No cycle machinery changed this session.

## Standing-instruction adherence check

- **DR-021** all anchors Adelaide ✅. **Cat 2** first-action gate: S234's confirmed first action (draft-then-HOLD) executed exactly; the build ran only after the operator's explicit walkthrough sign-off ✅. **Cat 3** empirical verification: baselines recorded before the first edit; per-item tests as the brief named them (safety_net tag on/off, market-scope exactness, draw-down via inventory before/after, dismiss-vs-eligibility, display-only rounding, B5 zero-flags acceptance); suites green at every commit ✅. **Cat 4** live-integration honesty: every item classified implemented-not-live; the report names what each live look must confirm; tick 1 NOT claimed ✅; S223 one-pass rule honoured (the 5.8 sweep covers the whole mutation class, incl. two surfaces outside the original friction list) ✅. **Cat 5** software calls made and recorded (10 design calls in the report, nav rename flagged for the operator) ✅. **S227 git autonomy:** seven descriptive commits with the co-author trailer, pushed to origin main, green tree only, no DBs/secrets ✅. **§9 money fence:** self-assessed file-by-file in the report; diff surface verified against the claim — zero fenced files touched ✅.

## Open items

**Closed in S235:** the whole S234 redesign friction list (wrong-variant picking → shape-first + confirm card; silent Log Past Bet save → persistent panel; invisible lays → activity board; safety_net never set → auto-tag; watchdog dismiss; BetLog 2dp; Betfair picker; stale-page class; "API 503" labels) — all implemented-not-live.

**New (routed to S236 triage):** the report's residuals F1–F7; operator-visible changes to brief (nav rename, new logging flow, burst-review screen).

**Carried:** Sarie's $50 FB (convertible any day — the new flow will exercise B3/B5 naturally); cycle-demotion build (direction agreed; own brief on operator's call; Addendum-A hardening rides it); the `current_state.md` parking lot minus the items this build closed.

## Session close state

bethub-v3: HEAD `51b62f7` = origin/main, tree clean, dist rebuilt (app down throughout). Store: untouched this session (still the S234 close state — 33 lifetime bets all settled, Sarie's $50 FB the only inventory). Workers: OFF. Rebuild root: new artefacts this session — `cycle_demotion_design_note.md` (+ Addenda A/B), `race_page_rework_brief.md` (+ Addendum B), `race_page_rework_report.md`, this record; `current_state.md` updated. No phantom files.

## Forward routing

**S236 FIRST ACTION (operator-confirmed at S235 close: "make triage auto-action" — AUTO-EXECUTES on open, no HOLD):** triage `race_page_rework_report.md` inventory-first per Cat 1 — surface the operator-relevant findings in plain language (nav rename; the new logging flow; residuals F1–F7; what each item's live look must confirm) and route forward. Per the brief's §10 the routing lands on: **live-proof on the operator's next racing day, which is also the standing tick-1 attempt** — the build targets exactly the friction that kept days 1–2 from being clean. The triage session does not write the demotion brief unless the operator asks.

Also open for the operator, any time: run a racing day (tick-1 attempt on the new UI); convert Sarie's $50 (exercises B3/B5 live); commission the cycle-demotion build.
