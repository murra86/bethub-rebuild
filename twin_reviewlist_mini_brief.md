# 0m mini-brief — review pass over the 679 refused twin markets

**Authored:** S263 governance session, 2 Aug 2026. Read-only
characterization against the live capture DB + the nightly repair's own
refusal log; no code, no writes, no VPS state touched.
**Status:** PROPOSED — nothing here has been executed.

## What this is, in plain terms

The overnight twin cleanup finished its job on 31 Jul: 5,316 duplicated
race records merged. Exactly **679 markets remain deliberately
untouched** because the safety check refused them — and it was right to
refuse every one: these are not two copies of the same race, they are
**one Betfair market label sitting on two different real races**.
Merging them would have destroyed good data; that is the safety check
working. This brief says what the 679 actually are (now measured), how
to fix them, and what it costs.

**Headline: 673 of 679 are "yesterday/today" duplicate labels** — the
same market stamped on both a row dated D and a row dated D+1 for the
same venue and race slot, a leftover of the timezone date-stamping bug
that DR-036 killed on 29–30 Jul. The set is frozen history: the newest
member is 28 Jul, and **zero new ones have appeared since the fix
went live**. Nothing is leaking; this cleanup can be scheduled, not
rushed. Day-to-day betting is unaffected either way — these rows are
country/harness/greyhound history, the read-union already serves reads
across twins, and the merge refusal only means they stay unmerged.

**Confidence: HIGH** on the characterization (every number below is
from the live DB and the 1 Aug repair-run log, which agree exactly:
540 + 139 = 679). **MEDIUM** on the per-class size estimates — the
classify script in §4 produces the exact split; the samples below are
verified by hand.

---

## 1. The census and the refusal split (evidence)

- Census (`SELECT betfair_win_market_id FROM races WHERE
  betfair_win_market_id IS NOT NULL GROUP BY 1 HAVING COUNT(*)>1`):
  **679 markets / 1,361 race rows** (676 two-row, 3 three-row:
  `1.255440517`, `1.257186012`, `1.258366903` — the known members).
- Nightly repair (`racing-twin-repair`, 1 Aug 19:35 UTC run, 69.2s,
  `logs/twin_repair.log`): `{'skipped_gate': 540, 'skipped_settle':
  139}`, orphan scan all-zero, "Twin markets remaining in scope: 679".
  Every refusal is logged per market with its reason — the review list
  already exists in raw form.
- **Identity-gate refusals (540):** donor/canonical runner-name overlap
  below 50% — in fact **511 of 540 overlap ZERO names**; only 29 sit
  between 0 and 50%. These are different races, full stop.
