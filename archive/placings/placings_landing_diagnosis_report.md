# Placings not landing — diagnosis + clock-stop (Code report)

**Executed:** 2026-06-29, 13:35 → 13:55 ACST (single bounded Code session, per `placings_landing_diagnosis_brief.md`, LOCKED S197).
**Mode:** READ-WRITE on the one anchor (`scripts/backfill_race_metadata.py`, Phase-0 guard only); capture.db `mode=ro` for all reads; one sanctioned backlog pass via the unchanged `sync_day()` upsert. All API access read-only GETs, single-threaded, ≥1.5s between dates. Analytical/capture-side only — no v3, settlement, money-path, Betfair or scraper contact. Bet-safety clean (DR-033).
**Outcome:** Phase 0 landed and verified — the clock is stopped (`BACKLOG_FREEZE_RETIRE=True`; no recoverable date can be retired while F1 is open). Phase 1 isolated the divergence point with evidence: the API holds the positioned runners (589 for 2026-03-15), but for the recoverable tail dates they **never reach `upsert_runner`** — the race row's metadata is touched while the runner payload arrives empty under request-budget degradation; and a *second*, narrower identity-collision bug (Dubbo-class) would corrupt on write even when the payload is present. Root cause + the exact proposed fix are in §5–§6.

---

## 1. Run header

| Item | Value |
|---|---|
| SSH gate | **PASS** — `ssh racing-vps -o ClearAllForwardings=yes`, host `srv1449394`, operator ssh-agent. |
| Repo / HEAD | `/home/racing/racing-data-capture`, branch `master`, HEAD **`5f71488`** (unchanged at close). |
| Anchor (only file edited) | `scripts/backfill_race_metadata.py` — `M`, trickle code present. `subscription/racing_api.py`, `storage/database.py`, sync path **read only**. |
| capture.db | `data/capture.db` — **4,102,516,736 B (~4.10 GB)**, live WAL; reads `mode=ro`; one pass wrote via `sync_day()` upsert only; file never copied. |
| Sidecar before | `data/backlog_trickle_state.json` (mtime Jun 28 14:01): **20 dates @ strike 2, 0 exhausted** (verbatim recorded §2). |
| Sidecar after | **20 dates @ strike 3, 0 exhausted** (honest +1 from the verification pass; no rewrite, no retirement). |
| VPS wall-clock | gate `04:05:38Z` (13:35 ACST); pass 13:38:40–13:39:55 ACST; close 13:54:40 ACST. |
| Timestamps | capture.db stores UTC; report times ACST (UTC+9:30, no June DST) per DR-021. |

---

## 2. §0 baseline gate — PASS (hard STOP if not)

| Check | Required | Found | |
|---|---|---|---|
| SSH | reaches host | `SSH_OK`, srv1449394 | ✅ |
| Repo / HEAD | `master`, `5f71488` | `master`, `5f71488` | ✅ |
| Anchor state | `M`, trickle present | `M scripts/backfill_race_metadata.py`, trickle present | ✅ |
| Sidecar | present, recorded verbatim | present (802 B); 20 dates, all `{"strikes": 2}`, none exhausted | ✅ |

**Recorded drift (not a gate failure):** the prior report (2026-06-28) closed the sidecar at **strike 1**; it now reads **strike 2** — one nightly timer (2026-06-28 23:30 ACST) fired between sessions and advanced every date +1, exactly as F2 predicted. HEAD, anchor state and trickle code are unchanged, so the substrate is intact and the gate passes. The drift confirms the clock is live (strike 2/5 → retirement ~3 nights out) and makes Phase 0 more urgent: next timer fires tonight 2026-06-29 23:30 ACST. Proceeded.

**Working-tree gate.** Start dirty list = 14×`M` + 8×`??` (anchor among the `M`). Close-out `git status --porcelain` is **byte-for-byte identical** — anchor still `M`, no new tracked files (sidecar gitignored), no git state mutated (no add/commit/stash/restore/checkout/reset). No files were written to the VPS this session (every diagnostic harness ran via SSH stdin). A pre-existing `/tmp/placings_probe.py` from the prior session was left untouched.

---

## 3. Phase 0 — the clock-stop guard (the one read-write change)

