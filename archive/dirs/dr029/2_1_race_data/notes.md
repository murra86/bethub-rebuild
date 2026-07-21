# Inspection-session notes (Code, 2026-04-30 ACST)

Tiny carry-over notes from the inspection. Things that didn't fit the main report cleanly but a future session may want to know.

## Code-stratification heuristic — choices made during execution

- `race_class` was checked as a possible code discriminator but its distinct values are uniformly thoroughbred-only (BM58, MDN-SW, CL1, Listed, etc.); harness and greyhound rows have no `race_class` value at all. Cannot be used as a code splitter.
- `meeting_type` (METRO/PROVINCIAL/COUNTRY/blank) and `track_type` (turf/synthetic/blank) overlap inconsistently — same venues (Flemington, Doomben, Royal Randwick, Cranbourne) appear in both blank and populated sets. Not usable as a code splitter on their own.
- `state` IS the cleanest code splitter: AU 8-states populated → thoroughbred (verified via venue list — Flemington, Doomben, Royal Randwick, etc., all canonical thoroughbred); state blank → AU non-thoroughbred (verified via venue list — Albion, Menangle, Globe Derby, Melton, Penrith, etc., canonical greyhound/harness venues). The harness vs greyhound split within `state IS NULL/blank` was done by `race_name` keyword (`pace`/`trot`/`mobile`/`stand`) — verified against sample race_name values like `R5 1720m Pace M` (clearly harness). Greyhound is the residual; this misclassifies any harness race whose race_name lacks the keywords. Operator-Claude can refine if the bucket ambiguity matters for an interpretation.

## Query-execution decisions

- `betfair_snapshots` cadence queries used the full live-capture window (60 days), not a sampled subset. SQLite handled the queries within ~30s each — full-window computation was tractable so no sampling was applied. Brief authorised sampling 500 races × 3 codes × 2 windows; not exercised.
- For `actual_jump_time`, two derivation paths were considered: (a) `betfair_historical.actual_off_time` (used — half coverage in 12m, zero coverage in 30d) and (b) the first `betfair_snapshots` row with `snapshot_phase='POST_START'` (not pursued — would require ~1.6M-row scan and the live-capture window has bigger structural problems anyway). If §2.6 settlement model wants a robust derivation, the second path is computable but expensive.
- For settlement-lag distribution: `races.updated_at` is updated by every snapshot-batch write (so it tracks last-snapshot rather than first-result-observation). This makes it useless as a result-observation proxy. The computed difference `updated_at - actual_off_time` returned implausible numbers (p50 ≈ 9,500 days) confirming the proxy is unsuitable. Reported as "structurally non-measurable" rather than fudging through.
- Inter-snapshot interval queries grouped by `(race_id, runner_id)` for per-(market, runner) cadence. Market-level snapshots (no `runner_id`) were excluded from the cadence calculation. Including them would mix runner-level and market-level cadence which have different structures.

## Operator-side launchd hygiene observation (full)

Full output of `launchctl print gui/501/com.bethub.vps-tunnel`:

- `runs = 11992`
- `last exit code = 126`
- `state = not running`
- `runs every 30 seconds`
- `properties = runatload | inferred program | managed LWCR | has LWCR`
- inherited environment: `SSH_AUTH_SOCK = /private/tmp/com.apple.launchd.wSDmzozLYn/Listeners`

Recent `/tmp/bethub-tunnel.log` entries are 30 lines of identical:
```
/bin/bash: /Users/tim/Desktop/Projects/bethub-v2/scripts/vps-tunnel.sh: Operation not permitted
```

A direct invocation by the operator's interactive shell (which has Full Disk Access) succeeds — the script itself works.

## Things the brief asked about that aren't reported

- `bookmaker` column allowed values: confirmed `pointsbet`, `ladbrokes`, `neds`, `unibet`, `playup`, `sportsbet`, `tabtouch`. No others present. PalmerBet absent (Cloudflare-blocked, documented out-of-scope). TAB API absent (per `data_layer_current.md` §5.1, "needs TAB Studio registration", not confirmed live).
- `match_evidence` JSON column on `races` carries cross-ID mappings between Betfair and the various bookmakers — useful for the §2.10 source-survey work, not material to this inspection beyond schema discovery.
- `betfair_historical.match_method` distinct values were not exhaustively enumerated; sample showed `'venue+race_no+time_exact'` and the schema comment lists `'market_id', 'venue_date_race', 'name_fuzzy', 'unmatched'` — likely the full set.

## Performance notes (for future sessions running similar inspections)

- DB is 2.0 GB with WAL active. Read-only mode (`mode=ro`) was used throughout; `.timeout 60000-600000` on individual queries. No queries timed out.
- Heaviest queries (cadence percentiles with window functions over 1.6M snapshot rows × 8.3k races) ran in 30-60 seconds each — comfortable.
- SSH-and-SQLite path (rather than HTTP API) was the right call for this inspection. The data API at `127.0.0.1:8400` is not built for ad-hoc analytical queries.

End of notes.
