# BRIEF — Account-reference format-mismatch class: surface & approach review (READ-ONLY)

**File:** `interface_triage/account_ref_surface_review_brief.md`
**Drafted:** S184 · 2026-06-24 ACST · LOCKED on operator approval
**Repo under review:** `/Users/tim/Desktop/Projects/bethub-v3`
@ `main` (HEAD `2329604`)

---

## §1 — What this brief is and is not

This is a READ-ONLY codebase review, executed in a single
bounded Claude Code session. Two jobs: (a) prove the COMPLETE
surface of the account-reference format-mismatch class across
the full stack; (b) pressure-test whether retype-to-hex-str-
verbatim is the correct treatment at every site, and whether
"minimal-holistic" is the right altitude — or whether a shared
canonical type is needed now.

Code applies NO fixes and edits NO source — not even the sites
already known. Surprises become findings in the report, not
edits and not mid-session pings. Remediation routes to the
next operator-Claude triage session, which drafts the fix
brief. Code does not write that fix brief.

If the surface proves larger than one session can fully map,
that is a finding (partial-but-coherent beats complete-but-
lost-coherence) — not a continuation past budget.

## §2 — Why this work exists

The F2 fix (`account_id_normalization_report.md`) closed the
promo WRITE path: account_id / book_id / account_at_book_id
are now stored verbatim as operational hex (`uuid4().hex`) on
the promo spine, FK-safe, with a regression guard. Proven.

But its report surfaced two open edges: F-A (read-path callers
— `balance_derivation` and the racing `/log-context` endpoint
— re-normalise these refs through `UUID`, re-dashing them, so
the pool DISPLAY still fails against real accounts) and F-B
(`domain/cash_flow` plausibly shares the pattern — UNVERIFIED).

This session (S184) confirmed F-B is real and enumerated four
modules still typing the three refs as `UUID`. BUT that
enumeration matched only the `: UUID` annotation form. The
defect class is broader than the annotation — it includes
unannotated params, `str()`/f-string/`.hex` serialisation,
query/lookup construction, and the FRONTEND origin of the
`/log-context` query param's format. A grep cannot prove that
surface is closed. Before a "holistic" fix brief locks, the
surface must be proven complete and the approach verified — so
we close the class in one pass rather than discover a fifth
live site mid-cutover.

## §3 — Pre-reads (in order)

Required:
- `/Users/tim/Desktop/Projects/bethub-rebuild/interface_triage/account_id_normalization_report.md`
  (the F2 report — the convention, the named anchors, F-A/F-B)
- `/Users/tim/Desktop/Projects/bethub-rebuild/interface_triage/account_id_normalization_brief.md`
  (the contract F2 ran against — in-scope vs excluded)

Reference-only (consult if needed, not required end-to-end):
- governing DRs: DR-030 (module boundary), DR-027/028 (two-
  database), DR-021 (Adelaide time), settlement byte-identity.

## §4 — System access

- Mac filesystem, direct. Repo:
  `/Users/tim/Desktop/Projects/bethub-v3` @ `main` (HEAD `2329604`).
- READ-ONLY. No source edits. No DB writes. Read-only
  inspection only: grep/ripgrep, read_file, pytest COLLECTION
  (`--collect-only`) and import-linter if useful for tracing —
  no test that mutates, no fixes.
- Dirty working tree is expected (~69 git entries at F2
  close). Code runs NO git state-changing command and makes NO
  edit, so the dirty list MUST be byte-for-byte unchanged at
  close. Confirm via `git status` start and close.
- Adelaide local timestamps (ACST/ACDT) per DR-021 for every
  time reference in the report.

## §5 — Substantive scope

The three references in scope, everywhere they appear:
`account_id` · `book_id` · `account_at_book_id`
Operational/canonical form = hex (`uuid4().hex`, 32-char,
dashless), verbatim, as the router mints and the DB stores.

### §5.1 — Prove the surface (enumeration)

Known floor from S184 (confirmed; do NOT just re-confirm these
— treat as the floor and find the ceiling):
- `domain/cash_flow/__init__.py` (refs typed UUID, 409–411)
- `workflows/cash_flow/v1/cash_flow_store_adapter.py`
  (UUID() on read 312–315; str(UUID) on write 344–348)
- `workflows/balances/v1/balance_derivation.py`
  (wraps fetched ids in UUID; UUID-typed params + dataclass)
- `ui/api/routers/racing.py` (`/log-context` param typed UUID)

Commission: enumerate EVERY site across the full stack —
`domain/`, `workflows/`, `ui/api/`, `frontend/`, `scripts/` —
where any of the three refs is typed (annotated OR not),
stored, read, compared, serialised (str / f-string / `.hex` /
format), or used to build a query / lookup / filter, in any
form that is NOT hex-verbatim. For each: file:line, the
operation, and the form it produces or expects (hex vs dashed
vs UUID-object). Output a scope map (table) — the complete
site inventory.

CRITICAL distinction — do NOT flag the spine-owned UUIDs:
`event_id`, `parent_event_id`, `supersedes_event_id`,
`correlation_id`, `promo_id`, `promo_template_id` legitimately
stay UUID. Only the three account refs are in scope.
Misclassifying a spine id as an in-scope site is a false
positive; call the boundary explicitly where it's close.