**Mechanism located.** Retirement is two coupled facts: `run_backlog_pass()` sets `ent["exhausted"]=True` after `BACKLOG_EXHAUST_AFTER` (5) strikes (L269–272), and `get_backlog_dates()` (L149) drops any date with `exhausted` from the selector. At gate, **0 dates were exhausted**, so the guard need only prevent the flag from ever being set.

**The change — minimal, named-anchor, reversible.** Two edits inside the named anchor (constants region + the strike/retire region of `run_backlog_pass`), nothing else:

```diff
 BACKLOG_MAX_ATTEMPTS = 20           # per-night attempt ceiling ...
+BACKLOG_FREEZE_RETIRE = True        # PHASE-0 CLOCK-STOP (S197): while True, dates still accrue
+                                    # strikes but are NEVER marked exhausted/retired ... Flip to
+                                    # False once F1 lands; struck dates self-clear on first real fill.
 BACKLOG_MIN_DELAY = 1.5
@@ run_backlog_pass(), resultless branch
-            if ent["strikes"] >= BACKLOG_EXHAUST_AFTER:
+            if not BACKLOG_FREEZE_RETIRE and ent["strikes"] >= BACKLOG_EXHAUST_AFTER:
                 ent["exhausted"] = True
                 retired.append(date_str)
```

With the guard ON the retire condition is unreachable regardless of strike count; strikes still accrue (honest F2 signal intact). When the F1 fix lands and a real placing arrives, the existing `gained > 0` branch does `state.pop(date_str)` — struck dates self-clear with no further deploy. `sync_day`, `_sync_single_*`, `upsert_runner`, the schema, the recent-window pass and `main()` are untouched. File `py_compile`-clean.

