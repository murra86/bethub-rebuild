# Report — Placement visibility (Betfair order-refusal reason on the Terminal)

**Executed:** 2026-06-18 ACST (Adelaide-local, DR-021)
**Brief:** `dr029/2_4_betfair_streaming/placement_visibility_brief.md`
**Repo:** `bethub-v3` (`/Users/tim/Desktop/Projects/bethub-v3`)
**Type:** Observability / diagnostic-enablement — no behaviour change.

---

## 1. What changed

One source file plus its existing test file. `place_bet` recorded every
outcome to the in-memory audit sink and returned it in the HTTP body, but
printed **nothing** to the Terminal — so the operator saw only a bare
`503`. It now logs exactly one outcome line per call, reusing the reason
already in scope. Log statements only: no change to the gate, the order
body, the REST call, the `_emit_entry` audit calls, reason mapping, or any
returned envelope.

### 1.1 — Module logger (§5.1)

```python
# child of the API-surfaced `clients.betfair_client.v1` namespace → reaches
# the existing Terminal handler by propagation; logging_setup.py untouched
logger = logging.getLogger(__name__)
```

Name resolves to `clients.betfair_client.v1.placement`, a child of the
`clients.betfair_client.v1` namespace the S161 work surfaced at INFO — the
same propagation path the streaming modules use (§2 proves it).

### 1.2 — One outcome line per branch (§5.2 / §5.3)

Each of `place_bet`'s four return branches now runs **emit → log →
return** (FLAG B): the existing `_emit_entry(...)` and the `return` are
unchanged; a single log line sits between them, reading only values
already computed. Every line carries `customer_order_ref` so an attempt
ties to its audit entry.

```python
# 1. Gate refusal (after the unchanged condition + envelope + _emit_entry):
logger.warning("betfair placement refused (ref=%s): %s",
               customer_order_ref, env.reason.value)            # → betfair_streaming_disconnected
return env

# 2. REST error (except BetfairRestError → map_rest_error_write):
logger.warning("betfair placement failed (ref=%s): %s",
               customer_order_ref, env.reason.value)            # → betfair_auth_expired / _rate_limited / _api_unreachable
return env

# 3. Rejection (rejection_code in payload) — §5.3 clean rendering:
rejection_reason = rej_env.rejection_code
if rej_env.rejection_detail:                                    # omit the detail when absent, no `None` noise
    rejection_reason = f"{rej_env.rejection_code} ({rej_env.rejection_detail})"
logger.warning("betfair placement rejected (ref=%s): %s",
               customer_order_ref, rejection_reason)
return rej_env

# 4. Success:
logger.info("betfair placement confirmed (ref=%s): bet_id=%s matched=%s remaining=%s",
            customer_order_ref, result.bet_id,
            result.initial_size_matched, result.size_remaining)
return FreshEnvelope[BetPlacementResult](...)
```

Levels per §5.2: the three failure branches WARNING, success INFO. One
line per call — `place_bet` is not a hot path (§5/§9.5).

---

## 2. Gate-untouched proof

The bet-safety interlock is byte-for-byte unchanged. The `git diff` shows
**only added lines** around it — the condition, the
`BETFAIR_STREAMING_DISCONNECTED` envelope, and the `_emit_entry` call carry
no `-` lines:

```python
    streaming_state = streaming_client.streaming_status().state          # unchanged (L158)
    if streaming_state != StreamingConnectionState.SUBSCRIBED:           # unchanged (L159)
        env = UnavailableWriteEnvelope(
            reason=BetfairReadUnavailableReason.BETFAIR_STREAMING_DISCONNECTED,
            retry_after=10,
            rejection_code=None,
            rejection_detail="Streaming connection unavailable; placement queue paused.",
        )                                                                # unchanged (L160–165)
        _emit_entry(audit_sink, ... outcome=WriteOutcome.STREAMING_DISCONNECTED ...)   # unchanged
+       logger.warning("betfair placement refused (ref=%s): %s",
+                      customer_order_ref, env.reason.value)             # added beside the return
        return env
```

The full-suite pass (1013, incl. the pre-existing
`test_place_blocked_when_streaming_disconnected`) confirms the gate's
behaviour and envelope are intact.

### Propagation + no `uvicorn.access` duplication

Runtime check after importing the API app (runs `configure_logging()` as
production does), emitting a child WARNING through a probe on both parent
and root:

```
child.propagate: True   child.handlers: []
parent has bethub handler: 1   parent.propagate: False
root has bethub handler: 0
child effective level: INFO
times record reached a handler across parent+root: 1  (expect 1 — parent only, not root)
```

Same result as the prior two visibility reports: the child's record fires
the parent's `bethub-app-stream` handler once, then stops (parent
`propagate=False`) — never reaching root, so no `uvicorn.access`
duplication. `logging_setup.py` did not need to change.

---

## 3. Test baseline

| Stage  | Command            | Result                    |
|--------|--------------------|---------------------------|
| Before | `uv run pytest -q` | **1009 passed, 0 failed** |
| After  | `uv run pytest -q` | **1013 passed, 0 failed** |

