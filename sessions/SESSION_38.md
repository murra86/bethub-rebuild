# Session 38 — DR-029 §2.2 sports operational layer specified

**Opened:** 2026-04-30 17:58 ACST
**Closed:** 2026-04-30 ~20:00 ACST
**Tool routing:** Claude Chat
**Governing DRs invoked:** DR-029 (active arc, §2.2 specified), DR-027/028 (cross-DB discipline — confirmed not extending to operational layer), DR-024 (operating/analytical separation — framework §2.2 lives within), DR-026 (inline-snapshot pattern — referenced for sports bet record shape), DR-021 (timestamp).

## Anchor

`TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` returned `2026-04-30 17:58 ACST`. Anchored 58 min after Session 37 close.

## Pre-flight

Rebuild folder root state matches Session 37 close exactly: 7 canonical .md, dr029/ with scope + 10 artefacts in 2_1_race_data/. WIP at 105 KB. Scope at 31 KB.

## §2.2 specification — what was delivered

`architecture.md` gained a new top-level section: `## Operational layer — Betfair direct`. Total 122 lines added, structured as:

- **B.0** — what this layer is, what it isn't. Frames the operational layer as v3's read path to Betfair for operational consumers, parallel to `vps_client` for analytical reads against `capture.db`. Explicitly notes the layer writes nothing to disk, holds no retention, and reconciles with the analytical line by construction modulo cadence lag. Cross-DB boundary discipline (DR-027/028) does not extend here because the boundary is between v3's bet-data SQLite and capture.db; `betfair_client` sits on neither side of that boundary.

- **B.1.1** — sports page sources. v3's sports page sources from Betfair direct via `betfair_client`. Page filtered to pre-defined sports/leagues from DUR §4 (AFL, NRL, NBA, NBL, EPL, La Liga, Ligue 1, Serie A, MLS, International Cricket, Tennis majors, NHL, MLB, NFL, MMA). Core market types per sport family: Match (head-to-head, two-way for AFL/NRL/etc., three-way for soccer), Line (handicap), Total (over/under), Cricket-specific shapes. Read pattern is read-on-demand. Staleness/unavailability signalling via explicit "Betfair unavailable — retry" rather than stale-data-as-current; partial unavailability allowed.

- **B.1.2** — bet entry and the line ladder. The substantive UX shape lock. Match markets are direct selection. Line/Total markets use the line ladder pattern: operator types unsigned line value (e.g., "6.5"), v3 fetches Betfair's line-variant markets and renders an 11-line ladder centred on operator's typed value, both sides shown (Carlton-side / Collingwood-side for handicap; over / under for total), back/lay prices and best-back-size liquidity per row, "no market" placeholder where Betfair has no live market. Each priced row carries two trailing action icons emulating v2: ⚡ HedgeModal and 📝 LogBet. Both inherit resolved Betfair `market_id` + operator-typed line + operational snapshot. Ladder pattern is sport-agnostic. Failure-mode handling specified including the empty-state escape hatch when typed line is far outside Betfair's offering range. Auto-line-matching named as v3.1+ candidate dependent on §2.5's source implementation.

- **B.1.3** — favourite inference for handicap markets. **Simplified per operator-call mid-session.** Original draft had a 5%-implied-probability tolerance rule. Operator pulled back to plain rule: shorter-priced side in head-to-head market is favourite, full stop. Rare pick'em case (both sides price near-flat, line market exists at zero or near-zero) falls through to label-pick. Edge case for head-to-head temporarily unavailable: ladder still renders with neutral side labels; bet logs against `market_id` resolved at confirm time.

- **B.1.4** — sports auto-settlement. Betfair-direct canonical, public-archive fallback (AFLTables for AFL, NRL equivalents) at 90 minutes post scheduled fixture end. Decision logic specified explicitly across six branches (SETTLED → finalised; CANCELLED → voided; OPEN/SUSPENDED >90min → fallback; fallback resolves → provisional; both resolve and disagree → provisional; neither resolves → provisional). 90-minute threshold per-sport-tunable as future flexibility. Past-90-min-no-result lands as `provisional` in Burst Review for operator confirmation, matching racing's provisional flow.

- **B.1.5** — sports bet record shape. **Simplified per operator-call mid-session.** Original draft said "Betfair-unavailable-at-log-time — bet cannot be logged through normal path; operator falls back to manual recording off-system." Operator pulled back: should still be able to input a bet if Betfair client isn't working. Specification updated with placeholder-record fallback path: bet record created with operator-typed line, stake, soft-book details intact; Betfair `market_id` and operational snapshot fields flagged `betfair_unresolved = true`; reconciliation step when Betfair returns resolves the `market_id` from stored fixture+market-type+line+selection metadata and backfills snapshot with explicit `snapshot_resolved_late = true` flag. Failure mode hasn't been observed in v2 history — path exists as insurance not as routine flow.

- **B.1.6** — SGM and specialist markets architectural provision. SGM out-of-scope v3-day-one but architecture must not preclude later addition. Three architectural provisions made now: market-type tab strip extensibility; bet record shape designed to extend cleanly to multi-leg recording (single field today, list-of-`market_id` later); line-ladder pattern doesn't apply to SGM but write-time-input philosophy does. SGM-specific concerns (3-leg-min, correlation EV modelling, specialist-market discovery) named as v3.1+ scope dependent on sports analytical needs settling.

