# VPS Hardening — Final Acceptance Report (S241, Fri 17 Jul 2026, 05:03 close-out)

Contract: `vps_hardening_brief.md` v3 (approved 13 Jul "lets go"; DR-035 harden→reset).
Build ran Days 0–3 as scheduled (14–16 Jul) + drills. This report scores the §3
acceptance list and closes the build. Repos: racing-data-capture VPS=Mac=GitHub synced
throughout (latest `751d8c0`); every change landed as commits.

## §3 acceptance scorecard (13 items)

1. **Kill drill — PASS (16 Jul, live).** Collector stopped 10:34 → alert with
   AUTO-RESTART note at 11:00 (26 min, bound ≤75) → W3 restart succeeded → RACING
   RECOVERED 11:15 → snapshots fresh, streak reset, ledger `2026-07-16 1`.
2. **Restart-cap negative — PASS (live evidence, overnight 15→16 Jul).** Cap reached
   (2 restarts burned), subsequent failures sent "NEEDS HANDS: restart cap (2/day)
   reached", no third restart attempted. State machine also unit-tested.
3. **Identity drill — PASS (16 Jul 06:05).** 73/73 market-bearing rows stamped pre-jump;
   sweep-run-twice diff over 551 identities EMPTY (idempotent, zero overwrites); zero
   duplicate fragments; swept-then-collected single-fragment proven at the 08:30
   collector start. Red-before satisfied by the 15 Jul LIVE red→green incident (sweep
   TOO_MUCH_DATA failure caught by stamped-coverage 10:30/11:15, fixed, stamped 10 min
   pre-jump) rather than a synthetic re-run.
4. **Calendar diff — PARTIAL / DEFERRED.** No formal independent-calendar diff was run.
   Partial evidence from live ops: every bookmaker-known race 15–16 Jul was stamped or
   explained (Muswellbrook sportsbet-only trials investigated empirically, 30-day
   1,051/1,104 evidence). Recommend one formal diff pass next week on a normal day.
5. **Dog day proof — PASS with one deferral (16 Jul, first natural dog day).**
   143 greyhound races stamped (2/3 of card, matching the 2× volume prediction), market
   ids + prices + snapshots flowing, code=greyhound end-to-end into the tool's picker
   (W7c). Discovery hit 208 markets — PAST the old 200-cap cliff; pagination + the
   sweep's 60/page weight fix carried it. Volume/disk delta modest (db +~30MB w/ dogs,
   disk 36%). **Deferred: picker-latency re-measure** (needs an operator session
   measurement; S237 baseline 1.4s).
6. **Truncation alarm — PASS (synthetic + real).** `tests/test_page_cap.py`: endless
   full pages trip `hit_page_cap` at exactly MAX_PAGES; draining source doesn't. The
   REAL truncation class also fired live 15 Jul (Betfair TOO_MUCH_DATA weight cap) and
   was fixed + regression-pinned (PAGE_SIZE 60).
7. **Session proof — PASS.** Multiple sweeps under a live collector across 15–16 Jul;
   zero keepAlive/session disturbance in collector logs.
8. **Restore drill — PASS (14 Jul, Day 2).** Off-box copy restored to Mac scratch per
   `RESTORE_VPS.md`; integrity ok; 97,541 races read back.
9. **Reboot drill — PASS (TODAY 05:06, dead window, after 77 days uptime).** SSH back
   in ~60s; 8/8 racing timers active; racing-api 200 on 8400; sshd posture held
   (passwordauthentication no, permitrootlogin without-password); fail2ban active; all
   timer schedules intact (sweep 05:50, heartbeat 06:00, collector 08:30).
   **Finding (benign, recorded):** racing-capture starts at BOOT even outside its
   operating day (05:08 start after this reboot; designed window 08:30–19:00+). Kept
   as-is deliberately — post-outage capture resumes ASAP; the liveness operating-window
   gate (16 Jul fix) is keyed to the collector's day, and a boot-started collector
   simply runs early and harmlessly.
10. **W9 behaviour probe — PASS.** Proven Day 0 (real failed-password attempt refused;
    recovery key installed + tested; Hostinger console verified) and re-verified
    post-reboot today via `sshd -T`. fail2ban active post-reboot.
