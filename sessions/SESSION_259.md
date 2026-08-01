# SESSION 259 — twin-row permanent fix (0l) built, reviewed, deployed, repairing

Opened: 2026-07-29 ~20:15 ACST · build/deploy through 2026-07-30 ~00:40 ACST
Governing: DR-034 (executed), DR-035 (respected — no schema changes),
W7b write bans, RC-2 horse-identity principle, S189 live-proof taxonomy.
Operator directive: "Plan the twin-row fix, then execute adversarial
sub-agent reviews. If all clear - proceed. Only come back to me if my
guidance/decision required." No decision points arose; none raised.

## 1. Session open (standing checks)

VPS health all clear. RACING ALERT sweep: 9 overnight "Stamped coverage"
alerts all the kensington twin fragments (this session's target); one
self-recovered playup book-frozen alert (S257 pattern, no action).
Opened with the S258-directed pending-items summary + refreshers.

## 2. Evidence pass (live DB census, read-only)

- 8,876 markets all-time on >1 race row (first 2026-03-04).
- Since Apr: 6,534 date twins / 214 date+venue / 56 venue-variant /
  7 race-number (by market). Data split BOTH ways across twins (stamps
  old row, TAB snaps new row) ⇒ merge, not pick-a-winner.
- 63 same-date twin markets since Apr; 30 double-tracked on Betfair
  (the S258 Randwick R3 data-loss class).
- KEY FINDING: **zero new date twins since 15 Jul** — S238 W7 already
  killed the date generator. Live generators remaining: venue-variant
  class (collector normalised Betfair event.name while the sweep used
  event.venue; per-book venue spellings; no kensington/surface aliases)
  + the tiny race-number class. This shrank Layer B (no new date rule,
  no state→tz table needed; subscription writer no longer twins post-W7
  — B7 hardening dropped as risk>benefit, recorded here).

## 3. Design + adversarial reviews

Brief `twin_row_fix_brief.md` (v1 → reviewed v2). Three parallel
adversarial reviewers (repair-safety / write-side / read-side+governance),
verdicts 3× SAFE WITH FIXES; all accepted fixes integrated into v2 §8
changelog (blockers: horse-identity guard on every cross-fragment bridge;
donor-runner disposal + FK ON + orphan gates; terminal fence by market
age not date; B6 fence; B5 merge-on-refusal). Governance reads confirmed
by review: capture repair is 0l-commissioned and not bound by the v3
operator-present reset rule; fix-7 fence superseded by the commission
(citation corrected to archive/dirs/dr029/.../surgical_fix_7_design_brief.md:228).

## 4. Build (capture repo commit `6566641`, 18 files, +2838/−122)

- **Layer A (racing-api)**: `api/market_resolution.py` — shared DR-034
  fragment resolution + cross-fragment runner union under the identity
  guard (≥50% robust-name overlap gate both sides ≥3 names, fail-CLOSED;
  per-runner name agreement; scratched-OR; rank-preferred selection
  conflicts, audited). Both soft-odds routes + results by-market rewired.
  Built by a sub-agent to spec; red-before (6 new tests failed on old
  code); EXPLAIN no-scan guards extended.
- **Layer B (collector)**: `storage/race_resolve.py` shared market-id
  first resolver (twin-pick shared with identity_sweep — cannot diverge
  again); `_persist_race` adopts by market id, ALL post-adoption writes
  by row id, fill-if-null, identity columns untouchable; Betfair venue
  from event.venue (fallback via the date-suffix extractor, never raw
  event.name); BETFAIR_VENUE_ALIASES += kensington/randwick kensington;
  surface suffixes (synthetic/poly/polytrack) promoted into
  normalise_venue; one tracker per WIN market (`_find_tracked_market`),
  refused registration MERGES book ids + late catalogue-name backfill
  into the survivor; IntegrityError → tracker dropped + discovery forced
  (no capture gap); runner stamps fill-if-null-or-same.
- **Layer C**: `storage/twin_merge.py` core (identity gate; name-mapped
  fills; payload-less S:-keyed strangers dropped-to-journal — trial
  signature; N:-keyed card runners always move; child re-point across
  betfair_snapshots/bookmaker_snapshots/snapshot_batch_summary/
  betfair_historical with collision fallbacks; final-flag normalisation
  preferring the BSP-bearing set; race-row fill-if-null coalesce; full
  pre-image + child-manifest journal `race_row_merges`, same
  transaction; terminal fence 6h) + `scripts/merge_market_twins.py`
  driver (disk gate 2×DB, WAL checkpoints, Adelaide deadline abort,
  resumable, orphan-scan exit gate). B6: identity sweep now runs
  `merge_recent_twins(window=14d)` each pass, FK ON, counters in the
  sweep summary.
- Deviation from DR-034 §B.7 letter, recorded for DR-036: canonical
  completeness ranks stamped selections ABOVE raw runner count (raw
  count rewards trial-contaminated fragments — surfaced by a red test).
- Tests: 252 passed (54 new, red-before verified via path-limited stash
  for Layer B; agent-reported red run for Layer A; sabotage/rollback,
  crash-resume, idempotency, gate/fence tests for Layer C).

## 5. Deploy + live proof (evening, no races within 40 min; collector
was already past its 19:00 stop — new code loads at the 08:30 start)