- **B.1.7** — cadence note (open, tracked). Racing operational-cadence-check carry-in from operator's mid-session statement that v2's Betfair-direct racing cadence works well but may need review. v3 day-one runs sports operational reads on same polling pattern v2 uses for racing today; if §2.4 lands a Streaming connection, sports reads upgrade naturally. Cadence-appropriateness verification gated on Saturday API observation probe.

`dr029_scope.md` §2.2 gained a Session 38 close addendum summarising what was specified, naming v3.1+ candidates with their dependencies, and forward-routing §2.4 / §2.5 / §2.7.

## Mid-session pivots (operator-driven)

Three substantive shape changes during the session, each driven by operator pulling back from an over-engineered draft:

1. **Line input shape.** Initial draft assumed dropdown-list selection of Betfair line variants. Operator pivoted to text input with auto-rendering ladder. Reasoning: dropdowns degrade fast with 9-15+ available lines; text input is faster for the operator-knows-line case (the common case); ladder is discoverable for the operator-doesn't-know case.

2. **Five-above/five-below ladder.** Operator added this shape during the line-input discussion: not just the typed line, but the typed line ± 5 lines as a ladder. Architectural value: handicap and total markets have adjacent-line variants; showing the ladder reframes "yes/no on this exact line" to "which adjacent line is the better Betfair value." Foundation for future auto-line-matching (which will walk the ladder against soft-book line). Liquidity inline per row was operator-requested addition — operator wants to confirm Betfair-side liquidity is sufficient for stake to be matched, not just see the price.

3. **Action icons per row.** Operator surfaced the v2 pattern: lightning bolt for HedgeModal, pencil/log for LogBet. Specification adopted v2's existing pattern rather than introducing new UX vocabulary. Reuses operator's trained interaction pattern; lower-friction path to v3 day-one.

Plus the two simplifications during operator review:

4. **Favourite inference.** Operator simplified the 5% tolerance rule to plain shorter-priced-side rule. Cleaner specification, fewer edge cases to formalise.

5. **Betfair-unavailable-at-log-time.** Operator pulled back from the "block bet entry" architectural-purity stance to the placeholder-record-with-reconciliation operationally-smoother stance.

## Sample mockup

Mid-session, operator asked for visual sample before confirming the shape. Inline SVG mockup rendered showing three states: (1) empty input, (2) handicap with line typed (Carlton -6.5 example, 11-line ladder, both sides + liquidity), (3) total with line typed (165.5 example, 11-line ladder, over/under + liquidity). Operator ratified the shape after review with one addition (HedgeModal + LogBet action icons per row). Mockup shape ratified as the §2.2 UX-spec reference visual.

## Session shape

~2 hours wall-clock. Tool calls: 1 Adelaide-time anchor; 4 tool_search calls (Desktop Commander + projects-filesystem); 5 file reads (architecture.md grep + tail; dr029_scope.md head 160; agent_review/inputs/data_layer_current.md; ls of root); 1 read_me visualizer call; 1 show_widget call (the three-state mockup); 4 file edits (architecture.md ×3, dr029_scope.md ×2, work_in_progress.md ×3); 2 new file writes (this SESSION_38.md, Session 39 opening prompt).

**No discipline-rot incidents this session.** Operational/analytical line discipline held throughout — §2.2 is operational-only by definition; the operator's mid-session reaffirmation that v2's Betfair-direct racing path works well was named explicitly as racing-line, separate from soft-book operational. Plain-language framing held in mockup discussion and routing pivots; operator surfaced explicit response-style preference at close ("short responses with operational/gambling language; baby step by baby step") which is now folded into operator-instructions as a Session 38 reinforcement.

## Standing-instruction observances

- **Plain-language framing (Session 31 standing):** held throughout. Operationally-grounded language — "what happens when Tim opens v3 and clicks the sports tab on a Saturday afternoon to find an AFL market to bet" rather than "what `betfair_client` exposes via what method signatures."
- **Operational/analytical line discipline (Session 32 standing):** held. Operator's mid-session "v2's operational data works really well" was caught as racing-Betfair-direct specifically, not soft-book operational, before drafting proceeded. The §2.2 specification leaves §2.5 (soft-book) untouched as separately-scoped.
- **REPL discipline (Session 30 standing):** no multi-line REPL needed.
- **DR-027/DR-028 named in orientation:** done, with explicit framing of why they don't extend to the operational layer.
- **Pre-flight directory listing before substantive work:** done.
- **Filesystem discipline:** all rebuild-folder operations via projects-filesystem `edit_file`/`read_text_file` and Desktop Commander `start_process`; bash sandbox not used.
- **New standing instruction surfaced and folded:** Session 38 reinforces the operator's response-style preference (short, baby-step, plain operational language). Folded into operator-instructions in WIP.

## Thirteenth consecutive non-early-close session

Sessions 26-38 form an unbroken non-early-close run. Session 38 specifically delivered: §2.2 sports operational layer specified into architecture.md (122 lines, B.0 framing + B.1.1–B.1.7); §2.2 close addendum in dr029_scope.md; UX shape including line-ladder pattern, favourite inference, action icons emulating v2, fallback paths; SGM architectural provision; v3.1+ candidates named with dependencies. Session 39 routes to drafting the Saturday API probe brief.
