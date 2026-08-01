# SESSION 225 — B3 lay money-path: brief falsified → investigation → 4-part design → cautious build (P1–P4, suite green) → max-effort adversarial verify found a HIGH $0-path → HIGH-1 fix commissioned (in flight at close)

**Opened:** 2026-07-05 ~16:35 ACST (headless/manual open; S225 guarded auto-first-action = draft the B3 match-reconciliation fix Code brief).
**Closed:** 2026-07-05 19:27 ACST.
**Tool routing:** Governance/Chat-equivalent Claude Code session on the Mac (Bash + file tools). It **read** bethub-v3 first-hand but wrote **no** bethub-v3 code — all code work ran in **commissioned Claude Code sessions** (division of labour, Cat 5). Governance edits: bethub-rebuild docs + auto-memory only. **bethub-v3 HEAD byte-identical at `e2638fa` throughout; `BETHUB_SETTLEMENT_WORKER` OFF throughout; no money moved.**
**Governing DRs:** DR-032/033 (Betfair settlement spine / data-source roles), DR-030 (module boundaries), DR-027/028 (two-DB boundary), DR-019 (derived state on read), DR-021 (Adelaide anchors).

---

## Anchor
- Open ~16:35 ACST, close `TZ="Australia/Adelaide" date` → 2026-07-05 19:27 ACST. Same workday as S224 close (16:26) → tight-recap open; ran as a full working session.

## Session shape
The S224 auto-action — "draft the B3 wire-the-worker brief" — was drafted, then, at the operator's request, **grounded by adversarial verification that falsified its central premise**. That flushed the real problem (a Path-A placement mislabel, not a missing worker) and drove the whole S222-style chain: **investigation → design → cautious build → adversarial verify → fix**. The verify (max effort, operator-requested) is the star: it found a **confirmed HIGH money-path hole the four prior green suites all missed** — the fix re-creating the exact $0 bug in P3's own window. A targeted HIGH-1 fix was commissioned and launched; it is in flight at close, triage deferred to next open.

## What was delivered (in order)

1. **Drafted the B3 wire-the-worker brief → operator asked to ground it → adversarial verify FALSIFIED it.** Five read-only sub-agents against bethub-v3 confirmed the load-bearing facts, but one refuted the premise: the live lay entry `place_lay` (`racing.py:1105-1109`) writes a not-fully-matched lay **terminally** as `FINAL_PARTIAL matched_stake=0`, which `run_reconciliation_pass` (sweeps `PROVISIONAL*` only) **never touches** — so "just wire the worker" fixes nothing. Verified first-hand. Brief **superseded**; reframed to an **investigation commission** (`b3_match_reconciliation_investigation_brief.md`).

2. **Code investigation ran → root cause CONFIRMED + all 4 gaps CLOSED first-hand.** The Code host app's `~/Desktop` TCC access was revoked **mid-session**, leaving 4 gaps; the report landed at `/Users/tim/` (watcher never fired — wrong path + no sentinel). The **governance session's access was unaffected**, so it closed all four first-hand (§10 of `b3_lay_settlement_investigation_report.md`, relocated to `bethub-rebuild/`): **G1** lay money scales linearly with `matched_stake` (`balance_derivation.py:185/241`; 0→$0, direction independent); **G2** the adapter gives no live matched-size for a cleared order → resolver hardening needs a **new `listClearedOrders` read**; **G3** the live worker runs **no** reconciliation pass; **G4** store had 3 LAY bets, **exactly one mis-valued** (`434175139855`, real 4.98 booked $0).

3. **Drafted the 4-part coupled design** (`b3_lay_settlement_fix_design.md`): **P1** re-label placement (`remaining>0 → PROVISIONAL_PENDING`), **P2** wire the periodic reconciliation worker (on-in-live + `BETHUB_RECONCILIATION_WORKER` kill switch), **P3** recover true matched size for a cleared order via a new `listClearedOrders` read, **P4** gate settlement to exclude `PROVISIONAL*` + a park-not-settle safety valve. Coupled (fails closed). **Backfill DROPPED** per operator (test-bet log clears at live-proof).

4. **Cautious build commission → 2 Phase-0 STOPs (env, not design) → clean build.** The build brief made the design a **hypothesis to validate, not a spec** (a nod to the falsified v1). Two Code attempts STOPPED at the Phase-0 gate: the host app's TCC/Full-Disk-Access to `~/Desktop` was blocked (attempt 2 failed because the running process pre-dated the grant). Diagnosed: **run from a process started *after* the grant** — a fresh Terminal session (Terminal.app already has access). The build then completed (`b3_lay_settlement_fix_report.md`): **P1–P4 built additively on the dirty tree, HEAD unchanged, no git writes, suite 1327 passed / 1 xfailed (+38)**, Phase-0 clean, sensible documented deviations. Governance ground-checked HEAD + the P1 edit + new files.

