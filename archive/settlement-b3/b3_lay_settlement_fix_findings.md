# B3 — LAY Money-Path Fix: Phase-0 STOP (findings)

**Target:** bethub-v3 @ HEAD `e2638fa`
**Task:** CAUTIOUS BUILD of the coupled P1–P4 LAY money-path fix per `b3_lay_settlement_fix_design.md`.
**Outcome:** **STOPPED at Phase 0 — hard gate could not be executed.** No premise validated, no premise refuted, **no code written**, dirty tree **not inspected and not touched**.
**Date:** 2026-07-05 (Adelaide, DR-021).

---

## Phase-0 validation result (lead): HALTED — environment blocker, not a design defect

Phase 0 is an explicit *hard gate, no code* requiring **first-hand** re-grounding of the five premises (A), first-hand grep of the risk points (B), and a first-hand `git status`/`diff --stat` of the dirty tree (C). **None of A/B/C could be performed**, because this session has **no content access to `~/Desktop/**`** (read *or* write). I did not clear the gate on memory/prior-session recall — the commission demands first-hand verification and treats the design as a *hypothesis, not a spec*. So this is a **STOP**, not a proceed. It is **not** a finding that any design premise is wrong; the premises simply **cannot be checked** here.

---

## The blocker, precisely (two attempts)

macOS **TCC / Full Disk Access** for this Claude Code host process denies file-content `open()` across the entire `~/Desktop` subtree. `stat`/`ls` traversal is allowed; content read/write is not.

**Attempt 1 (start of session):**

| Probe | Result |
|---|---|
| `ls -d …/racing.py` | OK (stat allowed) |
| `head -1 …/racing.py` | `Operation not permitted` |
| Read tool on `b3_lay_settlement_fix_design.md` | `EPERM … open` |
| `git -C …/bethub-v3 rev-parse HEAD` | `Unable to read current working directory` (`.git` under blocked tree) |
| `touch /Users/tim/_wt` (home) / job tmp | OK (writable) |

**Attempt 2 (after operator re-granted Full Disk Access + relaunched the app):** **still blocked**, confirmed four ways —
- Bash `head -1 racing.py` → `Operation not permitted`.
- Read tool on `racing.py` and on the design doc → `EPERM … open`.
- `git … rev-parse HEAD` → `Unable to read current working directory`.
- A **freshly-spawned subagent** (child process) tried Read *and* `head` → **both BLOCKED**, same EPERM.
- `stat` shows the file is `-rw-r--r--` owner `tim` → confirms a **TCC content-denial**, not a filesystem-permission issue.

**Why the re-grant did not take:** macOS evaluates TCC / Full Disk Access against the **running process**; a process already alive when access is granted does **not** acquire it until it restarts. This is a **background job** — relaunching the *foreground* app did not restart this detached background process, and its child subagents inherit the same denied context. The grant is real, but this process cannot see it. (Consistent with the investigation session's note that a *separate* governance CC session — its own process, started with access — was unaffected.)

**Consequence — every Phase-0 input is unreadable, and no build output can be written:**
- Cannot read `b3_lay_settlement_fix_design.md` / `b3_lay_settlement_investigation_report.md` (the two documents to read first).
- Cannot read `racing.py`, `reconciliation.py`, `bets.py`, `settlement.py`, `betfair_adapter.py`, `record_builder.py`, `settlement_worker.py`, config — premises A1–A5 cannot be re-grounded.
- Cannot `grep` FINAL_PARTIAL/FINAL_FULL consumers (B) or run `git status`/`diff --stat` (C).
- Cannot **write** the P1–P4 edits back into `~/Desktop` (write `open()` denied by the same TCC scope).

---

## What was NOT done (boundaries honored)

- **No code written.** P1–P4 untouched (and unwritable here regardless).
- **Dirty tree not inspected and not touched** — no `git status`, no `diff`, no commit/stash/discard/checkout; git is non-functional in this process.
- **`BETHUB_SETTLEMENT_WORKER` left OFF** — not read, not changed. No worker started, no place/settle/reconcile/money-move, no DB write.
- **No workaround via subagents** — probed once (to diagnose), confirmed they inherit the same block; not used to bypass.

---

## Remediation — the build must run from a process started AFTER the grant

1. **Best — fresh session with access:** start a **new foreground Claude Code session** (or use the **governance CC session** that already has `~/Desktop` access) and send it the build prompt. A newly-started process will pick up the Full Disk Access grant. **This background job cannot inherit it without being restarted.**
2. **Restart this background job** if the harness supports relaunching it as a new process post-grant, then re-send.
3. **Paste (advisory only):** pasting the design doc + investigation report + current `racing.py`/`reconciliation.py`/`bets.py` + `git status --porcelain` + `git diff --stat` lets me run Phase 0 *analytically* against the paste — but it does **not** enable the build, since writing the edits into `~/Desktop` is blocked. Use this only if you want the Phase-0 verdict here before building elsewhere.

## Where this report lives
Written to `/Users/tim/.claude/jobs/0dd06eaf/tmp/` and mirrored to `/Users/tim/` (home). The intended `bethub-rebuild/` path is under the write-blocked `~/Desktop`. **Relocate to `bethub-rebuild/b3_lay_settlement_fix_findings.md` from an access-having session.**

<!-- B3 STOPPED PHASE0 -->
