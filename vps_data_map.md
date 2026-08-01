# VPS Data Map — what the capture holds and which tool features feed off it

**Drafted:** S238, 2026-07-13 (operator-directed: "revisit the VPS structure and how data feeds work to various tool features")
**Read-only survey** of the live capture.db + code on both sides. Companion to `vps_hardening_brief.md`.

---

## 1. The one-sentence architecture

The v3 tool talks to Betfair **twice, independently**: a **live line** (v3's own `betfair_client` — race-page prices, bet placement, settlement, account funds) and a **memory line** (the VPS capture, read through `vps_client` over the 8400 tunnel — everything retrospective). The VPS is the tool's memory, not its eyes.

## 2. What the VPS captures (three sources into one db)

| Source | What it writes | Codes covered | Runs |
|---|---|---|---|
| **Betfair collector** (live, event type 7) | Market ids, selection ids, price snapshots (back/lay/depth/BSP/SP-projections), market status | Thoroughbred + harness. **NOT greyhounds** (event type 4339 not subscribed — W7 fixes) | Continuously during racing |
| **Subscription feed** (The Racing API `/australia`) | Runner metadata (jockey/trainer/weight/form/breeding), results (positions, margins, SPs, stewards), race metadata | **Thoroughbred only** — no harness/greyhound backfill exists | Nightly 05:30 + backlog sweep |
| **Bookmaker odds capture** | Fixed win/place odds snapshots per bookmaker; bookmaker race ids (TAB/Sportsbet/Ladbrokes/Neds/…) | Whatever the bookmaker pages list (incl. greyhounds — that's why dog race *rows* exist with no Betfair identity) | Continuously during racing |

**Scale today:** 97k races · 583k runners · 3.6M Betfair snapshots · 6.4M bookmaker snapshots · 164k historical Betfair rows.

**Key field groups** (races/runners tables): identity (date/venue/number + `betfair_win_market_id` + per-bookmaker ids), race metadata (distance/class/condition/prize), runner form + breeding, results (position/margin/SP/status), coverage flags (`has_betfair_capture` / `has_bookies_capture` / `has_subscription_sync`), match confidence.

## 3. Which tool features feed off what

| Tool feature | Feed | Consequence |
|---|---|---|
| Race page live prices, quick lay, burst flow | v3's own Betfair line (NOT the VPS) | Works even if the VPS is down |
| Bet placement / settlement workers / account funds | v3's own Betfair line | Same — money paths never touch the VPS |
| **Log Past Bet (manual entry)** | VPS via `vps_client` (day catalogue → resolve → Betfair stamp) | **Only serves races the collector saw live pre-jump** (needs the market id). Sole v3 consumer of the VPS today (`ui/api/routers/bets.py`) |
| Manual-entry starting prices / results at settle-at-entry | VPS (`starting_price` / `results` reads) | Same dependency |
| Analytics (price-pressure research, EV validation) | capture.db directly (analytical line) | Research-only |
| Sports (future) | v3's Betfair line already has `sports_lines`; **VPS captures nothing sports-side** | Manual sports-bet entry would have no memory to run off — see §5 |

## 4. The structural rule that explains every gap

**A race is manually loggable if and only if the collector saw its Betfair market live before the jump.** The market id comes from nowhere else: the subscription feed restores thoroughbred results *after* the fact but never market ids (Betfair delists closed markets — unrecoverable, the Caulfield lesson).

Everything the operator has bumped into follows from this:
- Caulfield 11 Jul un-loggable → collector was down pre-jump.
- Greyhounds never in the picker → collector never subscribed to dogs (rows exist only via bookmaker odds, no Betfair identity).
- Harness loggable but fragile → captured live, but zero backfill safety net.
- Sports un-loggable later unless captured → same rule will apply.

## 5. Misfits vs the operator's stated direction (S238: "manual entry runs off captured Betfair data — all racing types, and sports when that time comes")

1. **Dogs missing** → W7 in the hardening brief (subscribe event type 4339). Roughly doubles daily race volume; disk at 35% has headroom; data reset starts with full coverage.
2. **Code classification is unreliable** — `track_type` only knows turf/synthetic (surface, not code); harness rows sit as 'turf'; the race-page T/H/G filters run on venue inference. With dogs arriving, stamp the code **from the Betfair event type at capture time** (the collector knows it at discovery). Folded into W7.
3. **Backfill asymmetry** — only thoroughbred has a second source. Harness/dogs loggability is 100% collector-uptime. The hardening pass (fast detect + auto-restart, W2/W3) *is* the mitigation; a paid harness/dogs results feed is the only true second source if ever wanted.
4. **Sports capture doesn't exist** — when Strategy-3 SGM goes live, manual sports entry will need either a VPS sports collector (new capture project: markets are named lines, not runner fields — schema won't stretch as-is) or a different rule for sports (e.g. stamp from v3's live line at bet time, no retrospective picker). Decision belongs with the sports build, not this pass — flagged so it's a decision, not a surprise.
5. **Single consumer, wide surface** — v3 reads the VPS only for manual entry, through 3 API routes, while the db carries 49-column races rows and 6.4M bookmaker snapshots mostly serving analytics. The planned data reset is the natural moment to decide what the *tool* contract with the VPS actually is (DR-028 single boundary already enforces the how).

## 6. Recommended sequence

1. **Hardening pass W1–W7** (brief approved → build): alerts + self-heal + dogs + code stamping.
2. **Data reset** (operator-planned): starts with all three codes captured, clean deficit, code-stamped rows.
3. **Sports capture decision**: at Strategy-3 wrapper time, pick VPS-sports-collector vs stamp-at-bet-time (§5.4).
