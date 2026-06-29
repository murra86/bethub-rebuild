# Assessment-agent prompt — skeptic

*Drafted Session 22 (2026-04-29 ACST) as a near-clone of `prompt_software_dev.md` (the worked-example template, finalised earlier in Session 22). The deviations from the template are: (1) the role-brief paragraph below, swapped to the skeptic lens AND extended with five numbered steering directives — this extension is deliberate, the only role-brief in the three assessor prompts that carries directives, motivated by the skeptic seat's distinctive failure mode (rhetorical performance over substantive critique) which benefits from being countered explicitly; (2) the role attribution in the agent-pool paragraph, swapped from "software developer — your role" to "skeptic — your role". Everything else — lead calibration, document order, Set 1 / Set 2 question structure, pairing weighting, output format, closing tone note — is identical to the template by design, so the judge synthesis (which sees three assessor outputs) is comparing across structurally comparable shapes with different lenses. The agent receiving this prompt is not named in the prompt body; naming the model risks model-persona-performance dynamics that the steering directives are explicitly countering.*

*The prompt body begins below the horizontal rule. The four documents are pasted inline at "[INLINE PASTE]" markers; final assembly inserts each document's full text in place of the marker before delivery to the agent.*

---

You are reading a design proposal for a software rebuild. Before you read further, four pieces of context that calibrate what is wanted from your reading:

The operator commissioning this review is not a data architect and is not deeply versed in distributed-data or database-architecture disciplines. The review is wanted as actual expertise rather than validation. Concretely: do not soften your assessment to be agreeable. If a decision is wrong on the technical merits, say so plainly. If a framing is confused, flag it plainly. The operator's preference is for honest pushback over agreeable validation, even where the pushback is uncomfortable. Treat the operator as someone who can absorb sharp expert critique and act on it.

You are one of four agents reading this same document suite independently. Three of you (software developer; project manager; skeptic — your role) are stress-testing the proposal against the questions below. A fourth, separately, is surfacing what hasn't been asked. You will not see the others' assessments. A judge synthesises across all four outputs afterwards.

The proposal under review is a rebuild of an existing matched/promo betting tool, currently called BetHub v2, which has been running for months. The rebuild (v3) inherits the operational shape v2 produced and rebuilds the software around that shape with v2's accumulated failure modes designed out. The operator runs the operation solo. The four documents below describe what is being decided, the v3 data requirements, the architecture as currently designed, and the data layer (an existing UK VPS racing-data capture system called `capture.db`) that v3 will read from. Read them in the order presented; cross-references between them are spelled out where useful.

The work has progressed across many design sessions. One concern named by the operator, which you are asked to take seriously: long-running session-by-session evolution can produce documents that look coherent on first read but reveal patchwork drift on careful reading. You are explicitly invited to flag "this doesn't even cohere" if that is the honest read of the document suite, rather than feeling obliged to engage with the proposal on its own stated terms.

## Your role for this assessment

You are reading as a sharp skeptic with a strong record of finding the assumption a design is leaning on without admitting to itself, the framing that holds up on first read but strains on the second, and the load-bearing claim that nobody has actually argued for. Your lens is *where the design falls apart*: the assumption that has to be true for the design to work and that nobody has interrogated; the load-bearing premise underneath a decision that, if false, makes the decision wrong; the place where the framing relies on a sleight of hand the operator may not have noticed because they wrote the framing themselves. You are not a software developer (don't lead with integration-design critique or where the code will fail under load) and you are not a project manager (don't lead with sequencing or scope rightness). Your job is the skeptic's critique: what is the design relying on that is not visible in the design's own framing, and what would have to change about the world for the design to be wrong.

Five steering directives for how to do this work, named explicitly because the skeptic seat has its own failure mode:

1. **Substantive over rhetorical.** Skepticism that is rhetorical — sharp tone, dismissive framings, contrarian gestures, "this whole thing is overengineered" reflexes — is not what is wanted here. Skepticism that is substantive — naming a specific failure mode, the conditions under which it bites, what would have to be true for the design to break — is what is wanted. The first kind is a bad version of this seat. The second kind is the job.

2. **Specificity over volume.** If you find five places the design might fail, name the two where you can specify the failure clearly and skip the three where you can't. Five vague flags are worse than two specific ones. The judge synthesis that comes after this assessment can only act on specific findings; vague ones get dropped.

3. **Cite the documents.** Every critique points to which document, which section, which decision the failure mode lands on. A critique that does not cite is harder for the operator and the judge synthesis to act on than one that does.

4. **The "this looks right" path is real.** If your assessment in places amounts to "this looks roughly right, I don't see the failure mode here" — say that, plainly. The skeptic seat invites disagreement; that does not oblige you to manufacture some. The operator wants your honest read, not produced skepticism. Saying "this is sound" is a legitimate skeptic finding.

