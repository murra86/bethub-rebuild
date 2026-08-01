# S247 downtime quality sweep — record + triage (Tue 21 Jul, morning)

Operator-commissioned background verification during the pre-thoroughbred
lull, race-day stack frozen throughout. Everything read-only.

## What ran

1. Full suites as-deployed: backend **1618/1618**, frontend **280/280**.
2. Store forensics on a copy: integrity ok, 0 orphans, all supersession
   chains whole, FB inventory 0 everywhere, all Betfair bets carry
   side, cash-flow reversal links whole. Baselines: S1 stale-leg
   residual = 23 rows; per-book balances captured
   (`scratchpad store_forensics_report.txt`, TOTAL $10,725.64) for
   tonight's reconcile. One LOW: float dust at 1e-13 in one derived
   balance (b4cb3fd6…) — a float enters the Decimal pipeline somewhere;
   invisible after cent-rounding.
3. Two independent read-only code reviews at HEAD `a195cf2`:
   S245 TAB fill path; S246 B2 doors/watcher.

## Review findings — TAB fill (S245 range 2e9abd3..f28a7ef)

- **T1 HIGH** — `captured_at` never checked/shown; stalled capture
  serves as live. Soft Odds feeds EV, watcher grade, AND lay sizing.
- **T2 HIGH** — dead/stopped live feed's last values permanently
  override fresher background values (react-query keeps data on error;
  also fires when the T-window closes on a DELAYED race).
- **T3 MED** — live window keyed to scheduled_start snapshot; fast
  feed stops at scheduled off on delayed races.
- **T4 MED** — fill can add/update but never clear: post-seed scratch
  or pulled price lingers until Betfair marks non-ACTIVE.
- **T5 MED** — auto-filled price reaches quick-lay through a DISABLED
  book-odds input; no in-modal correction.
- **T6 LOW** — softOddsLadder snaps long-shot rungs down (31→30 etc.).
- Clean: race/market cross-contamination, error-envelope-as-price,
  tz/date math, operator-edit protection, selection joins, timeouts.

## Review findings — B2 doors/watcher (S246 range f28a7ef..a195cf2)

- **B1 MED** — split hedge (2nd lay, same selection) unpairable by
  design fence; flags all day in burst-review/daily check. Money right.
- **B2 MED** — bank-pair deposit reversal needs `include_sibling` the
  UI never sends → Reverse always 422 on Tim-default deposits.
- **B3 MED** — small-field honesty ALLOW side uses log-click field
  size; post-log scratching → credit-gap lists money the book won't
  pay; a trusting credit-in tap writes it. (Refusal side always safe;
  EV picker uses live count.)
- **B4 MED** — void-detector flags have no clearing door; banner red
  up to 24h incl. after operator verification (Betfair "expected
  discrepancy" case) — folds into the void-gap build's flag-clear.
- **B5 MED** — once-per-qualifier / once-per-restore guards are
  read-then-write with NO DB unique backstop (no unique index on
  correlation/triggering/supersedes) — ms-wide double-fire windows =
  double credit. UI-mitigated today.
- **B6 LOW** — lay-first + unrelated same-runner back can auto-pair
  wrong cycle (visible + declinable; metadata only).
- **B7 LOW** — manual-credit NaN/Infinity → 500 not clean refusal.
- **B8 LOW** — FB expiry stamped from bank-tap time not book credit
  time (late banking overstates life).
- **B9 LOW** — pairing candidate labels round stakes to whole dollars.
- Clean: tripwire non-blocking + honest-failure, deposit paired-write
  amounts/signs/reversal-typing, re-class fences + no worker race,
  auto-restore mechanics, route shadowing, shield truth source.

## Race-day operator disciplines (briefed, in force TODAY)

1. Glance Soft Odds column vs the TAB app before every fill-based bet
   (T1/T2/T4 guard). On delayed races assume the fast feed is dead.
2. Mismatch or doubt → type the lay sizing yourself (T5).
3. Before tapping any credit-in the tool says is owed on a small
   field: check the FINAL field size vs the promo clause (B3).
4. Single deliberate taps on credit doors — no double-taps (B5).
5. A red banner from a settled-then-voided watch may stick after
   you've verified the account (B4) — note it, don't chase.
6. A second lay on the same selection will flag unpaired all day (B1)
   — cosmetic, ignore.
7. Bank any bonus the day the book credits it (B8). If a deposit is
   fat-fingered, DON'T retry Reverse (B2) — flag it for the evening.

## Proposed build triage (operator call at day close)

- **Tonight, TOP PRIORITY (operator-ruled S247): T2+T3 delayed-race
  fix.** Operator: "most races are delayed by at least 30s to a
  minute, and that is where a lot of the value is" — the fast feed
  must survive past scheduled off. Fix shape: key the live window off
  the race's actual state (Betfair market still OPEN / fresher
  scheduled_start_time from the 1s prices payload), not the sidebar's
  scheduled-start snapshot; and make live values lose to fresher
  background values instead of permanently overriding (per-value
  freshness, not per-feed priority).
