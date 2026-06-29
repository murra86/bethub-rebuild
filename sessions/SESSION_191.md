# Session 191 — VPS supply-side review triaged; DR-029 governance
# cleanup (stale auto-settle clause flagged); placings-backfill
# brief locked + Code released

**Opened:** 2026-06-25 21:02 ACST
**Closed:** 2026-06-25 21:55 ACST
**Tool routing:** Claude Chat (VPS-review triage + operator grounding
+ governance cleanup + brief drafting). Code commissioned
out-of-session once: the placings-backfill brief locked + read-back
confirmed + released this session (execution carries to S192).
**Governing DRs:** DR-021 (Adelaide time), DR-033 (data-source roles
— central this session), DR-029 (amended this session), DR-027/028
(operational/analytical boundary).

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date` → 2026-06-25 21:02 ACST.
- Close: `TZ="Australia/Adelaide" date` → 2026-06-25 21:55 ACST.
- ~53 min wall-clock; well under the ~3h soft split trigger.
  Same-workday open (~20 min after S190 close). No day rollover.

## Pre-flight checks (open ritual)

Clean open. current_state, SESSION_190, and v3_build_picture all
carried the matching 2026-06-25 20:42 ACST S190-close stamp (no
drift). Root folder clean (the extra `.md` files all live reference
artefacts, no phantoms). `.close_out_backups/` held exactly the
expected `SESSION_191_opening_prompt.md`. Directory listing settled
the S191 routing immediately: `vps_supply_review.md` was present —
the operator ran the VPS Code session between sessions — so the
primary was GO, not the frontend fallback.

## Session shape

A triage-then-commission session, with an operator-grounding
detour in the middle that paid off in a governance catch. Opened
same-workday on the S190 forward routing — auto-triage Code's
`vps_supply_review.md`. Triaged the review clean and produced the
operator digest. The operator then ran two grounding checks before
committing the fix: (1) a plain-language walkthrough of what the VPS
captures and what each field serves day-to-day, to confirm the work
matches the operation; (2) a memory-check on whether placings
auto-settle was deferred — which surfaced a stale DR-029 clause. The
governance was cleaned up (DR-029 S191 amendment), then the
placings-backfill brief was drafted, locked, read-back-confirmed,
and released to Code. Closed on a clean forward route: Code runs the
backfill out-of-session; S192 auto-triages the report.

## What was delivered

1. **VPS supply-side review — TRIAGED + digest produced.**
   `vps_supply_review.md` read in full. Verdict: the supply side is
   sound for what it captures — all seven `vps_client` reads run
   against live data, Betfair freshness ~2.5 min, and the Log Past
   Bet lookup (date→venue→race→market+runners) proven end-to-end on
   a real race. Three gaps surfaced, one operational: placings (the
   1st–4th ordinal) ~0.1% since May — the S174 gap, now quantified
   across the fade curve. Two usability: the `resolve_race`
   empty-runner edge (12.5% of stamped races) and harness/greyhound
   mislabelled as thoroughbred (~14%). Plus a coverage bound (only
   ~27% of recent races carry the Betfair stamp v3 joins on) and the
   brief's "~90 min ahead" timestamp oddity RESOLVED as a false
   alarm (it read market-start, not capture-time). Operator digest
   delivered in plain gambling terms, leading with the placings
   call.

2. **VPS capture walkthrough — operator grounding / fit-check.**
   Plain-language outline of the three capture sources and what each
   serves: Betfair (live — win/lose, BSP, price movement, identity);
   the Racing API (paid enrichment — finishing order, margins, form,
   pedigree, career stats); the soft-book scraper (captured but NOT
   read by v3 yet — parked for the Strategy 2 price tooling). Landed
   the punchline: most capture is future-analytical investment; the
   only daily-operational fields are win/lose (fed) and the placing
   (broken). Operator confirmed fit and restated the priority —
   broad-scope cheap-to-capture / expensive-to-reconstruct data for
   future and not-yet-conceived strategies.

3. **GOVERNANCE EVENT — DR-029 amended (S191).** The operator's
   recollection check (was placings auto-settle deferred?) was
   grounded against `decisions.md` + `data_sources.md`: CONFIRMED.
   DR-033 locks place/ordinal settlement (Safety Net 2nd–4th) as a
   manual operator flag; auto-settle is deferred, not declined,
   gated on (a) free bets being layable in-tool and (b) a DR-027/028
   boundary call. Grounding surfaced a STALE DR-029 clause — two
   bullets in DR-029's "what fit for purpose means concretely" list
   still said auto-settlement reads VPS race results as canonical
   (the pre-S174 design). Appended a dated **Amendment 2026-06-25
   (Session 191)** to DR-029 (immutability-respecting — locked
   bullets untouched, house-style matched against DR-026/027/030
   amendments) marking both clauses superseded by DR-033, with the
   exact superseded phrases quoted so a future read or grep lands on
   the correction. Self-correction logged: an earlier S191 framing
   called the captured placing "the single most operationally
   load-bearing thing day-to-day" — corrected, since settlement is
   manual, the placing's value is analytical capture + future
   auto-settle readiness, not a daily-ops dependency.

4. **Placings-backfill brief — DRAFTED + LOCKED + Code read-back
   confirmed + RELEASED.** `placings_backfill_brief.md` (rebuild
   root, 104 lines, 11 sections). A surgical forward fix + bounded
   recovery on the VPS capture pipeline: stop the nightly Racing-API
   sync skipping dates whose results publish after first run
   (recommended a trailing 14-day re-pull window; named the
   stamp-when-results-present alternative for Code to choose if
   cleaner), then backfill the gap (2026-03-01 → 2026-06-25, all
   races, resumable, partial-is-a-finding). Capture-side / analytical
   only; auto-settle named-and-excluded (§9); bet-safety clean by
   construction. Four operator-relevant calls surfaced pre-draft and
   accepted (one job both halves; backfill all races not bet-relevant;
   capture-side-only safety wall; partial backfill is fine). Code's
   read-and-confirm gate came back FAITHFUL — every element restated
   accurately, and the bet-safety reasoning came back grounded (not
   parroted: settlement is Betfair-only and never reads VPS placings,
   DR-027/028 boundary isolates the analytical write). RELEASED with
   the go-line. Code runs out-of-session.

## Standing-instruction adherence check

- **Cat 1 brevity / decision-maker framing** — held. Led with the
  call each turn; flagged "this deserves a little detail" before the
  VPS digest and the capture walkthrough.
- **Cat 1 plain language / no jargon** — held. The digest and
  walkthrough used real-world gambling terms (BSP = "the price when
  it jumped"; finish ordinal = "did it run 2nd/3rd/4th").
- **Cat 1 silent open/close ritual** — held. Open produced one
  combined orientation block; close ran silent to the one-line
  confirmation + opening prompt.
- **Cat 1 don't-surface-dev-lead-calls-by-default** — held. Surfaced
  the four operator-relevant brief calls in plain terms; held the
  fix-mechanism / single-session technical detail as Claude's.
- **Cat 2 brief-drafting skill** — held. Calls surfaced pre-draft for
  cheap redirect; brief drafted end-to-end, verified on write
  (line/byte/sha); Code prompt + read-and-confirm gate provided
  unprompted; read-back triaged before release.
- **Cat 2 always-provide-Code-prompt** — held. Provided at hand-off +
  the release go-line after the faithful read-back.
- **Cat 3 empirical verification before editing governance** — held.
  Re-read `decisions.md` (DR-033 + the DR-029 region) and
  `data_sources.md` from disk before the amendment; grep-located the
  exact stale clauses; brief anchors grounded by the fresh VPS review.
- **Cat 3 create_file banned / verify writes** — held. All writes via
  Desktop Commander; brief + amendment verified on write.
- **Cat 4 governance discipline / DR immutability** — held. DR-029
  amended via an appended dated note; locked bullets untouched;
  house style matched.
- **Cat 5 make-the-call** — held. Made the brief's software calls
  (fix mechanism, breadth, single-session handling) and surfaced
  them; self-corrected the placing-criticality overstatement rather
  than letting it stand.
- **Bet-safety hard rule — CLEAN.** No code touched in Chat. The
  brief is capture-side / analytical by construction; settlement and
  placement untouched. No contact with any money path.

## Open items

Pointer-only — full detail in `current_state.md`.

**New / promoted for S192:**
- Triage Code's `placings_backfill_report.md` (S192 primary, auto on
  open).

**Carried to S192:**
- Consolidated frontend fix brief (the S189 sweep polish dump —
  independent parallel start; the natural in-session piece after the
  placings triage).
- Launcher brief (capture-data provisioning + carried F9/F10/F12 +
  rebuild-if-source-newer).
- Settlement-worker brief — standalone (post-VPS-triage queue).
- Promo-seed item — standalone, small.
- W16 cutover scoping.
- Parking-lot (unchanged).

## Open items out (closed this session)

- **VPS supply-side review triage + operator digest (S191 primary)**
  — DONE. Triaged clean; supply side sound; three gaps surfaced
  (one operational placings, two usability); digest delivered. ✅
- **VPS capture walkthrough (operator grounding / fit-check)** — DONE.
  Three sources + serving outlined; operator confirmed fit and
  restated the broad-scope priority. ✅
- **DR-029 governance cleanup** — DONE. Stale auto-settle-reads-VPS
  clause flagged via a dated DR-029 amendment pointing to DR-033. ✅
- **Placings-backfill brief** — DRAFTED + LOCKED + read-back
  confirmed + RELEASED. ✅ (Execution + triage carry to S192.)

## Session close state

- `sessions/SESSION_191.md` — this record.
- `current_state.md` — rotated to S191 outcomes; stamp 21:55.
- `v3_build_picture.md` — header + interface-refinement row updated
  (VPS review triaged; placings brief locked + released); stamp 21:55.
- `decisions.md` — **DR-029 amended (S191 governance event)**; needs
  KB re-upload (now alongside the carried DR-032/S180 staleness).
- `placings_backfill_brief.md` — LOCKED (104 lines).
- `standing_instructions.md` — untouched (no new instruction this
  session).
- `.close_out_backups/` — stale S191 prompt removed; S192 opening
  prompt written.

## Pending operator-side actions

- **Run the placings-backfill Code session** — paste the released
  go-line; Code executes `placings_backfill_brief.md` end-to-end and
  produces `placings_backfill_report.md`. Run from the logged-in Mac
  session (ssh-agent must be available — the VPS key is
  passphrase-protected).
- **Re-upload `decisions.md`** to the bethub-rebuild Project KB — now
  carries BOTH the S191 DR-029 amendment AND the carried DR-032/S180
  amendment. KB copy stale.
- **Re-upload `standing_instructions.md`** to the Project KB
  (carryover — includes the S189 §4 live-integration rule).
- **Manage any live unmatched lays (S164)** — real exposure.
- **v2:** jump-start-only on request (to retirement).

## Forward routing (CONFIRMED with operator)

The operator confirmed: "close. triage to open next session." S192
**auto-triages** `placings_backfill_report.md` straight off the open
ritual (no confirmation gate, consistent with the established
pattern). On a clean triage → operator digest (gap recovered?
forward-fix mechanism sound? any leftover date range?) → route any
leftover backfill as a short follow-up run → then back to the
pre-cutover queue: consolidated frontend fix brief (independent
parallel start) / launcher capture-data provisioning →
settlement-worker brief → promo-seed item → W16 cutover. The operator
runs the placings Code session between S191 and S192.
