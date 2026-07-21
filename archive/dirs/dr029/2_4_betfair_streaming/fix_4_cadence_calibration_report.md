# Fix 4 — Cadence calibration report

**Drafted:** 2026-05-10 ACST (Adelaide local per DR-021)
**Session-open timestamp:** 2026-05-10 09:54:35 ACST
**Session-close timestamp:** 2026-05-10 10:08:10 ACST
**Source brief:** `dr029/2_4_betfair_streaming/fix_4_cadence_calibration_brief.md`
**Working tree:** `/Users/tim/Desktop/Projects/bethub-v3/`
**Predecessor:** W2 betfair_client v1.0 (deferred four cadence parameters as
"Fix 4 calibration target" placeholders).
**Shape:** surgical fix.
**Status at close:** all anchors landed; one §6 deviation surfaced (§5.2
prescribed import path created a circular dep, resolved by reordering
`streaming.py`'s import block); one §6 implementation-note adaptation
(§5.3 comment text adapted from "5 TPS" claim to verified on-disk
`betting_exceptions.md` numbers).

---

## §1 Summary

Fix 4 commissioned Code to calibrate the placeholder cadence constants W2
deferred. End-to-end this session:

- **§5.1 — `streaming.py` cadence constants.** Six constants in the load-
  bearing block. Two divergent placeholders fixed in value
  (`CACHE_STALE_THRESHOLD_SECONDS` 30 → 10; `SUSTAINED_RECONNECT_FAILURE_THRESHOLD`
  → renamed `SUSTAINED_RECONNECT_FAILURE_WINDOW_SECONDS` with semantic
  count-to-time shift). Four spec-aligned placeholders locked with per-
  constant `§-section` citation comments. Module docstring updated to
  close the W2 framing loop on subscribe-interval and REST per-phase
  cadence.
- **§5.2 — `live_pricing.py` duplicate consolidation.** Local
  `CACHE_STALE_THRESHOLD_SECONDS = 30` removed; constant re-imported from
  `.streaming` as the single source of truth. Module docstring updated.
- **§5.3 — `_connection.py` rate-limit verification.** `RateLimitBudget`
  defaults (`200/60s`) verified within Betfair's documented ceilings (3
  concurrent in-flight reads; 1000 instructions/sec on placement, per
  on-disk `betting_exceptions.md`). Locked; "Fix 4 calibration target"
  tag removed; dataclass docstring updated.
- **§5.4 — Tests.** Eight new tests added in `test_streaming.py` under
  the `# --- Fix 4 cadence-constant locks ---` block. Block A (4 constant-
  vs-spec assertions), Block B (2 back-off sequence assertions), Block C
  (2 sustained-failure window assertions).
- **§5.5 — `test_live_pricing.py` verified.** Existing 9 tests still pass
  after `live_pricing.py`'s import change. No patches of the local
  constant existed in this file; no patch-target adjustments needed.

**Test count delta:** 519 → 527 (+8 net new). Within target band 527-531.

**Quality gates:**
- `pytest`: 527 passed, 0 failed.
- `ruff check`: All checks passed.
- `lint-imports`: 5 contracts kept, 0 broken (120 files, 338 dependencies —
  unchanged from pre-baseline).

**Anchor checklist:**
- [x] §5.1 Change A — `CACHE_STALE_THRESHOLD_SECONDS` 30 → 10.
- [x] §5.1 Change B — count → time semantic shift (constant renamed; one
      call site updated; new `_first_failure_time_utc` instance state).
- [x] §5.1 Change C — header rewritten; per-constant citations added;
      module docstring updated.
- [x] §5.2 Change A — local `CACHE_STALE_THRESHOLD_SECONDS` deleted.
- [x] §5.2 Change B — re-imported from `.streaming` (with corollary
      reorder in `streaming.py` to dodge a circular import; see §6).
- [x] §5.2 Change C — module docstring updated.
- [x] §5.3 Change A — defaults verified, locked, "Fix 4 calibration
      target" tag removed.
