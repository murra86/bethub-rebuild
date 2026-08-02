# SESSION 264 — Sun 2 Aug 2026 (day; operator mostly outdoors, standing autonomy)

Operator turns: session open + GitHub note; three decision batches
(Flemington/settle-assist; D3; 0w-c/R7/0w-d); the PERSIST override
note; one brief tool use ~13:10 (store grew 306→308 cycles, 466→470
bets); "proceed with remaining work, then close."

## Opening state + checks
VPS health all clear. RACING ALERT review: overnight Betfair outage
01:45–~05:15 ACST self-resolved via scheduled restarts (operator ruling
that followed: overnight outages LOW priority — no night heroics;
missed overnight captures acceptable; international is wanted for
promos, not capture completeness). SIM-gateway 0w test alert confirmed
delivered. Outage-window races may lack Betfair ids (DR-032 §6).

## Governance mirror — resolved
Operator's GitHub note answered: `murra86/bethub-v3` = the CODE backup
(S228), the missing repo was `murra86/bethub-rebuild`. Operator created
it; push required a history rewrite (146MB DR-029 Newcastle probe
jsonl exceeded GitHub's 100MB hard limit at BOTH its historical paths;
untracked, kept on disk, gitignored; ALL SHAs changed; pre-rewrite
backup tarball retained in the job scratchpad). Mirror live and pushed
throughout the session. `raceday-0x-0z` branch also pushed to the v3
repo as backup before merging.

## The four adversarial reviews (parallel, then acted on same-session)
1. **0y plan**: diagnosis fully CONFIRMED in code; AMEND-FIRST →
   amendments stamped NORMATIVE in the plan file (headline: the plan's
   claim that evicted promo-pilot races "ride the background feed" was
   FALSE — one-line pilot fallback rescinds "don't edit that repo";
   focused-due needs an in-flight exclusion; 5 minor).
2. **raceday-0x-0z**: GO for merge (trial merge clean, suites green on
   merged tree) / FIX-FIRST F1+F2 on the replace button.
   `raceday_0x_0z_review_s264.md` incl. the first-live-use protocol.
3. **cycle accounting 1–3**: GO for 4–6; acceptance number and
   falsifiability replay independently re-verified; R1+R2 required
   (any operator edit "confirmed" a pairing; assign-cycle wrote no
   audit row). `cycle_accounting_phases123_review_s264.md`.
4. **1a plan**: AMEND-FIRST — coverage verified TO THE ROW; BSP defect
   is ABSENCE not mislabel; WINNER-demotion pin; dual-source dead-heat
   detection vs twin contamination; volume ≤~50 not ~30. Stamped
   NORMATIVE. Settle-assist shape: operator CONFIRMED preview.

## Shipped (bethub-v3 main, all pushed; final suite 2208 pytest + 558 vitest + tsc)
- `a44f176` merge raceday-0x-0z (zero conflicts).
- `d5db700` replace guards: REPLACE_SIZE_SHORTFALL (size_carried
  tripwire) + REPLACE_ROW_TERMINAL (status-guarded re-point).
- `15edcd8`+`fa68f60` cycle-move confirmation: R1/R2/R3 + post-impl
  tightening — only positive-marker notes confirm ("cycle move:" /
  repair shape); no-op edits emit nothing; live scan: exactly the 34
  repair moves pass (was 42 incl. promo corrections + no-op edits).
- `b53f091` **ops.correct_matched_price** (permanent, operator-
  commissioned): dry-run/--apply+backup/--from-ledger. FIRST LIVE USE:
  Flemington R7 bet-6e1460ef 7.6→5.07 (settled won lay — zero cash
  impact, liability/analytics truth), backup
  `bethub-pre-matched-price-20260802-124148.db`, verified reversible.
