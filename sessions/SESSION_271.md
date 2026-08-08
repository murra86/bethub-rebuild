# SESSION 271 — Saturday 8 August 2026 (proof day; four ships, three of my own findings retracted)

Branch `bethub-v3` `s267-race-row`, four commits, **all gated** (backend
2271 → 2276, frontend 621 → 624, `npm run build` clean). Nothing pushed
until close.

The day's shape: the predicted Caulfield defect arrived, three operator
problems were fixed end-to-end, a full P&L/promo review was produced —
and then most of the review's sharper claims were dismantled by operator
challenge. **The retractions are the most useful thing in this record.**

---

## 1. Standing checks

VPS all clear (disk 45%, capture fresh, backups 7h, 577 races). Mac app
running. 86 RACING ALERTs by 02:15 UTC — dominated by international
country-stamping artefacts, but **the Caulfield defect was correctly
caught inside them** by the stamped-coverage check. The alarm earned its
keep; the noise nearly buried it. That is the concrete case for scoping
those two checks to AU (S270 handoff item 1, still an operator call).

---

## 2. The split-meeting defect recurred, exactly as predicted

S270 said "expect a recurrence on Saturday's proof day". It landed on the
biggest meeting: `Caulfield` **and** `Caulfield Heath`, nine races each,
runner-verified identical (overlap 10/10, 15/16, 8/8, 12/12, 14/15,
10/10, 15/16, 13/13, 10/12).

**Damage was low.** All 8 books and 894 live Betfair snapshots sat on the
real row; the Heath twin held 112 runners and **zero** snapshots — an
inert shadow. EV, laying and Take-SP all worked. Unlike S270's Canberra
case the books did not split. The exposure was operator misclick: the
picker offered both as nine-race meetings.

### Root cause (new)

VPS `api/market_resolution.py` ~line 110 joins alias fragments on **raw
string equality** of `scheduled_start`. The two rows store the same
instant in different formats:

    Caulfield        2026-08-08T02:20:00+00:00
    Caulfield Heath  2026-08-08T02:20:00.000Z

The join never matches, so the runner-identity admission gate — which
would have passed these — is never reached. **The S270 fix is sound; its
key is too literal.** Fix: normalise both sides to a common instant,
leave the gate untouched.

**Operator ruled: fix AFTER racing, never mid-card.** A `racing-api`
restart during a live meeting is not worth it when prices are unaffected.
Deferred to the next sitting; queued in `worklist.md`.

The admission gate keeps earning its keep: five same-time, same-number
pairs today are genuinely different tracks and must never bridge
(Cunnamulla/Sportsbet Gladstone, Sportsbet Nanango/Louth,
Cunnamulla/Muttaburra, Wexford/Taif, Thistledown/Delaware Park).

---

## 3. Zumbo — the settled-then-voided flag was right

Leigh, $50 cash TAB, Randwick R2 "4. Zumbo" @ 6.0 under *Ins $50 FB 2+3*.
Betfair read `settled_runner_now_removed`; operator confirmed at the book
and re-classed to VOID. **+$50 recovered.**

### The reusable finding: scratch data is 80% unreliable

Of 291 runners flagged scratched on 8 Aug, **232 were still being priced
by bookmakers after the flag time.** By source: pointsbet 20/20, unibet
10/10, tabtouch 8/8, neds 6/6 — all 100% suspect; ladbrokes 107/139; tab
27/43; sportsbet 5/13; **betfair 0/2, the only clean source.**

A book returning a NULL price is being read as a scratching. Live case:
**Kate's Tiara** (Casino R2) flagged scratched off a Sportsbet NULL while
Ladbrokes and TAB priced her $5.00–5.50 seven minutes out. She ran — with
a $50 free bet and a $39.47 lay riding on her.

Queued in `worklist.md`. Until settled, **nothing downstream should treat
a book-sourced scratching as authoritative.**

---

## 4. Shipped

### `aac8163` — a bet logged today sits where you logged it

`LogOtherBet.tsx` stamped every bet `T00:00:00`. The BetLog is
newest-first, so a bet logged at 14:39 sank to **position 120 of 120**.
Now stamps today's bets with the Adelaide clock; a genuine backfill onto
a closed day keeps midnight, where sort position is moot.

### `56b9f1e` — moving a bet's account no longer looks like deletion

The "Moved: Tim → Sarie ✓" confirmation was rendered **inside the bet's
own row**. Moving the bet pushed it out of the active person-filter,
which unmounted the row and destroyed the notice with it. The operator
saw the bet vanish and was told nothing.

The notice now belongs to the page, which outlives the row, and says the
bet may have moved out of the current filters. The regression test drops
the bet from the refetched feed and asserts the notice survives — it
fails against the old code.

