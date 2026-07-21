# Contracts spec — Code session report

**Session:** Session 77 Code (single bounded session).
**Date:** 2026-05-04 ACST.
**Brief:** `dr029/2_7_api_contract_versioning/contracts_spec_brief.md` (drafted Session 77).
**Output paths:**
- `dr029/2_7_api_contract_versioning/vps_client_contract.md` (§§7–11 appended)
- `dr029/2_7_api_contract_versioning/betfair_client_contract.md` (§§7–15 appended)

---

## §1 — Summary

Single bounded Code session. The developer-readable formal specifications for both `vps_client` v1.0 and `betfair_client` v1.0 contracts have been transcribed below the §7+ placeholders in their respective contract documentation files. Every typed shape traces back to a named anchor in §2.6 §5.1, §2.9 §6.1, §2.4, or §2.7 §2 / §3 / §3.5 (anchor traceback in §5).

**Pre line counts (operator-readable §§1–6 + placeholder):**
- `vps_client_contract.md` — 125 lines.
- `betfair_client_contract.md` — 172 lines.

**Post line counts (with developer-readable §7+ appended):**
- `vps_client_contract.md` — 714 lines (added 589 lines of §§7–11).
- `betfair_client_contract.md` — 1172 lines (added 1000 lines of §§7–15).

**Completion status.** Substantively complete. Both files have:
- §7+ substantive (placeholder italic replaced).
- Every call surface in operator-readable §2 has a corresponding sub-section in the developer-readable spec.
- Version history table updated with a Session 77 Code row dated 2026-05-04.
- Cross-file consistency (envelope shape, versioning framing, out-of-scope discipline) maintained per §7.

**Findings surfaced (§6 below):** five findings, all minor — none required mid-flight resolution; all noted for operator-Claude triage in Session 78.

---

## §2 — Method

**Sequencing followed.** Recommended "horizontal" sequencing per brief §7 was followed:

1. All six pre-reads read end-to-end before touching either output file. Path mismatch on two pre-read paths surfaced and noted as Finding §6.1.
2. `vps_client_contract.md` §§7–11 drafted first (smaller surface — six call surfaces, no streaming, no write side).
3. `betfair_client_contract.md` §§7–15 drafted second, reusing the envelope shape established in `vps_client` and extending the reason enumeration with Betfair-specific values plus the write-side `betfair_write_*` overlay.
4. Cross-check pass on consistency (§7 of this report).
5. Version history rows appended in both files.

**Time taken.** Single bounded session, completed within Session 77's continuation. No partial-coherence trade-offs needed; the work fit comfortably in one session because the locked specs (§2.6 / §2.7 / §2.9 / §2.4) had already specified every contract surface, every reason enumeration, and every typed envelope shape — the work was transcription rather than design as the brief framed it.

**Approach.** Each developer-readable surface section follows the per-surface format from brief §5.2 / §6.2 uniformly: endpoint path under `/v1/...`, Python signature, parameter spec table, return-shape Pydantic model, surface-specific failure modes, example call and response across the relevant envelope statuses. Pydantic v2 idioms used; type-annotation form for signatures; Adelaide local timestamps per DR-021.

**Tech-stack assumption locked.** Python with Pydantic v2 named at `vps_client_contract.md` §7 and reused at `betfair_client_contract.md` §7. The contract is the field set, not the library — equivalent typed-class disciplines (dataclasses, attrs, msgspec) named as acceptable substitutes if the implementing code chooses.

---

## §3 — vps_client developer-readable spec delivered

Section-by-section breakdown of `vps_client_contract.md` §§7–11 (lines 123–714).

### §3.1 §7 — Overview (lines 123–136, 14 lines)

Tech-stack assumption (Python / Pydantic v2). Boundary discipline reminder per DR-027 / DR-028 and §2.7 §2.4 (`vps_client` is the only file knowing `capture.db` schema; v3 modules consume typed shapes only). How developers should read the section.