- Pushed VPS + GitHub; racing-api restarted, /health 200/9ms.
- **Layer A live-proven pre-repair**: GET soft-odds 1.260470533 (the
  market that served runners:[] all Tuesday) → 8 runners, stamps + TAB
  prices + the scratching flagged.
- Backup `capture.db.bak-s259-pre-twinrepair-20260729-122248` (4.8G,
  integrity ok, 106,916 races).
- Dress rehearsal on a copy: 1,061 markets merged (incl. the heaviest
  Mar/Apr double-collected class), orphan scans all zero, ~4-7s/market
  measured → full history ≈ multi-night. Rehearsal stopped after proof,
  copy deleted (review rail).
- **Canary (live DB, ≥20 Jul): 55/58 merged, 1 skipped_live (fence
  working), 2 skipped_gate — Wagga greyhound "race-number twins" with
  0% name overlap = mis-stamped market ids, NOT twins; parked for
  review. Orphans zero. Randwick market now ONE row, endpoint re-proven
  post-merge (8 runners).**
- Full-history run launched (`logs/twin_repair_full_s259.log`,
  run_id repair-20260729-*), deadline 04:30 ACST, resumable across
  nights; merged markets leave scope so re-runs converge.

## 6. Night-1 repair result (04:30 deadline abort, by design)

2,732 markets processed in 4h04: **2,530 merged, 202 gate-refused**
(the mis-stamped-market-id class through history — the guard refusing
to merge non-twins; they stay in scope and re-skip each night, so the
final census target is "remaining == gate-refused set"). Orphan scan
all zero. 6,291 markets remain. **Night 2 scheduled on the VPS:
transient timer `twin-repair-n2.timer`, fires 30 Jul 14:15 UTC
(23:45 ACST), deadline 04:30, log `twin_repair_full_s259_n2.log`.**

## 7. Open items out

- Nights 3+ as needed (same systemd-run pattern) until census
  converges; then re-run the S259 census queries and file the numbers.
- Review-list brief: ~200 gate-refused mis-stamped markets (incl. the
  Wagga greyhound pair 1.260468539/69) — separate small worklist item.
- First B6 self-heal counters appear in the 05:50 sweep log.
- model.db re-extract note (parked research; race ids pre-date merge).
- Live proof next Kensington/synthetic meeting: TAB column populated.
- SSH ops lesson: long remote jobs run nohup+logfile (a piped tail died
  with the SSH session mid-rehearsal; process survived, log pattern now
  standard).

## Carry-forward

S258 queue unchanged otherwise: Mango deploy (operator-present),
~8 Aug race-day batch, optional historical bonus-winnings EV recompute /
S231 haircut into code / "change promo" button idea.

## 8. Independent verification round (30 Jul morning, operator-directed)

