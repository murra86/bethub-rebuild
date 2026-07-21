# Placings backfill + nightly results-sync fix — VPS capture-side brief

**Status:** LOCKED (Session 191). Code read-back confirmed faithful + released.
**For:** Claude Code, single bounded out-of-session run.
**Mode:** READ-WRITE on the VPS `racing-data-capture` repo + capture.db (writes via the existing pipeline only). No v3, no live-betting, no settlement contact.

---

## 1. What this brief is and is not

This is a **surgical fix + bounded data-recovery run** on the VPS racing-data capture pipeline. Two halves, one Code session:

- **The fix (forward):** stop the nightly Racing-API results sync from skipping dates whose results publish *after* it runs, so finishing positions resume landing in capture.db going forward.
- **The recovery (backfill):** re-pull the missed finishing-position data for the gap window (2026-03-01 → 2026-06-25) that the bug dropped.

It **is not**: an auto-settlement build (placings stay a manual operator flag per DR-033 — see §9); a schema change (the columns already exist); a v3 / settlement / live-betting change of any kind; a fix to the harness/greyhound enrichment mapping (separate, excluded §9). Surprises become findings in the report, not mid-session escalations or scope chases. Remediation of anything found routes to the next operator-Claude session, not Code's report.

## 2. Why this work exists

