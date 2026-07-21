# Honest money reads — build report (B1, S244)

**Brief:** `honest_money_reads_build_brief.md` (grounded at `53a8585`).
**Built on:** `53a8585` → **`2e9abd3`**, 7 commits, pushed to
`origin/main`. All 8 scope items landed in the brief's sequencing order
(1 → 2 → 7 → 8 → 6 → 5 → 3 → 4).

**Suites:** backend `uv run pytest` **1511 green** (from 1481; +30 new
tests, 0 removed). Frontend `npx vitest run` **220 green** (from 215;
+5). `npx tsc -b` clean. Red-before/green-after proven on items 1, 5,
6, 7a/7b, 8.1 (failure reasons verified before each fix).

**THE PENDING STEP (operator):** everything below is
**implemented-not-live**. The app is still running the old code and the
served `dist/` was deliberately NOT rebuilt (standing S232 rule — never
rebuild the served frontend under a running app). Next app-down window:
`npm run build`, then restart. Until then the running app behaves
exactly as before this build.

---

## 1. What each item means for the betting day (live-integration bucket per item)

| # | Feature | Bucket |
|---|---------|--------|
| 1 | Credit guard reads the unbounded correlation path — double-credit / re-listing blindness past 1000 events is dead | implemented-not-live (backend; live at app bounce) |
| 2 | Promo event lists refuse silent windows — `limit` required at both layers | implemented-not-live (backend) |
| 3 | Bets-feed len-vs-total honesty: `limit` required in the TS client, burst-review truncation strip, standing rule in `ops/READS.md` + docstrings | rule/doc live now; UI strip needs dist rebuild + bounce |
| 4 | Money-movements fold-out says "latest 30 of N" + show-all | implemented-not-live (backend + UI) |
| 5 | Void detector count-checks + pages its window (still UNWIRED — B2 wires it) | implemented-not-live; stays dormant even after bounce |
| 6 | Manual resolution frees its reconciliation sweep slot (starvation class closed) | implemented-not-live (backend) |
| 7 | WON bonus-winnings bets now creditable + detected with the right whole-dollar amounts ($13/$33 class) | implemented-not-live (backend + UI) |
| 8 | Credit-gaps rows show where the runner FINISHED, verdict chips, one-tap "Dismiss N ran-outside" | implemented-not-live (UI + one backend field) |

**First racing day after the bounce — what changes on screen:** the
burst-review watchdog stops being placings-blind (each gap row grows a
"ran 2nd — CHECK BOOK" / "ran 5th — outside" / "?" chip and the owed
dollar amount), a WON bonus bet appears on the list with its owed $
and banks through the same one-tap door, and any >500-pending or
movements-window truncation announces itself instead of hiding.

---

## 2. Deviations from the brief (complete inventory)

