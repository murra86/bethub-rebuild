# TAB transport hardening (brief, S247 — build Wed 22 Jul)

**Status: COMMISSIONED S247 (Tue, during the live-proof day). Build
tomorrow in the quiet, tested, BEFORE Saturday (bet day). Capture repo
(`racing-data-capture`); v3 untouched except where noted.**

**S248 triage: review findings T1–T7 from `s248_build_plan_review.md`
folded inline below (marked [Tn]); brief is build-ready.**

**S248 BUILD + DEPLOY (Tue 21 Jul eve, a day early — operator call,
no more racing): items 1/2/3 BUILT, box suite 125 green (16 new,
red-before proven), deployed `625c650` (Mac→VPS push deploy,
`receive.denyCurrentBranch=updateInstead` now set on the box repo),
collector + racing-api restarted in the no-race window, per-book
check live-proven clean on the evening card ("All 2 candidate books
fresh"). Telemetry surfaced at GET /health/tab-transport + live-poll
changed=Y/N journal lines — evidence starts accruing with tomorrow's
cards. Item 4 (cadence config) DEFERRED behind the T1 IP-axis gate
(no behaviour change until it opens). Item 5 (source-freshness
probe): NOT yet built — site-XHR endpoint discovery + probe script
next (tomorrow quiet is fine; near-jump head-to-head needs live
races regardless). Local Mac dev note: curl_cffi 0.14.0 now
installed locally, full suite runs on the Mac too.**

## Why (Tue 21 Jul incident)

TAB flipped bot protection ~11:55 ACST: 403 on the transport's
"safari" alias TLS fingerprint (chrome/firefox also blocked;
safari17_0 passes). Feed dead 90 min mid-card; caught by the OPERATOR
noticing a frozen column (Warren R2 4.6 vs site 3.6), not by any
alarm. Hotfix live 12:52: `_IMPERSONATE = "safari17_0"` + collector
and racing-api restarts (commit tonight, backup at
/root/tab.py.pre-s247-fingerprint-bak).

## Build items

1. **Self-healing fingerprint rotation.** Ranked candidate list —
   built from the DEPLOYED fingerprint order (probed-200 candidates
   first, burned ones last; the draft list above was stale/inverted —
   do not follow it literally) [T2]. When the pinned fingerprint
   starts 403ing, hunt across fingerprint × IP, pin what passes, log
   the rotation at INFO (`TAB fingerprint rotated: X → Y`). Breaker
   only opens when ALL candidates fail — which requires the hunt
   budget to actually COVER the list: 8 tries < 6 fps × 2 sessions
   leaves tail candidates unreachable; size the budget to the list
   [T3]. Add a shared cooldown/breaker in tab.py covering BOTH pools —
   under total burn the live route must not run a full hunt (~8×20s
   timeouts) on the API threadpool every 8s poll [T3]. Validate
   impersonate names against the pinned curl_cffi at startup — unknown
   names currently burn hunt budget silently [T7]. Today's outage
   shape must self-heal in ≤1 cycle (red-before test: mock 403 on
   current fp, next candidate 200).
2. **Per-book staleness tripwire (liveness).** Today's outage fired
   NO alert: the bookmaker-staleness gate treats books as one pool and
   the other 7 books masked TAB. New W2-family check: for each book,
   if ≥1 NEAR-window race carries THAT book's race id and that book
   has zero snapshots in 20 min → RACING ALERT naming the book.
   (Cry-wolf guards: per-book, NEAR-window-gated, same cooldown
   machinery.) Three gates on the alarm [T4]: (a) inside the
   racing+expected_up block — else nightly false alarms after the
   post-19:00 clean exit; (b) post-lull arming — capture starts
   exactly T-60 = NEAR's forward edge, so require in-window time ≥
   threshold or first-snapshot-seen before arming; (c) abandoned
   meetings = accepted false-alert limit, or gate on non-abandoned.
   Detection latency as specced is 20–35 min — acceptable vs the
   90-min blind spot it closes; state so in the check's doc. Query
   cost [T5]: per-book MAX(snapshot_time) has no supporting index —
   scope to NEAR-window race ids or add (bookmaker, snapshot_time).
3. **Transport telemetry.** Per hunt: tries-to-pin, failure axis
   (fingerprint vs IP — same fp differing by IP ⇒ IP reputation),
   rotations/day, request volume/day. Per live-poll near jump
   (T-5→jump): did the price CHANGE since last poll (capture-side
   log or small table) → answers "what would faster cadence buy" with
   real numbers after Saturday.
4. **Cadence as config + rotation-ready architecture.** Live-pool
   polling cadence becomes a setting (default 8s, floor 3s). Support
   N pre-warmed pinned sessions round-robined so per-identity rate
   stays constant when cadence rises. DEFAULT STAYS 8s — flip only
   after item-3 telemetry shows the blocks are IP-side specifically
   [T1] AND the EV case holds AND operator buys the Decodo tier
   (spend pre-approved in principle if EV case shows). The observed
   burns were FINGERPRINT-wide, not per-IP — round-robin pools do NOT
   make faster polling safe against that axis; 3s cadence would burn
   the whole candidate list faster [T1].

5. **Source-freshness scoping (added after Warren R3, Tue ~13:25).**
   **S249 (Tue eve): DISCOVERY DONE + head-to-head #1 RUN.** Via the
   operator's real Chrome: the site's race page polls the SAME
   api.beta tab-info-service race endpoint the collector uses, ~7s
   cadence, differing only in params (jurisdiction=SA — the browser's
   geo — plus returnPromo/returnOffers). No hidden fresher host, no
   push channel for odds; "shards.beta" is JS bundles only. Probe
   built (`scripts/source_freshness_probe.py`, deployed VPS+GitHub
   `a2f4e50`) and run live on VCY R2 from the Mac: feed-params vs
   site-params tick TOGETHER (leads both ways within 1-2 six-second
   ticks) → params/jurisdiction are NOT the freshness axis from a
   residential vantage. Remaining suspect for the Warren lag: the
   VPS'S OWN VANTAGE (Akamai serving the datacenter IP a staler edge
   object). **Next: same probe run simultaneously Mac + VPS on one
   near-jump race (tomorrow's cards) — jsonl timestamps merge
   directly. If VPS lags Mac, the fix is transport/vantage (e.g.
   residential egress for the live pool), not URL or cadence.**
   Operator watched Azucar $15→$14 on the TAB WEBSITE while both the
   8-10s live feed AND the collector's direct API pulls served $13
   (capture rows 03:49/03:52 UTC = 13.0; live endpoint 200s every
   ~10s throughout) — the beta API host itself lags the site by
   minutes near jump. Faster polling of the same host cannot fix
   this. Build step: capture the tab.com.au site's own XHR/data
   endpoint, head-to-head freshness vs api.beta near several jumps;
   if the site's source is fresher, switch the live pool (and
   possibly collector) to it. Cadence/IP work is subordinate to
   this — source first, speed second. Scoping caveats [T6]: control
   JURISDICTION (the feed pulls NSW; the operator's browser may sit
   in an SA pool) and CDN edge variance before concluding host-level
   lag; and the tab.com.au site XHR is Akamai bot-manager territory —
   a host switch needs its own transport spike gate before adoption.

## Sequencing / fences

- Deploy Wed after testing on the box suites; restart collector +
  racing-api in a no-races window; verify next card start.
- Never raise cadence and rotate fingerprints in the same change.
- Decodo subscription: NO purchase now (today's failure was
  fingerprint, pool was healthy — pinned in 1 try). Upgrade triggers:
  hunts creeping >2-3 tries, per-IP 403 pattern, quota pressure, or
  item-3 EV case for faster cadence.