**Verification (§5, all three):**
1. **Diff** — exactly the two lines above; `grep` confirms two `BACKLOG_FREEZE_RETIRE` references (definition + gate), no other change.
2. **One backlog pass** (13:38:40–13:39:55 ACST, `delay=1.5`): `BACKLOG PASS: attempted=20 filled=0 placings=0 resultless=20 walled=0 retired=[] oldest_remaining=2026-03-01 remaining_backlog_dates=99`. Struck dates logged `strike 3/5`; **`retired=[]`**; selector held at 99 (did **not** fall by retirement).
3. **Sidecar honest** — all 20 dates moved 2 → 3 (the pass's own +1); **no `exhausted` flags**, no other dates touched, no rewrite.

Clock-stop **confirmed**.

---

## 4. Phase 1 — the trace (read-only)

Method: a standalone read-only harness (run via SSH stdin, never committed, not written to the VPS) importing `subscription.racing_api._api_get` and the storage key functions; capture.db opened `mode=ro`; API GETs paced ≥1.6s. No sync function or module was modified.

**Sync path identity keys.** `upsert_race` conflict key = `(race_date, venue_normalised, race_number)` — `subscription_meet_id` is **stored but not part of race identity**. `compute_runner_key` = `N:<number>` (else `S:<name>`). `upsert_runner` merges on `(race_id, runner_key)` with `COALESCE(excluded, existing)`. `sync_day` sources runners **only** from `/australia/meets/{id}/races` (no results endpoint exists in the path; `/australia/results` 404s).

### §6.2 trace — Dubbo R1 2026-03-15 (the worked case)

1. **Race identity.** API meet `met_aus_626943265490` course "Dubbo"; `normalise_venue("Dubbo")="dubbo"`. `upsert_race` key `(2026-03-15,"dubbo",1)` resolves to a **single** DB row `race_id=179226` (R1–R9 = 179226–179234, one row per number; no duplicate row for this meet). 179226 is a *genuine thoroughbred* row (`race_class='BOOT PREL'`, `track_type='turf'`, `created_at=2026-03-15T00:22` pre-race, `subscription_meet_id` now set, `subscription_synced_at=04:09:22` — touched by this session's pass).
2. **Runner identity.** API R1 = 8 positioned runners keyed `N:7`(I'm A Beaut, pos1), `N:1`(Big Lon, 2), `N:6`(Cool Aza Cat, 3), `N:4`(Words Of Fire, 4), `N:8`, `N:5`, `N:2`/`N:3`(109=scratched). DB row 179226 = 8 runners keyed `N:2,3,4,5,6,8,9,10`, **all `results_source='betfair_only'`, all `finish_position` NULL** — a **disjoint field** (Karinya Haz, Oursurfinsafari, Beancounter…). Same namespace (`N:<number>`), but the numbers map to **different horses**.
3. **Where it diverges.** The DB row was populated by the **Betfair/live-capture path** with a field foreign to the API: none of its 8 horses appear anywhere in the API's 03-15 AU meets; conversely the API's positioned horses have no home on this row (Big Lon → DB *Nowra* R1; Cool Aza Cat/Blazing Courage → DB *Nowra* R4 / *Port Macquarie* R6; I'm A Beaut/Words Of Fire/Simply Sonnet → absent). Because race identity is code-blind (no thoroughbred/greyhound separation) the foreign Betfair field shares the thoroughbred row, and the `N:<number>` runner-key collides across sources.
4. **Does the write even attempt?** This pass: 2026-03-15 synced **"63 races, 0 runners"** — `_sync_single_race` looped an **empty `runners` array**, so `upsert_runner` was **never reached** (the metadata upsert ran; the position-bearing write did not). A fresh isolated probe of the *identical* endpoint returns the full field (8 positioned). So the runners exist API-side; they did not reach the writer during the walk. **Read-only simulation** of the upsert had the payload been present: of 8 API runners → `add=2` (N:7, N:1 new) and **`collide_DIFFERENT_horse=6`** (e.g. API "Cool Aza Cat" pos 3 would COALESCE-overwrite the unrelated Betfair "Beancounter") — i.e. even a successful sync would corrupt, not cleanly land.

### §6.1 contrast — the other two reproduction cases

- **Single-meet recoverable (Townsville R1, `met_aus_843845379975` → race_id 179282):** API 10 positioned vs DB 10 `betfair_only`/NULL — **same horses, same `N:` keys** (`collide_same_horse=9/10`; the 1 "different" is an apostrophe artifact, "Parppy 'N' Me" vs "Parppy N Me"). Keys reconcile perfectly; blocked **only by non-landing**, not identity.
- **Duplicate-meet (bet365 Swan Hill):** both API meet_ids normalise to `"swan hill"` → **same** race_id 179275. Populated id `…724345`: 13 positioned, `collide_same_horse=12/13` (again one apostrophe case, "Ellie's Song"). Empty id `…671164`: a single junk runner `Villermont/Millinery/2022` keyed `N:0` (the F3 shadow). Same picture: correct field present, positions just not landed; the empty duplicate adds noise but is not the blocker.
- **Recoverability, fresh, the sync_day way:** for 2026-03-15 the API returns **589 positioned runners** (718 total) vs DB **263 in-scope filled** — ~326 recoverable placings on this date alone, confirming F1's figures.

---

## 5. Root cause

The placings fail to land via **two distinct mechanisms** (smallest isolable set; the first dominant, the second narrower-but-corrupting):

**RC-1 — non-landing of the recoverable tail (dominant; well-evidenced).** The oldest-first backlog walk lands dates front-to-back, but the leftover daily Racing-API request budget covers only ~9–14 dates per night. Dates 2026-03-01…03-14 landed during an earlier period (now `results_source='subscription'`, ~92% filled) and remain in the selector forever on their genuine ~8% residue — so every night they are re-attempted **first** and spend the budget. The recoverable tail (03-15→) is reached only after the budget is exhausted and comes back as **race shells with empty `runners`** (`races_synced>0`, `runners_synced=0`) — the metadata upsert runs, `upsert_runner` is never reached, no position lands, and the date is mis-classed **resultless** (it strikes). The tail's runners stay Betfair-sourced with NULL positions. For this class (Townsville, Swan Hill) the runner keys already match the API exactly, so the *only* thing missing is a live-budget fetch reaching the writer. *(The exact API-side degradation mode — runner-stripped 200s vs. budget cap — is not 100% isolable read-only without re-running a heavy multi-date pass, which §10 forbids; the clean cutover at the 10th date of the pass and the full-field result on isolated re-probe are the evidence.)*

**RC-2 — runner-key identity collision on cross-sourced rows (narrower; proven by simulation).** Where the Betfair path pre-populated a race row with a field **foreign** to the API (Dubbo: 6/8 different horses on shared `N:<number>` keys — a code-blind `(date, venue_normalised, race_number)` race match collapsing distinct fields onto one row), a *successful* sync would `COALESCE`-overwrite the wrong horse rather than land cleanly. This is the §2.1 Fix-5 venue/key-normalisation drift sibling. It is latent today only because RC-1 keeps the payload from arriving — fix RC-1 alone and this class corrupts.

---

## 6. Proposed fix (load-bearing — for the next brief to commission)

Smallest coherent change; **sequence RC-2 before RC-1** so recovering the tail cannot corrupt cross-sourced rows. Schema implication: **none**.

1. **RC-2 guard first — `subscription/racing_api.py::_sync_single_runner` (+ helper in `storage/database.py`).** Before upserting an API runner, reconcile by **horse identity**, not saddlecloth number alone: if `(race_id, N:<number>)` already holds a runner whose normalised name differs **and** whose source is non-subscription (Betfair), do **not** COALESCE the position onto it — match the API runner to the existing row by normalised name / `subscription_horse_id`, or insert under a name-based key. Note: `normalise_runner_name` is punctuation-sensitive (apostrophes), so any name-based reconciliation must strip punctuation or the Townsville/Swan-Hill "same horse" cases will false-miss.
2. **RC-1 fetch fix — `subscription/racing_api.py::sync_day`.** (a) Pace the per-meet `/races` calls: thread the `delay` through and `time.sleep(delay)` **between meet requests** (today the ≥1.5s delay is only *between dates*; within a date `sync_day` fires N meet calls unthrottled — the likely driver of mid-walk budget degradation). (b) Detect a runner-less "Results" payload (`race_status=='Results'` with empty `runners`) and surface it as a transient error so `run_backlog_pass` classes it **wall/transient** (recoverable, no strike, retry next night) instead of the current silent "resultless → strike". (c) Address the starvation: let the backlog selector advance past dates whose remaining deficit is genuine residue (e.g. prioritise by *recoverable* deficit, or skip a date whose unfilled in-scope runners the API also has no position for) so the recoverable tail is reached within budget.

This unblocks the operator goal (recoverable placings actually landing) for the Townsville/Swan-Hill majority via (2), without corrupting the Dubbo-class via (1). After it proves out, flip `BACKLOG_FREEZE_RETIRE=False` and the struck dates self-clear.

---

## 7. Findings (surprises → findings; report-only)

- **F-a — the F1 "identity mismatch" is two bugs, not one.** For the *majority* (Townsville, Swan Hill) keys match the API perfectly — the block is non-landing (RC-1), not identity. Only the Dubbo-class has a true identity collision (RC-2). The prior report's single "identity mismatch upstream of upsert_runner" framing fits Dubbo but undercounts the dominant fetch/landing failure.
- **F-b — duplicate meet_ids collapse to one row, not two.** Both Swan Hill API meet_ids normalise to `"swan hill"` and share `race_id=179275`; the "empty" duplicate injects a junk `N:0` runner but does not create a shadow row. F3's duplication is real but is *noise on a shared row*, not the blocker.
- **F-c — `venue_normalised` drift is live** (`"bet365 swan hill"` vs `"swan hill"`; `"Ladbrokes Pioneer Park"→"alice springs"`; `"Pioneer Park"→"pioneer"`). Not the proximate cause here but a standing identity hazard for any name-based fix.
- **F-d — resultless mis-classification.** RC-1's empty-payload responses are counted `resultless` and strike honest dates — the F2 clock is partly *manufactured* by RC-1, not just exposed by it. The Phase-0 freeze correctly neutralises the consequence; the RC-1 fix removes the cause.

---

## 8. Self-assessment

- **Isolable read-only and done:** the divergence point (write never attempted — empty runner payload reaches `_sync_single_race`), the identity keys, the Dubbo foreign-field collision (by simulation), the three-case contrast, and fresh recoverability (589 vs 263). Phase 0 landed and triple-verified.
- **Not fully isolable read-only:** the precise API-side reason the tail payloads arrive runner-less (budget-stripped 200 vs hard cap) — confirming it would need a controlled heavy multi-date pass, which §10 forbids. Stated as strongly-evidenced inference (RC-1), not asserted certainty.
- **Scope held:** one file edited (anchor), two named lines; capture.db `mode=ro` for reads, one sanctioned `sync_day()` pass; no v3/settlement/money-path/Betfair/scraper; no recovery/backfill run; sidecar not rewritten (honest +1 only); no git state mutated; dirty list byte-identical bar the already-`M` anchor; no files written to the VPS. Per §7, this is a **complete** Phase 0 + Phase 1 — not a partial stop.