- **Settled-count refusals (139):** the union of settled runners
  exceeds the field size (median excess 6, range 1–14 — e.g. "13
  settled on a field of 6") — two races' result sets under one label.

### Shape of the 679

| refusal | shape of the pair | n |
|---|---|---|
| gate | same venue + same race number, dates exactly 1 day apart | 425 |
| gate | different venue name, dates 1 day apart | 102 |
| gate | same venue, race number shifted by one, 1 day apart | 7 |
| gate | same date + venue, different race number (cross-code) | 6 |
| settle | same venue + same race number, 1 day apart | 128 |
| settle | different venue name, 1 day apart | 11 |

- **673/679 are exactly-one-day-apart pairs** (every multi-date gap is
  1 day). The remaining 6 are same-day cross-code collisions (below).
- The "different venue" pairs are mostly the same physical track under
  two naming streams: albion/albion park (40), ballarat/
  sportsbet-ballarat (24), geelong/ladbrokes geelong (16), gold coast/
  aquis park gold coast (4), terang/bet365 terang, plus one genuine
  cross-track name collision: **picklebet park warwick (QLD) vs
  warwick farm (NSW) — 21 markets**, and arb/coffs harbour (1).
- Dates: Mar 166, Apr 155, May 137, Jun 183, Jul 38 — flat across the
  pre-fix era, then stops. Newest rows 28 Jul; **none created after
  DR-036 shipped**.
- **677/679 predate 19 Jul** — outside the 14-day trial-metadata
  self-repair window (the S256 older-history repair remit); 60 markets
  carry one trial-flagged row.
- Venues are country/harness-heavy (markets touching the venue):
  Redcliffe 72, Albion (Park)
  102, Newcastle 57, Bendigo 35, Ballarat 56, Wagga 31, Flemington 31,
  Melton 28, Warwick pair 42, Geelong pair 34, Bathurst 17. Racing
  code is blank on 465 markets' rows (pre-backfill era); ~208 are
  harness by race-name ("Pace"/"Trot"), 6 greyhound-flagged.
- Settlement state: both rows settled on 556 markets; one settled /
  one PENDING or TIMEOUT on 119; neither settled on 4.
- Betfair capture flags: **both rows show captured** on 566 markets
  (pre-DR-036 snapshots landed on either twin — the S252 finding),
  exactly one row on 109, neither on 2. So "which row has capture" is
  NOT sufficient adjudication evidence on its own; ownership must come
  from Betfair-side truth (§4).

### What the wrongness actually looks like (verified samples)

Gate class — two clean, different races under one label (~10 sampled):

- `1.254775947` Redcliffe R1, 4 Mar vs 5 Mar (harness): 9 runners each,
  both settled, **0/9 names shared** (Glenledi Boy, Barnstormer… vs
  Wee Bonnie, Im Busted…). Same for `.949`/`.951` (R2/R3 — the whole
  meeting pair-stamped). Classic yesterday/today duplicate label.
- `1.254928003` Sunshine Coast, 7 vs 8 Mar with race-number shift
  (R1→R2): 0 overlap — next day's card renumbered, label followed the
  slot, not the race.
- `1.255042425` Picklebet Park Warwick (QLD) R1 7-runner field vs
  Warwick Farm (NSW) R1 8-runner field, consecutive days, 0 overlap —
  cross-track name collision, both rows settled with their own real
  results.
- `1.255440517` (3-row) Terang 16 Mar "R7" + bet365 Terang 17 Mar
  R6 + R7: the 16 Mar row's 10 runners are **the same horses as the
  17 Mar R7 row** (night-before fragment of the same race under the
  unsponsored venue name, mis-dated), while the R6 row is a different
  race entirely. One market, three rows, two distinct problems.
- `1.260468539` / `1.260468569` (the Wagga pair, 28 Jul, same-day):
  greyhound rows (R2 400m Mdn / R8 525m Gr4/5) and harness-named rows
  (R5/R9 "1740m Pace M") both under one label each, 0 overlap —
  cross-code id collision at a dual-meeting venue. The morning sweep's
  cross-code guard now refuses exactly this shape live (67 refusals
  on 1 Aug alone).
- `1.258366903` (3-row) Rockhampton 20 vs 21 May: a 20 May row with
  **zero runners** (empty night-before husk, PENDING) beside two real
  21 May races.

Settle class — one row contaminated with both days' results (5 sampled:
Goulburn `1.254991680`, Albany `1.257271925`, Port Macquarie
`1.258246467`, Moruya `1.259244850`, Kalgoorlie `1.259894950`):

- Goulburn R1: the 9 Mar-dated row holds 14 runners; the 10 Mar row
  holds **19 runners with interleaved duplicate finishing positions**
  — two horses "finished 1st", two "2nd" (Brutal Belle(1) AND King
  Edward(1)…). The row is the union of two days' fields, each settled
  against its own race, written onto one row by the pre-DR-036 write
  path. Port Macquarie shows 26 runners on one row, Moruya 23, Albany
  19. 116/139 settle-class markets show this over-full-row signature,
  and a wider scan finds ~249 of the 679 with a strongly over-full row
  — contamination reaches into the gate class too.
- Kalgoorlie: mis-dated row has zero runners (husk) but was still
  refused on results arithmetic — 9 such husk rows exist in the set.

---

## 2. Classification taxonomy (proposed)

Classify by **correction path**, not by symptom. Estimated sizes are
census-derived priors; the classify script (§4) makes them exact.

| class | what it is | est. size | correction |
|---|---|---|---|
| **A — wrong-day duplicate label** | two clean, distinct real races (usually same venue+R, D/D+1; incl. sponsor-alias venue pairs) | ~480–520 | keep the stamp on the true owner row; NULL `betfair_win/place_market_id` on the other. No merge, no runner moves. |
| **B — night-before husk/fragment of the same race** | 0-runner husks (9 known) + thin duplicates whose runners match the twin (Terang-style) | ~10–30 | husks: un-stamp, done. Fragments: correct the row's date stamp, then **let the existing B6 gate-passing merge take it** on the next nightly pass. |
| **C — contaminated row** | one row carries two races' runners/results (duplicate finish positions) | ~120–150 (139 settle + gate-side overfulls) | authority-driven split: move each foreign runner row to its true race row per the subscription field list for (venue, true date, race number); journal pre-images; then treat as class A. |
| **D — same-day cross-code collision** | Wagga pair + 4 more; harness/greyhound label on the wrong code's row | 6 | un-stamp the wrong-code row (owner obvious from code + runner names). Generator already blocked live by the sweep's identity guard. |
| **E — leave-as-is** | no Betfair-side truth available (2 zero-capture markets; anything ambiguous after classify) | small | leave refused, flag on the list. Costs nothing: the gate keeps them unmerged, read-union keeps reads whole, per-row results stay per-row. |

**Ownership adjudication (classes A–D), evidence in order of
strength:**
1. Betfair settlement truth — the market's settled winner
   (`betfair_historical` where present) matched against each row's
   authority results: only the true owner's winner agrees.
