# Take-SP brief — adversarial review round 1 (S240, 2026-07-14)

Three independent agents reviewed brief v1 (design attack / governance-contract / ops pre-mortem).
**All three: approve-with-amendments; none: redesign.** All amendments applied → brief v2 (tagged
D-n / G-n / O-n inline). This record condenses the findings; severity as issued.

## Blocking (each independently capable of losing money or trust)

- **G-1 CRITICAL — transient conversion-window read terminalises wrong money.** Partially-matched
  Take-SP lay absent from current orders while market suspended/in-play (+ `settled_time=None`,
  the S223 reality) falls to `absent_resolved_pre_settlement_full` (`reconciliation.py:396–408`)
  → FINAL_FULL at the stale pre-jump fragment, no later correction. B3 HIGH-1 guarded only the
  zero-matched branch. → mandatory fixture 6(c); Stage-0 capture must sample the window; whether
  the bet id/visibility survives conversion is empirically unknown → capture-first.
- **O-1 CRITICAL / D-4 — cash-lay default extends past the evidence.** FB "lose-side never
  negative" does NOT carry to cash: worked example −$30 realized vs −$1 planned (still better than
  −$45 lapse; win-side plan-identical). Backtest + live-proof v1 covered FB only. → D3′ reopened;
  panel recommends FB-only default; all-lays option requires honest cash sub-line + cash proof
  cycle + no-walk-away rule.
- **D-2 HIGH / O-3 HIGH — the UI would lie.** `Racing.tsx:508–510` toast calls MOC "lapses at the
  jump"; `onPlaced` meta typed PERSIST|LAPSE; in-modal partial banner alarms on the expected
  Take-SP state → double-hedge scenario ≈ −$135 on a "locked" cycle. v1's "gap is ONLY HedgeModal"
  was FALSE. → items 4/5 rewritten; Racing-route-level string tests (vitest doesn't typecheck).
- **G-3 HIGH / D-6 — "no contract change" was FALSE.** `bsp_market` serialized nowhere in the repo;
  guard requires contract §14.4 additions (`bsp_market`, `turn_in_play_enabled`) + v1.7 changelog +
  route + types.ts. Declared in-fence in v2. (`place_bet` §11.1 is the contract surface, not
  "place_lay".)
- **G-2 HIGH — default-ON at ship contradicted the brief's own live-proof gate.** → staged rollout:
  Stage 1 option-only, Stage 2 default flip after signed proof, per race code.
- **D-1 HIGH — BSP-flag gating alone is wrong for greyhounds.** Greys ARE BSP markets but never
  turn in-play → MOC likely a silent no-op with UI-manufactured false confidence (worse than
  today's truthful LAPSE). → gate on `bsp_market && turn_in_play_enabled`; greys keep LAPSE until
  code-G live proof.

## Majors folded into v2

- **O-2 HIGH:** no in-tool cancel — Take-SP placement is final from the tool; operating rule +
  phase-2 cancel-button candidate named beside D2.
- **O-4 HIGH / G-7:** conversions invisible next morning (persistence stored nowhere; failed
  conversions silent) → write-only `persistence_type` column + SP display tags + detail-dict
  carry + first-10-conversions eyeball rule.
- **D-3:** resize-UP shape (`sizeMatched > sizeRequested`, BSP below limit) violates
  `record_builder.py:285–289` invariant — the FIRST live conversion will have this shape →
  fixtures 6(a)/(b).
- **G-4:** fixtures-before-capture repeats the S223 mistake → Stage-0 capture-first; STOP
  pre-authorized as a planned exit (B3 pattern).
- **G-5:** v1's item-7 oracle (winner-less hold) contradicted designed semantics — removed runner
  ⇒ void/FAILED $0 (`reconciliation.py:441–460`); abandoned market ⇒ carry-forward → park → manual
  queue (O-7).
- **D-5:** headline stat is unconditional; conditional on conversion (drifters) BSP usually lands
  ABOVE the limit — "Why" reframed: recovery smaller than plan, never worse than lapse (FB).
- **G-6 / O-6:** live-proof under-fill design would itself trip the $10 floor; sizing rule +
  expanded proof matrix (BSP≠limit, sub-$10 cancel, grey attempt, cash cycle if D3′(b)).
- **D-7 / O-8:** $10-floor warning computed on the wrong quantity (full liability ≈ never <$10);
  reworded to remainder semantics + post-placement remainder-liability banner from
  `size_remaining`.
- **D-8 / O-9:** late-catalogue re-seed can flip the default under the operator's eyes; absent
  bsp data must HIDE the option; placement-surface persistence readback.
- **G-8:** greyhound default flip must be explicit + sample's G-code coverage unconfirmed; D1/D3
  provenance to session record at build close.
- **G-9 LOW:** contract §15.4 still says listClearedOrders out-of-scope (stale since S228) — fold
  correction into the v1.7 changelog entry.
- **G-10 LOW:** assert audit entry carries MOC; orchestrator's hard-coded PERSIST
  (`betfair_adapter.py:210`) is intentional — one-line note added so nobody parameterizes it.

## Verified-true v1 claims (for balance)

PersistenceType enum + route (`racing.py:579`, mapping 976–980) + `racing.ts:277` all MOC-ready;
HedgeModal genuinely the only *placement-input* gap; resolvers never read persistence
(reconciliation is the sole matched-truth conduit); current/cleared-order shapes MOC-capable;
fence OUT list enforceable; STOP-rule discipline right shape; FB economics sound in every reachable
state (thin pools, floor cancels, abandonments) — the core idea survives attack.

**Net effect on scope:** small build became a staged build with a capture-first step; effort
½ → ~2–2½ sessions + two racing-day touchpoints. Operator sign-off needs: brief v2 approval +
D3′ (cash default: panel recommends FB-only) + D2 (phase 2: park or commission).
