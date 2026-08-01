# SESSION 228 — git backup live; F-LIVE-1 fixed + live-proven; B4 seeded; F-LIVE-2 measured → fixed → LIVE-PROVEN in one session

**Opened:** 2026-07-06 11:35 ACST (cold manual open — no runner result; drift-check clean). Same workday as S227's 11:12 close.
**Closed:** 2026-07-06 14:22 ACST, Adelaide-anchored per DR-021. Same workday.
**Tool routing:** Single access-having governance Claude Code session on the Mac. Ran both fixes first-hand (Bash + file tools); spawned **independent read-only sub-agents** for two 3-lens adversarial verifies (6 agents total); observed both live launches by reading the live store (`mode=ro`) + the operator's pasted terminal text; ran a read-only out-of-band Betfair watcher (own session, list-calls only) for the F-LIVE-2 measurement.
**Bet-safety:** Money moved only as four operator-placed deliberately-lapsing lays (all $0 no-bets by design — the F-LIVE-2 measurement). Settlement worker OFF all session; reconciliation worker ON only while the operator's launched app ran (its normal live-mode opt-in). Live-DB writes: the B4 promo seed (reference data, idempotent, pre-seed `.bak` taken) — everything else `mode=ro`. Suite never left green; both commits pushed only on green trees.
**Governing DRs:** DR-019, DR-021, DR-027/028, DR-032/033.

---

## Session shape

Opened on the S227-queued first action (complete git automation), which finished in minutes once the operator did the one-time GitHub step. The A/C/B direction pick went to recommendation (A then C, B parked) — but the session ended up clearing **all three**: A (F-LIVE-1 fix) built + verified + committed; C (B4 seed) run + operator-confirmed; and B — planned as measurement-only — produced so decisive a finding that the operator directed "build fix now", and the fix went design → build → adversarial verify → commit → **live-proof** before close. Three of S227's live findings cleared in one sitting.

## What was delivered (in order)

1. **Git automation COMPLETE** — key registered + private repo `murra86/bethub-v3` created by operator; Claude wired the SSH `origin`, pushed `ede5ef9`, verified via `ls-remote`. Off-machine backup live; autonomous commit+push loop operational (3 pushes this session). Only remaining git item from S227 CLOSED.

2. **A — F-LIVE-1 promo cross-thread 500 FIXED class-wide** (`promo_crossthread_500_fix_report.md`, commit `7d221b7`). Root cause: FastAPI resolves a sync dependency and the sync endpoint in separate threadpool dispatches; the per-request sqlite connection crosses threads → `ProgrammingError` → 500 under live concurrent polling. One-pass class sweep (S223 discipline) found exactly three provider sites; all fixed with `check_same_thread=False` (per-request, sequentially-used connections; sqlite3 serialized mode as backstop). The S187/S188 storage-layer rewrite was deliberately NOT used — it would have broken `credit_in`'s single-transaction design; the fault lives at the router layer. Red-before proven; S189's xfail evidence marker retired per its own condition into a hard green 24-way concurrency guard; suite 1346→1350; 3-lens adversarial verify ALL UPHELD. **Live-proven on both launches** (catalogue 200s; promo screen clean).

3. **C — B4 promo-seed DONE** — `scripts/seed_promos.py` run against the live store: nine S132-locked templates + five warning types; verified by query; idempotent re-run wrote nothing; pre-seed backup `data/bethub.db.bak-s228-preseed` (gitignored). **Operator confirmed the nine promos display in the race-page picker.** EV-accuracy eyeball deferred (operator parking-lot). The empty-catalogue gap behind the Safety-Net free-bet cycle proof is closed.

4. **B — F-LIVE-2 measurement CONCLUSIVE** (`flive2_lapse_measurement_report.md`). Read-only watcher polled `listCurrentOrders` + all four `listClearedOrders` buckets every 15s across four operator-placed lapsing lays (Pakenham/Barcaldine/Shepparton/Wangaratta) + S227's Case B retrospectively. **5/5: Betfair files a never-matched order under `betStatus=LAPSED` within ~1–2min of the jump — never under SETTLED, the only bucket the resolver queried.** The app's park window was never too short; the filter was wrong. S227's Case B park = this exact mechanism.

