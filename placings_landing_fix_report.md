# Placings-landing surgical fix — Code report

**Executed:** 2026-06-29, 15:01 → 15:31 ACST (single bounded Code session, per `placings_landing_fix_brief.md`, LOCKED S198).
**Host / mode:** racing-data-capture VPS (`root@187.77.183.9`), live, READ-WRITE on three named anchors only. capture.db `mode=ro` for verification reads; the fix writes through the normal `sync_day()` / guarded `upsert_runner()` path. Capture-side analytical only — no v3, settlement, money path, or Betfair operational pricing (DR-033).
**Outcome:** Both parts landed and verified. **Part A** (write-side identity guard) landed and verified clean **before** Part B. **Part B** (fetch-side fix) landed; a surprise surfaced and was resolved in-scope (§Findings F-1). Empirical verification §9 is green: placings land on correctly-named horses, no cross-source overwrite, no false strikes, and the per-night walk reaches the recoverable tail. As the final edit, `BACKLOG_FREEZE_RETIRE` was flipped to `False`.

---

## 1. Baseline (dirty tree)

| Item | Value |
|---|---|
| HEAD | `5f71488` (unchanged at close) |
| Dirty at start | 14 × `M` + 8 × `??`. `subscription/racing_api.py` **clean**; `storage/database.py` and `scripts/backfill_race_metadata.py` already `M` (Phase-0 freeze + in-flight work). |
| Pre-existing `database.py` regions (NOT touched) | `save_betfair_snapshot` / `save_betfair_snapshots_batch` (~L511–572), `flag_final_betfair_snapshot` (~L692–724) — left byte-identical; their diff left-side line numbers are unchanged, content only relocated by my insertions above them. |
| Pre-existing `backfill` region | the trickle rewrite + Phase-0 freeze (the named RC-1 anchor); my B1/B2 edits are within it, additive. |

---

## 2. What changed (three files, no schema)

### Part A — write-side identity guard (LANDED FIRST)

**`storage/database.py`** — two new helpers after `normalise_runner_name` (+ `import re`):
- `robust_name_match_key(name)` — punctuation-deleting, whitespace-collapsing, lowercasing compare form used **only** for reconciliation (F-c): `"O'Reilly's Lad"` ≡ `"oreillys lad"`. The stored `runner_key` derivation is **unchanged** (no key migration / no schema change).
- `resolve_result_write_key(conn, race_id, candidate_key, runner_name)` — the §6 decision table, read-only: returns the existing same-horse row's key if the horse is already present under any key; else the candidate `N:<number>` if free/same-horse; else a name key `S:<robust>` so the API horse is inserted as its own row rather than COALESCE-overwriting a differently-named incumbent; else `None` (skip-with-finding).

**`subscription/racing_api.py`** — `_sync_single_runner` now calls the guard immediately before the write: `write_key = resolve_result_write_key(...)`; on `None` it logs and skips; otherwise it sets `fields["runner_key"] = write_key` and upserts. Match on **horse identity**, never the bare saddlecloth number.

### Part B — fetch-side fix (LANDED SECOND)

**`subscription/racing_api.py` — `sync_day()` return contract + pacing:**
- Additive return signals: `positions_seen` (runners that carried a finishing position) and `truncated` (a per-meet fetch raised, **or** the date returned races but **zero** runners across all of them — the degraded/quota signature). `_sync_single_race` / `_sync_single_runner` extended to count positions.
- **Per-meet pacing** (F-1): new `delay` param (default `0.0`); when `>0`, sleeps `delay` between per-meet `/races` fetches so the burst is not rate-degraded to empty 200s. `run_backlog_pass` passes its `delay`; the recent-window path (delay `0`) is unchanged.

**`scripts/backfill_race_metadata.py`:**
- **B1** — `run_backlog_pass` reads `truncated`/`positions_seen` and replaces the 3-branch classifier with 4 branches: `progress` (gained>0); `wall/transient` (error **or** truncated → no strike); `resultless+strike` (clean, fully-fetched, runners present, `positions_seen==0`); `complete-noop` (positions present but no new fill → no strike, no wall). A truncated or partial fetch can no longer manufacture a strike.
- **B2** — `get_backlog_dates` reorders the walk by **recoverable deficit DESC** (unfilled in-scope runners), tie-broken oldest-first, so the near-complete early-March residue stops monopolising the per-night budget.
- Passes `delay` to `sync_day`.

