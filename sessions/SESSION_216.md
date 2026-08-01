# SESSION 216 — Settlement-worker build brief LOCKED + handed to Code; backfill look cut short by capacity error

**Opened:** 2026-07-02 08:44 ACST (headless runner; first action held for review)
**Closed:** 2026-07-02 10:23 ACST
**Tool routing:** Chat (brief lock via `bethub-brief-drafting`; governance; close). Code executed the settlement-worker read-back out-of-session and HELD at the §3 gate.
**Governing DRs:** DR-021 (Adelaide anchors), DR-027/028 (two-DB boundary), DR-030 (module boundaries), DR-032 (Betfair settlement spine), DR-033 (data-source roles).

---

## Anchor

- Open (runner): `2026-07-02 08:44:09 ACST` — runner drafted the settlement brief and HELD for review.
- Close: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-07-02 10:23 ACST`.

## Pre-flight checks

Runner's S216 open drift-check was clean (current_state stamped 08:40 matching S215 close; SESSION_215.md present; build picture updated; root clean, no phantom files). `bethub-v3` at `e2638fa`, clean tree. On live pick-up, the runner's held result was fresh (run 08:44 > S215 close 08:40) and presented straight per the fast-path.

## Session shape

Build-commission + close session. Three strands: (1) resolved the one open money-path decision on the settlement brief and locked it via `bethub-brief-drafting`; (2) produced the Code prompt, handed off, and triaged the read-back that came back at the gate; (3) began the read-only backfill investigation while Code built — cut short by a platform capacity error before any VPS command ran. Close ran on the capacity signal (a split trigger) — clean, no push-through of the backfill work.

## What was delivered

1. **Settlement-worker build brief LOCKED and handed to Code.** The §5.1a removed-runner decision was resolved with the operator: **Option C (precise, reduction-factor-gated) with Option B pre-authorised as the fallback**. "Material" made market-type-aware — WIN parks at reduction factor ≥2.5% (Betfair's own line; below that nothing is deducted), PLACE parks on any factor >0 (Betfair applies it there even under 2.5%) — the PLACE half specifically to protect Strategy 4 place winners from silent under-parking. The reduction factor's sourcing (enriched settlement payload vs companion market-book read) was left as Code's §3-gate call, and §9's edit surface was widened narrowly to permit a companion read if needed (Code names what it touches). Added **§5.1b** at operator request: an early-operation verification surface emitting a record on every removed-runner decision (park and paid-full alike) — the operator reads these during initial live operation to confirm the guard decides correctly against real Betfair; detect-and-surface only, quietenable once proven. Draft renamed `settlement_worker_build_brief_DRAFT.md` → `settlement_worker_build_brief.md`. **Stats: 178 lines, 27,392 bytes, SHA256 `758cac8b4f90d342`.**

2. **Code prompt issued; read-back returned and HELD at the §3 gate.** Provided the copy-paste Code prompt (anchor, pre-reads, read-and-confirm gate, hard limits, output spec). Code ran out-of-session, opened and read all §5 anchors against live HEAD (`e2638fa`, clean), and posted the mandatory read-back: anchor confirmed, all 39 anchors resolve (6 cosmetic drifts, none change the build), §5.1a understanding matches. **Code chose the enriched-settlement-payload sourcing** and stopped at the gate needing **one operator call** before it edits — a §9 edit-surface question: (1) authorise a single additive line in `_translation.py` (`r.get("adjustmentFactor")`) so Option C ships **live-effective** [Code's recommendation], or (2) stay strictly inside the `settlement.py` named surface so Option C ships **plumbed-and-tested** with `_translation.py` population as a named follow-up (interim: field unpopulated → Option B park fires, never a silent full-payout). Both keep the money-path invariant. Full read-back saved to `settlement_worker_readback.md` for S217 triage.

3. **Backfill investigation ATTEMPTED — no new findings (capacity error).** Grounded the placings state from the S215 record and framed the three read-only questions (verify the ~6.1k deficit drop is real fills vs metric-scope/404-reclassification; characterise the `post_retry_truncated` wall; retire-vs-chase on the oldest ~100 dates). A platform capacity error hit **before any VPS command ran** — process tools were loaded but nothing executed. **No empirical VPS data was gathered this session.** Leading (unverified) hypothesis carried forward: the 6.1k drop is likely dates 404'ing out of the "recoverable" set (target shrinking, not burndown), which would partly pre-answer retire-vs-chase. VPS access was **not** re-verified — the S215 ssh-agent key may need re-adding next look (`ssh-add ~/.ssh/id_ed25519`).

## Standing-instruction adherence check

- **DR-021** — open + close both anchored in Adelaide local time. ✅
- **`bethub-brief-drafting` Step 7 (lock ritual)** — brief written, verified post-write, stats (line/byte/SHA) captured here. ✅
- **Cat 5 (operator–Claude division of labour)** — the money-path §5.1a and §9 calls were surfaced to the operator, not taken unilaterally; the code build is commissioned to Code, not done in Chat. ✅
- **Read-only DB discipline** — moot; no VPS/capture reads actually executed (capacity error pre-empted them). No code touched in Chat.
- **Split-trigger discipline (Step 3)** — capacity signal treated as a split trigger; backfill work deferred rather than pushed through. ✅
- No standing-instruction edits this session → no sweep, no skill-review trigger.

## Open items

Pointer-only — full list in `current_state.md`.

**New / changed in S216:**
- **Settlement-worker build brief LOCKED** (Option C + Option B fallback; §5.1b verification surface added). Handed to Code.
- **Code read-back HELD at the §3 gate** — awaiting operator go-ahead + the (1)/(2) §9 edit-surface pick. Saved to `settlement_worker_readback.md`.
- **Backfill:** investigation attempted but yielded no data (capacity error); state unchanged from S215 (deficit 35,718; walls on `post_retry_truncated`; 6.1k drop still unverified).

**Closed in S216:**
- Settlement-worker build brief drafting → lock (S216 gated auto-action). ✅
- Code prompt issued + read-back triaged to the point of the operator decision it needs. ✅

**Carried to S217:**
- **Settlement read-back triage** (auto-action) — recommend the (1)/(2) call + go-ahead, HOLD for operator.
- **Placings backfill investigation** (unchanged, now behind the read-back triage): verify the 6.1k drop; characterise `post_retry_truncated`; retire-vs-chase on the oldest ~100 dates. Re-verify VPS/ssh-agent access first.
- Promo-seed; W16 cutover scoping.
- Data Foundation arc (parallel, not gating).
- Cowork sub-agent review → pre-W16 go/no-go (tied to settlement-worker launch-readiness).

## Session close state

Rebuild root clean (no phantom files; `_DRAFT` brief gone, locked brief present; `settlement_worker_readback.md` added and referenced). `.close_out_backups/` swept to the S217 opening prompt only. `v3_build_picture.md` updated (settlement-worker stream moved: brief locked + handed → Code at read-back gate). `standing_instructions.md` untouched. No code touched in Chat; **bet-safety CLEAN** (no live Betfair, no settlement pass, no VPS writes; the settlement worker remains unbuilt and off-by-default by design). `bethub-v3` tree clean at `e2638fa` (Code made no edits — held at gate).

## Forward routing

**Confirmed with operator.** S217 auto-action = **triage the settlement-worker read-back** (`settlement_worker_readback.md`): recommend the (1)/(2) §9 edit-surface call and the go-ahead, then **HOLD** for the operator (the money-path call and sending go-ahead to Code are the operator's). Then, as the next work item, the **placings backfill investigation** carried from S216 (verify the 6.1k drop; characterise `post_retry_truncated`; retire-vs-chase) — read-only, re-verify VPS access first. Data Foundation harvest remains parallel, not gating. Pre-W16 Cowork multi-agent panel stays parked until the worker is wired toward launch.