2. Market event time — reconstructed from the row's Betfair snapshot
   timeline (an OPEN market with moving prices only within one row's
   race window; the twin sees a closed/flat market) vs each row's
   `scheduled_start` (rows are a day apart, so this is unambiguous).
3. Runner-level `betfair_selection_id` congruence with the market's
   actual selection set.
Anything that fails all three → class E, leave.

After correction, **no market has two rows any more, so the census
clears by construction**; any pair that is genuinely the same race
(class B fragments) re-dates and then merges through the normal
nightly gate — the self-heal path stays the only merge path.

---

## 3. Why the gate must stay exactly as it is

The 50% identity gate and the settled-count audit are the reason these
679 were preserved instead of destroyed — 511 zero-overlap pairs would
have been merged into nonsense by a laxer gate. **This pass must not
touch the gate**: no threshold change, no bypass flag, no
"trusted-list" merge around it. Corrections are label removals and
date/runner repairs that make rows *eligible* for the existing gate,
never substitutes for it. (Hard interlock, per the commissioning
directive and the friction-vs-safeguards standing rule: the gate is a
contract interlock, not a warning.)

---

## 4. What runs where

1. **Classify script** — `scripts/classify_twin_reviewlist.py` (new,
   capture repo, SELECT-only, indexed access paths only: market-id
   census + `race_id`-led runner lookups — the exact query shapes this
   session ran read-only against the live box without incident).
   Emits `data/twin_reviewlist_YYYYMMDD.csv`: one line per market —
   class, per-row evidence (runner counts, settled counts, overlap,
   Betfair-truth checks), proposed action, confidence
   (`AUTO_OK` / `REVIEW` / `LEAVE`). Copy lands in `bethub-rebuild/`
   for the operator.
2. **Operator review** — bulk-approve `AUTO_OK` (expected: most of
   class A, all husks, the Wagga pair); eyeball `REVIEW` (class C and
   low-confidence A); `LEAVE` needs no action. 30–60 minutes.
3. **Correction pass** — `scripts/correct_twin_stamps.py` (new,
   journaled writer on the `merge_market_twins.py` chassis: per-market
   short transactions, WAL checkpoint cadence, disk-headroom gate,
   crash-resume by market id, `--dry-run` default). Applies approved
   actions only. Class C runner moves ship behind their own
   per-market approvals and can land in a later staged run.
4. **Verification** — census re-run (expected: 679 − approved), orphan
   scan (expected all-zero), spot-check the samples above, then let
   the nightly repair pass confirm "remaining in scope" drops to the
   approved LEAVE count.

## 5. Safety rails

- **Journal pre-images** — the repair machinery's precedent
  (`race_row_merges` + S259 journaling) extended: full pre-image of
  every touched `races` row and every moved runner row, written as
  append-only JSONL in `data/` **before** each write. **No schema
  changes of any kind** — no new tables or columns — because the 0n
  data-reset thread holds the schema-lock reserves.
- **Backups** — run only after a fresh nightly backup OK
  (`data/backups/`, 5.3 GB, 19:30 UTC); the backup is the restore
  point, the journal is the surgical undo.
- **Un-stamp beats delete** — zero row deletions in this pass; wrong
  labels are removed, every real race row is kept.
- **Timer coordination** — never run concurrent with the 19:35 UTC
  nightly twin-repair; use the same maintenance window or mask the
  timer for the run's duration.
- **Collector safety** — short transactions + busy_timeout per the
  established second-writer pattern; classify is SELECT-only and
  index-bound.

## 6. Effort estimate

| piece | estimate |
|---|---|
| classify script + tests + review-list generation | ~half a code sitting |
| operator review of the list | 30–60 min |
| correction pass for A/B/D/E (label un-stamps, re-dates) + dry-run + verification | ~half a sitting |
| class C reconstruction (runner splits vs authority) | +half–1 sitting, stageable later |

Total: **1–2 code sittings**, operator in the loop between steps.
A/B/D/E alone would already clear an estimated ~500–550 of the 679.

## 7. Dependencies and non-goals

- **0n (data reset):** holds the schema-lock reserves — this pass
  makes no schema changes. If the reset rebuilds this history first,
  re-run classify (idempotent, minutes) rather than carrying stale
  approvals across.
- **DR-036 (S259):** the generator is dead — zero new twins since it
  shipped; this is a frozen backlog, schedule at leisure.
- **S256 trial-metadata older-history repair:** stays with the
  data-reset thread; classify only *flags* the 60 trial-marked
  markets.
- **Optional follow-on, explicitly deferred:** discovering the TRUE
  market ids for un-stamped rows (many will be DR-032 outage-window
  races that legitimately have none).
- **Out of scope:** any change to the identity gate, the settled-count
  audit, the nightly repair, or the read-union; any merge outside the
  existing gate; greyhound/harness code backfill.
