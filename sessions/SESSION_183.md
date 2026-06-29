# Session 183 — Build 2 triaged (bet-safe, logic proven); F2 account-id format defect surfaced as the live-credit blocker; account-id normalization fix brief drafted, locked + handed to Code, gate released

**Opened:** 2026-06-23 22:30 ACST
**Closed:** 2026-06-23 23:36 ACST
**Duration:** ~1h6m, single calendar day. Same-workday continuation of
S182 (closed 22:01 ACST; S183 opened 22:30, 29 min later).
**Tool routing:** Claude Chat (Build 2 report triage + F2 grounding +
account-id normalization brief drafting + Code read-and-confirm triage) +
Desktop Commander (governance reads/writes; ~6 v3 read-only code
groundings — `accounts.py` id generation, `domain/promos` + `promo_*`
spine field typing, `fb_deployment.py` deploy-path id copy,
`store/repositories/bets.py` + `domain/bets`/`domain/accounts` operational
format, the spine tests' seed format; the brief writes). No DB access.
One out-of-session Code action released this session (the F2 fix — runs
out-of-session; triage routed to S184).
**Governing DRs invoked:** DR-021 (anchors). DR-032 (promo link, amended
S180 — **unaffected** by the fix; the credit's promo reference is
unchanged). DR-030 (module boundaries — the fix sits within
`domain/promos` + `workflows/promos`, no boundary crossed). DR-027/028
**not triggered** (single-DB; no cross-database read or write).

---

## Anchor

- Open: `2026-06-23 22:30 ACST` (session-open ritual; same-workday
  continuation of S182's 22:01 close).
- Close: `TZ="Australia/Adelaide" date` → `2026-06-23 23:36 ACST`.

## Pre-flight checks

Open ritual ran clean: drift-check passed (current_state ↔ SESSION_182 ↔
v3_build_picture all matched the 22:01 S182 close); `.close_out_backups/`
held only the S183 opening prompt; rebuild root + `interface_triage/`
clean (no phantom files); the Build 2 report was present
(`promo_attach_build2_report.md` — Code had run). Required reads completed
in order (current_state, standing_instructions in full, project_context,
SESSION_182, plus the S183 triage target — the Build 2 report). Per the
operator's S182 close instruction, S183's opening action was the Build 2
triage run **automatically on open, no confirmation prompt** — honoured.
Same-workday tight recap; build picture + open-items delta folded into the
recap rather than rendered separately (operator in flow, 29-min gap).

## Session shape

Three strands. First, **triaged Code's Build 2 build report**
(`promo_attach_build2_report.md`, 322 lines) automatically on open,
inventory-first: clean on the bet-safety gate (settlement byte-identical,
SHA `9e07a75d…`, off the settlement path), the logic proven (credit-once,
idempotency, pool-fill, cycle inheritance all tested; Python 1166→1180
+14, 0 regressions) — **but** the report's headline finding **F2** is a
real blocker: the promo-event spine stores account/book reference ids in a
different text format than the operational store, so a credit (or deploy)
against a real router-created account fails its FK check. Surfaced F2 to
the operator in plain language; ratified F1 (adapter promo-reference
accept-path) + F3 (feed promo-serial exposure) silently as Claude's
territory.

Second, the operator pushed on whether F2 (and the pattern of findings)
means v3 is being band-aided rather than solidly fixed. Gave the
band-aid-vs-structural fork honestly, then **grounded F2 in the live
code** to determine the structural fix: confirmed the operational store
(`accounts.py` generates `uuid4().hex`; `bets.py` + `domain/bets` +
`domain/accounts` all store these ids as plain hex TEXT) is internally
consistent, and the promo-event spine is the **lone divergent layer**
(types the three reference fields as `UUID`, serializes to dashed). The
spine's tests seed dashed `str(uuid4())`, which is why F2 hid behind green
tests. The deploy path shares the identical latent risk (copies the ids
straight from the credit event).

Third, the **brief-drafting skill fired** for the F2 fix. Grounded the
exact anchors (domain field lines, derivations/adapter signatures, the
adapter write/read boundary, the credit-write wrap, the spine-owned ids
that must stay UUID), drafted the brief in numbered sections, locked it,
and released Code after a faithful read-and-confirm gate (Code verified
every anchor against the live code, returned a more-complete do-not-touch
list than the brief named, and caught a line-537 imprecision — the brief
pointed the write-side at a line that's actually in a validation check,
harmless once the field is str; Code has the real save site at 702–708).

## What was delivered

1. **Build 2 build report triaged (auto on open).**
   `promo_attach_build2_report.md` (322 lines) inventory-triaged. **Bet
   safety clean** — settlement byte-identical (`9e07a75d…`), the credit is
   a pure promo-event write off the settlement path, no manual-resolve /
   provisional contact. **Logic proven** — a settled-lost Safety Net
   qualifier with a promo credits the free bet into the pool exactly once
   (amount correct, pool fills), a second click is idempotent, the deployed
   free bet inherits its qualifier's cycle; Python 1166→1180 (+14), vitest
   109→110, tsc clean, HEAD/dirty-tree unchanged. **Six §5 pieces all
   built.** F1 (adapter `_require_promo_reference` accept-path for the
   single-level serial — DR-032-faithful, no validator relax) + F3
   (`promo_template_id` exposed on the BetLog feed for the client gate;
   server gate authoritative) both ratified silently as Claude's territory.

2. **F2 surfaced as the live-credit blocker + grounded structurally.** The
   promo-event spine stores `account_id` / `book_id` / `account_at_book_id`
   as `UUID`-normalized-to-dashed; the operational store stores them as
   dashless `uuid4().hex` TEXT. A credit/deploy against a real
   router-created account raises `FOREIGN KEY constraint failed` (proven
   twice in the Build 2 session). The spine is the lone divergent layer;
   the deploy path shares the identical latent risk; the spine's tests seed
   dashed, so F2 hid behind green tests. Operator concern addressed
   honestly: this is a structural fix (conform the one divergent layer; no
   live-data migration), and the test-format migration is the anti-
   recurrence mechanism.

3. **Account-id normalization fix brief drafted, locked + handed to Code.**
   `interface_triage/account_id_normalization_brief.md` (323 lines, 11
   sections). Retypes the **three operational-store reference fields**
   (`account_id` / `book_id` / `account_at_book_id`) from `UUID` to `str`
   through one layer — domain types (`domain/promos` 664–666, 776 + sweep),
   derivations + adapter signatures, the adapter write/read boundary
   (pass-through, no normalization), the credit-write wrap
   (`fb_credit.py` 184–186), deploy-path confirmation — and migrates the
   spine tests to the production hex format plus adds an FK regression test
   (a credit against a hex `accounts_at_book` row with `foreign_keys = ON`
   that proves the write succeeds + pool fills). **Spine-owned ids stay
   UUID** (event_id, promo_id, promo_template_id, triggering_bet_id,
   triggering_promo_instance_id, every `*_event_id`, correlation_id) — the
   surgical boundary, enforced as a §9 hard limit. Hard limits: settlement
   byte-identical, no operational-store change, no schema change, no bet-id
   convention change, named anchors only, dirty-tree discipline. Locked +
   stamped 2026-06-23 (S183), operator-approved.

4. **Code read-and-confirm gate triaged + released.** Code verified every
   anchor against the live code, returned a more-complete do-not-touch list
   than the brief named, and caught the line-537 imprecision (a validation
   check, not the row-save; harmless once the field is str; real save site
   702–708 confirmed). Faithful — released with the build prompt. Code
   builds out-of-session; report routed to S184.

## Standing-instruction adherence check

- **DR-021 anchoring (Cat 2):** open 22:30 + close 23:36 ACST. ✓
- **Silent session-open (Cat 1):** steps 1–5 silent; same-workday tight
  recap; auto-triage on open per operator (no confirm); build picture +
  open-items delta folded into the recap (in-flow, 29-min gap). ✓
- **Inventory-first on long reports (Cat 1):** the Build 2 report triaged
  inventory-first; classified by impact; surfaced the bet-safety verdict +
  F2 as the one operator-facing blocker, handled F1/F3 silently. ✓
- **Plain-language / decision-maker framing (Cat 1):** F2 and the
  band-aid-vs-structural question answered in real-world terms (account-id
  "format mismatch", "hiding behind green tests"), no schema field names in
  operator-facing text. ✓
- **Escalate-to-detail-when-warranted (Cat 1):** flagged the
  band-aid-vs-structural fork as deserving detail before delivering it. ✓
- **Verify empirically / ground "already built" (Cat 3, Cat 4 S178):** F2's
  structural fix grounded against the live code (accounts.py, the spine
  typing, the deploy-path copy, the bets store, the test seeds) before
  drafting — the brief's anchors are grounded, not assumed. ✓
- **Make-the-call / don't punt (Cat 5):** the canonical-format direction
  (conform the spine, not the operational store), the retype-to-str
  mechanism, the surgical boundary, and the F1/F3 ratifications all made as
  dev-lead calls; only the operational ones (the live-credit blocker, the
  sequencing call) surfaced. ✓
- **Don't surface dev-lead calls by default (Cat 1, S163):** hand-off kept
  to the structural-fix guarantees + the one sequencing call; F1/F3 + the
  mechanism noted as ratified, not enumerated for review. ✓
- **Brief-drafting skill fired (Cat 2):** ran end-to-end — job named,
  pre-flight grounding, surgical-fix spine, hard limits, output spec, Code
  prompt with read-and-confirm gate. ✓
- **Always provide the Code prompt at hand-off (Cat 2, S163):** the
  read-and-confirm prompt provided at lock + the release prompt at
  gate-clear, both unprompted. ✓
- **Pre-execution risk advisory + chunked writes (Cat 3, S126):** the brief
  + this record written in ≤30-line chunks (no DC timeout this session). ✓
- **`create_file` banned (Cat 3):** all writes via
  `Desktop Commander:write_file` / `edit_block`. ✓

## Open items

Pointer-only — full live list in `current_state.md`.

## Open items out (closed / resolved S183)

- **Triage the Build 2 build report** — DONE; bet-safe + logic proven;
  surfaced F2 as the blocker. ✅
- **Band-aid-vs-structural concern** — ADDRESSED; F2 fix scoped as a
  structural conform-the-divergent-layer fix, no live-data migration,
  test-format migration as the anti-recurrence guard. ✅
- **Draft the account-id normalization (F2) fix brief** — DONE; locked +
  handed to Code. ✅
- **F2 fix read-and-confirm gate** — DONE; faithful, released. ✅

## New items in (S183)

- **Triage the account-id normalization (F2) fix report** — S184 primary
  (once the operator runs the Code session). On a clean triage — settlement
  byte-identical, the FK-failure-now-passes proof, deploy path confirmed,
  0 regressions — the **promo-on-bet + credit-in arc is complete** and live
  crediting works against real accounts.

## Session close state

- **Rebuild root + `interface_triage/`:** clean, no phantom files.
- **`interface_triage/account_id_normalization_brief.md`:** written (323
  lines), LOCKED + stamped 2026-06-23 (S183), operator-approved.
- **`interface_triage/account_id_normalization_report.md`:** not yet
  present (Code runs out-of-session) — S184 triage target.
- **`current_state.md`:** rotated to S183 close (23:36 ACST).
- **`v3_build_picture.md`:** interface-refinement stream next-milestone
  advanced (S183: Build 2 triaged bet-safe + logic-proven; F2 surfaced as
  the live-credit blocker; account-id normalization fix brief locked +
  handed + gate released; S184 triages the report); timestamp bumped.
- **`standing_instructions.md`:** not edited (no new instruction surfaced).
  S178's + S180's pending KB re-uploads still stand.
- **`decisions.md`:** not edited this session (DR-032 amendment was S180;
  its Project-KB re-upload remains pending).
- **`.close_out_backups/`:** `SESSION_184_opening_prompt.md` written;
  stale `SESSION_183_opening_prompt.md` removed.

## Forward routing (confirmed with operator)

Operator confirmed close after releasing Code on the F2 fix (chose to
close rather than line up the launcher brief this session). **S184's
opening action is to triage Code's account-id normalization fix report**
(`account_id_normalization_report.md`) once the operator has run the Code
session. Inventory pass; confirm the bet-safety gate (settlement SHA
byte-identical); confirm the F2 reproduction now passes (a credit against a
real hex-format account succeeds, the pool fills); confirm the deploy path
writes against a hex account without the FK failure; confirm 0 regressions;
surface any findings. **On a clean triage the promo-on-bet + credit-in arc
is complete** — live crediting works against real accounts.

Then the run-up to cutover: the **pre-cutover live-validation sweep**
(operator-run, manual — register a real account, log a real qualifier,
credit + deploy + settle a real free bet through the launched app, to
flush any other latent seam in a controlled pass), the **launcher brief**
(F9/F10 + F12 + rebuild-if-source-newer; independent of the F2 fix — can
run parallel or after, operator's routing call), then **W16 cutover
scoping**. The Racing-API placings backfill remains its own parallel brief
(not a blocker). Forward routing confirmed.
