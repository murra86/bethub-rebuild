# W12 balances — Code session opening prompt

You are picking up the W12 balances workstream
(read-side derivations for Locations 1 + 2 balance,
operation net-flow, free-bet inventory state,
AccountCare warning state, promo journey state).
The brief is locked.

## Required reads — in order

1. `dr029/w12_balances/w12_balances_brief.md` — the
   commission. Read end-to-end.
2. `architecture.md` §A.5 — the cash-flow model the
   brief implements. Recently amended to reflect
   the single-flavour profit-share model (holder's
   bank IS the parked pool — they are literally
   the same physical money; a profit-share is pure
   ledger reallocation, never bank-touching). The
   brief and §A.5 are coherent under the clarified
   model.
3. `current_state.md` — live working state.
4. `standing_instructions.md` — operator-Claude
   working agreement.
5. `governance.md` — close-out and ship discipline.
6. `decisions.md` — Decision Records, particularly
   DR-019 (read-time derivation), DR-022
   (book/account vocabulary), DR-027/DR-028 (two-DB
   boundary), DR-030 + S124 amendment (module-
   boundary contracts with derivation-chain carve-
   outs), DR-032 (canonical bet-record / bet-leg
   shape).

## Load-bearing first action — §6.1 alignment check

Before any substantive edits, run all seven
alignment checks in brief §6.1 (A through G). The
brief is anchored on shipped W14.1 / W13 / W11 /
W4-W6 substrate; if shipped reality has drifted,
the brief's spec needs adjustment before any code
lands.

The §6.1 checks are not optional. Operator-
amplified judgement applies — surface ANY concern
beyond the seven specified checks as ALIGNMENT-
FINDING-H or beyond.

**ANY ALIGNMENT-FINDING halts substantive edits.**
Surface findings in §3 of the ship report;
operator-Claude triages in the next session. Code
does NOT unilaterally amend specs, contracts, or
DRs to resolve findings.

## Substantive build — only on clean alignment

If §6.1 passes clean, execute the §6.2 build order
in sequence. The two substrate step-zeros (§5.1
`warning_type_id` slug-flip; §5.1b `funding_source`
field drop) land FIRST, then the derivation
sections §5.3–§5.8, then the §5.9 module-structure
and lint-imports verification, then §5.10 tests.

Each step has a verification gate per §6.2. Don't
short-cut.

## Hard limits

§9 enumerates them in full. The load-bearing ones:

- §9.2 — no schema or substrate changes beyond
  the named §5.1 + §5.1b carve-outs.
- §9.4 — no Alembic migration; the orphan
  `funding_source` column in the
  `cash_flow_events` table is tolerated.
- §9.5 — no cross-domain imports beyond
  derivation-chain carve-outs.
- §9.7 — dirty-tree discipline (Sessions 35/36/37
  pattern).
- §9.8 — partial-ship discipline: no half-baked
  ship; surface as a finding if a step doesn't
  land cleanly.

## Output

§8 names the ship report shape. Write to
`dr029/w12_balances/w12_balances_report.md` (the
canonical path is free; the prior S133 alignment-
halt report has been renamed to
`w12_balances_s133_alignment_report.md` for
historical reference).

The ship report must surface:
- Alignment check outcomes (§3 of the report).
- Substrate-step outcomes for §5.1 and §5.1b (§4).
- Build-step outcomes per §6.2 (§5).
- Test count: baseline (W13 close: 753 passing)
  vs post-ship, with net delta named and any
  variance beyond ±5 flagged as a finding.
- Lint-imports / mypy / ruff verification.
- Any deferred work or open findings.

## Tool routing and codebase

Claude Code single bounded session. Filesystem via
Desktop Commander or `projects-filesystem`. The v3
codebase is at `/Users/tim/Desktop/Projects/bethub-v3/`;
the rebuild governance folder is at
`/Users/tim/Desktop/Projects/bethub-rebuild/`.

## Single bounded session — halt discipline

This is one bounded session. Do not extend beyond
the locked scope. If you hit a wall (alignment
finding, dirty-tree complication, test-count
explosion, scope ambiguity), halt and ship the
report with what's landed. Operator-Claude triages
next session. No unilateral spec amendments.