- [x] §5.3 Change B — dataclass docstring updated (comment text adapted
      from brief's "5 TPS" framing to verified on-disk numbers; see §5
      implementation notes).
- [x] §5.4 Block A — 4 tests added.
- [x] §5.4 Block B — 2 tests added.
- [x] §5.4 Block C — 2 tests added.
- [x] §5.5 — `test_live_pricing.py` verified passing; no patch-target
      adjustments needed.

---

## §2 Files changed

| File | Pre LOC | Post LOC | Δ |
|---|---|---|---|
| `clients/betfair_client/v1/streaming.py` | 595 | 640 | +45 |
| `clients/betfair_client/v1/live_pricing.py` | 207 | 204 | −3 |
| `clients/betfair_client/v1/_connection.py` | 105 | 111 | +6 |
| `tests/clients/betfair_client/v1/test_streaming.py` | 349 | 468 | +119 |
| **Total (4 files)** | **1256** | **1423** | **+167** |

No new files created. No edits outside the four named §5 anchors.

---

## §3 Test count delta

- **Pre-baseline:** 519 tests collected, 519 passed.
- **Post-baseline:** 527 tests collected, 527 passed.
- **Delta:** +8 (matches §5.4 target exactly; within the 527-531
  acceptable band).

---

## §4 New tests added

All eight live in `tests/clients/betfair_client/v1/test_streaming.py`
under the `# --- Fix 4 cadence-constant locks ---` block at the end of
the file.

**Block A — Constant-value-vs-spec assertions (4 tests):**

1. `test_heartbeat_loss_threshold_is_2x_heartbeat_ms` —
   `HEARTBEAT_LOSS_THRESHOLD_SECONDS == 2 * CACHE_FRESHNESS_TARGET_SECONDS == 10`
   (per §2.4 §12.5).
2. `test_cache_stale_threshold_is_2x_freshness_target` —
   `CACHE_STALE_THRESHOLD_SECONDS == 2 * CACHE_FRESHNESS_TARGET_SECONDS == 10`
   (per §2.4 §12.4).
3. `test_reconnect_backoff_initial_is_1s_and_max_is_30s` —
   `RECONNECT_BACKOFF_INITIAL_SECONDS == 1`,
   `RECONNECT_BACKOFF_MAX_SECONDS == 30` (per §2.4 §15.3).
4. `test_sustained_reconnect_failure_window_is_60s` —
   `SUSTAINED_RECONNECT_FAILURE_WINDOW_SECONDS == 60` (per §2.4 §15.3).

**Block B — Reconnect back-off sequence (2 tests):**

5. `test_reconnect_backoff_sequence_matches_section_15_3` — the doubling-
   with-cap sequence over 8 attempts equals `[1, 2, 4, 8, 16, 30, 30, 30]`
   per §15.3.
6. `test_reconnect_backoff_caps_at_max_after_5_doublings` — the 6th
   non-immediate attempt is capped at `RECONNECT_BACKOFF_MAX_SECONDS`.

**Block C — Sustained-failure window (2 tests):**

7. `test_sustained_failure_escalation_at_60s_window` — drives 7
   successive disconnects with the clock advancing through cumulative
   times `[0, 1, 3, 7, 15, 31, 61]` (the 1+2+4+8+16+30 back-off
   cumulative-summed); asserts `time_since_first_failure >=
   SUSTAINED_RECONNECT_FAILURE_WINDOW_SECONDS`.
8. `test_sustained_failure_no_escalation_below_60s` — drives 5
   successive disconnects through `[0, 1, 3, 7, 15]` (the 1+2+4+8+16
   sum = 31s, below the window); asserts `time_since_first_failure <
   SUSTAINED_RECONNECT_FAILURE_WINDOW_SECONDS` and that
   `consecutive_reconnect_failures == 5`. This is the test-side load-
   bearing assertion that the threshold is *time*, not *attempts* — a
   regression to count-based thresholding would escalate at 5 attempts;
   the time-based threshold must not.