### Freeze (final edit)
`BACKLOG_FREEZE_RETIRE`: `True` → **`False`** (§7 last step), only after §9 verified clean.

---

## 3. Verify results (§9, before / after)

### 3.1 Part A guard — read-only logic verify (before any write)

| Reproduction race | API runners | Resolution | Different-horse overwrite? |
|---|---|---|---|
| **Dubbo R1** (179226, foreign Betfair field) | 8 | 2 → free key (N:7, N:1); **6 → redirected to `S:<name>`** off colliding number keys | **0** (asserted) |
| **Townsville R1** (179282, same field) | 10 | **10 → existing same-horse row** (incl. apostrophe `"Parppy 'N' Me"`→N:6) | **0** (asserted) |

### 3.2 RC-1 + RC-2 landing — `sync_day('2026-03-15')`, before/after

| Metric | Unpaced (V1) | **Paced, delay=1.5 (V1b)** |
|---|---|---|
| runners_synced / positions_seen | 208 / 155 | **414 / 327** |
| truncated | false | false |
| 03-15 in-scope filled | 263 → **263** (0 net) | 263 → **346 (+83)** |
| Townsville R1 filled | 0/10 | **8/10** (N:7,N:10 = pos 109 scratched) |

**RC-2 corruption proof (V1b, Dubbo R1 row-by-row):**

| Class | Rows | Result |
|---|---|---|
| Betfair incumbents (N:2,3,4,5,6,8,9,10) | 8 | **all unchanged, finish_position still NULL** — 0 overwrites |
| API horses on free keys | N:7 I'm A Beaut→1, N:1 Big Lon→2 | correct |
| API horses redirected to name keys | `S:cool aza cat`→3, `S:words of fire`→4, `S:simply sonnet`→5, `S:blazing courage`→6, `S:tick`/`S:velocette`→scratched | correct horse, correct position |

> Townsville (same-field) positions land on the **existing** rows; Dubbo (foreign-field) positions land on **new** rows; in both cases no differently-named incumbent is overwritten. The guard behaves identically live and in the read-only verify.

### 3.3 B1 no-false-strike — deployed `run_backlog_pass` classification (monkeypatched I/O, no DB/API/sidecar touch)

| sync_day signal (gained) | Classification | Strike? |
|---|---|---|
| clean, positions, **new fill** (gained>0) | progress | no |
| **truncated** fetch | wall / transient | **no** |
| fetch error (e.g. 429) | wall / transient | no |
| clean, runners, **0 positions** (genuine resultless) | **resultless** | **yes (+1)** |
| clean, positions present, **no new fill** (already complete) | complete-noop | no |

### 3.4 B1 (live) + B2 + RC-1 recovery — one budgeted `run_backlog_pass`