### §3.2 §8 — Typed envelope (lines 137–206, 70 lines)

Three sub-sections:
- §8.1 Status enum (`fresh` / `stale` / `unavailable`).
- §8.2 Unavailable-reason enum — five values per §2.7 §2.3: `vps_unreachable`, `capture_db_locked`, `not_yet_captured`, `not_in_capture_window`, `genuine_absence`.
- §8.3 Envelope shape — generic over typed payload; concrete `FreshEnvelope[T]`, `StaleEnvelope[T]`, `UnavailableEnvelope`. Field semantics: `as_of`, `lag_seconds`, `retry_after`. Discipline note (v3 modules never see raw query exceptions).

### §3.3 §9 — Call surfaces (lines 207–636, 430 lines)

Six sub-sections, one per surface from operator-readable §2:

- **§9.1 Race metadata reads** (lines 211–282, 72 lines). Endpoint `/v1/race/{event_id}/metadata`. `RaceMetadata` Pydantic model with `RaceCode` enum (thoroughbred/harness/greyhound). All five `UnavailableReason` values applicable.
- **§9.2 Runner metadata reads** (lines 283–348, 66 lines). Endpoints `/v1/race/{event_id}/runners` and `/v1/race/{event_id}/runner/{selection_id}`. `RunnerMetadata` with `ScratchingStatus` enum.
- **§9.3 Results reads** (lines 349–424, 76 lines). Endpoint `/v1/race/{event_id}/results`. `RaceResults` carrying `RunnerResult` with `ResultSource` (Racing API / Betfair Win) and `StewardsStatus` enums; market-void flag, source-mix list.
- **§9.4 Bracketing reads** (lines 425–505, 81 lines). Endpoint `/v1/race/{event_id}/bracket?from={ts}&to={ts}`. `BracketingSeries` of `BracketSnapshot` per timestamp; `RunnerSnapshot` with top-of-book ladders, LTP, SP near/far, traded volume. Optional `selection_id` filter.
- **§9.5 BSP / sp_near / sp_far reads** (lines 506–563, 58 lines). Endpoint `/v1/runner/{event_id}/{selection_id}/bsp`. `BspReading` distinguishing pre-reconciliation projection-only state from post-reconciliation final BSP.
- **§9.6 Identifier-resolution reads** (lines 564–636, 73 lines). Endpoint `/v1/identity/resolve?market_id={mid}&selection_id={sid}`. `IdentityResolution` with `resolved` boolean and `lag_indicator_seconds`. Notes the §2.9 §4.2 12-hour escalation discipline as v3-side, not enforced inside `vps_client`.

### §3.4 §10 — Versioning mechanics (lines 637–685, 49 lines)

Five sub-sections covering path-based versioning, per-surface bumping, backward-compatible additions per §2.7 §4.1, breaking changes per §2.7 §4.2, deprecation warning emission with the 90-day window per §2.7 §4.3.

### §3.5 §11 — Out of scope (lines 686–714, 29 lines)

Five sub-sections per operator-readable §3 + §2.7 §2.5: operational reads, writes to `capture.db`, soft-book operational reads, analytics-derived fields, sports analytical reads. Each framed at formal-spec level (e.g. §11.2 explicit that "the lack of write methods is not 'not implemented yet'; it is 'v3 has no writable claim on the analytical layer.'").

---

## §4 — betfair_client developer-readable spec delivered

Section-by-section breakdown of `betfair_client_contract.md` §§7–15 (lines 170–1172).

### §4.1 §7 — Overview (lines 170–187, 18 lines)

Tech-stack assumption reused from `vps_client`. Boundary discipline per DR-028 + §2.7 §3.4 (one-file boundary against Betfair API churn). Reads-and-writes-share-the-module note (per operator confirmation; §2.7 §3.4). Decoupling from Betfair's own versioning. Reading guide.

