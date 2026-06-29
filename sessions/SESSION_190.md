# Session 190 — workflow-integration audit triaged;
# VPS supply-side review brief locked + Code released;
# two new pre-cutover gaps surfaced

**Opened:** 2026-06-25 18:40 ACST
**Closed:** 2026-06-25 20:42 ACST
**Tool routing:** Claude Chat (triage + brief drafting + VPS
reachability diagnosis + governance). Code commissioned
out-of-session twice: the S189 workflow-integration audit (report
triaged this session) and the VPS supply-side review (brief locked
+ Code read-back confirmed + released this session).
**Governing DRs:** DR-021 (Adelaide time), DR-027/028 (two-DB
operational/analytical line + single integration boundary),
DR-033 (data-source roles), DR-026 (at-log snapshot).

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date` → 2026-06-25 18:40 ACST.
- Close: `TZ="Australia/Adelaide" date` → 2026-06-25 20:42 ACST.
- ~2h wall-clock; under the ~3h soft split trigger. Same-workday
  open (~24 min after S189 close).

## Pre-flight checks (open ritual)

Clean open. current_state, SESSION_189, and v3_build_picture all
carried the matching 2026-06-25 18:16 ACST S189-close stamp (no
drift). Root folder clean; `.close_out_backups/` held exactly the
expected `SESSION_190_opening_prompt.md` (Phase-2 carry).
Same-workday tight recap delivered; build picture rendered (state
moved at S189 close); open-items delta skipped (no delta vs the
S189-close snapshot).

## Session shape

A triage-then-commission session. Opened same-workday on the S189
forward routing — triage Code's `workflow_integration_audit.md`
(which the operator ran between sessions; report landed 18:43).
The triage produced the operator digest and confirmed the audit's
known-answer calibration. The audit surfaced two genuinely new
pre-cutover gaps beyond Log Past Bet, which the operator routed as
their own standalone items (Claude's dev-lead call, operator-
endorsed). The session then moved to the next queued brief — the
VPS supply-side review — grounded the demand contract, drafted +
locked the brief, diagnosed a VPS-access wrinkle live, confirmed
the box healthy, confirmed Code's read-back faithful, and released
Code. Closed on a clean forward route: Code runs the VPS review
out-of-session; S191 auto-triages the report on open.

## What was delivered

1. **Workflow-integration audit — TRIAGED + digest produced.**
   `workflow_integration_audit.md` read in full. Verdict: clean,
   read-only, map untouched, and the locked known-answer check
   PASSED — Log Past Bet independently re-derived as
   implemented-not-live {unprovisioned} (and demonstrated live,
   HTTP 500 on the lookup). Operator digest delivered as the live
   picture: Betfair reads live-proven; five write paths
   built+provisioned-but-unproven (one live pass lifts them);
   Log Past Bet blocked; auto-settlement not-wired; promo
   catalogue empty live.

2. **Two new pre-cutover gaps surfaced (audit findings).**
   (a) **Auto-settlement has no live runner** — `run_settlement_
   pass` exists + tested but nothing calls it (no worker / cron /
   endpoint), so cycle-settlement automation is dark and the
   manual PROVISIONAL resolve queue never gets fed. (b) **Promo
   catalogue empty live** — the whole promo-on-bet machinery is
   wired but no promo rows are seeded in the live DB, so the
   picker / EV promo-modes / credit gate have nothing to point
   at (data-seeding gap, not broken code). Plus context finding:
   the entire analytical cross-DB read surface is dormant on the
   demand side (only the race-lookup is wired). Drift items D1–D5
   noted in the audit report.

3. **Routing decision — both new gaps kept as standalone items**
   (operator delegated the call; Claude's dev-lead recommendation
   taken). Settlement-worker → its own brief (fires on the
   highest-risk surface — real money + FB credits; the caller is
   where double-fire bugs live, so it earns its own bet-safety
   framing; settlement logic itself untouched). Promo-seed → its
   own small item (additive write to the live DB; carries its own
   additive/settlement-untouched/idempotent framing; kept off the
   launcher to keep that brief lean). Neither depends on the VPS
   review (both read Betfair / the operational store). Pre-cutover
   queue re-ordered: VPS review → frontend fix brief (parallel) →
   settlement-worker brief → promo-seed item → launcher brief →
   W16 cutover.

4. **VPS supply-side review brief — DRAFTED + LOCKED + Code
   read-back confirmed + RELEASED.** `vps_supply_review_brief.md`
   (rebuild root, 174 lines, sha `da2ff055`). Grounded the demand
   contract first (architecture.md §A.8/§A.9 cross-DB read tables;
   `bethub-v3/contracts/vps_client_contract.md`; the eight
   implemented `vps_client` read methods; `data_sources.md`). A
   read-only single-session Code review that, for each of the
   eight `vps_client` reads, checks the live capture.db holds that
   data in the shape the client expects, fresh + complete enough
   to wire against — verdict per read (fit / fit-with-gap /
   not-fit). Two tiers: near-term DEEP (race lookup, finish
   results, race classification — Log Past Bet + auto-settlement
   feeds), analytical LIGHT (runner detail, BSP, price curve,
   identity resolution). Plus the finish-position gap QUANTIFIED
   (S174 nightly one-shot-sync bug — verify-only) and a capture-
   liveness section. Output: `vps_supply_review.md`. Code's
   read-back triaged faithful (job, §5 tiering, all §9 hard
   limits, §4 Step-0 SSH stop gate, §8 output spec, §3 pre-reads-
   first) and RELEASED with the go line.

   **Claude's calls baked into the brief (operator-delegated):**
   scope = all eight reads tiered; the placings gap is quantify-
   only (the actual backfill + nightly-sync FIX stays its own
   parallel brief, named-and-excluded in §9).

5. **VPS reachability diagnosed live (access wrinkle resolved).**
   The box is UP and capturing (`/health` via the live tunnel:
   collector active, capture.db present, bookmaker scrape ~36 min
   old). Fresh SSH from the Chat tool path failed publickey — root
   cause: the key (`~/.ssh/id_ed25519`) is passphrase-protected
   and only usable through the operator's unlocked ssh-agent,
   which the spawned shell can't see. NOT a server-side lockout.
   Confirmed by borrowing the live agent socket: SSH shell +
   `mode=ro` capture.db read both work. Operator ran `ssh-copy-id`
   (key already installed). Brief §4 updated to carry the access
   reality: run the Code session from the logged-in Mac session
   (agent available); `-o ClearAllForwardings=yes` to silence the
   harmless port-8400 collision with the live tunnel. One liveness
   oddity folded into the brief: the `/health` Betfair stamp read
   ~90 min ahead of wall-clock — likely market-start time not
   capture time; the review resolves the semantics.

## Standing-instruction adherence check

- **Cat 1 brevity / decision-maker framing** — held. Led with the
  call each turn; flagged "this deserves a little detail" before
  the longer VPS-access explanation.
- **Cat 1 plain language / no jargon** — held. The digest framed
  the live picture in operator terms ("the dropdown is empty",
  "the tool isn't watching your cycles close"); the SSH wrinkle
  explained as "my shell can't see your unlocked key".
- **Cat 1 silent open/close ritual** — held. Open ritual produced
  one combined orientation block; close ran silent to the one-
  line confirmation + opening prompt.
- **Cat 1 don't-surface-dev-lead-calls-by-default** — held. On the
  VPS brief hand-off, surfaced only the two operator-relevant
  calls (scope breadth, placings-gap quantify-only) and the three
  worth-a-glance items (SSH stop gate, mode=ro, timestamp oddity);
  did not enumerate consequence-free dev-lead detail.
- **Cat 2 brief-drafting skill** — held. Demand contract grounded
  before drafting (Step 2); inspection/measurement shape (S28/S33
  precedent); brief drafted end-to-end, verified on write
  (line/byte/sha), Code prompt + read-and-confirm gate provided
  unprompted; read-back triaged before release.
- **Cat 2 always-provide-Code-prompt** — held. Provided unprompted
  at lock; provided the release line after the faithful read-back.
- **Cat 3 empirical verification** — held throughout. Every claim
  about VPS state (box up, capture live, SSH auth cause, capture.db
  readability) came from live Desktop Commander probes, not memory.
  Demand contract re-read from disk before drafting.
- **Cat 3 create_file banned / verify writes** — held. All writes
  via Desktop Commander; brief + record verified on write.
- **Cat 3 never-copy-DB** — carried into the brief as a §9 hard
  limit (capture.db is a live WAL file; mode=ro, query in place).
- **Cat 4 ground "already built" (S178)** — exercised: grounded the
  `vps_client` surface against live code and found it more built
  than the audit implied (eight read methods), which shaped the
  brief's all-eight scope.
- **Cat 4 classify-done-by-live-integration (S189)** — exercised:
  the digest reported each part of the tool by live-integration
  bucket, not green tests.
- **Cat 5 make-the-call** — held. Took the operator-delegated calls
  (scope breadth; placings quantify-only; standalone-items routing)
  and stated each in one line with reasoning, rather than punting.
- **Bet-safety hard rule — CLEAN.** No code touched in Chat. The
  VPS review is read-only by construction; settlement / placement
  untouched. No contact with live money paths.

## Open items

Pointer-only — full detail in `current_state.md`.

**New / promoted for S191:**
- Triage Code's `vps_supply_review.md` (S191 primary, auto on open).
- Settlement-worker brief — new standalone (post-VPS-triage queue).
- Promo-seed item — new standalone, small.

**Carried:** consolidated frontend fix brief (the S189 sweep polish
dump — independent parallel start); launcher brief (capture-data
provisioning + carried F9/F10/F12 + rebuild-if-source-newer);
Racing-API placings backfill + nightly-sync fix (own brief, now
informed by the VPS review); W16 cutover scoping; the full
parking-lot (unchanged).

## Open items out (closed this session)

- **Workflow-integration audit triage (S190 primary)** — DONE.
  Triaged clean; known-answer check confirmed; operator digest
  delivered. ✅
- **VPS supply-side review brief** — DRAFTED + LOCKED + Code
  read-back confirmed + RELEASED. ✅ (Execution + triage carry to
  S191.)
- **VPS reachability check** — DONE. Box up, capture live, SSH
  cause diagnosed (agent, not lockout), access reality folded into
  the brief. ✅

## Session close state

- `sessions/SESSION_190.md` — this record.
- `current_state.md` — rotated to S190 outcomes; stamp 20:42.
- `v3_build_picture.md` — header + interface-refinement row updated
  (audit triaged; two new gaps; VPS review brief locked + released);
  stamp 20:42.
- `vps_supply_review_brief.md` — LOCKED (174 lines, sha `da2ff055`).
- `workflow_integration_audit.md` — Code's audit report (read this
  session; retained as reference).
- `standing_instructions.md` — untouched (no new instruction this
  session).
- `.close_out_backups/` — stale S190 prompt removed; S191 opening
  prompt written.

## Pending operator-side actions

- **Run the VPS supply-side review Code session** — paste the
  released go-line; Code executes `vps_supply_review_brief.md`
  end-to-end read-only and produces `vps_supply_review.md`. Run
  from the logged-in Mac session (ssh-agent must be available).
- **Re-upload `standing_instructions.md`** to the bethub-rebuild
  Project KB (carryover — includes the S189 §4 live-integration
  rule).
- **Re-upload `decisions.md`** to the Project KB (DR-032 amended
  S180; KB copy stale — carryover).
- Manage any live unmatched lays (S164). v2 jump-start-only on
  request.

## Forward routing (CONFIRMED with operator)

The operator confirmed: close S190 now; S191 **auto-triages**
`vps_supply_review.md` straight off the open ritual with **no
confirmation gate** (operator directive this session). On a clean
triage → produce the operator digest → route the placings backfill
+ nightly-sync fix as its own Code brief (now informed by the
review) → feed the launcher brief's capture-data provisioning with
the confirmed path/shape → settlement-worker brief → promo-seed
item. The consolidated frontend fix brief is the independent
parallel start if the VPS report has not landed when S191 opens.
The operator runs the VPS review Code session between S190 and S191.
