# SESSION 227 — B3/B2 money-loop LIVE-PROVEN on real Betfair (B2↔B3 CLEARED) — via a mid-session live stream-buffer fix

**Opened:** 2026-07-06 07:28 ACST (cold manual open — no runner result for S227; S226 closed to an operator-driven first action).
**Closed:** 2026-07-06 11:12 ACST, Adelaide-anchored per DR-021. Same workday.
**Tool routing:** Single access-having governance Claude Code session on the Mac (Full Disk Access). Ran the stream fix first-hand (Bash + file tools), spawned **read-only** sub-agents for the 3-lens adversarial verify, and observed the live-proof by reading the live store (`data/bethub.db`, `mode=ro`) while the operator drove the app + real bets.
**Bet-safety:** bethub-v3 HEAD byte-identical at `e2638fac` throughout; the only code change is the stream read-buffer fix (`_stream_transport.py`, additive on the dirty tree, **no git writes**); both workers ON **only** during the supervised live-proof window, **OFF** at close (operator-confirmed). Real money moved (two small real lays) — the whole point of the live-proof.
**Governing DRs:** DR-019 (money derives on read from `matched_stake`), DR-021, DR-027/028, DR-032/033.

---

## Session shape

Opened as the S226-deferred B3 supervised live-proof. The **first live launch immediately surfaced a blocker** — the Betfair stream fell into an unrecoverable reconnect loop (`Separator is not found, and chunk exceed the limit`). Rather than push through, the session **investigated → fixed → verified** the stream bug first (read-only investigation resolved a genuine symptom-vs-root-cause fork; a surgical bounded-buffer fix, red/green + 3-lens verified), then **ran the full live-proof to a clean pass** on real money. A second live finding (a promo-screen cross-thread 500) surfaced during the proof and was classified (money-harmless, governance-relevant). Net: the lay money loop is proven end-to-end on real Betfair; **B2↔B3 cleared**.

## What was delivered (in order)

1. **Stream 64 KiB read-buffer overflow — investigated, fixed, verified** (`stream_read_buffer_overflow_fix_report.md`). Root cause: the live connector `open_tls_connection` used asyncio's default 64 KiB `StreamReader` line cap; the all-AU-racing market image overruns it → `readline()` ValueError → the broad `except` reconnects → the oversized image is the first frame every reconnect → unrecoverable loop. Latent since the S198 baseline (not a regression). Fork resolved on evidence: the buffer cap is a genuine bug (fix regardless); the broad subscription is a deliberate design choice (park the trim). **Fix (surgical, `_stream_transport.py`):** new bounded `STREAM_READ_LIMIT = 8 * 1024 * 1024`, passed to `asyncio.open_connection(..., limit=…)`. **3 new tests**; wiring test **red-before/green-after PROVEN** (reverted → fail; restored byte-identical md5-confirmed); suite **1343 → 1346**. **3-lens independent read-only refute-verify (correctness / blast-radius / test-integrity) — ALL UPHELD.** Live-confirmed: the stream reached SUBSCRIBED and held across two launches + a restart.

2. **B3/B2 supervised live-proof — PASSED** (`b3_liveproof_result.md`). **Case A (matched):** LAY $3.15 on *2. Aston Valhalla* (Shepparton) placed unmatched → landed `provisional_pending` (P1) → matched → reconciliation wrote the **TRUE** stake (0→3.15 @ 2.56, `final_full`; B3) → gate held it `pending` while open (P4) → on `CLOSED`/null-`settled_time` (S223) it settled `settled_lost` (layed the WINNER → LAY inversion), real liability **−$4.91, not $0** (B2). **Case B (never-matched):** LAY $8.33 on *1. Frankys Lass* left to lapse → held `provisional_pending` through 3 reconciliation sweeps (~10 min), never got a conclusive lapsed signal → **P4 park valve** escalated it to the manual queue (`settlement_state → provisional`), `matched_stake` stayed 0, **never auto-settled** (HIGH-1 principle live). **B2↔B3 CLEARED; B2 auto-settlement fully money-proven.**

3. **Governance close stamped** (`b3_governance_close.md` §6 — LIVE-PROOF PASSED).

## Findings surfaced live (all logged in `b3_liveproof_result.md`)

- **F-LIVE-1 (real, NOT money-path):** promo-catalogue cross-thread SQLite 500 (`store/repositories/promos.py:189`) — this is **S187/S189 Finding 1** (per-request `get_db_connection` cross-thread class), assessed at S189 as "does not trip live → parked post-cutover." **It tripped live.** That call is falsified → **Finding 1 comes OFF "parked" and becomes a real pre-cutover fix** (S187/S188 per-method-connection pattern). Money-harmless (read path, empty B4 catalogue, `/bets` stayed 200, workers unaffected).
- **F-LIVE-2 (operator-raised tuning question):** a lapsed lay parks rather than auto-`FAILED` because Betfair cleared-orders didn't surface the lapse in the 3-sweep/~10-min window; observed that once parked, reconciliation did not re-sweep it. Deeper unknown: does a purely never-matched order *ever* appear in cleared-orders? **Resolve by measurement** (place several lapsing lays, log clear-times) → then a park-threshold/design decision. Money-safe regardless.
- **S1 (residual, money-harmless):** reconciliation leaves `bet_legs.matched_stake` stale on a post-placement match (Case A: bet=3.15, leg=0.0). Money derives from `bets.matched_stake` (`balance_derivation.py:142-144`), not the leg; nothing money-bearing reads the leg. Same family as S226 R3. Candidate harden.
- **Parking-lot (UX):** BetLog shows "$0 at $0" for unmatched/pending bets — wants requested stake + intended price + runner surfaced (S171 BetLog surface).