**Existing test docstring touched:** the existing
`test_cache_cleared_state_lasts_when_advance_past_stale_window` docstring
referenced "30s"; updated to "10s per §2.4 §12.4". Test body unchanged
(the `+35s` clock advance still puts the cache past the 10s window;
test passes both pre- and post-change).

---

## §5 Implementation notes

### §5.1 — `streaming.py`

All three changes (A, B, C) landed.

**Change A** (`CACHE_STALE_THRESHOLD_SECONDS` 30 → 10) — one-line value
swap; comment block above the constant rewritten per the brief.

**Change B** (count → time semantic shift) — required three edits beyond
the rename + value:

1. Renamed `SUSTAINED_RECONNECT_FAILURE_THRESHOLD` →
   `SUSTAINED_RECONNECT_FAILURE_WINDOW_SECONDS`. Old name removed
   entirely (no callers besides `streaming.py` itself).
2. Added a `_first_failure_time_utc: datetime | None = None` instance
   attribute to `StreamingClient.__init__`. This is *state*, not a *new
   constant / function / public API* — it's needed to anchor the time-
   since-first-failure computation. The brief's §5.1 Change B
   acknowledged this as "(semantic change, not just a value swap)".
3. Updated the single call site in `_on_disconnect` to compare elapsed
   time vs the window rather than count vs threshold. Reset hook in
   `_on_auth_ack` clears `_first_failure_time_utc` on successful auth
   (mirrors the existing `_consecutive_reconnect_failures = 0` reset).

The if-branch body inside `_on_disconnect` remains `pass` (unchanged from
W2) — the existing alert mechanism per §15.3 is upstream via the
`cache_path_eligible` / snapshot guards, not an in-`_on_disconnect`
side-effect. See §7 for whether this should be revisited at Session 113.

**Change C** (comment block + module docstring) — header rewritten,
per-constant `§-section` citations added above each of the six
constants, module docstring updated to close the subscribe-interval and
REST per-phase cadence loops within the file's own documentation.

### §5.2 — `live_pricing.py`

All three changes landed but **§5.2 Change B triggered a §6 deviation**
(see §6). The brief's prescribed `from .streaming import
CACHE_STALE_THRESHOLD_SECONDS` creates a partial-init circular import
because `streaming.py` already imports `MarketPrices`, `parse_market_prices`
etc. from `.live_pricing` at module load.

**Resolution:** reorder `streaming.py`'s top-of-file imports so the
cadence-constants block appears *before* the `from .live_pricing import
(...)` line, with `# noqa: I001, E402` on the post-constants imports to
silence ruff's "unsorted import block" warning. The block now reads:

```
from . import _clock                          # stdlib + intra-package
from ._auth import AuthProvider               # imports
from .envelope import (...)
                                              # cadence constants
HEARTBEAT_LOSS_THRESHOLD_SECONDS = 10         # ...
...
CACHE_STALE_THRESHOLD_SECONDS = 10

from .live_pricing import (...)               # noqa: I001, E402
from .settlement import MarketStatus          # noqa: I001, E402
```

This is a structural reorder of `streaming.py` outside `§5.1`'s named
line range (53-60), but it is the corollary fix that makes §5.2 Change B
work as written. Surfaced as §6 deviation #1.