### §4.2 §8 — Typed envelope (lines 188–275, 88 lines)

Four sub-sections:
- §8.1 Status enum reused from `vps_client_contract.md`.
- §8.2 Read-side unavailable-reason enum — six Betfair-specific reasons per §2.7 §3.3: `betfair_auth_expired`, `betfair_rate_limited`, `betfair_market_suspended`, `betfair_streaming_disconnected`, `betfair_market_not_found`, `betfair_api_unreachable`. Plus shared `genuine_absence` (the only `vps_client` reason that applies to live-side reads).
- §8.3 Write-side unavailable-reason enum — three values per §2.7 §3.3: `betfair_write_rejected`, `betfair_insufficient_funds`, `betfair_bet_placement_in_progress`. `betfair_write_*` prefix per §2.7 §3.5.
- §8.4 Envelope shape — generic `FreshEnvelope[T]` / `StaleEnvelope[T]` reused; `UnavailableReadEnvelope` and `UnavailableWriteEnvelope` distinct (write envelope carries `rejection_code` + `rejection_detail` for Betfair-side rejection codes).

### §4.3 §9 — Read surfaces (lines 276–658, 383 lines)

Five sub-sections:

- **§9.1 Operational live-pricing reads** (lines 280–378, 99 lines). Endpoints `/v1/market/{market_id}/prices` and `/v1/market/{market_id}/runner/{selection_id}/best`. `MarketPrices` and `RunnerBestPrices` shapes. Cache-as-of timestamp on every payload. Cadence parameters explicitly out-of-scope per Fix 4.
- **§9.2 Settlement reads** (lines 379–471, 93 lines). Endpoint `/v1/market/{market_id}/settlement`. `MarketSettlement` carrying the five anchor fields per §2.6 §5.1 (`market_status`, `settled_time`, runner-level `settlement_status`, market-void, per-runner-void) plus the three count fields per §2.6 §4.5 (`dead_heat_count`, `removed_runner_count`, `unexpected_state_count`).
- **§9.3 Sports-line query** (lines 472–545, 74 lines). Endpoint `/v1/event/{event_id}/markets?market_type={...}`. `SportsMarketVariant` list returned with `line_value` typed (None for MATCH_ODDS, float for HANDICAP/TOTAL).
- **§9.4 Scheduled-time reads** (lines 546–597, 52 lines). Endpoint `/v1/market/{market_id}/scheduled_time`. `MarketScheduledTime`. Empirical caveat per §2.9 §3.5 about `marketTime` mutability noted.
- **§9.5 Identifier-resolution checks** (lines 598–658, 61 lines). Endpoint `/v1/identity/check?market_id={mid}&selection_id={sid}`. `IdentityCheck` with `exists` boolean. Distinguished from `vps_client.identity_resolve` (analytical-side).

### §4.4 §10 — Streaming surface (lines 659–782, 124 lines)

Six sub-sections covering connection lifecycle (§10.1 — five `StreamingConnectionState` values), subscribe call surfaces (§10.2), streaming status read (§10.3), order cache shape (§10.4 — `UnmatchedOrder`, `MatchedPositionLevel`, `OrderPosition`), reconnect/heartbeat/message-dispatch contract (§10.5), and subscribe / dispatch upward (§10.6 — typed `MarketUpdate` and `OrderUpdate` events; concrete dispatch primitive — callback / queue / async generator / observable — left to Code at implementation).

**Cadence parameters NOT specified** per brief §6.1 + §2.7 §5.2 + Fix 4. The contract specifies the connection *shape*; cadence numbers (`heartbeatMs=5000`, back-off `1s/2s/4s/8s/30s` cap, etc.) appear in §2.4 as v3 build proper operational tuning, not contract surface.

### §4.5 §11 — Write surfaces (lines 783–995, 213 lines)

Three sub-sections:

