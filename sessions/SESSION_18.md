# Session 18 log

**Opened:** 2026-04-28 19:17 ACST
**Status:** active
**Anchor source:** `TZ="Australia/Adelaide" date` per DR-021

---

## Scope (in order)

1. **Companion documents for the multi-agent review.**
   `architecture_current.md` (descriptive — what's locked, entities,
   DRs, framed for outside readers; largely extractable from
   `architecture.md`'s reconciliation contract section + decisions.md
   DR-027/028) and `data_layer_current.md` (descriptive — what
   `capture.db` does today, fields, cadence, gaps; new file, needs
   operator input on empirical state of capture.db). Target ~2–4
   pages each. **First priority.**

2. **Multi-agent governance review orchestration itself**, if
   capacity permits after companion docs land. Otherwise carries to
   Session 19. **Second priority.**

## Carry-out triggers

- Context tightens or operator fatigue surfaces → stop after (1),
  carry (2) to Session 19.
- Empirical-capture session for `data_layer_current.md` reveals
  scope larger than current-state-doc shape → close out, redefine
  next-session scope.
- §2 close-out protocol fired in Sessions 12–17. Bias toward
  closing early. Sessions 15 and 16 close-out failures underline
  pushing through is the exception, not the default.

## Governing DRs

DR-021 (timestamp anchor), DR-007 (vocabulary), DR-022 (account /
book / account-at-book), DR-024 (operating/analytical separation),
DR-027 (two-database architecture), DR-028 (integration boundary
discipline), plus the governance.md session close-out protocol
§§1–4 (especially §3 script structure AND §4 recovery procedure
given Sessions 15 and 16 close-out failures) and the pre-flight
directory-listing instruction.

## Event log

- 19:17 ACST — session opened, log created. Adelaide local time
  anchored via `TZ="Australia/Adelaide" date`.
- 19:17–19:25 ACST — orientation: read work_in_progress,
  SESSION_17, decision_under_review (six sections complete),
  v3_data_requirements (B.1–B.8 absorbed), architecture
  (reconciliation contract A.0–A.9 read in full), decisions
  (DR-001 through DR-029 read in full; DR-027/028 named explicitly
  per orientation discipline), governance (multi-agent review
  pattern + close-out protocol §§1–4). Pre-flight directory
  listing run; rebuild folder root clean post-Session-17, one
  backup remaining (`SESSION_16_20260428T1900_recovery`), 17
  archived session files SESSION_01 through SESSION_17, no active
  session_log.md, no SESSION_18.md, no architecture_current.md or
  data_layer_current.md. State entering Session 18 confirmed.
- 19:25 ACST — DR-027 / DR-028 named per orientation discipline.
  Cross-DB boundary protections registered for the session.
- 19:25–19:50 ACST — `architecture_current.md` drafted (158 lines,
  ~3 pages). Seven sections: framing, high-level shape (three
  layers + two databases + operating/analytical separation),
  entity model with vocabulary lock, event log spine with
  supersession + cash-flow model, cross-DB boundary (capture.db
  framing + DR-027/028 + read-time uses + periodic-only API),
  reconciliation surfaces (six surfaces + operation-net-flow
  distinguished + settlement-as-divergence-not-hierarchy +
  burst-review workflow), DR index. Operator review surfaced two
  corrections: (a) capture.db consumer framing was wrong —
  Strategy 1 not yet a thing, AFL Edge mothballed for months,
  Racing EV model not actually a live consumer; only BetHub v2
  reads it today and even that is light. The honest framing is
  "data layer running ahead of analytical need; v3 is the first
  execution-time consumer." Fixed in §2 and §5.1. (b) "Burst" was
  used in §6 without definition — outside readers wouldn't have
  it. Added a short framing paragraph at first use, also covering
  persona session (the contrasting operating-mode context) and
  noting the DR-022 vocabulary correction.
- 19:50–20:15 ACST — operator surfaced uncertainty about whether
  v2 is actually a capture.db consumer; instinct was that v2 might
  go direct to Betfair without VPS at all. Empirical check via v2
  codebase + log inspection: vps_client is wired into v2's racing
  page (`api/racing.py`) and into `betfair_sync.py` (used during
  settlement for race-result lookup), so the code paths exist. BUT
  v2's bethub.log shows "VPS API unreachable, is the SSH tunnel
  running?" warnings every 30 seconds for the past six days
  continuously, no successful VPS calls in that window, and v2
  operating normally throughout because betfair_sync's actual
  settlement path is direct to Betfair API and the racing page
  isn't a primary operator surface. Honest framing now: capture.db
  has no real active consumer at the moment despite being
  continuously running; v3 will be the first execution-time
  consumer; this materially changes the operational stakes on
  tunnel reachability — v2 demonstrates "VPS unreachable for a
  week, no one notices" is the empirical default, while v3's
  design calls VPS on every bet log. The `bf_snapshot_unavailable`
  graceful-degrade flag in DR-026 is currently theoretical
  insurance against a failure mode v2 has demonstrated is common.
  Re-edited §2 (two-databases paragraph) and §5.1 (capture.db
  framing) with this empirical grounding plus a new third
  paragraph in §5.1 making the v3-stakes-change explicit. The
  framing is now stronger for the multi-agent review than the
  original "thriving multi-consumer ecosystem" framing — assessors
  see the actual operational reality and the risk it implies for
  v3.