5. **Max-effort adversarial re-verify (operator-requested) → DEFECTS FOUND, worst HIGH** (`b3_verification_report.md`; reproduced the suite exactly first-hand). **HIGH-1 (CONFIRMED):** P3's cleared-orders fall-through **re-books the incident-class winner at $0/`FAILED`** — a 0-matched lay that matches, clears out of `listCurrentOrders`, and whose cleared read *misses* (lag/500) → market-settlement fall-through returns `FAILED` off stale `matched_stake=0` (real REST `settled_time` is always `None`), terminally, excluded from sweep **and** valve, **no self-heal, untested** (the fall-through tests all use a non-zero stale stake — green by omission). **HIGH-2:** B3 is mechanically inseparable from the un-live-proven S222/S223 chain in one uncommitted tree (commit-time coordination). Plus MEDIUM-1/2/3/4, LOW-1..5 (incl. LOW-5: untracked `data/bethub.db.bak-S222-*` not gitignored). **What held:** P1, the P4 gate + valve, the P2 worker, and the settle-vs-reconcile race discipline — all sound and well-tested; HIGH-1 is the only hole in the race story.

6. **Commissioned the HIGH-1 fix (+ test gaps), launched — in flight at close** (`b3_high1_fix_commission.md`). One unifying principle: **never terminalise to `FAILED` without a conclusive never-matched signal; carry-forward (no decision) when the cleared read is inconclusive; the park valve backstops.** Scope: Fix A (HIGH-1 carry-forward), Fix B (MEDIUM-1 null-price → carry-forward), Fix C (MEDIUM-4 persist mid-flight stake), + tests MEDIUM-2/3 + LOW-2 (+ recommended LOW-1). Red-before/green-after required on the HIGH-1 test. `b3_high1_fix_report.md` pending.

## Standing-instruction adherence check
- **DR-021** — open + close Adelaide-anchored. ✅
- **Cat 4 (bet-safety)** — bethub-v3 HEAD byte-identical at `e2638fa`; **no code touched in Chat** (governance read-only on bethub-v3; all edits in commissioned Code sessions, which held HEAD + made no git writes). `BETHUB_SETTLEMENT_WORKER` OFF throughout. No place/settle/money-move. The one known mis-valued live row left as-is (clears at live-proof). ✅
- **Cat 5 (division of labour)** — code building/verifying/fixing routed to Code sessions; governance did commissioning, first-hand grounding, and triage. Money-path scope calls (drop backfill, phase-vs-full, posture) surfaced to + made by the operator. ✅
- **S178/S189 discipline** — every premise re-grounded first-hand before acting; the adversarial verify operationalised "green ≠ correct" and caught HIGH-1. ✅
- **First-action gate (S200, hard)** — S226 first action **confirmed with operator**: triage the HIGH-1 fix report on open (`b3_high1_fix_report.md`).
- **Cat-2 sweep** — `current_state.md`, `cutover_readiness_map.md`, `v3_build_picture.md` updated this close; no `standing_instructions.md` change warranted.

## Open items
Pointer-only — full detail below + in the artifacts.

**New / changed in S225:**
- B3 root cause CONFIRMED (Path-A placement mislabel, not just "not-wired") — the S224 "not-wired" trace was one level too shallow.
- 4-part coupled fix (P1–P4) **BUILT + suite-green** on `e2638fa` (additive on dirty tree).
- Max-effort adversarial verify → **HIGH-1 confirmed** (fix re-creates $0 path) → **NOT cleared for money**; **HIGH-1 fix in flight**.
- **HIGH-2** commit-time coupling + **LOW-5** `.db.bak` gitignore — operator commit-time items.

**Closed in S225:**
- B3 investigation (root cause + all 4 gaps). ✅
- Wire-the-worker brief falsified + superseded. ✅

**Carried to S226:**
- **Triage `b3_high1_fix_report.md`** (first action, auto) → if clean, commission a **focused re-verify of the changed P3 path** → then governance-close B3.
- Then the operator's **supervised live-proof** (report §4 runbook + the §4.4 HIGH-1 negative case) → clears B2↔B3.
- Operator commit-time: HIGH-2 dirty-tree staging decision; LOW-5 `.db.bak` ignore.
- B4 promo-seed; Betfair-entry flexibility scoping; natural-monitoring watch-list (post-B7); B5/B6.

## Session close state
Session-bound watcher stopped (triage deferred to open). bethub-v3 at `e2638fa`, worker OFF, no code in Chat, v2 untouched. Artifacts all in `bethub-rebuild/`. `current_state.md` rotated; `cutover_readiness_map.md` + `v3_build_picture.md` updated; `SESSION_225.md` written; S226 opening prompt generated with the confirmed auto-action. **Bet-safety CLEAN.**
