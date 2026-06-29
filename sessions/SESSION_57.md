# Session 57

**Title:** §2.1 BSP-gap verification — clean. §2.1 race-data fit-for-purpose stream closes (six-fix surgical arc complete). DR-029 stream count drops from ten to nine. Session also surfaced journal-vs-filesystem drift on §2.1 arc state and reconciled.
**Opened:** 2026-05-03 11:32 ACST
**Closed:** 2026-05-03 12:01 ACST
**Wall-clock:** 29 min (single sitting, single workday — same-workday continuation of Session 56's 11:00 close).
**Tool routing:** Claude Chat. No Code routing this session — verification ran via direct Desktop Commander queries against capture.db.
**Governing DRs invoked:** DR-029 (data-layer fit-for-purpose review — active arc), DR-027 (two-database architecture), DR-028 (cross-DB integration boundary discipline), DR-021 (timestamp anchoring).

---

## Anchor

Open: `TZ="Australia/Adelaide" date "+%Y-%m-%d %H:%M %Z"` → `2026-05-03 11:32 ACST`.
Close: same command → `2026-05-03 12:01 ACST`.

Sunday late morning, same-workday continuation of Session 56's 11:00 close (32 min gap; same-workday per Cat 1).

## Pre-flight checks

Open ritual run via `bethub-session-open` skill:

- 13 `.md` files at rebuild root + `openapi.json` (matched expected count at Session 56 close).
- All directories present.
- `.close_out_backups/` contained `SESSION_57_opening_prompt.md` only (Session 56 close artefact, expected).
- Drift-check passed: `current_state.md` last-updated `2026-05-03 11:00 ACST` matched Session 56 close; `sessions/SESSION_56.md` present and non-empty; `v3_build_picture.md` last-updated `2026-05-03 07:20 ACST` matched (artefact didn't move at Session 56 close — correct).
- Governing DRs named in orientation summary.
- Same-workday calendar-calibrated recap delivered (tight).
- V3 build picture: skipped silently (no stream movement Session 56).
- Open-items delta: skipped silently (no meaningful between-session delta).

## Session shape

Session 57 was a **verification-plus-reconciliation session** with three threads:

1. **§2.1 BSP-gap verification.** Operator opened with the trigger that Devonport R1 should have settled. Probed capture.db state directly via Desktop Commander start_process + ssh — confirmed Devonport R1 (race_id 1010972) settled (`capture_status = SETTLED`), Betfair WIN market `1.257604461` populated, last snapshot 11:13:32 ACST. Ran the §7.2 verification query against `runners` joined to `betfair_snapshots` — 6/6 active runners with BSP populated, magnitudes 1.88 to 226.50 (all sane), `is_final_snapshot = 1` for all six. Forbes R1 (race_id 1010700) cross-checked — 9/9 active runners, BSP range 2.86 to 62.92. Two-for-two clean.

2. **Journal-vs-filesystem drift surfaced and reconciled.** Initial recommendation was to draft a Fix 5 brief, anchored on the assumption that §2.1's surgical-fix arc still had Fix 5 (venue harmonisation) outstanding. Reading the actual filesystem disclosed that Fix 5, Fix 6, Fix 7, and Fix 8 had already executed across Sessions 46–50, with **2,596 runner rows now carrying both `finish_position` AND `betfair_selection_id`** post-Fix-8 (the headline cross-tab that was 0→0 since Session 35). Recommendation reset; reconciliation pass run on operator request.

3. **Big-picture v3 overview produced.** Operator asked for a simple overview of v3 development and what's left before cutover. Delivered a three-phase shape (DR-029 close → v3 build → cutover) with the six-streams-remaining DR-029 picture and the major Phase 2 build items.

Substantively closed: §2.1 race-data fit-for-purpose stream. Forward routing confirmed: Session 58 picks up §2.3 (periodic-API pattern reframe).

## What was delivered

### 1. §2.1 BSP-gap verification — clean

Direct Desktop Commander queries against capture.db (live VPS, no copy):

**Devonport R1 (race_id 1010972):**

```
runner_number  runner_name      n_snapshots  n_bsp_rows  bsp_value
1              Don Turboas      17           1           2.804
2              Strato Ken       17           1           1.88
3              Awesome Orphan   17           1           38.491
4              Gotterup         17           1           106.828
5              Nunkeri          17           1           12.0
6              Stripntough      17           1           226.498
```

6/6 active runners, all BSPs sane (range 1.88 → 226.50), all `is_final_snapshot = 1`, all on snapshot_time `01:43:32 UTC` = 11:13:32 ACST (1m32s post-jump).

**Forbes R1 (race_id 1010700):** 9/9 active runners, BSP range 2.86 to 62.92.

All four §7.2 success criteria from the original BSP brief met:
- Active runners have BSP populated (n_with_bsp = n_active_runners).
- BSP magnitudes sane (`0 < bsp_price < 1000`, no NaN-encoded floats).
- BSP tagged as final snapshot.
- Two settled AU thoroughbred WIN markets verified (Devonport + Forbes).

**§2.1 BSP-gap closes.** The Fix 3 BSP write-back path is empirically working.

### 2. Observation surfaced for forward reference (Fix 4 input)

The BSP-bearing snapshots were written 1m32s post-jump while `market_status` was still `OPEN`, not after the market went CLOSED+45min as the Saturday API observation probe characterised. Betfair returned `actualSP` values in the open-but-post-jump window. **Better than expected** — BSP is reachable earlier than the probe predicted — but a deviation from the probe's documented behaviour. Logged as forward-reference input for Fix 4 cadence design (the timing nuance feeds Fix 4's brief, not §2.1's close).

### 3. Journal-vs-filesystem reconciliation

Session 56's record and `current_state.md` framed §2.1 as "BSP-fix verification deferred to Session 57" without acknowledging that §2.1's actual close was a six-fix surgical arc, of which Fix 3 (BSP write-back) was the last empirically-gating piece. Reconciliation pass surfaced:

- ✅ Fix 1+2 — race-result write-back. Sessions 35–36.
- ✅ Fix 3 — BSP / sp_near / sp_far write-back. Session 37 (code) → Session 56 (re-applied) → Session 57 (verified).
- ✅ Fix 5 — venue harmonisation lift. Sessions 46–47.
- ✅ Fix 6 — venue regex broadening + alias extension + dry-run merge. Session 47.
- ✅ Fix 7 — merge-mechanism design probe. Session 48.
- ✅ Fix 8 — race-level merge execution. **+784 race-row merges, +2,596 runner-row `with_both` cross-tab cell.**

**Non-gating residual quality work** (logged as open items in `current_state.md`, none gate DR-029 close):

- Fix 9 — Racing API re-fetch for the 2,081 pre-Fix-8 merged races' empty runner arrays.
- Fix 10 — `has_subscription_sync` flag desync root-cause diagnostic.
- Three-row collision per-row triage (52 keys).
- Low-confidence match review.
- Durable Fix 8 merge tooling promotion.
- Stale `client.py:189` docstring.

### 4. Big-picture v3 overview

Three-phase shape delivered to operator in plain language:

- **Phase 1 — DR-029** (currently here, ~70% done). §2.1 closes today, §2.2 closed Session 38, eight items remain (§2.3, §2.4, §2.5, §2.6 race path, §2.7, §2.8, §2.9, §2.10) plus close-out governance paragraph.
- **Phase 2 — v3 build** (not started). Operational layer (accounts, hygiene, AccountCare, promo allocation), execution layer (bet logging, burst-review UI, hedge modal, live pricing), accounting layer (ledger, reconciliation, settlement, reports). Slices 1–6 already locked in `architecture.md`; integration modules `vps_client` / `betfair_client` / `softbook_client` build against the DR-029-locked contracts.
- **Phase 3 — cutover** (not started). v2 stays running; v3 takes over operationally; no transaction backfill (per Session 13 revision 4 / Session 14 promotion).

Plus the four-jobs-v3-must-do framing from `vision.md` (run the operation, capture data accurately, surface decisions in real time, measure what works) and the soft items that layer on post-cutover (soft-book vendor source, Strategy 3 SGM modelling, Strategy 4 place-market modelling, three-pieces-of-named-debt remediation).

## Standing-instruction adherence check

- **Cat 1 (orientation summary)** — DR-029, DR-027, DR-028, DR-021 named at open.
- **Cat 1 (calendar-calibrated recap)** — same-workday tight recap delivered (32 min between close and open).
- **Cat 1 (V3 build picture conditional render)** — skipped silently (no stream movement Session 56).
- **Cat 1 (open-items delta)** — skipped silently (no meaningful between-session delta).
- **Cat 1 (drift-check)** — done at open. All three checks matched.
- **Cat 1 (short responses, plain language)** — held throughout. The reconciliation pass and v3 overview were longer-form by explicit operator request ("simple overview of the entire version 3 development"); flagged with implicit "this deserves a little detail" via the structured shape.
- **Cat 1 (decision-maker framing)** — held. Three operator decisions surfaced cleanly: probe-now-vs-wait (operator: probe), §2.1 closure-with-observation (operator: option 1, Fix 4 input), close-vs-continue (operator: close, §2.3 next).
- **Cat 1 (don't drift to alternatives when operator clear)** — held after initial slip. First Fix-5-recommendation slip caught by reading filesystem before drafting.
- **Cat 1 (unwind shorthand)** — held. DRs cited with bracketed reminders; "Fix 3", "§7.2", "§2.1", "§2.3", "actualSP" all unwound on use.
- **Cat 2 (timestamp re-anchoring)** — open and close anchored.
- **Cat 2 (pre-flight directory listing)** — done at open and close.
- **Cat 2 (Desktop Commander default)** — held throughout. All capture.db queries via `Desktop Commander:start_process` + ssh against live VPS. `tool_search` called once mid-session for `start_process` parameter schema (deferred-tool pattern — expected).
- **Cat 2 (no-DB-file-copy)** — held. All capture.db queries via live VPS sqlite3.
- **Cat 2 (operational/analytical line discipline)** — n/a; verification queries were analytical-line reads only.
- **Cat 2 (closing summary on opening-prompt-produced sessions)** — to be omitted at this close per skill default.
- **Cat 2 (write_file vs create_file gotcha)** — held. This session record uses `Desktop Commander:write_file`.
- **Cat 3 (external API resources reach-for)** — n/a this session; verification was capture.db state, not external API shape.
- **Cat 4 (DR-027/028 invoked)** — named at open. Cross-database boundary held cleanly throughout — capture.db queries were read-only verification only.
- **Cat 4 (operator review of artefacts is between-session work)** — held. No artefacts produced this session that need between-session operator review.
- **Cat 4 (Betfair-as-canonical-source extension)** — n/a this session; carries forward.
- **Cat 5 (software questions are Claude's)** — held. Verification design (which queries to run, which races to cross-check, how to interpret the open-vs-CLOSED market-state observation) framed as Claude's calls; operator confirmed direction.

**Process drift caught and corrected mid-session.** Initial recommendation was Fix 5 brief drafting, off a stale mental model that Fix 5 was outstanding. Caught when reading the actual filesystem before drafting; reconciled cleanly. Lesson reinforced: **read filesystem before recommending route**, especially after multiple sessions of execution work the journal may not yet reflect.

**No new standing instructions surfaced this session.**

## Open items in (carried forward)

All non-closed items from Session 56 carry forward to Session 58. Status updates:

- **§2.1 race-data fit-for-purpose** — **CLOSED THIS SESSION.** See "Open items out".
- **§2.4 Fix 4 cadence design** — unchanged. Brief drafting unblocked; held lightly until operator has Betfair API documentation (Exchange REST + Streaming) collected between sessions.
- **§2.5 soft-book interface contract** — unchanged.
- **§2.10 external analytics scan** — unchanged. Inventory write-up is the remaining work.
- **WIP §16** — VPS in-flight work (13 modified + 7 untracked post-BSP-fix). Unchanged.
- **Pending architectural extension (Session 42)** — unchanged. Post-DR-029 documentation pass.
- **Fix 9 (Racing API re-fetch)** — unchanged. Non-gating quality work.
- **Fix 10 (`has_subscription_sync` flag desync root-cause)** — unchanged. Non-gating quality work.
- **Three-row collision per-row triage** — unchanged. Non-gating.
- **Low-confidence match review** — unchanged. Non-gating.
- **Durable Fix 8 merge tooling** — unchanged. Non-gating.
- **Session numbering slip in probe brief** — unchanged. Cosmetic.
- **EX_LADDER entitlement question** — unchanged. Operator-side homework.
- **Drift-check methodology gap** — unchanged. Light-touch; folds into next pre-flight pattern naturally.
- **`bethub-analytical` project awaiting activation** — unchanged. Out-of-rebuild-project work.
- **Post-DR-029 monitoring layer (smaller scope)** — unchanged. Parked.
- **§2.1 BSP-fix code finding (c) — stale `client.py:189` docstring** — unchanged. Non-gating; trivial fix folds into any future brief touching the file.
- **§2.1 BSP-fix code finding (d) — Sunday discovery returned 71 Betfair WIN markets but 106 active races** — unchanged. Out of scope for §2.1 (now closed); materially affects substrate Fix 4 / §2.5 will reach for. Surfaced for forward reference.

**New (Session 57):**

- **§2.1 BSP timing observation — open-but-post-jump BSP reachability** — Empirical observation that Betfair `actualSP` populates 1–2 minutes post-jump while `market_status` is still `OPEN`, contrary to the API observation probe's "CLOSED+45min" characterisation. Better than expected (BSP reachable earlier). Forward-reference input for Fix 4 cadence design — the timing nuance affects when Fix 4's snapshot writer should attempt BSP capture. Not a §2.1 reopener; logged for Fix 4.

## Open items out

- **§2.1 race-data fit-for-purpose — CLOSED.** Six-fix surgical arc complete (Fix 1+2, Fix 3, Fix 5, Fix 6, Fix 7, Fix 8) plus today's empirical verification. Headline outcome: 2,596 runner rows now carry both `finish_position` AND `betfair_selection_id` post-Fix-8; BSP populated for all active runners on settled AU thoroughbred WIN markets post-Fix-3 verification. The DR-029 close addendum at `dr029/dr029_scope.md` §2.1 will need updating with the close detail at DR-029 close-out time (not this session). DR-029 stream count drops from ten to nine.

## Session close state

- **Rebuild folder root:** 13 `.md` files + `openapi.json` (unchanged from Session 56 close). No phantom files. All directories present.
- **`current_state.md`:** updated by close ritual to reflect §2.1 closure, residual non-gating items, Session 58 forward routing on §2.3.
- **`v3_build_picture.md`:** §2.1 stream moves from `in flight` to `done` (carry-rule applies — drops next render after Session 58). Other streams unchanged. Artefact updated; "Last updated" stamp moves to this close timestamp.
- **`standing_instructions.md`:** unchanged this session. Re-upload to Project knowledge base still pending operator-side from Session 55.
- **`sessions/`:** Session 57 record written by close ritual.
- **`.close_out_backups/`:** Session 57 opening prompt removed at close; Session 58 opening prompt to be written by close ritual.
- **Project knowledge base:** unchanged. Operator-side `standing_instructions.md` re-upload still pending.
- **VPS state:** healthy. Zero `database is locked` errors today. Snapshot loop firing on Sunday races. BSP write-back empirically verified.
- **`bethub-analytical/`:** unchanged.

## Forward routing

**Confirmed with operator at close:** "Let's go with your recommendation. Close it up, and we'll start with 2.3 next session."

Session 58 primary deliverable: **§2.3 (periodic-only API pattern reframe on operational/analytical axis).**

Per `dr029/dr029_scope.md` §2.3, the work is documentation/specification: reaffirm periodic-only for analytical reads (vps_client against capture.db), explicitly carve out operational consumers as a separate concern (per §2.4 Betfair Streaming spec and §2.5 soft-book interface contract), preserve the bracketing argument for analytical reads while clarifying it does not transfer to operational reads. Reframed from existing DR-029 scope per Recommendations 1 and 5 of the multi-agent review.

Smallest §-item by shape across DR-029. Good "warm up" after §2.1's six-fix arc closure; gets a tick on the board cleanly while the operator collects Betfair API documentation between sessions for §2.4 Fix 4 brief drafting.

**Out of scope for Session 58:** §2.4 Fix 4 cadence design (still held lightly until Betfair API docs land); §2.5 soft-book contract (separate session); §2.6 / §2.7 / §2.8 / §2.9 / §2.10 (sequenced after §2.3 + §2.4 + §2.5).

**Operator-side actions between sessions:**

1. Continue collecting Betfair API documentation (Exchange REST + Streaming) from developer.betfair.com — input for Fix 4 cadence brief drafting, §2.10 external analytics scan, and §2.4 Streaming spec.
2. Re-upload `standing_instructions.md` to bethub-rebuild Claude Project knowledge base — carried over from Session 55.
3. Optionally: review `bethub-analytical/README.md` and decide on activation timing.
4. Open Session 58 with the standard "open session 58" trigger.
