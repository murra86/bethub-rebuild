# TAB API Scoping Brief (S241, 16 Jul 2026) — for operator reading pre-Saturday

Operator flag: TAB is the main promo driver; embed the TAB API, HIGH priority, build from
Mon 20 Jul. Two investigation agents ran 16 Jul evening: (1) web research on the 2026 TAB
API landscape (live-probed), (2) full code map across racing-data-capture + bethub-v3.

## 1. Bottom line

- **The integration is smaller than expected.** TAB is ALREADY fully wired through the
  capture system end-to-end (adapter, race-id stamping, snapshot storage, dispatch) — it
  was disabled solely because TAB started rejecting our requests. Re-enabling is a
  one-line flag once the transport works.
- **Root cause of the 403s CONFIRMED (live probe):** TAB put its API host behind edge
  bot-protection (Akamai-style) that blocks **datacenter IPs and non-browser TLS
  fingerprints**. Our capture VPS is a datacenter IP calling with python-requests —
  exactly the blocked profile. TLS completes, the request is silently dropped. The
  website itself still answers 200. No auth was ever required and none is now — the
  block is about *where from* and *what client*, not credentials.
- **No promo/bonus data exists in any TAB API tier** — the `returnPromo` flag is generic
  market branding, not your generosities. Promo intel stays manual (diary/screenshots).
  What we get is: fixed win/place odds per runner, tote, scratchings/deductions, race
  status, results/dividends — near-real-time, all jurisdictions (pick the one matching
  the betting account; prices differ by state).
- **Value into the tool:** auto-filled SOFT ODDS for TAB races (still operator-editable),
  which lights up Raw/Promo EV without typing and feeds the future race watcher. TAB
  odds also land in the capture store for the analytics line.

## 2. Access options

**Option A — the semi-public info-service endpoints (RECOMMENDED).** What every active
hobby client uses (reference: `JaseZiv/bettRtab`, last commit Jan 2026). No signup, no
keys. "Activation" = look like a browser from a residential IP:
- Real Chrome User-Agent + Referer/Origin tab.com.au (our adapter already does this),
- **browser TLS fingerprint** (curl-impersonate / `curl_cffi` — our python-requests JA3
  is part of what's being blocked),
- **residential egress** (the decisive factor), retry-with-backoff, ~1s pacing.
Personal, low-rate use (~dozen races/day) is the tolerated norm; undocumented, so it's
tolerance not licence — volume stays polite, cache aggressively.

**Option B — official TAB Studio API (parallel hedge, operator action).** OAuth,
sanctioned, but approval is discretionary ("TAB Account Tier and historical account
records"), personal non-commercial only, unpublished turnaround, and skewed toward
wagering apps rather than odds trackers. **Suggested: operator lodges the free individual
registration at studio.tab.com.au/register/individual this week as a hedge** — if ever
granted, we swap transports and stop caring about bot filters. Do not plan around it.

## 3. Egress design (the one real decision)

The capture VPS cannot call TAB directly (datacenter IP). Two candidates:

- **A1 — VPS keeps the fetcher, upgraded transport:** swap the TAB adapter's HTTP client
  to `curl_cffi` (Chrome impersonation) and route TAB through the Decodo **residential**
  pool (the capture box already uses Decodo for other books). Cheapest; zero new moving
  parts. Might still fail if Decodo pool IPs are flagged. **First thing to test Monday —
  a 1–2h spike.**
- **A2 — home-side fetch relay (fallback, robust):** the Pi gateway sits on our
  residential Superloop IP 24/7. A small fetcher on the Pi polls TAB (browser-fingerprint
  client, home IP — indistinguishable from browsing tab.com.au from home) and the VPS
  pulls snapshots from it over Tailscale. ~half-day build. Hygiene note: use the HOME IP,
  never the betting SIM lanes — no linkage between scraping and the AdsPower identities.

## 4. Integration path through the stack (from the code map)

1. **Capture side:** fix transport per §3 → remove `"tab"` from `DISABLED_BOOKMAKERS`
   (one line — everything else is already wired: `tab_race_id` stamping, snapshots,
   circuit breaker). Extend the snapshots route to key bookmaker odds by
   **betfair_selection_id** (the runners table already holds the join — capture matched
   TAB↔Betfair identities at ingest; the route just doesn't expose the column yet).
2. **Tool side:** new **operational** route `GET /markets/{market_id}/soft-odds` proxying
   capture's TAB block. NOT a vps_client surface — the contract explicitly defers
   soft-book reads (§11.3), so this rides the operational line by design, no contract
   bend.
3. **Frontend:** seed `manualOdds` (the Soft Odds column) from the TAB feed keyed by
   selection id — the input component already supports external pre-fill and stays fully
   operator-editable; typing over a pre-fill behaves exactly like today.

## 5. Plan + effort

- **Mon am:** A1 spike (curl_cffi + Decodo residential from the VPS). Works → adapter
  swap + flag flip + selection-id column on the route (rest of Monday).
- **A1 fails → Mon pm–Tue:** A2 Pi relay + same downstream steps.
- **Tue/Wed:** v3 route + Soft Odds auto-fill + tests (fenced, display/data only —
  no money paths anywhere in this build).
- Operator actions: (optional, recommended) Studio registration this week; confirm which
  TAB jurisdiction your account bets in (prices differ per state — we poll that one).

## 6. Risks, honestly

- Bot-filter arms race: TAB can tighten again; the circuit breaker + fault-banner
  visibility means a block degrades loudly, never silently. Odds column falls back to
  manual typing — today's behaviour — on any failure.
- ToS: personal-use polling at our volumes is the tolerated community norm, but it is
  tolerance, not permission. Studio approval (Option B) is the clean fix if granted.
- Scope discipline: nothing in this build touches money paths; it is a data feed into a
  display column and the capture store.