Worth recording: **no bet has ever been deleted in this app** (zero
`bet_deleted` events, all time). The disappearance was always a display
defect.

### `4d1bb12` — the account check's rounding allowance scales with the bet

The watchdog auto-books differences small enough to be exchange rounding
and flags the rest. The ceiling was a flat 5¢ — the wrong **shape**, not
the wrong size.

Half the lines derive as a bare stake (only ever a half-cent out). The
other half derive as `stake × (price − 1)`, where both factors are stored
to 2dp and **each one's rounding is multiplied by the other**. The price
term bites, because it scales with the whole stake.

Morphettville R6 surfaced it: a lay of $36.67 @ 9.58, matched by Betfair
in fragments so the stored average price is rounded. Betfair took
$314.71, the tool derived $314.63, and the 8¢ gap sat outside a 5¢
ceiling while being comfortably inside the ±$0.23 that 2dp storage can
produce there. As stakes grow this misfires more often — and a check that
cries wolf stops being read.

Allowance now computed from the same terms the derivation uses, never
tighter than the old floor. A genuine break (wrong price, missed partial
fill, mis-applied commission) is dollars, not tens of cents, and still
lands far outside. The mismatch message names the allowance so the size
of a real break is legible.

**Applied live:** app restarted, dry run confirmed the line moved from
`line_mismatch` to bookable, then booked through the tool's own audited
path. **Account now reconciles exactly: Betfair $1,660.35 = tool
$1,660.35, zero flags.** Backup
`bethub-pre-watchdog-tolerance-20260808-1745.db`.

### `c69b0c9` — a fixed disagreement stops printing for the day

Found while verifying the above. The daily money check replays the whole
day's log, so the resolved flag kept printing a ⚑ **directly under a
summary that already read "0 flag(s) — matches the account"**. Flags are
now scoped to the pass they were logged against; only the latest pass
speaks for the account. A flag with no summary after it is always shown —
something ran and failed to summarise, which must never be swallowed.
Compared by owning pass rather than time window, so two passes in the
same second still own their flags.

---

## 5. Money handled live

**Wrong-account move on a settled bet carrying a live credit.** Caulfield
R6 "9. Custom" ($50 @ 1.8, settled lost) had earned a $50 insurance free
bet to Tim@TAB. The in-tool move button **correctly refused** — a live
promo event rode the bet. Ran the sanctioned door:

    uv run python -m ops.correct_promo_chain --yes plan --bet <qualifier> \
        --target <aab> --reason "..."
    uv run python -m ops.correct_promo_chain --yes execute --composition 4145f6c3

Bet and credit both moved to Sarie@TAB; Tim left with nothing stranded;
coherence sweep clean. The credit was **in hand and unspent** — the
simplest shape, no deploy re-funding. Backup
`bethub-pre-promochain-sarie-20260808-1530.db`.

Note: `--yes` is a **global** flag and must precede the subcommand.

---

## 6. P&L and promo review

Produced as two artifacts (analytical + plain-language explainer) and
`pl_and_promo_review_s271.md`.

**Analysis snapshot (17:00): today +$744.87** on 144 settled; all time
+$3,728.27 on 711. **Final at close: today +$746.00** on **149** settled
(10.91% on turnover); **all time +$3,729.40** on **716** (12.06%,
$30,925.61 turnover). Five bets settled after the analysis ran — four
PointsBet backs 17:20–17:53 and a TAB free bet — plus the pending AFL
bet. **Nothing pending, no open cycles.** The $1.13 movement changes no
conclusion, so the review is left on its consistent 17:00 population with
the final figures noted on it.

**The finding that holds:** cash qualifiers 467 bets / $21,156 staked =
**−$242.75**; free bets **+$6,832**; hedges **−$3,027**. Qualifiers are
the entry fee, not the business. Strip the promos out and the operation
loses $243; with them it makes $3,369. **Profit scales with promos
harvested, not turnover and not selection.**

**Promos read per CYCLE and grouped by MECHANISM** (operator: combine the
dollar amounts). Insurance-2nd-or-3rd 299 cycles **+$12.73/cycle, 95% CI
+2.75…+22.71 — the only number in the whole review proven clear of
zero.** Bonus winnings 88 cycles −$2.85 with CI −19.40…+13.69:
indistinguishable from break-even. Splitting by cap had made one variant
look like a −21.1% disaster.

**Rank on mechanics, not results.** Insurance pays on 2nd/3rd (common);
bonus winnings needs a **win** (uncommon) — 11.3% vs 6.0% edge. Ranking
on realised results would need ~2,970 cycles.