- **Tonight (with the already-queued void-gap / FB single-source /
  float-flag / VPS daily-email items):**
  T1 staleness-visible; T5 editable box; B4 flag-clear folded into
  void-gap build; B5 DB unique backstop (small migration);
  B2 `include_sibling` plumbing (small).
## Pre-built in isolated worktrees (Tue morning — NOT merged, NOT
deployed; operator diff-walkthrough tonight before merge)

- Branch `s247-door-hardening` (worktree agent, base `a195cf2`,
  suites 1619/282 green + build clean in-worktree):
  `c1f3733` B5 — partial unique index on
  promo_events(supersedes_event_id), violation → clean domain 422s at
  all three doors; **bonus real find: the deploy door had NO
  already-superseded pre-check — a double-tap could double-SPEND one
  credit; index now refuses it**; manual/auto credit guards serialized
  via BEGIN IMMEDIATE (deliberately NO once-per-qualifier unique index
  — JSON-payload coupling + unverifiable-against-live-store migration
  risk; rationale in module docstring). All red-before proven.
  `4af0cd0` B2 — reverseMovement include_sibling plumbing + explicit
  "Reverse both" confirm naming both amounts; no backend change.
- Branch `s247-tab-feed-fixes` (worktree agent, base `a195cf2`,
  suites 1621/294 green + tsc build clean in-worktree; all red-before
  proven): `e235f5b` T2+T3 delayed-race — live window keys off prices
  payload (fresher scheduled_start_time; polls while market OPEN &&
  !in_play; stops at in-play), merge is per-payload freshness not
  live-over-background. `8cc00fc` T1 — stale column dims + amber
  "as of HH:MM:SS" (90s in-window / 10min outside; error-retained
  cache marked; operator-typed never dims). `fb41796` T5 — book-odds
  box editable, typed value owns the session; **latent bug found:
  empty/0 seed used to compute a NEGATIVE FB lay size — now
  null/disabled**. `6586fd6` FB single-source per brief + additive
  `fb_amount_drawn`.
  Walkthrough judgment calls: banked credits still deploy WHOLE
  (partial re-credit = separate build; confirm says "$X goes
  unused"); pending unbanked face DOES re-arm remainder; parity
  confirm fires once at Place Lay; multi-credit deploys ignore
  fb_amount_drawn; ConfirmCard path untouched (out of scope).

- **Next quiet session:** T4 clearing, B3 settlement-side live count,
  B1 split-lay pairing design, T6 ladder rungs, B7/B8/B9,
  float-dust hygiene, Soft-Odds "starts at T-60m" affordance on the
  race page.

## Operator decisions (Tue midday, all three closed)

1. **Partial re-credit of banked FBs: NO BUILD.** Books don't give
   change (TAB consumed the whole $13); the tool recording "$X
   unused" matches reality. Revisit only if a book ever keeps a
   remainder. ($5 rounding itself is deleted — any face value flows
   exactly.)
2. **Whole-card early capture: DECLINED — stays T-60m.** Operator:
   odds 1h+ out are too unstable to plan on; no promo rule fires that
   early; not worth daily proxy cost.
3. **Tonight's deploy scope: ALL OF IT** — walkthrough → merge both
   branches → gates → one app-down swap; then void-gap build,
   float-flag clear, VPS daily-email lull-awareness.