`live_pricing.py`'s import line uses `from .streaming import
CACHE_STALE_THRESHOLD_SECONDS as CACHE_STALE_THRESHOLD_SECONDS` — the
explicit `as` form is ruff's idiomatic way to mark a re-export and avoid
the F401 "imported but unused" warning. The constant is now single-
sourced in `streaming.py`; `live_pricing.CACHE_STALE_THRESHOLD_SECONDS`
is the same Python object (`is True`) — verified in the §7.4 sample
block.

### §5.3 — `_connection.py`

**Change A — verification outcome:** locked. The 200/60s defaults sit
well within Betfair's documented `TOO_MANY_REQUESTS` ceilings:

- 3 concurrent in-flight reads (`listMarketBook` with order/match
  projections, `listCurrentOrders`, `listMarketProfitAndLoss`,
  `listClearedOrders`) — per on-disk `dr029/2_4_betfair_streaming/
  reference_guide/betting_exceptions.md` lines 32-39.
- 1000 instructions/sec on `placeOrders` / `cancelOrders` —
  same source.

200 calls per 60-second window averages to ~3.3 calls/sec, far below
both ceilings, with bursting headroom inside the 60s window.

**§6 deviation note (comment text adaptation, not value change):** the
brief's §5.3 Change A draft comment text cited "Betfair's published
baseline is roughly 5 transactions/sec per app key (≈300/60s)." I could
not source this 5 TPS / 300-per-minute figure in §2.4 §11 or the on-disk
references. The actual documented ceilings (3 concurrent reads; 1000
instr/sec on placement) are higher than the brief's framing suggested.
The conclusion (200/60s is conservative against Betfair's ceilings) is
*more* supported, not less. I locked the values per the brief's expected
path and adapted the comment text to cite the verified on-disk numbers
rather than an unsourced framing. Surfaced as §6 deviation #2.

**Change B — dataclass docstring** updated to match Change A's adapted
comment. The "Fix 4 calibration target" tag is gone from `_connection.py`.

### §5.4 — Tests

8 tests added; structure matches the brief's Block A / Block B / Block C
layout. Notable:

- **Block B** — the brief described these tests as "given the back-off
  function (existing in `streaming.py`'s reconnection logic)." There is
  no back-off function in `streaming.py` today; `RECONNECT_BACKOFF_MAX_SECONDS`
  is defined but never referenced anywhere in the module. The Block B
  tests are written as pure-arithmetic assertions against the constants
  (`min(initial * 2**n, max)` for the doubling-cap shape). They lock the
  cadence the eventual back-off function (v3 build proper) must implement.
  Surfaced as §8 finding.

- **Block C** — `_first_failure_time_utc` is exposed as a `_`-prefixed
  instance attribute (private, not public API per the brief's hard
  limit). Tests assert against it. The if-branch body in `_on_disconnect`
  is `pass` (unchanged); the test verifies the time comparison itself,
  not a new alert side-effect.

### §5.5 — `test_live_pricing.py`

Verified passing (9 tests, all green). Grep confirmed no patches of
`CACHE_STALE_THRESHOLD_SECONDS` via module attribute exist in this file —
the only reference to the constant in the test tree was in
`test_streaming.py:322` (existing test docstring), which I updated for
accuracy. **No patch-target adjustments needed.**

---

## §6 Deviations from brief

Two deviations, both flagged here for visibility.

### Deviation #1 — `streaming.py` import block reorder (§5.2 corollary)

**What:** moved the cadence-constants block in `streaming.py` above the
`from .live_pricing import (...)` line, with `# noqa: I001, E402` on
the post-constants imports.

