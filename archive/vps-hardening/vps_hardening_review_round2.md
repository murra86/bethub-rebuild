# VPS Hardening Brief — Round-2 review record (S238, 13 Jul 2026)

Three fresh reviewers on brief v2: closure audit (all 30 round-1 findings), adversarial attack on the NEW content (W8/W9/dead-man/W7b constraints), operational buildability. All findings folded into brief v3.

## Closure audit: 22 CLOSED / 8 PARTIAL / 0 MISSED
Partials (all now fixed in v3): A1 first-sighting fallback unspecified; A3 "local racing day" undefined + collector's own UTC stamp not in scope; A6 state=NULL rows (51,568 already in db); A9 acceptance 3 contradicted W7b.7's honest limit + no independent calendar diff; A10 sweep-login vs collector-session unverified; B3 resolve_race cross-sibling union (DR-034 §4) unnamed; B8 health_check.py also embeds `ssh root@...` (incl. "DIAGNOSTIC CONTEXT" block) — "alert emails" wording wouldn't force the strip; B9 scripted-logging supersession line missing.
Key positive verification: the daily 6am heartbeat email EXISTS (racing-health-check.timer → health_check.py sends unconditionally, lands in gmail Sent) — the dead-man's switch is buildable as designed.

## Fresh attack on v2 additions (R2-1..R2-12)
- **R2-1 CRITICAL:** `PasswordAuthentication no` as written silently fails — sshd first-match: `sshd_config.d/50-cloud-init.conf` (yes) beats the main file and any 99-* drop-in. LIVE: password auth is on today DESPITE 60-cloudimg-settings.conf saying no. Fix: edit 50-cloud-init.conf itself + cloud-init `ssh_pwauth: false`; acceptance = `sshd -T` + a REAL failed password attempt, never a config grep.
- **R2-2 CRITICAL:** exactly ONE authorized key exists; no recovery path named. Mac lost on a trip = welded out. Fix: verify Hostinger console + deposit second (offline/phone) key BEFORE the flip.
- **R2-3 HIGH:** market id does NOT uniquely identify a row — 8,710 market ids on >1 row (UTC-boundary twins, e.g. Bairnsdale 1.259928926 on both 12 and 13 Jul rows); no index on betfair_win_market_id; upsert_race's COALESCE overwrites by default. Deterministic first-sighting + multi-row rules required; sweep needs its own write path; index now, UNIQUE at reset.
- **R2-4 HIGH:** the 9 PM sync_day cron has NEVER run (unescaped `%` truncates the command — syslog-verified, failing nightly since 2 Mar). Results/PLACED land ONLY via the 05:30 backfill already; v3 has no same-evening results consumer. W4 = deletion + assertion, NOT a fold. The sister cp line is dead-but-armed (recreating /home/racing/backups/ resumes 4.4GB/day raw-cp hoarding — the 8-Jul recipe); the 23:30 cron start is redundant AND broken (racing calling systemctl with no sudo).
- **R2-5 HIGH:** dead-man is real but its honest blind window = time-to-next-session (travel = days — the motivating outage shape); 6am is seasonal (ACDT→7am) — window ≥25h. State it; follow-up: external ping.
- **R2-6/R2-7 MED:** keep-1 demotion gated on "proven once" is worse than keep-2 if the Mac pull silently dies → gate on CONTINUOUS freshness (W5 asserts off-box <48h); pin source glob `data/backups/capture_*.db` (three backup dirs exist to get wrong); never touch live `capture.db*`; backup_db.sh verified SAFE (sqlite3 .backup, atomic, prune-first).
- **R2-8 MED:** stamped-coverage naive predicate cries wolf day one (live: 8 legitimately-missing of 133 next-24h; overseas venues; 180 trials; fragment twins double-count). Candidate set pinned: ≥1 bookmaker race id AND AU state; dedupe on (venue, number, local day); market id satisfied by any twin; trials by venue list.
- **R2-9 MED:** daily filename rotation defeats rsync delta (nightly full 4.4→6-8GB); pull architecture correctly ransomware-safe UNLESS --delete mirroring. Restic or --link-dest; N generations; never mirror-delete.
- **R2-10 MED:** fail2ban + roaming operator (two source IPs in 3 days) = self-lockout risk; finite bantime + console escape hatch.
- **R2-11 LOW (safe-verified):** chmod 600 .env breaks nothing (all services/cron run as racing; chmod only, never chown); .gitignore already covers secrets, never committed — push safe; exclude debris (`['DB_PATH`, .bak).
- **R2-12:** batch liveness_check.py edits (W1+W2+W3+W9-strip = ONE pass); reconcile interim in-session mailbox authority vs approval-gated W5; estimate 2-3× light; name the cut order.

## Operational review
- Drill safety: kill/identity/reboot drills destroy real races unless run AFTER W7b live + day stamped; verified dead window 02:30–06:30 ACST; identity drill 06:00–06:30 with hard abort before earliest jump; drills then cost price snapshots only.
- W9-first VERIFIED SAFE (all automation on the single proven key) — but with the R2-1/R2-2 protocol; keep root-by-key this pass (user+sudo mid-build multiplies lockout modes).
- W8a (git commit+push) moves to Day 0 BEFORE any edits.
- Dogs-live held behind W7c or mislabelled dog races surface in the live tool mid-proving-window.
- Honest estimate: 3.5–4.5 build days, 5–7 calendar days (soak nights, 6am cycles, first dog day). Day 0–5 schedule adopted into v3 §4. Fastest-value cut: Day 0 + W7b + W1 ≈ 2 days.
- Operator moments: approval + reset decision line; Hostinger console verify; KB re-uploads; W7c app-down dist swap window; supervised drills.