- **§11.1 Bet placement** (lines 787–886, 100 lines). Endpoint `/v1/orders/place`. `place_bet` signature with `BetSide`, `PersistenceType` enums; PERSIST default per §2.4 §9.6. `BetPlacementResult` return shape. Audit-trail link to §12. Duplicate-submit debounce window behaviour per §2.4 §14.2.
- **§11.2 Bet cancellation** (lines 887–938, 52 lines). Endpoint `/v1/orders/cancel`. Optional `size_to_cancel` for partial cancel. Idempotent at bet-ID level per §2.4 §9.8.
- **§11.3 Bet replacement** (lines 939–995, 57 lines). Endpoint `/v1/orders/replace`. Atomic cancel-and-replace per §2.4 §9.2. §2.4 §14.6 atomicity-gap caveat noted (API-level atomic; stream events surface as separate legs).

### §4.6 §12 — Audit-trail discipline (lines 996–1059, 64 lines)

Three sub-sections:
- §12.1 Audit-log entry shape — `AuditLogEntry` Pydantic model with `WriteOperation` and `WriteOutcome` enums, `customer_order_ref` join key, `elapsed_ms` for latency analysis.
- §12.2 Where the log lands — durable, append-only, locally-accessible, never transmitted externally.
- §12.3 Single-cycle analysis discipline — `customer_order_ref` is the join key for cycle reconstruction per Cat 4.

### §4.7 §13 — Streaming-disconnect-blocks-writes behaviour (lines 1060–1102, 43 lines)

Four sub-sections covering block trigger (§13.1 — non-`SUBSCRIBED` states block placements), block behaviour upward (§13.2 — `BETFAIR_STREAMING_DISCONNECTED` envelope), why this lives in `betfair_client` not v3 (§13.3 — DR-028 second-integration-point protection), what is not blocked (§13.4 — cancellation and replacement permitted; reads return staleness rather than refusing).

### §4.8 §14 — Versioning mechanics (lines 1103–1147, 45 lines)

