# Judge synthesis prompt — multi-agent governance review

*Drafted Session 23 (2026-04-29 ACST). This is the judge synthesis prompt template that runs after the four agent outputs are collected. The judge sees the four original documents plus the four agent outputs (Question B from Session 21). The judge synthesises rather than chooses (Question B lock; `governance.md` multi-agent review pattern). This prompt is structurally different from the four agent prompts — it has different inputs (documents plus assessments), a different brief (synthesis not assessment), and a different output structure (per-question synthesis spanning the four agents, not single-agent assessment per question).*

*Model: fresh Claude Opus, separate session, no project context. The judge's output is the operator-facing artifact of the multi-agent review.*

*The prompt body begins below the horizontal rule. Final assembly inserts each of the four documents in place of the document inline-paste markers, and each of the four agent outputs in place of the assessment inline-paste markers, before delivery to the agent.*

---

You are reading the outputs of a multi-agent governance review and synthesising across them. Before you read further, four pieces of context that calibrate what is wanted from your reading:

The operator commissioning this review is not a data architect and is not deeply versed in distributed-data or database-architecture disciplines. The review is wanted as actual expertise rather than validation. Concretely: do not soften your synthesis to be agreeable, and do not soften the assessors when they were sharp. If the assessors agreed that something is wrong on the technical merits, say so plainly. If they disagreed and one read is clearly stronger than another, say so plainly. The operator's preference is for honest synthesis over agreeable smoothing. Treat the operator as someone who can absorb sharp expert critique and act on it.

You are the synthesis seat in a multi-agent governance review. Four agents read the same four-document suite independently. Three of them (a software developer, a project manager, a skeptic) stress-tested the proposal against a named question list. A fourth surfaced what the named list did not reach — load-bearing assumptions going undefended, questions not being asked, backgrounded items that should have been foregrounded, framing strain. None of them saw the others' work. Your job is to synthesise across all four outputs.

The proposal under review is a rebuild of an existing matched/promo betting tool, currently called BetHub v2, which has been running for months. The rebuild (v3) inherits the operational shape v2 produced and rebuilds the software around that shape with v2's accumulated failure modes designed out. The operator runs the operation solo. The four documents below describe what is being decided, the v3 data requirements, the architecture as currently designed, and the data layer (an existing UK VPS racing-data capture system called `capture.db`) that v3 will read from. The four agent outputs follow the documents.

The work has progressed across many design sessions. One concern named by the operator, which the assessors were asked to take seriously: long-running session-by-session evolution can produce documents that look coherent on first read but reveal patchwork drift on careful reading. Where the assessors flag this directly, your synthesis weighs it.

## Your role for this synthesis

**Synthesise rather than choose.** The job is not to pick the winning agent or to decide which assessment is right. The job is to produce, for the operator, a navigable synthesis of the four agents' outputs that makes the multi-agent picture visible — where they agree, where they disagree and on what grounds, and what recommendations emerge from the synthesis itself. The operator can read the four assessments in full if they want to; what they need from you is the synthesis they cannot produce by reading the four outputs end-to-end.

The framing matters. A judge looking at four substantive disagreements naturally reaches for a verdict; the brief here actively pulls the other way. Your authority is in the synthesis layer, not the resolution layer. Where the four agents disagree, the most useful output is "they disagree because they are weighing X and Y differently, the strongest version of each side runs as follows, and here is what the operator now needs to decide" — not "the software developer is right, the skeptic is wrong." Reserve that kind of resolution for the rare cases where one agent is straightforwardly correct on technical grounds the others missed; default to surfacing the disagreement structure.

Three rules that hold across the synthesis:

**Read the four agent outputs as primary inputs, not as commentary on the documents.** They are first-class material here. Your synthesis must engage with what each agent actually said, cite by agent ("the software developer argues...", "the skeptic notes...", "the open-questions agent surfaces..."), and represent each fairly. Misrepresentation in the synthesis layer is more expensive than in any single assessment because it propagates to whatever the operator does next.

**Weight by argument strength, not by author seat.** The skeptic seat carries no automatic weight on assumptions; the software developer seat carries no automatic weight on architecture. Where the skeptic's coherence finding rests on weaker grounds than the project manager's coherence finding, say so. Where the open-questions agent surfaces a load-bearing assumption that the three assessors all missed, weight it accordingly. The seat each agent occupies shaped what they were looking for; it does not shape how much their findings count once produced.

**Synthesis-derived recommendations are findings the four agents collectively produced that no single agent stated alone.** These are the highest-leverage output of this review. They are most often a recommendation that emerges from triangulating across two or more agents, or from combining a substantive finding with a coherence-of-framing finding. Surface them clearly and label them as synthesis-derived rather than as any single agent's claim.

## The four documents

### Document 1 — Decision under review

# Decision under review — multi-agent governance review

*Drafted collaboratively across Sessions 15–17 (2026-04-28). Operator-Claude session, "Claude asks, operator tells, Claude records." Six-section template per `governance.md`.*

---

## 1. What is being decided

I'm about to rebuild the tool I run my betting operation on. Before I start building it, I want to make sure the v3 design supports the most efficient possible bet execution while also being accurate and logical in how it captures betting activity, balances, and P&L changes. The tool needs to deliver decision-making information efficiently and make bet decisions and execution frictionless. It also needs to keep accurate balances and produce valuable insights into betting activity, supported by a database that can drive good bet decisions over time. This is a forward-looking project: I want the data layer to capture what will be needed for analytics I haven't yet conceived of, because the questions will surface as the operation runs. The operation runs today on v2, which has a very high administrative and correctional cost — bug-fixes and reconciliation work that costs me real money in inefficiency and mistakes. v3 needs to fix that, and that priority sits behind every design choice in front of you.

---

## 2. Why this is being reviewed

These four questions are facets of one concern, not four independent ones. The concern is whether v3's accounting layer and the data layer that supports it are designed well enough — simply enough, accurately enough, with enough forward-looking data coverage — to support a sophisticated betting operation as both the software and my own skill develop, without repeating the v2 failure modes that have been costing me real money.

The four questions cut into that concern from different angles:

*Bet schema simplification* — v2's bet-record schema became a data mess. Any change, update, or refinement could take hours or days and still produce bugs. The instinct in v3 is to define the bet schema as simply and cleanly as possible from the outset. I want assessors to stress-test whether the proposed simplification is genuinely the right move, or whether I'm over-correcting against v2.

*Data-layer-first sequencing* — the clock is always ticking. I don't want to build v3 only to discover later that I missed an easy-to-capture data field that would have unlocked valuable analysis. I want to be forward-looking and capture fields the literature cites as predictively valuable even if I don't yet know what I'd do with them — because as my skill develops, new angles will surface, and the data needs to already be there. The review needs to confirm the data layer is set up to support analytical breadth: my own betting performance, market movement, how the market interprets performance signals into price, liquidity dynamics, the approach to jump time, and angles I haven't thought of yet.

*Data review scope rightness* — related. I want confidence the scoping is sound and will support a sophisticated operation as both the software and my skill in embedding and probability disciplines develop.

*Periodic-only API pattern* — I want to know whether this is the best approach, and whether it's the best approach with the least overhead and the lowest risk of overcomplication. I'm not deeply versed in these disciplines, and I want expert disinterested review to make sure the model is sound.

Layer separation context: v3 has a clear separation between the operational/execution layers (where the operator does work) and the data/database layer (which supports them, and which the future analytics layer will draw from). There's also a behavioural/account-isolation layer (the fingerprints, IPs, and account-isolation discipline that keeps accounts alive). These layers interlink — bet decisions depend on data captured at log time; analytics depend on data captured continuously; account longevity depends on the behavioural layer working. The four review questions sit at the seam between the accounting layer and the data layer, but the assessors should read them with the interlinking in mind, not in isolation.

Reversal cost is a major consideration. v2 demonstrated that reversing decisions, or even adding and refining things, can become ridiculously unwieldy — taking a long time and ultimately not delivering the result. Once v3 is logging bets in a particular schema shape against a particular API contract, changing the shape or the contract becomes expensive. Getting these decisions right before build is much cheaper than reversing them after.

Structural protection is also a major consideration, but the framing matters. The primary protection is making the seamless, efficient flow the path of least resistance, so that shortcuts aren't needed in the first place. This is why minimising manual operator input has been such a focus across the design: a manual input has to be absolutely necessary, or of very high value, to earn its place in v3. Removing all manual input isn't possible, though, and wherever manual input remains, the temptation to shortcut will too — so the secondary protection is that the architecture makes those shortcuts structurally hard where it can. There's a tradeoff — automation costs upfront engineering — but shortcuts are usually taken when things are cumbersome, so the structural fix is primarily removing the cumbersomeness, with restriction as a backstop for the residual cases. The four questions in this review sit at the seam between the accounting layer and the data layer, where getting the design right means the seamless flow holds and shortcuts don't surface as a temptation; getting it wrong means v3's operating flow becomes friction-laden, and friction is what produced v2-shaped failure modes in the first place.

---

## 3. Current direction

*Two-database split (DR-027 / DR-028).* v3's accounting-layer database owns bet-data — every entity and event involved in the bet lifecycle, settlement, hedging, promo cycles, free-bet ledger, cash flow, and the day-one AccountCare implementation. A separate database, `capture.db`, runs on a UK VPS and owns market-data — Australian thoroughbred / harness / greyhound races today, with sports markets (AFL, NRL, others) to be added per the data review. No fact lives in both databases; v3 reads market-side context on demand through a single integration module. Cross-database joins happen at read time, not via stored copies.

*Data-layer-first sequencing (DR-029).* The v3 build does not start until the data layer (`capture.db` plus its data API) has been reviewed against v3's scoped requirements and any required extensions are complete and stable. The sequence is: produce a written statement of v3's data requirements (done — `v3_data_requirements.md`); run this multi-agent review; scope the data review; pre-execution governance check; data review execution including the external analytics scan; final data layer lock; v3 build begins.

