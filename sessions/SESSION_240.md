# Session 240 — 2026-07-14 (13:28–~17:00 ACST)

## What was delivered

1. **Session open + standing checks:** VPS health all clear ×3 ticks; one known alert only
   (00:53 UTC pre-refinement, harmless). Runner schedule re-created (item 8). No slots missed
   (opened 13:28, stint B was 16:03).
2. **Pi gateway restored after operator's Mac restart:** root cause = Tailscale stopped on the
   Mac (profiles point at the Pi's Tailscale IP; fail-closed worked as designed). Pi itself was
   healthy throughout. All 3 lanes re-proven end-to-end over Tailscale+auth (Kate/Optus,
   Sarie/Vodafone, Mads/Vocus). **Tailscale added to macOS login items — recurrence closed.**
3. **BetLog zero-P&L display fix (operator request):** settled $0 (free-bet losses) now renders
   unsigned grey, not green "+0.00"; `+` reserved for true positives page-wide. 188 frontend
   tests green; staged-build + atomic dist swap under the running app; pushed `6180b51`.
4. **FB-flow check (operator raised duplication):** confirmed UI-pass brief item 7 (auto-select)
   covers the unambiguous-credit ask; S237 single-pass pre-fill wiring documented; UI-pass runner
   amended to test the pre-fill chain end-to-end + fix display-side gaps; live walkthrough flagged
   for next racing day.
5. **Take-SP investigation → backtest → brief v2 (the day's big analytical arc):**
   - Mechanism confirmed: MOC persistence = pre-jump instruction, liability preserved on
     conversion; client/route/types already MOC-capable.
   - Backtest (`fb_lay_take_sp_analysis.md`): take-SP recovers ~$61 on the 2 real partials
     (Capital Asset $38.95 vs $4.60; Catch The Red Eye $31.18 vs $4.43); wide sample 13,798
     runners: BSP ≤ closing lay 98–100%. Live exhibits same day: Aged Care (pending — check at
     settlement) + Paw Lonnie ($50 FB unhedged lost → $0).
   - Brief drafted → operator resolved D1 (default ON) → **3-agent adversarial review, all
     approve-with-amendments** (`take_sp_brief_review_round1.md`): G-1 CRITICAL conversion-window
     wrong-money path (reconciliation.py:396–408 terminalises stale fragment), UI-lies findings
     (Racing.tsx toast), bsp_market serialized nowhere (contract v1.7 additions in-fence), staged
     rollout, capture-first fixtures. **Brief v2 written with all amendments**
     (`take_sp_build_brief.md`); operator accepted panel rec → **D3′ = FB-mode-only default**.
     Build awaits formal sign-off + D2, slotted post-hardening.
6. **Day-2 stint B (hardening build, 16:03 runner):**
   - **W7 CODED NOT DEPLOYED, `6ea50aa`** (VPS=Mac=GitHub, tree clean, 61 tests green on the box,
     services untouched): shared `storage/racing_day.py`; paginated per-event-type discovery w/
     page-cap ALERT; per-market venue-local race_date (killed the UTC-today two-writers
     fragmentation bug; bookmaker query date → AU racing day); racing_code stamped at discovery;
     dogs 4339 behind `INCLUDE_GREYHOUNDS` default OFF (flip at W7c swap); collector collision
     valve (cross-code diverts to sweep's suffixed key; NULL-holder: dogs divert, harness passes).
   - **W5 formalized + CLOSED:** standing_instructions.md Cat 2 block + session-open SKILL.md
     Step 5c + zip; operator re-uploaded both to Project KB same day.
7. **Nuns Chorus mis-settle corrected (operator request):** FB back was accidentally settled
   Lost; runner won. Reverted the single mistaken field to pending, re-settled Won through the
   normal door → +$170.00, cycle nets +$35.60 (= the computed lock). Both log lines visible to
   the money check as operator_manual. Operator's blocked edit attempts noted → strengthens the
   deferred "settled-bet edit loosening" item (relevant before Saturday's settle-heavy day).
8. **Operator decisions this session:** Friday 17 Jul v3 TOOL DATA RESET commissioned + scope
   confirmed (all-settled precondition → backup → scoped wipe keeping setup tables → day-0
   re-seed from operator balances → verify to the cent); remaining builds front-loaded Friday
   morning (07:07 readiness runner added); take-SP D1/D3′ as above.

## Open items / next session (S241)

- **FIRST ACTION AT OPEN: re-create the runner schedule (memory item 8) and RUN MISSED SLOTS in
  order.** Likely missed by a same-evening or next-morning open: **20:23 Aged Care settlement
  check** (record actual vs take-SP counterfactual $35.62 in `fb_lay_take_sp_analysis.md`); if
  opening after Wed 07:11, the **Day-3 deploy** runs at open (pre-racing constraint applies).
- Schedule remaining: (b) deploy Wed 07:11 → (c) W7c 15:03 → (d) swap+dogs-live 22:03 →
  (e)(f) drills Thu 06:05/10:33 → (g) UI pass Thu 13:03 (amended: FB pre-fill tests) →
  (h) swap 22:33 → (i) close-out Fri 05:03 → (k) readiness Fri 07:07 → (j) RESET Friday
  operator-present. Alert watch 2-hourly 09:23–21:23.
- Take-SP brief v2 sign-off + D2 (post-hardening).
- Settled-bet edit loosening: candidate for post-reset session (operator hit it twice today).
- FB pre-fill live walkthrough with operator, next racing day.

## Governance notes

- racing-data-capture Mac→VPS git flow documented: origin=VPS working repo rejects
  checked-out-branch push → push github + temp branch, ff-merge on box.
- Brief v1→v2 structural change (staged rollout, capture-first) is review-driven, recorded in
  `take_sp_brief_review_round1.md`.