The VPS supply-side review (`vps_supply_review.md`, S190–191) quantified and re-confirmed the S174 diagnosis: the finishing-order ordinal (1st–4th per runner, sourced from the Racing API) collapsed from ~75–80% coverage through February 2026 to ~0.1% by May, and sits at 0.1% now. Root cause confirmed live: the nightly subscription sync stamps each date as synced on first touch — before results publish — and never re-pulls it. This is **analytical data** (the operational line settles win/lose off Betfair only, per DR-033; placings are the operator's manual flag). The value is preserving a cheap-to-capture / expensive-to-reconstruct record while it is still inside the Racing API's 12-month AU window. Every day unfixed, the leading edge of recoverable data ages out.

## 3. Pre-reads

Required (on the VPS, `racing-data-capture` repo):
- `subscription/racing_api.py` — the `sync_day()` path that pulls Racing-API results and stamps `subscription_synced_at`.
- `scripts/backfill_race_metadata.py` — `get_unsynced_dates()` (the `WHERE subscription_synced_at IS NULL` filter) and the `--date` / `--days` flags.
- The metadata-backfill cron + timer (`racing-metadata-backfill.timer`; daily cron `30 11 * * *` UTC).

Reference-only (Mac, rebuild folder — read if context needed, not required):
- `vps_supply_review.md` §4 (the quantified gap + the confirmed-still-live mechanism, with the function anchors).
- `data_sources.md` (Racing API role + AU coverage tier).
- `decisions.md` DR-033 + the DR-029 S191 amendment (why placings are analytical-only and settlement never reads them).

## 4. System access

- **VPS** via SSH (`racing-vps`), run from the operator's logged-in Mac session so the passphrase-protected key is available through the ssh-agent (per S190 — a freshly spawned shell without the agent fails publickey). Use `-o ClearAllForwardings=yes` to avoid the harmless port-8400 collision with the live `/health` tunnel.
- **Read-write** on the `racing-data-capture` repo source files (the fix) and on capture.db **through the existing pipeline scripts only** (the backfill).
- **No hand-edits to capture.db.** All writes go through `sync_day()` / `backfill_race_metadata.py` via their normal code path. Measurement reads open capture.db `file:…?mode=ro` and query in place — never copy the file (it is a live ~4 GB WAL database).
- Adelaide local timestamps (ACST, UTC+9:30, no DST in June) for every time-of-day reference in the report, per DR-021. capture.db stores UTC; convert on report.

## 5. Scope — the work, in order

### §5.1 — Ground the anchors + working-tree state (first, before any edit)
- Locate `get_unsynced_dates()` in `scripts/backfill_race_metadata.py` and `sync_day()` in `subscription/racing_api.py`; confirm the live line ranges and the exact `subscription_synced_at IS NULL` filter + the first-touch stamp write. The review named these by function; confirm by reading before editing.
- Read the repo working-tree state (`git status`, `git diff --stat`). The VPS repo may be dirty from the March rework. Record the dirty file list at session start. If any dirty region intersects the edit anchors below, **stop and surface as a finding** before editing — do not edit through someone else's uncommitted work.

### §5.2 — The forward fix (the bug)
**Behaviour required:** recent dates must be re-pulled until their results are actually captured, then stop — so a date synced before results published gets retried and filled, rather than stamped-and-abandoned. The fix must be **bounded** (it must not re-pull the entire history nightly, and must not retry a resultless date forever).

**Recommended implementation** (Code may choose a cleaner hook against the live code and surface the choice as a finding): a **trailing re-pull window** — each nightly run re-syncs the last N days (recommend **N = 14**) regardless of the `subscription_synced_at IS NULL` filter, in addition to genuinely-unsynced dates. Rationale: AU results publish within hours-to-days of a race; a 14-day trailing re-pull guarantees every date is re-touched enough times to catch late-publishing results, is naturally bounded to 14 days of work, and is safe because `sync_day()` upserts idempotently (COALESCE).

**Alternative Code may prefer** (name it, don't silently swap): only stamp `subscription_synced_at` once results are actually present for the date (so the existing IS NULL filter self-heals), with an age bound so an abandoned/resultless date is not retried indefinitely. If Code judges this cleaner against the real code, it may implement it instead — but must state which it chose and why in the report.

Edit only the named anchors. After each edit, `git diff <file>` to confirm only the intended change landed.

### §5.3 — The backfill (recovery run)
- Run the existing `backfill_race_metadata.py` over the gap window **2026-03-01 → 2026-06-25** using its `--date` / `--days` flags (which already force past the IS NULL filter). All races in the window, not bet-relevant only (broad-scope capture — operator directive).
- Respect the Racing API rate limit (5 req/sec). Confirm the script's existing throttle; do not exceed it.
- **Resumable / single-session bounded:** if the full window will not complete in one Code session, recover as much as cleanly completes, then **stop and report the exact leftover date range** for a follow-up run. Partial-but-clean beats complete-but-rushed.
- The backfill writes through `sync_day()`'s idempotent upsert — existing rows are filled, not duplicated.

## 6. Sequencing within session
1. §5.1 ground anchors + working-tree state (gate: stop if dirty regions collide).
2. Capture the **pre** baseline (§7).
3. §5.2 forward fix; `git diff` confirm.
4. §5.3 backfill run (resumable).
5. Capture the **post** baseline (§7).
6. Write the report (§8).

The fix lands before the backfill so the pipeline is correct before the recovery runs through it; the backfill is the larger, interruptible operation, so it sits late where a clean stop is cheapest.

## 7. Empirical verification (pre and post)
**Pre-backfill baseline** (capture.db, `mode=ro`): `finish_position` coverage by race month across the gap window and the pre-gap reference — % of runners with non-null `finish_position` for 2025-11 → 2026-06. Expected to reproduce the review's curve (~76–80% through Feb → 21% Mar → 6% Apr → 0.1% May/Jun).
**Post-backfill:** the same query. Success = the gap months (Mar–Jun) lift materially toward the pre-gap ~75–80% level, bounded by what the Racing API actually holds for AU (thoroughbred confirmed; harness/greyhound thin — a shortfall there is a capability limit, not a fix failure; quantify it rather than score it).
**Forward-fix verification — carve-out:** proving the fix catches *future* late-publishing results would need real results to publish (out-of-session). In-session, prove the **mechanism** instead — show a recently-stamped date is now re-pulled by the changed path (e.g. an inspection/dry-run that the trailing window re-touches a date whose `subscription_synced_at` is already set). State this as an in-session-mechanism vs out-of-session-live carve-out (Session 36 precedent).

## 8. Output spec
Single file: `placings_backfill_report.md` (rebuild root). Sections: run header (SSH gate, paths, VPS wall-clock, Adelaide stamps); working-tree state at start; pre-backfill coverage table (by month); the forward fix (which approach chosen + why, the anchor, the bound, `git diff` confirmation); the backfill run (date range processed, rows filled, rate-limit adherence, leftover range if any); post-backfill coverage table (before/after by month); forward-fix mechanism verification (+ the carve-out); findings; self-assessment (what couldn't be tested + why). Rough length 250–400 lines; exceed only if the work warrants, flagged in self-assessment. **Does not contain:** recommendations, remediation plans, auto-settle design, or any scope into other VPS capture work — those route to the next operator-Claude session.

## 9. Hard limits (non-negotiable)
- **No auto-settlement.** Placings stay a manual operator flag (DR-033). This brief captures the data; it does not wire it into any settlement path. Do not build, scaffold, or "prepare" auto-settle.
- **No contact with the operational line.** No edits to `bethub-v3`, settlement, live betting, the operational store, or any money path. Capture-side / analytical-line only (DR-027/028).
- **No schema changes to capture.db.** The columns exist; this is a sync-logic fix + a recovery run.
- **No hand-edits / direct surgery on capture.db.** All writes go through the existing pipeline scripts. Never copy capture.db; measurement reads are `mode=ro` in place.
- **No git state mutation.** No `git add`/`commit`/`stash`/`restore`/`checkout`/`reset`. Read tree state at start; `git diff` after each edit; `git status` at close to confirm the dirty list is unchanged but for the named anchors.
- **Edit only the named anchors** (`get_unsynced_dates` / `sync_day`, or the single cleaner hook Code names). No drift into adjacent capture code.
- **No fix to the harness/greyhound enrichment mapping** (review Findings C/D) — separate concern, excluded here.
- **No touch to the soft-book scrapers or the Betfair snapshot path** — different capture streams, out of scope.
- **Single bounded session.** If the backfill won't complete cleanly, partial + leftover-date range is a finding, not a continuation.
- **Don't fix the named debt** (no test framework, no migration framework) — out of scope.

## 10. What happens after Code's session
The next operator-Claude session (S192) reads `placings_backfill_report.md` and triages: confirm the gap recovered (post-coverage lifted), the forward-fix mechanism sound, the chosen approach acceptable, and any leftover date range routed to a short follow-up backfill run. Then back to the pre-cutover queue: launcher capture-data provisioning → settlement-worker brief → promo-seed item → W16 cutover. Code does not write the next brief.

## 11. Cross-references
- **DR-033** (data-source roles — Betfair operational/settlement, Racing API analytical/enrichment, placings manual flag) — the controlling decision; this brief sits entirely on the analytical line.
- **DR-029 amendment, S191** (settlement does not read VPS placings — supersedes the old auto-settle-reads-VPS claim).
- **DR-027 / DR-028** (the two-database operational/analytical boundary this stays on).
- **DR-021** (Adelaide-local timestamps in the report).
- `vps_supply_review.md` §4 (the quantified gap + confirmed-live mechanism + function anchors).
- **Session 174** (the original finish-position pipeline diagnosis).
- `data_sources.md` (Racing API AU coverage tier + role).
- **Excluded / parked:** harness-greyhound enrichment mapping (Findings C/D); the empty-runner `resolve_race` edge (Finding A); the multi-code label fix (Finding C) — all separate from this capture-integrity fix.