**Why:** the brief's §5.2 Change B prescribes `from .streaming import
CACHE_STALE_THRESHOLD_SECONDS` in `live_pricing.py`. Without the
reorder, this fires `ImportError: cannot import name
'CACHE_STALE_THRESHOLD_SECONDS' from partially initialized module
'clients.betfair_client.v1.streaming'`. The reorder makes the brief's
prescribed import work as written.

**Impact:** localised to `streaming.py`'s top-of-file region. No
business-logic, type-shape, or function-signature change. Tests + ruff +
lint-imports all pass. The reorder is documented inline in `streaming.py`
with a four-line block comment explaining why.

**Brief precedent:** §6 (Sequencing within session) anticipated this kind
of corollary: "If a different order surfaces during execution as
cleaner, Code may deviate; flag the deviation in §6 of the report with
the reasoning."

### Deviation #2 — `_connection.py` comment text adapted (§5.3 Change B)

**What:** the dataclass docstring now cites the on-disk
`betting_exceptions.md` numbers (3 concurrent reads, 1000 instr/sec on
placement) rather than the brief's draft "5 transactions/sec per app
key (≈300/60s)" framing.

**Why:** the "5 TPS" / "300/60s" claim could not be sourced in §2.4 §11
or any of the on-disk Betfair references. The actual documented ceilings
are higher; the brief's underlying conclusion (200/60s is conservative)
is more strongly supported by the verified numbers, not weakened.

**Impact:** comment text only — the values (`max_calls_per_window=200`,
`window_seconds=60`) remain unchanged, locked per the brief's expected
outcome. The "Fix 4 calibration target" tag is removed.

**Brief precedent:** the operator-flagged §5.3 Change A item explicitly
authorised verification against §11 + the on-disk reference. The comment
text adaptation is a verification refinement, not a value change.

---

## §7 Open questions for triage

One open question — flagged for Session 113 visibility, not blocking
Fix 4 close.

**The `_on_disconnect` if-branch body is `pass`.** After Change B's
count-to-time semantic shift, the time-based comparison correctly
evaluates and the test suite asserts the comparison (Block C). But the
body of the if-branch when the comparison is True is still `pass`. The
existing comment says "Sustained failure surfaces as `unavailable`
upstream via the snapshot / cache_path_eligible guards; state stays
RECONNECTING for upstream observers reading status" — i.e. the alert
mechanism is upstream, not in-`_on_disconnect`.

**Question for triage:** is `pass` the right body, or should the if-
branch *do* something (raise an event, set a flag, log an alert)?
Whatever the answer, it's out of Fix 4 scope (the brief's hard limits
forbid adding new state / public API / business logic) and belongs in
v3-build-proper or a Session 113 follow-up Decision.

---

## §8 Findings beyond brief scope

One finding, surfaced for Session 113 awareness.

**`RECONNECT_BACKOFF_MAX_SECONDS` is defined but never used in any
back-off function.** The constant exists; the actual reconnection logic
in `streaming.py` is `simulate_reconnect_attempt()` which calls
`connect()` directly with no back-off computation. The Block B tests
assert against the doubling-cap math purely via constants arithmetic
(`min(initial * 2**n, max)`); they do *not* exercise a back-off function
in `streaming.py` because none exists.

This is consistent with W2 brief framing: W2 ships "the *shape*" — state
machine, cache, message dispatch — leaving the actual socket-reading
loop and the real `betfairlightweight` integration to v3 build proper.
The back-off function is in the latter category. The Block B tests lock
the cadence that the eventual back-off function (v3 build proper or a
Session 113 follow-up) must implement.

This finding is NOT a Fix 4 deviation — Fix 4's brief never claimed there
*was* a back-off function to test against; the Block B test description
referenced "the back-off function (existing in `streaming.py`'s
reconnection logic)" but that phrasing is loose given the actual W2
shape. The pure-arithmetic test approach is the right interpretation.

---

## §9 Self-assessment

### §9.1 Pre/post baselines

| Metric | Pre-baseline | Post-baseline | Δ |
|---|---|---|---|
| Test collection | 519 | 527 | +8 |
| Test pass count | 519 | 527 | +8 |
| Test failures | 0 | 0 | 0 |
| `ruff check` (full repo) | clean | clean | — |
| `lint-imports` contracts | 5 kept, 0 broken | 5 kept, 0 broken | — |
| `lint-imports` files / deps | 120 / 338 | 120 / 338 | — |

### §9.2 Functional verification checklist

- [x] All `tests/clients/betfair_client/v1/test_streaming.py` pass
      (existing 26 + new Block A + B + C = 34 tests).
- [x] `tests/clients/betfair_client/v1/test_live_pricing.py` still passes
      (9 tests, no regressions from §5.2 import change).
- [x] All other `tests/clients/betfair_client/v1/` tests still pass (189
      total in that directory).
- [x] All `tests/workflows/` and `tests/ui/` tests still pass.
- [x] Full suite passes (527 / 527).
- [x] `ruff check` clean (full repo).
- [x] `lint-imports` 5 contracts kept, 0 broken.
- [x] No live Betfair API calls — constants and tests only.
- [x] No edits outside the §5 named anchors (modulo the §6 deviation #1
      reorder of `streaming.py`'s import block — same file, structural
      adjustment, no function/type/business-logic change).
- [x] No new untracked files at the repo root level.

### §9.3 git status snapshots

**Pre-baseline (session-open, 2026-05-10 09:54:35 ACST):**

```
modified:   clients/betfair_client/v1/__init__.py
modified:   clients/betfair_client/v1/_translation.py
modified:   pyproject.toml
modified:   uv.lock