Two fresh sub-agent verifiers over the shipped work and the completed runs.

**Data-integrity reconciliation (live DB vs pre-repair backup): DATA
INTACT.** Conservation exact to the row: races 106,916−2,632=104,284;
runners 630,246−22,916 (22,914 name-mapped + 2 payload-less S: dups,
both verified empty); betfair/bookmaker/historical snapshot totals equal
the backup EXACTLY (zero lost; dup_children_dropped=0 on all 2,632
journal rows). Journal reconciles all three runs to the second; orphan
scans genuinely zero; gate-refused markets byte-identical to backup; no
rehearsal traces. Corrections it caught: (a) **Pinjarra 1.259600429 is
NOT yet merged** — night 1's deadline stopped before it; brief-invariant
claim corrected here, it sits in the night-2 backlog; (b) Randwick keeps
a THIRD market-id-less fragment (row 3406578, ladbrokes-keyed, 520 book
snapshots) — the out-of-scope shell class HOLDS REAL DATA (data-reset
thread evidence); (c) **12 merged date-twins united contradictory result
sets** (each fragment a different full result — mis-stamped results,
pre-existing; both sets + pre-images preserved; 82 more such races had
the duplicates already on one row pre-repair, 1,819 DB-wide = capture-
quality issue, not merge damage).

**Post-build adversarial code review: no blockers; FIX BEFORE NIGHT 2 —
done.** F1 settled-count now GATES pre-write (skip-to-review; was
audit-after); F2 final-flag keeps the most-BSP set (was latest-with-BSP);
plus result-conflict gate (catches the 12-races class when field_size is
NULL; consistent dead-heats still merge), nameless key-collision kept
distinct, batch-summary orphan scan, cross-code refusal in
resolve_by_market, driver refuses >12h deadlines. Commits post-`6566641`
pushed before the night-2 timer. 256 tests green.

**F2 retro check: zero damage.** `refix_final_flags_s259.py --dry-run`
recomputed all 2,136 normalised final sets from the backup: old and new
rules chose the SAME set in every case (refixed: 0). No retro mutation
performed; script retained in repo as the audit trail.

**Review-list item (needs its own small brief):** ~200 gate-refused
mis-stamped markets + 74 settled-excess audits + 12 contradictory-result
races (journal pre-images) + market-id-less data-bearing shells
(Randwick 3406578 exemplar).

## 9. Quiet-sitting continuation (30 Jul morning): 0m built + dry-run,
current_state refreshed, race day moved to LIKELY SAT 1 AUG

- Worklist reviewed with operator: stale closures (0j/settled-edit/B2
  watch), 0m + 0n added; priority = repair auto-completes → Sat 1 Aug
  batch → quiet queue.
- current_state.md refreshed (S258+S259 delta; was S257-current, the
  "6 sessions stale" worklist note was itself stale).
