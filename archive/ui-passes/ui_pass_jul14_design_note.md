# UI pass — operator bet-session notes, 14 Jul 2026 (S239 discussion → drafts)

**Source:** operator's rough notes from last bet session, discussed and resolved 14 Jul.
**Status:** DRAFTS — mock at `ui_pass_jul14_mock.html`; build commissions after operator walkthrough, and NOT before W7c lands (v3 repo owned by the S238 hardening runners until Tue evening).
**Fences:** no money paths anywhere in this pass. Settled-bet edit loosening is EXCLUDED (operator: delicate, dedicated future session). Betfair order EDITS (price/persistence change) are EXCLUDED (operator: later job, fenced brief when commissioned).

## In scope (10 → 8 items)

1. **BUG — runner list clipped at 10, unscrollable (race page).** Top priority. Fix = scrollable runner list (max-height + overflow-y), full field always reachable; density preserved.
2. **BUG — promo button shows no selected state.** Visible active treatment.
3. **Theme: black content on white frame, app-wide.** Operator-confirmed: content surfaces (cards, inputs, tables, panels) go black; the page beyond borders/margins stays white (e.g. Log Past Bet: black input areas, white page around them). One system, replacing the warm sheet — same token discipline as S237 (swap `index.css` vars, not per-page CSS).
4. **EV colours:** negative = red, 0–5% = amber, 5%+ = green (was grey for negative). Note: with the standing ~3pt haircut rule, amber ≈ "technically positive, actually marginal" — intended.
5. **BetLog columns:** race + race number, account, book, promo. Bet id removed from display (retained in data; available via row expand).
6. **Same-race duplicate warning (burst safety):** amber non-blocking strip on the lay confirm card when the selected account-at-book already has a bet on that race. Never blocks (S236 principle).
7. **Free-bet auto-select in the race-page promo bar** when (a) exactly one FB credit in the account, or (b) all the account's FB credits are the same kind (e.g. 3×$50). Multiple kinds → manual, no guess. Extends S237's insurance-armed default.
8. **Persist/lapse READ-ONLY tag** on the race-page activity summary for Betfair bets on that race. Data already on the current-orders read path (`persistence_type` in betfair_client `_translation.py` / `current_orders.py`) — serialize through the activity feed, render tag. NOTE for walkthrough: placement currently defaults PERSIST (`_translation.py:368` fallback) — the tag may reveal the operator's lays are persist, not lapse as assumed.
9. **Results lookup** — surfaced in the BetLog settle door (and race page where natural): pull the race result through the existing vps_client results read so manual settlement doesn't require looking results up elsewhere. Expectation set with operator: thoroughbred = full placings (subscription feed); harness/dogs = winner-level (Betfair-derived), dogs only from the W7 deploy forward.
10. **BF Close column (operator upgraded from deferred → IN SCOPE, 14 Jul):** Betfair projected BSP (`sp_near`) per runner on the race page — green ▼ shortening / red ▲ drifting vs current price. Justification: plumbing verified COMPLETE end-to-end (betfair_client `_translation.py:525` + `_stream_parser.py:300` + `live_pricing.py:56` + frontend type `api/racing.ts:75`) — nobody ever rendered it; the table is being reworked in this pass anyway, so marginal cost ≈ one column. Pairs with the existing Trend arrow (direction + destination).

**Column rule (operator, walkthrough feedback): the runner table RETAINS every existing column** — Runner | BF Back | BF Lay | Matched | Raw EV | Promo EV | Soft Odds (input) | Trend | Actions — plus the new BF Close. Both EV columns get the item-4 colour bands.

## Deferred (named, not dropped)
- **Settled-bet edit loosening** (promo-attached/Betfair refusals) — dedicated session; operator will bring the specific bet he hit.
- **Betfair order edits** (upping lay price, lapse→persist as jump approaches) — later fenced money-path brief; the read-only tag is deliberately its groundwork.
- **SP-based FB hedging (operator, 14 Jul — dedicated fenced brief when commissioned):** Betfair's third persistence type `MARKET_ON_CLOSE` ("Take SP") converts the unmatched lay to an SP bet at the jump automatically — no editable moment exists at SP-set. Two shapes: **Shape 1 (recommended first)** = Take-SP option in the quick-lay with equalisation maths done at placement against projected SP (`sp_near`); for an SP lay the LIABILITY carries and stake self-adjusts to liability/(SP−1), which keeps the FB-wins vs lay-wins outcomes near-equal across realistic SPs (operator's $50@5.50 example: liability varies only ~$4 across SP 5.5–6.6). **Shape 2 (heavier, later)** = pre-jump re-equalisation worker replacing unmatched orders at T−N secs (replacement.py/cancellation.py exist) — unattended live-order automation at jump time; attended-only rule + jump-timing risk; only consider after Shape 1 live-proven. BOTH require money-path chain work beyond placement: reconciliation/settlement of SP-converted bets, placement audit for the new persistence type, adversarial review of the equalisation maths. Slot: after this week's builds settle.
- **Projected closing price per runner (operator, 14 Jul):** show Betfair's near price (projected BSP) on the race page as a drift/shorten indicator. Ties directly to price-pressure research cycle-1's top NOW signal (projected-SP convergence gap); capture already stores `sp_near`/`sp_far`; first step per `implementation-review-prep.md` = verify sp_near serialized in `/prices`. Natural companion to the order-edit job.

## Sequencing
Mock walkthrough (operator) → build brief locked → build AFTER W7c dist swap (Tue evening) so one hand in v3 at a time; ships as one pass with `npm run build` gate + app-down dist swap.
