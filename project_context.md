# Project context

This is the orientation primer for any fresh session of the bethub-rebuild project. Operator-authored, version-controlled, slow-changing. Read at session open alongside `current_state.md` and `standing_instructions.md`.

---

## 1. What this project is

bethub-rebuild is the v3 architectural rebuild of BetHub v2. v2 is a Flask/SQLite/React betting management platform — built March-April 2026, mature operational state, running daily. The platform's design target is managing ~30+ Australian bookmaker accounts across multiple personas; today's working scale is more modest (around 10-15 bookmakers actively in rotation), with the larger account footprint as an aspirational ramp-up. v3 is a clean rebuild from the ground up, governed by numbered Decision Records (DR-001 through DR-029+), not a refactor or extension of v2.

Why a rebuild rather than an extension: v2 was built fast under operational pressure and accumulated structural debt that became expensive to design around — particularly the bet schema, the persona/account/book vocabulary, and the absence of a clean operational/analytical separation. v3 is being built from the lessons learned in v2. The architectural goals: a coherent design picture (two-database split per DR-027/028, derived state on read per DR-019, operating-mode and analytical-mode separation per DR-024) built against locked decisions rather than retrofitted; further improved operating and execution efficiency for day-to-day betting work; and a strong basis for analytical capability layered on top later.

v2 is still running. Per operator's explicit direction, v2 receives no modifications during the rebuild — bug fixes only if operationally critical, no feature work. v3 starts fresh from day 0 with no transaction backfill from v2 (per Session 13 revision 4 / Session 14 promotion). The two systems coexist until v3 is operationally ready, at which point cutover happens cleanly.

The active gating arc is DR-029 (the data-layer fit-for-purpose review before v3 build begins). v3 build does not start until DR-029 closes. DR-029 itself is a multi-session arc working through ten in-scope items (race-data fit-for-purpose verification, sports operational layer specification, Betfair Streaming spec, soft-book interface contract, settlement model, API contract versioning, bet-schema reframing, write-side coherence, external analytics environmental scan).

---

## 2. Who the operator is

Tim is the operator and product owner. Based in Adelaide, South Australia (ACST/ACDT timezone). Background is in business and governance analysis; not a software engineer or data architect. Working toward full-time professional sports and racing trading as the long-term goal — bethub-rebuild is being built in service of that goal.

Tim has been running promotional and value betting operations across Australian bookmaker accounts for nearly a decade, previously managed via Excel spreadsheets before BetHub v2 was built. That decade of operational experience has been almost entirely sign-up-bonus and deposit-bonus based — extracting value from new-account promos. Engaging with EV-driven betting (modelling true probabilities, finding lines where the market is wrong, treating bets as probabilistic positions) is a relatively new direction, taken up alongside v2's build. Tim has working confidence on betting fundamentals, odds, and promo mechanics; the EV side is an active area of learning, not yet ground-truth-level expertise.

