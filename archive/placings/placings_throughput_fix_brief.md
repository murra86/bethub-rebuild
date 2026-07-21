# Brief — placings-recovery throughput & false-quota fix

**Type:** Surgical fix (read-write, two named files + one systemd timer). Single bounded Code session.
**Status:** LOCKED — drafted and locked 2026-07-01 (Session 211).
**Anchored on:** live probe 2026-07-01 (Chat), `race_date_semantics_report.md`, `placings_trickle_report.md`.
**Bet-safety:** CLEAN by construction — analytical/capture side only (DR-033). No operational/betting DB, no Betfair operational path, no bet mutation touched.

---

## §1 — What this brief is and is not

This is a **surgical fix** to the racing-data-capture placings-recovery pipeline. Code makes the named changes to two files plus one systemd timer, verifies with a real backlog burn, and produces one report.

- Single bounded Code session. If the work doesn't fit, that's a finding, not a continuation.
- Surprises become findings in the report, not mid-session escalations to operator-Claude.
- Code does **not** propose or make the `race_date` identity-key fix (fault B — see §9). If the verification burn surfaces ghost-row creation, Code **measures and reports it**; it does not remediate it.

## §2 — Why this work exists

The placings backfill has recovered ~zero rows across weeks of effort while the deficit sits at ~41,633. A Chat-side live probe on 2026-07-01 established two things by direct observation:

1. **There is no API quota.** The Racing API returns no rate-limit or quota headers of any kind; a full resulted date (2026-06-06: 24 meets, 153 races, 1,944 runners, 1,855 placings) fetched clean **in 7.8 seconds** with 5/sec pacing, zero empty responses. The "daily cap / budget" model — embedded in the code's own comments (`get_unsynced_dates` docstring; `run_backlog_pass` constants) and in prior session summaries — is false.
2. **The wall is a per-second rate limit, misread.** When the per-second ceiling is tripped (most plausibly by the recovery job running concurrently with the live collector at the 23:30 ACST slot), the API returns HTTP 200 with an empty body — not a 429. The client's `raise_for_status()` passes, the empty result is logged as "truncated," and the nightly pass walls after 3 consecutive such events.

This brief fixes the throughput gate so rows can flow. It does **not** fix the matching-key fault (fault B) that determines whether flowed rows attach to the correct race — that is a separate, governance-adjacent brief (§9, §10).

## §3 — Pre-reads

Required, in order:

1. This brief.
2. `race_date_semantics_report.md` — the two-path `race_date` skew; context for why fault B is excluded and what the ghost-row verification is watching for.
3. `subscription/racing_api.py` — the API client and `sync_day` (edit target).
4. `scripts/backfill_race_metadata.py` — the backlog runner (edit target).

Reference-only (not required): `placings_trickle_report.md`, `BETHUB_DATA_REFERENCE.md`.

## §4 — System access

- **VPS:** `root@187.77.183.9` : `/home/racing/racing-data-capture`. **Read-write** on the two named files in §5 and the one systemd timer in §5.4. No other files edited.
- **capture.db:** opened `mode=ro` for all verification queries (§7). Never copied. Read via `start_process` Python at the canonical path.
- **Git:** working tree may be dirty. Read `git status` at session start; edit only named anchors; `git diff <file>` after each edit; `git status` at close to confirm the dirty-file set changed only by the named files. No `git add/commit/stash/restore/checkout/reset`.
- **Timestamps:** Adelaide local (ACST/ACDT) per DR-021 for every time reference in the report; note the UTC equivalent for timer changes.

## §5 — Substantive scope

Four changes, in dependency order.

### §5.1 — Client resilience: retry degraded fetches instead of swallowing them
**File:** `subscription/racing_api.py`, `sync_day()` per-meet loop (currently ~L206-235) and its `truncated` logic (~L243-257).

- A `/australia/meets/{id}/races` call that returns an **empty** races list is treated as **rate-degradation, not genuine-empty** (a resulted meet always has races). On empty, back off and retry the same meet with escalating delay (e.g. 1s -> 2s -> 4s), up to a small bounded number of attempts (Code chooses; 3-4 is the intent). Only if it stays empty after retries does the meet count toward `truncated`.
- **Instrument the ground truth:** on the *first* degraded (empty-200) response of a run, log the full response headers and status once, so the next real run captures definitively what the API emits under degradation. This is the cheap replacement for the quota guesswork.
- Do **not** add retry blindly inside `_api_get` for the meets-list call — an empty *meets* list can be legitimate (dateless/off day). Retry belongs at the per-meet `/races` level where empty is semantically wrong.

### §5.2 — Correct pacing to the real 5/sec ceiling
**File:** `subscription/racing_api.py` (the `delay` plumbing) and `scripts/backfill_race_metadata.py` constant `BACKLOG_MIN_DELAY` (L111).

- The 1.5s floor (~0.67/sec) is ~7x too slow. Target a sustained rate **at or under 5/sec** single-threaded. Observed per-request latency is ~0.14s, so a delay of ~0.15-0.2s lands comfortably under the ceiling with margin. **Determine empirically:** in the §7 burn, measure achieved req/sec and confirm it stays under 5/sec and produces zero post-retry empties; set the constant to the safe value that testing supports rather than a guessed number.
- Keep it single-threaded (no concurrency) — the ceiling is shared with the live collector, and concurrency would re-create contention.

### §5.3 — De-fang the false wall
**File:** `scripts/backfill_race_metadata.py`, `run_backlog_pass()` wall block (~L288-303) and `BACKLOG_WALL_THRESHOLD` (L107).