Six sub-sections paralleling `vps_client_contract.md` §10 plus §14.3 (decoupling from Betfair's own versioning per §2.7 §3.2 — four worked cases of how Betfair-side change does or does not bump `betfair_client`). §2.10 inventory writeup wave named at §14.4 as backward-compatible addition examples.

### §4.9 §15 — Out of scope (lines 1148–1172, 25 lines)

Five sub-sections per operator-readable §3 + §2.7 §3.5: analytical reads, soft-book reads, sports analytical capture, account management, market discovery beyond v3 day-one workflows. Auth-flow specifics, rate-limit budget allocation, cadence parameters carry-forward per §2.7 §5.2 noted at §15.5 close.

---

## §5 — Anchor traceback

For each call surface, the anchor in the locked specs that the developer-readable spec drew on. Anchor coverage is complete — every typed shape traces back to a named anchor.

### §5.1 vps_client surfaces

| Surface | Anchor | Notes |
|---|---|---|
| §9.1 Race metadata | §2.9 §6.1 (vps_client contract — race-level fields) | Operator-readable §2 race metadata bullet. |
| §9.2 Runner metadata | §2.9 §6.1 (runner-level fields) | Operator-readable §2 runner metadata bullet. |
| §9.3 Results | §2.9 §6.1 + §2.6 §5.1 (Betfair-side comparison shape) | Source identifier on each row distinguishes Racing API result from Betfair Win settlement per operator-readable §2. |
| §9.4 Bracketing | §2.9 §6.1 | Pre-jump market snapshot windows. |
| §9.5 BSP / sp_near / sp_far | §2.9 §6.1 + §2.10 (BSP fix landing zone — backward-compatible addition path) | §2.10 named in brief §5.3 as anchor; verified §2.10 file present at `dr029/2_10_external_analytics_scan/2_10_external_analytics_scan.md`. The reading-time projection vs reconciled-BSP distinction in `BspReading` is the §2.4 §13 BSP-reachability framing made explicit at the contract layer. |
| §9.6 Identifier-resolution | §2.9 §6.1 surface (c) | Passive sanity check; v3-side 12-hour escalation discipline noted as outside `vps_client` enforcement. |

### §5.2 betfair_client surfaces

| Surface | Anchor | Notes |
|---|---|---|
| §9.1 Operational live-pricing | §2.9 §6.1 (read surfaces) + §2.4 §5 + §2.4 §7 | Cadence deferred per Fix 4. |
| §9.2 Settlement | §2.6 §5.1 (5 fields) + §2.6 §4.5 (3 count fields) | All eight fields present in `MarketSettlement`. |
| §9.3 Sports-line query | §2.9 §6.1 surface (a) | Five-step flow §2.9 §2.2; this surface is step 3. |
| §9.4 Scheduled-time | §2.9 §6.1 surface (b) | §2.9 §3.5 empirical caveat noted. |
| §9.5 Identifier-resolution | §2.9 §6.1 surface (c) | Live-side check; distinct from `vps_client.identity_resolve`. |
| §10 Streaming | §2.4 (entire brief — §3 lifecycle, §4 auth, §5–6 subscription, §7 cache, §8 reconnect) | Cadence parameters explicitly out-of-scope. |
| §11 Write surfaces | §2.9 §6.1 (write-side framing) + §2.7 §3.5 (write-side tagging) + §2.4 §9 (REST order placement) | `betfair_write_*` reason prefix per §2.7 §3.5. |
| §12 Audit-trail | §2.7 §3.5 + Cat 4 single-cycle analysis discipline | Entry shape, durability discipline, single-cycle join key. |
| §13 Streaming-disconnect-blocks-writes | §2.7 §3.4 | Operator-confirmed contract behaviour, not v3-side decision. |

**No anchors missing or ambiguous in the substantive sense.** All shape fields, all reason values, all behaviours trace back to a named locked-spec anchor.

---

## §6 — Findings

Five findings surfaced. None required mid-flight resolution; all noted for operator-Claude triage in Session 78.

### §6.1 Pre-read path mismatches

The brief §3 names two pre-read paths that do not match disk:

- Brief: `dr029/2_6_settlement_model/2_6_settlement_model.md` → actual: `dr029/2_6_settlement_race/2_6_settlement_race.md`.
- Brief: `dr029/2_9_write_side_coherence/2_9_write_side_coherence.md` → actual: `dr029/2_9_write_side/2_9_write_side.md`.

**Severity:** trivial. Content fully available; the brief author's working folder titles drift slightly from disk-locked folder names. The §2.4 path matches; the §2.7 path matches.

**Recommended resolution:** brief author updates §3 pre-read paths in a future brief revision, or operator-Claude notes the alias for Session 78 lookup. No effect on this session's output.

### §6.2 Edit-locked §6 vs version history table update instruction

The brief §10 hard-limits state "Code does not edit the operator-readable summaries (§§1–6 in either file). Append-below-§7-only." The version history table sits inside §6. The brief §7 sequencing instruction nevertheless says "Update the version history table in each file with a Session 77 Code row dated today."

**Severity:** minor — apparent contradiction in the brief. Resolved here by appending exactly one new row to each file's table (no modifications to existing rows; no other §1–§6 content touched). The interpretation is that "the table is append-only governance log" per §2.7 §4.4, and appending a row is the table's intended growth path rather than a §6 edit in the broader sense.

**Recommended resolution:** brief author clarifies in a future edition. The convention adopted here (table-append-only as compatible with append-below-§7-only) is the natural reading.

### §6.3 v1.0 retirement reason value not yet in enumeration

`vps_client_contract.md` §10.5 references `endpoint_retired` as an enum value v1 surfaces would return after the deprecation window's 90-day end. v1.0's `UnavailableReason` enum (§8.2) does not include this value. The §10.5 text notes "the retirement enum value is a backward-compatible addition per §10.3 when the first deprecation cycle runs."

**Severity:** trivial. v1.0 ships without any v1-retired surfaces (every v1.0 surface is current); the value's absence is correct for v1.0. The first time a v2 surface issues, the corresponding `endpoint_retired` value lands as a backward-compatible addition.

**Recommended resolution:** none. Noted for future-self transparency. If operator-Claude prefers the value to land in v1.0 as a forward-compatibility hook, it is a one-line edit to §8.2 (and the parallel addition to `betfair_client_contract.md` §8.2) — a reasonable belt-and-braces choice but not load-bearing.

### §6.4 Order subscription not separately named in operator-readable §2

`betfair_client_contract.md` operator-readable §2 names "Streaming connection" as one surface and "Bet placement / cancellation / replacement" as three write surfaces. The §2.4 brief specifies that the Streaming connection carries both market data subscriptions (§2.4 §5) *and* an order subscription (§2.4 §6); the order subscription is the live-state source for unmatched orders and matched positions.

In drafting §10 of the developer-readable spec, the order cache shape (§10.4) and order-subscription dispatch (§10.6) were included inside the Streaming surface section, since both share the connection per §2.4 §6.1 / §7.1.

**Severity:** minor. The operator-readable summary's "Streaming connection" naming is consistent with §2.4's framing (one connection, two streams), but the developer-readable spec necessarily decomposes it. A reader of operator-readable §2 alone would not know that an order subscription cache is part of the Streaming surface; they would learn it from §2.4 or from §10 of the developer-readable spec.

**Recommended resolution:** operator-Claude considers whether to add a one-line clarifier to operator-readable §2 ("Streaming connection — covers both market data subscriptions and the order-state subscription"). Out of scope for this Code session per hard-limits.

### §6.5 Concrete dispatch primitive for streaming events left as Code's-call

`betfair_client_contract.md` §10.6 specifies typed `MarketUpdate` and `OrderUpdate` event payloads but leaves the concrete dispatch primitive (callback, queue, async generator, observable) as Code's call at implementation. The §2.4 brief §7.9 names "the cache is read-many, write-one — many consumers can read at once, only the I/O thread writes. Read-write coordination is via read-write locks or copy-on-write structures (Code's call when the brief executes)."