11. **Soak — PASS.** 16 Jul = one normal night + full (dog-)day with EXACTLY ONE alert:
    the kill drill's own. Zero false alarms including stamped-coverage. The three
    cry-wolf families found during the week (evening bookmaker/no-book-ids, morning
    jump-outs/no-markets, overnight collector designed-off) were each fixed same-day and
    verified silent under the exact conditions that caused them.
12. **Dead-man proof — PASS.** The 06:00 heartbeat arrived at 06:00:25 from the box
    rebooted 54 minutes earlier — and for the first time this week it reads
    "✅ All Healthy" (previous dailies carried the cry-wolf "6 Issues"; the W2 fixes
    cleaned the daily report too). The 05:50 identity sweep also ran green post-reboot
    (Persistent=true honoured; 63 updated, 0 collisions). The
    suppression variant (kill a heartbeat → detection flags VPS-DOWN) was NOT separately
    staged: detection lives in the W5 session-open assert ("daily health email ARRIVED"),
    which has run at every session open this week; staging a suppression would spend a
    real heartbeat gap for a check the standing assert already performs. Recorded as an
    accepted deviation.
13. **Unit tests + commits — PASS.** All VPS changes as commits to the GitHub remote
    (`murra86/racing-data-capture`); capture suite 86 green on Mac and box; v3 companion
    suites 1464/207 green. Notable additions this week: liveness operating-window +
    stamped-coverage + book-id-gate tests, page-cap tests, W7c code tests.

## W-item closure

W1 gmail delivery ✓ · W2 honest alerts ✓ (+4 live refinements beyond brief: bookmaker
book-id gate, stamped-coverage w/ sportsbet-only trials rule, collector operating-window
gate, twin-key fix) · W3 self-heal ✓ live-proven · W4 cron landmines deleted ✓ ·
W5 mailbox watch formalized + operated all week ✓ · W7 dogs live ✓ · W7b identity sweep
✓ (3×-daily, idempotent, weight-cap fixed) · W7c tool companion ✓ (T/H/G + confidence
through the picker) · W8a code off-box ✓ · W8b data off-box + restore ✓ · W9 door locked
✓ (reboot-proven). **W6 (v3 fault-banner tripwire incl. VPS disk) remains the named
separate build.**

## Soak-week alert history (complete)

- 14 Jul: 11× "Bookmaker data" cry-wolf (evening harness, zero book ids) → book-id gate
  built 15 Jul, silent under same conditions 15+16 Jul evenings. 1× known Betfair
  pre-refinement alert (00:53).
- 15 Jul: 2× "Stamped coverage" — REAL (sweep TOO_MUCH_DATA death); fixed + stamped
  10 min pre-jump. The tripwire's first live catch, on its first morning.
- 15→16 Jul overnight: 9× "Collector" cry-wolf vs designed daily-session shutdown; both
  W3 restarts burned fighting design (each exited cleanly again) → operating-window gate
  built 16 Jul morning; silent 16→17 overnight. Side benefit: cap/needs-hands wording
  demonstrated live (= item 2).
- 16 Jul: 1× Collector alert + 1× RECOVERED = the kill drill itself. Nothing else.
- 17 Jul (to close-out): zero.

## Named follow-ups (inherited + new)

W6 fault banner (incl. VPS disk tripwire) · formal calendar-diff pass (item 4) · picker
latency re-measure (item 5) · health_check.py exits 1 after successful send (cosmetic,
unit shows "failed") · liveness cooldown-file touch adds ≤30 min first-alert latency
(cosmetic) · RECOVERED email reuses failure template header (cosmetic) · venue-alias
fragmentation ("Albion"/"Albion Park") — pre-existing, reset-adjacent · collector
boot-start-outside-window characteristic (documented, intentionally kept).

## Verdict

**Hardening build CLOSED — 11 PASS, 2 PARTIAL (formal calendar diff deferred; picker
latency measure deferred), 0 FAIL.** The box is loud (honest alerts proven under a week of real conditions),
self-healing (live-proven), watched (W5 operating), and survivable (off-box code+data,
restore- and reboot-drilled, door locked). Cleared for today's data reset and Saturday.
