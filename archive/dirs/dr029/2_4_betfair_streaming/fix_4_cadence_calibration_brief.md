# Fix 4 — Cadence calibration brief

**Drafted:** 2026-05-10 ACST (Adelaide local per DR-021)
**Source spec:** `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md`
(Sections 12, 13, 15.3 — Streaming cadence design).
**Empirical input:** `dr029/2_1_race_data/api_probe_report.md`
(Saturday 2026-05-02 probe; cadence-of-meaningful-change tables).
**Predecessor:** W2 betfair_client v1.0 implementation (W2 brief
deferred four cadence parameters as "Fix 4 calibration target"
placeholder constants per W2 brief §5.3).
**Shape:** surgical fix. Closest precedent: W6.1 anomaly_reason_code
surgical amendment (542-line brief, Session 105 ship).
**Status at lock:** awaiting operator review.

---

## §1 What this brief is and is not

Fix 4 commissions Code to **calibrate the placeholder cadence
constants** W2 deferred — replace divergent values with spec-locked
ones, lock spec-aligned values by removing the "Fix 4 calibration
target" tag, consolidate one duplicate constant, verify two
rate-limit defaults against §11, and add tests asserting the locked
values match their cited §-section sources.

This is a **single bounded Code session**. Code reads this brief
end-to-end, executes against named anchors only, and produces one
report at the named output path. Surprises become §6 deviations
or §7 findings, not blockers. Remediation routes to operator-Claude
triage in the next session, never inside Code's report.

Specifically in scope:

- **Two divergent placeholders fixed.** `CACHE_STALE_THRESHOLD_SECONDS`
  in `streaming.py` and `live_pricing.py` is currently 30s; §2.4
  §12.4 says staleness fires at 2× heartbeatMs = 10s. Change to 10s
  in both files. `SUSTAINED_RECONNECT_FAILURE_THRESHOLD` in
  `streaming.py` is currently 5 (count of attempts); §2.4 §15.3 says
  escalate after 60 seconds of cumulative failure. Replace the
  count-based threshold with a time-based 60-second threshold
  (semantic change, not just a value swap).
- **Four spec-aligned placeholders locked.** Remove the "Fix 4
  calibration target" comment tag from `HEARTBEAT_LOSS_THRESHOLD_SECONDS`,
  `RECONNECT_BACKOFF_INITIAL_SECONDS`, `RECONNECT_BACKOFF_MAX_SECONDS`,
  `CACHE_FRESHNESS_TARGET_SECONDS` in `streaming.py`. Replace with
  per-constant comment citing the §-section that locks the value
  (§12.5 / §15.3 / §15.3 / §12.2 respectively).
- **One duplicate constant consolidated.** `live_pricing.py`'s local
  `CACHE_STALE_THRESHOLD_SECONDS = 30` is a duplicate of the
  `streaming.py` constant. Remove the local definition; import from
  `streaming.py`. The two files stay in sync by construction.
- **Two `RateLimitBudget` defaults verified.** `_connection.py`'s
  `max_calls_per_window: int = 200` and `window_seconds: int = 60`
  are flagged as Fix 4 calibration targets. Verify against §2.4 §11
  and the on-disk Betfair API reference. If defaults fall within
  Betfair's documented ceilings, lock and remove the "Fix 4
  calibration target" comment. If they don't, surface as a §6
  deviation with proposed values; do not silently change.
- **Tests added** asserting locked constants match their §-section
  citations, the reconnect back-off sequence matches §15.3, the
  cache-stale threshold equals 2× the freshness target, and the
  sustained-failure threshold escalates at 60 seconds rather than
  on count.

Specifically not in scope (see §9 hard limits for the full list):