**Severity:** trivial — explicitly named as Code's-call by §2.4 §7.9. The contract surface is shape-only at v1.0; the implementation primitive is a v3 build proper choice.

**Recommended resolution:** none. The convention matches the §2.4 framing. Flagging for operator-Claude visibility only.

---

## §7 — Cross-file consistency check

### §7.1 Envelope shape

Both files use the identical three-status discriminated union — `EnvelopeStatus` enum with `FRESH` / `STALE` / `UNAVAILABLE` values; identical `FreshEnvelope[T]` and `StaleEnvelope[T]` generic shapes; identical `as_of` / `lag_seconds` / `retry_after` field semantics. **Consistent.**

`UnavailableEnvelope` is `vps_client`-only; `betfair_client` splits into `UnavailableReadEnvelope` and `UnavailableWriteEnvelope` per the §2.7 §3.3 and §3.5 read-vs-write distinction. The split is locked by the §2.7 brief, not a drift.

### §7.2 Reason enumerations

`vps_client.UnavailableReason` carries five values per §2.7 §2.3.

`betfair_client.BetfairReadUnavailableReason` carries six Betfair-specific values per §2.7 §3.3 plus shared `genuine_absence`. None of the other four `vps_client` reasons apply to `betfair_client` (no VPS, no `capture.db`, no ingestion-lag concept on the live API, no captured-window concept).

`betfair_client.BetfairWriteUnavailableReason` carries three `betfair_write_*` values per §2.7 §3.3 / §3.5.

**Consistent with the locked specs.** The split is structural, not a drift.

### §7.3 Versioning framing