5. **F-LIVE-2 fix BUILT + LIVE-PROVEN** (`flive2_lapsed_bucket_fix_report.md`, commit `2e22c5f`; operator go-ahead "Build fix now"). `get_cleared_order_state` falls back LAPSED→CANCELLED on SETTLED miss (settled path byte-identical — trap-tested with a 500-rigged LAPSED route; any bucket read failure → ReadUnavailable); `ClearedOrderStateSnapshot` gains optional `size_cancelled`; the resolver's existing `cleared_order_lapsed` FAILED branch gains the conclusiveness guard — fallback hits FAIL only when the FULL requested stake lapsed back, else carry forward (`cleared_lapsed_size_mismatch`) to the park valve (HIGH-1 held). 8 new tests, red-before proven (5 of 6 first-wave behaviourally red on `7d221b7` — the test lens corrected my "4 red / 2 lock-in" claim: one lock-in also failed pre-fix on new-field scaffolding); its two coverage flags closed pre-commit (+2 tests). Suite 1350→**1358**. 3-lens verify ALL UPHELD (money lens attacked partial-match races: every uncertain shape degrades to park/manual, never FAILED). **LIVE-PROOF: operator relaunched on the fix; the first sweep (14:17) auto-resolved all four lays `provisional_pending → FAILED`/$0 in one pass** — no parking; manual queue still holds only S227's pre-fix park.

## Findings / calls of note

- **The S189 "Finding 1 doesn't trip live" call was falsified live (S227) and is now closed** — fixed and live-proven, pre-cutover as re-classified.
- **Watcher design call (Cat 5):** own read-only Betfair session (list-calls only) rather than touching app code — Betfair supports concurrent sessions; the app's stream held SUBSCRIBED throughout, confirming no interference.
- **Sweep-the-class discipline (S223) applied twice:** three connection-provider sites fixed in one pass; LAPSED + CANCELLED buckets both added in one pass (VOIDED deliberately excluded — matched-then-voided already handled via market settlement).
- **Operator catch → parking-lot:** BetLog shows the four failed no-bets as "Pending" — the badge is `settlement_state`, which only the settlement worker stamps (OFF today by design). Display-only; add failed/no-bet rendering to the BetLog display items (S171 family).
- **Residuals recorded** in `flive2_lapsed_bucket_fix_report.md` §6: R-A (latent `place_hedge` proposed-vs-requested stake invariant — unreachable, add if ever wired), R-B (partial-then-lapse `sizeCancelled` semantics — confirm at first live partial), R-C (carry-forward counter naming), R-D (mismatch-loop REST cost, valve-bounded). Plus F-LIVE-1's: pre-existing `log_bet` exception-path close leak (LOW); four test-fixture factories in the dispatch-crossing shape (test-only).

## Standing-instruction adherence check

- **DR-021** — open + close Adelaide-anchored. ✅
- **Cat 2 first-action gate (hard)** — S229 first action CONFIRMED with operator: HOLD for a supervised settlement window (settlement worker ON → stamps the four lays terminal + live-proves the settlement side). ✅
- **Cat 3 git (S227 autonomy amendment)** — commit+push after each substantive land, green-tree-only, no DB/secrets staged, descriptive messages + co-author trailer, everything reported to operator. First session under full autonomy: clean. ✅
- **Cat 4 S223 sweep-the-class + S189 live-integration classification** — both operationalised (see above); fixes classified implemented-not-live until each live-proof, then upgraded. ✅
- **Cat 5** — technical calls made without punting (fix-site choice, watcher design, bucket scope); operational calls surfaced (A/C/B pick, build-now, first action). ✅

## Open items

**Closed in S228:** off-machine git backup ✅; F-LIVE-1 (fixed + live-proven) ✅; B4 promo-seed (seeded + confirmed) ✅; F-LIVE-2 (measured + fixed + live-proven) ✅.

**Carried to S229+** (full detail `current_state.md`):
- **S229 first action (CONFIRMED): supervised settlement window** — settlement worker ON; first pass stamps the four S228 lays terminal (BetLog badges resolve) and live-proves settlement over the LAPSED-fix output; watch R-B if a partial-lapse ever appears.
- Operator manual-queue housekeeping: S227's parked `434257942837` (unchanged).
- EV-accuracy eyeball on the seeded promos (operator, later).
- BetLog display items: failed/no-bet badge (new), unmatched-bet detail "$0 at $0" (S227).
- S1 leg-stake harden; stream subscription-trim; remaining cutover blockers B1 (arguably exercised twice now), B5 tunnel, B6 cutover mechanics, B7 monitoring.

## Session close state

bethub-v3 at `2e22c5f` (= origin/main; tree clean; suite 1358 green). Both workers OFF once the operator closes the app window. New artefacts in `bethub-rebuild/`: `promo_crossthread_500_fix_report.md`, `flive2_lapse_measurement_report.md`, `flive2_lapsed_bucket_fix_report.md` (live-proven stamp applied). `current_state.md` rotated; `v3_build_picture.md` updated; `.close_out_backups/SESSION_229_opening_prompt.md` generated (S228 prompt swept). Live store: 9 promo templates + 5 warnings seeded; four measurement lays `failed`/$0 (settlement stamp pending the S229 window); pre-seed `.bak` on disk (gitignored). **Bet-safety CLEAN.**
