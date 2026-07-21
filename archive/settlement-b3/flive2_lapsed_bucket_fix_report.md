# F-LIVE-2 LAPSED-bucket resolver fix — build report (S228)

**Run:** 2026-07-06 (S228), Adelaide-anchored per DR-021. Follows directly from `flive2_lapse_measurement_report.md` (same session; operator go-ahead "Build fix now").
**Outcome:** BUILT + 3-lens adversarially verified (ALL UPHELD). Suite **1350 → 1358 green**. Committed `2e22c5f`, pushed to `murra86/bethub-v3` under the git-autonomy guardrails. **Classification: LIVE-PROVEN (same session)** — app restarted on the fix at 14:12; the first reconciliation sweep (14:17) auto-resolved **all four** S228 measurement lays `provisional_pending → FAILED` / $0 in one pass (attempt 17), no parking, manual queue untouched (only S227's pre-fix park remains). §5 executed as planned.
**Anchor:** built on `7d221b7`; new HEAD `2e22c5f`. Money-path change (reconciliation resolver) — built under full discipline: red-before tests, class sweep, independent adversarial verify.

---

## 1. What was fixed

The S228 measurement proved a never-matched order is filed by Betfair under `listClearedOrders betStatus=LAPSED` within ~2 minutes of the jump (5/5), and never under `SETTLED` — the only bucket the resolver queried. So a lapsed lay could never auto-resolve; every one fell to the P4 park valve → manual queue (S227 Case B, and the four S228 measurement lays).

## 2. The change (3 source files, single choke point)

- **`workflows/bet_entry/v1/betfair_adapter.py` `get_cleared_order_state`** — queries `SETTLED` first (byte-identical path, fallbacks never touched on a hit — trap-tested); on miss falls back to `LAPSED`, then `CANCELLED` (the other never-matched-money bucket, per the S223 sweep-the-class rule; `VOIDED` deliberately excluded — matched-then-voided is already handled by market-settlement disambiguation). Fallback hits report summed `size_cancelled`. Any bucket read failure → `ReadUnavailable` — never a silent not-found off a failed read.
- **`workflows/bet_entry/v1/orchestrator.py` `ClearedOrderStateSnapshot`** — gains `size_cancelled: Decimal | None = None` (populated only by the fallback buckets; legacy constructions unaffected).
- **`workflows/bet_entry/v1/reconciliation.py` `_resolve_one`** — the existing `cleared_order_lapsed` → FAILED branch gains the **conclusiveness guard**: when `size_cancelled` is populated it must equal the bet's full requested stake; any partial shape (e.g. a matched fragment the read didn't see) carries forward with new reason `cleared_lapsed_size_mismatch` to the park-valve backstop. HIGH-1 preserved: no path terminalises possibly-matched money; every uncertain shape degrades toward manual review.

The park valve is unchanged and remains the backstop; it just stops catching the common case.

## 3. Tests (8 new; red-before proven)

Bucket-fallback (LAPSED, CANCELLED), settled-hit-skips-fallback (a 500-trapped LAPSED route proves the settled path never pays the extra calls), fallback-read-unavailable, multi-row `size_cancelled` summing, LAPSED-row-with-settled-money lock-in (Betfair-reported settled money is booked, never FAILED), full-stake lapse → FAILED, size-mismatch → carry-forward. Red-before independently re-verified by the test lens against a pristine `7d221b7` copy: **5 of 6 first-wave tests behaviourally red** (the settled-skips lock-in also failed pre-fix, but only on the new field's absence — scaffolding, not behaviour; my in-session claim of "4 red / 2 lock-in" was inaccurate on that count and is corrected here). Suite 1358, zero skips.

## 4. Adversarial verification — 3 independent read-only lenses, ALL UPHELD

1. **Money-correctness** (attack: make it FAIL a matched bet) — no reachable path. The sharpest race (partial match then lapse, pre-settlement: matched fragment not yet in SETTLED, LAPSED row present) is exactly what the guard catches — partial `size_cancelled` ≠ requested → carry forward. Decimal comparison exact end-to-end (TEXT round-trip, no float leg); strict equality fails toward carry-forward.
2. **Blast-radius** — one production call site; settlement resolvers confirmed clean of any cleared-orders/SETTLED assumption (class sweep complete); no exhaustive reason-code matcher breaks; REST cost bounded (extra calls only on the absent+SETTLED-miss tail); diff surgical.
3. **Test-integrity** — real adapter under test, routing collision-free, both trap tests proven non-vacuous, counts reconcile. Its two coverage flags (multi-row summing; LAPSED-with-settled-money) were closed with the two extra tests before commit.

## 5. Live-proof plan (next launch — the ride-along)

The four S228 measurement lays sit `provisional_pending` / `pending` in the live store with their LAPSED records confirmed present on Betfair's side. On the next app launch (reconciliation worker on), the first sweep should resolve **all four to `FAILED` / $0 automatically** — reason `cleared_order_lapsed` — leaving only S227's already-parked bet in the manual queue. That single observation live-proves the fix end-to-end with zero new bets. Watch alongside: promo screen stays clean (F-LIVE-1 re-confirm) and **R-B** (§6) if any partial-lapse bet ever arises.

## 6. Residuals (parked, non-blocking)

- **R-A (LOW, latent, unreachable today):** `place_hedge` places `proposed_stake` but records `requested_stake` with no invariant tying them — a divergence could theoretically defeat the full-stake guard. No production caller exists (quick-lay uses one value for both). Add a one-line invariant if `place_hedge` is ever wired.
- **R-B (assumption, confirm opportunistically):** the guard assumes Betfair's `sizeCancelled` is the lapsed portion only on a partially-matched bet (per docs; the 5/5 measurement covered full lapses only). First live partial-then-lapse observation closes it.
- **R-C (cosmetic):** carry-forward decisions tally under the `left_provisional_read_unavailable` counter regardless of reason (pre-existing naming drift).
- **R-D (pre-existing, unchanged):** a mismatch-carried bet re-pays the 3 cleared reads each pass until the park valve (settlement-worker-gated) bounds it — same loop class as the existing inconclusive carry-forwards.

<!-- F-LIVE-2 FIX BUILT (S228) — LAPSED/CANCELLED fallback + full-stake guard; suite 1358; 3-lens UPHELD; commit 2e22c5f pushed; live-proof = next launch auto-FAILs the 4 measurement lays; residuals R-A..R-D -->