- 20:15–20:35 ACST — operator confirmed Option 3 carry-in approach
  (surface in `data_layer_current.md` AND flag as multi-agent
  review carry-in question separately, leave DUR untouched). Also
  confirmed Session 18 close here with `data_layer_current.md` as
  Session 19 fresh-mind work. Tunnel state empirically verified
  (no autossh process, no listener on 8400, curl fails immediately;
  launchd plist `com.bethub.vps-tunnel.plist` exists at
  `~/Library/LaunchAgents/` but isn't running) — confirmed
  likely-easy fix outside Session 18 scope; logged as Session 18
  follow-up in work_in_progress.md.
- 20:35–21:00 ACST — close-out: pre-condition polarities verified
  against this session's actual operations (session_log active →
  archived; SESSION_18.md absent → present; architecture_current.md
  unchanged at close; data_layer_current.md absent before, absent
  after; work_in_progress.md updated for Session 19; DUR
  untouched; decisions.md untouched; SESSION_16 recovery backup
  cleaned). work_in_progress.md updated. Close-out script written
  with §3 all-or-nothing structure, backups before writes, "files
  moved? verified." print before success-logged manifest per
  Session 16 lesson.

---

## Close-out

**Closed:** 2026-04-28 21:00 ACST

**Summary:** Session 18 produced `architecture_current.md` (158 lines, ~3 pages, descriptive document for the multi-agent review framed for outside readers without project context). Seven sections: framing, high-level shape (three layers + two databases + operating/analytical separation), entity model with vocabulary lock, event log spine with supersession + cash-flow model, cross-DB integration boundary (capture.db framing + DR-027/028 + read-time uses + periodic-only API), reconciliation surfaces (six surfaces + operation-net-flow distinguished + settlement-as-divergence-not-hierarchy + burst-review workflow), DR index. Sixteenth consecutive early-close session.

The substantive design move this session was an empirical discovery during operator review: capture.db's actual current consumer state. Initial draft framed v3 as joining a multi-consumer ecosystem; operator first corrected the consumer list (Strategy 1 not yet a thing, AFL Edge mothballed, Racing EV model not actually a live consumer), then surfaced uncertainty about whether v2 itself was actually consuming capture.db. Empirical verification via v2 codebase + bethub.log inspection confirmed: vps_client wired into v2's racing page and betfair_sync settlement path, but the SSH tunnel has been unreachable continuously for at least six days with v2 operating normally throughout (settlement goes direct to Betfair API, racing page isn't a primary operator surface). capture.db today is a quietly-running data layer with no real active consumer. v3 will be the first execution-time consumer, and that materially changes the operational stakes on tunnel reachability — the `bf_snapshot_unavailable` graceful-degrade flag in DR-026 is currently theoretical insurance against a failure mode v2 has demonstrated is common. Honest framing now in `architecture_current.md` §2 and §5.1; full surfacing carries to Session 19's `data_layer_current.md` as a v3-stakes question for assessors. DUR §4 left untouched per Session 17 close (re-opening would create a fourth-pass framing risk).

**Lessons applied (from Session 15 + 16 close-out failures):** pre-condition assertion polarities verified against this session's actual operations before running the close-out script. session_log.md (active) pre-existed and is removed; sessions/SESSION_18.md did not pre-exist and is created; architecture_current.md was created this session and remains; data_layer_current.md did not pre-exist and remains absent (deferred to Session 19); work_in_progress.md pre-existed and is updated; DUR pre-existed and remains untouched; decisions.md pre-existed and remains untouched. Session 16 lesson applied: visible "files moved? verified." print *before* the success-logged manifest. Session 17 backup cleanup (`SESSION_16_20260428T1900_recovery`) included.

**Open items carrying to Session 19:**

- `data_layer_current.md` (descriptive — what `capture.db` does today, fields, cadence, gaps; new file, needs operator input on empirical state of capture.db; carries the Session 18 operational-reality finding as a v3-stakes question for assessors). **First priority for Session 19.**
- Multi-agent governance review orchestration itself (second priority, contingent on `data_layer_current.md` landing cleanly; realistically Session 20 if it consumes Session 19).
- Build strategy decision (strangler-fig vs clean break + slice strategy) — post multi-agent review.
- DR-029 data review scoping after multi-agent review approves direction.
- **VPS tunnel restart** — separate from documentation work; likely-easy fix outside Session 18 scope; operator's call when to address; doesn't block Session 19's documentation work but worth restoring before any v3 build session that would actually exercise the integration.
- **Parked separately (not for the review):** the operator-Claude context-retention concern surfaced Session 17 — distinct from the architectural review; deserves its own attention as a governance question. Not folded into DUR; not Session 19 work.

**Backups removable post-Session-18:** none (Session 18's own backups will be cleaned at Session 19 open after verification).

**Operator instructions still in effect for Session 19:** unchanged from Session 18 list, plus a new addition: for empirical questions about v2 or capture.db state, verify via codebase + log inspection rather than trusting operator memory or first-pass assumption — Session 18 demonstrated this concretely (operator's instinct was directionally right but only the empirical check produced the honest framing).

**Standing instruction reaffirmed:** complete opening prompt for Session 19 produced at session close per the recent_updates standing instruction.