**D1 — [operator-relevant / money] Kind-aware gate changes what a
bonus_winnings template can credit.** Before: ANY promo kind attached
to a settled-lost safety-net bet passed the credit-in gate. Now a
`bonus_winnings`-kind template credits ONLY on the WON shape. I
verified the real catalogue read-only: the two live bonus_winnings
templates ("TAB Bonus Winnings 25% to $100 (FB)", "Bonus Winnings
(Cash)") have never been credited through the settled-lost arm, so no
live behaviour regresses. A test fixture that had this mislabelled
(cash-25% template seeded `bonus_winnings` while testing the
settled-lost cash arm) was re-labelled `insurance` — the shape it
actually tests.

**D2 — [operator-relevant / money] Live-shape verification beyond the
brief.** The two real S244 bets (Sarie/Leigh class) were checked
read-only against the new arithmetic: both are `settled_won`, side
NULL, $50 @ 2.0 and $50 @ 3.6 → the new door/detector compute exactly
**$13 and $33** — the amounts TAB actually paid. Both already carry
correlation-stamped credits (hand-banked during S244 triage), so after
the bounce they will correctly NOT re-list; the next bonus win flows
through the door end-to-end.

**D3 — [dev-detail] Item 2 test-site list was under-counted.** The
brief named 9 bare test call sites; 6 more existed in the same files
(`test_promo_store_adapter.py` scoped lists, `test_promos_repository.py`
×3). All 15 now pass explicit bounds. No scope change — same fix class.

**D4 — [dev-detail] `npm run build` not run.** The brief's test plan
names it; the session constraint (app running, S232) overrides.
`npx tsc -b` served as the type gate — it is the same compiler check
without writing `dist/`. `git diff` confirms `ui/web/dist` untouched
across all 7 commits.

**D5 — [dev-detail] Item 1 "one-off data assertion" is a standing
test.** Implemented as a pytest that opens `data/bethub.db` READ-ONLY
(`mode=ro` URI) and skips when absent (CI). It ran against the real
store and **passed**: every triggered credit carries
`correlation_id = triggering_bet_id` (restore correctives exempt) —
legacy exposure zero, exactly as the brief predicted post 17-Jul reset.

**D6 — [dev-detail] Door/detector side-guard asymmetry (deliberate).**
The door refuses only an explicit `side='LAY'` (mirrors settlement's
single-inversion convention: NULL reads as BACK); the detector SQL
lists only `side IN ('BACK', NULL)`. A non-canonical side value (not
produced by any current writer) would be creditable at the door but not
listed by the detector — an under-list, never a wrong credit.

**D7 — [dev-detail] Item 5 `max_results` default changed** from 100 to
`MAX_CANDIDATES_PER_RUN` (500) with a hard clamp at 500 and offset
paging in batches of 100. Zero production callers (grounding-confirmed),
so no runtime behaviour changes anywhere.

**D8 — [dev-detail] Item 8.1 endpoint had NO existing tests.** New
module `tests/ui/api/test_bets_race_result.py` (4 tests: outside-top-4
red-before, placed runner, scratched runner, soft-miss discipline).

**D9 — [operator-relevant / operations, cosmetic] Watchdog section
retitled** "Watchdog — qualifiers owed a credit" (was "lost qualifiers
with no credit") and the empty-state line updated — the list now
includes WON bonus bets, so the old title would have been dishonest.

---

## 3. Findings (complete inventory)

**F1 — [money] The correlation stamp holds across the whole real
ledger.** 30 credit events live; the read-only assertion found zero
rows where a triggered credit lacks its `correlation_id` stamp. The
item-1 guard therefore covers every historical credit from the first
post-bounce request — no backfill, no migration, no window.

**F2 — [money] Dead-heat / removed-runner bonus wins have NO in-app
write path.** The door correctly refuses them ("settle this one by
hand" 422) and the detector lists them marked hand-settle — but the
only way to actually write that hand-computed credit today is the
adapter/seed path outside the app. Flagged as a B2 candidate (a
manual-amount credit door), not built here (would be a new promo write
surface, outside this brief's fences).

**F3 — [operations] Verdict chips need the template on the catalogue.**
A gap row whose serial has no catalogue row lists with
`promo_kind='unknown'`, no expected amount, no chip, and is never
swept — fails safe toward the operator looking at it.

**F4 — [operations] Truncation strips only fire past real caps** (>500
pending on burst-review; >30/200 movements). Day-to-day they stay
invisible; they exist for the day something grows past a cap — that
day now announces itself.

**F5 — [dev-detail] `vi.restoreAllMocks` does not clear `vi.fn()`
factory-mock call HISTORY** — a cross-test call-count leak surfaced in
the BurstReview suite; fixed with an explicit `mockClear()`. Worth
knowing for future vitest count assertions.

**F6 — [dev-detail] Making `BetFeedFilters.limit` required broke one
weak `Record<string, unknown>` cast in BetLog's generic filter setter** —
routed via `unknown` per the compiler's own suggestion; call sites
unchanged.

**F7 — [dev-detail] Item 5 paging note:** offset paging over a
newest-first order can shift page boundaries if rows insert
mid-sweep; the detector is read-only and unwired, and `window_total`
(counted at sweep start) + `truncated` absorb the honesty. Noted in
the module comment for the B2 wiring session.

---

## 4. Open questions (complete inventory)

**Q1 — [operator / money] Dead-heat bonus hand-settle path** — accept
adapter-side manual credits as the interim workaround, or commission
the manual-amount credit door in B2? (See F2.)

**Q2 — [operator / operations] BetRight ≤7 conditional stays
display-only.** The chip renders "ran 3rd — check terms (≤7 field pays
nothing)" and never auto-classes the row; the catalogue still cannot
EXPRESS the conditional (Cat-4 standing). The B2 catalogue-conditional
item remains open — nothing here pre-empts it.

**Q3 — [operator / operations] Sweep-slot backlog drain.** Item 6 fixes
the CLASS going forward; a bet ALREADY resolved-but-stuck from before
the bounce cannot free its own slot (manual resolution only fires from
PROVISIONAL, and it has already fired). I attempted a read-only count
of that stuck class in the live store but the DB was busy (WAL lock —
the app was writing; earlier read-only checks in this session
succeeded), so **this is unverified**. One-line check when convenient:
`sqlite3 "file:data/bethub.db?mode=ro" "SELECT COUNT(*) FROM bets
WHERE match_status IN ('provisional','provisional_pending') AND
settlement_state IN ('settled_won','settled_lost','voided');"` —
0 = nothing to drain; >0 = each row burns one sweep slot per 60s pass
until normalised (ask before touching).

**Q4 — [dev] Sibling adapter limit defaults** (bet_mutations / ops /
cash_flow) keep their silent `limit=1000` — named debt per the brief,
no bare money-path callers today.

---

## 5. Verification detail

Red-before/green-after (failure reason checked before each fix):

- **Item 1:** 1000 filler credits + real credit at #1001 → old guard
  returned None (blind) and a second credit WROTE (silent double) →
  new guard finds it, dedupe holds. Plus: revoked-credit-still-answers
  (locked contract) and correlation-stamp tests.
- **Item 5:** 105-bet window → old report saturated `swept=100` with no
  signal → now sweeps 105 (`window_total=105, truncated=False`);
  capped run reports `swept=50, window_total=105, truncated=True`.
- **Item 6:** manually-resolved stuck-PROVISIONAL bet stayed in
  `list_unreconciled_bets` → now excluded; FAILED/FINAL_PARTIAL/
  FINAL_FULL mapping proven; money values pass through byte-identical;
  terminal-match-status rows get no write at all.
- **Item 7a/7b:** the real Sarie/Leigh shapes — door 422 → 201 with
  "13.00"/"33.00" (ROUND_HALF_UP whole dollar, cents-serialised); cap
  binding proven; LAY / price-less / dead-heat / settled-lost all 422;
  detector empty → listed with expected $13/$33 → gone after credit-in;
  cash variant writes PROMO_CASH_CREDITED (7c).
- **Item 8.1:** 5-runner race, bet on the 5th → `placings` still caps
  at 4 but `selection_position=5`; scratched flagged; soft-miss intact.

Gates: `uv run pytest` 1511 green; `cd ui/web && npx vitest run` 220
green; `npx tsc -b` clean. `data/bethub.db` touched by READ-ONLY
queries only (mode=ro). Money-path fences held: settlement edits =
exactly the named `apply_manual_operator_resolution` insertion; no bet
money field written anywhere (item 6 passes existing values through);
promo spine append-only, no new event types; no raw SQL writes.

Commits (all pushed to `origin/main`):

- `eae7c11` items 1+2 — credit-guard window killed; required limits
- `32a7160` item 7 — winnings-shape credit coverage
- `4928a10` item 8 — placings on the credit-gaps list
- `85c2008` item 6 — sweep-slot hardening
- `1cb5bf4` item 5 — void detector count-checked paging
- `31b1ec6` item 3 — bets-API read honesty (consumer side)
- `2e9abd3` item 4 — movements fold-out honesty

## 6. Operator checklist for the bounce

1. App down → `cd ui/web && npm run build` → restart app.
2. Open burst-review: the watchdog should show ZERO owed qualifiers
   (the two S244 bonus bets are already credited — if either re-lists,
   stop and flag it: that would mean the dedupe read is wrong).
3. Next WON bonus bet: confirm the listed owed $ matches the book
   before banking (the whole-dollar rounding is TAB-ratified; other
   books may round differently — that is a terms observation, not a
   code assumption).
4. First gap-row chips: spot-check one "ran Nth" against the actual
   race result once, then trust the sweep.