**By racing code, per cycle:** thoroughbred 414 **+$3,828.72** (+20.0%);
harness 10 +$159.86; greyhound 40 −$33.29; non-racing 7 −$74; the three
Betfair-outage bets −$153. Thoroughbreds are the operation. Today was
100% thoroughbred.

**Free-bet conversion 0.70** — fourth independent ~70% reading, on the
full 121-bet population. Money-weighted 0.6998. **Do not split by event
type** (operator: "I just take the 70% wherever I can get it, may even be
on sport").

**Hedge timing, answering the operator's question:** early hedges convert
**0.734** against **0.674** inside three minutes — 6.1¢ per free-bet
dollar, 95% CI +2.0…+10.1¢, significant. ~4¢ is filling; ~2¢ is **price**
(fully-matched-only: 0.740 vs 0.721; the lay sits 11.9% above the back
price inside three minutes against 10.2% earlier). **The market tightens
into the jump.** Worth more than the $171.60 fill-failure figure alone.

---

## 7. Three retractions — the most important section

All three were caught by operator challenge, not by me.

**One — "$523.50 of credit in hand".** Derived by subtracting free-bet
stakes from credit face. Invalid: a credit's face and the stake it funds
are different quantities, and superseded credits still read `finalised`.
Filtering on `supersedes_event_id` fails too, because a *deploy*
supersedes its credit. **Truth: zero in hand, all $6,001 spent, $10 ever
expired (0.17%).** Ask `ops.correct_promo_chain credits --pairing`, or
read the daily money check. **Never derive it.**

**Two — "the EV indicator runs a third hot".** `promo_ev_at_log` is
stamped on **free bets too**, at ~70% — that is the engine's estimate of
*that free bet's conversion*, not a whole-play edge. Summing those with
the qualifiers' stamps tripled the apparent forecast ($1,980.64 →
$5,853.05). **Truth: qualifier-only prediction $1,980.64 against
$3,438.77 realised — the estimate is slightly conservative, and the
per-cycle difference (+$3.41, 95% CI −$4.40…+$11.21) is inside the
noise.** No detectable bias in either direction.

**Three — "ignore thin days, they're noise".** Too glib. Per cycle, quiet
days (<40 bets) return **−$3.71** against **+$13.17** on busy days; the
−$16.87 gap is significant (CI −30.89…−2.85). **But the cause is promo
mix:** busy days run 90% insurance promos, quiet days only 32%, and
average edge falls 10.98% → 7.24%. A quiet day is a day the good promos
are not on offer. Actionable in a way "it's noise" is not.

### The common thread

**Three times I conflated a convenient population with the population
that actually answers the question** — credit face vs stake funded, free
bet stamps vs qualifier stamps, day-level ROI vs per-cycle results.
Define the population before computing the statistic.

### How much data each open question needs

| Question | Effect | sd | Cycles needed | Held |
|---|---|---|---|---|
| Is the EV estimate biased? | $3.41 | $82.38 | 2,242 | 428 |
| Do bonus-winnings promos lose? | −$2.85 | $79.20 | 2,967 | 88 |
| Does insurance 2+3 make money? | +$12.73 | $87.90 | 183 | 299 ✓ |

One question is settled. The others need an order of magnitude more data
than exists. **Where a result cannot be measured, rank on mechanics.**

---

## HANDOFF — S272

1. **FIRST: review the operator's notes on burst days.** Operator has
   taken notes and wants them worked through at open, ahead of anything
   else here.
2. **Caulfield split fix** — root cause known (§2), normalise
   `scheduled_start` before the alias join, keep the runner gate. Verify
   Caulfield/Caulfield Heath and Haydock bridge while the five
   coincidental pairs do not. **Mirror the VPS capture repo — it still
   has no git remote, so `b74d99f` and this fix live only on that box.**
3. **Scratch-source reliability** (§3) — decide the fix. Trust `betfair`;
   demote book-sourced flags; never let a NULL price alone set
   `scratched`.
4. **Model recalibration** — operator flagged it as overdue. Not because
   it is provably wrong (§7 retraction two) but because international
   racing, the promo mix and the 28.4% trigger rate have all moved.
   Maintenance, not a bug fix.
5. **Alert-noise scoping to AU** — still an operator call; §1 is the
   evidence.
6. **Deploy-scheduler fix or retirement** — carried from S269, untouched.
7. **582 mis-attached BSP rows** inside the S267 import — carry into any
   analysis of that data.
8. **The AFL bet SETTLED — lost, −$50.** Recorded as "Sydney vs. Port —
   Port +48.5", not +40.5 as described in conversation. The line was
   never confirmed against the ticket, so if +40.5 was right the record
   is still wrong even though the money landed the same way. Worth
   settling for the record; it is also the bet whose account moved.