- No subscribe-interval constant. W2's brief listed "subscribe
  interval" as one of four cadence targets, but in v3 today
  subscriptions are call-driven (`subscribe_markets()` invoked
  when a market enters the day's race programme, not on a timer);
  there is no `SUBSCRIBE_INTERVAL` constant to calibrate. The
  brief's §11 cross-references close this loop explicitly.
- No REST per-phase polling cadence constants
  (STANDARD/INTENSIVE/POST_START/SUSPENDED/CLOSED). The probe
  report has cadence-of-meaningful-change numbers per phase, but
  v3 has no code path consuming them today — `live_pricing.py`
  prefers Streaming and falls through to a one-shot REST read on
  cache-stale, not a polling loop. Documented in §11 cross-
  references for whenever a v3 surface adds REST polling.
- No orchestrator-side cadence change. The VPS scraper's INTENSIVE
  cadence (60s vs probe-supported 1s) is analytical-line concern;
  Session 81 Trade-off B parked it until v3 build proper makes the
  orchestrator's cadence less load-bearing. Out of scope here.
- No jump-anchor design changes (`marketTime` mutability, market-
  status transitions as race-state signal). Session 81 Trade-off
  C reframed this as W4/W5 design substance, not Fix 4.
- No rate-limit re-tuning beyond the §5.3 verification. If §11
  surfaces a divergence, it's a §6 deviation flagged to triage,
  not a fix.
- No changes to `streaming.py` / `live_pricing.py` / `_connection.py`
  business logic, type shapes, function signatures. Constants
  and comments only. The state machine, cache shape, message
  loop, reconnection logic, rate-limit budget mechanics — all
  unchanged.
- No new Pydantic models, no new functions, no new public API.
- No edits outside the four named files (the three production
  files plus the test file).
- No git operations (no `git add` / `git commit` / `git stash` /
  etc.). Dirty-tree state is preserved per existing W4 + W6 +
  W6.1 + W6.5 + W7 + W8 + W9 ship pattern.
- No Alembic migrations. No DB writes. No live Betfair API calls.

This is the smallest brief surface in the v3 build line. Constants
move; tests assert; comments cite. The reason it earns a brief
rather than ad-hoc edits is the discipline cost of spec-source
attribution and the test coverage of the calibration — both worth
locking through Code's bounded-session workflow.

## §2 Why this work exists

W2 (the betfair_client v1.0 implementation, brief at
`dr029/w2_betfair_client/w2_brief.md`) deferred four named cadence
parameters as "Fix 4 calibration target" placeholders. Per W2 brief
§5.3 (lines 481-490):

> Cadence parameters not specified. Per contract §10 and Fix 4
> deferral: heartbeat threshold, subscribe interval, reconnect
> back-off cadence, and polling cadence outside burst windows are
> operational tuning deferred to v3 build proper. W2 implements
> the *shape* (state machine, message-loop scaffolding,
> reconnection-trigger logic) with placeholder constants for the
> timing parameters that will be calibrated post-Fix-4. The
> placeholders are documented in module docstrings as "Fix 4
> calibration target."

Session 81 closed Fix 4 as a separate artefact (Trade-off A
resolution: "drop Fix 4 as a separate artefact; W2's eventual
brief reads §2.4 + probe report directly for cadence numbers").
That close-out plan didn't execute at W2 brief drafting time —
W2 deferred cadence as placeholders rather than consuming §2.4 +
probe directly. The deferral propagated through W3 → W4 → W6 →
W6.5 → W7 → W8 → W9 without revisiting; the placeholder constants
remain unspecified-vs-spec in v3 today.

Operationally: the placeholders aren't bleeding EV today because
v3 isn't operationally live (no real bet flow, mocked-only tests).
On the day v3 takes its first real bet, the cadence values
determine whether v3 is fast and alert when it matters (markets
approaching jump, value-hunting) and cheap and quiet when it
doesn't (markets hours away). Wrong values mean v3 either
(a) bets on stale prices because the staleness threshold lets
30-second-old reads through, or (b) gives up on a flaky connection
too early because the failure threshold escalates after ~31
seconds rather than the spec-named 60.

Fix 4 closes this gap before v3 goes live, so the day v3 takes
its first real bet the cadence surface is properly tuned.

Empirical inputs are both locked and on disk:

- §2.4 spec (sections 12.2, 12.4, 12.5, 13.5, 15.3) names each
  parameter and its operational role with derivations.
- Saturday 2026-05-02 probe report (`dr029/2_1_race_data/
  api_probe_report.md`) has empirical numbers from 10-hour live
  observation across four AU races (2 thoroughbred, 1 harness,
  1 greyhound).

For each placeholder constant: read what §2.4 says, cross-check
against the probe where applicable, pick the value, write the
reasoning in the comment, lock with a test.

## §3 Pre-reads

Required reads (in order, before drafting any code change):

1. `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md` —
   §12.2 (heartbeat cadence — locks `heartbeatMs=5000`),
   §12.4 (the cadence the burst UI sees — locks staleness at 2×
   heartbeatMs = 10s),
   §12.5 (cadence floor for operational fitness — locks 10s of
   total silence as connection-death detection),
   §13.5 (per-phase change rates — informs out-of-scope REST-
   polling notes, not the constants in scope),
   §15.3 (reconnection back-off and escalation — locks 1/2/4/8/16/30
   back-off sequence, capped at 30s, escalate at 60s of sustained
   failure).
2. `dr029/2_1_race_data/api_probe_report.md` — §3.4 (cadence-of-
   meaningful-change at 1-second granularity, per-phase tables for
   thoroughbred / harness / greyhound). The probe doesn't directly
   constrain the in-scope constants (those are spec-derived from
   §2.4); it constrains the out-of-scope REST per-phase polling
   cadence numbers documented in §11 cross-references.
3. `dr029/w2_betfair_client/w2_brief.md` — §5.3 (Streaming surface,
   the deferral that established the "Fix 4 calibration target"
   tag pattern).
4. `dr029/2_4_betfair_streaming/betfair_stream_api_reference.md` —
   the on-disk Betfair Streaming API reference. Section 11 reads
   on rate limits cross-reference this. Used for §5.3 verification.
5. `clients/betfair_client/v1/streaming.py` (595 lines) — the file
   carrying the six in-scope constants. Anchor on lines 54-60
   (the "Fix 4 calibration targets" comment block plus the six
   constants).
6. `clients/betfair_client/v1/live_pricing.py` (207 lines) — the
   file carrying the duplicate `CACHE_STALE_THRESHOLD_SECONDS`
   constant. Anchor on lines 41-44.
7. `clients/betfair_client/v1/_connection.py` (104 lines) — the
   file carrying `RateLimitBudget` defaults. Anchor on lines
   42-52 (the dataclass definition and its comment block).
8. `tests/clients/betfair_client/v1/test_streaming.py` (349 lines)
   — the test file Code extends with the new constant-value and
   sequencing assertions. Read structure of existing tests; new
   tests follow the same shape.

Reference-only (consult on demand, not required cover-to-cover):

- `decisions.md` — DR-021 (timestamp anchoring), DR-027 (two-
  database architecture), DR-030 (v3 repo layout / module-boundary
  discipline), DR-031 (v3 tech stack — pytest, ruff,
  lint-imports).
- `sessions/SESSION_80.md` and `sessions/SESSION_81.md` —
  Session 81 close-out resolution on Fix 4 (Trade-off A drop,
  Trade-off B park, Trade-off C document-and-close).
- `dr029/dr029_scope.md` — §2.4 in-scope item.
- `external_api_resources.md` — pointer set for Betfair Exchange
  API documentation (used if §11 verification needs to consult
  Betfair's published rate-limit numbers).

## §4 System access

- **Filesystem (read-write):** Mac local at
  `/Users/tim/Desktop/Projects/bethub-v3/`. Edit anchors named
  in §5 only — three production files plus one test file.
- **Working tree:** dirty per W6 + W6.1 + W6.5 + W7 + W8 + W9
  ship pattern. Operator's in-flight work has not landed since
  W9. Pre-baseline `git status` capture at session start; post-
  baseline `git status` capture at session close. The dirty-file
  list does not change across the session — Fix 4's edits land
  inside the existing untracked `clients/betfair_client/v1/`
  namespace and the existing untracked `tests/clients/betfair_client/v1/`
  namespace.
- **Python interpreter:** `.venv/bin/python` (3.12.7) per W6.1 /
  W6.5 / W8 / W9 precedent. Invoke via the venv interpreter
  explicitly (W6 §8.1 finding mitigation).
- **Tests:** `pytest` from the venv. Pre-baseline run at session
  start to establish the count (expected 519 from W9 ship per
  W9 report §3); post-baseline run at session end to verify net-
  new test delta.
- **No git operations.** No `git add`, `git commit`, `git stash`,
  `git restore`, `git checkout`, `git reset`. Brief edits land
  inside already-untracked files.
- **No live Betfair API calls.** All work is constant-value
  changes, comment edits, and test assertions against in-process
  values.
- **No DB access.** Fix 4 doesn't touch storage, schema, or any
  database surface.
- **Adelaide local timestamps per DR-021** — all session
  timestamps and log lines.

## §5 Substantive scope sections

§5 names every change Fix 4 makes. Anchors are file + region.
Code edits only what's named here.

### §5.1 — `streaming.py` cadence constants (the load-bearing block)

**File:** `clients/betfair_client/v1/streaming.py`
**Region:** lines 53-60 (the "Fix 4 calibration targets" comment
block plus the six constants immediately below it).

Six constants live in this block. Two diverge from spec (Changes
A and B), four are spec-aligned and need locking (Change C).

**Change A — `CACHE_STALE_THRESHOLD_SECONDS`: 30 → 10.**

Current (line 60):

```python
CACHE_STALE_THRESHOLD_SECONDS = 30
```

Replace with:

```python
# Per §2.4 §12.4: stale = 2× heartbeatMs (5s × 2 = 10s).
# Cache-stale fires when no message has been received within
# this window — connection-death backstop, not freshness.
CACHE_STALE_THRESHOLD_SECONDS = 10
```

Rationale: §2.4 §12.4 ("the cadence the burst UI sees") explicitly
defines `stale` as "no message has been received within 2× heartbeatMs."
With `heartbeatMs=5000` (per §12.2), the staleness window is 10s,
not 30s. The 30s placeholder gives v3 a 3× more lax threshold —
v3 would treat a feed as fresh for up to 30s with no messages,
well past §2.4's connection-death detection window of 10s. Bringing
the threshold to 10s aligns with the spec's intent: surface
degradation early, fall back to REST or alert the operator before
prices drift.

**Change B — `SUSTAINED_RECONNECT_FAILURE_THRESHOLD`: count → time.**

Current (line 59):

```python
SUSTAINED_RECONNECT_FAILURE_THRESHOLD = 5
```

This is a count of consecutive failed reconnect attempts. Replace
with a time-based 60-second cumulative-failure threshold:

```python
# Per §2.4 §15.3: escalate after 60 seconds of cumulative
# reconnect failure. With back-off sequence 1/2/4/8/16/30
# (capped) the count varies by where the back-off is in the
# sequence; threshold is *time*, not *attempts*.
SUSTAINED_RECONNECT_FAILURE_WINDOW_SECONDS = 60
```

Rename the constant from `..._THRESHOLD` (count semantics) to
`..._WINDOW_SECONDS` (time semantics) to make the change explicit
at every call site; remove the old name entirely. Update call
sites accordingly — the failure path now compares
`time_since_first_failure >= SUSTAINED_RECONNECT_FAILURE_WINDOW_SECONDS`
rather than `attempt_count >= SUSTAINED_RECONNECT_FAILURE_THRESHOLD`.

Rationale: the §15.3 spec is explicit on the time threshold:
"if Streaming has not successfully reconnected within 60 seconds
of the first failure, v3 surfaces a hard operator-facing alert."
The count-based 5-attempt threshold escalates on the same flaky
network at ~31s (back-off cumulative 1+2+4+8+16=31 by the 5th
attempt) — too fast on a transiently degraded link. Time-based
threshold is what §15.3 names; the existing call sites need the
straightforward semantic update.

**Change C — Comment block update + locked-citation comments.**

Lines 53-55 currently read:

```python
# ---------------------------------------------------------------------------
# Fix 4 calibration targets (per contract §10 + brief §5.3)
# ---------------------------------------------------------------------------
```

Replace the section header with:

```python
# ---------------------------------------------------------------------------
# Cadence constants (locked Fix 4 cadence calibration brief,
# Session 113. Sources: §2.4 spec sections cited per constant.)
# ---------------------------------------------------------------------------
```

Above each of the four spec-aligned constants, add a one-line
comment citing the §-section that locks the value:

```python
# Per §2.4 §12.5: 2× heartbeatMs (5s × 2 = 10s) — connection-
# death detection. Two consecutive missed heartbeats means the
# stream is dead.
HEARTBEAT_LOSS_THRESHOLD_SECONDS = 10

# Per §2.4 §15.3: first reconnect attempt is immediate; back-off
# sequence 1/2/4/8/16/30s (this constant is the first non-immediate
# step).
RECONNECT_BACKOFF_INITIAL_SECONDS = 1

# Per §2.4 §15.3: back-off capped at 30s — keeps v3 below
# Betfair's TOO_MANY_REQUESTS connection-rate ceiling.
RECONNECT_BACKOFF_MAX_SECONDS = 30

# Per §2.4 §12.2: heartbeatMs=5000 — minimum interval at which
# v3 receives a ChangeMessage even if no underlying change. The
# freshness target equals the heartbeat cadence.
CACHE_FRESHNESS_TARGET_SECONDS = 5
```

Constants A and B from above get their own citation comments per
the new pattern.

The "Fix 4 calibration target" tag is gone everywhere in the file
after this change. The values are spec-locked, with citation in
place for any future reader.

**Module docstring** (lines 11-16) currently reads:

```python
"""
...
Cadence parameters (subscribe interval, reconnect back-off, heartbeat
threshold, polling cadence outside burst windows) are Fix 4 calibration
targets per contract §10. Placeholder constants are tagged below.
"""
```

Replace the cadence sentence with:

```python
Cadence constants are locked (Fix 4 cadence calibration brief,
Session 113). Sources cited per constant in the cadence-constants
block below. Subscribe interval is not a constant — subscriptions
are call-driven (`subscribe_markets()` invoked per market entering
the day's race programme), not periodic. REST per-phase polling
cadence is not a v3 constant today — `live_pricing.py` prefers
Streaming and falls through to one-shot REST on cache-stale; if
v3 ever adds polling-loop REST, the probe-derived per-phase
numbers live in §13.5 of the §2.4 spec.
```

This closes the W2 framing loop on "subscribe interval" and the
out-of-scope REST per-phase cadence numbers within the file's
own documentation.

### §5.2 — `live_pricing.py` duplicate constant consolidation

**File:** `clients/betfair_client/v1/live_pricing.py`
**Region:** lines 41-44.

**Change A — Delete local constant.** Remove:

```python
# Fix 4 calibration target: cache-vs-REST staleness threshold lives in
# `streaming.py` (cache-side concept). REST returns `fresh` by definition
# per contract §4 — `stale` is a streaming-cache surface only.
CACHE_STALE_THRESHOLD_SECONDS = 30
```

**Change B — Import from `streaming.py`.** At the top of the file
where existing imports live, add:

```python
from .streaming import CACHE_STALE_THRESHOLD_SECONDS
```

Position alphabetically among the `from .streaming import ...`
existing imports if any; otherwise add a fresh `from .streaming
import ...` line in alphabetical order with other intra-package
imports.

**Change C — Update module docstring** (lines 14-16) which currently
reads:

```python
"""
...
Cadence parameters (cache-vs-REST freshness threshold) deferred to Fix 4 —
the placeholder constants are tagged below.
"""
```

Replace the cadence sentence with:

```python
Cache-vs-REST freshness threshold is sourced from `streaming.py`'s
`CACHE_STALE_THRESHOLD_SECONDS` (locked at 10s per §2.4 §12.4).
The two files stay in sync by construction — there is no
`live_pricing.py`-local copy.
```

After §5.2 lands, the constant is single-sourced in `streaming.py`;
`live_pricing.py` references it via import. The "Fix 4 calibration
target" tag is gone from `live_pricing.py`.

### §5.3 — `_connection.py` rate-limit verification

**File:** `clients/betfair_client/v1/_connection.py`
**Region:** lines 41-52 (the `RateLimitBudget` dataclass and its
comment block).

**Change A — Verify defaults against §2.4 §11 + on-disk Betfair
reference.** Read `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md`
§11.1 through §11.6 plus the on-disk Betfair Streaming API
reference (§3 pre-reads item 4) for documented rate-limit ceilings
on REST endpoints (`listMarketBook` / `listRunnerBook` / placement /
cancel / replace) and Streaming.

The current defaults are:

```python
max_calls_per_window: int = 200
window_seconds: int = 60
```

Compare against the documented Betfair ceilings. Two outcomes:

- **If 200/60s falls within Betfair's documented ceilings** (the
  expected case — Betfair's published baseline is 5 transactions/sec
  across reads + writes per app key, which is 300 calls/60s; 200/60s
  is conservative against that), update the comment to lock the
  values:

  ```python
  # Per §2.4 §11: Betfair's published baseline is roughly
  # 5 transactions/sec per app key (≈300/60s); v3 stays well
  # below that with a 200/60s budget. The window-based shape
  # absorbs short bursts without breaching the ceiling on
  # average. Adjustable per §11 if Betfair's ceilings change
  # for v3's app key.
  max_calls_per_window: int = 200
  window_seconds: int = 60
  ```

  Remove the "Fix 4 calibration target" tag from the dataclass
  docstring. Lock the values.

- **If §11 / Betfair reference says the defaults are wrong** (not
  expected, but possible), do NOT silently change the values —
  surface as a §6 deviation in the report with the proposed
  values plus the §-section citation, and leave the production
  values untouched until Session 113 triage routes the change.

**Change B — Update the dataclass docstring** (lines 44-49):

Currently reads:

```python
"""Cheap operator-visible budget tracker. Per contract §7 the rate-limit
awareness lives inside `betfair_client`; v3 modules never see it.

Cadence numbers (window length, max calls per window) are Fix 4
calibration targets — placeholder defaults here.
"""
```

Replace the second paragraph with (assuming Change A's expected
outcome — the verification confirms defaults are within Betfair's
ceilings):

```python
"""Cheap operator-visible budget tracker. Per contract §7 the rate-limit
awareness lives inside `betfair_client`; v3 modules never see it.

Window length and max-calls-per-window are sourced from §2.4 §11
(Betfair's published baseline ≈5 transactions/sec per app key).
The 200/60s defaults sit conservatively below that ceiling.
"""
```

If Change A surfaces a §6 deviation, leave the docstring's "Fix 4
calibration target" tag in place pending triage.

### §5.4 — Tests

**File:** `tests/clients/betfair_client/v1/test_streaming.py`

The test module currently runs ~30 tests covering the streaming
state machine, message-loop, and cache. Fix 4 adds a new test
block at the bottom of the file: `# --- Fix 4 cadence-constant
locks ---` plus 8 tests.

**Block A — Constant-value-vs-spec assertions (4 tests):**

1. `test_heartbeat_loss_threshold_is_2x_heartbeat_ms` —
   `HEARTBEAT_LOSS_THRESHOLD_SECONDS` equals 10; assert via
   computation: `2 * HEARTBEAT_MS_REQUESTED // 1000` (where the
   heartbeat-ms-requested is the existing constant or
   subscription parameter Code can reference). Ties the value
   to its derivation rather than hard-coding 10.
2. `test_cache_stale_threshold_is_2x_freshness_target` —
   `CACHE_STALE_THRESHOLD_SECONDS == 2 * CACHE_FRESHNESS_TARGET_SECONDS`.
   Asserts the relationship §12.4 names rather than the raw
   value.
3. `test_reconnect_backoff_initial_is_1s_and_max_is_30s` —
   asserts both back-off endpoints; cited to §15.3.
4. `test_sustained_reconnect_failure_window_is_60s` —
   `SUSTAINED_RECONNECT_FAILURE_WINDOW_SECONDS == 60`; cited to
   §15.3.

**Block B — Reconnect back-off sequence test (2 tests):**

5. `test_reconnect_backoff_sequence_matches_section_15_3` —
   given the back-off function (existing in `streaming.py`'s
   reconnection logic), assert the sequence emitted on
   successive failures is 1, 2, 4, 8, 16, 30, 30, 30, ... per
   §15.3. Captured as a list comparison: `actual == [1, 2, 4,
   8, 16, 30, 30, 30]` for 8 attempts.
6. `test_reconnect_backoff_caps_at_max_after_5_doublings` —
   the 6th non-immediate attempt's back-off is capped at
   `RECONNECT_BACKOFF_MAX_SECONDS`. Defensive against any future
   change to the doubling-cap mechanic.

**Block C — Sustained-failure window test (2 tests):**

7. `test_sustained_failure_escalation_at_60s_window` —
   simulate 7 successive reconnect failures with cumulative
   wall-clock time crossing 60s; assert the sustained-failure
   alert path fires (existing alert mechanism in `streaming.py`
   — Code locates the call site).
8. `test_sustained_failure_no_escalation_below_60s` —
   simulate 5 successive reconnect failures with cumulative
   time at ~31s (1+2+4+8+16); assert the sustained-failure
   alert path does NOT fire (count alone is insufficient;
   threshold is time).

The two Block C tests are the test-side load-bearing for §5.1
Change B (the count-to-time semantic shift). Without them the
test suite would silently accept a regression back to count-based
threshold.

**Test count delta target: +8 net new tests** (519 → 527).
Acceptable band: 527-531 (+8 to +12) — Code may produce up to
4 additional tests for natural test boundaries surfacing during
write (e.g. an explicit live_pricing.py import test, or a
defensive test for the constant rename ensuring the old name
doesn't reappear). Flag in §6 deviation if outside the band.

### §5.5 — `live_pricing.py` test touch (light)

**File:** `tests/clients/betfair_client/v1/test_live_pricing.py`

Verify the existing 145-line test file still passes after §5.2's
import change. No new tests required — the existing tests cover
the cache-vs-REST boundary and read against the imported value
transparently.

If any existing test depends on the local `CACHE_STALE_THRESHOLD_SECONDS`
shape (e.g. patches it via module attribute), Code adjusts the
patch target to the imported source (`streaming.CACHE_STALE_THRESHOLD_SECONDS`)
rather than `live_pricing.CACHE_STALE_THRESHOLD_SECONDS`. Surface
in §5 implementation note if any patches needed adjustment.

## §6 Sequencing within session

Code's session walks in dependency order:

1. **`streaming.py` first** (§5.1) — the load-bearing changes.
   Two value changes (Changes A and B), one comment-block update
   (Change C), one module-docstring update. Internal call-site
   updates for the count-to-time rename happen as part of Change
   B (Code locates the `SUSTAINED_RECONNECT_FAILURE_THRESHOLD`
   references inside the file — there should be 1-3 of them in
   the reconnect path — and updates each).
2. **`live_pricing.py`** (§5.2) — duplicate consolidation. Depends
   on Change A from §5.1 (the constant in `streaming.py` is now
   the source of truth at value 10). Three changes (delete local,
   import, docstring update).
3. **`_connection.py`** (§5.3) — rate-limit verification. Independent
   of §5.1 and §5.2; can land in any order. Two outcomes (lock or
   defer to §6 deviation per Change A logic).
4. **Tests** (§5.4 and §5.5) — depend on §5.1, §5.2, §5.3 landing.
   Block A (constant-value assertions), Block B (back-off sequence),
   Block C (sustained-failure window) in `test_streaming.py`.
   `test_live_pricing.py` runs unchanged but verified.
5. **Verification** (§7) — pre/post baselines on test count, ruff,
   lint-imports.

The order is intentional. The duplicate consolidation in §5.2 reads
from `streaming.py`'s now-locked value; the test assertions reference
the now-renamed `SUSTAINED_RECONNECT_FAILURE_WINDOW_SECONDS` constant
at the new name. If a different order surfaces during execution as
cleaner, Code may deviate; flag the deviation in §6 of the report
with the reasoning.

## §7 Empirical verification

### §7.1 — Pre-baseline (session open)

Capture all of the following:

- `pytest --collect-only -q | tail -1` — pre-baseline test count.
  Expected: 519 (W9 ship state per W9 report §3).
- `pytest -q` — full-suite pass/fail. Expected: 519 passed.
- `ruff check clients/betfair_client/v1/ tests/clients/betfair_client/v1/`
  — clean.
- `lint-imports` — 5 contracts kept, 0 broken (W9 ship: 120
  files, 338 dependencies).
- `git status` — capture the dirty-file list. No `git add` /
  `git commit` / `git stash` allowed; the snapshot is for the
  report's §9 self-assessment.

### §7.2 — Post-baseline (session close)

Re-run all of §7.1's commands.

Expected post-baseline:

- Test count: ~527 (+8 net new). Acceptable band: 527-531
  (+8 to +12); flag in §6 if outside the band.
- Full-suite pass: all green.
- `ruff check` clean.
- `lint-imports` 5 kept, 0 broken. Files / dependencies count
  unchanged — the new import in `live_pricing.py` is intra-
  package (`.streaming`), already present in the import graph,
  not a new edge.
- `git status` — same dirty-file list at the file level. No new
  untracked files at the root level. No modifications outside
  the named §5 anchors.

### §7.3 — Functional verification checklist

Code confirms in the report's §9 self-assessment:

- [ ] All `tests/clients/betfair_client/v1/test_streaming.py`
      pass (existing + new Block A + B + C tests).
- [ ] `tests/clients/betfair_client/v1/test_live_pricing.py`
      still passes (no regressions from §5.2 import change).
- [ ] All other `tests/clients/betfair_client/v1/` tests still
      pass (no regressions from any constant change).
- [ ] All `tests/workflows/` and `tests/ui/` tests still pass
      (downstream consumers of `betfair_client` are unaffected
      because none of them reference the cadence constants
      directly).
- [ ] Full suite passes.
- [ ] `ruff check` clean.
- [ ] `lint-imports` 5 contracts kept, 0 broken.
- [ ] No live Betfair API calls (constants and tests only).
- [ ] No edits outside the §5 named anchors.
- [ ] No new untracked files.

### §7.4 — Sample verification

The report's §9 captures one verification block showing the
locked constants in their final state — module-level imports of
`streaming.py`'s constant block, plus the `live_pricing.py`
re-export pattern, plus the `_connection.py` `RateLimitBudget`
defaults — confirming the wire shape Session 113's Fix 4 triage
will read against.

## §8 Output spec

**Path:** `dr029/2_4_betfair_streaming/fix_4_cadence_calibration_report.md`
(absolute: `/Users/tim/Desktop/Projects/bethub-rebuild/dr029/
2_4_betfair_streaming/fix_4_cadence_calibration_report.md`).

**Length range:** 300-500 lines. Surgical-fix shape, smaller than
W6.1 (305-line report) on the lower end and not larger than W6.5
(850-line report). Constant-value calibration plus 8 tests plus
verification blocks should sit comfortably in the 300-500 band.
Flag in §9 self-assessment if outside the band.

**Required structure:**

- **§1 Summary** — what shipped end-to-end in one paragraph plus
  the named-anchor checklist (Changes A-C across §5.1, A-C across
  §5.2, A-B across §5.3, Block A/B/C across §5.4, §5.5 verified).
  Test count delta. ruff / lint-imports state.
- **§2 Files changed** — table of pre/post LOC for every file
  touched. No new files (this is a constant-calibration brief;
  edits land inside `streaming.py`, `live_pricing.py`,
  `_connection.py`, and `test_streaming.py`).
- **§3 Test count delta** — exact pre and post numbers, the +N
  delta, any band-flag.
- **§4 New tests added** — listed by block (A/B/C per §5.4)
  with one-line description per test.
- **§5 Implementation notes** — one sub-section per §5.x anchor.
  What landed, any inline decisions taken. The §5.3 Change A
  outcome (locked vs surfaced as §6 deviation) is restated
  explicitly in the implementation note for visibility.
- **§6 Deviations from brief** — any deviation from the §5
  anchors, the §6 sequencing, or the test-count band. Expected:
  zero or one (the §5.3 Change A outcome is the most likely
  deviation surface).
- **§7 Open questions for triage** — anything Code surfaced that
  the next operator-Claude session needs to resolve. Expected:
  zero or one.
- **§8 Findings beyond brief scope** — anything Code noticed
  during execution that wasn't anchored in the brief but warrants
  surfacing. Expected: zero or one.
- **§9 Self-assessment** — pre/post baselines table per §7.1 /
  §7.2; functional verification checklist per §7.3 (10 items
  ticked); `git status` snapshots; length flag; DR-021 timestamp
  confirmation; sample verification per §7.4.

**What the report does not contain:**

- No recommendations for what to do next. Forward routing is
  Session 113's call.
- No proposals for fixes outside the brief's scope.
- No design changes from the §5 anchors. Anchor-level changes
  surface as §6 deviations.
- No `git` operations in the implementation notes.

## §9 Hard limits

Non-negotiable. Code does not, under any circumstances:

- **Modify business logic, type shapes, or function signatures.**
  Constants and comments only. The state machine, cache shape,
  message loop, reconnection logic, rate-limit budget mechanics —
  all unchanged.
- **Add new constants, new Pydantic models, new functions, new
  public API.** The brief calibrates existing constants; it does
  not introduce new surface.
- **Add a `SUBSCRIBE_INTERVAL` constant.** Subscriptions are
  call-driven in v3; there is no subscribe interval to calibrate.
  Closing this loop is part of the module-docstring update in
  §5.1 Change C, not a new constant.
- **Add REST per-phase polling cadence constants** (STANDARD /
  INTENSIVE / POST_START / SUSPENDED / CLOSED). The probe report
  has these numbers; v3 has no code path consuming them today.
  Out of scope; documented in §5.1 Change C module docstring.
- **Touch the orchestrator-side cadence** at all. The VPS
  scraper's INTENSIVE cadence is analytical-line concern, not
  v3-client concern. Out of scope per Session 81 Trade-off B.
- **Touch any jump-anchor design surface** (`marketTime`,
  market-status transitions). W4/W5 substance per Session 81
  Trade-off C reframe; not Fix 4 territory.
- **Re-tune `RateLimitBudget` defaults** beyond the §5.3
  verification. If §11 surfaces a divergence, surface as §6
  deviation; do not silently change values.
- **Edit `decisions.md`, `architecture.md`, `governance.md`,
  `standing_instructions.md`, `current_state.md`,
  `v3_build_picture.md`, or any rebuild-folder governance file.**
  Code-side governance touches are Chat-territory. Specifically:
  closing `governance.md` §4's Fix 4 deferred-capability entry,
  removing stale Fix 4 references from `current_state.md`, and
  updating `v3_build_picture.md` if relevant — all Chat-side
  work in Session 113.
- **Edit `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md`**
  or any other `dr029/` document. The spec is the source; the
  brief consumes it.
- **Edit `clients/betfair_client/v1/` files outside the three
  named in §5** (`streaming.py`, `live_pricing.py`,
  `_connection.py`). The other modules in this directory are
  unaffected by Fix 4.
- **Edit `clients/vps_client/`, `workflows/`, `ui/`, or any
  module outside `clients/betfair_client/v1/`.** Fix 4 is
  contained to the betfair_client v1 surface.
- **Run `git add` / `git commit` / `git stash` / `git restore` /
  `git checkout` (file-targeted) / `git reset`.** Dirty-tree
  state is preserved; `git status` is read-only.
- **Make live Betfair API calls.** All work is constant edits
  and test assertions; nothing hits a network.

If the brief's anchors and the live codebase diverge — for
example, a §5 anchor has moved, a constant has been renamed by
intervening work, a test fixture is missing — Code surfaces the
mismatch as a §6 deviation in the report and stops at the
affected anchor; the remaining anchors that don't depend on the
affected one continue. The next operator-Claude session resolves
the mismatch.

## §10 What happens after Code's session

The next operator-Claude session (Session 113 by current
sequencing) runs Fix 4 report triage via the inventory-first
cadence pattern (sweep candidate `(l)`):

1. Read the Fix 4 report end-to-end.
2. Inventory pass — classify §6 deviations, §7 open questions,
   §8 findings as no-call (Code's territory, awareness only) or
   operator-call (warrants routing).
3. Walk operator-call items one-per-round. Resolve each.
4. Governance hygiene (Chat-side, same session if budget allows
   or split into a follow-up):
   - Close `governance.md` §4's Fix 4 deferred-capability entry
     (capability §3) — Fix 4 closes here; the entry was flagged
     stale at Session 81 Trade-off A close.
   - Remove stale "Fix 4 cadence brief" references from
     `current_state.md` carry-forward sections.
   - Verify `v3_build_picture.md` — Fix 4 was never explicitly
     a build-picture stream, so likely no change needed.
   - Reconcile the Fix 5 "venue harmonisation" deferred-capability
     entry in `governance.md` §4 (capability §4) which has been
     stale since Session 46 ship, flagged Session 80, never
     reconciled.
5. Forward routing: Fix 4 closes the §2.4 cadence-constant gap.
   Remaining DR-029 surfaces:
   - **v3-build-proper re-cut work** — multi-session arc, ready
     to start.
   - **Standing-instruction sweep** — multiple Cat 1 candidates
     accumulated; dedicated fresh-mind session.

Code does not produce the next brief. Forward routing is the
next session's work.

## §11 Cross-references

**Source spec:** `dr029/2_4_betfair_streaming/2_4_betfair_streaming.md`
(2821 lines). Primary anchors — §12.2 (heartbeat cadence),
§12.4 (the cadence the burst UI sees), §12.5 (cadence floor for
operational fitness), §15.3 (reconnection back-off and
escalation), §11 (rate-limit and data-limit handling).

**Empirical input:** `dr029/2_1_race_data/api_probe_report.md`
(365 lines). §3.4 (cadence-of-meaningful-change tables) — informs
the out-of-scope REST per-phase polling cadence numbers documented
in §5.1 Change C module docstring; does not directly constrain
in-scope constants.

**Predecessor brief:** `dr029/w2_betfair_client/w2_brief.md`.
§5.3 establishes the "Fix 4 calibration target" placeholder
pattern Fix 4 closes.

**Active governing DRs:**
- DR-021 (timestamp anchoring, Adelaide local time) — applies
  to every test fixture, every log line, every session
  timestamp.
- DR-027 (two-database architecture) — context only. Fix 4
  doesn't touch storage.
- DR-030 (v3 repo layout / module-boundary discipline) —
  load-bearing for the §5.2 import (`from .streaming import
  CACHE_STALE_THRESHOLD_SECONDS` is intra-package, satisfies
  module-boundary discipline).
- DR-031 (v3 tech stack) — load-bearing (pytest, ruff,
  lint-imports).

**Predecessor sessions:**
- Session 80 — surfaced the Fix 4 deferral, framed three
  trade-offs.
- Session 81 — Trade-off A (drop separate artefact, W2
  consumes §2.4 + probe), Trade-off B (orchestrator parked),
  Trade-off C (`marketTime` documented-and-closed; jump-anchor
  reframe parked for W4/W5). Session 81's Trade-off A close-out
  did not execute at W2 brief drafting time — Fix 4 reopens via
  the surgical-fix brief shape rather than the in-W2 inline
  shape.

**Out-of-scope items called out for clarity:**
- Subscribe interval. W2 framing was loose; v3 has no
  `SUBSCRIBE_INTERVAL` constant because subscriptions are call-
  driven (`subscribe_markets()` per market entering the day's
  programme), not periodic. Resolved in §5.1 Change C module
  docstring.
- REST per-phase polling cadence (STANDARD: 30-60s, INTENSIVE:
  1s, POST_START: 1s, SUSPENDED: 5s+, CLOSED: 30s × 5min then
  stop). Probe-derived per §13.5 of §2.4 spec; no v3 code path
  consumes these today.
- Orchestrator-side cadence (analytical-line, Session 81
  Trade-off B parked).
- Jump-anchor design (`marketTime` mutability, market-status
  transition reframe). W4/W5 substance per Session 81
  Trade-off C.
- Rate-limit re-tuning beyond §5.3 verification.

**Carry-forward items this brief logs:**
- W6 §8.1 finding — `requires-python = ">=3.12"` venv
  invocation foot-gun. Fix 4 follows the existing mitigation
  (use the venv interpreter explicitly).
- Governance hygiene pending after Fix 4 ships:
  `governance.md` §4 Fix 4 entry close, `current_state.md`
  carry-forward cleanup, Fix 5 `governance.md` §4 entry
  reconciliation (stale since Session 46 — not Fix 4 work but
  surfaces in the same hygiene pass).

---

**End of brief.**
