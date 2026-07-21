# Live stream 64 KiB read-buffer overflow — investigation + fix (S227)

**Opened:** 2026-07-06 (S227), Adelaide-anchored per DR-021.
**Status:** FIX BUILT + red-before/green-after proven + 3-lens independent read-only refute-verify (all UPHELD). Suite **1346 passed / 1 xfailed** on bethub-v3 @ HEAD `e2638fac` (additive on the dirty tree, no git writes, both workers OFF, no money moved).
**Trigger:** surfaced live at the S227 B3 live-proof — the moment the operator launched live, the Betfair stream fell into an unrecoverable reconnect loop, blocking the live-proof. This is a **stream-transport / liveness** fix, not a money-path change.
**Governing DRs:** DR-021, DR-019 (money-path untouched), DR-031 (asyncio/uvicorn threading).

---

## 1. Symptom (observed live)

On live launch (`mode=live`), the Terminal printed, every ~1–2 seconds, forever:

```
betfair stream: ... reached SUBSCRIBED at startup.
betfair stream: connection error: Separator is not found, and chunk exceed the limit
betfair streaming: subscribed → reconnecting (op=disconnect)
betfair stream: socket open to stream-api.betfair.com:443
... (repeat)
```

The stream reached SUBSCRIBED, then immediately dropped and reconnected — never holding. No self-heal.

## 2. Root cause (CONFIRMED, not theorised)

The live connector `open_tls_connection` (`clients/betfair_client/v1/_stream_transport.py`) called `asyncio.open_connection(host, port, ssl=context)` with **no `limit=`**, so the `StreamReader` used asyncio's default line cap of **64 KiB** (`_DEFAULT_LIMIT = 2**16`; confirmed empirically = 65536). The read loop's only read is `reader.readline()`. When a single newline-delimited frame exceeds 64 KiB, `readline()` raises `ValueError` ("chunk exceed the limit" / "chunk is longer than limit" — two asyncio phrasings for the same overrun). The broad `except Exception` in the run loop catches it as a "connection error" → `_signal_drop` → reconnect. The oversized frame is the **initial market image**, which arrives right after SUBSCRIBED — so every reconnect reaches SUBSCRIBED (resetting backoff to 0 → immediate retry), gets the same oversized image, and dies again. A tight, unrecoverable loop.

**Why the image is >64 KiB:** the racing market subscription filter (`RACING_MARKET_FILTER`) is deliberately coarse — **all AU horse ("7") + greyhound ("4339"), WIN + PLACE, no market-id restriction** — with full `EX_MARKET_DEF` + `SP_PROJECTED` + `SP_TRADED` fields and 3-level ladders. On a busy AU card the initial image overruns 64 KiB.

**Not a regression:** the transport is unchanged since the S198 baseline checkpoint `7c4482b`. This is a **latent bug** — the 64 KiB cap only bites once the live image exceeds it, which depends on how many AU races are live at that minute (which is why it looked "proven healthy" at S162 and failed at S227).

## 3. The fork, resolved on evidence

- **Raising the buffer is correct regardless of subscription breadth.** A production Betfair feed legitimately sends frames >64 KiB; a 64 KiB cap on it is a genuine transport bug. Raising it is not a mask.
- **Trimming the broad subscription is a separate DESIGN decision, not this fix.** The coarse filter is deliberate (comment: "coarse over fine-grain… race-type scoping at the consumer surface, NOT here"), and the SP fields are load-bearing for the §13 BSP-reachability gate. Trimming has display + safety-gate consequences → **PARKED** as its own item (folds with the known >200-market `SUBSCRIPTION_LIMIT_EXCEEDED` note).

## 4. The fix (surgical)

`clients/betfair_client/v1/_stream_transport.py`, two hunks:

- New bounded constant: `STREAM_READ_LIMIT = 8 * 1024 * 1024` (8 MiB) — generously above the largest realistic image, but **bounded** so a corrupt/runaway frame still fails safe (reconnect) rather than exhausting memory. ~125× the default.
- Connector: `asyncio.open_connection(host, port, ssl=context, limit=STREAM_READ_LIMIT)`.

No change to framing, parsing (`parse_frame`), dispatch, placement, settlement, or reconciliation.

## 5. Verification standard met

- **Empirical mechanism check:** a default `StreamReader` raises `ValueError` on a 200 KiB line; an 8 MiB reader reads it whole.
- **3 new tests** (`test_stream_transport.py`): wiring (connector passes `limit=STREAM_READ_LIMIT > 64 KiB`), default-reader-rejects-oversized-frame, raised-limit-admits-oversized-frame.
- **Red-before/green-after PROVEN:** with `limit=` removed, the wiring test fails (`assert None == 8388608`); restored **byte-identical** (md5-confirmed); green after.
- **Suite:** `uv run pytest` → **1346 passed, 1 xfailed** (1343 → 1346, +3).
- **3-lens independent read-only refute-verify (S226 pattern) — ALL UPHELD:**
  - **Correctness/completeness:** `readline()` is the only read (no second overflow point); error-to-mechanism exact match; 8 MiB sound both directions (segmentation helps; monolithic worst case ~1.2 MB); fix is on the genuinely live path (`composition.py:367-372` wires `open_tls_connection`); buffer fix alone lets SUBSCRIBED hold.
  - **Blast-radius/money-safety:** the only `asyncio.open_connection` in the repo (all `vps_client` hits are SQLite); no sibling latent bug; no money logic touched; HEAD `e2638fac`, no git write.
  - **Test-integrity:** red-before independently reproduced against a `/tmp` copy; reader tests exercise asyncio's only `ValueError` path; 200 KiB a robust non-fragile proxy; suite count confirmed exactly.

## 6. Residuals (none block resuming the B3 live-proof)

- **R-b (LOW, liveness, money-harmless — watch at live-proof):** 8 MiB is an engineering estimate, not measured against a real all-AU image. `segmentationEnabled: True` chunks the image so per-frame size should sit well under 8 MiB, but a genuinely larger single frame would reintroduce the loop (fails safe to reconnect). **Watch:** confirm the stream holds SUBSCRIBED steadily at launch; optionally capture the largest observed frame size to convert the estimate to a measurement.
- **R-c (LOW, liveness, money-harmless — parked, watch at live-proof):** the transport recovers only from `INVALID_SESSION`; a `SUBSCRIPTION_LIMIT_EXCEEDED` / `FAILURE` status on the broad subscription would block SUBSCRIBED at bring-up rather than corrupt anything. Today's live log showed the subscription accepted (no limit-exceeded), so latent, not active. Folds with the parked subscription-breadth item.
- **R-a (operator commit-time):** this stream fix now joins the B3 money-path changes in one uncommitted tree — commit it in isolation if provable "no money code touched" attribution is wanted (extends the existing HIGH-2 staging item).
- **Parked (separate design item):** trim the coarse all-AU WIN+PLACE market subscription (with the >200-market `SUBSCRIPTION_LIMIT_EXCEEDED` note) — deliberate, deferred.

## 7. Close decision

Stream buffer fix is **BUILT + verified + green**. It unblocks the S227 B3 live-proof: on relaunch, Phase 0 now doubles as the live confirmation of this fix (the stream must hold SUBSCRIBED steadily instead of looping). Flags stay OFF until the live-proof passes.

<!-- STREAM READ-BUFFER OVERFLOW FIX (S227) — built + 3-lens verified; live confirmation folds into the B3 live-proof Phase 0 -->