Untracked files:
    clients/betfair_client/v1/account_funds.py
    clients/betfair_client/v1/current_orders.py
    clients/betfair_client/v1/market_catalogue.py
    tests/clients/betfair_client/v1/test_account_funds.py
    tests/clients/betfair_client/v1/test_current_orders.py
    tests/clients/betfair_client/v1/test_market_catalogue.py
    tests/ui/
    tests/workflows/
    ui/api/
    ui/web/
    workflows/bet_entry/v1/
```

**Post-baseline (session-close, 2026-05-10 10:08:10 ACST):**

```
modified:   clients/betfair_client/v1/__init__.py
modified:   clients/betfair_client/v1/_connection.py        ← Fix 4
modified:   clients/betfair_client/v1/_translation.py
modified:   clients/betfair_client/v1/live_pricing.py       ← Fix 4
modified:   clients/betfair_client/v1/streaming.py          ← Fix 4
modified:   pyproject.toml
modified:   tests/clients/betfair_client/v1/test_streaming.py  ← Fix 4
modified:   uv.lock

Untracked files: (unchanged from pre-baseline — all 11 entries)
```

The four Fix 4-modified files appeared in the modified list as expected.
No `git add` / `git commit` / `git stash` / `git restore` operations run.
No new untracked files. No modifications outside the four named §5
anchors (modulo the §6 deviation #1 inside `streaming.py` itself).

### §9.4 Length flag

This report: ~445 lines. Within the 300-500 line target band per §8.

### §9.5 DR-021 timestamp confirmation

All session timestamps captured in Adelaide local time per DR-021:
- Session-open: 2026-05-10 09:54:35 ACST.
- Session-close: 2026-05-10 10:08:10 ACST.
- Report drafted: 2026-05-10 ACST.

### §9.6 Sample verification — locked constants

Run from `/Users/tim/Desktop/Projects/bethub-v3/` via
`.venv/bin/python -c "..."`:

```
streaming.HEARTBEAT_LOSS_THRESHOLD_SECONDS         = 10
streaming.RECONNECT_BACKOFF_INITIAL_SECONDS        = 1
streaming.RECONNECT_BACKOFF_MAX_SECONDS            = 30
streaming.SUSTAINED_RECONNECT_FAILURE_WINDOW_SECONDS = 60
streaming.CACHE_FRESHNESS_TARGET_SECONDS           = 5
streaming.CACHE_STALE_THRESHOLD_SECONDS            = 10
live_pricing.CACHE_STALE_THRESHOLD_SECONDS         = 10
   (re-export from streaming.py — same id: True)
_connection.RateLimitBudget defaults:
   max_calls_per_window = 200, window_seconds = 60
```

Wire shape Session 113's Fix 4 triage will read against:
- All six `streaming.py` cadence constants at locked values per §-section
  citations.
- `live_pricing.CACHE_STALE_THRESHOLD_SECONDS` is the *same Python
  object* as `streaming.CACHE_STALE_THRESHOLD_SECONDS` (verified via
  `is`). Single source of truth.
- `_connection.RateLimitBudget` defaults locked at 200/60s per verified
  Betfair ceilings.

---

**End of report.**
