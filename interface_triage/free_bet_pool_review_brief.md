# Free-bet pool review brief (read-only)

**Drafted:** 2026-06-19 ACST (Session 168, Claude Chat).
**For:** one bounded Claude Code session, out-of-session.
**Type:** read-only source-code review. No edits, no
build, no schema change. Output is one report that the
next Chat session triages.

---

## §1 — What this brief is and is not

This is a **read-only review** of v3's free-bet pool and
settlement layer. Code reads the named source, answers
three questions with file/line evidence, sizes the
effort to close the gap, and writes one report.

It **is**: a source map + effort estimate.

It **is not**: a fix, a build, a schema change, or a
draft of the eventual build brief. Code changes no
files in `bethub-v3`. Surprises are recorded as findings
in the report, not chased into code. Remediation routes
to Chat triage next session, not into this session.

If the review needs more than one Code session, that is
itself a finding — Code reports the partial map and
stops rather than running past budget. A partial-but-
coherent map beats a complete-but-rushed one.

---

## §2 — Why this work exists

Session 167 ran a records-look that found linking a
triggered free bet to its qualifier needs no new schema
— the storage already carries the link. Session 168
opened that into the bigger picture: the operator's
free-bet handling is a **pool** model, and the question
is no longer "wire a link" but "how much of the pool
foundation is built, and what does the rest cost."

The pool model is a **locked decision from Session 70**.
Code cannot see that conversation, so it is reproduced
here as the reference the review maps against.

### The locked free-bet pool model (Session 70)

Every account-at-book carries **one pooled free-bet
balance**, treated as cash-equivalent for placement:

- **Pooled balance, not tokens.** When a qualifier
  triggers a $50 free bet, the account-at-book's free-bet
  balance rises by $50. Placing a free-bet-funded bet
  draws the balance down. The operator does not pick
  "which free bet" — they draw from the pool.
- **Oldest-first drawdown.** Consumption takes the
  oldest unspent free bet first, then the next. This is
  what sets the parent/cycle attribution automatically —
  the parent is whichever earlier bet generated the
  free bet at the front of the queue. Operator never
  picks; v3 attributes at commit.
- **Discrete-fenced free bets are a flag, not a separate
  balance.** Some books issue a free bet that must be
  used as a single unit. Rare. Carried as a "discrete"
  flag on the ledger entry; if a drawn amount does not
  match, consume a non-discrete entry instead or warn.
  Invisible in 95%+ of cases.
- **Ad-hoc / goodwill free bets** (book gives one with no
  triggering bet) are entered manually — no qualifier,
  so no parent cycle to inherit.

### The timing-gap requirement (Session 168)

The book often settles a qualifier and credits the free
bet **before** the tool has settled that qualifier. So
the operator may want to deploy free-bet funds the tool
does not yet know about. The model must tolerate this:
let the pool go briefly provisional (e.g. reads −$50),
record the drawdown, and **back-attribute** it once the
qualifier settles in-tool and the credit lands. This is
the piece whose cost is least known and the main reason
this review exists.

---

## §3 — Pre-reads

Required, in order:

1. This brief in full — especially the §2 locked model.
2. `interface_triage/cycle_capture_records_look.md`
   (rebuild folder) — the Session 167 records-look this
   review extends.

Reference-only (read if a question needs it, not
front-to-back):

- `interface_triage/frontend_fixes_brief.md` /
  `frontend_fixes_report.md` — precedent brief + report
  shape only.

All other reads are the source files named in §5.

---

## §4 — System access

- **Filesystem:** `bethub-v3` repo at
  `/Users/tim/Desktop/Projects/bethub-v3`. **Read-only.**
  Code opens files; it does not edit, create, or move
  any file in the repo.
- **Databases:** none required. This is a source review,
  not a data audit. If Code believes a live read would
  sharpen an answer, it names that as a finding and the
  read stays read-only at the canonical path (never copy
  the DB file) — but the default expectation is no DB
  access needed.
