# Standing worklist

Living document — the current open queue, one line of context each.
Older queue docs (`s242_s243_feedback_workplan.md`) are historical.
Updated: S263, 1 Aug 2026 evening — 0u deploy verified, 0t-A marked
shipped, 0m unblocked; statuses reconciled after the mixed-up S262
close-out.

## CURRENT ORDER (S260, 31 Jul — operator re-sequenced)

**Operator bumped the lay-matching fix UP (31 Jul).** It was inside 0t,
which sat behind 0p international. It now runs ahead of the Phase 1
deploy. Rationale it serves: every lay placed on race day currently
lands unlinked, so shipping it before Saturday stops the problem
growing rather than only cleaning up after it.

1. **0u — CAPTURE RESILIENCE: DEPLOYED; core objectives VERIFIED by
   adversarial review (S263, 1 Aug); post-deploy defects found + one
   fixed live.** Core: SUCCESS banner 04:27 ACST; both FK indexes built
   + probe-verified (root cause WAS the missing runner_id index, not
   lock policy); twin repair **DONE in 695s — 5,316 merged at ~7.6/s**,
   orphans zero, **ZERO db-lock errors** (grep validated against the
   30 Jul incident's 668); **TWIN BACKLOG CLEARED** — reviewer
   re-derived the census: exactly 679 remain, set-identical to the
   540 identity-gate + 139 settled-audit refusals (= the 0m
   population), no new twin since 28 Jul; rehydration exercised live
   21×, works. Review also found: **a 20-restart storm 18:57–20:30 UTC
   (deploy-script stamp bug: root-owned file + UTC-vs-Adelaide date;
   93-min post-deploy capture blank in the overnight dead zone)** —
   live stamp FIXED 1 Aug eve (chown racing:racing, write-verified),
   so tonight restarts ONCE; one RACING ALERT post-deploy (playup
   frozen 08:54 UTC, then invisible to liveness via candidate-set
   exit); unattended-upgrades SIGKILL mid-race-day (~2m17s, Doomben R8
   pre-jump ticks lost). Record: `sessions/SESSION_260.md` postscript.
   TAIL (Sunday): (a) formal rehydration proof — collector journal
   after tonight's 18:55 UTC single restart — **DONE S263 morning:
   PROVEN (one restart, "AUDIT rehydrated 32 in-flight races", stamp
   fix working every tick)**; (b) CODE FIXES DONE S263 (`9d86480`,
   suite 558): stamp writes via temp+os.replace (ownership-proof) +
   both unit guards treat `activating` as active; (c) liveness blind
   spot BUILT S263 (`86a16b1`, suite 561): the check names a book
   that "left the card early" (produced recently, zero now, boarded
   card racing on), triple-gated so overnight false alarms stay dead.
   PLAYUP VERDICT: it NEVER froze — it simply didn't board Toowoomba's
   night meeting (normal product shape, ~1.5% of Toowoomba races
   ever); capture behaved correctly; fully healthy today. Both commits
   PUSH-HELD until the Phase 1 deploy lands (sha pin); liveness
   activates at its next timer run after landing, the restart-guard
   at the 04:25 daily restart. DEFERRED micro-item: a discovery-time
   "SERVED venue not listed" INFO line (needs the true coverage-key
   normaliser, not the collision valve). (d) OPERATOR DECISION — pin
   unattended-upgrades service restarts to the 04:00–06:00 window;
   (e) disk: old root-owned backups — deletion in flight via the S263
   retention audit (operator pre-approved).
2. **0t-A — LAY MATCHING: SHIPPED S260 + LIVE-PROVEN (31 Jul).**
   v3 `6c0e287` + review fixes `1f3a7f5` (`326a181` is the separate AU
   rail pin, corrected S263); first live pairing fired in
   1.43s (Geelong, Inside Job) — the control had never once fired
   before. Root cause for the record: the operator lays 1–3s BEFORE
   logging the FB back (31 of 32 cases) and the old candidate list only
   offered pre-existing backs. Replay validation over all 336 live
   bets: 61/61 lays link, zero wrong, zero ambiguous.
   **TAIL COMPLETE S263 (2 Aug 09:52): the 34-row historical repair
   RAN — operator reviewed the proposal (`lay_repair_proposal_s263.md`),
   confirmed Sir Myka (verified P&L-indifferent: both FBs at 13.0,
   both lays 43.10@14.0), repair rehearsed (per-bet P&L byte-identical,
   466 bets) + pre-live review GO (102/102 ids) + applied in one
   transaction with backup `bethub.db.pre-layrepair-20260802-095251`
   (verb `ops/repair_lay_cycles.py`, v3 `b84456d`). RESULT: 0 unpaired
   lays store-wide, 306 cycles, 34 audit events, money check CYCLE
   PAIRING WATCH (0). 100% for past bets + 100% future (21/21 since
   the linker). THE 0t-A ITEM IS CLOSED END-TO-END.**
3. **0p — INTERNATIONAL PHASE 1 deploy. DATA BLOCKER CLEARED S267 —
   READY.** BUILT + reviewed 4×; capture `f2fa921` (498 tests) + v3
   `ddbcc77`. The 5 Aug 04:35 attempt FAILED at the rekey preflight: 342
   non-AU rows carried a Betfair market id, refusing the §3.3
   disjointness proof. S267 found **all 342 were AUSTRALIAN races with a
   wrong country stamp** (Bathurst 299 stamped GB, Canterbury 43 stamped
   US) — the guard was RIGHT; rekeying would have burned `bathurst|gb`
   and `canterbury|us` into the venue identity key. Corrected at the root
   (`af18787`): all three country write paths now refuse a non-AU stamp
   on a row carrying an Australian state code, and `country_stamp_fixes`
   journals the 583 corrected rows with `--reverse`. **Disjointness count
   is now ZERO — no guard change needed.** S266's "wait for repair-zero"
   was unreachable: the 679 remaining twins ARE the refused 0m
   population and the nightly repair has merged nothing since 31 Jul.
   Next: confirm disjointness still zero at deploy time → Gate B → drop
   `BETHUB_RACING_COUNTRIES=AU` → Gate C. STILL OPEN from S266: the
   deploy loop must refuse to ARM at a time its own guard forbids
   (249 refusals, zero successes, across 8 loops).
4. **0t-B — the rest of cycle accounting.** Cycle-as-a-set view,
   open/closed state, the standing invariant, and the P&L relabel
   (see `pl_audit_s260.md` D6: do NOT unify the two P&L figures —
   divergence is $0.00 over 14 days and structurally one term).
5. **0m — review-list corrector: MINI-BRIEF DELIVERED S263**
   (`twin_reviewlist_mini_brief.md`). Headline: 673/679 are
   ADJACENT-DAY DUPLICATE LABELS (one market stamped on yesterday's
   AND today's row — pre-DR-036 UTC-date residue); 540 gate-refusals =
   two different real races under one label; 139 settle-refusals =
   mostly contaminated rows holding two days' interleaved results
   (116 over-full); + 6 cross-code (Wagga) + 9 husks. SET IS FROZEN
   (newest 28 Jul; zero new since DR-036). Fix shape: classify script
   → operator review list → journaled un-stamp pass (no deletions;
   identity gate stays sole merge authority); ~1–2 sittings; classes
   A/B/D/E alone clear ~500–550. Cross-link: the morning sweep's
   cross-code guard refused 67 suspicious cards on 1 Aug — the same
   class, now blocked live at write time.
6. **0v — "Split this credit" + undo for account-anchored credits.**
   **Operator-queued 31 Jul, explicitly NOT urgent.** Books routinely
   issue a bonus as N × $X; the tool can only record one lump, and a
   deploy supersedes the WHOLE credit — so deploying $30 against a $150
   lump would silently destroy $120 of free-bet inventory and break the
   ledger cross-foot the S260 audit certified. Two gaps, both the
   familiar "working engine, no caller": the 0q *Undo credit…* button is
   gated on a credit being attached to a BET (`BetLog.tsx:679`), so
   account-anchored goodwill/deposit credits have **no undo path in the
   UI at all** — even though the server door accepts them; and there is
   no way to express a split. Proposed: a *Split this credit* action on a
   live unspent credit (N × $X → revoke + re-issue in one audited step,
   refusing if anything has been deployed), which gives the undo for
   free. Surface on Balances as well as BetLog.
   **Stopgap already done 31 Jul** (operator-authorised, sanctioned doors
   only): Sarie/Ladbrokes $150 → 5 × $30, verified via
   `compute_account_at_book_balance` (`free_bet_balance=150.00`,
   `free_bet_count=5`, cash untouched). Backup
   `bethub.db.bak-s260-pre-fbsplit-20260731-090813`.
   **Loose end CLOSED (S263 review, 1 Aug): moot — all six
   Sarie-Ladbrokes $30 credits (the 5 split + a 6th triggered 1 Aug)
   are now fully deployed; zero live, nothing left to expire.**

7. **0w — SIM GATEWAY HARDENING (SCHEDULED POST-RACE-DAY, Sun 2 Aug).**
   Operator-scheduled 31 Jul. Runs on the Pi only — touches NO BetHub code,
   no capture, no deploy window, so it can sit alongside 0p international.
   Context: Kate's provider swapped her SIM to **Vodafone, the same carrier
   as Sarie**, so the per-lane carrier assertion can no longer tell lanes
   3001 and 3002 apart. Operator ruled the shared carrier NOT a linkage risk
   (distinct IPs, distinct numbers) — **do not re-raise that**; the work here
   is purely about DETECTING a crossed lane, which the carrier check used to
   do for free. Two quick guards already shipped 31 Jul and are LIVE + tested
   (launcher refuses when >1 interface sits on a lane's subnet; monitor fails
   if any two lanes share an egress IP). This item is the rigorous remainder:
   **(a) ALERTING — DONE S263 2 Aug, LIVE + END-TO-END PROVEN** (test
   email delivered to Gmail 07:50 ACST, subject "TEST - RACING ALERT
   (SIM gateway): …"). Design: the Pi ssh-triggers a forced-command
   sender on the capture VPS (one mail implementation, one creds
   location; proven an arbitrary command cannot execute — it becomes a
   subject line). Batched alerts, 30-min cooldown, still-failing #N
   escalation, delivery-failure retry every 15 min. All four existing
   guard ALERT points wired. Files + .baks in the agent report;
   healthcheck now v4 (`.bak-20260802-alert-routecheck`).
   **(b) ROUTE-LOSS DETECTION — DONE same pass**: per-lane
   `ip route show table N` non-empty assertion (tables 101/102/103),
   failure alerts through (a) naming the 31-Jul replug shape; validated
   via a simulation hook with the real tables untouched. Lanes were
   never disturbed (3proxy PIDs 1.5 days old throughout).
   **(b) Close the dispatcher's route-loss blind spot.** `60-sim-refresh`
   reconciles a lane only when its bound IP differs from the live interface
   IP. An unplug/replug that returns the SAME DHCP address leaves the lane
   with a flushed routing table and a service that still looks healthy —
   this is exactly what took Kate down on 31 Jul. Fail-closed (the 3proxy
   source bind means traffic dies at the home router rather than leaking),
   and it usually self-heals because `MACAddressPolicy=random` normally
   yields a new IP, but it can persist. Fix: also assert
   `ip route show table N` is non-empty, not just compare IPs.
   **(c) Pin each lane to its physical USB socket.** `NamePolicy=path`
   already encodes it (`enu1u1`=3-1.1 Kate, `enu1u2`=3-1.2 Sarie,
   `enu1u4u1`=3-1.4.1 Mads). Refuse to start on the wrong socket. Deferred
   deliberately on 31 Jul: it fails closed if a router is ever replugged
   into a different socket, which is an operational cost worth taking only
   with the operator's eyes open.
   **(d) Operator-side, no engineering:** a "which account am I" bookmark in
   each AdsPower profile showing the current egress IP on open — the only
   cover for opening the wrong profile, which no Pi-side check can catch.
   Evidence + full test results: memory `router-sim-proxy-gateway`
   (2026-07-31 S261 entries). Backups on Pi:
   `/usr/local/bin/sim-proxy.sh.bak-20260731-guard`,
   `sim-proxy-healthcheck.sh.bak-20260731-v2`.

8. **0x — "CHANGE PROMO" BUTTON ON BETLOG (operator-flagged 1 Aug,
   POST-RACE-DAY).** Third promo mis-pick in a week: Tim/TAB Shes
   Peakin (Parklands R5, 30 Jul, $10) logged against "Ins $25 Cash
   2nd" when the real promo was "Ins $25 FB 2nd" — the trigger banked
   $10 CASH where TAB paid a $10 FREE BET (same shape as S258's
   hand-swap and S259's Sarie/Albion Park incident that commissioned
   the CLI). Corrected 1 Aug via `ops.correct_promo_selection --apply`
   (cancel-credit `a1a86071`, re-issue FB `ebb6fd1b`, bet re-pointed;
   settlement_review coherence sweeps clean after). The engine is
   built and now three-times proven — this item is the two-click
   BetLog caller the S259 header already anticipated ("the engine a
   BetLog 'change promo' button would call"). Self-serve rule applies:
   recurring error class → operator button, not Claude hand-fixes.

9. **0y — RACE-PAGE TAB FRESHNESS: refresh run on race selection
   (operator race-day batch, 1 Aug).** Operator, race day: selecting a
   new race leaves TAB odds stale "up to a minute (at times more)".
   Wanted: every race selection fires an immediate TAB refresh for
   that race — freshest odds possible at decision time. Capture-side
   trigger + v3 wiring; sits on top of the S257 lag work (3.5s pickup
   was proven for the FOLLOWED race — this is about the switch-to
   moment).

10. **0z — BETLOG/MODAL RACE-DAY UX BATCH (operator race-day batch,
   1 Aug).** Five related items from the Sat 1 Aug burst:
   (a) Unmatched/failed exchange orders show "0.00 @ 0.00" in BetLog
   (live example: Gilgandra R4 Calmundi lay `bet-52a3614f`, requested
   $41.10, match_status=failed, no price stored) — REQUESTED price and
   stake must be stored and displayed for unmatched/failed orders.
   (b) Reopen the modal for an unmatched order — change odds and
   re-send (today the only path is Betfair direct).
   (c) FB auto-select: accounts often hold multiple FBs; after a
   free-bet placement + Betfair order completes in the modal, the NEXT
   free bet should auto-select for the following placement.
   (d) MATCHED-PRICE TRUTH: Flemington R7 Arkansaw Kid lay
   `bet-6e1460ef` recorded matched_price 7.6 but Betfair matched at
   AVERAGE 5.07 ($39.89 stake, $162.35 liability on the exchange
   screen) — the tool stores the requested price, not the actual
   average matched price. Pull the real average from the Betfair order
   after matching (betfair_bet_id exists). Liability/P&L math reads
   wrong until then on any lay matched better than asked.
   (e) OPTIMUM LAY STAKE AT ACTUAL PRICE (the R7 question "better way
   to ensure the optimum stake is always sent in?"): stake $39.89 was
   optimal for the ASKED 7.6 (=300/(7.6−0.08)) but the market matched
   at ~5.07 where optimal was ~$60 — under-hedged by ~$20 of stake.
   Proposal: modal computes stake from the live best-available lay
   price at send time (and/or warns when asked price is far off
   current best) rather than the typed price.

11a. **1b — BONUS-WINNINGS AUTO-CREDIT, END TO END
   (operator-COMMISSIONED S263, 1 Aug eve: "This should all be
   automatically calculated. It requires a permanent fix, not
   patches."). BUILT overnight S263 — v3 `d3583cf` (pushed): parts
   (a) rounding term, (b) computing credit box + drift confirm,
   cash undo door + reclass-fence fix, (d) correction verb
   `ops.correct_credit_amount`. Gates: 2002 pytest / 510 vitest /
   tsc / build; red-before at every layer (stash-proven for
   fence+undo). Part (c) AUTO-BANK-ON-SETTLE deliberately STAGED —
   the plan review found it reverses the standing "credits stay a
   manual operator action" decision; operator question posed.
   POST-IMPL REVIEW PASSED (SAFE-TO-DEPLOY, no gates; rehearsed on a
   scratch DB copy first). **DEPLOYED + CORRECTION RUN 2 Aug 06:15
   ACST (operator "go", app closed): dry-run eyeballed → --apply →
   backup `bethub-pre-1b-correction-20260802-061532.db`, 4 credits
   superseded+re-issued exact, template term now 'cents', live bonus
   cash 149.88, derived Tim/Bet365 = $859.38 EXACT, money check
   clean. The $2.12 class is closed end-to-end.** REMAINING TAIL:
   (i) operator answer on auto-bank-on-Won (part (c) staged);
   (ii) 3 LOW test gaps (create-endpoint rounding validation, TopBar
   radio wiring, kind-default matrix FB/NULL arms) in a quiet
   sitting; (iii) live smoke on the next real bonus win (TAB whole-
   dollar / Bet365 cents / drift confirm).
   Brief `bonus_autocredit_brief.md` (plan + amendments + verdicts).** CORRECTED DIAGNOSIS (planner, verified in store): the
   5 credits were NOT hand-typed — all carry
   credit_source='triggered'; the operator tapped Burst Review's
   "bank the credit" and the SERVER computed every amount under a
   HARDCODED whole-dollar-ceiling rounding rule (TAB's, in
   credit_terms.py) applied to a book that pays exact cents. And
   return_pct=0.25 was ALREADY stored — EV was already right; the
   missing term is per-template ROUNDING. Tool overstates Bet365 by
   $2.12 vs the app's $859.38 until (d) runs. Shape: (a) new
   `credit_rounding` template term ('cents' for Bet365; NULL = TAB
   whole-dollar unchanged) through door + gap detector + new-promo
   card; (b) manual-credit box prefills the computed amount
   (single-source + drift confirm; kind defaults from return_type);
   (c) server-side auto-credit on soft-settle WON (shared evaluator,
   source='system', non-fatal, Burst Review auto-lane) + CASH
   extension of the undo door (the reclass fence's cure is currently
   unreachable for cash); (d) correction CLI supersede+re-issue the 4
   events ($57→$56.25, $26→$25.50, $23→$22.50, $11→$10.63), balance
   == app to the cent; backup + red-before + money check.
   (e) P&L RECONCILIATION SHIPPED S263 (`bdadb8f`), then REVISED to
   the operator's decision (2 Aug, `caa8ac9`, DO NOT RE-RAISE):
   **bonus cash IS cash — "effectively an odds booster" — so BetLog
   shows ONE P&L figure that simply includes the window's bonus cash
   (pnl_all_in); no "bonus cash"/"all-in" labelling, no Balances
   caption.** Both pages now show the same number for matching
   windows with zero explanation needed. Server still reports both
   terms (data honest; nothing double-counted). dist swap rides the
   next app-closed moment. Remaining 0t-B: the cycle-complete number.
   **ALL RECOMMENDATIONS APPROVED + BUILT 2 Aug morning (`2daa17a`,
   operator: "Proceed with all recommendations"): (c) auto-bank on
   settled WON is LIVE-on-restart — shared eligibility gate (door
   wording verbatim), source='system', non-fatal hooks in the settle
   door + log-past-bet, GET /v1/promos/auto-credits + Burst Review
   "Banked automatically on Won" lane, settle response carries the
   credit marker; the standing credits-stay-manual decision REVERSED
   (recorded in credit_gap.py). Corrections now stamp occurred_at
   from the replaced credit (yesterday's four keep 2 Aug — one-off).
   The 3 owed test gaps CLOSED. BONUS FIND+FIX: the manual settle
   door had always WIPED dead_heat/removed_runner counts — now passed
   through + regression-pinned (would have paid full bonuses on
   dead-heat wins under auto-bank). Gates 2011/518/tsc/build
   (app-closed). POST-IMPL REVIEW #2 PASSED — SAFE-TO-RESTART, all 8
   items, live numbers pinned (bets $3,636.05 + bonus cash $149.88 =
   all-in $3,785.93, self-check 0.00). REMAINING: operator restart →
   live smoke on today's first bonus win. LOW awareness: Log Past Bet
   has no dead-heat input — a past dead-heat win logged Won auto-banks
   the FULL bonus; undo on the row is the cure.**

11b. **1a — RESULTS LOG IN-TOOL (operator race-day batch, 1 Aug).**
   A results surface (finish order per race) in the tool: stops the
   manual result-hunting at settlement time, and feeds auto-settlement
   + automatic insurance/promo triggering (4th/5th cashback class
   included). Operator framing: "Need to save time settling bets and
   searching for results." Capture already holds Betfair settled
   states + the top-4/5 where subscribed — scope out what's missing
   for an authoritative finish order before building.

Everything below is the standing detail, unchanged in content.

0l. **DONE S259 (build+deploy+canary night of 29–30 Jul; capture
   `6566641`).** All three layers live: read-side cross-fragment union
   (blank-column class dead — live-proven on market 1.260470533),
   write-side identity (market-id-first adoption, venue unification,
   one tracker per market), historical merge repair (canary 55/58;
   full history resumes nightly with 04:30 deadline until done).
   VERIFIED 30 Jul (independent round): DATA INTACT exact-to-the-row;
   post-build review fixes shipped pre-night-2 (settled gate,
   result-conflict gate, most-BSP final set — retro check: zero
   damage). TAIL: (a) confirm nightly repair completion + census
   (night 2 timer armed 23:45); (b) model.db re-extract before that
   parked research resumes. Successors: 0m (review-list pass) and
   0n (data-reset inputs). Records: twin_row_fix_report.md (operator),
   twin_row_fix_brief.md (design+reviews), SESSION_259.md, DR-036.

0t. **CYCLE ACCOUNTING — every operation traceable to its origin
   (operator-COMMISSIONED S259, 30 Jul; SEQUENCED AFTER 0p
   international racing, operator-directed: "flag this as a fix after
   the international racing item before we implement anything").**
   Operator requirement, verbatim: *"the profit of those free bets
   still linked with the insurance cycle that may span multiple dates.
   It's about having all the operations accounted for and being able to
   be traced back to its origin."* **EXPLICITLY REJECTED by the
   operator: counting un-deployed free-bet value in P&L** — "I don't
   think that should be counted in the P&L until they're actually
   converted into cash." (This supersedes my earlier FB-at-70%
   suggestion; do not re-raise it.)
   **WHAT ALREADY EXISTS (verified S259):** cycle inheritance is real —
   `fb_credit.resolve_inherited_cycle` (FIFO oldest consumed credit →
   its triggering_bet_id → that qualifier's cycle_id) so a deployed FB
   JOINS its qualifier's cycle instead of minting a new one; BetLog's
   `CycleChain` renders the whole chain + a Net when cycle_bet_count>1;
   `ops/settlement_review.py:774-796` prints "CYCLES TOUCHED TODAY"
   with each cycle's net.
   **WHAT IS MISSING:** no view of cycles AS A SET — no open/closed
   state, no "which cycles are still in flight", no cycle list
   independent of "touched today" or of expanding the right bet. The
   date-filtered BetLog P&L splits a cycle across days by design, so no
   date view ever shows a cycle's true end-to-end result.
   **OPERATOR-SPOTTED LINK (correct):** the money check's "lay sits in
   a cycle with no back" sweep IS cycle logic —
   `workflows/bet_entry/v1/cycle_pairing.py:170` `list_unpaired_lays`
   finds LAYs (24h window) whose cycle holds NO non-LAY bet, i.e. a
   hedge never joined to the insurance bet it hedges. Evidence the
   plumbing is real but not closed; fold this sweep into the cycle work
   rather than leaving it as a standalone flag.
   **ACCEPTANCE BAR SET BY OPERATOR (corrected 30 Jul — NOT "100
   cycles"): 100% OF CYCLES ACCURATELY TRACKED.** This is a
   completeness+correctness bar, not a volume demo, and it materially
   changes the shape of the work: it is NOT just a reporting view over
   the existing links — it requires (a) an AUDIT that every bet sits in
   the right cycle and no cycle is orphaned, mis-linked or split,
   (b) a REPAIR pass for whatever the audit finds (the unpaired-lay
   sweep below is exactly the class that would fail this bar today),
   and (c) an ongoing invariant/check so it STAYS at 100%. Acceptance
   is a reconciliation with a number, not a screenshot of a populated
   list.
   **PROCESS DIRECTED: adversarial review at BOTH planning and
   implementation stages.**
   **FOLDED IN (operator, 30 Jul): a THOROUGH P&L REVIEW — confirm the
   P&L is built on sound logic and calculation.** Rationale: cycle-level
   netting is only trustworthy if the per-bet arithmetic under it is.
   Shape it like the S258 EV audit (`ev_calc_audit_s258.md`): a written
   audit that either signs the maths off or names each defect, with a
   fix list. Scope to cover at minimum —
   (a) `bet_net_pnl` per bet: stake/return/void handling, BACK vs LAY
   inversion, part-matched stakes, settled vs pending boundaries;
   (b) commission: the S250 0g per-market half-even + largest-remainder
   allocation and the S247 market-commission rebate (mixed win/loss
   markets) — re-prove against a real Betfair statement window;
   (c) FREE BET treatment: FB stake must not subtract from cash, FB
   returns credit cash only on win — and per the operator's standing
   rule, un-deployed FB face value NEVER counts as P&L;
   (d) promo credits: cash credits in the dashboard sum, the S259
   supersession/rejected-terminal filters, and the fact that BetLog's
   period strip carries NO promo term (the two "P&L" numbers answer
   different questions — decide and document which is canonical, and
   whether the labels should differ);
   (e) the Balances self-check exact-zero equality — what it does and
   does NOT prove;
   (f) cycle-level netting: the sum used by `CycleChain` and the money
   check's "cycles touched today", incl. cycles spanning dates;
   (g) the S231 haircut rules ($6-$10 screen EVs ~3pts, FB conversion
   65%) which exist in memory/governance but NOT in code — decide
   whether P&L/EV reporting should apply them.
   Deliverable: `pl_audit_s26x.md` + any fixes, red-before tested.

   Open questions for the build brief (operator's call): where the view
   lives (Burst review section / own tab / BetLog "group by cycle"
   toggle); what "closed" means for a cycle whose FB expired unused or
   was never deployed (closed at zero vs held open).

0s. **Promo-selection correction verb — hardening before cross-kind
   use (S259 post-execution review findings 3-5).** The verb
   (`ops/correct_promo_selection.py`) is proven for the same-kind
   re-type it shipped for, and RAN LIVE 30 Jul. Before it is used for
   a CROSS-KIND re-point or wired to the BetLog button: (a) re-assert
   settlement_state + matched_stake under the lock (S254 pattern —
   currently only the credit's supersession and the bet's template are
   re-checked); (b) `face_value_expiry` is hardcoded None and ignores
   the target template's `fb_expiry_days` (harmless while every
   catalogue template is NULL, diverges the day TAB's 7-day window is
   set); (c) the verb does not re-apply the credit-in door's kind
   gates (settled_won for bonus_winnings, LAY refusal, dead-heat /
   removed-runner refusal, insurance small-field void) — a cash→
   bonus_winnings re-point on a settled_lost bet would mint a credit
   the door itself refuses. Also: BetLog's paid-marker counts the
   rejected cancellation as a banked credit (right by coincidence when
   the amounts match, wrong when they differ) — needs a status filter.

0r. **DONE S259 (30 Jul, v3 `414148a`) — one Accounts tab: Balances
   on top in its format, account setup below restyled to match;
   /balances redirects (carrying query+hash, the post-registration
   ?deposit= deep link needs it); Balances' standalone min-height
   neutralised in the wrapper so the setup half is not pushed a
   viewport down. 494 vitest / tsc -b / scratch build. LIVE at next
   app start. Original commission:**
   **Consolidate Balances + Accounts onto ONE tab (operator-
   commissioned S259, 30 Jul).** Operator spec: Balances content at the
   TOP, keeping its current format exactly; Accounts content BELOW it
   in the bottom half of the same page; the tab is called **Accounts**
   (the "Balances" nav entry goes); the Accounts half is restyled to
   emulate the Balances template/format. Same shape as the S259 Manual
   Bet merge (wrapper page, children rendered untouched where possible,
   legacy routes redirect) — but with real restyling work on the
   Accounts half, so budget more than the Manual Bet merge took.
   Display-only; no money-path logic changes. Check first for element
   -id collisions between the two pages (the Manual Bet merge's one
   real risk) and for anything deep-linking /balances.

0q. **"Undo this credit" button (operator-flagged S259, 30 Jul —
   live instance: a $25 Tim/PointsBet FB credited off a losing
   insurance qualifier that never actually triggered; BetLog offers
   no undo).** **The ENGINE ALREADY EXISTS and is tested** — S243
   `POST /v1/promos/credit-revocations` (`ui/api/routers/promos.py`
   :1124 → `workflows/promos/v1/fb_revoke.record_free_bet_revoke`):
   supersedes a live `free_bet_credited` with a revoke terminal,
   refuses an already-spent or already-superseded credit, mandatory
   reason. NO frontend caller exists (grep: only a BetLog test
   mentions the path) — so this is a UI-only build: an action beside
   "Manual credit…" on a bet whose credit is live + unspent, S237
   inline confirm naming amount/book/holder, server already enforces
   every refusal. Spent credits: out of scope, they need the spend
   correction (restore door) first — surface that as the refusal
   message. NOTE the cash twin: a wrongly-banked CASH credit is
   cancelled by the rejected-cash shape the S259 promo-selection verb
   now writes (`ops/correct_promo_selection`), NOT by this door —
   the button should cover both once that verb lands.

0p. **PHASE 0 DEPLOYED S259 (30 Jul; capture `02e148f`+`1dafcc3`+`fd115fd`+`ec604d0`) — continuous operation (the 19:00 stop hour cost 10h39m of overnight capture on 29 Jul), country+local_race_date groundwork, per-venue coverage model, liveness heartbeat. D8 settled: race_date flip DEFERRED to Phase 1 (probe proved TAB files overseas races under the AU card date). UK pilot = a `jurisdiction_config` row flip; IE one row away. Brief: `international_phase0_brief.md`. NEXT: read tomorrow's recompute (`au_suppressed` must be 0), then Phase 1. Original assessment below.**
   **INTERNATIONAL THOROUGHBREDS — ASSESSED S259 (30 Jul).
   Verdict MEDIUM-LARGE, and it is a CLEANUP, not a greenfield build.**
   Full brief: `international_thoroughbreds_assessment.md` (operator
   summary at the top). Operator intent: "no differentiation between
   international and Australian thoroughbreds — just another class of
   race"; driver = more promos than anticipated.
   **HEADLINE: international racing is ALREADY IN THE SYSTEM and nobody
   decided that.** Arrived in volume ~20 Jul (~10x step change). In 14
   days: 1,108 international races polled (MORE than the 1,044 AU),
   289,316 international book snapshots = 29% of all odds traffic and
   **44% of proxied/Decodo-billed traffic** — i.e. the substrate of the
   30 Jul quota blowout. Output: **0 of 1,925 have a Betfair market id;
   0 of 1,515 finished races have a finishing position; 0 BSP rows; 0
   subscription syncs.** Un-loggable in the tool by design (DR-032 §6,
   enforced at 4 layers, hardest `store/schema/bets.py:60` NOT NULL).
   So today it is pure cost for zero usable output.
   **MY PRE-ASSESSMENT READ scored 6/8 confirmed, 1 worse mechanism,
   1 REFUTED — corrections recorded so they are not repeated:**
   (b) right but the live path is NOT the Sydney fallback —
   `orchestrator.py:222-223` stamps Sydney-today as race_date for every
   bookmaker-discovered race (a Del Mar race run 26 Jul Pacific is
   filed 27 Jul; 12 meetings smeared across up to 8 dates each);
   (c) **REFUTED** — the 19:00 stop only fires when no races are
   active and international keeps the tracker list non-empty; the
   collector ALREADY runs ~20h/day and "Past stop hour… exiting"
   appears ONCE in the whole log. No scheduler reshaping needed;
   (d) premise wrong in our favour — the 3GB plan was never sized on
   AU-only volume, it was already 44% international.
   **TOP RISKS:** R1 wrong dates regenerate the DR-036 twin class (no
   Betfair market ⇒ market-id-first enforcement cannot engage at all,
   ~150 mis-stamped rows/day). R2 NO country field anywhere + venue
   collisions ALREADY LIVE (US Canterbury Park → `canterbury`, same key
   as Sydney's, 4 days apart; Betfair's (AUS)/(GB) tags deliberately
   discarded; `_find_matching_venue:541` bidirectional substring). R3
   zero results/BSP/settlement (Racing API country-locked in the URL
   path; betfair_historical only the 8 AU states; UK/IRE market names
   carry no `R\d` so the tool's race-result door fails permanently).
   R9 **10GB Decodo will NOT survive** — modelled ~13GB/month (13-20).
   R13 EV produces confident WRONG numbers — `commission.ts:12` applies
   the 8% AU fallback to 2-5% UK markets, over-charging EV by 3-6 pts
   and biasing AGAINST good international promo bets; S253 calibration
   is AU-only, unproven abroad. Also: watchdog simultaneously too loud
   and blind overnight; **the promo model cannot express "international"
   at all** — literally the feature the driver asks for.
   **SEQUENCING:** Phase 0 is UNCONDITIONAL (half a sitting, worth doing
   even if 0p is dropped): per-book jurisdiction coverage model (kills
   5,000-11,000 daily TAB 404s), feed it to liveness (kills overnight
   false alarms), fix the date stamp, retire the 19:00 assumption.
   **R2 MUST precede R4** — the moment Betfair international discovery
   flips on, `state_from_timezone` (racing_day.py:60-64) stamps every
   foreign race "AU"; wrong order corrupts data faster than today.
   **OPERATOR DECISIONS PENDING (D1-D7 in the brief):** D1 (blocking)
   proxy plan — recommend traffic diet first, then re-model, then
   upsize. D2 which jurisdictions — only TAB + TABtouch serve anything
   outside NZ/HK; recommend a UK/IRE pilot and explicitly DROP
   Turkey/Brazil/Korea/Uruguay/Chile/Malaysia (budget, no promo case);
   **only the operator knows where the promos actually are.** D3
   country in the natural key vs the DR-035 reset reserve (recommend a
   plain `country` column now, key change folds into the reset).
   D4/D5 formalise continuous operation + 04:00-06:00 maintenance
   window, grow disk (~12mo runway). D6 keep Adelaide as "the day" but
   the picker must show the venue-local date. D7 show international EV
   marked uncalibrated, AFTER fixing commission.
   **3 CHEAP UNVERIFIED FACTS that could reorder everything:** real
   Betfair international market counts (one read-only catalogue call —
   drives both cost and page-cap sizing); whether the Racing API
   subscription covers GB/IRE/FR/US results (hard prerequisite for
   Phase 2); PointsBet's own code warns international meetings may be
   TOTE-ONLY with no fixed odds — if that generalises, some
   jurisdictions are useless for fixed-odds promos and D2 shrinks.

0p. **INTERNATIONAL THOROUGHBREDS — operator-COMMISSIONED S259
   (30 Jul), to start AFTER the promo-selection correction.** Operator
   intent, verbatim: "there should be no differentiation between
   international thoroughbreds and Australian thoroughbreds and their
   treatment. It's just another class of race that we have to bring
   in." Driver: more promos on international races than anticipated.
   Approach directed: assess complexity + risk first, sub-agents for
   planning/execution/post-implementation as needed, return only for
   guidance/decisions. EARLY RISK READ (S259, pre-assessment — verify
   in the brief): (a) Betfair discovery is AU-country-filtered
   (`list_au_win_markets`); (b) `_TZ_STATE`/`state_from_timezone` are
   AU-only and `local_racing_day` falls back to Australia/Sydney — an
   international venue would take the Sydney fallback and mis-stamp
   race_date, i.e. regenerate the twin class 0l just killed (HIGHEST
   RISK, design against DR-036); (c) collector stops 19:00 Adelaide —
   international racing runs overnight, so operating hours + the
   whole scheduler shape change; (d) proxy traffic: the 10GB Decodo
   plan was sized on AU-only volume hours after the 3GB plan hit its
   ceiling (30 Jul) — international will move it again, size before
   switching on; (e) TAB 404s on races it does not serve (S250) and
   overnight "book frozen" alerts are already foreign-racing false
   alarms — liveness/alerting needs a coverage model per book;
   (f) racing-code classification + venue aliases are AU-centric;
   (g) results/BSP/settlement coverage for international (subscription
   + Betfair historical) must be proven before bets ride it;
   (h) DR-032 §6 (a Betfair market must exist at logging time) is the
   gate that keeps bets joinable — confirm international coverage.

0m. **Twin repair review-list correction pass (NEW S259 — small, not
   urgent, needs its own mini-brief).** The identity guard refused to
   merge ~200 mis-stamped markets (fragments whose runner names don't
   overlap = wrong market label, incl. Wagga greyhounds
   1.260468539/69) + 74 settled-count audits + 12 merged date-twins
   carrying contradictory result sets (journal pre-images preserved;
   new gate stops further ones). Shape: classify → correct market
   stamps → let B6 merge the real twins → reconcile the 12 result
   conflicts against authority results.

0n. **Data-reset inputs from 0l (NEW S259 — file with the reset
   thread, no standalone build).** (a) UNIQUE market-id index + code
   dimension in the natural key (DR-035 reserve — the schema lock
   behind the procedural discipline now live); (b) market-id-less
   shell fragments HOLD REAL DATA (Randwick row 3406578, 520 book
   snapshots) — venue+date+runner-name harmonisation is the only
   merge spine; (c) same-code |code valve mints (DR-036 §6) strip
   with the reset migration; (d) pre-14-day trial metadata + S:-row
   cleanup (S256) unchanged; (e) 1,819 non-merged races DB-wide carry
   duplicate finish positions (capture-quality, pre-existing).

   (0l's original S258 commission, kept for history:)
   **Twin-row permanent fix (operator-COMMISSIONED S258, 29 Jul —
   "permanent fix rather than a patch job").** Live instance that day:
   Randwick (Kensington track) split into "randwick" (Betfair
   selection stamps, no TAB) + "randwick kensington" (TAB feed +
   tab_race_id, zero stamps) + an empty "kensington" shell — same
   betfair market ids on two rows, so BOTH soft-odds endpoints
   resolved the TAB fragment, found no selection ids, and served
   `runners: []` = blank TAB column in the tool all day (capture
   itself unaffected). Diagnostic queries in SESSION_258 §9. Scope
   for the build (one sitting, capture-side):
   (a) odds-join hardening — both soft-odds endpoints assemble the
   selection map across ALL fragments of a market (DR-034 done
   properly), so no future split can blank the column;
   (b) the actual de-twinning — venue-identity aliasing at race-row
   creation (the "randwick kensington"/"kensington" class joins the
   existing S255 suffix-alias machinery) + a repair pass for
   historical twins. Ties into the S252 finding (63% of Betfair
   markets since Apr attached to TWO race rows) and the S256
   data-reset thread — design against those files before building.
   **ESCALATING EVIDENCE (same day, ~14:00): twins cause CAPTURE DATA
   LOSS, not just blank display.** Randwick R3: collector ran TWO
   trackers over the one race ("kensington R3" + "randwick kensington
   R3", journal 03:57-04:05 UTC), final ~6 min of Betfair+TAB
   snapshots landed on NO twin (last rows 03:58:12, race off ~04:04),
   BSP pass logged "0 final-snapshot rows updated", settlement
   "16 runners settled" on an 8-horse field (both twins' runner sets).
   The fix must cover the COLLECTOR's race-tracking identity, not only
   the read-side join.

## Build items (operator-gated, money-path unless noted)

0. **Bankroll model (S248, operator-commissioned — SUPERSEDES the
   self-withdrawal remittance pairing idea, which is CANCELLED).**
   Operator dedicates a real spare bank account as the operation
   bankroll; Tim's holder float = that account, tracked to the cent.
   Deletes the is_self special case that caused the 21-Jul $165 crack
   (that crack's hand-fix: remittance `30b289c3`, backup
   `bethub-pre-s248-remit-fix-20260721.db`; under the new model a
   Tim book-withdrawal landing in his float is CORRECT — no pairing
   needed). Build (small, frontend + one door default; app-down dist
   swap, never race hours):
   - Un-hide the self float row on Balances (`Balances.tsx:256`),
     relabel "Bankroll", show at top; include it in the card total.
   - Deposit door for Tim: default source flips 'bank' → 'float'
     (bankroll), same as other holders. Funding/remittance stay as
     the rare personal↔bankroll transfer doors.
   - Rename "At risk right now" tile → "Current exposure"
     (operator-locked wording).
   - Daily money check gains: bankroll row == real bank-app balance.
   Establishment DONE 21 Jul eve: bankroll account seeded $3,000.00
   (incl. the returning $165), booked as ONE funding event `93513c7b`
   (backup `bethub-pre-s248-bankroll-seed-20260721.db`); Tim float =
   3,000.00 = bank account; op cash 14,940.14, self-check green.
   Bankroll==bank-app is a standing daily check from now.
   **Display build DONE 21 Jul eve (`404a928`, frontend-only, suites
   301 green, tsc+vite verified): Bankroll row + tile, Current
   exposure rename, deposit default from-float, door titled
   "Tim — bankroll". LIVE on next app start — the launcher rebuilds
   dist app-down automatically (operator: close window, double-click
   BetHub.command).**

0d. **COMPLETE S258 (29 Jul) — walkthrough delivered AND first real
   transfer done by operator. Item closed.**
   New movement kind `transfer` (receiver's account_id): ONE door
   action books the remittance(bankroll)+funding(holder) pair on one
   correlation; pair-reverses through the existing include_sibling
   door (message generalized to "paired action"). Bankroll row now
   LEADS with "Transfer to a holder's float" (receiver picker,
   outbound preview, bankroll-side success note) and its own doors
   carry the locked wording ("Money in from personal bank" / "Money
   out of the operation"); non-self doors unchanged. Red-before both
   sides; suites 1734/307; dist rebuilt app-down. Walkthrough note:
   transfer is the new DEFAULT door on the bankroll row (was
   funding) — flag to operator. Reverse-door pairing question
   resolved: rides the existing pair-reversal door.

0e. **DROPPED by operator decision S258 (29 Jul) — not required.**
   The bankroll==bank-app check stays manual. Do not re-raise.
   (Was: research UBank API/feed access to automate the daily check.)

0b. **"Moved to your bank" tile → "Bankroll" (operator-DECIDED S248
   eve).** The tile becomes the current bankroll (is_self holder
   float) — the operation's liquidity/solvency number, homebase of
   all funds. Folds into the item-0 build. Net-flow endpoint stays
   (unconsumed by the tile; cleanup call later). For the record, the
   old figure −$11,085.17 = returned $465 − sent_in $11,550.17,
   dominated by the day-0 seed ($10,684.67) booked as funding.

0f. **COMPLETE S258 (29 Jul, v3 `b42820d` + race-screen refinement
   `5c389e9`) — operator-confirmed live (books hidden in production).
   operator walkthrough then (hide button on each Balances book row,
   inline warn-not-block confirm, per-card "N hidden — show" restore
   fold-out, Burst review "Bets at hidden or unlisted books" section).
   New display-only `hidden` column (active flag untouched — its blast
   radius mapped first: pickers, PnL, watchdog, correction gates). Bet
   write paths untouched (already permissive; phantom-pairing hole now
   SURFACED by the derived review read, 7-day window, no stored
   flags). v1 exclusion per the S249 rule: no balance-at-log-time
   flagging (not recorded; retro-deriving would mislabel). Red-before
   at every layer; 1926 pytest / 465 vitest.**
   Original commission (kept for reference): Two halves:
   - **Remove from list:** an account-at-book row on the Balances
     page can be removed from its holder's list. Soft-archive only —
     ALL data retained (bets, ledger events, derivations untouched);
     the row just stops rendering in the holder's list. Confirm
     dialog warns when anything is outstanding on that pairing:
     non-zero derived balance, pending/unsettled bets, unreconciled
     rows, armed promos — operator can proceed anyway. (Likely shape:
     display-visibility flag on `accounts_at_book`, NOT the existing
     `active` flag if that gates logic elsewhere — check first;
     needs an un-hide path so nothing is a one-way door.)
   - **Permissive bet entry:** a bet logged at a book whose tool-side
     pairing has no current balance, or whose pairing is hidden from
     (or missing in) the holder's Balances list, is ALLOWED through
     placement/logging without ceremony — then auto-flagged into
     Burst review for later pairing/correction (existing unpaired-lay
     flag + burst-review catch-all precedent, B2/S235).
   Not built yet — commissioned for a later sitting; money-path
   discipline applies (red-before tests, walkthrough before any
   store change). **Operator conduct rule for this build (S249):
   be conservative — review the existing codebase deeply enough to
   be sure nothing built breaks; an incomplete-but-safe feature
   beats a complete one that risks the stack. Additive changes
   only; when a shared flag/path is in doubt, don't touch it.**

0g. **DONE S250 (22 Jul am, `8b41ea3` + rider `7f692c8`) — commission
   per-market cent-rounding.** `lay_commission_by_bet` now quantizes
   each market's commission half-even (the mode that matched the S249
   live read) and allocates by largest remainder (bet_id tie-break),
   so per-bet shares are cent amounts summing to the market's rounded
   figure; rebate is now signed (sub-cent top-up on fraction-carrying
   all-win markets). Red-before per shape incl. a half-even
   discriminator (0.205 → 0.20); suite 1729. Offline re-proof: live
   store derives the Betfair row 2,428.96 EXACTLY (== S249 real
   read). Display rider done: funds-gap flag totals print at 2dp.
   REMAINING: live watchdog re-proof at next app-open — funds gap
   must read 0.00 and the banner clear (fires automatically on the
   first worker cycle); if a residual appears, suspect the rounding
   mode (half-up vs half-even distinguishable only on an exact
   half-cent market).

0c. **DONE S250 (22 Jul am, `22b51de`) — `/holdings` serves
   cent-quantised `parked_pool` / `total_with_holder` (existing
   `_CENTS` pattern), 2dp asserted by test. Watchdog flag-detail
   quantisation done under 0g's rider (`7f692c8`).**

1. **Betfair void gap fix — BUILT + DEPLOYED S247 (64ff337).** Live
   use pending the first real flag (attended tap).  Originally: Walkthrough done Mon 20 Jul: attended
   "Re-check from account" tap on a watchdog flag; only the account's
   own cleared-orders VOIDED record can flip the row; before/after
   money confirm. Design + code-verified annex + build constraints:
   `betfair_void_retrue_design_note.md`. (~One sitting when
   authorized.) The gap, for the record: a post-settlement exchange
   void refunds the real account but the tool's row keeps its wrong
   verdict — flagged as "expected discrepancy" today, unfixable in-app
   until this lands.

0j. **DONE S256 (28 Jul) — SHIPPED + live-proven (stale entry caught
   in the S259 worklist review): Allbets $90 cash + $100 goodwill FB
   banked in-tool; conditioning log retired to the diary. Original
   commission kept below for reference.**
   Other-code bet row (operator-COMMISSIONED S251, 23 Jul —
   build Sun/Mon with the post-freeze deploys). One relaxed bet-entry
   path for non-racing bets (conditioning bets now; AFL SGM pilot bets
   later): book/holder + free-text event + stake/odds, tagged
   `conditioning` (or `sports`), NO Betfair stamp (field already
   optional; nothing consumes it for these — no lay pairing, no
   auto-settle, no watchdog re-check), settled through the existing
   BetLog Won/Lost/Void soft-settle door. No new tables/money concepts/
   screens beyond a minimal entry form. Money-path discipline
   (red-before tests). On landing, `conditioning_bets_log.md` retires
   to a conditioning diary (which book/when/why) — backfill the
   2026-07-23 Allbets $40 AFL bet as its first row. ~One sitting.
   **Rider (same sitting): goodwill/deposit credit door** — bank an
   FB/cash credit anchored to the ACCOUNT-AT-BOOK (no triggering bet;
   mandatory reason, optional expiry), surfaced on the Balances row.
   Semantics: deposit-triggered credits (Allbets $100 initial-deposit
   FB = first case, currently in `conditioning_bets_log.md`). UI gate
   discovery S251: manual-credit action requires terminal bet WITH
   promo attached (BetLog.tsx:548) — plain-cash bets can never anchor
   a credit through the UI, by design; hence the account-anchored door.

0k. **BUILT+DEPLOYED+REVIEWED S255 (26 Jul eve, capture `8645e08`+
   `054c2e5`+`6dfa987`) — DAILY by operator direction. FIRST SATURDAY
   RAN 1 Aug: hourly sweeps fired all morning; informal proof strong —
   14/14 early races carried full-field TAB prices by 07:20 (promo-
   pilot morning review). §4 ACCEPTANCE REPORT DELIVERED S263
   (`morning_sweep_s263_acceptance.md`): **PARTIALLY MET — everything
   the sweep controls passed** (12/12 runs, 8/8 books, 78,745 morning
   rows across all 104 AU thoroughbred races, TAB 100/104 median first
   capture 06:24); the strict per-bucket bar missed only for measured
   structural reasons (books publishing late = the book not the sweep;
   the T−75m margin; late Betfair stamps) — the ONE sweep-own cause is
   TABtouch always swept last losing ~9 races to the 50-min deadline.
   MICRO-ITEM: rotate book order per run + deadline tune. OPERATOR
   SIGN-OFF PENDING: accept caveats, or re-measure one more Saturday
   after the tune.** Timer live on the VPS (06:00–17:00 Adelaide
   hourly, every day; first unattended morning Mon 27 Jul);
   double-smoke-tested; adversarial review done — 5 real findings fixed
   (writer-lock, cache keys, S252 twins, cross-code identity guard,
   window erosion) + liveness freshness now excludes MORNING rows.
   First-Saturday acceptance (§4) = part of the Sat 1 Aug race-day
   sitting; report `morning_odds_sweep_report.md`. Original brief (kept
   for the acceptance gate + analysis scope):
   `morning_odds_sweep_brief.md`.
   Capture has ZERO prices before T−60m from any source (11.1M rows since
   March) — blinds the early-placement study (stopped at its Chunk-0 gate)
   and the S252 morning-market edge (7.8 pts). Build: standalone
   `scripts/morning_sweep.py` + own systemd timer on the identity-sweep
   pattern — hourly 06:00→17:00 Adelaide, **Saturdays-only v1**, AU
   thoroughbreds with stamped Betfair ids, races >T−75m only, same tables
   with `snapshot_phase='MORNING'`. TAB on its OWN session pool (never the
   pinned collector/live pools); replicate the overround>150% guard; do
   NOT write `snapshot_batch_summary` (no phase column — contamination);
   no orchestrator/phase-machine changes, purely additive, disable =
   mask the timer. First task on the box: inventory the live crontab +
   systemd timers (deploy folder ≠ live box; 08:25-vs-9:00 collector-start
   question — report, don't fix). Acceptance = brief §4 on the first swept
   Saturday (incl. the per-book morning publish-time table). ~One sitting
   VPS-side; each swept Saturday feeds the study (2–3 = coarse answer,
   8–12 = full). Analysis itself explicitly out of scope.
   **Operator motivations (S254), for the eventual analysis brief:** (1)
   calm morning placement vs pre-jump scramble (the scramble breeds the
   wrong-account errors); (2) possible morning-market edge (S252 7.8 pts);
   (3) volume across the full card; (4) **account health** — non-pro
   bettors' timing profile. Nuance for the analysis: books profile
   beating-the-close (CLV) more than clock time, so the SAME drift data
   prices both the EV cost and the camouflage value of morning placement —
   report them together.

## Operator actions (do as they come up operationally)

2. **DROPPED by operator decision S258 (29 Jul) — permanently.**
   BetRight sends no promo offers, and it was the only book needing
   the `3rd needs ≥8 runners` template term. Do not re-raise. The
   honesty rules and template machinery stay as-is (inert for
   BetRight). (Was: set the term on BetRight insurance variants the
   day each template is next used; list `b2_build_report.md` item 5.)
   **FB expiry days: DROPPED by operator decision S254** — operator
   manages expiries manually and doesn't want the input burden; the
   in-tool expiry machinery stays deliberately inert (NULL = never
   expires in-tool, harmless). Do not re-raise.

0h. **Call quality / anticipation — CYCLE-3 RESEARCH EXECUTED S250**
   (operator-commissioned "begin, thorough, with web research").
   **Report: `bethub-analytical/race-price-pressure/
   cycle3_tab_leadlag/report.md`** (+ 3 sweep digests in
   `research/`). Delivered: Betfair leads TAB ~40s–2min (HRY +40s,
   event clustering 30–120s, desk median 61s inter-reprice in final
   2min) — independently matching the industry-triangulated prior;
   windows fast (persistence≈0 at snapshot res); favourites/mids are
   the clean end; returnHistory = TAB's own ms-stamped reprice log
   (SAME-DAY retention only — nightly harvester = data gap G2);
   evening re-run armed. NEXT builds to commission: G1 persist
   live-pool fetches (+returnWinTime/percentageChange/flucs), G2
   nightly harvester, N3 threshold-follower hazard signal → shadow
   mode; camouflage constraints (jitter/round stakes) first-class.
   Original R1 grade backtest + R2 sp_near trust + R3 trend v2 + R4
   label pass remain queued behind the signal work. TAB latency
   levers: DONE S250 (refresher live at ceiling).

0i. **DONE S259 (30 Jul, v3 `ff44007`) — clear releases to auto-fill + owned-box marker; walkthrough at next app start. Original:**
   **Soft-odds ownership UX (operator-flagged S250, investigate-only
   done — small, flagged for a later sitting).** Today: ANY touch of
   a soft-odds box (type / stepper tap / CLEAR) marks that runner
   operator-owned for the race — the feed never writes it again, no
   release path (race switch only). Per-runner in code; "whole table
   stopped" = cumulative claims + the clear trap (clearing leaves a
   permanently dead box, doesn't re-seed) + 30s background cadence
   outside T-30m. Build when commissioned: (1) clear = hand the
   runner BACK to auto-fill; (2) subtle owned-box marker so frozen
   vs live-fed is visible. REJECTED: time-based auto-release
   (silently reverting an operator number mid-decision is worse).

## Watch items / small calls (post-live-mileage)

3. **Void-detector window size** (S246 review note): the watchdog only
   re-checks bets placed in the last 24h — a later void is never
   flagged. Revisit once the watchdog has live mileage (cost vs
   coverage call).
4. CLOSED S259 review — the post-B2 first start happened weeks ago
   (many clean starts since); the one-time migration watch is moot.
5. **RACE-DAY LIVE-PROOF BATCH — RESTORED S263 (1 Aug review found it
   dropped from all current surfaces).** Deferred at S257 to "next
   attended race day (~8 Aug)" on the premise the operator would be
   away 1 Aug — the premise proved false (1 Aug was attended and
   bet-heavy) but the batch was never re-surfaced, so 1 Aug came and
   went with no disposition recorded. Items: (a) the 3 parked panel
   checks (additivity, $-at-risk, steadies/concentrates — need a real
   promo bet; 1 Aug had them); (b) first live REASSIGN button use
   (1 Aug's fix used `correct_promo_selection`, not reassign);
   (c) TAB column side-by-side eyeball vs the book's app (S257 carry);
   (d) Take-SP Stage 0 capture (~$12 bounded, operator present);
   (e) OPTIONAL: historical bonus-winnings EV recompute (S258).
   **S263 walk-through: ask which of these today already covered;
   the rest ride the next attended race day.**
   (Historical S246 list, superseded: TAB auto-fill/watcher/B2 doors —
   all long since live-proven.)

## Build items — signed off, staged

5a. **DONE S247 — float "unseeded" cleared** (4× $0 DAY_0_OPENING
   markers incl. Tim; all seeded=True).  Originally:
   write $0.00 DAY_0_OPENING holder adjustments for Kate/Sarie/Leigh
   dated 2026-07-17 (reset day) via one-off script + pre-write backup
   (S246 pattern; no door writes this event type, movements door
   rejects $0). Money-neutral; clears the Balances warning by its own
   definition. Floats verified absolute + reconciled S247.

5b. **DONE S247 — FB face single-source DEPLOYED (64ff337).**
   Originally: hedge modal rounded an armed $13 credit's
   face down to $10 (silent — the drift guard compares against its own
   rounded prefill), logging/hedging off the wrong face while drawing
   the full $13. Fix = the input box is the only source; buttons and
   auto-arm populate it; submit-time parity confirm; drawdown records
   actual amounts. Brief: `fb_face_single_source_fix_brief.md`.
   Frontend-only, app-down dist swap, never during race hours.

6. **Take-SP — SHIPPED AS DEFAULT S263 (2 Aug, v3 `8432c36`;
   operator decision SUPERSEDES the S246 staged Stage 0/1/2 plan,
   recorded in the client contract).** All five Betfair placement
   paths default to MARKET_ON_CLOSE for all races; NEW `bsp_market`
   flag from the catalogue gates the modal (BSP absent/false → option
   HIDDEN, old behaviour + amber note — never default a money option
   on missing data); operator overrides untouched; new placements
   only (resting orders keep their persistence). Red-before ×11;
   suites 2048/527; dist rebuilt app-closed. Post-impl review in
   flight (lay-liability-at-SP analysis the focus). Motivating case:
   the 1 Aug Calmundi $41.10 unmatched lay. REMAINING from the old
   brief: the phase-2 flip-sweep for already-resting orders (unbuilt,
   parked); types.ts global regeneration (separate maintenance pass —
   found ~4,000 lines stale).**

## Small follow-ons from the S254 reassign build (none blocking)

- INTENTIONAL-UNHEDGED ACKNOWLEDGE — DONE S263 2 Aug (v3 `17dad49`,
  2036/523/tsc/build, app-closed dist): BetLog "No hedge —
  intentional…" action writes an append-only annotation; the money
  check moves acknowledged bets to a quiet "✓ acknowledged intentional
  (N)" line; both operator-declared 1 Aug bets seeded (El Pensador,
  Syrian Diamond) — money check clean, ⚑⚑ lines gone. PREMISE FIX
  found en route: the FB-no-hedge sweep has a 24h window (lines age
  out silently, they never "flagged forever") — OPERATOR CALL queued:
  should no-hedge FBs persist until answered, like unpaired lays do?

- Settled-bet DETAIL edits — DONE S256 (both-stake-fields + banked-
  credit fence; used live S258 for the 4.20→4.116 deduction fix).
  Stale entry caught in the S259 review.
- `BetLog.test.tsx` mock-hygiene sweep (index-based `mock.calls`
  assertions can read a prior test's calls — standing flakiness class).
- v1 policies to revisit only if they bite: 2+ orphans on a correction
  target → refuse (could add a name-the-bet flag); under-faced spares
  accepted silently; correction credits copy expiry verbatim.
- Cross-book reassign stays refused pending the placement-stamp policy
  (promo stamps feed the S253 calibration).
- `current_state.md` refreshed S263 (1 Aug) — keep refreshing at close
  whenever the picture moves; it goes stale fast on deploy weeks.
- Wrong-account SPEND bet whose qualifier is correct: no self-serve fix
  (fail-closed to runbook); build only if it ever actually occurs.

## Parked (unchanged from earlier queues)

Money-movements filters on Balances (account / account-at-book /
transaction type / date range — operator nice-to-have, S247; include a
"Clear" button, and add the same Clear to the existing BetLog
filters; ALSO a Clear/reset button on the race-page Promo bar,
tucked top-right — one tap back to a fresh no-promo state for quick
promo switches; the arm-nothing path already exists in TopBar,
placement only — S247) · Balances P&L-after-profit-shares line + per-holder
distributions-given summary (S247; data fully captured —
total_profit_share_distributed already derived, display only) ·
Profit-attribution design note (per holder / per book, CHAIN-first
rollup — cross-book hedges make naive per-book views lie; conventions
needed: reversal display, in-flight money, FB valuation; then an
analytics build) ·
Results-retention build · theme verdict ·
spray-cost analysis · race-watcher Phase 2 (whole-card + promo
assignment) · dogs/harness soft-odds coverage · lay order-price on the
unmatched bar (needs placement-path persistence) · demotion build
(agreed, not commissioned) · VPS hardening brief approval ·
fingerprint burn-list persistence across collector restarts
(DOWNGRADED S250: the 21-Jul overnight "total burn" was actually
TAB 404s on races it doesn't serve, misread as blocks — fixed
capture-side `caffb78` (TabRaceNotFound: pin kept, no hunt, no
breaker, no cb hit); real burns remain rare).

## S263 OPERATOR DECISIONS (2 Aug, "Fine with your recommendations")

1. CUT LINE: v3-done = this week's plan; 0m + 0v trail after (plans
   reviewed and ready).
2. CYCLE ACCOUNTING (shapes the Tue–Wed build): cycles close at bonus
   expiry with an "expired unused" marker + auto-reopen on late pay;
   view = BetLog group-by-cycle toggle; the S231 $6–$10 haircut IS
   codified into the EV display (never realised P&L); the four 2-Aug
   replacement-credit dates get one audited re-true to 1 Aug (fold
   into the build).
3. OS UPDATES: DONE 2 Aug — needrestart list-only + apt timers moved
   to 04:15/04:45 ACST (VPS overrides in place, verified).
4. MORNING SWEEP §4: ACCEPTED with the explained caveats — the sweep
   is signed off; the book-rotation tune stays a micro-item.
5. GOVERNANCE MIRROR: approved; awaiting the operator's one-click
   repo creation (murra86/bethub-rebuild, private) — no API token on
   this machine to create it; push ready.
6. 4th/5th TEMPLATE: CREATED 2 Aug via the adapter ("Stake back
   4th/5th → Cash (cap $100, 14+ runners)", refund_positions [4,5],
   position_min_field {4:14,5:14} — the honesty clause encoded).
   Promo-pilot: stays as-is (available, not in the routine) — no
   explicit keep/park recommendation was made or approved.
7. MONEY-CHECK DIALS: DONE 2 Aug (`23ba696`, suite 2053, red-before
   ×5): no-hedge flags now persist until a lay joins or an
   acknowledgement exists (window removed; live run = 0 new flags +
   acknowledged 2, as predicted post-repair); GOODWILL CREDITS section
   live — first run surfaced the $10 Sarie goodwill credit expired
   unredeemed (S262), classification store-verified.

## S264 OPERATOR DECISIONS (2 Aug)

1. GOVERNANCE MIRROR: DONE — operator created `murra86/bethub-rebuild`;
   pushed 2 Aug (history rewritten to untrack the 146MB DR-029 probe
   file at both historical paths — GitHub 100MB hard limit; file kept
   on disk, gitignored; SHAs changed, pre-rewrite backup taken).
2. OVERNIGHT CAPTURE OUTAGES: LOW PRIORITY standing. "Not as concerned
   for outages at night. I want international racing to bet on as promo
   exists, but I'm not too concerned if we miss some races in the
   capture." No night heroics; consider downgrading overnight alert
   escalation (micro-item, not commissioned).
3. FLEMINGTON R7 RE-TRUE: YES, fix (stored 7.6 → Betfair true 5.07 avg;
   settled won lay, zero cash impact, analytics/liability truth only).
   PLUS: operator commissioned a PERMANENT fix — this class (wrong
   stored matched price on a settled row) recurs occasionally →
   self-serve correction verb `ops.correct_matched_price` (house
   pattern: backup, mutation event, original economic date, reuse
   0z(d) ledger-truth plumbing post-merge). Flemington R7 = first
   live use.
4. SETTLE-ASSIST SHAPE (1a): one-tap-with-per-bet-preview CONFIRMED
   (operator: "happy with your recommendation"). Full-auto stays
   stageable later per the 1b part-c pattern.
5. TAKE-SP MANUAL OVERRIDE NOTE (operator, 2 Aug ~13:15): one pending
   free-bet cycle's lay was deliberately re-marked PERSIST (away from
   the new Take-SP/MARKET_ON_CLOSE default) by the operator in-tool.
   When it settles: the persisting order is INTENTIONAL, not a defect;
   do not count it against the Take-SP first-live-SP-fill watch item.
6. 0s VERB HARDENING: DONE S264 (merged to main, suite 2205). All
   guards per plan+amendments: under-lock re-assert, fb_expiry_days
   honored, kind gates re-applied on re-point (cash→bonus_winnings on
   settled_lost now refused), replacement keeps original economic
   date, insurance gate extracted+shared with the credit-in control,
   cycle-move marker collision refused. (d) paid-marker filter was
   already live (S259 `329c42f`) — verified, nothing rebuilt.
   SHIP NOTE for operator: the verb now REFUSES voided bets on every
   arm (deliberate plan §2c change) — the refusal message names the
   undo route to use instead. Cross-kind CLI use is now cleared.
7. D3 (plan §9.4): GO — operator agreed 2 Aug. book_correction ledger
   adjustments join the headline P&L (split by reason from
   day_0_opening, which stays excluded). Build commissioned S264.
8. 0w(c) SOCKET PINNING: GO — operator accepted the fail-closed cost
   ("each router keeps its socket; dead lane after replug = check the
   socket first"). Build commissioned S264.
9. R7 RATIFIED: provisional credits close plays (auto-reopen on
   finalise); Burst Review lane is the accepted backstop for
   qualifier-lost plays with credit under review.
10. 0w(d): operator will add the "which account am I" IP bookmark to
   each AdsPower profile themselves next time at the machine.
   D3 DONE S264 (`0b664c8`, suite 2208): one shared predicate; strip
   pnl_all_in + Balances hero both include book_correction; the
   two-ledger self-check identity holds by construction (live: exactly
   −$0.01, headline $3,865.92, self-check difference 0.00);
   day_0_opening stays excluded.
11. 0w(c) DONE S264: single map /etc/sim-proxy-sockets.conf (Kate
   3-1.1 / Sarie 3-1.2 / Mads 3-1.4.1, derived from live devpaths);
   launcher refuses wrong-socket start pre-route-mutation (plain-
   language message names the fix); healthcheck v5 asserts running
   lanes + alerts through the proven email path; validated live-pass +
   simulated-failure both arms; 3proxy PIDs unchanged throughout.
   Backups *.bak-20260802-socketpin. 0w ENGINEERING COMPLETE —
   remaining: (d) operator bookmark only.

## S265 OPERATOR DECISIONS (3 Aug)

1. SETTLE-UP LANE MOCK APPROVED (mock v2.1,
   `settle_up_lane_mock_s265.html`): chronological races, one aligned
   grid per bet row, compact promo labels, badge vocabulary confirmed
   (Won / Lost / Void / Settle-lost-+-bank green-red; Lost—check-book /
   Hand settle / Waiting-on-result amber holds; Betfair bets excluded
   with one header line). Operator: "go with this for now" — expect
   race-day feedback as a v2 pass. 1a Phase 2 is BUILDABLE.
2. PROMO AUDIT FOLLOW-UPS (all five decided):
   (a) 'Ins 2nd Winnings FB $100' ARCHIVED — winnings-based promo the
       stake-based engine cannot compute; rebuild only if it returns.
   (b) BetRight small-field variant DECLINED — "no more promos with
       BetRight, won't likely use it again". Do not re-raise.
   (c) FB EXPIRY TRACKING DECLINED — "will introduce more complexity
       and I try to use them within 24 hours". Removed from the list;
       do not re-raise. fb_expiry_days stays NULL everywhere.
   (d) 'Ins $25 Cash 2nd' ARCHIVED — the mis-pick trap; unhide if a
       real cash-2nd promo appears.
   (e) 'Bonus Winnings (Cash)' RENAMED 'Bet365 Bonus Winnings (Cash)'
       — cents rounding is Bet365's rule; never pick for TAB.
   Implementation: soft-archive flag shipped end-to-end (v3 `1fefeb5`);
   archived templates leave all pickers client-side, stay on the
   catalogue payload for historical resolution. Live data updated in
   the same sitting (archive ×2 + rename, notes stamped).
3. Context for (2): S265 promo-catalogue integrity audit (sub-agent,
   3 Aug) — all 89 live credits recompute to the cent; every historical
   defect properly superseded; findings were forward-risk only.

4. R7 RATIFIED (cycle accounting review rec 7): "provisional credits
   close plays" stands as shipped. Weighed S265 on live data — the
   under-review state has never occurred (109 finalised / 7 rejected,
   0 provisional ever), is burst-lane-visible while it exists, and
   play state re-derives (re-opens) instantly on rejection. Stricter
   reading declined (double-listing noise, no incremental catchment).
   REVISIT TRIGGER: books that routinely dispute or slow-walk credits.

## Small follow-ons from the S265 walk-through (3 Aug, none blocking)

- **Bet365 rail SHIPPED in code** (`v3 TopBar`): arming Bet365 shows
  "Bonus 25% → Cash" as the primary; LIVE at the next app-closed dist
  rebuild + restart.
- **Credit visibility on the qualifier card:** BetLog's bet card shows
  the promo name but not the BANKED credit amount — the operator
  couldn't see the $25-vs-$31.50 correction from the card (proof was
  indirect: the deployed FB stake + zero leftover FB). Small addition:
  a "banked credit $X" line on bets with a triggered credit. Fits
  naturally with 1a Phase 3 surfaces.
- **FB conversion blank on a hedged, converted FB back:** the Velocity
  Miranda FB back (won +$137.50, lay −$119.72, face $25) shows
  "FB conversion —" where 71.1% is derivable from its own cycle.
  Scope: when does realised_conversion_rate populate; likely a
  compute-at-read gap for the paired-lay shape.

## Parked idea (S265, operator-flagged, NOT commissioned)

- **In-tool analytics page** — "at some stage we will likely develop a
  high level analytics page in the tool so I can review performance."
  Foundation when it happens: `promo_cycle_analytics_reference_s265.md`
  (canonical read rules R1–R8 + the qualified per-template/book
  baseline; every rule was learned against live data — the page's
  queries must honor all eight or its numbers will be wrong).

- **Venue-name hygiene (S265 Results-page census):** capture store holds
  'The' (truncated 'The Gardens' — one Newcastle greyhound meeting split
  across two rows, races 1-9,11 vs 10,12 on 1 Aug), 'bet365 Hamilton',
  'Aquis Park Gold Coast'. Display-side folded via the v3 alias map +
  picker merge; the STORE split is a capture naming defect (0m family)
  — fold into the 0m sitting or the coverage-key normaliser work.

## S265 OPERATOR COMMISSION (4 Aug) — THE CALL AS THE SINGLE INDICATOR

Operator: "make the CALL item as reliable a data point as possible to
advise whether I should execute a trade or not — ideally a single
indicator that all my decision making is made on." Also: "I will
respect the call from now on" (post-audit; LEAVE overrides validated
as -53% ROI on his own record). Program plan:
`call_reliability_program_plan_s265.md` (A contract / B four inputs /
D three stages) — adversarial review in flight at write time. This
SUPERSEDES worklist 0h (R1 grade backtest) — 0h becomes stage D1's
core. Sequenced after the Phase-1/0y landing settles.