*Data review scope.* In scope: race-data fit-for-purpose verification against v3's scoped needs; addition of sports market data capture into `capture.db` (currently absent); periodic-only API pattern with analytical bracketing; settlement model; external analytics environmental scan time-boxed to two sessions covering racing and sports; API contract versioning and documentation. Out of scope: analytics layer formalisation; account-isolation/behavioural layer formalisation; Cloudflare-blocked book scraping. NZ thoroughbred/harness/greyhound coverage is re-asked during the review as a sub-question — included if Racing API supports it, excluded if not.

*Periodic-only API pattern with analytical bracketing.* The data API returns the most-recent stored snapshot from `capture.db` (typically 0–60s old in pre-jump windows) with its timestamp, plus scratch state. v3 stores this inline on the bet record and marks staleness flags above tunable thresholds. No on-demand fresh-now snapshot pattern is added to the API. The analytical justification: surrounding-interval snapshots (T-x and T-x+cadence) read from `capture.db` at analysis time bracket the bet's true market state across the bet timestamp, observing market movement *around* the bet rather than at a single point — structurally stronger than a single fresh snapshot. Cadence verification is a data-review item; if pre-jump cadence proves insufficient, resolution paths in priority order are: extend the pre-jump intensive window, tune standard-cadence interval, accept staleness with operator-visible indicator. On-demand is a last resort, not introduced unless these paths fail.

*Bet schema — open question for this review.* The current schema stores inline market-context snapshot per DR-026 (best back/lay price + size, total matched, snapshot timestamp, staleness flags) and field-size captures per Slice 6 (`field_size_at_bet_placement`, `field_size_at_settlement`) directly on the bet record. The simplification under consideration is to drop these in favour of resolving race-side context entirely from `capture.db` at read time, with the bet record carrying only identifiers (Betfair `market_id`, runner `selection_id`, placement timestamp) and v3-context fields (stake, odds, promo linkage, hedge state). For this review the question is treated as open — both shapes are described so assessors can weigh them on their structural merits.

*Settlement model.* VPS race result is canonical for "what happened in the race" — auto-settlement reads finish position from `capture.db` via the integration module. Operator-recorded book settlement (cash returned to the at-book balance) is canonical for "what the operator's cash outcome was." Where the two diverge — voids per book rules, dead-heat handling differences, stewards' inquiry resolutions — divergences are surfaced as reconciliation signals in burst review or session reconciliation reports, not algorithmically resolved. No confidence hierarchy is built; the architecture treats divergence as information, not as a problem to rank.

*Reconciliation surfaces.* Six reconciliation surfaces are produced as natural outputs of derived state vs. operator-observed reality: cash reconciliation (computed at-book balance vs. operator-entered actual balance), free-bet reconciliation (computed FB inventory vs. operator-counted FB credits at book), settlement reconciliation (auto-settled bets vs. operator's observation of book payout), race-result reconciliation (capture.db result vs. book settlement), hedge reconciliation (hedge state per the derivation algorithm vs. operator's mental model), and cash-holding-with-custodian reconciliation (computed Location 2 vs. custodian's actual bank balance dedicated to the operation). An operation-net-flow informational view is also produced (cumulative net impact on the operator's bank since day 0, derived from the four bank-touching event types) but is not a reconciliation surface — Tim's bank includes personal activity outside the operation, so no apples-to-apples external check exists.

*Forward-looking architectural shape.* v3 is two databases day-one. AccountCare is embedded in v3's bet-data database with a simple implementation (warnings, tiers, phase tracking, basic conditioning state). The long-term architectural shape is uncertain — whether AccountCare ever warrants its own database is one open thread, surfaced for the assessors as part of Section 6's ask. The reason for noting the question at all: if the long-term shape is multi-database, DR-028's cross-DB integration discipline needs to hold for more than one boundary, which raises the stakes on getting the discipline right under today's single-boundary load.

---

## 4. Concerns the operator wants the assessors to weigh

*Concern 1 — Administrative overhead and error-detection time.* v2's worst failure mode was administrative overhead: data errors (operator-introduced — wrong book, wrong account, wrong wager) and system bugs (producing wrong numbers from broken logic) were costly to correct. The fix-cost mattered, but what mattered more was *detection time* — errors and bugs hid for days or weeks before being noticed, by which point the downstream effects had compounded. v3 needs to reduce fix-cost (fixes should be quick and effective, not produce further bugs) and reduce detection time (errors should surface fast).

The v3 detection mechanism is a Claude-driven burst-review triage workflow, designed in as a day-one capability. The shape: Claude extracts everything flagged across the six reconciliation surfaces and other anomaly signals, investigates each, and presents the operator with a triaged list — superficial vs. deeper-in-the-tool. Operator-initiated (so it sits inside operator workflow), Claude-driven (so the extraction and investigation work is offloaded). This is structurally different from v2's flagged-items page, which was a passive surface the operator had to remember to visit and didn't get traction.

The bet-schema-simplification question bears most heavily on this concern: a simpler schema is easier for Claude to triage, easier to fix when wrong, and produces fewer downstream cascade effects per fix. The reconciliation-surfaces design (six surfaces as natural outputs of derived-state-on-read per DR-019) bears on this directly too.

*Concern 2 — Flexibility: market coverage and bet types.* v2 was too restrictive on what could be logged. Two specific examples. First, no custom Betfair orders — the operator was forced to take whatever back or lay price was available, with no way to set a custom price target. Second, line-extraction quality on sport markets was poor: for sports like NBA the tool would show handicap or over/under markets at lines (e.g. ±8.5) that were nowhere near the centre line the Betfair market was actually offering (e.g. ±3.5). The five-market spread either side of centre was the right design; the matching to the centre was broken.

The day-one v3 sport scope, deliberately bounded: NBA, NBL, International Cricket, AFL, NRL, Tennis majors, NHL, MLB, NFL, MMA, plus soccer majors (EPL, La Liga, Ligue 1, Serie A, MLS). The architecture must support adding sports/leagues later without restructuring — extending the incremental-scraper-addition principle (DR-018) into the sports-data-capture layer.

