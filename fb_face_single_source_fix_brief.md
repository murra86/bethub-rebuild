# FB face single-source fix (build brief, S247)

**Status: COMMISSIONED S247 (Tue 21 Jul, morning) — build tonight
alongside the void-gap build. Frontend placement path: app-down dist
swap required; NOT during race hours.**

## The bug (live catch, 20 Jul — Sarie $13 TAB FB)

Operator armed a $13 credit; the hedge modal pre-filled the stake box
at $10 (`FB_STAKE_ROUNDING_INCREMENT = 5` rounds the face DOWN to a $5
multiple — W17.1 §5.4 v2-parity rule written for $25/$50 faces,
`HedgeModal.tsx:231`). The drift warning could not fire: it compares
the typed value against the already-rounded prefill, not the armed
face (`:404-408`). Result: bet logged $10, hedge sized for $10
($7.51 lay — exact for $10, not $13), drawdown consumed the full
$13.00. Realized cost ~$2 (lost leg, undersized lay); record
understates stake $3. Every odd-faced credit (stake-back refunds are
odd-faced by nature) hits this until fixed.

## The fix — single source of truth (operator-proposed, adopted)

1. **The manual FB face input box is the ONLY source.** Logging, hedge
   sizing, EV, and drawdown all read the box. No second path.
2. **Quick buttons ($25/$50/$100) POPULATE the box** — they are entry
   shortcuts, not a parallel value. Rounding lives only in the
   buttons; `roundDownToIncrement` is removed from the armed-face
   prefill path.
3. **Auto-selection / promo-bar arming populates the box with the
   credit's TRUE face** (13.00 stays 13.00).
4. **Submit-time parity check** (dev-lead addition): if box ≠ sum of
   armed credit faces, one plain confirm names the difference and the
   consequence ("draw $X and leave $Y armed" vs "ticket is really
   $Z"), and `draw_down_breakdown` records the amount ACTUALLY drawn.
   Deliberate part-use stays possible; silent mismatch becomes
   impossible.
5. **Drift warning repointed** at the true armed face (it currently
   guards against a drift the modal itself creates).

## Tests (red-before on 1 and 3)

- Armed $13 → box shows 13.00, logged stake 13.00, lay sized off 13.
- Quick button $50 → box 50.00; typing over it wins.
- Box $10 vs armed $13 → confirm fires, drawdown records 10.00,
  remainder stays armed.
- Existing $25/$50 flows byte-identical through the log path.

## Fences

- No backend money-path changes expected; if the drawdown-amount
  recording needs an API change it is additive only.
- `npm run build` is the frontend gate (vitest doesn't typecheck);
  dist swap app-down only.
- Historical rows are NOT rewritten (the $10/$13 row stands as logged;
  its story is documented here and in memory).