## Standing-instruction adherence check

- **DR-021** — open + close Adelaide-anchored. ✅
- **Cat 4 (bet-safety)** — HEAD byte-identical `e2638fa`; stream fix additive, no git writes; red-before reverted+restored byte-identical (md5); workers ON only in the supervised window, OFF at close; real money moved only as the intended live-proof (two small lays). ✅
- **Cat 5 (division of labour)** — access-having governance session ran the stream fix first-hand (legitimate, held the access); adversarial verify routed to independent read-only sub-agents (author-bias counter); the symptom-vs-root-cause fork and the fix-vs-park scope calls surfaced to the operator. ✅
- **S178/S189 discipline** — investigation resolved the fork before building; live-proof surfaced findings green tests missed (F-LIVE-1, F-LIVE-2). "Green ≠ live-correct" operationalised. ✅
- **First-action gate (S200, hard)** — S228 first action confirmed: **HOLD — present the A/C/B option overview + recommendation, then await operator decision** (operator elected "decide at open," requested the overview be prepared). ✅
- **Cat-2 sweep** — `current_state.md`, `cutover_readiness_map.md` (pending), `v3_build_picture.md` updated this close; no `standing_instructions.md` change warranted.

## Open items

**Closed in S227:**
- Stream 64 KiB buffer overflow — fixed + verified + live-confirmed. ✅
- **B3/B2 live-proof — PASSED; B2↔B3 CLEARED.** ✅

**Carried to S228 (pointers; full detail in `current_state.md` + `b3_liveproof_result.md`):**
- F-LIVE-1 (promo cross-thread 500 — Finding 1 off-park → fix brief).
- F-LIVE-2 (cleared-orders clear-time measurement → park-threshold/design decision).
- S1 (leg-stake propagation harden); BetLog unmatched-detail display; stream subscription-trim (parked).
- **Operator manual-queue housekeeping:** clear parked bet `434257942837` ($8.33 lapsed, $0 no-bet).
- **Operator commit-time (extends HIGH-2 / LOW-5):** B3 fix + stream fix share the uncommitted tree; stage/commit deliberately; `*.db.bak-*` gitignore.
- Remaining cutover blockers: B1 (fresh-lay full loop — exercised in passing today), B4 promo-seed, B5 tunnel, B6 cutover mechanics, B7 monitoring.

## Session close state

bethub-v3 at `e2638fac` (stream fix additive on the dirty tree, no git writes), both workers OFF, v2 untouched. New artefacts in `bethub-rebuild/`: `stream_read_buffer_overflow_fix_report.md`, `b3_liveproof_result.md`; `b3_governance_close.md` §6 stamped. `current_state.md` rotated; `v3_build_picture.md` updated; `SESSION_227.md` written; `.close_out_backups/SESSION_228_opening_prompt.md` generated (stale `SESSION_226_opening_prompt.md` swept). **Forward routing CONFIRMED with operator:** S228 opens HOLDING — presents the A (fix promo 500) / C (B4 promo-seed) / B (park measurement) overview + Claude's recommendation (A→C, B parked), then awaits the operator's pick. **Bet-safety CLEAN.**

## Post-close addendum — git checkpoint (operator-authorised)

After the close, the operator authorised "execute all things related to git." Actioned the S227-close commit-time items (HIGH-2 / LOW-5): added `*.db.bak*` to `.gitignore`, staged 38 files (37 code/test + `.gitignore`) with a verified-empty `data/`/`.db` staging set, and committed a **local checkpoint `ede5ef9`** (was `e2638fa`) — "B3 lay money-path fix chain (S222–S227) + live stream buffer fix — LIVE-PROVEN". The commit is a **clean snapshot of the live-proven code (no code change)**; the live DB/WAL and the `.db.bak` backup are excluded/ignored; working tree now clean (`data/` untracked as designed). **HIGH-2 + LOW-5 RESOLVED.** The one remaining git item is **off-machine backup** — no remote configured; push pending the operator's one-time GitHub login (then add remote + push). This is the first HEAD move since `e2638fa`; the bet-safety invariant now anchors on `ede5ef9`.

Operator then directed **full git autonomy**: "fully automate all aspects of git so you can handle it all." **`standing_instructions.md` §git-hygiene amended (S227)** — Claude now owns the `bethub-v3` git lifecycle (commit + push after substantive work, no per-write approval) under fixed guardrails (never commit DB/secrets, never force-push, green-tree-only, private repo, still reports what it committed). Enabling setup pending the one-time operator step (register `~/.ssh/id_ed25519` to GitHub + create an empty private `bethub-v3` repo; GitHub auth is a security boundary Claude can't cross). **Governance events this addendum:** (a) standing-instruction change → needs re-upload to the Project knowledge base + open/close skill review at next open; (b) **S228 first action CHANGED** from the A/C/B hold to "complete git automation setup, then the A/C/B hold" (`current_state.md` + `SESSION_228_opening_prompt.md` updated).