`vps_client_contract.md` §10 and `betfair_client_contract.md` §14 use parallel sub-section structure: path-based versioning, per-surface bumping, backward-compatible additions, breaking changes, deprecation warning emission, 90-day window per §2.7 §4.3. `betfair_client` adds §14.3 (Decoupling from Betfair's own versioning) per §2.7 §3.2 which has no `vps_client` analogue (no upstream versioning to decouple from).

**Consistent.**

### §7.4 Out-of-scope discipline

`vps_client_contract.md` §11 and `betfair_client_contract.md` §15 each carry five sub-sections per their operator-readable §3. Both use formal-spec-level framing (e.g. `vps_client.md` §11.2: "the lack of write methods is not 'not implemented yet'; it is 'v3 has no writable claim on the analytical layer.'"). Boundary-protection rationale appears in both files referring to DR-028 "no second integration point."

**Consistent.**

### §7.5 Tech-stack and convention reuse

`betfair_client_contract.md` §7 explicitly names "same conventions as `vps_client_contract.md` §7" rather than re-stating. `betfair_client_contract.md` §8.1 explicitly names "Reused from `vps_client_contract.md` §8.1." Cross-references are explicit so a reader can pick up either file alone and get to the shared discipline.

**Consistent.**

---

## §8 — Self-assessment

### §8.1 Did the work fit one Code session?

**Yes, comfortably.** Single bounded session per brief §1 and §7. No partial-coherence trade-offs needed; no Session 33-style "complete-but-lost-coherence" risk surfaced. The transcription nature of the work (per brief §2) — every contract surface, every reason enumeration, every typed envelope shape pre-locked across §2.6 / §2.7 / §2.9 / §2.4 — meant Code's job was rendering, not designing, and rendering is fast.

### §8.2 Was the brief's anchor coverage sufficient?

**Yes.** Every typed shape in the developer-readable spec traces back to a named anchor in §2.6 §5.1, §2.7 §2 / §3 / §3.5, §2.9 §6.1, or §2.4. The brief's §5.3 and §6.3 anchor maps were sufficient to draft each surface without inventing contract surfaces, error semantics, parameter lists, or return shapes (per brief §1 hard line "What it is not. Not a design brief.").

The two potentially-thin anchor points — the BSP / sp_near / sp_far surface (anchored per brief §5.3 to §2.9 §6.1 + §2.10 §2 BSP fix landing zone) and the order subscription dispatch primitive (per Finding §6.5) — were both resolvable within the brief's allowance for "shape, not implementation."

### §8.3 Drift risks the next session should know about

Three drift risks worth flagging for Session 78 triage:

- **The dispatch primitive in `betfair_client_contract.md` §10.6 is shape-only.** When v3 build proper picks the concrete primitive (callback / queue / async generator / observable), the choice should be reflected back into the contract documentation as a backward-compatible §14.4 addition. Otherwise the contract documentation drifts from implementation reality. Low-risk because §2.4 §7.9 already names this as Code's-call at implementation.
- **The `endpoint_retired` reason value (Finding §6.3) is named as future addition, not present in v1.0 enumerations.** When the first v2 surface deprecation cycle runs, both files need a one-line addition to their §8.2 unavailable-reason enums. If operator-Claude prefers belt-and-braces, the addition can land now; if not, the future-addition note in §10.5 / §14.6 carries the discipline.
- **`vps_client.IdentityResolution` and `betfair_client.IdentityCheck` are deliberately distinct shapes** — analytical-side and live-side resolution carry different field sets (`IdentityResolution` carries `lag_indicator_seconds`; `IdentityCheck` carries `market_status` / `runner_status`). A future temptation to "harmonise" the two shapes would break the §2.9 surface (a)/(c) distinction. The §9.6 / §9.5 docstrings explicitly distinguish them; recording here for vigilance.

None of the three are blocking; all are visibility-only flags for Session 78.

---

**End of report.**
