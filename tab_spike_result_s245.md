# TAB API — A1 spike result (S245, 20 Jul 2026)

**Verdict: A1 revived and PROVEN.** The capture VPS + Decodo residential
(Australia-targeted) + `curl_cffi` **Safari** impersonation pulls live
TAB odds end-to-end. No Pi relay needed; no new spend; zero linkage to
the operator's own TAB account (runs off the VPS, not the home line).

## Root-cause correction to the S241 scoping brief

The scoping brief assumed the 403s were **datacenter-IP + non-browser
TLS fingerprint**. The spike showed the real block is **geographic**:

- TAB's info-service serves **Australia only**. The capture VPS is a
  **UK** IP (Hostinger/London) → "unavailable from your location".
- On top of geo, TAB's Akamai front door rejects most proxy IPs and
  non-browser TLS. **Safari** impersonation passes; **Chrome** does not
  (Chrome fingerprint → 403 even from a good AU IP; confirmed on both
  the Pi and Decodo).

## The working transport (proven)

- **Proxy:** Decodo residential, **country-targeted AU**. Correct
  username format is `user-<DECODO_USERNAME>-country-au-session-<sid>-sessionduration-<mins>`
  on **`gate.decodo.com:7000`**. (The bare-username / `au.decodo.com`
  endpoint returns Netherlands IPs — NOT Australia. The `-country-au`
  modifier without the `user-` prefix returns 407. Both were dead ends;
  the `user-` prefix on gate:7000 is the fix.)
- **TLS:** `curl_cffi` `impersonate="safari"` (installed on the VPS,
  0.14.0).
- **Reliability model — hunt-and-pin:** a *fresh random* AU IP passes
  TAB only ~1-in-several tries (most → 403 "Access Denied"). But once a
  **working** IP is found and **pinned** via a sticky session, it holds
  (proven 8/8 consecutive calls on a pinned Telstra QLD IP). So the
  fetcher must: cycle sessions until a 200/JSON, then pin that session
  (sessionduration) for subsequent polls; re-hunt on a 403. Hunt was
  fast in testing (found on try 1 twice; expect a few tries worst case).
- **Endpoints confirmed working through this transport:**
  - `GET .../racing/dates/{date}/meetings` → 56 meetings (R/G/H).
  - `GET .../racing/dates/{date}/meetings/R/{venue}/races/{n}` →
    racecard with fixedOdds returnWin/returnPlace per runner (live
    Wagga R1 pulled: 8 runners, win/place present).

## Decodo plan facts (operator-confirmed)

Residential, ACTIVE, 3 GB plan ($3.75/GB, $11.25/mo), 1.06/3 GB used.
Country targeting (incl. AU) is included free on residential — **no
upgrade required.** Data cost for TAB polling is a few MB/day —
negligible against the 3 GB.

## Two-build split (operator-designed, S245)

- **Build 1 — background feed + watcher + soft-odds column.** TAB back
  on in the capture system (its existing pre-jump cadence:
  60-min window, snapshot every 5 min, ~2 min in the last 5, forced
  final T-10..T-30s). Soft Odds column auto-fills from the capture
  store. Feeds the future race watcher.
- **Build 2 — dedicated live-refresh IP for the active race page.** A
  SECOND pinned Decodo AU session (own IP), refreshing only the race
  page the operator has open, ~every 15-30s while open and within
  ~30 min of jump, stopping on navigate-away. Near-live odds for the
  one race that matters. Scoped after Build 1.

## Freshness decision (locked)

Background feed (from store) serves the watcher; dedicated live IP
serves the active race page. Global **TAB-odds on/off toggle** (on by
default; off when betting a non-TAB book). No money paths in either
build — display/data only.
