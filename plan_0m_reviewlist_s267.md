# PLAN — 0m: clear the 679 refused twin markets

**Status:** PLAN, for adversarial review. Nothing applied.
**Session:** S267, 5 Aug 2026.
**Sources:** `twin_reviewlist_mini_brief.md` (S263, characterisation),
`twin_row_fix_brief.md`, `scripts/reviewlist_correct.py` (S259, built,
**never run on live**).

## Measured state, today

- Census: **679 twin markets / 1,361 rows**. Frozen — newest 28 Jul,
  zero new since DR-036 shipped. Nothing is leaking.
- Nightly repair has merged **nothing since 31 Jul** (runs in ~4s). It
  will never clear these; they are the refused population by design.
- `scripts/reviewlist_correct.py` **dry run against live, 5 Aug**:
  `{'cleared': 369, 'left': 172, 'not_refused': 138}`
  leave reasons `{'no unique keeper/loser': 167, '3 fragments': 3,
  'age fence': 2}`.

So the S259 tool already adjudicates **369 of 679** and has never been
allowed to write. The remaining ~310 are the classes it was not built
for.

## Why the gate must not be touched

The 50% identity gate and the settled-count audit are why these 679
survived instead of being merged into nonsense — **511 of 540
gate-refusals share ZERO runner names**. This work must not change a
threshold, add a bypass, or build a trusted-list merge around the gate.
Every correction here is a **label removal or a date/runner repair that
makes a row eligible for the existing gate** — never a substitute for
it. Hard interlock.

## Phasing — each phase ships and is verified before the next

### M1 — apply what is already built (369 markets)
Run `reviewlist_correct.py --apply` on live. It clears the Betfair
market-id stamp from the non-owner fragment, journalling pre-images into
`market_stamp_corrections`. No deletions, no merges, no runner moves.

Adjudication is the existing S1/S2/S3 signal set (id-envelope,
date↔start, date↔activity) with abstention rules already reviewed in
S259.

**Before applying:** take a DB backup; hand-verify a 10-market sample of
the 369 against the mini-brief's ownership evidence order (Betfair
settled winner → market event time → selection-id congruence).
**After:** census must fall 679 → ~310; orphan scan zero; read-union
still serves every affected race.

**Reversal:** the journal carries pre-images. A `--reverse` path must
exist before M1 applies — confirm it does; if not, that is part of M1.

### M2 — class D, same-day cross-code (6 markets)
Wagga pair + 4. Owner is obvious from racing_code plus runner names
(greyhound 400m Mdn vs harness "1740m Pace"). Un-stamp the wrong-code
row. Small, unambiguous, already blocked live at write time by the
morning sweep's cross-code guard.

### M3 — class B, husks and night-before fragments (~10–30)
9 known zero-runner husks: un-stamp, done. Genuine fragments (the Terang
`1.255440517` shape — same horses, mis-dated): correct the row's date
stamp and **let the existing nightly gate merge it on its own next
pass**. We do not merge here.

### M4 — class C, contaminated rows (~120–150)
The hard one. One row carries two races' runners and results — Goulburn
holds 19 runners with duplicate finishing positions, Port Macquarie 26,
Moruya 23. 116 of 139 settle-refusals show this over-full signature and
it reaches into the gate class too (~249 rows overall).

Correction is an **authority-driven split**: move each foreign runner
row to its true race per the subscription field list for
(venue, true date, race number), journal pre-images, then treat the
market as class A. This writes to `runners`, which nothing else in this
programme does.

**M4 is the phase most likely to be deferred**, and that is an
acceptable outcome — see "what good looks like".

### M5 — class E, leave and record
Anything failing all three ownership tests stays refused and goes on the
list with its reason. Costs nothing: the gate keeps them unmerged, the
read-union keeps reads whole, per-row results stay per-row.

## Risk register

| risk | mitigation |
|---|---|
| Un-stamping the WRONG fragment (destroys the good row's Betfair link) | three-signal adjudication with abstention; 10-market hand sample before M1; journal + reverse |
| M4 moves a runner to the wrong race | authority = subscription field list, not inference; pre-images journalled; phase gated behind M1–M3 proving out |
| Writing during capture | run inside the maintenance window; the repair/backup window rules apply |
| Collides with tomorrow's Phase 1 deploy | **M1 must not run in the same window as the 04:40 deploy.** Sequence them. |
| "Cleared the census" read as "fixed the data" | report per class, not one number; M5 leftovers named explicitly |

## What good looks like

M1+M2+M3 clear roughly **400–420 of 679** with low risk and full
reversibility. M4 is a separate, heavier sitting touching `runners`.
**Declaring M4 out of scope for today is the expected, correct answer**
— the set is frozen, nothing leaks, and day-to-day betting is unaffected
either way. The mini-brief itself budgets 1–2 sittings.

## Acceptance

1. Census falls by exactly the number of markets reported cleared, per
   class, with no market silently skipped.
2. Orphan scan zero after every phase.
3. A reverse run on a DB copy restores the pre-images byte-for-byte.
4. The identity gate is textually unchanged (`git diff` proves it).
5. Read-union serves every affected race before and after.
6. `uv run pytest` green on the capture repo.

## Explicitly out of scope

- Any change to the merge gate or its thresholds.
- Deletions of any kind.
- Merging anything by hand — the nightly gate stays the sole merge
  authority.