- **0m BUILT under its own mini-brief + adversarial review
  (twin_reviewlist_brief.md, SAFE WITH FIXES — all integrated incl.
  chimera-payload quarantine, S1 corroboration floors, venue-local tz
  pinning, age fence).** `scripts/reviewlist_correct.py` (+6 tests,
  262 suite green, capture pushed). DRY RUN on the FULL census:
  6,244 twin markets → 5,646 real twins (tonight's repair), 598
  refused-class pairs → 208 would CLEAR / 390 LEAVE (221 no unique
  keeper, 56 three-fragment, 107 S1-only failing floors, 6 age fence).
  LIVE RUN DEFERRED until the nightly repair converges (review F6) —
  next session action.
- Report-only extracts filed: 452 duplicate-position pairs across 94
  merged canonicals (`twin_reviewlist_extract_s259.txt`; the
  12-merge-introduced subset included) + 73 settled-excess audit
  lines (both = mis-stamped results class → 0m follow-up/0n; ORDER:
  classify/exclude BEFORE any model.db re-extract or historical EV
  recompute).

## 10. 0i BUILT (30 Jul, v3 `ff44007`) — clear releases the box, owned
boxes marked

Sub-agent build to spec under house rules, reviewed + gated by me
(diff review, scratch vite build; served dist untouched — live at next
app start via the launcher's app-down rebuild). Mechanism mapped:
ownership = operatorTouchedRef set on every soft-odds commit in
Racing.tsx, checked by the feed-seed and book-switch-blank effects;
CLEAR previously marked ownership too = the dead-box trap. Now: real
price (>1) owns (never auto-released — operator numbers are never
silently reverted, per the S250 rejection); CLEAR releases (feed
re-seeds next tick). Subtle navy accent + hover note on owned boxes,
TAB book only. Red-before (4/6 new tests failed old code); 480 vitest
(+6), tsc clean. Operator walkthrough at next app start: type a price
→ navy accent, feed stops touching it; press CLEAR → box hands back
to the feed within a tick.

## 11. Relaunch blocker fixed (30 Jul ~10:25) — latent tsc -b errors

Operator's app relaunch failed at the launcher gate (`tsc -b && vite
build`): two type errors in ConfirmCard.test.tsx, latent since
`e63e7d3` (S258 EV fix) — mock missing `success`, `promoEvForStake`
absent from the test's snapshot type. Not from 0i (different files),
but today's checks SHOULD have caught them: vitest doesn't typecheck
and `tsc --noEmit` resolves a narrower scope than build mode. Fixed
`70ee141` (tsc -b exit 0, 480 vitest), pushed. LESSON (memory
updated): the only valid v3 frontend gate is the launcher's own
`tsc -b && vite build` — never --noEmit or vitest alone.

## 12. Decodo quota outage (30 Jul ~10:10-11:10 ACST) — diagnosed,
restored, hardened

Operator's confirmation run surfaced a stale TAB column (108m).
Diagnosis chain: live-soft-odds 503 live_pools_hot → hunt-exhausted
log storm → collector "CONNECT tunnel failed, response 407" → direct
proxy test with configured creds FAILED → Decodo dashboard: 3GB plan
at 3/3 GB, 7 days to renewal. NOT a TAB block, NOT the twin fix, NOT
fingerprints. Root cause of the root cause: S255 daily sweep + S257
dual live sessions lifted usage to ~200-300MB/day ≈ 7GB/mo pace on a
3GB plan — under-provisioned since those builds.

Operator upgraded to 10GB (PayPal; dashboard lagged the payment ~15m
but the gate authenticated). Recovery: racing-api bounced (benches
cleared), collector breakers self-reset, live endpoint 200 with fresh
prices mid-card.

Hardening SHIPPED same hour (capture pushed + api bounced):
ProxyAuthError — a 407 from the gate short-circuits the TAB hunt with
the real reason (was: misread as worn fingerprints, burned the full
rotation); liveness gains check_proxy_auth (~1KB probe, named alert
naming every proxied book). Probe verified live ("Decodo proxy
authenticating"). Collector loads the tab.py change at tomorrow's
start (protective-only). FOLLOW-UP filed: traffic-diet review (size
compression/cadence wins with real numbers; never silently trade S257
latency). Also of note: today ran the twin fix's first live day —
today's card created CLEAN (Gatton R1 single row, market id + TAB id
+ stamps on one row).

## 13. Manual Bet page (operator-commissioned this sitting, v3 `a8ff45f`)

Operator ask: combine Log Past Bet + Other Bet into one "Manual Bet"
page — with a confirm-first fence if non-trivial. Scoping verdict:
genuinely simple (both pages self-contained, nav-linked only, separate
endpoints untouched) — proceeded per instruction. Build: /manual-bet
wrapper with a Racing (past bet) / Other (non-racing) toggle rendering
the EXISTING forms untouched; mode carried in ?mode= (refresh-safe);
legacy /log-past-bet and /other-bet redirect with mode preserved; nav
one entry. Post-implementation review inline (small surface, child
forms untouched — their own suites keep guarding the money paths):
mode switch drops in-progress fields, same as the old page-to-page
navigation; noted for the walkthrough. Red-before (module-absent);
485 vitest / tsc -b / scratch build. LIVE at next app start.

## 14. Exit closes the tab (operator-commissioned this sitting, v3 launcher)

Operator ask with a confirm-first fence — and this one NEEDED it: a
web page cannot close its own tab (browser policy), so the obvious
window.close() would silently do nothing. Operator chose the reliable
route via AskUserQuestion: the launcher (runs ON the Mac) closes any
Chrome tab on localhost:$PORT via AppleScript after a clean port
release. Guards: skip when a newer BetHub holds the port; skip when
Chrome isn't running (a bare tell would LAUNCH it); index-descending
close. One-time macOS "Terminal wants to control Chrome" prompt on
first use (operator briefed); non-Chrome = old exit screen, nothing
worse. Shape dry-tested against live Chrome with a no-match URL.
TAKES EFFECT from the NEXT launch (the currently-running launcher is
the old script) — so the second exit from now is the first that
closes the tab.

## 15. Manual Bet layout revision + tab-close debug (operator, same
sitting; v3 `69db439`)

Layout: toggle DROPPED — both forms stacked (Log Past Bet then Other
Bet, own headings, thin divider); no id collisions between the forms
(checked); legacy /other-bet redirect scrolls to its section. 483
vitest / tsc -b / scratch build.

Tab-close "still not closing": mechanism PROVEN end-to-end from a test
context (marker tab opened, the launcher's exact block closed it) —
the script is sound. Remaining suspects: (a) the exit tested was the
still-running OLD-launcher session (started 10:55, pre-change), or
(b) macOS Automation permission silently denied. Errors were being
swallowed — now logged to ~/.bethub/tab_close.log (-1743 = grant
Terminal→Chrome in System Settings > Privacy & Security > Automation).

## 16. Promo-credit correction class — verb BUILT + RAN LIVE, undo
button SHIPPED (v3 `329c42f`)

Operator hit two instances in one afternoon of ONE class: *the credit
banked isn't the credit the book gave*. (a) Sarie/TAB insurance logged
against "Ins $25 Cash 2nd" when TAB paid a FREE BET — tool overstated
cash $10, understated FB $10. (b) Tim/PointsBet $25 FB credited off an
insurance that never triggered, with no undo in BetLog.

Diagnosis for (a) found THREE design locks blocking every existing
door (cash credits unrevokable; balance derivation ignored
supersession; re-crediting a locked contract; the S254 correction CLI
refuses cash chains). Operator chose "build the proper fix" with
reviews at both ends.

**Planning review returned UNSAFE-AS-WRITTEN** and found the thing I
missed: a SANCTIONED cash-revocation shape already exists (a
superseding `promo_cash_credited` with `status='rejected'`, S130 Cat-5,
recorded on the payload model, TWO consumers already reading it). That
made the build smaller (no enum/schema/adapter change) and killed my
`free_bet_revoked`-reuse plan (which the store adapter would have
refused anyway). Also caught: the atomicity claim was false against
the real writers (every adapter write commits) → adopted S254 §3d
raw-insert discipline; `credit_source='correction'` isn't a valid enum
member; the amount formula diverged from the door (insurance passes NO
cap) → extracted a SHARED kind-aware helper both call; and the
money-read change had to be LOCKSTEP across balance_derivation AND
pnl_dashboard or the Balances self-check (exact-zero equality) renders
a false mismatch.

**Post-execution review returned FIX FIRST** (rehearsed the exact run
on a byte-exact snapshot first): (1) the docstring claimed a
`bet_edited` audit row the code never wrote → now raw-inserted in the
same txn, FAILS CLOSED (reassign-door contract, regression-tested);
(2) the new cash guards ignored superseded but not REJECTED terminals,
which would have locked the corrected bet out of the wrong-account
doors forever → status filter on both + the verb's own live-credit
query (also enables a SECOND correction). Attacks that did NOT hold:
atomicity (statement-traced), crash-safety (hard kill mid-txn leaves
the store untouched), door-refactor identity, lockstep, FB
spendability.

**LIVE RUN 30 Jul ~15:05 ACST** (backup `…-pre-cashcorrection-
20260730-135352`): Sarie/TAB cash 1163.90 → 1153.90, FB inventory
0 → $10.00, bet on "Ins $25 FB 2nd", audit row written, live cash
credits 0, daily money check clean.

**0q undo button SHIPPED same commit**: surfaces the S243 revoke
engine that had no caller. Offered only for a live UNSPENT bonus
credit; cash and spent credits get a plain explanation instead of a
failing button. Sub-agent found a third state I hadn't specified —
after a spend is RESTORED the qualifier's credit is permanently
un-revocable (the live replacement carries the deploying bet's
correlation), so the action is withheld rather than offered-and-failing.
Gates: 1948 pytest / 489 vitest / tsc -b / scratch build.

Follow-ups filed: **0s** (verb hardening before any CROSS-KIND re-type
or button wiring: settlement guard under the lock, fb_expiry_days
ignored, door kind-gates not re-applied, BetLog paid-marker counts the
rejected terminal). Records: `promo_selection_correction_brief.md`.

## 17. Accounts consolidation (0r) SHIPPED — v3 `414148a`

Operator spec followed exactly: one tab "Accounts", Balances on top in
its current format, account setup below restyled to the Balances
language, "Balances" nav entry removed. Wrapper renders both existing
route components untouched (their suites are the behaviour guarantee).
Two judgement calls beyond the spec, both recorded: (a) the /balances
redirect CARRIES search+hash — a literal `<Navigate>` would have broken
the post-registration `?deposit=<aab>` deep link that opens the deposit
card (agent caught it, tested both ways); (b) Balances' standalone
`min-height: 100vh` is neutralised IN THE WRAPPER ONLY — measured live
at 1406px content vs a 1359px viewport, so it is marginal today but
would leave a blank band whenever the money picture is short (hidden
books, fewer holders); Balances' own stylesheet and format untouched.
The Accounts half previously painted the GLOBAL cool-dark tokens on a
white body ground — stacked, the two halves clashed badly; it now
paints the same warm slab with Balances' card/heading/row/chip
treatments mapped element for element.

## 18. P&L question (operator, 30 Jul) — answered, gap filed as 0t

Operator noticed the today-filtered BetLog P&L did NOT move when the
$10 cash credit became a $10 free bet. Traced: `_period_stats`
(bets.py:1076-1140) folds ONLY `bet_net_pnl` over bet rows — no promo
term has ever been in that number. The Balances dashboard P&L is a
different number (settled_pnl + promo_cash) and DID move: promo_cash
10.00 → 0.00, bonus_value +$10 (now $35 / 2 FBs), self-check 0.00.
Money correct; the gap is display. Material because the insurance
strategy's qualifier LOSES and the value returns as a credit, so the
BetLog daily P&L systematically understates promo days (today: +$3.10
while ignoring $10 of FB earned). Filed 0t with three options
(promo line / relabel "bet P&L" / both) — operator decision on shape.

## 19. International thoroughbreds (0p) — ASSESSED, decisions pending

Operator commissioned it mid-session ("no differentiation from AU
thoroughbreds — just another class of race"; driver = more promos than
anticipated), directing assessment-first with the standing autonomy.
Assessment delivered: `international_thoroughbreds_assessment.md`.

**Verdict MEDIUM-LARGE, and it is a CLEANUP not a greenfield build.
Headline: international racing is ALREADY IN THE SYSTEM and nobody
decided that** — arrived ~20 Jul (~10x step change); 1,108
international races polled in 14 days (MORE than the 1,044 AU);
**44% of proxied/Decodo-billed traffic**, i.e. the substrate of the
30 Jul quota blowout; and **zero usable output** (0/1,925 with a
Betfair market id, 0/1,515 finished races with a position, 0 BSP, 0
subscription syncs). Un-loggable by design (DR-032 §6, 4 layers).

My pre-assessment risk read scored 6/8 confirmed, 1 worse mechanism,
1 REFUTED — recorded in 0p so the corrections stick. Notably the
19:00 stop-hour concern was WRONG (international keeps trackers alive;
the collector already runs ~20h/day) and the date bug's live path is
the orchestrator's Sydney-today stamp, not the tz fallback.

Phase 0 is UNCONDITIONAL (worth doing even if 0p is dropped): per-book
jurisdiction coverage model, feed it to liveness, fix the date stamp,
retire the 19:00 assumption. Ordering constraint recorded: R2 (country
identity) MUST precede R4 (Betfair international discovery) or
`state_from_timezone` stamps every foreign race "AU".

7 operator decisions (D1-D7) pending — D1 (proxy plan) blocking, D2
(which jurisdictions) needs operator knowledge of where the promos
actually are. 3 cheap unverified facts could reorder the plan.

## 20. International Phase 0 — BUILT + DEPLOYED (capture `02e148f`,
`1dafcc3`, `fd115fd`, `ec604d0`)

Operator settled D1/D3/D4/D5/D6/D7 on my recommendations; D2 = UK pilot
(jurisdiction set built as CONFIG — `jurisdiction_config` seeded AU=on,
GB/IE=off, so scope is a row flip; my UK+IRE recommendation stands and
IE is literally one row). I settled **D8** myself (defer the race_date
flip to Phase 1) and the pre-build probe PROVED it right: TAB files
overseas meetings under the AU CARD DATE — Sandown Park UK and
Leicester ran 29 Jul UK time and sit on TAB's 30 Jul card — so flipping
race_date would have asked TAB for a date the race is not on, and a
cutover twin on a market-LESS race is invisible to race_resolve,
twin_merge AND the nightly self-heal (all need a market id). Phase 0
adds `local_race_date` alongside instead; Phase 1's flip is now
dry-runnable.

**CORRECTIONS to my own S259 assessment (recorded so they stick):**
(1) **The 19:00 stop hour DOES fire — 10 times, and on 29 Jul the
collector was down 10h39m (21:52→08:30), the entire overnight
international card, silently.** My earlier "REFUTED" read was wrong; it
was based on one log line. This is the biggest operational fact in 0p
and is what commit 1 fixes. (2) The date stamp is NOT regenerating the
twin class — two censuses over 21 days found ONE true twin among
market-less races, and it is Australian; the real defect is card
fragmentation (Windsor GBR 20 Jul: races 1-5 on one date, 6-7 on the
next), a display bug. (3) The 30 Jul 01:30 "book frozen" email was a
**TRUE POSITIVE** (the Decodo 407 outage began 00:42) — designing the
watchdog to silence that class would have silenced a real outage; it is
now a unit test. (4) `state='AU'` appears on 0 of 104,822 rows ever, so
the state_from_timezone fear was theoretical.

**Build findings beyond the brief:** the TAB mnemonic bug is worse than
described — TAB lists the same track TWICE on one card (once with a
mnemonic, once without), both normalise to one venue key, and the
mnemonic-less copy came SECOND and **overwrote a working race id**
(live 30 Jul: delaware, galway, thistledown, wolverhampton). Country
map errors caught: SAU→SA would have collided with South Australia
(335 rows), the data uses HK not HKG, MB (Assiniboia Downs) was
missing. The 04:05 recompute could never have run (inside the repair
window) — second fire added at 04:35.

**Deploy (16:30 ACST, 0 races within 25 min):** pushed VPS + GitHub;
migrations applied live (2 nullable columns + 3 tables, additive, no
rebuild, no lock); collector restarted clean; 2 new timers installed
and enabled (coverage recompute 04:05+04:35, gap-aware restart
04:15-05:30 every 5 min). Liveness ran green INCLUDING the new
heartbeat ("1638 snapshots across 15 servable NEAR races in 20m").
385 tests (from 262). Restart wrapper dry-run behaved conservatively
(already handled today → no-op).

**Known-and-intended for the next 24h:** coverage suppression is INERT
until the first recompute (so the 404 reduction cannot be read before
tomorrow, and only if the twin repair has cleared by 04:35); the
heartbeat is deliberately loud from its first run; `au_suppressed` in
the recompute log MUST read zero (non-zero = build failure, kill switch
`COVERAGE_SUPPRESSION_ENABLED=0` + restart).

## 21. SESSION CLOSE — operator directives for S260

Operator closed the session with three commissions, in priority order:

**1. INTERNATIONAL PHASE 1 — the FIRST action of S260.** Same approach
as everything else this session: sub-agents for planning AND
implementation, adversarial review at both ends, return only for
guidance/decisions. Context the operator has already been given: UK
races (30 today) ARE being captured but CANNOT appear in the tool
because none carry a Betfair market id, and the tool's
`collapse_fragments` drops market-less rows before display — the
Betfair market is the spine. Phase 1 = turn on Betfair international
discovery, but ONLY AFTER the country identity work lands (the ordering
lock: flipping GB=1 first would have `state_from_timezone` stamp every
foreign race AU). D2 remains UK pilot; GB is a `jurisdiction_config`
row flip; IE one row away (my UK+IRE recommendation stands, unanswered).

**2. DETAILED BET-BY-BET REVIEW (sub-agents, detailed).** Operator's
words: *"a detailed review of every single bet in the tool"*;
confirmation that *"every single insurance bet and free bet has been
grouped or linked in its full journey"*; that *"every bet in the tool
has a story that makes sense and has the right shape"*; and that
*"everything in terms of data integrity and tracking and oversight is
working properly"*. Motivation: *"We've done quite a few tweaks and
changes so I want to make sure that data integrity has been maintained
and things are actually being tracked and followed properly even with
all the changes."*
**NOTE THE OVERLAP: this IS the audit half of 0t (cycle accounting).**
0t's acceptance bar is "100% of cycles accurately tracked" = audit +
repair + ongoing invariant. This commission delivers the AUDIT; the
repair and the invariant remain 0t. Run them as one piece of work.

**3. REVIEW OF EVERY CHANGE MADE THIS SESSION** — *"appropriate,
rigorous, and correct and they won't lead to any risks or disruption or
downstream issues."* Scope = the full S259 commit set across BOTH
repos: capture `6566641`, `2e33bff`, `02e148f`, `1dafcc3`, `fd115fd`,
`ec604d0` (+ the earlier proxy-auth commit); v3 `ff44007`, `69db439`,
`dbebdec`, `02442f0`, `329c42f`, `414148a`, `0b235cd`. Include the LIVE
DATA ACTIONS, not just code: the twin merge (2,530+ markets), the
promo-selection correction run, and the Phase 0 migrations.

Sequencing note for S260: Phase 1 first (operator-directed), then the
bet review + change review. Both reviews are sub-agent work by
direction.

## 22. Session close state

Repos at close — capture `ec604d0` (VPS + GitHub, deployed, collector
restarted, 2 new timers live); v3 `0b235cd` (GitHub; LIVE at the
operator's next app start). Backups: money DB
`bethub.db.bak-s259-pre-cashcorrection-20260730-135352`; capture
`capture.db.bak-s259-pre-twinrepair-20260729-122248` (both verified).
Suites at close: capture 385, v3 1949 pytest / 494 vitest.

Session shape: opened as a standing-check + pending-items session, ran
~21 hours across two days, and closed having shipped the twin-row
permanent fix (0l) end-to-end with independent data-integrity
verification, a promo-credit correction class (verb + undo button) with
a live money correction, five operator-asked UI changes, the Decodo
outage diagnosis + proxy-auth hardening, and international Phase 0.
Six adversarial review rounds were run across the session; every one
found something real, and two (the promo planning review and the
post-execution review) changed the design before it touched money.

Honest record of my own errors this session, all corrected in-flight:
the "collector doesn't stop at 19:00" claim (wrong — it cost 10h39m on
29 Jul); the invented cash-revoke mechanism (a sanctioned one already
existed); a docstring asserting an audit write that did not happen; a
layout override that targeted the wrong element; the BetLog
rejected-terminal display bug that my own reviewer predicted and I
deferred rather than fixed (operator hit it first); and the "100
cycles" mishearing of "100% of cycles".
