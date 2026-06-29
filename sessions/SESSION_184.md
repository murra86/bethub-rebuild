# Session 184 — F2 fix triage → band-aid call → account-ref surface review brief

**Opened:** 2026-06-24 ~13:58 ACST (recovered mid-session after a
dropped connection; the lost chat had run the S184 open ritual and
the F2 triage, then died on the band-aid question).
**Closed:** 2026-06-24 14:46 ACST.
**Tool routing:** Claude Chat (triage + dev-lead calls + brief
drafting). Claude Code commissioned out-of-session (review brief +
the earlier F2 fix). Desktop Commander throughout.
**Governing DRs:** DR-030 (module boundary — the altitude tension),
DR-027/028 (two-database), DR-021 (Adelaide time), settlement
byte-identity.

---

## Anchor

- Close anchor: `TZ="Australia/Adelaide" date` → **2026-06-24 14:46
  ACST**.
- Open was recovered from a dropped-connection transcript; the
  literal open-ritual timestamp (13:58 ACST) carried in the pasted
  chat, not re-run this session.

## Session shape

A recovery-and-continue session. The connection dropped in the
original S184 after Code's F2 fix report had been triaged and the
operator had asked the dev-lead question: *is the proposed
display-side fix a band-aid, given it's the same root cause as F2?*
This session picked up at exactly that question, grounded it in the
live v3 code, resolved the approach, then commissioned a read-only
review brief before any fix locks. No session-open ritual re-run;
no drift-check (the recovery transcript carried the open state).

## What was delivered

**1. F2 fix report triaged (`account_id_normalization_report.md`).**
The literal F2 WRITE defect is fixed and proven: a credit + deploy
against a real `uuid4().hex` account succeeds under
`foreign_keys = ON`, stored verbatim, the pool fills to $20 then
drains to 0. Settlement byte-identical (`9e07a75d…40d4a3`). A
permanent FK regression guard was added
(`test_f2_regression_hex_account_credit_holds_fk_and_fills_pool`).
Promo spine green (112 passed). NOT all-green: Code's headline F-A —
the same hex-vs-dashed mismatch lives one rung up on the
read/display path (`balance_derivation.py` :512 + the racing
`/log-context` endpoint re-normalize the three refs through `UUID`),
so against a real account the pool would show empty even though the
credit exists. Correctly flagged-not-chased (outside the §5 named
anchors); the 10 read-path-caller test regressions ARE this
surfacing, not a break in the fix.

**2. F-B (cash_flow) confirmed real.** The report flagged
`domain/cash_flow` as plausibly sharing the pattern but did NOT
verify it. This session verified it live:
`domain/cash_flow/__init__.py` types the three refs `UUID` (409–411);
`workflows/cash_flow/v1/cash_flow_store_adapter.py` re-normalizes
through `UUID(...)` on read (312–315) and writes dashed via
`str(UUID)` (344–348). Identical F2 pattern, one domain over. The
tell: Code had to seed the cross-domain balance tests as *dashed*
str (not hex) "for cash_flow consistency" — promo and cash_flow have
DIVERGED on the format of the same three fields.

**3. Band-aid question resolved → MINIMAL-HOLISTIC.** The operator
asked, as dev lead, whether fixing only the display path was a
band-aid. Answer: yes — same root cause across FOUR sites
(cash_flow domain + cash_flow store adapter + balance_derivation +
racing router), two divergent conventions (promo hex-verbatim,
cash_flow dashed); the root is that the three account refs have NO
single canonical format — every module decides for itself. The
holistic fix closes the whole class in one bounded sweep + guards,
not three sequential "fix this path too" briefs. Chose
minimal-holistic for pre-cutover: one sweep retyping all in-scope
sites to hex-str-verbatim + per-path regression guards + cash_flow
verify-and-fix folded in (NOT deferred as a later F-B patch), with a
shared canonical account-ref type PARKED as a post-cutover hardening
item (the full-holistic option — its cross-domain reach is a DR-030
decision, too much blast radius under the cutover clock).

**4. Review-first gate added (operator call).** Before the fix
locks, the operator chose to commission a READ-ONLY codebase review
— because this session's enumeration was annotation-scoped (the grep
matched `: UUID` annotations only), and the defect class is broader:
unannotated params, `str`/f-string/`.hex` serialization, query/
lookup construction, and — the highest-value unknown — the FRONTEND
origin of the `/log-context` query param's format. A review also
gives independent eyes on whether retype-to-hex-str is the right
treatment everywhere and whether minimal-holistic is the right
altitude. Review and fix kept as SEPARATE sessions deliberately: a
scope/altitude surprise is the operator's call, not something Code
flows straight into mutating.

