# B5 — VPS tunnel auto-start + health-gated watchdog — build report (S229)

**Run:** 2026-07-06 (S229), Adelaide-anchored per DR-021.
**Outcome:** BUILT + LIVE-TESTED same session (4-case matrix below, all in mock mode — no Betfair contact). Suite **1358 green** (shell-only change). Committed `eef2fc2`, pushed to `murra86/bethub-v3`. **Classification: live-proven for the tunnel mechanics** (real SSH, real VPS, real drops); the in-app ride-along (race lookups succeeding through a launcher-owned tunnel during a live day) confirms opportunistically at the next launch.
**Anchor:** built on `2e22c5f`; new HEAD `eef2fc2`. One file: `BetHub.command`. No Python/app-code change.

---

## 1. The gap (B5, `cutover_readiness_map.md`)

The Log-Past-Bet race lookup rides an SSH tunnel (local 8400 → VPS racing API). Before this fix, nothing in v3 started it or restored it: the operator had to remember it, and a mid-day drop silently 500'd every lookup until someone noticed. Observed live this very session: 8400 was dead at open (a half-open leftover tunnel from S228's window).

## 2. Discovery that reshaped the design

**The tunnel is a shared resource with v2 until cutover.** A standalone supervisor already exists — `bethub-v2/scripts/vps-tunnel.sh --bg` (PID-file + blind 5s respawn loop) — and had been keeping 8400 alive since 22 June. It is boot-fragile (nothing restarts it after a reboot) and v2's day depends on it. So v3's launcher cannot blindly own the port: two blind respawn loops fight over the bind on every drop.

**Design (Cat 5 call): health-gated watchdog in the v3 launcher.**
- At launch: if 8400 answers `/health`, reuse ("watching it"); else dial immediately.
- The watchdog loop only ever dials when 8400 is actually dead; while any healthy tunnel holds the port (ours, v2's, hand-started) it idles on 15s health polls. No bind fights, no spam.
- SSH hardening: `BatchMode=yes` (a passphrase prompt can never hang a Finder launch), `ServerAliveInterval=15/CountMax=2` (~30s half-open detection), `ExitOnForwardFailure=yes`, redial 10s after any exit. Log: `~/.bethub/tunnel.log`.
- Launch reports status plainly ("VPS race lookup: connected." / a WARNING naming the consequence) after the app health check; non-fatal either way.
- Shutdown kills the watchdog's process group AND reaps our ssh by its unique `BatchMode` command-line fingerprint — this covers the window-close ordering where the watchdog subshell dies before the cleanup trap runs (found live in testing: the orphaned ssh survived group-kill). A tunnel we didn't start never matches the fingerprint and is never touched.
- `BETHUB_VPS_TUNNEL=0` skips the whole block (offline use).

## 3. Live test matrix (mock app mode, real SSH/VPS)

| Case | Result |
|---|---|
| T1 cold start (no tunnel anywhere) | auto-dialled, healthy before browser-open ✅ |
| T2 hard-kill our ssh mid-run | watchdog redialled, healthy in ~15s (rode through one bind race) ✅ |
| T3 worst-case teardown (watchdog killed first, then launcher) | app stopped, our ssh reaped, both ports released, lock cleaned ✅ |
| T4 coexistence | launched over v2's tunnel ("watching it"); killed v2's ssh → converged healthy in <40s, zero spam in our log; closed v3 → our ssh reaped, v2's supervisor reclaimed 8400 within ~15s ✅ |

Machine end-state after testing: v2 supervisor running and holding the tunnel (as it was), no app, both workers off.

## 4. Residuals (named, non-blocking)

- **R-T1 (coexistence-window churn, pre-existing):** while a v3-owned tunnel holds 8400, v2's blind loop redials the VPS every ~5s, fails the local bind, and retries — pointless SSH connects + VPS auth-log noise until v3 closes. Self-heals on handback. Dissolves at cutover (v2 supervisor retired then; noted for B6's retire-list). Fixing v2's loop is out of scope per the no-v2-changes rule.
- **R-T2 (reboot gap, narrowed not closed):** nothing starts any tunnel at boot. Now covered whenever BetHub v3 is launched (the common case); a boot where the operator goes straight to v2 still needs `vps-tunnel.sh --bg` by hand. A LaunchAgent would close it fully — deliberately deferred to B7 (monitoring/observability) where always-on infrastructure belongs.
- **R-T3 (half-open detection bound):** a half-open tunnel can serve 500s for up to ~30s before ServerAlive kills and the watchdog redials. Accepted; tighter bounds cost keepalive noise.

<!-- B5 BUILT + LIVE-TESTED (S229) — health-gated launcher watchdog, coexists with v2 supervisor; commit eef2fc2; residuals R-T1 churn / R-T2 boot / R-T3 half-open window -->