| Observation | Value |
|---|---|
| 1st date attempted (B2: deficit-first) | **2026-06-06** (deficit 1421) — **not** 03-01 (deficit 39, sits at #97) |
| 06-06 result | **+1123 placings** (gained>0, progress, not struck) |
| 04-25 / 04-04 / 05-16 | **truncated → wall (no strike)**; 3 consecutive → walk stopped |
| Sidecar before → after | `{strike 3: 20}` → `{strike 3: 20}` — **unchanged**, `retired=[]` |
| Freeze during 2–4 | `True` throughout (no retirement) |

### 3.5 B2 ordering (read-only, deficit-first)

`get_backlog_dates()` now returns, e.g.: `#1 2026-06-06 (1421)`, `#2 2026-04-25 (1407)`, `#3 2026-04-04 (1391)` … with the early residue at the back — **`2026-03-02` #96 (46)**, **`2026-03-01` #97 (39)**. 99 backlog dates total.

---

## 4. B2 mechanism choice

Chose **deficit-priority ordering** (most unfilled in-scope runners first) over the per-night single-probe cap. Rationale: every backlog date is currently struck at the *same* level (strike 3), so a strike-based "frozen-struck to the back" reorder cannot discriminate near-complete residue from the recoverable tail. The unfilled **deficit** does: early-March residue is 39–46, the recoverable tail 278–1421. Ordering by deficit puts recoverable-rich dates first (so the per-night attempt budget **and** the Racing-API request budget reach them while fresh) and lets residue fall to the back, where it self-deprioritises further as it completes. This is the brief's "frozen-struck residue to the back" intent realised via a robust, empirically-verifiable signal.

---

## 5. Findings (surprises → findings, not escalations)

- **F-1 (load-bearing) — B1+B2 alone do not land placings; per-meet pacing was required.** The first paced-free `sync_day('2026-03-15')` fetched only **208/718** runners and landed **0 net** — Dubbo and Townsville came back empty *within sync_day's unpaced 10-meet burst*, while an isolated, 1.6s-paced per-meet sweep returned **all 10 meets / 718 runners / 589 positions**. The degradation is the RC-1 cause reproducing *inside a single date* and returns empty 200s (so `truncated=False`). Per-meet pacing is exactly the gap the brief flags in §5 ("sync_day … No pacing or budget awareness") and diagnosis §6-2a; it is within the named `sync_day` anchor and necessary for §7's "fully fetched payload / untruncated fetch and its positions land" contract. Added as part of Part B. With pacing, 03-15 landed +83 and 06-06 landed +1123.
- **F-2 — residual truncation persists under an exhausted daily budget.** Even paced, V1b fetched 414/718 and the V2 pass walled after one date. This session's own verification probing consumed much of today's Racing-API request budget; on a normal night with a fresh budget the paced fetch should be materially more complete. Crucially, B1 makes this **safe regardless**: truncated/partial fetches are classified transient (no strike), so no recoverable date is ever wrongly retired while completeness builds over nights.
- **F-3 — the new `complete-noop` branch protects the already-filled early-March dates.** Dates whose payload carries positions but yield no new fill (03-01…03-14, ~92% filled) are classified `complete-noop`: never struck, never retired, parked at low deficit at the back. Only clean, fully-fetched, genuinely positionless dates strike and (freeze now off) retire after `BACKLOG_EXHAUST_AFTER`.

---

## 6. Dirty-tree confirmation

- **No git operations of any kind** were run (no add/commit/stash/restore/checkout/reset). HEAD `5f71488` unchanged.
- `git status --short` at close = baseline **plus exactly one new entry**: `subscription/racing_api.py` (`M`) — the third target, clean at start. The other two targets (`storage/database.py`, `scripts/backfill_race_metadata.py`) remain `M`; the remaining 13 `M` + 8 `??` are byte-identical to baseline. No new `??` files (every diagnostic harness ran via SSH stdin; nothing was written to the VPS).
- After every edit, `git diff <file>` confirmed only intended lines changed; the pre-existing `database.py` Betfair regions were not touched. All three files `py_compile`-clean.

---

## 7. Self-assessment

- **Proven:** Part A guard (read-only verify + live V1b: 0 overwrites, correct rows); RC-1 landing (V1b +83 on 03-15, V2 +1123 on 06-06); RC-2 no-overwrite; B1 all four branches (deterministic unit on the deployed function) + live truncated→wall with an unchanged sidecar; B2 (deficit ordering + the pass reaching 06-06 first, never 03-01). Freeze held through steps 2–4 and was lifted only as the final edit.
- **Part A landed and verified clean before Part B** — the sequencing contract held; the payload was never fed through an unguarded write path.
- **Freeze-off is safe under the new logic:** recoverable dates land → strikes clear; already-filled residue → `complete-noop` (never strikes, never retires); only genuinely positionless dates strike → retire. Residual truncation (F-2) only ever classes wall (no strike), so it cannot wrongly retire.
- **Not fully closed in-session (honest):** completeness of a *single* night's fetch under today's exhausted budget (F-2) — the fix is correct and safe, but full per-date landing builds over nights with fresh budget; not provable in one session without the very budget this session spent verifying.
- **Recovery footprint (disclosure):** the §9 proofs landed ~**1,206** correct placings across two dates (03-15 +83, 06-06 +1123) as the sanctioned one-budgeted-pass + named-date proof. This is **not** the full backlog replay — that systematic, monitored recovery remains the next session's milestone (§12).
- **Scope held:** three named files; no schema/migration; no recovery run; no git ops; capture-side analytical only (DR-033); ACST timestamps (DR-021); surprises booked as findings, no mid-session escalation.

---

## 8. Hand-off (§12)

Next operator-Claude session: confirm the guard + fetch fix verified clean (this report), confirm `BACKLOG_FREEZE_RETIRE=False`, then commission the **recovery run** (systematic replay of the recoverable backlog, deficit-ordered, paced) — the "start the data recovery" milestone. Watch F-2: pace and let nightly fresh-budget passes build completeness; B1 guarantees no recoverable date retires while they do.
