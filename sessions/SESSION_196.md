# Session 196 — trickle check-up found the backlog WEDGED; diagnosed
# (grounded against live code + live API + capture.db); the placings
# trickle-fix brief DRAFTED + LOCKED + Code read-back confirmed + RELEASED

**Opened:** 2026-06-28 19:13 ACST
**Closed:** 2026-06-28 21:09 ACST
**Tool routing:** Claude Chat (trickle check-up + diagnosis via Desktop
Commander SSH/SQLite/live-API probe; brief drafting via the
brief-drafting skill). No v3 code touched in Chat; the brief commissions
out-of-session Claude Code.
**Governing DRs:** DR-021 (Adelaide time); DR-033 (placings analytical,
settlement Betfair-only — the controlling decision behind the fix's
bet-safe-by-construction framing); DR-027/028 (capture-side boundary).

---

## Anchor

- Open:  `TZ="Australia/Adelaide" date` → 2026-06-28 19:13 ACST (Sun).
- Close: `TZ="Australia/Adelaide" date` → 2026-06-28 21:09 ACST (Sun).
- Same-workday continuation of S195 (closed 16:52 same day). ~2h active,
  no day-rollover, no split trigger — full close.

## Pre-flight checks (open ritual)

Clean drift-check: `current_state.md` carried the matching 2026-06-28
16:52 S195-close stamp; `SESSION_195.md` present + non-empty;
`v3_build_picture.md` updated at S195 close. **One anomaly surfaced at
open:** `.close_out_backups/` held a stale `SESSION_195_opening_prompt.md`
alongside the live `SESSION_196` one — the S195 close-out claimed to sweep
it but the sweep didn't land (the S195 DC-server hang is the likely
reason). Swept this close.

## Session shape

A check-up that turned into a diagnose-and-commission session. The
2026-06-28 trickle check-up (due today, surfaced first at open) found
the backlog-trickle **wedged**, not progressing. The session grounded
the cause against the live VPS code, the live Racing API, and capture.db;
answered the operator's question ("can we get all placings from the
Racing API?") empirically; then drafted, locked, and released the fix
brief to Code. Single clean arc, no pivot.

## What was delivered

1. **Trickle check-up — WEDGED, not closing.** Read the VPS
   `metadata_backfill.log`: three nightly runs (2026-06-25/26/27) each
   filled **zero** dates; `remaining_backlog_dates` climbed **95 → 96 →
   97** instead of falling. Not "slow" — stuck.

2. **Root cause diagnosed + grounded.** The pass walks oldest-first; its
   oldest dates' only gaps are genuinely-resultless races. It mis-reads
   the resulting zero-runner dates as a quota wall (3 consecutive →
   `break`, L213–218) and stops the night before reaching any recoverable
   date behind them. The strike/retire logic can never fire on these
   front dates (`idx < last_fill_idx` with `last_fill_idx == -1` forever,
   L228) → they are immortal and gate everything. Each night one fresh
   date ages into the window → the slow climb.

3. **Operator's "can we get all the placings?" — ANSWERED empirically.**
   The sync is **not** the problem: 2026-03-01 is 91% filled (50 of 55
   thoroughbred races, 456 runners). The 5 stuck races are one meeting —
   **Naracoorte** — and a live Racing-API probe confirmed the API returns
   those races + runners but **null finishing positions** (only
   scratched=109). Signature of an abandoned / never-resulted meeting:
   the placings don't exist on the API's side. Conclusion: we can pull
   placings for essentially all genuinely-resulted races; a small
   residue (abandoned meets + individual non-finishers) is unrecoverable
   and normal.

4. **A secondary wrinkle flagged.** The nightly logged "0 runners" for
   2026-03-01 while the live API returns runners for it now → likely the
   sync occasionally tripping on **unstable/duplicate meet IDs** (the API
   listed Naracoorte twice; a 404 on a 03-04 meet). Folded into the fix
   as observe-and-flag (not a sync rewrite).

5. **The trickle-fix brief DRAFTED + LOCKED + RELEASED.**
   `placings_trickle_fix_brief.md` (rebuild root, 152 lines, sha
   `63db7afd03f46117`, 11 sections + §0 baseline gate). A surgical
   read-write fix to ONE file (`scripts/backfill_race_metadata.py`, the
   already-dirty `M` anchor): measure progress by **placings actually
   filled** (a before/after capture.db count) not the unreliable
   `runners_synced`; **strike a resultless date on its own merit**
   (drop the `idx < last_fill_idx` gate) and **don't break the walk** on
   it; reserve "stop for tonight" for a genuine feed error/empty/rate-
   limit; add a per-night attempt cap (`BACKLOG_MAX_ATTEMPTS`, default
   20). Robust to the meet-ID wrinkle by construction (retire needs N
   *clean-but-no-new-fill* attempts; an error/empty is wall-not-strike).
   `sync_day()` / recent pass / schema named-excluded; bet-safety clean
   by construction (DR-033). **The fill-rate readout (§8) is a
   load-bearing report deliverable** per the operator's requirement:
   overall % filled by month + the unfilled remainder classified
   (abandoned/small vs recoverable) + a by-code note on what the
   thoroughbred figure excludes.