- **Git:** read-only. No `git add/commit/stash/restore/
  checkout/reset`. The working tree is dirty/in-flight by
  design (frontend fixes landed S167, untracked `ui/web/`)
  — Code does not touch it.
- **Timestamps:** Adelaide local (ACST/ACDT) for every
  time reference in the report, per DR-021.

---

## §5 — Review areas

Three areas. Each is answered with file/line evidence,
not from assumption. Where the answer is "not built,"
say so explicitly and name where it would live.

### §5.1 — What does settlement do today?

**Question:** when a qualifier settles, does v3 do
anything to the free-bet pool — specifically, does a
settled-as-placed insurance qualifier auto-create the
triggered free-bet credit? Or is crediting still manual
/ absent?

Chat's pre-flight (S168) found `domain/settlement/` is an
empty stub (`__init__.py`, 0 bytes), but the real
settlement + reconciliation logic lives under
`workflows/bet_entry/v1/`. A grep of `settlement.py`
(1,354 lines) for `free_bet` / `credit` / `triggered` /
`promo` returned **nothing** — first-pass signal that
settlement does not touch the promo layer. Confirm or
correct that.

Anchors:

- `workflows/bet_entry/v1/settlement.py`
- `workflows/bet_entry/v1/reconciliation.py`
- `workflows/bet_entry/v1/orchestrator.py`
- `ui/api/routers/provisional.py` (the existing
  `PROVISIONAL` bet-state + manual-resolve queue)
- `domain/settlement/__init__.py` (confirm empty)

Report: what settlement does on each terminal state
(won / lost / voided / provisional), and the exact
answer on whether free-bet crediting happens anywhere in
that path. If crediting exists, name the file/line; if
not, name where it would have to hook in.

### §5.2 — How much of the pool model is wired?

**Question:** map the §2 locked model against the code,
piece by piece — for each, BUILT / PARTIAL / MISSING
with evidence.

Map these five:

1. **Pooled balance per account-at-book** — is the
   free-bet balance derived as one pooled figure?
2. **Credit→qualifier link** — does a credited free bet
   record the bet that earned it, and is the trigger
   path enforced?
3. **Oldest-first drawdown + automatic cycle/parent
   attribution at commit** — does deploying a free bet
   consume oldest-first AND set the new bet's `cycle_id`
   from the qualifier? (Records-look found the deployed
   bet currently starts a FRESH cycle — confirm and
   locate exactly where the propagation is missing.)
4. **Discrete-fenced flag** — does a ledger entry carry
   a discrete/single-unit flag, with any handling?
5. **Operator deploy surface** — does the screen draw
   from the pool, or still have the operator tick
   individual free bets? (`LogBetPanel.tsx` currently
   has an `isFreeBet` toggle + a per-credit checkbox
   list keyed on `credit_event_id` — confirm.)

Anchors:

- `domain/promos/__init__.py` (`free_bet_credited` /
  `free_bet_deployed` payloads; `triggering_bet_id`;
  `source_credit_event_ids`; `draw_down_breakdown`)
- `workflows/promos/v1/fb_deployment.py`
- `workflows/promos/v1/promo_derivations.py`
- `workflows/promos/v1/promo_store_adapter.py`
- `workflows/balances/v1/balance_derivation.py`
- `store/schema/promos.py`, `store/schema/bets.py`
- `store/repositories/bets.py`
- `ui/api/routers/racing.py` (the bet-log POST;
  `consumed_credit_event_ids`)
- `workflows/bet_entry/v1/record_builder.py`
- `ui/web/src/components/LogBetPanel.tsx`,
  `ui/web/src/api/racing.ts`

### §5.3 — What does closing the gap cost?

**Question:** size the remaining work, split into two
buckets, because they carry very different cost and risk.

**Bucket A — clean cycle attribution.** Wire the
deployed free bet to inherit its qualifier's cycle
(oldest-first), so a triggered free bet joins the
qualifier's cycle instead of starting fresh. Assume the
qualifier's credit already exists in the tool.