- With §5.1 retry in place, a recoverable degraded fetch no longer reaches this block (it's retried inside `sync_day`). A `truncated` result that *survives* retry, or a hard fetch **error** (connectivity/exception), remains a legitimate stop signal.
- Distinguish the two in the log line and the stop condition: a hard connectivity error can still stop the night; a post-retry `truncated` should be rarer and its threshold reconsidered upward (Code's call, reasoned in the report) now that transient degradation is handled upstream. The comment text asserting a "quota/connectivity wall" is corrected to reflect there is no quota.

### §5.4 — Reschedule the nightly timer out of the contention window
**Unit:** `racing-metadata-backfill.timer` (currently `OnCalendar` = 14:00 UTC / 23:30 ACST).

- Move it to a low-contention slot — a window with minimal live AU racing and no live-collector burst. Candidate: **~20:00 UTC (05:30 ACST)**, pre-dawn Adelaide. Code proposes the slot in the report and applies it to the timer unit; the exact time is an operator scheduling preference and may be revised at triage. `daemon-reload` after editing; confirm next-fire with `systemctl list-timers`.
- This is a mitigation, not the fix — §5.1-5.3 make the pass robust *regardless* of slot. Both together is the belt-and-braces.

## §6 — Sequencing within session

5.1 -> 5.2 -> 5.3 -> 5.4, then §7 verification. Rationale: retry (5.1) must exist before pacing (5.2) is tuned, because pacing is validated by the absence of post-retry empties. The wall change (5.3) depends on retry existing. The timer move (5.4) is independent and last. Verification runs against all four in place.

## §7 — Empirical verification

Capture **before** and **after** state so the report shows what moved.

**Baseline (before, `mode=ro`):**
- Total recoverable deficit (the in-scope unfilled-thoroughbred count the code already computes).
- Count of race rows for a chosen historical test window and how many have placings filled.

**Burn (the real test):** run the manual backlog path (`--days` / `--date` range) over a **bounded historical slice of ~40 dates** drawn from the deficit — enough to prove behaviour at scale without attempting the full 41k. During the burn, capture:
- Dates attempted, dates that gained placings, total placings gained.
- Achieved requests/sec (confirm <=5/sec) and count of empty-200s **before** vs **after** retry.
- Whether the pass walls at all, and if so on what (hard error vs post-retry truncated).

**Ghost-row check (the fault-B tripwire, `mode=ro`):** compare race-row counts in the test window before vs after the burn. If the backfill **created new race rows** (rather than filling placings on existing ones), report the count and a few examples with their `race_date` vs `scheduled_start`. This is the signal that fault B is biting and needs its own brief.

**Success =** rows flow at scale (placings gained across the slice), req/sec under ceiling, zero or near-zero post-retry empties, no unexpected wall. Ghost-row creation is *reported*, not a pass/fail gate for this brief.

## §8 — Output spec

Single file: `placings_throughput_fix_report.md` in the bethub-rebuild folder root (same location as prior placings reports).

Sections: (1) what changed, per §5 anchor, with `git diff` excerpts; (2) baseline numbers; (3) burn results table; (4) achieved pace + empty-200 before/after retry; (5) ghost-row check result; (6) the captured degradation headers from §5.1 instrumentation (or a note that no degradation occurred during the burn); (7) self-assessment incl. any hard limits touched and confirmation the dirty-file set is unchanged.

~250-400 lines. Contains **no** recommendations for fault B beyond stating whether the tripwire fired, and **no** overall "recovery is solved" verdict — that's operator-Claude's triage call.

## §9 — Hard limits (non-negotiable)

Code does **not**:
- Touch the `race_date` identity/upsert key, `upsert_race`'s conflict key, or any canonical race-identity logic (fault B — DR-032/034 territory; separate brief).
- Change any schema (no columns, no tables, no indexes).
- Edit any file other than `subscription/racing_api.py`, `scripts/backfill_race_metadata.py`, and the one timer unit.
- Touch the live-capture orchestrator, the Betfair path, or anything on the operational/betting side.
- Attempt the full 41k backlog — the §7 burn is a bounded ~40-date proof, not the clear.
- Run any git write op; edit outside named anchors; escalate mid-session.
- Propose remediation for ghost rows or `race_date` (report the tripwire only).

## §10 — What happens after Code's session

Next operator-Claude session reads `placings_throughput_fix_report.md` and triages:
- If rows flowed clean and the ghost tripwire did **not** fire -> commission a follow-up brief for the full-backlog burn (dedicated mode/timer to walk all deficit dates to zero).
- If the ghost tripwire **did** fire -> fault B (the `race_date` identity-key fix) becomes the priority brief, with a governance check on whether the canonical race-identity key must drop `race_date` (DR-032/034). Code does not write either follow-up; that's the next session's work.

## §11 — Cross-references

- Governing DRs: DR-021 (timestamp anchoring), DR-033 (Betfair operational / Racing API analytical split — this work is analytical side). DR-032 / DR-034 (canonical race identity) are the *excluded* territory (§9).
- Prior artefacts: `race_date_semantics_report.md` (fault B mechanism), `placings_trickle_report.md` (prior recovery design), the 2026-07-01 Chat probe (no-quota + 7.8s clean-date evidence).
- Excluded / parked: full-backlog burn mode, ghost-row / `race_date` identity fix, any rate-tier change pending the theracingapi.com support reply.