Account hygiene is similar — Tim knows the obvious mechanics (don't be too profitable too fast, vary bet shapes, mix promos with non-promos, watch for limiting signals), but the subtler patterns are still being discovered through ongoing operational work. The browsing-activity and behavioural-fingerprint side is genuinely new territory — this is the first time Tim has used per-account router/SIM isolation and AdsPower fingerprint profiles, and how much isolation is actually required to keep accounts clean is an open question the operational work will answer. The v3 tools being built will materially improve that discovery process — current visibility into hygiene patterns is partial and largely intuition-driven.

The mathematical and probability side is also an active area of learning. Tim has studied Bayes' theorem, the central limit theorem, binomial distributions, and probability density functions, but is still early in that journey. That foundation will need to deepen before v3's analytical layer is built out. Claude will be leaned on for support there. The current rebuild work is deliberately sequenced with the analytical layer deferred — DR-029 settles the data layer, then operational v3 builds, and the analytical capability layers on top later when both the data and Tim's mathematical foundation are ready.

Software questions are Claude's; betting and operational questions are Tim's. This division is encoded as a standing instruction (see standing_instructions.md Category 5). Tim is the strategic decision-maker on the project, not the technical decision-maker. Architectural direction, code, schema design, and tooling choices are Claude's calls (proposed for confirmation, not punted back). Routing decisions, scope decisions, what to chase, which strategy to prioritise — those are Tim's calls, framed in terms of operational impact and strategy consequences.

Working environment: Adelaide-based Mac, Claude.ai Max plan, sessions split between Claude Chat (planning, governance, decisions, prompts, briefs) and Claude Code (file edits, code, tests, VPS work). Voice input is sometimes used for mobile sessions (DJI Mic Mini + Samsung S24). Sessions are structured with explicit open/close protocol per `governance.md` and `standing_instructions.md`.

---

## 3. The four racing strategies

Tim's racing profit work is organised around four strategies, each with its own EV profile, account-health profile, and operational shape. They are referenced throughout the rebuild docs by number — Strategy 1 through Strategy 4. The split matters because the data v3 needs differs per strategy, and the burst-review workflow design downstream of DR-029 is calibrated to which strategies are running.

**Operational reality today: Tim's operation is heavily dependent on Strategy 1 — roughly 95% of current profit comes from Safety Net cycles.** Strategy 2 contributes the remaining ~5%. Strategies 3 and 4 produce no profit today — both are aspirational growth directions, not income lines. v3's design has to keep Strategy 1 working cleanly above all else; Strategy 2 second; Strategies 3 and 4 are scoped but not gating. Anything that risks Strategy 1's operability (account hygiene compromise, promo-detection by books, settlement friction) is a higher-priority concern than anything that improves Strategies 2-4.

### Strategy 1 — Safety Net

Promo-driven insurance bets. The bookmaker offers a refund (cash or free bet) if the chosen runner finishes second, third, or fourth depending on the promo. Tim places the bet at advertised odds. Three possible outcomes per cycle:

1. **Runner wins.** Bet pays out at advertised odds — this is the profit outcome. Tim generally targets odds in the 2:1 to 8:1 range; EV tends to evaporate quickly above that because the higher-priced runners win infrequently enough that the refund layer doesn't compensate. Discovering the optimal odds band for insurance cycles is itself an analytical project for later — what odds range produces the strongest real EV across enough volume to be statistically meaningful.
2. **Runner finishes outside the insurance placings.** Pure loss — the original stake is gone, no refund triggers.
3. **Runner doesn't win but finishes inside the insurance placings (typically 2nd, 3rd, or 4th depending on promo).** The refund triggers — usually as a free bet, not cash. The free bet then runs through its own cycle and typically converts to roughly 70% of face value because free bets pay winnings only, not stake. So this outcome is *loss mitigation*, not break-even — Tim still loses on the cycle, just by less than outcome 2.

The strategy is +EV across volume because outcome 1's full-odds payout, even though rare, more than compensates for outcomes 2 and 3 across enough cycles. The refund layer doesn't make individual cycles profitable — it tightens the loss distribution so the rare wins clear the running deficit and produce positive EV. Bread-and-butter strategy, high promo dependency, high account risk because the books recognise the pattern quickly. The original bet plus the triggered free bet (if any) plus the free bet's outcome are analysed as a single cycle, never in isolation.

### Strategy 2 — Price Booster

Top Fluc, Best of Best, Best Tote, bonus-winnings-on-win, and similar price-uplift / bonus promos on drifters. Two sub-shapes: (a) price-uplift — Tim places the bet at advertised odds, the bookmaker pays out at the higher of advertised / closing fluc / tote, Tim takes the price-uplift edge; (b) bonus-winnings — Tim places the bet at advertised odds, on a win the bookmaker pays the win plus a free bet matching the winnings (e.g. 100% bonus winnings to $50), the free bet then runs through Strategy 1-style cycle analysis. Best account-health profile of the four because the bet shape looks like ordinary punting; the EV comes from the price/bonus layer, not the bet itself. This is the strategy where soft-book operational live pricing is structurally needed (per `architecture_current.md` §5.4 and DR-029 §2.5).

### Strategy 3 — Correlated Friction

Same-game multi (SGM) bonus-back promos in AFL, NRL, and other team sports. Tim builds correlated multi-leg bets where the legs reinforce each other (e.g. team to win + team's star player to score + total points over) — bookmakers tend to underprice the correlation, which produces positive EV that the bonus-back layer compounds. Needs a correlation model, which depends on team-sport historical data (fitzRoy R package for AFL, equivalents for NRL, future NBA/NFL). Currently scoped but not yet built out — the analytical foundation is being assembled.

### Strategy 4 — Synthetic Each-Way

Pure value betting on place markets and synthetic each-way constructions (using Betfair PLACE markets or layered exchange/book combinations). Thin margins, no promo dependency, god-tier for account health because the bet shape is statistically indistinguishable from sharp punting. The most analytically demanding of the four — needs accurate place-market probability modelling, which is downstream of the corrected Harville model work (currently calibrated to γ=0.77, δ=0.62, ε=0.48 with a 5% safety margin per the racing EV model project). **Tim does not yet have a working understanding of how Strategy 4 actually executes — the mechanics of synthetic each-way construction, the value-identification heuristics, and the staking discipline are all areas to learn later, likely alongside the deeper probability study mentioned in section 2.** Not a priority during DR-029 or initial v3 build; revisited when the analytical layer is being designed.

### Standing analysis convention

Any bet whose outcome drives downstream behaviour (free bet trigger, bonus-back, refund, cashback) is analysed as a single cycle, never in isolation. The whole sequence — original bet, downstream event, follow-on bet, follow-on outcome — is one analytical unit. Strategies 1 and 3 are the most cycle-shaped of the four; Strategy 2's price-uplift sub-shape is single-leg, but its bonus-winnings sub-shape is cycle-shaped; Strategy 4 is pure single-leg value. Encoded as a standing instruction (see standing_instructions.md Category 4).

---

## 4. Key vocabulary

The rebuild docs use a small set of terms with specific meanings. Not all of them are everyday English; the discipline matters because v2's structural debt traces partly to vocabulary drift early in its build. The terms below are the ones most-used across `architecture.md`, `decisions.md`, and the DR-029 artefacts.

### Account, book, account-at-book

Per DR-022 (the vocabulary decision):

- **Book** — a bookmaker as an organisation. Sportsbet, Ladbrokes, PointsBet, etc. There are roughly 20-30 books in the Australian market that v3 cares about.
- **Account** — an individual betting identity owned by a person. Tim has multiple accounts; a household member may have additional accounts. Each account is a real-world human-recognised identity used to register at books.
- **Account-at-book** — the specific relationship between one account and one book. If Tim's account "Tim Smith" is registered at Sportsbet, that's one account-at-book. If the same account is also registered at Ladbrokes, that's a second account-at-book. The account-at-book is the unit at which most operational state lives — balance, promo eligibility, limiting status, transaction history.

DR-022 supersedes earlier "persona" vocabulary; per DR-022 read prior DRs' "persona" as "account."

### Operational line vs analytical line

Per the Session 32 standing instruction:

- **Operational line** — `betfair_client` direct. Live pricing, bet entry, real-time burst-review work. ~1-second cadence near the jump in v2 today. Time-sensitive; failure here means missed bets.
- **Analytical line** — VPS scrape into `capture.db`. Periodic, not time-sensitive. Captures soft-book odds + Betfair API + Racing API for backward-looking analysis (model calibration, EV measurement, account-health analytics).

Both lines exist; both are needed; they serve different purposes and run at different cadences. Reading a cadence number from analytical-side measurement and reasoning about operational fitness is a recurring drift pattern flagged in standing_instructions.md Category 4.

### The three databases

bethub-rebuild's data architecture spans three databases:

1. **v2's bethub.db** at `/Users/tim/Desktop/Projects/bethub-v2/data/bethub.db`. Local SQLite (WAL mode). v2's operational store. Not modified during the rebuild. Will be retired at v3 cutover.
2. **capture.db** on the VPS at `/home/racing/racing-data-capture/data/capture.db`. Analytical store. Captures Betfair API, Racing API, and soft-book scraper output for backward-looking analysis. Read by v3 (and would have been read by v2, though v2's consumer paths went largely unused). Owned by the analytical-line per DR-027.
3. **v3's operational store** — TBD; specified during v3 build, gated behind DR-029 close. Will own operational state (accounts, account-at-book, bets, promos, balances, transactions, operations log). Per DR-027/028, no shared tables with capture.db; integration is by reference only (Betfair-side identifiers as join keys).

### Betfair as canonical source

Per architecture.md §D12 and the Session 42 architectural-extension flag:

- Betfair is the canonical source for anything Betfair owns — event identity, venue name, sport, commission rate, market structure.
- BetHub owns operational state — bet records, promo eligibility, balances, account-at-book status, settlement.
- Pending architectural extension (Session 42 flag): "Betfair as canonical source" extending to *all* bet records, including softbook bets logged manually. Every bet record carries Betfair-side identifiers (`betfair_market_id`, `betfair_selection_id`, Betfair venue/sport/event-name) as the canonical join key. Eliminates fuzzy-matching against the analytical layer. Load-bearing enough to belong in `architecture.md` and possibly a new DR — discussed in post-DR-029 documentation pass.

### Decision Records (DRs)

Numbered architectural agreements in `decisions.md`. DR-001 through DR-029+. Immutable once locked; new DRs are added, existing DRs are not edited (amendments are added as separate appended notes). When invoked in conversation, DRs are cited by number with a bracketed plain-language reminder per standing_instructions.md Category 1 — e.g. "DR-027 (the two-database architecture decision)", "DR-014 (the multi-book hot-path requirement)". The most architecturally load-bearing DRs are listed in `current_state.md` "active governing decision records."

---

## 5. Active arc — DR-029

DR-029 (the data-layer fit-for-purpose review before v3 build begins) is the gating decision arc. v3 build does not start until DR-029 closes. The arc has been running across multiple sessions and is currently mid-flight.

### What DR-029 is

A structured review of whether the existing data layer (capture.db on the VPS, the v2 bethub.db, the Racing API and Betfair API streams feeding both) is fit for v3's purpose, *before* committing to v3's build. The review surfaced from a multi-agent governance review across Sessions 20-26 — four assessor agents (software-developer / PM / skeptic / open-questions) plus a judge synthesis flagged data-layer concerns that needed empirical resolution rather than design-time guessing.

### Scope

Locked in `dr029/dr029_scope.md` (rebuild folder), 247 lines. Ten in-scope items, ten out-of-scope items, nine-step execution sequencing.

In-scope items:

1. §2.1 — race-side data fit-for-purpose verification (closed Session 34 with known-debt-named, surgical-fix arc through Sessions 35-37+ executing the resolution).
2. §2.2 — sports operational layer specified Betfair-direct, no analytical capture (closed Session 38).
3. §2.3 — periodic-only API pattern reframed on operational/analytical axis.
4. §2.4 — Betfair Streaming spec and cadence design (Fix 4 brief drafting waits on Saturday's API observation probe).
5. §2.5 — soft-book interface contract source-flexible.
6. §2.6 — settlement model (sports path re-specified per §2.2).
7. §2.7 — API contract versioning across three module contracts.
8. §2.8 — bet-schema reframing on operational/analytical axis.
9. §2.9 — write-side bet-entry coherence.
10. §2.10 — time-boxed external analytics environmental scan (substantially fed by the Saturday API observation probe).

Out-of-scope items: full analytics layer build (deferred per scope limits), account-isolation layer formalisation, Cloudflare-blocked soft books, vendor selection for soft-book operational source, sports analytical capture in capture.db (asymmetric architecture acknowledged), reachability/continuous-fitness scoping (dissolved per Session 27), NZ racing inclusion (backward-compatible-later), burst-review triage workflow design (downstream of DR-029).

### Where the arc is right now

§2.1 closed-with-known-debt-named at Session 34. Surgical-fix arc through §2.1's resolution:

- **Fix 1+2** — race-result write-back to `runners.finish_position` plus the `racing-metadata-backfill.service` rework. Executed Sessions 35-36 cleanly. Headline cross-tab `with_both` (finish_position AND betfair_selection_id present) stayed at 0→0 due to venue-normalisation drift between live-capture and Racing API paths — routed to Fix 5.
- **Fix 3** — BSP / sp_near / sp_far write-back. Executed Sessions 36-37 cleanly within dirty-tree rules. Change (b) is a clean win (sp_near/sp_far populating 100% INTENSIVE / 95% STANDARD post-restart vs 0% across 1.6M baseline rows). Change (c) BSP write-back path wired correctly per brief but empirically inert — Betfair's `priceProjection=SP_TRADED` does not surface `r.sp.actual_sp` on closed AU thoroughbred WIN markets. Routed to direct API observation probe.
- **Saturday API observation probe** — runs Saturday morning ACST 2026-05-02 (the day after this session). Direct empirical capture of Betfair `MarketBook` API behaviour across 4 races (2 thoroughbred + 1 harness + 1 greyhound) plus parallel Racing API capture, replacing inference with raw observation. Five questions: when does `r.sp.actual_sp` populate; cross-code response-shape parity; what fields the API exposes that the snapshot writer doesn't capture (substantial chunk of §2.10's deliverable); cadence of meaningful change at 1-second granularity (informs Fix 4 cadence design); race/runner identity alignment between Betfair and Racing API. Brief locked at `dr029/2_1_race_data/api_probe_brief.md`.
- **Fix 4** — cadence design. Brief drafting waits on probe results.
- **Fix 5** — venue harmonisation + retroactive race-key merge. Brief drafting independent of probe; can land any session.

### What gates v3 build

DR-029 close. The remaining DR-029 items (§2.3, §2.5, §2.6 sports path, §2.7, §2.8, §2.9, §2.10) plus the §2.1 surgical-fix arc completion (Fixes 4 and 5) plus the close-out governance paragraph (covering periodic data-fitness re-verification and the three pieces of named debt — no test coverage, no migration framework, monolithic orchestrator file) all need to land before v3 build starts. No commitment on session count to close — the arc takes as long as the work needs.

---

## 6. Tooling and environment

The bethub-rebuild project runs across two complementary Claude surfaces plus a local environment, with a structured division of labour between them. Understanding the split matters because tool routing decisions show up in every session.

### Claude Chat (this surface)

Used for: planning, governance, decisions, prompt drafting, brief drafting, multi-agent review work, scope documents, session records, architectural discussion. Anything that's primarily about thinking, structuring, deciding, or producing reference artefacts.

Claude Chat does not edit code in the v2 or v3 codebase directly during normal operation. Code edits happen in Claude Code sessions (see below). Chat does write and edit governance documents in the rebuild folder via Desktop Commander, including briefs that commission Claude Code work.

### Claude Code

Used for: file edits, code authoring, code review, tests, VPS work (SSH operations, log inspection, service restarts), surgical fixes against locked briefs, empirical database queries, anything involving the live v2 or VPS systems.

Tim opens a Claude Code session out-of-session (separately from the operator-Claude Chat session) and points it at a locked brief in the rebuild folder. Code executes the brief end-to-end with hard-limits explicit (single bounded session, no edits outside named anchors, dirty-tree handling explicit per Sessions 35/36/37 pattern). Code produces a report in the rebuild folder; the next Chat session reads the report and triages.

The split is deliberate: Chat does the thinking work where context retention matters and where the operator's strategic input drives direction; Code does the execution work where focused single-purpose runs against locked specifications are the right shape. Mixing them produces sessions that drift between modes and lose context budget.

### Desktop Commander as default filesystem and process tool

This Claude Chat session runs on Tim's local Mac via Desktop Commander. There is no bash sandbox available, no separate Linux container, no other shell environment. Every filesystem operation, every Python invocation, every `git` command routes through `Desktop Commander:start_process` (or its file-targeted siblings: `read_file`, `write_file`, `edit_block`, `list_directory`).

The bash_tool that may appear in Claude's tool list is non-functional in this environment — calls fail with "no such file" because it cannot reach the Mac filesystem.

`projects-filesystem` MCP server is an acceptable alternative for rebuild folder file operations only — specifically `projects-filesystem:write_file` for fresh artefacts and `projects-filesystem:edit_file` for edits. Detailed filesystem and tooling rules live in `standing_instructions.md` Category 3.

### Project knowledge base + skills approach (Phase 2 forward)

Per Session 40-42's session operations proposal, the rebuild project uses a Claude Project (`bethub-rebuild`) holding the canonical reference docs uploaded once and available to every chat in the Project without per-session re-reading. Three skills (`bethub-session-open`, `bethub-session-close`, `bethub-brief-drafting`) encode the procedural patterns that previously lived in opening prompts and operator instructions.

The Project knowledge base contains the slow-changing canonical truth: `vision.md`, `architecture.md`, `decisions.md`, `governance.md`, `v3_data_requirements.md`, `dr029/dr029_scope.md`, `standing_instructions.md`, `project_context.md` (this file).

The journal layer stays in the rebuild folder on local disk: `current_state.md` (live working state, ~10-20 KB target), `sessions/SESSION_N.md` (immutable session records), `dr029/` (active arc artefacts — briefs, reports, scope addenda).

The skills fire automatically from natural-language requests; no `/command` syntax. Each skill loads only when relevant — no per-session prelude burn.

### Live database queries

For empirical questions about v2 or capture.db state, queries run via `Desktop Commander:start_process` with Python against the live database file directly — never copy the file. v2 lives at `/Users/tim/Desktop/Projects/bethub-v2/data/bethub.db`. capture.db lives on the VPS at `/home/racing/racing-data-capture/data/capture.db` (via SSH tunnel `root@187.77.183.9`).

### Operator workflow

Tim works between sessions reviewing artefacts (briefs that Claude has drafted, reports that Claude Code has produced). Operator review of artefacts is between-session work, not a session blocker — see standing_instructions.md Category 4. At every session close on a multi-session arc, Claude generates a complete opening prompt for the follow-up session without being asked. Tim pastes it into the next session to open.

Future state: once `current_state.md` proves itself reliable across two or three sessions running alongside opening prompts, Tim may switch to typing only "Open session N" / "Close session N" with Claude reading `current_state.md` plus `standing_instructions.md` plus flagged DRs to orient. No commitment to switch — switch only on evidence.

### Multi-agent review for material strategic decisions

For material strategic and architectural decisions — the kind where getting it wrong has compounding downstream cost — the project uses a multi-agent review pattern that brings in models outside the Anthropic family (Grok, Gemini, ChatGPT, others as appropriate) alongside fresh Claude instances. The pattern was established across Sessions 20-26 for the multi-agent review that triggered DR-029, and the canonical reference is in `governance.md` (multi-agent review pattern).

Why other models: different model families have different failure modes. Claude tends to validate framing too readily; Grok pushes harder on coherence and is willing to call something incoherent; Gemini is structured and PM-shaped; ChatGPT was excluded from the Sessions 20-26 review for its gambling-content safety posture but may suit other domains. Stacking models against the failure mode of the specific decision (skeptic seat, validation seat, structuring seat, synthesis seat) produces signal that no single model can.

This is rare by design — multi-agent review is expensive in operator effort and Claude session time. Reserved for material decisions where the cost of being wrong significantly exceeds the cost of the review. Not for routine architectural choices, which are Claude's calls (proposed for confirmation per standing_instructions.md Category 5).