**Bucket B — timing-tolerance reconciliation.** Allow a
deploy before the credit exists in-tool: provisional
pool balance (can read negative), the drawdown recorded,
and back-attribution once the qualifier settles in-tool
and the credit lands. Note any reuse available from the
existing `PROVISIONAL` bet-state / burst-review queue
machinery.

For **each bucket** report: effort scale (S / M / L with
a rough session count), the files that would change,
qualitative risk (especially anything that reaches the
bet-record write or settlement path), dependencies /
ordering between the buckets, and a confidence level on
the estimate. No code is written — this is sizing only.

---

## §6 — Sequencing within session

Do §5.1 (settlement map) first, then §5.2 (pool map),
then §5.3 (effort) — the effort estimate depends on
what the first two find. If a cleaner order emerges,
Code may deviate and say why in the report.

## §7 — Success criteria

The review succeeds when all three areas are answered
with file/line evidence, every BUILT/PARTIAL/MISSING
call is backed by a citation, both effort buckets carry
a scale + confidence level, and no file in `bethub-v3`
was changed. "I could not determine X" is an acceptable
finding if the reason is named — guessing is not.

---

## §8 — Output spec

One file, written to:

`interface_triage/free_bet_pool_review_report.md`
(rebuild folder — NOT inside the `bethub-v3` repo).

Section structure:

1. Settlement-today map (§5.1 answer).
2. Pool-model wired-vs-missing table (§5.2 — the five
   pieces, each BUILT / PARTIAL / MISSING + evidence).
3. Effort estimate (§5.3 — buckets A and B, scale,
   files, risk, dependencies, confidence).
4. Findings / surprises (anything outside the three
   questions worth flagging).
5. Self-assessment (coverage, any area left partial,
   confidence overall).

Rough length 250–450 lines. Over is fine if the detail
earns it; flag it in the self-assessment if so.

The report does **not** contain: code changes, a build
plan or build brief, schema proposals, or a recommended
sequencing decision (now-vs-later is Chat's call with the
operator next session — the report sizes, it does not
decide).

---

## §9 — Hard limits (non-negotiable)

- **Read-only.** No edits, creates, moves, or deletes in
  `bethub-v3`. The only file Code writes is the report,
  in the rebuild folder.
- **No git operations** of any kind. Dirty tree is left
  exactly as found.
- **No schema changes, no build, no fixes.** Even an
  "obvious" one-line wire-up is out of scope — this
  review sizes that work, it does not do it.
- **No bet-path or settlement-path edits.** The live-
  proven placement path stays untouched. This is the
  bet-safety hard rule: zero reach into placement or
  settlement code.
- **Single bounded session.** If the map can't complete,
  report partial + stop; don't continue past budget.
- **No mid-session operator escalation.** Run end to
  end; surface open questions as findings in the report.
- **Don't draft the build brief.** That is the next Chat
  session's job, drafted against this report.

## §10 — What happens after Code's session

The next Chat session reads the report, triages the three
answers in plain operational terms for the operator, and
two decisions follow: (a) draft the cycle-capture / pool
build brief against the now-known effort, and (b) the
operator's call on whether the timing-tolerance bucket
(B) goes in pre-cutover or sequences as its own slice
straight after. Code does not produce that brief.

## §11 — Cross-references

- **Locked decision:** Session 70 free-bet pool model
  (pooled balance, oldest-first drawdown, automatic
  cycle attribution, discrete-as-flag) — reproduced §2.
- **Builds on:** S167 `cycle_capture_records_look.md`.
- **DRs:** DR-030 (v3 module boundaries — the review
  respects them but changes nothing), DR-032 (Betfair
  canonical reference / the cycle axis), DR-022
  (account / book / account-at-book vocab), DR-021
  (Adelaide timestamps).
- **Excluded / parked:** the launcher brief (independent,
  unaffected by this review); all racing-page parking-lot
  items; the manual realised-conversion how-to (waits on
  the build-brief UI shape).
