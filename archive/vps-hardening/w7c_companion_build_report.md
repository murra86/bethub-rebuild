# W7c v3 Companion Build Report (S241, Wed 15 Jul 2026, 15:03 slot)

Contract: `vps_hardening_brief.md` §W7c — fenced, normal process, store/read plumbing only.
Gate verified at open: Day-3 deploy landed (sweep live, collector on W7 code, codes stamped).

## What was built

**End-to-end: the picker now knows what species it's picking.**

1. **VPS racing API** (racing-data-capture `bb89463`): `RaceSummary`/`RaceDetail` serve
   `racing_code` + `match_confidence` (additive, nullable; guarded reads so a pre-migration
   db can't 500 the route). racing-api restarted, verified live (Healesville rows serve
   `greyhound` / 1.0).

2. **vps_client §9.7** (bethub-v3 `3c56ebf`), contract changelog + §9.7 amended — every
   change §10.3 backward-compatible:
   - `code` fields now carry the store's stamped code. Legacy NULL-code rows fall back to
     THOROUGHBRED (the documented v1.0 constant) — pre-W7c behaviour is unchanged for
     exactly the rows that produced it.
   - DR-034 collapse coalesces code/confidence across twin fragments (most-complete
     fragment may be a legacy row; any fragment's non-null code is authoritative — same
     market id ⇒ same physical race; confidence falls back to min across twins, cautious).
   - `resolve_race(code=)` — the wrong-species guard for cross-code venue+number twins
     (Albion Park harness R7 vs greyhound R7). A code no candidate matches is IGNORED,
     never fatal (legacy rows must stay resolvable).
   - `ResolvedRace.match_confidence` + `low_confidence` (`< 0.9`) — the pick-time caution.
   - `MeetingSummary.code` = majority code of the venue's races (display hint; per-race
     truth on `RaceSummary.code`).

3. **v3 routes**: `GET /v1/bets/lookup/race` takes optional `code`; `ManualBetCreateRequest`
   carries optional `code` so the server re-resolve stays on the picked species. The
   `win_market_id` 409 cross-check remains the hard guard (proven in test: no code +
   more-complete wrong-species twin → 409; with code → 201).

4. **Picker UI (LogPastBet)**: venue rows show `Venue · T/H/G (n)`; race rows `R7 · H`;
   race options keyed `number::code` so cross-code twins are distinct picks (was: same
   race_number = colliding option values — the wrong-species trap); resolved hint shows
   the code; low-confidence resolve renders a role=alert caution with the score:
   "check the runner names look right before logging".

## Verification

- Backend **1464 passed** (8 new client tests incl. twin disambiguation, legacy fallback,
  coalesce, ignore-rule, caution; 1 new route test proving 201-with-code / 409-without).
- Frontend **192 passed** (2 new: twin picks pin the resolve; caution renders).
- `npm run build` clean. **Dist NOT swapped** — tonight's 22:03 app-idle slot per plan.

## Named follow-ups (not this pass)

- `_MANUAL_SPORT = "Horse Racing"` — the manual leg's sport label is still one string for
  all codes. Money-adjacent (leg stamping); deliberately untouched under "store/read
  plumbing only". Fold into a future fenced pass if honest leg labels are wanted.
- `ui/web/src/api/types.ts` (OpenAPI-generated mirror) not regenerated — the picker uses
  the hand-written `bets.ts` types; the mirror refreshes on its next scheduled regen.
- Two code-letter vocabularies coexist by design: sidebar `T|H|G` (api/racing.ts) vs
  lookup `thoroughbred|harness|greyhound`; the picker maps to letters at render only.

## State

racing-data-capture: VPS=Mac=GitHub `bb89463` (racing-api restarted on it this afternoon).
bethub-v3: `3c56ebf` pushed. App still serving the old dist until 22:03. Dogs-live flip
(collector `INCLUDE_GREYHOUNDS`) also lands at the 22:03 slot — after it, greyhound races
appear in capture and the picker's G rows become live rather than sweep-only.