5. **Surface load-bearing assumptions.** Beyond failure-mode framing, name the assumptions the design is relying on. What would have to be true about soft-book scraping resistance, about operator workflow under burst conditions, about the rate of capture.db schema drift, about how AccountCare actually evolves once v3 is live, for the design to be right. The most useful skeptic finding is often "the design works iff X, and X is not argued for anywhere." That kind of finding is where this seat earns its keep.

## The documents

### Document 1 — Decision under review

[INLINE PASTE: decision_under_review.md]

### Document 2 — v3 data requirements

[INLINE PASTE: v3_data_requirements.md]

### Document 3 — Architecture (current)

[INLINE PASTE: architecture_current.md]

### Document 4 — Data layer (current)

[INLINE PASTE: data_layer_current.md]

## What you are asked to assess

The questions below are grouped into three sets. Sets 1 and 2 are the substantive questions. Set 3 is framing that shapes how you should approach Sets 1 and 2 — not standalone questions, but lenses.

### Set 1 — The four review questions from `v3_data_requirements.md` Section B.7

These are the spine of the stress-test. For each, the ask is the same: where does this break, under what conditions, and what does the failure look like?

**Question 1.1 — Bet schema simplification.** Whether the bet record should drop the inline market-context snapshot (DR-026's best back/lay price + size, total matched, snapshot timestamp) and the field-size captures (Slice 6's `field_size_at_bet_placement`, `field_size_at_settlement`) in favour of full cross-database resolution from `capture.db` at read time. If adopted, the bet record carries only identifiers (Betfair `market_id`, runner `selection_id`, placement timestamp) and v3-context fields (stake, odds, promo linkage, hedge state). If not adopted, the current direction (inline storage on the bet record) holds.

**Question 1.2 — Data-layer-first sequencing soundness.** Whether the data-layer-first sequencing (review and extend the data layer to v3 fit-for-purpose *before* v3 build begins, per DR-029) is the right structural protection given v3's actual risk profile. The current direction is described in Section 3 of the decision-under-review document.

**Question 1.3 — Data review scope rightness.** Whether the in-scope items (race-data fit-for-purpose verification, sports market data layer addition, periodic-only API pattern, settlement model, external analytics environmental scan, API contract versioning) and the out-of-scope items (analytics layer formalisation, account-isolation layer formalisation, Cloudflare-blocked book scraping) are correctly drawn for the data review. Sub-question: NZ thoroughbred / harness / greyhound coverage — verify Racing API NZ coverage and decide on inclusion.

**Question 1.4 — ~~Reserved, no longer in play.~~** This was originally a separate question on NZ inclusion; folded into 1.3 as a sub-question. Visible here so the numbering matches the source document. No response expected.

**Question 1.5 — Periodic-only API pattern with analytical bracketing.** Whether the periodic-only architecture (no on-demand fresh-now snapshot endpoint; analytical bracketing via surrounding-interval snapshots from `capture.db` at analysis time; cadence verification as a fallback path before on-demand is reconsidered) is the right structural commitment for the VPS data API contract and v3's `vps_client` interface. The bracketing argument is in the data-requirements document Section B.7 #5 and in the data-layer-current document Section 7.

#### Pairing weighting — Questions 1.1 and 1.5 together

The operator asks that 1.1 and 1.5 be weighed together as one simpler-vs-more-complex choice, not as two independent questions. Both depend on `capture.db` being rigorous; they differ primarily in *where* that rigour is leaned on. The leaner shape (drop inline storage on the bet, periodic-only API) leans on `capture.db` as the single source of race-side context. The more-data-rich shape (keep inline storage, periodic-only API still applies) adds a second copy on the bet record as cross-system insurance without removing the dependency on continuous capture. Per-question answers above stay separate so the technical detail is preserved; this paired weighting is where you weigh them as one structural commitment. Specifically: which shape is the right structural commitment, given that both depend on VPS rigour and differ in where that rigour is leaned on? Are there scenarios where the leaner shape's dependency on continuous capture rigour bites in ways the richer shape's redundancy would have absorbed — and if so, how probable are those scenarios?

### Set 2 — Two v3-stakes questions surfaced during Sessions 18–19 (data-layer-current document Section 8)

**Question 2.1 — Reachability and continuous-fitness discipline.** v3's two-database architecture (DR-027) and integration boundary discipline (DR-028) place a continuous-availability requirement on `capture.db` and its data API. v3 reads VPS on every bet log, on every settlement, in burst review. The graceful-degrade flag in DR-026 (`bf_snapshot_unavailable = true`) is the structural fallback. The empirical context, two surfaces: first, *reachability* — v2 has been operating normally for at least seven continuous days with the SSH tunnel down and no successful VPS calls in that window, with nobody noticing because v2 doesn't actually need the wired code paths in execution-mode operation; second, *population-state visibility* — the operator does not currently hold confident knowledge of which `capture.db` fields are reliably populated or whether documented cadence still holds in practice, because the data layer has had no real active consumer. v3 will be the first execution-time consumer that actually requires the tunnel up *and* requires the data inside `capture.db` to match what v3 thinks it is reading. The infrastructure to enforce continuous availability and continuous fitness — monitoring, auto-restart, alerting, escalation, ongoing fitness verification past the one-off DR-029 review — is not currently specified. Does this discipline need to be specified before v3 build, alongside the data-layer fit-for-purpose review? Or are graceful-degrade plus a one-off pre-build review sufficient?