Delta = 4 new tests in the existing `tests/clients/betfair_client/v1/test_placement.py`
(fake/mock, no I/O; log captured via a handler attached directly to the
placement logger):

- `test_rest_error_logs_warning_with_mapped_reason` — a 401 → REST-error
  placement logs WARNING carrying the **live** mapped reason
  (`env.reason.value`, here `betfair_auth_expired`) + the order ref.
- `test_gate_refusal_logs_warning` — the gate-refusal branch logs WARNING
  naming `betfair_streaming_disconnected` + the ref.
- `test_successful_placement_logs_info_with_bet_id` — a success logs INFO
  naming the `bet_id` + the ref.
- `test_rejection_logs_warning_with_rejection_code` — a Betfair rejection
  logs WARNING naming `MARKET_NOT_OPEN_FOR_BETTING` + the ref.

Quality gates on touched files:

- `ruff check clients/betfair_client/v1/placement.py tests/clients/betfair_client/v1/test_placement.py` → **All checks passed!**
- `uv run lint-imports` → **5 kept, 0 broken** (DR-030 unchanged).

---

## 4. Hard-limit adherence (§9)

1. **Bet-safety interlock untouched.** The `streaming_state != SUBSCRIBED`
   condition (L158–159) and the `BETFAIR_STREAMING_DISCONNECTED` envelope
   (L160–165) are byte-for-byte unchanged (§2 diff); only a WARNING line
   was added beside the return.
2. **Observability only.** No change to control flow, the order body, the
   REST call, the `_emit_entry` calls, reason mapping, or any returned
   envelope. The four log lines read in-scope values and return them
   unchanged.
3. **No live Betfair / credentials / network / order placed.** Tests drive
   the existing `MockTransport` + fake streaming fixtures; no I/O.
4. **No git writes; dirty list = the two expected files only.** No
   add/commit/stash/restore/checkout/reset. `git status --short` went
   **56 → 58**, the two new lines being exactly `placement.py` and
   `test_placement.py` newly `M`; the other 56 lines are unchanged. No
   handler on root → no `uvicorn.access` duplication (§2).
5. **One line per `place_bet` call.** Exactly one outcome line per branch;
   no loops, no per-field spam. Each new test asserts a count of 1.

Edits confined to the §5 anchors: `clients/betfair_client/v1/placement.py`
and its test file. No other source file.

---

## 5. What the operator will now see

**Refused lay** (the line the next live attempt needs — WARNING + the
Betfair reason, instead of a bare 503):

```
2026-06-18 15:00:56 WARNING clients.betfair_client.v1.placement: betfair placement failed (ref=bet-record-uuid-12345): betfair_auth_expired
```

Other refusal shapes:

```
WARNING clients.betfair_client.v1.placement: betfair placement refused (ref=…): betfair_streaming_disconnected
WARNING clients.betfair_client.v1.placement: betfair placement rejected (ref=…): MARKET_NOT_OPEN_FOR_BETTING
```

**Successful lay** (INFO + bet_id, a confirming line):

```
2026-06-18 15:01:10 INFO  clients.betfair_client.v1.placement: betfair placement confirmed (ref=bet-record-uuid-12345): bet_id=318946271234 matched=50.0 remaining=0.0
```

(The first WARNING line above was reproduced verbatim by the §2 runtime
check.)

---

## 6. Findings + self-assessment

- **F1 — the 503 will be named at source.** Per the S162 localisation, the
  lay 503 comes from the REST `POST /v1/orders/place` raising
  `BetfairRestError`; that path is branch 2, which now logs
  `env.reason.value` at WARNING. The next live lay will print the live
  reason (auth/session, rate-limit, or unreachable) — the input the next
  triage needs to scope the actual fix. No fix attempted here (DR-032 auth
  path is a later brief).
- **F2 — REST-error audit entry carries no `rejection_detail`.** Branch 2's
  `_emit_entry` passes `rejection_code=None, rejection_detail=None` (the
  reason lives in the envelope, not the rejection fields). The log line
  therefore surfaces `env.reason.value`, which is the meaningful field for
  that branch — no detail is lost. Named, not actioned.
- **F3 — reason rendering reads the envelope, never re-maps.** Branches log
  `env.reason.value` / `rej_env.rejection_code` directly (§5.3); the
  `map_rest_error_write` / `write_envelope_for_rejection` mappings are
  unchanged and uncalled by the logging.
- **Self-assessment:** All five hard limits held. Brief §6 sequence
  followed end-to-end; 1013/0 green, ruff clean, imports 5/5, dirty list
  56→58 with exactly the two expected files, no double-logging, gate
  byte-for-byte unchanged. Code-proves-wiring / operator-proves-live split
  intact: the live Terminal naming the actual refusal reason is the
  operator's next `BetHub.command` lay (§10). No placement/auth fix, no
  recommendation on the eventual fix — that is the next operator-Claude
  session's call.
```