6. **Code's read-and-confirm gate — FAITHFUL → RELEASED.** Code restated
   the §0 baseline gate (PASS — HEAD `5f71488`, anchor `M`), the named
   edit anchors and the full no-touch list (`sync_day`, recent pass,
   `get_unsynced_dates`, schema), the read-write/read-only boundary, and
   the dirty-tree + bet-safety rules — all accurate. Its one addition (a
   small read helper for the fills COUNT) is in-anchor and exactly what
   §5.1 needs. Released; Code executes out-of-session.

## Standing-instruction adherence check

- **Cat 1 same-workday calibration** — held at open (tight recap; build
  table correctly not dumped on a same-workday gap).
- **Cat 1 silent open ritual** — **PARTIAL MISS again.** Step headers
  ("Step 1 — Timestamp anchor", "Step 2 — Required reads", "Anchor: …",
  "Pre-flight directory listing") leaked into operator-facing text during
  the open ritual — the same drift the S114 tightening targets and
  S193/S195 last tripped. The close ran without step-header narration.
  Flag carried so the next open watches for it. (Recorded here, not a new
  instruction.)
- **Cat 1 brevity / decision-maker framing** — held; the longer
  diagnosis/answer turns were justified-detail (operator asked "why" +
  "can we get all placings"), flagged-as-detail in register.
- **Cat 5 make-the-call** — held. Made the fix-design software calls and
  surfaced them as a tight redirectable list, not punted.
- **Cat 2 always provide the Code prompt at hand-off** — held (ready-to-
  paste prompt given with the brief).
- **Cat 3 create_file banned / verify writes** — held. Brief written via
  Desktop Commander; verified (`wc`/`shasum`/`grep`, 152 lines, sha
  `63db7afd`).
- **Cat 3 live DB reads mode=ro, never copy** — held (`sqlite3
  -readonly`; capture.db never copied; the API probe is read-only GETs).
- **Brief-drafting skill** — followed: pre-flight grounding against live
  code/API/DB, surgical-fix shape, surfaced calls, provided the prompt.
- **Bet-safety hard rule — CLEAN.** Analytical/capture-side only; no v3 /
  settlement / money-path; no code touched in Chat (the brief commissions
  Code).

## Open items

Pointer-only — full detail in `current_state.md`.

**New / changed this session:**
- **Trickle WEDGED → fix commissioned.** `placings_trickle_fix_brief.md`
  drafted + locked + Code-confirmed + released; Code executing
  out-of-session, producing `placings_trickle_fix_report.md`.
- **Trickle check-up cadence → DAILY** (operator instruction this
  session) until the fill-rate is confirmed climbing/plateauing — not the
  prior ~2-day cadence.

**Carried to S197:**
- Launcher capture-data provisioning brief (still next after the
  trickle-fix triage — bumped one slot, not dropped).
- Cash-modal back-stake blank — pre-cutover must-fix (small frontend).
- Settlement-worker brief (IOU design + manual-match-to-lay).
- Promo-seed item (also unblocks the race-page promo buttons).
- W16 cutover scoping.
- Parking-lot items (unchanged) + the duplicate/unstable meet-ID question
  (flagged in the fix brief as observe-only; a follow-up only if it's
  hiding *recoverable* results).

## Open items out (closed this session)

- **The 2026-06-28 trickle check-up — DONE.** Ran it; result: wedged →
  diagnosed → fix commissioned. The check-up itself is closed; it
  continues as the new daily cadence on the fix.

## Session close state

- `sessions/SESSION_196.md` — this record.
- `current_state.md` — rotated to S196 outcomes; stamp 2026-06-28 21:09.
- `v3_build_picture.md` — **untouched** (no v3 build stream moved this
  session; the trickle is capture-side analytical, not a tracked build
  stream; the frontend-live change was already captured at S195 close).
- `standing_instructions.md` — untouched (no new/edited standing
  instruction; the daily-check cadence is session-state, not a standing
  rule). KB re-upload still pending (carryover).
- `decisions.md` — untouched. KB re-upload still pending (carryover).
- `placings_trickle_fix_brief.md` — NEW, locked, released to Code.
- `.close_out_backups/` — stale `SESSION_195` prompt + consumed
  `SESSION_196` prompt swept; `SESSION_197_opening_prompt.md` written.

## Pending operator-side actions

- **Run the Code session** against `placings_trickle_fix_brief.md` (the
  prompt was provided this session).
- **Re-upload `decisions.md`** to the bethub-rebuild Project KB (S191/S180
  amendments; carryover).
- **Re-upload `standing_instructions.md`** to the Project KB (S189 §4;
  carryover).
- **Manage any live unmatched lays (S164)** — real exposure.
- **v2:** running (jump-started S195); jump-start-only to retirement.

## Forward routing (CONFIRMED with operator)

**S197 AUTO-TRIAGES `placings_trickle_fix_report.md` straight off the
open ritual — NO confirmation gate** (operator directive this session:
"prompt next session to do auto triage on the opening process"). Triage
shape: confirm the mechanism unjammed (resultless front date strikes
without breaking the walk; the walk reaches a date behind it); **read the
fill-rate readout first** (overall % filled + remainder classified —
confirm the gap is just the acceptable abandoned/small-race residue);
confirm bet-safety/dirty-tree clean. Then kick off the **daily**
fill-rate + backlog check (read `metadata_backfill.log` + the fill-rate
query) until the rate plateaus — the real "it's working" signal. Launcher
capture-data provisioning brief is next after.