### §5.2 — Pressure-test the treatment, per site

For each site in the §5.1 map, judge whether retype-to-hex-
str-verbatim is the correct fix HERE, or whether the site
needs a different treatment: a serialisation change, a query-
construction change, a schema dimension, or a genuine cross-
domain seam. Flag any site where hex-verbatim would itself
break something (e.g. a legitimate consumer that needs a
different form). The deliverable is a per-site verdict, not a
blanket "retype everything".

### §5.3 — Frontend trace (the highest-value unknown)

Trace where the racing `/log-context` query-param value
ORIGINATES in the frontend (`frontend/src/...`). What format
does the JS actually send for `account_at_book_id` — hex, or a
dashed/UUID-shaped string? This decides whether the F-A fix is
backend-only (retype the route param to str) or whether the
mismatch is upstream in the client and a backend retype alone
won't make the pool display. State the origin format with the
file:line that produces it. If the frontend sends non-hex,
that is an ESCALATION-CLASS finding (see §9).

### §5.4 — Pressure-test the altitude (independent verdict)

Independently judge: does "minimal-holistic" hold — i.e.
retype all in-scope sites to hex-str-verbatim + add per-path
regression guards, with NO new shared cross-domain type — as
the right altitude for a single pre-cutover fix session? Or
does the proven surface argue a shared canonical account-ref
type / normaliser is genuinely needed NOW (structurally
eliminating the class) despite the DR-030 module-boundary cost
and the cutover clock? Give a reasoned verdict either way;
this is genuine independent review, not ratification of the
operator-Claude recommendation.

## §6 — Sequencing within session

1. §5.1 enumerate (surface first — everything else needs it).
2. §5.2 per-site treatment.
3. §5.3 frontend trace (informs the altitude call).
4. §5.4 altitude verdict (last — it rests on 5.1–5.3).

A cleaner order Code discovers is fine; the dependency is only
that the verdict (5.4) comes after the surface (5.1) and the
frontend trace (5.3).

## §7 — Success criteria

The session succeeds when the report delivers:
- a complete §5.1 scope map (every site; hex/dashed/UUID form
  determined per site), with a stated confidence and any area
  Code could not fully prove named explicitly;
- a per-site treatment verdict (§5.2);
- the frontend origin format with file:line (§5.3);
- an altitude verdict with reasoning (§5.4);
- an explicit hit / no-hit call on each §9 escalation trigger.

## §8 — Output spec

Single file:
`/Users/tim/Desktop/Projects/bethub-rebuild/interface_triage/account_ref_surface_review_report.md`

Sections: baseline (HEAD, dirty count, settlement SHA
unchanged) · §A surface map (table) · §B per-site treatment ·
§C frontend trace · §D altitude verdict · §E escalation-
trigger calls · self-assessment (coverage, confidence, what
was not provable in one session).

Anticipated ~300–500 lines. Report contains NO applied fixes,
NO source edits, NO next-brief draft, NO overall "ship it"
sign-off beyond the §D verdict.

## §9 — Hard limits (non-negotiable)

- READ-ONLY. Zero source edits — not even the four known
  sites. This is a review; the fix is a separate session.
- No git state-changing ops (no add/commit/stash/restore/
  checkout/reset). Dirty list unchanged at close.
- `settlement.py` (`workflows/bet_entry/v1/settlement.py`, SHA
  `9e07a75d…40d4a3`) untouched — byte identity. (Read-only
  makes this automatic; named for the record.)
- No schema change, no DB write, no persisted-data change.
- Do NOT re-litigate the promo spine: the F2 fix is correct
  and proven. The 10 read-path-caller test failures are the
  known F-A surfacing, NOT a regression — do not flag them as
  broken promo work.
- Do NOT flag spine-owned UUIDs (§5.1) as in-scope sites.
- Single bounded session. Over-budget surface = a finding.
- No mid-session escalation. Run end-to-end; surface
  everything in the report.
- ESCALATION-AS-FINDING: if Code finds a frontend dimension
  (§5.3 non-hex origin), a schema dimension, or concludes a
  shared canonical type is needed pre-cutover — it reports
  that PROMINENTLY as a headline finding and STOPS THERE on
  that thread. It does NOT expand scope to fix, design, or
  prototype the larger change.

## §10 — What happens after

Next operator-Claude session (S185 triage) reads this report,
confirms the surface is complete and the approach/altitude
sound, then drafts the FIX brief against the verified surface
— framed as "close the account-reference format class" (all
in-scope sites + cash_flow verify-and-fix + per-path guards).
If the review surfaces a scope/altitude surprise (frontend,
schema, or shared-type-now), that is the operator's call
before the fix brief locks. Code does not draft the fix brief.

## §11 — Cross-references

- F2: `account_id_normalization_report.md` + `_brief.md`
  (`interface_triage/`).
- DRs: DR-030 (module boundary — the altitude tension),
  DR-027/028 (two-database), DR-021 (Adelaide time),
  settlement byte-identity.
- Arc: W16 cutover (this review de-risks the last credit-in
  edge before cutover scoping).
- Parking: shared canonical account-ref type = post-cutover
  hardening item (the §5.4 "full-holistic" option, if not
  pulled forward).

---
*End of brief. LOCKED S184 2026-06-24 ACST.*
