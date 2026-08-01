# S259 change review — run in S260 (30 Jul 2026)

**Operator commission:** "review all the changes that have been implemented in this session to ensure that they're all appropriate, rigorous, and correct and they won't lead to any risks or disruption or downstream issues." Scope: both repos AND the live data actions.

**Method:** three independent read-only reviewers (capture commits / v3 commits / live data), instructed to skip everything S259's own verification round already found and fixed. Everything real that they found has been **fixed, tested, and shipped in this session** — nothing is left open except two design items noted at the end.

---

## Verdict in one paragraph

The S259 work held up well. The live data actions are clean: the 2,530-market twin merge reconciles to the row with zero orphans and the backup intact, the Sarie cash→free-bet correction used the sanctioned event shapes end-to-end, and the Phase 0 migrations are exactly as designed. The money-path code (promo correction + undo button) passed every check without a finding. The reviewers found **six real residual defects** — none data-corrupting, none blocking tonight's repair — of which five are already fixed and deployed; the sixth (recycle starvation) needs a design choice and is folded into the international Phase 1 review.

---

## Live data actions — ALL PASS (no action needed)

- **Twin merge:** journal `race_row_merges` = 2,632 rows across 3 runs (main run exactly the reported 2,530). 5 random spot-checks: canonical exists, donor gone, runner counts ≥ pre-image, zero drops. Orphans: 0 across runners / betfair_snapshots / bookmaker_snapshots. Backup present (5.1 GB). Wagga pair 1.260468539/1.260468569 correctly still unmerged behind the identity gate.
- **Sarie correction:** rejected `promo_cash_credited` supersession → linked $10 `free_bet_credited` → `bet_edited` audit row → backup present. Cash derives 1153.90 ✓. FB derives 0.00 — **benign**: the free bet was deployed at 15:30 same day (bet settled lost), after the 13:53 correction.
- **Phase 0 migrations:** columns + `jurisdiction_config` (AU=1, GB=0, IE=0) as designed. 317 races already carry `country` / 195 `local_race_date` — small pre-stamped set, flagged to the Phase 1 build.

## v3 code — money path CLEAN; 3 defects fixed (`fa594c2`, pushed)

`329c42f` verified against all three standing rules: raw inserts on a bare connection, lockstep balance reads (`balance_derivation` + `cash_flow` both exclude superseded/non-finalised), sanctioned revocation shapes only. Undo button cannot fire on cash/spent credits; double-fire blocked client- and DB-side. Accounts redirects carry query+hash; no orphaned links.

Fixed this session:
1. **Launcher startup could kill -9 Chrome** — `BetHub.command` startup stale-port clear lacked `-sTCP:LISTEN` (the exact root cause `02442f0` fixed at shutdown, second lsof site). After an unclean exit, relaunch could kill Chrome's process via its lingering CLOSE_WAIT socket.
2. **Feed could stomp a half-typed sub-$2 price** — after 0i made CLEAR release the box, a feed tick could overwrite an in-progress retype. Re-sync now skips a focused input; blur catches up.
3. Tab-close URL match tightened (`//localhost:PORT/` + `127.0.0.1`; was a bare `contains`).

Tests after fixes: tsc clean, 494 vitest, 1949 pytest, dist rebuilt.

## Capture code — 4 defects fixed + DEPLOYED (`f50d4b2`, live 18:16 ACST, collector restarted into a verified gap)

1. **CONFIRMED — market-adopted rows froze volatile metadata.** Post-twin-fix, the adoption path was fill-if-null only, so `scheduled_start` / track condition never updated after first sighting — stale starts fed liveness NEAR windows, the restart gap check, and the twin terminal fence. Fixed: `_VOLATILE_COLUMNS` whitelist (scheduled_start, track_condition_raw/-, rating) is last-write-wins, never nulled; identity columns untouched.
2. **Sweep bypassed the cross-code refusal** — `identity_sweep.py` didn't pass `racing_code` into `resolve_by_market`, leaving the S259 greyhound-vs-thoroughbred ban inert on the subscription path (the Wagga mis-stamp class). Fixed + None-return guarded (`code_refused` action, no crash, no runner writes).
3. **Coverage re-probe was per-discovery-pass (~48/day), not daily** — `_probed` now carried across `CoverageIndex.load()` reloads; fail-open preserved (restart re-probes once, new day always probes).
4. **Proxy-auth probe alerted on any transient failure** — now requires 2 consecutive failing probes (file-based streak, same prior art as W3); a sustained 407 still alerts by the second 15-min cycle, so the 30 Jul Decodo detection speed is preserved.

Tests: 385 → 396, 0 failed. Twin-repair path untouched; pushed to VPS + GitHub.

## Open items (tracked, not blockers)

- **Recycle starvation (LIKELY):** under continuous operation the 04:15–05:30 gap-aware recycle may never find a gap (`near_races()` counts ALL races incl. overnight internationals; today it gave up at 05:30). Needs a design choice (count tracked/served races only, or alert after N skipped days) — folded into the international Phase 1 review, which changes the overnight regime anyway.
- **Tomorrow's recompute may silently not run:** tonight's repair can hold its systemd slot past both recompute timers (Persistent=false). Tomorrow's check must verify `logs/coverage_recompute.log` has real output — absence of an `au_suppressed` line is not a pass.
- Minor, noted only: `PRAGMA foreign_keys=ON` inside an open txn in identity_sweep is a no-op (backstop only); the au_suppressed metric can't see AU venues with blank state + NULL country.