**5. Account-ref surface review brief drafted + locked + handed.**
`interface_triage/account_ref_surface_review_brief.md` — **240
lines, 10,697 bytes, sha `a8b39f861821f3f9`**, 11 sections.
Source-review shape (Session 33 precedent). Read-only, zero source
edits. Two jobs: (§5.1) prove the complete surface across domain/
workflows/ ui/ frontend/ scripts/ — every site the three refs are
typed/stored/read/compared/serialized/queried in non-hex form, as a
scope map; (§5.2–§5.4) pressure-test the treatment per site, trace
the frontend `/log-context` param origin (its own area + escalation
trigger), and give an independent altitude verdict. §9 hard limits:
read-only, dirty tree unchanged, settlement untouched, do NOT
re-litigate the proven promo spine, do NOT flag spine-owned UUIDs
(event_id, parent_event_id, supersedes_event_id, correlation_id,
promo_id, promo_template_id), escalation-as-finding (report
prominently, don't expand scope to fix). The seven drafting calls
were surfaced to the operator and all accepted. A ready-to-paste
Code prompt was provided (read-and-confirm gate per Flow 3 — Code
echoes back the two jobs, the read-only constraint, the in-scope
refs vs spine-owned UUIDs, and the output path before starting).

## Standing-instruction adherence check

- **Cat 1 (brief drafting — surface only strategic/operational
  decisions):** honoured. The band-aid resolution and the
  minimal-vs-full-holistic altitude were surfaced as the operator's
  calls; technical detail (which files, line ranges, §-section
  shape) handled inside the brief.
- **Cat 1 (tool routing recommended explicitly):** honoured —
  Chat-drafts / Code-executes named at each step.
- **Cat 2 (fenced-block ~60–70 char wraps):** honoured in the brief
  draft and the Code prompt.
- **Cat 2 (opening prompt generated unprompted at close):**
  honoured — S185 prompt written (with the operator's verbatim
  workflow question as the primary deliverable).
- **Cat 3 (DB read discipline):** not exercised — no DB reads this
  session (code inspection only, read-only grep/read_file).
- **Cat 4 (BetHub Code sessions read+confirm before building):**
  honoured — the Code prompt enforces the read-and-confirm gate.
- **Cat 4 (Drive sync — do not prompt at close):** honoured — no
  Drive prompt.

## Open items

Pointer-only — full detail in `current_state.md`.

**Closed in Session 184:**
- Triage the F2 fix report — DONE (write defect fixed + proven;
  F-A/F-B surfaced). ✅
- Band-aid-vs-holistic question — RESOLVED (minimal-holistic; same
  root cause, four sites, two conventions; shared type parked
  post-cutover). ✅
- Verify F-B (cash_flow) — DONE; confirmed real. ✅
- Review-first decision — MADE (operator gate). ✅
- Draft + lock + hand the surface review brief — DONE
  (`account_ref_surface_review_brief.md`, sha `a8b39f86…`). ✅

**New / promoted for Session 185:**
- **S185 primary (operator-set, no confirmation): describe the
  operator's actual betting WORKFLOW/activities for a $50 2nd/3rd
  insurance bet** — operational detail (what the operator is
  physically doing), lighter on software internals. NOT a triage.
- Triage Code's `account_ref_surface_review_report.md` — CARRIES;
  runs whenever the operator has run the review Code session (may be
  before or after S185's workflow question). On a clean review,
  draft the FIX brief against the verified surface ("close the
  account-reference format class").

**Carried (unchanged from S183 unless noted):**
- Pre-cutover live-validation sweep (operator-run, manual) — after
  the account-ref class closes.
- Launcher brief (F9/F10 + F12) — independent; parallel or after.
- Racing-API placings backfill + nightly results-sync fix — own
  brief; parallel, not a blocker.
- W16 cutover scoping (after the briefs land).
- Parking-lot (unchanged): hedge-link on manual entry;
  bet-mutation-log viewer; Log Past Bet soft-books-only picker;
  in-app catalogue-management UI; `presets.ts` dead-code (F6);
  free-bet config-control cosmetics (F1); `…_instance_id` rename;
  partial free-bet draw-down; Piece B (post-cutover).

## Session close state

- Rebuild folder root: clean, no phantom v2 files.
- New this session: `interface_triage/account_ref_surface_review_brief.md`
  (240 lines, sha `a8b39f86…`).
- `current_state.md` rotated to S184 close.
- `v3_build_picture.md` updated (W17 stream moved): lead paragraph
  + W17 milestone carry the S184 outcome.
- `.close_out_backups/`: stale `SESSION_184_opening_prompt.md`
  removed; `SESSION_185_opening_prompt.md` written.
- No `standing_instructions.md` change this session.

## Forward routing — CONFIRMED WITH OPERATOR

S185 opens directly on the operator's workflow-description question
(verbatim in the opening prompt), no confirmation needed. The
review-report triage carries as an open item and runs whenever
Code's review report has landed; on a clean review, the next step is
the fix brief against the verified surface. Operator confirmed this
routing at S184 close ("Provide Claude Code prompt, then please
close the session. For the open of the next session do the below
question, no confirmation needed.").

---
*Session 184 record. Closed 2026-06-24 14:46 ACST.*