- **0t-B phases 4–6** (`c57172d`,`f34155d`,`2ab9ed7`,`2288d51`):
  derived cycle state (expiry/revoked close + auto-reopen, no writes),
  all-in net on both money surfaces via ONE derivation, BetLog "Group
  by play" toggle + /v1/bet-cycles + F9 footer, D2/D5/D7/D10, §6e
  relabel, S231 haircut codified (evEngine promoEV only, never
  realised P&L). **Four occurred_at re-trues APPLIED LIVE 13:50**
  ($114.88 → 1 Aug = $149.88; backup
  `bethub-pre-creditdates-20260802-135019.db`; idempotent).
  Post-impl review: **CLEAN**. **0t-B CLOSED**
  (`cycle_accounting_0tb_closeout_s264.md`): **308/308 cycles ·
  470/470 bets · 100.0% · zero defects**, daily check carries it;
  4 LOW notes filed; C8 caveat resolved via the audited assign-cycle.
- `8b5212e` **0s verb hardening** (built in worktree, merged):
  under-lock re-asserts, fb_expiry_days honored, kind gates re-applied
  on re-point, replacement keeps original economic date, insurance
  gate shared with the credit-in control, voided bets refused (names
  the undo route). Cross-kind CLI use CLEARED. (d) verified already
  live since S259.
- `0b664c8` **D3** (operator GO): book_correction in headline P&L via
  one shared predicate; live delta exactly −$0.01 → $3,865.92;
  self-check identity holds; day_0_opening stays excluded.
- Dist rebuilt at app-closed after each frontend-affecting merge.

## Pi (0w) — ENGINEERING COMPLETE
(c) socket pinning shipped: `/etc/sim-proxy-sockets.conf` (Kate 3-1.1 /
Sarie 3-1.2 / Mads 3-1.4.1 from live devpaths); launcher refuses
wrong-socket start pre-route-mutation; healthcheck v5 asserts running
lanes through the proven alert path; validated live-pass + simulated
failure on both arms; 3proxy PIDs untouched. Remaining: (d) operator's
AdsPower IP bookmark only.

## S264 operator decisions (recorded in worklist)
Mirror done · overnight outages LOW · Flemington YES + permanent verb ·
settle-assist = preview CONFIRMED · D3 GO · 0w(c) GO (fail-closed cost
accepted) · R7 RATIFIED · 0w(d) operator-side. Plus the PERSIST note:
one pending FB lay deliberately re-marked PERSIST from Take-SP —
intentional, not a defect, not the first-SP-fill watch item.

## HANDOFF — next session does these FIRST
1. **Phase 1 deploy**: loop2 gave up 13:46 (36 attempts — Sunday card
   never gapped). **`s264-deploy-loop3` transient timer fires 18:30
   ACST (09:00 UTC)**, 3h budget spanning the AU-end→UK-start gap.
   Check `logs/deploy_phase1_attempts.log` for ALL DONE / gave up /
   FAILED MID-FLIGHT; re-arm with a new unit name if needed. AFTER
   landing (unchanged from S263): push capture master (`86a16b1`) +
   fast-forward VPS → Gate B SQL over the day
   (`international_phase1_brief.md` §7) → GB flip only after Gate B
   holds → remove `BETHUB_RACING_COUNTRIES=AU` from BetHub.command →
   Gate C with one real GB promo bet. NOTE: overnight-outage races
   (2 Aug 01:45–05:15) may lack Betfair ids — don't let them fail
   Gate B unexamined.
2. **1a build** (post-deploy): plan + NORMATIVE S264 amendments;
   preview shape locked; Phase 0 first (capture-side, on post-deploy
   master).
3. **0y build** (post-deploy): plan + NORMATIVE S264 amendments incl.
   the one-line promo-pilot fallback.
4. **Watch items**: first live replaceOrders use (protocol in
   `raceday_0x_0z_review_s264.md`); first live SP fill (minus the
   PERSIST bet) + settled-oversize micro-test; first bonus-win
   auto-bank live smoke (still unproven); backup path of
   correct_matched_price had its first live exercise — fine.
5. Week plan: v3-done = 1a + 0y remain in scope; 0m + 0v trail.