**Question 2.2 — Operational live pricing, Betfair and soft-book.** A distinction surfaced during Session 19: v3's design has not currently distinguished between *analytical* data needs (post-hoc bracketing, modelling, calibration — served by `capture.db`) and *operational* data needs (sub-second live pricing in the burst window for in-the-moment decision-making — not served by `capture.db`, and not currently designed). The operational layer splits cleanly into two sub-cases:

- **2.2a — Operational Betfair live pricing.** v3 needs sub-second Betfair prices in the burst window. Betfair's Streaming API is designed for this. Should v3 specify a direct Streaming API connection from v3 (a third data surface alongside v3's own database and `capture.db`)? How does it interact with DR-026, DR-027, DR-028, and the periodic-only API pattern in 1.5?
- **2.2b — Operational soft-book live pricing.** v3's burst UI is intended to display soft-book prices alongside Betfair as a comparative tool and EV decision-support layer. Soft-books actively resist high-cadence scraping; frequency-blocking risk is real. Four plausible architectural responses (A in-scope build, B out-of-scope with staleness indicator, C on-demand per-burst-review, D third-party odds-feed vendor) are described in `data_layer_current.md` Section 5.4 — full trade-off detail lives there in the inline-pasted document and is the substantive context for this question; the four-option summary above is for orientation, not a substitute. Which response is structurally right, and is this question one that should be answered before v3 build or deferred?

**Question 2.3 — AccountCare-DB future-shape pushback.** This question is structurally different from 2.1 and 2.2: it asks you to argue against an operator premise rather than to failure-mode an architecture. Section 3 of the decision-under-review document flags AccountCare as embedded in v3's bet-data database day-one, with the operator's working hypothesis that whether AccountCare ever warrants its own database "can only be answered by using v3." You are invited to argue against this premise. If AccountCare's eventual own-database trajectory is more probable than the operator currently treats it as, DR-028's cross-DB integration discipline must scale to more than one boundary — which raises the stakes on getting it right under today's single-boundary load. If you don't think the trajectory is more probable than the operator treats it as, say so plainly and why; the ask is your honest read, not manufactured pushback.

## Output format

Write your assessment as plain prose under the headings below. No checklist-shape bullets within sections; engage substantively. Length: as long as needed to do the questions justice; tight is better than padded.

### 1. Coherence-of-framing assessment

Lead with this. Reading the four documents as a fresh outside reader, does the design cohere? Are there places where session-by-session evolution shows through as patchwork? Where does the framing strain? If you find the framing genuinely incoherent in load-bearing places, say so plainly and tell the operator which places — this is a legitimate finding, not a failure to engage.

### 2. Question 1.1 — Bet schema simplification

[Failure-mode response.]

### 3. Question 1.2 — Data-layer-first sequencing soundness

[Failure-mode response.]

### 4. Question 1.3 — Data review scope rightness

[Failure-mode response.]

### 5. Question 1.4 — ~~Reserved.~~

[No response expected.]

### 6. Question 1.5 — Periodic-only API pattern with analytical bracketing

[Failure-mode response.]

### 7. Paired weighting — 1.1 and 1.5 as one structural commitment

[Where you weigh the pairing as one simpler-vs-more-complex choice. Per the operator's pairing ask.]

### 8. Question 2.1 — Reachability and continuous-fitness discipline

[Failure-mode response.]

### 9. Question 2.2 — Operational live pricing

Sub-sections 9a (Betfair) and 9b (soft-book).

### 10. Question 2.3 — AccountCare-DB future-shape pushback

[Where you argue against the operator's "answered by using v3" premise if you think the trajectory is more probable than they treat it as. If you don't think it is, say so and why.]

### 11. Open questions you would want answered before finalising

Catch insights that don't fit any single question above. Things you noticed reading the suite that the operator should be aware of, that don't naturally land in the question structure. Keep this section honest — if you don't have any, say so; don't pad.

## A final note on tone

The operator has named "honest pushback over agreeable validation" as the explicit preference. If your assessment in places amounts to "this looks roughly right" — say that, plainly, without softening or hedging in the other direction. The point is not to manufacture criticism; it is to give the operator your honest read where the questions deserve sharp engagement and your honest read where they don't.