The line-matching problem is a source-limitation question (the captured data didn't expose the centre line cleanly, so the display logic had nothing better to show) rather than a pure implementation bug, but it's tractable — candidate approaches include using VPS-captured soft-book lines as the centre reference plus ±5 markets either side, with a custom-input fallback. The data review's scope item "addition of sports market data capture" needs to include line-extraction quality as a sub-concern, not just presence-of-capture.

*Concern 3 — Information availability for decision-making at execution time.* The operator currently spends manual time entering odds into the Racing EV model. The model exists, scrapers exist, but the integration between scraped data and the operator's at-execution-time view isn't surfacing what's needed without manual data entry. v3 must close that gap. At minimum, the most-relevant scraped soft-book information available today should be surfacing in the operator's bet-logging context without manual intervention. The shape of failure here is "v3 is built but I'm still doing manual data work to make the model usable" — exactly the administrative overhead Concern 1 flags, surfacing in a different layer of the system.

This bears on the data-layer-first-sequencing question (the data must be in shape *before* execution-layer build begins, otherwise execution layer is built against a broken integration), the data review scope (what gets captured, how is it surfaced to v3), and the periodic-only API pattern (the captured data must reach v3 via the API in a form the execution layer can consume directly, not via manual operator transcription).

*These three concerns are the operator's evaluation criteria for v3.* If v3 lands well on all three, it's working. If it leaves any of them exposed, it's not. Assessors should hold the four review questions up against these three concerns and weigh which combinations of design choice deliver against which concerns.

---

## 5. Alternatives considered

*v3 owning its own data, including race-side capture.* The alternative was a single-database v3 that absorbed race-data capture into the execution and operational tool itself. This was set aside because v2's data failed for exactly that shape of reason — data stored locally all over the place, in the same tool that was operating, with no clean separation. v3's direction is the opposite: a single source of data on the VPS, captured 24/7, that the execution and operational tool reads from. Analytics, when it is built, feeds off the same VPS data layer. The shape is one data layer, multiple consumers — not one tool that owns its data.

*Building v3 in parallel with the data review, or building v3 first and extending the data layer later.* Two alternatives were on the table: parallel (data review and v3 build progress together, integrate when both are ready) and build-first-then-extend (build v3 against current `capture.db`, treat data-layer gaps surfacing during build as extensions done as needed). Both were set aside. The data layer needs a proper review first — what `capture.db` is currently capturing (and what fields it's missing), and what data sources are available to us beyond what's currently being scraped. That review is as much exploratory as it is design-locking: we don't yet know everything that's available, and v3's shape should be informed by what we actually have. Building first or in parallel would mean designing v3 against assumptions about data availability — risking either v3 being built around fields that aren't actually accessible, or v3 being built too limited in scope when more data was available than we thought. Locking the data layer first is the path where v3 gets designed against a known and stable foundation.

*On-demand fresh-now snapshot at bet lodgment, or a hybrid combining on-demand and periodic.* A point-in-time snapshot fetched fresh at the moment a bet is logged would be a useful thing to have — it captures the market exactly as the operator is seeing it. The honest position from the operator side: it might be more useful than is currently thought, and that's part of what the assessors are being asked to weigh. It was set aside on a tradeoff: adding the on-demand path adds complexity to how the data works (a second code path on the VPS, a second integration with Betfair under bet-log latency, a second thing that can fail or drift), and the analytical value gained over what the periodic capture already provides looks marginal from the operator's vantage. The periodic data, with cadence tuned to be suitable for analysis, looks good enough. The hybrid was set aside for the same reason — it retains the on-demand complexity *plus* the periodic path, so the cost-side of the tradeoff doesn't reduce. The shape chosen is: rely on the periodic capture that already runs, accept the small staleness, avoid the data-risk and infrastructure overhead that on-demand would introduce.

*Keeping the bet record more data-rich.* This question travels alongside the periodic-only API question above: both are facets of the same underlying choice between simpler-and-leaner and more-data-rich-with-more-complexity. The current direction (in force, but treated as open for this review) keeps the bet record carrying inline race-context — DR-026's market snapshot at log time and the Slice 6 field-size captures at placement and settlement — under a cross-system-durability framing. The alternative under consideration drops these: the bet record carries only identifiers and bet-context fields, with race-side context resolved entirely from `capture.db` at read time. Both shapes depend on the VPS data layer being rigorous; the simpler shape leans on that rigour as the single source of race-context, while the more-data-rich shape adds a second copy on the bet row as cross-system insurance without removing the dependency on continuous capture. Operator framing: this is fundamentally about alignment with whichever shape the review recommends. If the review lands on the simpler shape, the bet record drops the inline race-context fields. If the review lands on the more-data-rich shape, the bet record retains them and the cross-system-durability framing carries through. The two questions fall together; the assessors' job is to weigh the simpler-vs-more-complex tradeoff, not to weigh schema and API independently.

---

## 6. What the operator wants the assessors to produce

*Primary framing.* Stress-test this and find the failure mode. Assume the proposal could fail; locate where, describe how. The reason this framing rather than "tell me what we might be missing" or "tell me whether this is sound": the operator wants pointed interrogation of the named decisions, not a broad scan that risks surfacing concerns already discussed in process but not visible to assessors, and not validation that risks confirming-by-default. The four review questions in `v3_data_requirements.md` (B.7) are the spine of the stress-test. For each, the ask is: where does this break, under what conditions, and what does the failure look like.

*Secondary ask alongside the primary framing.* The operator wants assessors to also stress-test the *framing itself*. Reading the document suite as a fresh outside reader, does what's in front of you actually hang together as a coherent design — or does long-running session-by-session evolution show through as patchwork that drifts when you read it carefully? Assessors are explicitly invited to flag "this doesn't even cohere" if that is the honest read, rather than feeling obligated to engage with the proposal on its own stated terms. This ask is secondary to the failure-mode interrogation, not a replacement for it: both questions are legitimate and the operator wants both answered.

*Pushback ask — AccountCare-DB future shape.* Section 3's closing bullet flags that AccountCare is in v3's bet-data database day-one, with a simple implementation, and that whether it ever warrants its own database is one open thread. The operator wants this treated as genuinely open by assessors. The operator's own framing: "AccountCare-as-its-own-DB is a maybe that can only be answered by using v3" — the working hypothesis is that the answer surfaces from operating, not from up-front design. Assessors are invited to argue *against* this premise. Specifically: if AccountCare's eventual own-database trajectory is more probable than the operator currently treats it as, DR-028's cross-DB integration discipline has to scale to more than one boundary, which raises the stakes on getting that discipline right under today's single-boundary load. If assessors think the trajectory is even moderately probable, the operator wants to know — so the discipline can be designed with that future in mind rather than retrofitted.

*Pairing ask — B.7 #1 (bet schema simplification) and B.7 #5 (periodic-only API).* Per Section 5 entry 4, these two questions are two facets of the same underlying simpler-vs-more-complex choice and the operator asks assessors to weigh them together, not as two independent questions. The current direction on each is described separately in Section 3 and `v3_data_requirements.md` so the technical detail is preserved, but the assessment ask is unified: which shape — leaner-bet-record-with-periodic-only-API, or more-data-rich-bet-record-with-richer-API — is the right structural commitment, given that both depend on VPS rigour and differ primarily in where that rigour is leaned on. Assessing them independently risks splitting a coherent design choice into two half-answers that don't compose.

*Operator-background calibration framing.* The operator is not a data architect and is not deeply versed in these disciplines. The review is wanted as actual expertise rather than validation. Concretely: assessors should not soften their assessments to be agreeable. If a decision is wrong on the technical merits, the operator wants to be told plainly. If a framing is confused, the operator wants that flagged plainly. The operator's preference is for honest pushback over agreeable validation, even where the pushback is uncomfortable. Assessors writing for this review should treat the operator as someone who can absorb sharp expert critique and act on it, not someone who needs the critique softened.


### Document 2 — v3 data requirements

# v3 data requirements

*Promoted from `SESSION_12_SCRATCH_v2.md` Part B Session 14 (2026-04-28 15:35 ACST). Self-contained. Reserved as input for Session 15 multi-agent governance review.*

---

**Audience:** Session 15 multi-agent governance review. Document is self-contained and intended for extraction as `v3_data_requirements.md`. Read order does not depend on Part A; cross-references to Part A are stated where useful, but the reader can absorb this section alone.

**Purpose:** Statement of what v3's accounting layer needs from the data layer (`capture.db` + data API) to operate, organised so the upcoming DR-029 data review can audit `capture.db` against this requirement set.

### B.1 Scope of the data layer for v3

**In scope for the data layer:**

- All race-side data v3 reads on demand: race metadata, runner detail, results, time-series snapshots, scratching state, BSP, calibration data
- Sports market data (AFL, NRL at minimum): currently absent from capture.db, must be added per DR-029
- Soft-book scrape data: cadence verification per DR-014's hot-path use case
- Periodic-only API contract per DR-029 (no on-demand fresh-now)
- API versioning and contract documentation (per DR-028 forbidden pattern 3)

**Out of scope:**

- Analytics layer formalisation (deferred per DR-029)
- Account-isolation layer (deferred per DR-029)
- Cloudflare-blocked book scraping (deferred per DR-029, "an entire project in itself")
- v3-side caching, mirroring, or denormalisation of any of the above (forbidden per DR-028)

### B.2 Race-side data requirements

#### B.2.1 Race metadata

For every AU thoroughbred / harness / greyhound race v3 might log a bet against, the data layer must expose, indexed by `event_id` (Betfair market_id) and resolvable by `(race_date, venue_normalised, race_number)`:

- Race classification (`race_class`)
- Race distance (`race_distance` in metres)
- Race surface (`race_surface`: turf / synthetic / dirt or applicable code-equivalent)
- Race group / tier (e.g., G1 / G2 / G3 / Listed / Stakes / Handicap)
- Track condition at jump
- Track type (e.g., flat / circle / trotting / pace)
- Scheduled jump time
- Actual jump time (post-jump)
- Race code (thoroughbred / harness / greyhound)
- Venue (canonical name)
- Race number

**NZ thoroughbred / harness / greyhound:** out of scope day-one; re-asked as a sub-question under B.7 #3 (DR-029 scope rightness) — see footnote there.

#### B.2.2 Runner-level metadata

Per runner per race, indexed by Betfair selection_id and race natural key:

- Runner name (canonical, with operator-friendly normalisation for display)
- Barrier / box / draw
- Weight carried (where applicable)
- Jockey / driver / trainer
- Form indicators where Racing API exposes them (last-start, days since last run, distance change, code change)
- Finishing position (post-result)
- Beaten margin (post-result)
- BSP (Betfair Starting Price) where available
- Scratching events with timestamp (scratched_at, late_scratch flag)

#### B.2.3 Race results

For settled races:

- Finish positions for all starters
- Dead-heat indication
- Stewards' inquiry status (where reported)
- Margin between positions
- Race time / sectional times where source exposes them
- Result observed_at timestamp from source
- Source identifier (Betfair / Racing API / Racing Australia / Racenet)

**Auto-settlement reads from the data layer.** v3's `bet_settled` for racing bets uses VPS race result as canonical for "what happened in the race." Two-source agreement (e.g., Betfair Win + Racing API) → `finalised`. Single high-confidence source → `finalised`. Low-confidence single-source or divergence → `provisional`, surfaced to Burst Review.

#### B.2.4 Betfair time-series snapshots

For each runner in each in-scope market, the data layer captures and exposes:

- Best back price + size available
- Best lay price + size available
- Top 3 back prices + sizes (market depth)
- Top 3 lay prices + sizes (market depth)
- Total matched on the market
- Snapshot timestamp

**Cadence:** existing capture.db tiered cadence (5 min standard → 60s pre-jump intensive in 5 min window → 60s in-running → 2 min settlement checks).

**Cadence verification is a DR-029 data-review item.** Empirical check that pre-jump cadence is tight enough for v3's actual bet-log timing distribution. Resolution paths in priority order if insufficient: (a) extend pre-jump intensive window; (b) tune standard-cadence interval; (c) accept staleness with operator-visible indicator. On-demand pattern is not introduced unless (a)/(b)/(c) fail.

#### B.2.5 Bookmaker time-series snapshots

For DR-014's burst-mode soft-book price context:

- Existing scrapers (Entain, PointsBet, Unibet, PlayUp, TABtouch, Sportsbet via Racing API) produce time-series snapshots at 5 min standard / 90–120s intensive cadence
- Cadence sufficiency for DR-014's hot-path use case is **a DR-029 data-review item** — verification, not assumption
- Cloudflare-blocked books (Sportsbet non-racing, BetRight, Betr, PalmerBet, Dabble) deferred per DR-029

#### B.2.6 BSP and calibration data

- BSP per runner per race (post-jump)
- Daily calibration summaries (existing capture.db output)
- Batch summaries (existing capture.db output)

These support the Racing EV model and any future racing analytics. Already in capture.db; v3 reads via data API on demand.

### B.3 Sports market data requirements

**Currently absent from capture.db. First item in the DR-029 data review.**

For Betfair sports markets (AFL, NRL day-one; other sports via review scope decision):

- Market identifiers (event_id, market_id, selection_id) per match
- Match metadata (teams, scheduled start time, league, round, season)
- Match results (post-event)
- Time-series snapshots equivalent to B.2.4 — best back/lay + sizes, depth, total matched, timestamp
- BSP equivalent where available
- SGM market structure where Betfair exposes joint markets (drives Slice 3 SGM model fields)

**Day-one v3 sports-bet behaviour without sports capture:** v3 logs sports bets with `bf_snapshot_unavailable = true`. Surfaced in Burst Review. Auto-settlement for sports bets falls back to operator-confirmation path until sports capture lands.

**Soft-book sports market coverage:** separate scope question for the data review.

### B.4 Data API contract

The data API (`racing-api.service` on UK VPS, `127.0.0.1:8400` over SSH tunnel; v3 `vps_client` is the integration module) exposes the data above through a versioned contract.

**Contract requirements per DR-028 forbidden pattern 3:**

- Versioned endpoints (e.g., `/v1/race/{event_id}/metadata`, `/v1/race/{event_id}/snapshot/latest`, `/v1/race/{event_id}/result`)
- Schema change discipline: backward-compatible additions in-place; breaking changes only via new version
- Deprecation policy with notice period
- Contract documentation lives with the data layer, not v3
- v3's `vps_client` interface is specified against the locked contract
- Schema-drift surfaces in `vps_client` (one file), not scattered across v3 modules

**Periodic-only API pattern (DR-029):**

- `vps_client.get_latest_snapshot(event_id, runner_id)` returns most-recent stored snapshot with its timestamp; v3 derives staleness
- `vps_client.get_market_curve(event_id, runner_id, from_ts, to_ts)` returns time-series for analytical queries
- `vps_client.get_race_result(event_id)` returns settled race result
- `vps_client.get_scratch_state(event_id, as_of)` returns scratching events up to a timestamp
- `vps_client.get_race_metadata(event_id)` returns race classification and runner detail

**No on-demand fresh-now endpoint.** Periodic capture is sufficient given analytical bracketing.

**VPS-unreachable handling:** v3 logs the bet with `bf_snapshot_unavailable = true`, surfaces in Burst Review.

### B.5 External analytics environmental scan (data-review item)

**Time-boxed to two sessions of work** in the DR-029 data review (covering racing AND sports as parallel work-streams).

**Methodology:**

1. Source-by-source field inventory: what does Betfair API expose beyond current capture? Racing API beyond current use? Other accessible sources (official racing bodies, free historical archives, sectional times, league data feeds, fitzRoy, AFLTables, NRL-equivalents)?
2. Analytics literature reconciliation: published research, public-domain models, betting-syndicate disclosures, Kaggle, blog posts. What features matter predictively?
3. Cross-reference into capture decisions, three buckets:
   - Available + currently captured → no action
   - Available + not currently captured + cheap → capture in the data review
   - Available + not currently captured + expensive, OR not available → parked with rationale
4. Cost test: capture-cheap filter only. No new external API calls beyond what's already authorised.
5. Capture-only constraint: no analytics design happens here. The analytics layer remains deferred and out of scope.

### B.6 Data review sequencing (DR-029)

The pre-build sequencing (already documented in DR-029):

1. Reconciliation contract write-up across Slices 1–6 — **Session 12 produced v1; Session 13 produced delta-spec; Session 14 produces v2 (this document) and promotes.**
2. Build strategy decision — likely Session 15+ now after multi-agent review reframes the question.
3. First multi-agent governance review — Session 15, assesses DR-029 sequencing, this v3 data requirements doc, the deferred bet-schema-simplification question, the periodic-only API pattern, and DR-029 scope rightness (with NZ folded in).
4. Data review scoping — post-multi-agent-review.
5. Pre-execution governance review — operator go/no-go on data review scope.
6. Data review execution — extensions built, tested, documented, contract versioned. Per-extension governance check.
7. Final data layer lock review — confirms API contract is locked, `vps_client` interface is specified, data layer is fit-for-purpose.
8. v3 build begins.

### B.7 Open questions reserved for Session 15 multi-agent review

These are reserved for the review and **must not be pre-empted** in the data review scoping.

1. **Bet schema simplification.** Whether DR-026 inline snapshot storage and Slice 6 `field_size_at_bet_placement` / `field_size_at_settlement` should be removed in favour of full cross-DB resolution from capture.db (bet stores only identifiers + placement_time; race-side context resolved via `vps_client` at read time). If adopted, simplifies bet_placed payload, revises the Slice 6 amendment, cleans DR-028 forbidden pattern 1 by removing its single narrow exception. **Until reviewed, current schemas remain in force.**

2. **DR-029 sequencing soundness.** Whether the data-layer-first sequencing (review → extend → lock → then v3 build) is the right structural protection given v3's actual risk profile.

3. **DR-029 scope rightness.** Whether the in-scope items (race-data fit-for-purpose, sports market layer, periodic-only API pattern, settlement model, external analytics environmental scan, API contract versioning) and out-of-scope items (analytics layer, account-isolation layer, Cloudflare-blocked books) are correctly drawn. **Footnote:** NZ inclusion is re-asked here as a sub-question — verify Racing API NZ coverage; if available, NZ enters scope; if not, NZ remains day-one limitation.

4. ~~**NZ inclusion.**~~ Folded into #3 as a footnote.

5. **Periodic-only API pattern with analytical bracketing.** Whether the periodic-only architecture (no on-demand fresh-now, cadence verification as fallback path) is the right structural commitment for the VPS data API contract and `vps_client` interface. Independently assessed alongside #1 because they share a data-shape concern but address different parts of the architecture (#1 is bet-record storage; #5 is the API contract itself). The DR-029 deliberation in Session 11 reasoned through this with the bracketing argument (surrounding-interval snapshots from `capture.db` at analysis time are structurally stronger than a single fresh on-demand snapshot, because they tell us about market movement *around* the bet rather than at a single point) — Session 15's review is independent assessment of this deliberated decision.





### B.8 What this document does NOT contain

- It is not the data review scoping. That's post-Session-15 work, after the multi-agent review approves direction.
- It does not specify new data fields to capture. The environmental scan in B.5 is the methodology for surfacing those during the data review.
- It does not pre-empt the deferred bet-schema-simplification question. The current schema is documented; the simplification is flagged but not adopted.
- It is not exhaustive of v3's queries against the data layer. It captures the structural shape of v3's data dependence; specific query patterns surface during build.

---


### Document 3 — Architecture (current)

# Architecture (current)

*Companion document for the multi-agent governance review. Drafted Session 18 (2026-04-28). Descriptive — what is locked, what entities exist, what DRs apply. Framed for assessors reading without prior project context. Citations to DRs by number with a one-line gloss; the DR index at the end (§7) collects these for back-reference.*

---

## 1. What this document covers

v3 is the rebuild of an existing matched/promo betting tool (currently called BetHub v2). v2 has been running for months and continues to operate during the rebuild. v3 inherits the operational shape v2 produced — accounts at bookmakers, promotional bets, hedging on Betfair, free-bet ledger, AccountCare conditioning, a VPS-based racing-data capture system already in production — and rebuilds the software around that operational shape with v2's accumulated failure modes designed out.

This document describes the v3 architecture as it currently stands across Slices 1–6 of the rebuild design work (Sessions 5–10), with subsequent amendments through Session 14. It is descriptive, not persuasive: the goal is to give an assessor enough of v3's architectural shape to engage with the four review questions in `v3_data_requirements.md` (B.7) and the framing in `decision_under_review.md`. It does not re-derive design choices — those live in `decisions.md`.

---

## 2. High-level architectural shape

**Three layers (DR-002).** v3 separates into three layers with strict boundaries between them:

- **Operational layer** — daily and weekly cadence. Profile and account switching, AccountCare conditioning, promo allocation across accounts, the action queue surfacing what to do next.
- **Execution layer** — per-bet cadence. Bet logging, hedging on Betfair, EV calculations, live odds display, race-window navigation.
- **Accounting layer** — quiet background. Event log, derived balances, free-bet ledger, reconciliation surfaces, reports.

Each layer has one job and a defined interface to the others. v2's failure shape was that all three concerns mixed in every page, so a UX change to a promo-cap field touched the schema. v3's strict-boundary discipline is the structural fix.

**Two databases (DR-027).** Bet-data and race-data are owned by separate databases:

- **v3's accounting-layer database** (working name `bethub.db` or successor) owns bet-data: every entity and event involved in the bet lifecycle, settlement, hedging, promo cycles, free-bet ledger, cash flow, and the day-one AccountCare implementation.
- **`capture.db`** (existing UK VPS racing-data capture system) owns race-data: races, runners, finish positions, Betfair time-series snapshots, bookmaker time-series snapshots, BSP, daily calibration summaries.

No fact lives in both databases. v3 reads race-side context on demand at read time through a single integration module. The two-database stance is recognition, not invention — capture.db has been running on the VPS for months, but its current consumer situation is materially weaker than continuous use: BetHub v2 has code wired to it (racing page, result lookup during settlement), but the SSH tunnel that v2 depends on for VPS reach is frequently down, often for days at a stretch, with no operational impact on v2 because v2's actual bet-settlement path goes direct to Betfair API and the racing page isn't a primary operator surface. In effect, capture.db today is a quietly-running data layer without a real active consumer. v3 is the first consumer that will use the data layer at execution time, and that materially changes the operational stakes on tunnel reachability — §5 returns to this.

**Operating-mode and analytical-mode separation (DR-024).** A second separation cuts orthogonally to the three layers: operating-mode surfaces (action queue, bet logger, hedge modal, anything inside a burst) display only forward-looking, decision-relevant context; analytical-mode surfaces (reports, reconciliation views, P&L, EV-realised-vs-estimated dashboards) live behind dedicated entry points. The operator does not see "how am I doing today" while operating. This shapes which derivations get computed where, and it appears in the reconciliation-surface design (§6).

---

## 3. Entity model (v3 bet-data side)

Eight v3-side entities (Slice 1 lock):

```
account
  └── account_at_book ─── book ─── ownership_cluster
                                    └── platform
                              │
                              └── promo (when book runs an offer)
                                    └── promo_template
                              │
account_at_book
  └── bet ─── promo (nullable FK)
```

**Vocabulary (DR-022).** `account` is a real person (Tim, Kate, friends) whose identity is used for registrations. `book` is the betting company (Sportsbet, PointsBet, Ladbrokes, etc.). `account-at-book` is the specific registration of one account at one book — the unit at which money sits, promos arrive, and conditioning happens. One account never holds two registrations at the same book. Older DRs (DR-010, DR-013) use "persona" where the corrected reading is "account."

**Cash-flow reference data (Slice 5):**

- `account_holders` — custodian identity for the cash-flow model (Tim plus other people who hold operation cash on Tim's behalf).
- `payees` — recipients for non-bet outflows (tax, infrastructure, data subscriptions, tooling).
- `warning_catalogue` — closed-schema-open-vocabulary reference for AccountCare warnings.

**No `race` entity exists in v3.** Race-side data lives in capture.db. Bets carry race-side identifiers as references, not as foreign keys: Betfair `market_id` (primary), the natural-key tuple `(race_date, venue_normalised, race_number)` (fallback). Race classification, distance, surface, finish position, runner detail, BSP, time-series snapshots — none of these live on v3 entities. Where v3 needs them, it reads on demand through the integration module described in §5.

---

## 4. Event log — the spine

v3's accounting layer is event-sourced. A single append-only event log holds every event type. Derived state (balances, FB inventory, hedge state, reconciliation views) is computed at read time from the event log per DR-019 — v3 stores no aggregates and no balances.

**Common event header.** Every event carries: `event_id`, `event_type` (closed enum), `recorded_at` (system clock at write time), `occurred_at` (when the underlying real-world fact happened), context FKs (`account_id` / `book_id` / `account_at_book_id` where relevant), `supersedes_event_id` (nullable; for corrections), `parent_event_id` (nullable; e.g. `bet_settled.parent_event_id` → `bet_placed`), `payload` (JSON, type-specific), `source`, `correlation_id`, `notes`.

**Event categories.** Consolidated from Slices 2–6:

- *Bet lifecycle* — `bet_placed`, `bet_correction`, `bet_settled`, `bet_leg` (SGM legs), `lay_order_finalised`, `hedge_state_classification`.
- *Promo lifecycle* — `promo_observed`, `promo_journey_annotation`, `free_bet_credited`, `free_bet_deployed`, `free_bet_revoked`, `free_bet_expired`, `promo_cash_credited`.
- *AccountCare* — `accountcare_warning_raised`, `accountcare_warning_cleared`.
- *Cash flow (two-balance-location model)* — `account_holder_funding`, `account_at_book_deposit`, `account_at_book_withdrawal`, `account_holder_remittance`, `account_at_book_balance_adjustment`, `account_holder_balance_adjustment`, `external_payment`, `profit_share_distribution`.

**Supersession semantics.** Corrections never delete or modify the prior event. A correction writes a new event with `supersedes_event_id` pointing at the prior event; both remain in the log permanently. Derived state walks the supersession chain at read time, treating only the most-recent non-superseded event as authoritative. Cascade rules govern what other event types are auto-superseded when a `bet_settled` is superseded — closed list, day-one limited to `free_bet_credited` and `promo_cash_credited`, with auto-cascade for mechanically-clean full invalidation and manual cascade (operator-explicit) for graded cases.

**Two-balance-location cash-flow model (Slice 5 + Session 14 amendment).** v3 tracks two balance locations: account-at-book balances (Location 1, derived from cash-flow events touching specific account-at-books) and cash holdings with custodians (Location 2, derived per-custodian from funding, deposits, withdrawals, remittances, profit-share distributions, and balance adjustments). Tim's personal bank account is *not* in the model — Tim's bank includes personal activity v3 does not see, so v3 cannot produce a "current bank balance" figure. An informational *operation-net-flow* view computes cumulative net impact on Tim's bank since day 0 from the four bank-touching event types (funding out, remittance in, external payment out, profit-share distribution out where funded directly from Tim). It is informational, not a reconciliation surface (§6 distinguishes).

---

## 5. Cross-DB integration boundary

### 5.1 capture.db — what it is

capture.db is an existing SQLite database running on a UK VPS as part of the racing-data capture system. It captures Betfair time-series price-and-volume snapshots and bookmaker scrape data for Australian thoroughbred, harness, and greyhound racing on a tiered cadence (5 min standard / 60s pre-jump intensive in the 5-min window before scheduled jump / 60s in-running / 2-min settlement checks). It also stores race results, BSP, and daily calibration summaries. The system predates v3 by months and runs continuously on the VPS itself.

The consumer situation today, framed honestly: BetHub v2 has code wired to capture.db's data API — the racing page and the betfair_sync settlement path both call it — but in practice the SSH tunnel that v2 needs for VPS reach is frequently down for extended periods (at the moment of writing, the tunnel has been unreachable continuously for at least six days, with v2 logs showing health-check failures every 30 seconds throughout). v2 has been operating normally throughout this window because its actual settlement path is direct to Betfair API, not via VPS, and the racing page isn't a primary operator surface. So although capture.db has been collecting data the whole time, it has no real active consumer at the moment. v3 is the first consumer that will use the data layer at execution time — at every bet log, on every settlement, in burst review.

This materially changes the operational stakes on tunnel reachability. v2 demonstrates that "VPS unreachable for a week, no one notices" is the empirical default. v3's design has v3 reading capture.db on every bet log; the `bf_snapshot_unavailable = true` graceful-degrade flag in DR-026 is currently theoretical insurance against a failure mode v2 has demonstrated is actually common. v3 building on top of an integration the operator has not had to keep alive operationally is a real risk worth naming explicitly. v3 does not own capture.db, does not write to it, and does not duplicate any of its data — but v3 *does* take on a continuous-availability requirement that v2 has not enforced.

Sports markets (AFL, NRL, others) are *not* covered by capture.db today. Day-one v3 sports bets log with a `bf_snapshot_unavailable = true` flag until a sports-capture extension is built — first item in the upcoming DR-029 data review.

### 5.2 The boundary

Per DR-027 (two-database architecture):

- v3 references race-side data by stable identifier — primarily Betfair `market_id`, fallback the natural-key tuple `(race_date, venue_normalised, race_number)`.
- v3 reads race-side context on demand through the existing read-only data API on the VPS (currently `racing-api.service`, reached over SSH tunnel at `127.0.0.1:8400`).
- Cross-DB joins happen at read time in Python at the integration boundary — not in SQL.
- All v3 access flows through one Python module (working name `vps_client`). No raw SQLite reads from capture.db elsewhere in v3. No second HTTP client. No bypass.

Per DR-028 (integration boundary discipline), four patterns are forbidden:

1. **No race-data caching in v3.** v3's database stores no race-data fact. The single narrow exception is the DR-026 inline market-context snapshot on `bet_placed` (best back/lay price + size, total matched, snapshot timestamp), justified explicitly on cross-system-durability grounds — and itself flagged as one of the four review questions for this assessment.
2. **No race-data denormalisation onto v3 entities.** No race classification, no distance, no surface, no finish-position-derived-from-VPS on v3 rows. The Slice 6 `field_size_at_bet_placement` and `field_size_at_settlement` fields on `bet_settled` are bet-context captures (race state at specific bet-context moments), not race-context denormalisations — they are also under review alongside the DR-026 inline snapshot, as one paired question.
3. **No second integration point.** Schema drift, contract changes, and integration failures must surface in one file, not scattered.
4. **No reflexive extension to additional external sources.** Adding a third data source (a second VPS service, a third-party API, another database) requires its own architectural decision; the DR-027 pattern grants no standing permission.

### 5.3 Read-time uses

| v3 event or query | Reads from capture.db (via vps_client) |
|---|---|
| `bet_placed` write (live mode) | Latest snapshot for `(market_id, runner_id)`; scratch state at `bet_placed_at` |
| `bet_placed` write (retrospective) | Same, with snapshot-aligned-to-placement flag = false |
| `bet_leg` write (SGM) | Per-leg snapshot for each leg's `(market_id, selection_id)` |
| `bet_settled` auto-settlement | Race result for `event_id` (finish positions, dead-heat, scratch list) |
| Burst Review filter by race class | Race classification for each bet's `event_id` |
| Analytical queries (timing, counterfactual, EV calibration) | Full price-and-volume curve from time-series |

### 5.4 Periodic-only API pattern (DR-029)

The data API returns the most-recent stored snapshot from capture.db (typically 0–60 seconds old in pre-jump windows) with its timestamp, plus scratch state. v3 stores this inline on the bet record and marks staleness flags above tunable thresholds. **No on-demand fresh-now snapshot pattern is added to the API.** The analytical justification is bracketing: surrounding-interval snapshots (T-x and T-x+cadence) read from capture.db at analysis time bracket the bet's true market state across the bet timestamp, observing market movement *around* the bet rather than at a single point — structurally stronger than a single fresh on-demand snapshot. Cadence verification is a data-review item; if pre-jump cadence proves insufficient, resolution paths in priority order are: extend the pre-jump intensive window, tune standard-cadence interval, accept staleness with operator-visible indicator. On-demand is a last resort. This pattern is one of the four review questions.

---

## 6. Reconciliation surfaces

Reconciliation is what v3 is named for. Six reconciliation surfaces are produced as natural outputs of derived state vs. operator-observed reality. Each lives in its own view; each is a derived-on-read computation against an external check.

| Surface | Compares |
|---|---|
| **Cash reconciliation** | Computed at-book balance (Location 1) vs operator-entered actual book balance |
| **Free-bet reconciliation** | Computed FB inventory vs operator-counted FB credits visible at the book |
| **Settlement reconciliation** | v3 auto-settled bets vs operator's observation of book payout |
| **Race-result reconciliation** | capture.db race result vs book settlement |
| **Hedge reconciliation** | Hedge state per the derivation algorithm vs operator's mental model |
| **Cash-holding-with-custodian reconciliation** | Computed Location 2 per custodian vs custodian's actual bank balance dedicated to the operation |

**Operation-net-flow view (informational, not a reconciliation surface).** Cumulative net impact on Tim's bank since day 0, derived from the four bank-touching event types. It is *not* a reconciliation surface because Tim's actual bank statement isn't an apples-to-apples external check — it includes personal spending v3 does not see. Operation-net-flow answers "since day 0, how much net cash has the operation pulled from / returned to my bank." It does not answer "what is my current bank balance."

**Settlement-divergence philosophy (DR-029).** VPS race result is canonical for "what happened in the race." Operator-recorded book settlement is canonical for "what the operator's cash outcome was." Where the two diverge — voids per book rules, dead-heat handling differences, stewards' inquiry resolutions — the divergence is a reconciliation signal, not an algorithmically-resolved conflict. No confidence hierarchy is built; the architecture treats divergence as information.

**Burst Review — the operator-facing detection workflow.** Two terms first. *Burst* is v3's name for an unplanned span of opportunistic operating time, triggered by available promos — can last 20 minutes (a casual Tuesday afternoon) or 6+ hours (a Saturday spring-carnival day); within a burst the operator switches rapidly between accounts and books to take time-sensitive promos before race jumps. *Persona session* is the contrasting mode: an explicit, planned span operating as a single account for non-time-critical work (conditioning bets, browser activity, account upkeep), with profile and isolation infrastructure locked to that account for the duration. Bursts and persona sessions are the two operating-mode contexts; together they cover every operator-active moment, and DR-024's operating/analytical separation applies during both. (Vocabulary note: persona-session terminology is from DR-010, before DR-022 corrected "persona" to "account" — read it as a single-account session.)

Reconciliation surfaces feed a Claude-driven burst-review triage workflow designed in as a day-one capability. Claude extracts everything flagged across the six surfaces and other anomaly signals, investigates each, and presents the operator with a triaged list. Operator-initiated, Claude-driven. This is the v3 successor to v2's flagged-items page (which was a passive surface that didn't get traction). The cost of administrative overhead and detection time is the operator's named first concern in the DUR; the burst-review design is the structural answer.

---

## 7. DR index — short reference for back-cites in this document

- **DR-002** — three-layer separation (operational / execution / accounting) with strict boundaries.
- **DR-007** — vocabulary discipline: definitions of "concern," "decision," "principle," "metric" locked.
- **DR-019** — derived state computed on read, not stored. Bets and operations log entries are the source of truth; everything else is computed at read time.
- **DR-022** — vocabulary correction: `account` (person) / `book` (bookmaker) / `account-at-book` (registration).
- **DR-024** — operating-mode and analytical-mode surfaces are separated; operating-mode does not show "how am I doing" data.
- **DR-026** — at-log-time market-context snapshot captured on every bet (single narrow caching exception per DR-028 forbidden pattern 1; under review).
- **DR-027** — two-database architecture: v3 bet-data and capture.db race-data are separately owned, joined at read time by reference.
- **DR-028** — integration boundary discipline: four forbidden patterns (no race-data caching, no race-data denormalisation, no second integration point, no reflexive extension to additional external sources).
- **DR-029** — data layer reviewed and brought to v3 fit-for-purpose before v3 build begins; periodic-only API pattern with analytical bracketing locked; settlement-as-reconciliation-not-hierarchy locked.

Slice records (Slices 1–6) live as session logs in the rebuild folder; this document compresses what they collectively lock. The full reconciliation-contract walkthrough is in `architecture.md` §A.0–A.9; this document is the framed-for-outside-readers compression.


### Document 4 — Data layer (current)

# Data layer (current)

*Companion document for the multi-agent governance review. Drafted Session 19 (2026-04-28). Descriptive — what `capture.db` and its data API do today, what fields are captured, what cadence runs in practice, what gaps exist. Framed for assessors reading without prior project context. Sits alongside `architecture_current.md` in the doc suite; extends that document's §5.1 into data-layer-specific detail without re-stating it.*

---

## 1. What this document covers

`architecture_current.md` describes v3's bet-data side — entities, event log, reconciliation surfaces, the cross-DB integration boundary. This document describes the *other* database in the two-database architecture: `capture.db`, the existing UK VPS racing-data capture system that v3 reads from but does not write to.

The framing is descriptive: what `capture.db` does today, not what v3 needs from it. The needs side lives in `v3_data_requirements.md` (B.1–B.6). The ask of this document is to give assessors the factual ground — what's actually being captured, at what cadence, with what coverage, with what gaps — so that the four review questions in `v3_data_requirements.md` (B.7) can be assessed against the actual data layer, not against an idealised one.

A **v3-stakes question for assessors** is surfaced in §8 alongside (not folded into) the four B.7 questions.

---

## 2. What `capture.db` is and where it runs

`capture.db` is a SQLite database running on a UK Hostinger VPS as part of an existing racing-data capture system. The system predates v3 by months and runs continuously. It has its own service (`racing-api.service` on the VPS) exposing a read-only HTTP data API, reached from the operator's local environment over an SSH tunnel at `127.0.0.1:8400`.

The capture system itself comprises:

- A Betfair time-series capture process polling the Betfair API on a tiered cadence for AU thoroughbred / harness / greyhound markets.
- A set of bookmaker scrapers (Entain, PointsBet, Unibet, PlayUp, TABtouch, Sportsbet via Racing API) running on the same VPS, writing time-series price snapshots into `capture.db`.
- A race-metadata and race-results population path drawing from Racing API and result-source feeds.
- BSP capture post-jump.
- Daily calibration summaries and batch summaries derived from the time-series data.

The system was originally built to serve a multi-consumer ecosystem (Strategy 1, BetHub v2, the Racing EV model, AFL Edge). The actual current consumer state is described in §3 — it differs materially from the original framing.

**v3 does not own `capture.db`.** v3 reads via the data API; v3 does not write; v3 does not duplicate any of its data on the bet-data side beyond the single narrow DR-026 inline-snapshot exception. The cross-DB boundary discipline is locked in DR-027 / DR-028.

---

## 3. Current operational reality

Empirically verified during Session 18 (2026-04-28) via v2 codebase inspection (`api/racing.py`, `betfair_sync.py`) and `bethub.log` review:

**capture.db has no real active consumer at present.** The originally-framed multi-consumer ecosystem is not the current state. Strategy 1 is not yet operational. AFL Edge has been mothballed for months. The Racing EV model is not a live execution-time consumer. BetHub v2 has code wired to capture.db's data API in two places — the racing page and the betfair_sync settlement path — but in practice the SSH tunnel that v2 depends on for VPS reach has been unreachable continuously for at least six days at the time of this writing, with v2 logs showing health-check failures every 30 seconds throughout that window.

**v2 has been operating normally throughout the tunnel-down period.** Settlement goes direct to Betfair API rather than via VPS; the racing page isn't a primary operator surface. The launchd plist `com.bethub.vps-tunnel.plist` exists at `~/Library/LaunchAgents/` but isn't currently running. Tunnel restart is a likely-easy fix, but the operational signal is what matters: VPS unreachable for a week, no one notices.

**v3 is the first execution-time consumer that will actually exercise the integration.** v3's design has v3 reading `capture.db` on every bet log, on every settlement, in burst review. The `bf_snapshot_unavailable = true` graceful-degrade flag in DR-026 is currently theoretical insurance against a failure mode v2 has demonstrated is the empirical default rather than the exception. v3 takes on a continuous-availability requirement that v2 has not enforced — monitoring, auto-restart, alerting — and that requirement is currently unspecified.

**Operator familiarity has decayed alongside consumer absence.** The operator does not currently have confident knowledge of which `capture.db` fields are reliably populated, what cadence holds in practice versus what was specified at build time, or where the rough edges sit. This is the same root cause as the reachability gap: a data layer with no real active consumer accumulates uncertainty about its own state. The DR-029 data review is the structural answer — sections 4–6 below frame each field set as schema-defined with empirical state requiring verification during that review, rather than asserting current population state.

**Why this matters for assessors.** The architectural elegance of the two-database split (DR-027) and the integration boundary discipline (DR-028) sits on top of an availability assumption that has not been operationally validated, and a population-state assumption that has not been recently re-verified. v3 building on top of an integration the operator has not had to keep alive — and whose contents the operator no longer holds in working memory — is a real risk worth naming explicitly. §8 carries this through as a v3-stakes question.

**Analytical-versus-operational distinction (operator-discovery, Session 19).** Re-encountering documented cadence during Session 19 review surfaced a structural distinction the existing documents have quietly conflated. `capture.db` is built as an *analytical* data layer — polled snapshots written to a database for post-hoc bracketing, modelling, and calibration, with retention indefinite and latency tolerance in minutes-to-hours. v3 also has an *operational* live-pricing need — sub-second prices in the burst window for in-the-moment decision-making, with retention zero and latency tolerance sub-second. These are different consumers with different requirements, not the same data path with a tunable cadence dial. For Betfair, the operational pattern is uncontroversial — Betfair offers a Streaming API designed exactly for this and a direct connection from v3 is the obvious shape. For soft-book operational live pricing, no equivalent pattern exists — see §5.4. Neither operational surface is currently designed in v3, and the distinction sharpens the v3-stakes question in §8.

---

## 4. Race-data fields captured (schema-defined)

Indexed primarily by Betfair `market_id` (event identifier) and resolvable by the natural-key tuple `(race_date, venue_normalised, race_number)`. Scope: AU thoroughbred, harness, and greyhound racing. NZ is not currently in scope.

The fields below are what the schema defines. Empirical population state — which fields are reliably populated, which are sparse, which are nominally present but unusable — is not currently held with confidence by the operator and will be re-verified in the DR-029 data review.

### 4.1 Race metadata

Schema-defined fields per `v3_data_requirements.md` B.2.1: `race_class`, `race_distance` (metres), `race_surface` (turf / synthetic / dirt), `race_group` (G1 / G2 / G3 / Listed / Stakes / Handicap), `track_condition` at jump, `track_type` (flat / circle / trotting / pace), `scheduled_jump_time`, `actual_jump_time` (post-jump), `race_code` (thoroughbred / harness / greyhound), `venue` (canonical), `race_number`.

### 4.2 Runner-level metadata

Schema-defined fields per `v3_data_requirements.md` B.2.2: indexed by Betfair `selection_id`. Runner name (canonical, with operator-friendly normalisation), barrier / box / draw, weight carried (where applicable), jockey / driver / trainer, form indicators where Racing API exposes them, finishing position (post-result), beaten margin (post-result), BSP, scratching events with timestamp (`scratched_at`, `late_scratch` flag).

### 4.3 Race results

Schema-defined fields per `v3_data_requirements.md` B.2.3: finish positions for all starters, dead-heat indication, stewards' inquiry status (where reported), margin between positions, race time / sectional times where source exposes them, result `observed_at` timestamp, source identifier (Betfair / Racing API / Racing Australia / Racenet).

Auto-settlement reads here: v3's `bet_settled` for racing bets uses VPS race result as canonical for "what happened in the race." Result-source-disagreement handling and lag-from-finish-to-population are empirical-state items for DR-029 verification.

### 4.4 Betfair time-series snapshots

Per runner per in-scope market, snapshot fields: best back price + size, best lay price + size, top-3 back depth, top-3 lay depth, total matched, snapshot timestamp.

DR-020 documented cadence (tiered): 5-minute standard outside the pre-jump window; 60-second pre-jump intensive in the 5-minute window before scheduled jump; 60-second in-running; 2-minute settlement checks. Whether this cadence still holds in practice is one of the central DR-029 verification items, given that the analytical-bracketing argument in DR-029 leans on pre-jump cadence being tight enough.

**Operator-flagged concern, surfaced during Session 19 review:** the documented 60-second cadence near jump and in-running prompted re-examination, and the primary realisation is structural rather than tuning-related. `capture.db` is an analytical capture layer; the operational live-pricing need v3 has near jump (per §3) is a separate concern that this layer was not built to serve and should not be tuned to serve. There is also a secondary, narrower analytical-bracketing concern — if the bracketing snapshots either side of a logged bet placed in the last 60 seconds before jump are 60 seconds apart in a fast-moving market, the bracket may be too wide to be analytically meaningful. The bracketing concern is real but secondary; whether it materially affects v3's analytical needs depends on how often racing bets are actually placed inside that window in operator workflow, which is a DR-029 verification item. The structural concern — that operational live pricing is a separate need requiring a separate design — is the load-bearing one and is carried through §3 and §8.

### 4.5 BSP and calibration data

BSP per runner per race (post-jump). Daily calibration summaries and batch summaries are produced as derived outputs of the time-series data. Coverage reliability across the three codes is a DR-029 verification item.

---

## 5. Bookmaker-data fields captured (schema-defined)

Soft-book time-series snapshots are captured via dedicated scrapers running on the same VPS, writing into `capture.db` alongside the Betfair time-series data. Same caveat as §4 applies: the field and scraper sets below are schema- and configuration-defined; current empirical state (which scrapers are actually running, which have died, which produce reliable data) is a DR-029 verification item.

### 5.1 Scrapers (configuration-defined)

Per `v3_data_requirements.md` B.2.5 and DR-014: Entain (Ladbrokes/Neds), PointsBet, Unibet, PlayUp, TABtouch, Sportsbet via Racing API. TAB API was flagged as "needs TAB Studio registration" in earlier context and has not been confirmed live. Cloudflare-blocked books (BetRight, Betr, PalmerBet, Dabble, and Sportsbet non-racing) are out of scope and not captured.

The VPS scrapers route through a Decodo rotating residential proxy, which is what enables capture from books that would otherwise block standard datacenter IPs. The Cloudflare-blocked books listed above remain out of scope despite the proxy because they apply additional protections (browser fingerprinting, behavioural challenges) that Decodo alone does not bypass — they require headless-browser scraping infrastructure not currently in place.

### 5.2 Cadence (specified)

Documented cadence: 5-minute standard, 90–120-second intensive in the pre-jump window. Snapshot fields: best price per runner per market with timestamp, scrape source, race natural key. Cadence sufficiency for DR-014's hot-path use case (in-burst soft-book price context displayed alongside planned promo actions) is a central DR-029 verification item — the test is whether the cadence is empirically tight enough for the operator to trust the displayed price against what's actually on the book at decision time.

### 5.3 Sports markets

Sports markets (AFL, NRL, NBA, soccer leagues, others on the day-one v3 list per DUR §4) are **not captured** today. This is the largest known gap and is the first item in the upcoming DR-029 data review.

### 5.4 Operational soft-book live pricing (v3 need not currently designed)

v3's intended use case includes displaying soft-book prices alongside Betfair in the burst UI, both as a comparative tool and as a decision-support layer for identifying favourable EV bets at the moment of decision. This is an *operational* need (sub-second, in-the-moment, no retention requirement), distinct from the analytical soft-book capture in `capture.db` (which is the right tool for post-hoc analysis but the wrong tool for in-burst live pricing).

The operational soft-book live-pricing case is structurally harder than the operational Betfair case. Betfair offers a Streaming API designed for sub-second consumption; soft-books actively resist scraping and especially resist the high-cadence scraping operational decision-making would require. Frequency-blocking is the primary risk — current VPS scrapers work at 5-minute / 90–120-second cadence partly because that volume hides in normal-user traffic patterns; per-second cadence across multiple books simultaneously near every AU race jump is a different request-volume profile that residential proxies alone may not protect against. Proxy economics shift accordingly. The detection arms race is asymmetric — books iterate detection in days, operator finds out about a block when prices stop flowing during the burst window when the cost of degraded data is highest.

Four plausible architectural responses worth weighing:

- **Option A — in-scope, build operational soft-book layer.** Separate higher-cadence scraping infrastructure with appropriate proxy investment (likely a different proxy product than current Decodo rotating residential — sticky sessions, larger pool, or both). Maximum operational leverage, maximum engineering investment, real ongoing block-risk during burst windows.
- **Option B — out-of-scope, display last-known soft-book price from `capture.db` with explicit staleness indicator.** Burst UI shows Betfair live (sub-second from Streaming API) and soft-book prices flagged "as-of T-90s" or similar. Operator factors staleness into the decision. Lowest engineering cost, no block-risk, but degraded comparative decision-support — short-lived value windows on the soft-book side go unobserved.
- **Option C — on-demand fresh scrape per burst review.** When operator initiates a burst review on a specific race, v3 triggers a one-shot fresh scrape across in-scope books for that race only, at the moment of review. Lower request volume than continuous high-cadence (per-race-on-demand vs every-race-continuously) but still higher than current and still adversarial; middle-ground viability is uncertain.
- **Option D — third-party odds-feed vendor.** Subscribe to a commercial odds aggregator that already does the high-cadence soft-book scraping. Trade-offs: ongoing subscription cost vs one-off engineering cost, data-quality and book-coverage dependent on the vendor, lock-in risk if v3 builds operational features around their API and they raise prices or shut down, and whether available aggregators cover the specific books v3 needs (a vendor with 80% coverage of v3's day-one book list is meaningfully less useful than 100%). Operator pre-decision-homework worth doing: scan the market to identify whether a vendor exists that covers v3's specific book list at acceptable cost. If yes, the soft-book operational question shifts from "is it viable" to "build vs buy with known cost on both sides." If no, A/B/C are the only real options.

The choice among A/B/C/D is non-trivial and has downstream implications for v3's burst UI, decision-support story, ongoing operational risk profile, and the v3-stakes-question landscape in §8. The question is surfaced for the multi-agent review in §8 (sub-question 6b).

---

## 6. Known gaps

The named gaps below are operator-confirmed. The unnamed gaps — fields that look populated in the schema but aren't usable in practice, scrapers nominally running but producing garbage in specific conditions, edge cases worked around silently — are not currently held with confidence by the operator (per §3) and are themselves the substance of what the DR-029 data review verifies.

**Sports markets entirely absent from `capture.db`.** Day-one v3 sports bets log with `bf_snapshot_unavailable = true` until a sports-capture extension is built — first item in the upcoming DR-029 data review. The day-one v3 sport scope per DUR §4 (NBA, NBL, International Cricket, AFL, NRL, Tennis majors, NHL, MLB, NFL, MMA, plus EPL, La Liga, Ligue 1, Serie A, MLS) is the target of the extension.

**Soft-book cadence sufficiency for DR-014's hot-path is unverified.** The 5-minute standard / 90–120-second intensive cadence has not been empirically tested against the operator's actual in-burst decision-making latency. Verification is a DR-029 data-review item.

**Cloudflare-blocked books are out of scope.** Sportsbet non-racing, BetRight, Betr, PalmerBet, Dabble require headless-browser scraping infrastructure not currently in place. Operator-confirmed out of scope per DR-029 ("an entire project in itself").

**NZ thoroughbred / harness / greyhound is out of scope day-one.** Re-asked as a sub-question in the DR-029 data review per Session 13 revision 5; folded into B.7 #3 footnote in `v3_data_requirements.md`.

**Account-isolation layer formalisation is out of scope** for the DR-029 data review per operator decision. The TP-Link MiFi + AdsPower + SOCKS5 infrastructure remains operator-managed manual workflow.

**Empirical population-state visibility into `capture.db` itself is a gap.** As §3 notes, the operator does not currently hold confident knowledge of which fields are reliably populated, which are sparse, where the rough edges sit, or whether documented cadence still holds. The DR-029 data review is the structural answer; this document does not paper over the gap by asserting state the operator cannot confirm.

---

## 7. Data API contract surface today vs DR-029 requirements

The data API today is `racing-api.service` running on the VPS, reached at `127.0.0.1:8400` over SSH tunnel from the operator's local environment.

**What exists today.** A read-only HTTP API consumed by v2's `vps_client` module. v2's calls cover race metadata, latest snapshot lookup for `(market_id, runner_id)`, scratch state, and race result. The interface is implementation-coupled — schema lives in v2's client code rather than in formal contract documentation maintained alongside the data layer.

**What DR-029 requires.** A versioned contract (`/v1/race/{event_id}/metadata`, `/v1/race/{event_id}/snapshot/latest`, `/v1/race/{event_id}/result`, etc.), backward-compatible additions discipline, breaking changes only via new version, deprecation policy with notice period, contract documentation living with the data layer not with v3, schema-drift surfacing in `vps_client` (one file) per DR-028 forbidden pattern 3.

**Gap.** Today's interface is a working integration, not a versioned and documented contract. DR-029 calls for the lift to versioned-and-documented before v3 build begins. The lift is in scope for the post-multi-agent-review data review and is structurally important: DR-028's forbidden pattern 3 ("no second integration point") is operationally meaningful only when there *is* a documented contract for `vps_client` to be specified against.

**Periodic-only API pattern (DR-029).** Today's API returns most-recent stored snapshot from `capture.db` with timestamp. v3's design holds this pattern — no on-demand fresh-now endpoint, analytical bracketing via surrounding-interval snapshots read from `capture.db` at analysis time. The pattern is locked in DR-029 and is one of the four B.7 review questions.

---

## 8. v3-stakes questions for assessors

Two questions, surfaced separately from the four B.7 review questions in `v3_data_requirements.md`. Both operationally discovered during Sessions 18–19, framed here for the multi-agent review.

### Question 1 — Reachability and continuous-fitness discipline

v3's two-database architecture (DR-027) and integration boundary discipline (DR-028) place a continuous-availability requirement on `capture.db` and its data API. v3's design calls VPS on every bet log, on every settlement, in burst review. The graceful-degrade flag in DR-026 (`bf_snapshot_unavailable = true`) is the structural fallback when VPS is unreachable.

**The empirical context, two surfaces.** First, *reachability*: v2 has been operating normally for at least six continuous days with the SSH tunnel down and no successful VPS calls in that window. v2's wired code paths exist; v2 doesn't actually need them in execution-mode operation. Tunnel restart is a likely-easy fix that nobody has had to make, because nobody has noticed. Second, *population-state visibility*: the operator does not currently hold confident knowledge of which `capture.db` fields are reliably populated or whether documented cadence still holds in practice (§3 and §§4–6). Both surfaces share a root cause — the data layer has had no real active consumer, so neither its availability nor its contents have been operationally pressure-tested.

**What this means for v3.** v3 will be the first execution-time consumer that actually requires the tunnel to be up *and* requires the data inside `capture.db` to match what v3 thinks it's reading. v3's continuous-availability and continuous-fitness requirements are *new* operational requirements, not inherited ones. The infrastructure to enforce them — monitoring, auto-restart, alerting, escalation, and ongoing data-fitness verification past the one-off DR-029 review — is not currently specified.

**The ask of assessors.** Does v3's reachability-and-fitness discipline need to be specified before v3 build, alongside the data-layer fit-for-purpose review? Or are graceful-degrade and a one-off pre-build review sufficient — i.e., is the design genuinely robust to the same "VPS unreachable for a week, no one notices" pattern v2 has demonstrated, and to the slower drift of `capture.db` schema/cadence/coverage over v3's operational lifetime, or do these patterns indicate a structural gap in v3's design that the graceful-degrade flag and one-off review together paper over?

### Question 2 — Operational live pricing, Betfair and soft-book (analytical-versus-operational distinction)

Surfaced during Session 19 review. v3's design has not currently distinguished between *analytical* data needs (post-hoc bracketing, modelling, calibration — served by `capture.db`) and *operational* data needs (sub-second live pricing in the burst window for in-the-moment decision-making — not served by `capture.db`, and not currently designed). Per §3 and §§4.4 / 5.4, these are different consumers with different requirements; trying to serve both from the same polled-snapshot-into-SQLite path pulls the design in directions it wasn't built for. The operational layer is currently un-designed and splits cleanly into two different problems.

**6a. Operational Betfair live pricing.** v3 needs sub-second Betfair prices in the burst window for racing decisions near jump and for any in-running consideration. The pattern is uncontroversial — Betfair's Streaming API is designed for this — but the design move itself has not been made. Should v3's design specify a direct Streaming API connection from v3 (a third data surface alongside v3's own DB and `capture.db`)? How does that interact with DR-026 (which currently sources at-log-time `bf_snapshot` from `capture.db` — would the live feed be a better source when available?), DR-027 (the two-database split — does a non-database operational feed sit cleanly alongside it?), DR-028 (the one-integration-point discipline — does it extend to operational integrations or remain race-data-specific?), and B.7 #5 (periodic-only API pattern — does it become structurally cleaner if operational needs are served elsewhere)?

**6b. Operational soft-book live pricing.** v3's intended burst UI displays soft-book prices alongside Betfair as a comparative tool and EV decision-support layer. The operational pattern is structurally harder than the Betfair case — soft-books actively resist high-cadence scraping, frequency-blocking risk is real, and four plausible architectural responses exist (per §5.4): (A) in-scope, build operational soft-book layer with appropriate proxy investment; (B) out-of-scope, display last-known from `capture.db` with explicit staleness indicator; (C) on-demand per-burst-review fresh scrape; (D) third-party odds-feed vendor. The choice has meaningfully different downstream implications for engineering cost, ongoing block-risk, data quality, decision-support quality, and vendor lock-in. Assessor reasoning on the trade-offs — and on whether the question can or should be answered before v3 build vs deferred — would be valuable. Operator pre-decision-homework on whether suitable vendors exist for the specific v3 day-one book list is in flight separately and may inform the answer.

### Relationship to B.7

Both questions are independent of the four B.7 questions in `v3_data_requirements.md` but interact with them — Question 1 with all four (the data layer's continuous fitness underpins every B.7 answer); Question 2 particularly with #5 (the periodic-only API pattern argument depends on operational needs being served elsewhere; if they're not, periodic-only has to do double duty and the answer to #5 becomes harder). Assessors are invited to weigh both questions alongside the existing four.

---

## 9. Document scope notes

This document is descriptive of `capture.db`'s current state. It does not propose changes; it does not specify the data review's scope (that's the post-multi-agent-review work per DR-029); it does not enumerate v3's data needs (that's `v3_data_requirements.md`). The full DR-029 data review will produce a written audit covering race-data fit-for-purpose, sports-market layer addition, periodic-only API pattern, settlement model, external analytics environmental scan, and API contract versioning — informed by the multi-agent review's outputs and any direction adjustments those outputs prompt.


## The four agent outputs

### Assessment 1 — Software developer

[INLINE PASTE: software_dev_assessment.md]

### Assessment 2 — Project manager

[INLINE PASTE: pm_assessment.md]

### Assessment 3 — Skeptic

[INLINE PASTE: skeptic_assessment.md]

### Assessment 4 — Open questions

[INLINE PASTE: open_questions_assessment.md]

## What you are asked to produce

Write your synthesis as plain prose under the headings below. No checklist-shape bullets within sections; engage substantively. Length: as long as needed, tight rather than padded. Cite agents by seat ("the software developer argues...", "the skeptic notes...", etc.) and cite documents by section where it sharpens the synthesis.

The synthesis is structured per-question rather than per-agent, so the operator can open this document at "Question 2.2" and see the four-agent picture for that question without reading the four assessments end-to-end. Two top-level sections frame the per-question synthesis and the open-questions agent's findings; eight per-question sections carry the substance; one closing section names synthesis-derived recommendations that emerge across questions.

### 1. Coherence-of-framing — the four-agent picture

The three assessor prompts asked each agent to lead with a coherence-of-framing assessment. The open-questions agent was asked to flag framing strain. Across all four outputs, what is the picture? Where do the four converge on coherence findings, where do they diverge, and where are the strongest concerns about framing strain landing? If the four agents broadly converged on "the suite coheres" or "the suite has framing issues in load-bearing places," say so plainly and name where. If they diverged, surface the divergence structure rather than picking a side.

### 2. Question 1.1 — Bet schema simplification

For each per-question section below, the structure is the same: where the four agents agree, where they disagree and on what grounds, and any synthesis-derived observation. If only some of the agents engaged with this question (the open-questions agent in particular may not have engaged at the per-question level), say so and synthesise what is available.

### 3. Question 1.2 — Data-layer-first sequencing soundness

Same structure as §2.

### 4. Question 1.3 — Data review scope rightness

Same structure as §2.

### 5. Question 1.5 — Periodic-only API pattern with analytical bracketing

Same structure as §2. Note: Question 1.4 was reserved/folded; no synthesis section for it.

### 6. Paired weighting — Questions 1.1 and 1.5 as one structural commitment

The operator asked the three assessors to weigh 1.1 and 1.5 together as one simpler-vs-more-complex choice. Synthesise across the three pairing-weighting outputs. Where do the assessors land on the paired structural commitment, where do they diverge, and what does the synthesis say about the paired choice that the per-question syntheses (§2 and §5) don't already say?

### 7. Question 2.1 — Reachability and continuous-fitness discipline

Same structure as §2.

### 8. Question 2.2 — Operational live pricing (Betfair and soft-book)

Same structure as §2. Sub-syntheses for 2.2a (Betfair) and 2.2b (soft-book) where the assessors split them out.

### 9. Question 2.3 — AccountCare-DB future-shape pushback

This question asked the assessors to argue against an operator premise. Synthesise: did the assessors find the trajectory more probable than the operator treats it as, and on what grounds? Where they diverge — including where one or more concluded the operator's framing is right and the trajectory is not more probable — represent that fairly.

### 10. Open-questions agent — what the named list did not reach

The open-questions agent had a different brief from the three assessors. Synthesise its findings into the picture: which load-bearing-assumption findings, missing-question findings, or backgrounded-should-be-foregrounded findings sharpen or qualify the per-question syntheses above? Where do the open-questions findings land alongside the assessors' findings — converging, diverging, or surfacing concerns the assessors did not? If the open-questions agent's findings land independently of the per-question structure, surface them in their own right.

### 11. Synthesis-derived recommendations

Recommendations the four agents collectively produced that no single agent stated alone. These are findings that emerge from triangulating across agents — for example, where the skeptic's load-bearing-assumption finding combines with the open-questions agent's missing-question finding to produce a recommendation neither stated alone, or where the project manager's sequencing concern combines with the software developer's integration finding to produce a delivery-shaped recommendation. Label each as synthesis-derived and trace which agents' findings it draws on. If you find none — i.e., the four agents' findings stand on their own and the synthesis adds no recommendations beyond what any single agent stated — say so plainly. Manufactured synthesis recommendations are worse than honest absence.

## A final note on tone

The operator has named "honest pushback over agreeable validation" as the explicit preference, and asked the four assessors to soften nothing. Your synthesis should not soften them. If three of four agents agreed something is wrong, the synthesis says so plainly. If the agents converged on a verdict the operator may not want to hear, the synthesis carries it through. Smoothing is the synthesis-seat failure mode — averaging four sharp assessments into one diplomatic summary loses what the multi-agent review was for. If the four agents collectively concluded the design is roughly right in places, say so plainly without manufactured criticism. The point is to give the operator your honest synthesis where the assessors were sharp and your honest synthesis where they were not.
