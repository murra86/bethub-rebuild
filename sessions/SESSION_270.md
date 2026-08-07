# SESSION 270 — Friday 7 August 2026 (three stuck bets, one rule changed)

Opened ~12:20 ACST, closed ~17:35. Working branch `s267-race-row`,
**pushed** (5 commits, including the two S269 owed). Backend suite
2248 → 2271, frontend 616 → 621. One commit on the capture VPS
(`b74d99f`, local repo — that box has no remote).

The session was driven by three bets the operator could not enter. It
ended up changing a money-surface rule, correcting a live credit, and
fixing a capture-read defect found at the open.

---

## 1. Standing checks

**VPS all clear** — disk 45%, collector running, capture fresh, backups
2 copies / 7h old, overnight sweep ran, tunnel up, 746 races captured.
**Betfair back** after Thursday's maintenance window.

**48 RACING ALERTs.** S269 read the same class as "all explained". They
were not — see §5. Two live classes: country stamping (the parked
Newmarket alarm, plus international artefacts) and stamped coverage.

---

## 2. Three bets that could not be entered

Moree R5 *Deebo*, Ballarat Synthetic R6 *Bliss Bomb*, Gosford R6
*Street Lyric* — $51 each, all lost, AllBets-Tim, 6 Aug.

All three jumped **inside Thursday's Betfair outage**. Betfair captured
**zero** snapshots in the 05:00 UTC hour, so those races never got a
market id, and `_lookup_api.collapse_fragments` dropped market-less rows
on purpose (DR-034 stance 3, DR-032 §6 — "a bet needs a Betfair market at
logging time"). **39 of 215 AU races that day were un-loggable; Murray
Bridge, Mt Isa and Hobart vanished from the picker entirely.** The screen
showed an empty list, which reads as "this race never happened".

### The ids are gone. Proven, not assumed.

1. Live catalogue for that window: **0 markets**, both event types.
2. Fetch by explicit id: nothing — **including a control race we know
   existed and have stamped**. That control is the decisive result:
   Betfair purged the whole day, so there is no lookup route left and
   therefore **no way to verify any candidate id**.
3. Historical feed is monthly; August lands in September.

### The arithmetic that was deliberately not used

Gosford's stamped ids step by exactly +3 (`R1 …389 … R4 …398, R8 …410`),
which predicts the three missing ones. **Not used, and must not be.** A
wrong market id does not fail loudly — it silently welds a bet, and later
its settlement, onto the wrong race. That is exactly how 582 settled BSP
rows landed on wrong races in the S267 import.

---

## 3. Shipped

### `cbf764a` — the entry screen calls a track what every other screen does

`normaliseVenue` was wired into BetLog, Results, Settle-Up and
ProvisionalBetModal — but **not `LogPastBet.tsx`**. The same meeting read
"Sportsbet-Ballarat Synthetic" when logging and "Ballarat Synthetic"
everywhere else. Label cleaned; `value` kept **raw** (it is the
`races_by_venue` key and the `resolveRace` argument). Twin venues that
clean to the same label keep the raw string in parentheses rather than
being merged — collapsing two store rows here would hide a meeting's
races, and that repair belongs store-side. Both empty states now name the
no-market drop instead of rendering nothing.

### `a76eeae` — a bet on a market-less race can be recorded

Market-less rows are carried through the collapse (grouped on natural key
so an outage day cannot double-count its own card) and given a minted
`nobf:<capture row id>` identity; runners get `nobf:r<saddlecloth>`.

Safety is **structural, not procedural**: real Betfair ids are
`1.xxxxxxxxx` and selection ids are numeric, so anything joining on
exchange identity finds **nothing** rather than the wrong thing. The
failure mode is a blank, never a silent mis-pairing.

- `place_hedge_bet` refuses a minted id **before any network call** —
  reaching a live placement path with one is a routing bug worth failing
  on, not a Betfair rejection that looks retryable.
- The create endpoint is already settle-at-entry and terminal-only, so
  these never enter the settlement worker; and a `nobf:` id fed to a
  settlement read fails **closed**.
- The re-pick cross-check works **both ways** — a minted id offered for a
  race that HAS a real market is rejected too, which would otherwise
  silently detach a good bet from the exchange.
- Full promo/free-bet machinery retained. The existing legless other-code
  path could never have carried this: it hard-codes `is_free_bet=False`
  and no promo.

**Live-proven** — the operator entered all three bets through it.

### `d6c8dd6` — `--observed-amount` on `ops.correct_credit_amount`

The 1b verb recomputes a wrong credit from the template's terms, because
the defect class it was built for was the door's own arithmetic. A second
class existed with no expression: **the book paying what the terms do not
predict**. Bounded, never trusted — positive 2dp; an insurance credit may
not exceed the qualifier's own stake; an id not also passed as
`--credit-event` is refused so a typo cannot silently fall back to
recomputing. Audit note reads "observed at book, terms would give cap=50",
so an asserted figure can never look terms-derived.

---

## 4. Money handled live

Template **"Ins $50 FB 2+3"** caps at $50, so the $51 Bliss Bomb qualifier
banked $50. AllBets actually issued **$51**.

`e7b9079d` ($50) → rejected + replaced by `90754e3e` (**$51**) → paired to
the Kiwi Harmony spend through the sanctioned `/pair-spend` door
(`41d71c2c`). AllBets now **$0 FB / $77 cash — matches the bet slip to the
cent**. Backup `~/.bethub/backups/bethub-pre-1b-correction-20260807-161203.db`.

**Template deliberately left alone.** One observation must not rewrite a
real promo's terms, nor change every other credit drawn from it. **If it
pays over $50 again, the cap is wrong** — carry this.

**FB conversion measured: $51 → +$35.77 (lay won, after 10% commission) =
70.1%.** Third ~70% reading. Reported only; the 65% assumption stands.

---

## 5. The split-meeting defect — found at open, fixed on the VPS (`b74d99f`)

Three of today's meetings existed as **two rows under two spellings**,
runner-verified identical: Canberra / "Canberra Acton", Mt Gambier /
"Mount Gambier", Haydock Park / "Haydock Pk (Gbr)" (plus a bare third
row). Data split across the pair — Ladbrokes/Neds/Sportsbet on the alias
row at Canberra, and **at Urawa R5 TAB itself**, which blanks the odds
column on a race being looked at.

`racing-twin-repair` cannot catch it: DR-036/0l repairs rows that **share**
a venue key and split on identity. These have genuinely different
`venue_normalised`. It is a **venue-alias** failure, so S263's "no new twin
since 28 Jul" is true at the same time.

**Fix (read-only, no writes, no identity rewritten):** alias rows are
fetched as a second fragment shape — matched on the tightest natural key
(same date, race number, **exact** scheduled_start) — then **gated on
runner identity before admission**, failing closed (both sides ≥ 3 named
runners, ≥ 50% overlap of the smaller side).

### The admission gate is the lesson, and live data is what forced it

Matching on the natural key alone pulled **Urawa R5 (Japan)** in as a
fragment of **Traralgon R5 (AU)** — same minute, same race number,
opposite hemispheres. The Urawa row held a TAB snapshot, so it **won the
primary pick** and would have served another race's prices. The union's
own name guard refused to bridge its runners, but **that guard runs after
the primary is chosen and cannot protect a decision made before it.**

**The unit tests passed before this was caught.** Only the run against the
live store exposed it. Verified after the fix: all 14 genuine alias twins
bridge with the primary unchanged; Traralgon/Urawa correctly stays a
single fragment. Tests 22 → 25 including the module's standing EXPLAIN
no-scan guard on the new query.

Note: Haydock and Urawa carry **no Betfair stamp at all** — the sweep is
`SWEEP_COUNTRIES = ("AU",)` — so international still does not price. Phase
1 known, untouched.

---

## 6. Race-day readiness pass (for Saturday 8 August)

**Verified, not assumed** — app booted, tunnel raised, real endpoints hit,
then torn down again so the operator's launch starts clean:

- App boots with no errors; tunnel → capture API → picker returns **all 8
  of tomorrow's meetings** (Randwick 10, Caulfield 9, Eagle Farm 9,
  Morphettville 9, Kembla Grange 8, Townsville 8, Alice Springs 7, Belmont
  6 = 66 races), matching the store exactly.
