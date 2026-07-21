# Brief — Placement visibility (Betfair order-refusal reason on the Terminal)

**Drafted:** 2026-06-18 (Session 162, Adelaide-local / DR-021)
**Repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`)
**Type:** Observability / diagnostic-enablement — **no behaviour change.**
**Serves:** DR-029 §2.4 live validation. Third in the live-validation
visibility set, after `streaming_visibility_brief.md` (bring-up) and
`streaming_drop_visibility_brief.md` (post-startup drop).

---

## 1. What this brief is and is not

A single, bounded, **observability-only** Code session. It makes
`place_bet` name its outcome in the Terminal — most importantly the
**Betfair refusal reason** when an order is rejected — so the operator's
next live lay shows *why* on screen instead of a bare `503`.

It is **not** a fix to placement, auth, or the connection. It does not
change the bet-safety gate, the order body, the REST call, the audit
entries, control flow, or any returned envelope. Only log statements are
added. Surprises become findings in the report; remediation routes to the
next operator-Claude triage, not into this Code run.

## 2. Why this work exists

S162 live runs established, with the new streaming logging, that the lay
`503` is **not** the streaming interlock: the stream stayed `SUBSCRIBED`
from startup through to the lay (no drop line), so the bet-safety gate
**passed**. The `503` therefore comes from the next stage — the REST
`POST /v1/orders/place` call inside `place_bet`, which raised a
`BetfairRestError` that `map_rest_error_write` turned into a
connectivity-shaped envelope (→ `503`). The operator has ruled out a
suspended/closed market from the track side, leaving auth/session, rate-
limit, or transient-unreachable as the live candidates.

The blind spot: every non-success branch of `place_bet` records its
reason to the **in-memory** audit sink and returns it in the HTTP body,
but **nothing prints to the Terminal** — so the operator sees only a bare
`503`. This brief surfaces the reason (and the success line) so the next
lay names it.

## 3. Pre-reads

Required, in order:

1. This brief.
2. `streaming_drop_visibility_brief.md` + `streaming_drop_visibility_report.md`
   (same folder) — the immediately prior observability brief/report;
   establishes the module-logger-by-propagation pattern and the
   no-double-log proof this brief reuses verbatim.
3. `clients/betfair_client/v1/placement.py` — the file being edited.

Reference-only (on demand): `clients/betfair_client/v1/_errors.py`
(`map_rest_error_write` / `map_rest_error_read` — the reason mapping
whose output is being logged), `ui/api/routers/racing.py` `place_lay`
(the caller that maps the envelope to `503`/`409`).

## 4. System access

- **Mac filesystem, read-write**, confined to the §5 anchors.
- **No live Betfair. No credentials. No network. No order placed.**
  Verification is via the existing fake/mock placement tests only.
- Test suite runs under **`uv run pytest`** (uv project; S160 F1).
- Adelaide local timestamps (ACST/ACDT) in the report, per DR-021.
- **Git / dirty-tree (note — differs from the last two briefs):**
  `placement.py` and `tests/clients/betfair_client/v1/test_placement.py`
  are currently **clean/committed** (not in the dirty list). Editing them
  **will** add exactly two `M` lines (dirty list 56 → 58). That is
  expected and is **not** a git write. Still **no git writes** (no
  `add`/`commit`/`stash`/`restore`/`checkout`/`reset`); no *other* file's
  status changes. The §7 check is "exactly these two files newly `M`,
  nothing else," not "count unchanged."

## 5. Scope — what to add

One source file: `clients/betfair_client/v1/placement.py`, plus its test
file. No other source file. **`logging_setup.py` is NOT touched** — this
module's logger resolves to `clients.betfair_client.v1.placement`, a child
of the `clients.betfair_client.v1` namespace already surfaced at INFO, so
its records reach the existing Terminal handler by propagation (the same
path the streaming modules use). Confirm this rather than assume it.

### 5.1 — Module logger

Add `import logging` + `logger = logging.getLogger(__name__)` in the same
form as the streaming modules. No other structural change.

### 5.2 — One outcome line per `place_bet` call

`place_bet` has four return branches, each already paired with an
`_emit_entry(...)` audit call. Add exactly one log line per branch,
beside the existing return — reusing the reason already in scope. No
condition, no envelope, no `_emit_entry` call, no order body is changed.

- **Gate refusal** (`streaming_status().state != SUBSCRIBED` →
  `BETFAIR_STREAMING_DISCONNECTED`, ~L166–186): **WARNING**, naming the
  reason (`betfair_streaming_disconnected`). The gate condition and its
  envelope are byte-for-byte unchanged — a log line is added beside them,
  nothing else (this is the bet-safety interlock; §9.1).
- **REST error** (`except BetfairRestError` → `map_rest_error_write`,
  ~L203–223): **WARNING**, naming `env.reason.value` (the live one —
  e.g. `betfair_auth_expired` / `betfair_rate_limited` /
  `betfair_api_unreachable`). This is the line the operator needs.
- **Rejection** (`rejection_code` in payload, ~L230–250): **WARNING**,
  naming `rejection_code` + `rejection_detail`.
- **Success** (~L260–280): **INFO**, naming `bet_id` and matched/remaining
  size — a confirming line that the lay went through.

Include the `customer_order_ref` on each line so an attempt can be tied to
the audit entry. Do **not** log price/stake on anything below WARNING in a
way that floods — one line per call only; `place_bet` is not a hot path,
so a single line per outcome is correct, not a flood risk.

### 5.3 — Reason rendering

Log the reason from the value already computed (`env.reason.value`,
`rejection_code`, `rejection_detail`) — do not re-derive or re-map. If a
field is absent (e.g. no `rejection_detail`), omit it cleanly rather than
printing `None` noise.

## 6. Sequencing

5.1 (logger) → 5.2 (the four outcome lines) → 5.3 (clean reason
rendering) → test → full-suite baseline. One pass; no order dependency.

## 7. Empirical verification

- **Before:** `uv run pytest -q` — record pass/fail count.
- **After:** `uv run pytest -q` — record again; only delta is the new
  test(s).
- **New test(s)** (fake/mock, no I/O) in the existing
  `test_placement.py`: assert (a) a REST-error placement logs at WARNING
  carrying the mapped reason value; (b) the gate-refusal branch logs at
  WARNING; (c) a successful placement logs at INFO with the `bet_id`.
  Optionally (d) a rejection logs at WARNING with the rejection code.
- **Gate untouched proof:** show the `if streaming_status().state !=
  SUBSCRIBED` condition and its envelope are unchanged (diff context).
- **Quality gates:** `ruff check` clean on both touched files; `uv run
  lint-imports` → 5 kept, 0 broken.
- **Dirty-tree:** `git status --short` shows **exactly**
  `placement.py` and `test_placement.py` newly `M` (56 → 58), no other
  file changed, no git write commands run.
- **No-double-log:** child record reaches the parent handler once, never
  root (same proof as the prior report; reference it).

## 8. Output spec

Single file: `dr029/2_4_betfair_streaming/placement_visibility_report.md`.
Adelaide-local timestamps. Sections:

1. What changed (the logger + the four outcome lines; show them).
2. Gate-untouched proof (the interlock condition/envelope byte-for-byte).
3. Test baseline (before → after; new test(s) named).
4. Hard-limit adherence (the five §9 limits, each addressed).
5. What the operator will now see — sample Terminal lines for a
   **refused** lay (WARNING + the Betfair reason) and a **successful**
   lay (INFO + bet_id).
6. Findings + self-assessment.

Rough length 120–180 lines. No placement/auth fix, no recommendation on
the eventual fix — that is the next operator-Claude session's call.

## 9. Hard limits — non-negotiable

1. **Bet-safety interlock untouched.** The `streaming_status().state !=
   SUBSCRIBED` gate condition and the `BETFAIR_STREAMING_DISCONNECTED`
   envelope it returns are **byte-for-byte unchanged**. A WARNING line is
   added beside the existing return; the refusal logic itself is not
   modified in any way.
2. **Observability only.** No change to control flow, the order body, the
   REST call, the `_emit_entry` audit calls, reason mapping, or any
   returned envelope. Log statements only.
3. **No live Betfair / credentials / network / order placed.** Fake/mock
   placement tests only.
4. **No git writes.** No `add`/`commit`/`stash`/`restore`/`checkout`/
   `reset`. The two edited files appear as `M` (expected); no other file's
   status changes. No `uvicorn.access` duplication (no handler on root;
   reuse the existing named-namespace handler by propagation).
5. **One line per `place_bet` call.** No logging inside loops, no
   per-field spam; exactly one outcome line per placement attempt.

Excluded and named: the actual auth/session fix (the likely real cause —
next session's call once the reason is named), `cancellation.py` /
`replacement.py` (same pattern could apply later, out of scope here), the
racing-router `place_lay` log surface (the reason is logged at source in
`place_bet`; the router is not touched), the in-memory audit-sink
durability gap (parking-lot), the 200-market over-subscription
(parking-lot), and any change to `logging_setup.py`.

## 10. What happens after Code's session

The next operator-Claude session triages
`placement_visibility_report.md` (green tests, gate untouched, dirty list
= the two expected files only). Then the operator re-runs `BetHub.command`
live and attempts the $5 lay — the Terminal now **names the Betfair
refusal reason** (e.g. an auth/session error). That named reason drives
the scoping of the actual placement/auth fix brief (Chat → Code). Code
does not write that brief; this run ends at the report.

## 11. Cross-references

- **Serves:** DR-029 §2.4 live validation.
- **Follows:** `streaming_drop_visibility_brief.md` / `_report.md` (which
  ruled out the streaming gate as the lay-503 cause), and the S162 live
  runs that localised the 503 to the REST place-order call.
- **DRs:** DR-021 (Adelaide anchors), DR-030 (module layout — unchanged),
  DR-031 (uvicorn logging interaction — existing handler reused, not
  modified), DR-032 (Betfair canonical / auto-login — the auth path the
  named reason will point at, fixed in a later brief, not here).
- **Bet-safety hard rule:** preserved — the placement gate is observed,
  not modified.
