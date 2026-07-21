# UI Pass Build Report (S241, Thu 16 Jul 2026, 13:03 slot) — 12/12 items

Contract: `ui_pass_jul14_build_brief.md` (operator-APPROVED 14 Jul; mock v3).
Gates verified at open: W7c landed (`3c56ebf`) ✓, kill drill done ✓.
Commit: bethub-v3 `34b0e87` pushed. Suites: backend **1464**, frontend **207**, `npm run build`
clean. **Dist not ceremonially swapped** — the 22:33 app-idle slot releases it (note: the app
has been closed all day, so the built dist is already on disk exactly as Tuesday's was;
22:33 = verify-idle + record, same shape as last night).

## Items (all landed)

1. **Runner scroll + density**: table scrolls inside itself (`max(300px, 100vh−330px)` —
   ≥10 compact rows guaranteed, grows with screen), sticky header, bottom-fade hint
   "all N runners — scroll for the full field" on >10.
2. **Promo selected state**: armed promo = fill + border + ✓ (buttons; select fill+border).
   Scoped so person/book chips don't grow checks.
3. **Theme**: token-value swap in `index.css` to the mock's black-sheet palette (sheet
   #111417 / raised #1a1e23 / ink #e8e6e1 / line #2e343b; navy #3d6db5 / rose #d16b80;
   status greens/ambers/reds lifted). Page frame stays white. No per-page forks — every
   component follows the vars. Operator glance-check on next app open (one revision round
   expected per brief).
4. **EV bands (locked)**: negative red / 0–5 amber / 5+ green — odds table both EV columns
   + confirm-card snapshot. Boundary-tested at −0.1/0/4.9/5/5.1. (Burst review renders no
   EV — confirmed, nothing to band there.)
5. **BetLog columns (locked list)**: Placed · Race+No (venue+R# from the leg; new
   `betfair_market_name` on feed legs) · Runner · Account · Book · Side · Stake@odds ·
   Promo (FB marker folds in) · State. P/L and bet id live in the row expand.
6. **Duplicate warning**: amber non-blocking strip on the confirm card, operator-locked
   text, activity-feed lookup (shares the board's query cache).
7. **FB auto-select (additive)**: sole credit, or several identical → oldest auto-selected
   with "✓ auto-selected — …" note; mixed kinds stay manual; operator toggle-off retained;
   fires once per FB-mode entry, never overrides a manual pick.
8. **Persist/lapse tags (read-only)**: new read-only route
   `GET /v1/racing/markets/{id}/current-orders` (betfair_client §9.8 list_current_orders);
   feed items now carry `betfair_bet_id` as the join key; board polls 15s and tags Betfair
   rows PERSIST (solid green) / LAPSE (dashed grey) / TAKE SP. A settled order drops off
   the live map and its tag disappears — correct by design.
9. **Settle-door results**: first consumer of the §9.7 results surface. vps_client
   additions (all §10.3 additive): `RunnerResult.runner_name`, `RaceResults.track_condition`,
   `ResolvedRace.capture_race_id` (the §5.6 handle). New endpoint
   `GET /v1/bets/{bet_id}/race-result`: leg → Adelaide day + venue + R# → resolve →
   results; every miss = `available:false` → BetLog renders "no result captured yet".
   Placings render "1. Name (SP x.xx) · 2. … — Good 4"; thoroughbred full, winner-level
   naturally where that's all the store holds.
10. **BF Close**: `sp_near` per runner (already served end-to-end; never rendered until
    now), green ▼ / red ▲ / grey — vs the back/lay mid (±1%), column order LOCKED:
    # | Runner | Matched | BF Back | BF Lay | Raw EV | Promo EV | Soft Odds | BF Close |
    Trend | Actions. Saddlecloth # split into its own column.
11. **Live conversion/EV at the edited lay price**: recomputes as the price field changes;
    FB → conversion % banded green ≥65 / amber 60–65 / red <60 (S231 baseline);
    cash → plain EV%. Display-side recompute only.
12. **Modal cleanup**: (a) cash/FB radios → two-segment control, selection visually bound
    to its own label; (b) permanent FREE BET explainer REMOVED, replaced by a conditional
    one-line amber warning only when typed face ≠ armed credit.

## Fences (checked)

No money-path files touched (`place_lay`, settlement resolvers, reconciliation, credit
maths, record_builder untouched). Persistence is read-only display. Settled-bet edit rules
untouched. All new backend surface is GET-only. Contract additions all §10.3
backward-compatible (changelog NOT yet amended for item 9's three additive fields — done
in this report's companion contract edit).

## Acceptance tests (all present + green)

Scroll presence · EV boundaries · auto-select one/identical/mixed · duplicate trigger +
non-blocking + silent case · persist/lapse tag join (soft rows untagged) · results absence
AND captured render · BF Close directions + null/missing-mid · conversion recompute +
59.9/60/64.9/65 bands · segment toggle aria association · FB-mismatch conditional +
explainer gone.

## Post-release operator catch (16:1x ACST) — BF Close request gap, FIXED

Minutes into live use the operator found BF Close empty 15 min pre-jump. Root cause: the
live-prices `listMarketBook` request asked for `EX_BEST_OFFERS + EX_TRADED` but NOT
`SP_AVAILABLE` — the sp block never arrived, so `sp_near` was permanently null despite
being translated, typed, and rendered end-to-end. The pre-build verification had checked
the serializer, not the request. Fixed (`4bd215c`): `SP_AVAILABLE` added (weight 25/200,
single market), regression test pins it. Requires one app restart to take effect.
Lesson: "is the field served?" must be verified at the REQUEST, not just the translator.

## For the operator walkthrough (next app open)

Theme is the subjective item — one revision round budgeted. Also new since yesterday's
W7c: T/H/G letters through the picker; the race page now shows dogs (captured from today).