- Soft-odds through the new fix: **every runner priced** across the
  Canberra card (an alias-split meeting).
- Capture + API active, disk 45%, timers scheduled, Betfair login clean.
- Tomorrow's card discovered **clean** — all stamped, zero bare rows.
  Alias twins mint in the overnight bookmaker pass (~23:49 ACST); the fix
  now absorbs them.
- **Cleared 7 stale failed units** (s264/s265/s266 `deploy-loop3..9` —
  dead transient one-shots from 4 Aug, no timers). `--state=failed` is
  readable again; only `racing-liveness` remains, which **exits 1 by
  design when it sends an alert**. That is not a fault.
- Decodo proxy 522/502: 31 in ~1504 log lines (~2%). Transient, retried,
  costs the odd tick. Known.

### TAB fill — investigated, not a defect

Reported as "TAB odds not filling when clicked". TAB is **healthy** —
11,873 rows today, top book by volume, last snapshot 2 min before the
check. The pattern over 5 days:

| Code | Races | With a TAB id |
|---|---|---|
| Thoroughbred | 205 | **205 — 100%** |
| Greyhound | 784 | **0** |
| Harness | 204 | **0** |

Every race in the evening window was greyhound or harness, so there was no
TAB race id to fill from — and the operator confirmed AU thoroughbreds had
finished for the day. Today's thoroughbred ids landed **06:05 ACST**, ~6h
before the first jump, covering 7/7, 8/8, 7/7, 7/7, 8/8. Tomorrow's card
showing zero at 17:00 is therefore expected.

**Check tomorrow after 06:30:** open a Randwick race and click the fill.
If it works, set. If not, the overnight TAB stamping did not run.

---

## HANDOFF — S271 (next week)

1. **Alert noise is the top item.** 48 alerts in a day, dominated by
   international artefacts (country stamping + stamped coverage). A
   genuine AU failure can be buried. Scoping those two checks to AU is an
   operator call — the Newmarket alarm is parked on purpose.
2. **TAB has no greyhound/harness race ids at all** — 988 races over five
   days with no TAB odds available. Long-standing, not new; worth deciding
   whether it is a gap or intended.
3. **Deploy-scheduler fix or retirement** — still open (S269 item 2). The
   7 dead loop units are now cleared, which is half the cleanup.
4. **Saturday's four live proofs** — Take-SP first fill, SP-pool on a
   near-jump snapshot, first settle-up batch to the cent, first auto-banked
   bonus win.
5. **If "Ins $50 FB 2+3" pays over $50 again, the template cap is wrong.**
6. **582 settled BSP rows sit on the wrong race** inside the S267 import.
   Carry into any analysis of that data.
7. **Watch for more expired tests** (S269 item 6) — nothing systematically
   finds tests whose fixtures age out of a rolling window.
8. The VPS capture repo has **no git remote** — `b74d99f` exists only on
   that box. Worth a mirror.
