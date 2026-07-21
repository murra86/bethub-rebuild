# Free Bet button restore — Build 1 follow-up — Code brief

**Status:** LOCKED (pending operator sign-off at hand-off).
**Type:** Surgical frontend fix. Single bounded Code session.
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3` @ `main`
(HEAD `2329604`).
**Depends on:** Build 1 (promo-attach foundation) — built, in the
working tree, uncommitted.

---

## §1 — What this brief is and is not

This is a **surgical frontend fix**, executed in a single bounded
Code session. It restores the bare "Free Bet" pick to the
race-screen promo bar so selecting it drives the EV column into
free-bet → cash conversion mode (the v2 behaviour).

It is **not** a backend change, a schema change, a catalogue/seed
change, or any Build 2 (credit-in) work. It does not touch
settlement. Surprises become findings in the report, not
mid-session escalations or scope chases. Any remediation beyond
the named anchors routes to the next operator-Claude triage
session, not Code's report.

## §2 — Why this work exists

Build 1's §5.3 reconciliation call (Code finding F1) excluded the
bare "Free Bet" from the promo catalogue and removed its picker
button, on the reasoning that it carries no refund terms and is
"just a deployment marker."

That reasoning missed an operational function. In v2, selecting
"Free Bet" flips the race-screen EV column into **free-bet → cash
conversion** mode: each runner's EV shows the realised value of
converting a held free bet (back at book odds, lay on Betfair) at
the canonical 65% conversion rate. The operator uses this every
burst to spot which free bets are good conversions (targeting the
65–70% band). Removing the button removed that tool. The operator
has called for it restored, as it was in v2.

The conversion logic is intact in the EV engine (`evFreeBet`,
driven by `promo_type === 'free_bet'`, `DEFAULT_FB_CONVERSION_RATE
= 0.65`, in `ui/web/src/ev/evEngine.ts`). Only the picker entry
that reaches it was removed. This brief restores that entry.

## §3 — Pre-reads

Required, in order:

1. This brief.
2. `ui/web/src/components/PromoBar.tsx` — the catalogue-driven
   picker (the edit anchor).
3. `ui/web/src/promos/presets.ts` — holds the existing `free_bet`
   preset + `buildConfigFromPreset` / `findPreset` (unreferenced
   since Build 1 — finding F6 — the substrate this fix reuses) and
   `buildConfigFromCatalogue`.
4. `ui/web/src/ev/evEngine.ts` — the free-bet EV branch
   (`promo_type === 'free_bet'` → `evFreeBet`); read-only, do not
   edit.

Reference-only (no full read needed):

- `interface_triage/promo_attach_build1_report.md` — Build 1
  report (F1, F6 context).
- `interface_triage/promo_attach_build1_brief.md` — the locked
  Build 1 contract.

## §4 — System access

- **Mac filesystem, read-write**, limited to the named frontend
  anchors under `ui/web/src/`.
- **No database access** (this fix touches no persistence). No
  `capture.db`. No VPS / SSH.
- **No backend (Python) edits.**
- Adelaide local timestamps (ACST/ACDT) per DR-021 (timestamp
  anchoring, Adelaide local time) throughout the report.

**Dirty-tree substrate (expected, not drift):** the working tree
carries Build 1's uncommitted changes plus the operator's
in-flight `betfair_client` work — HEAD `2329604`, 69 `git status`
entries. `ui/web/src/` is an untracked directory, so editing files
within it adds no new top-level git entries. **Do not run any git
state-changing command** (`add` / `commit` / `stash` / `restore` /
`checkout` / `reset`) — a stash or reset would wipe the
uncommitted Build 1 build. Edit only the named anchors; leave
every other working-tree change byte-identical.

## §5 — Scope

### §5.1 — Restore the Free Bet pick on the promo bar

In `ui/web/src/components/PromoBar.tsx`, add a single fixed **"Free
Bet"** button alongside the catalogue-driven buttons (the
`catalogue.map(...)` block). It is a built-in picker affordance,
**not** a catalogue row — it renders whether or not the catalogue
contains it.

Selecting it sets a promo config with `promo_type: 'free_bet'` and
all terms null (`max_stake`, `return_pct`, `insured_positions`,
`return_type` null; `promo_template_id` null). Reuse the existing
`free_bet` preset substrate in `presets.ts` —
`buildConfigFromPreset(findPreset('free_bet'))` returns exactly
this — or a small dedicated free-bet config constant; Code's call
on the tidiest wiring. Reviving `buildConfigFromPreset` /
`findPreset` / the `free_bet` entry of `PROMO_PRESETS` for this one
button is in scope (it reverses part of finding F6).

Behaviour:

- **Active state:** catalogue buttons key active on
  `config.promo_template_id`; the Free Bet button has no serial, so
  key its active state on `config.promo_type === 'free_bet'`.
- **Toggle off:** clicking the active Free Bet button clears to
  `EMPTY_PROMO_CONFIG` (mirroring `selectCatalogue`'s re-click
  toggle).
- **Mutual exclusion:** selecting Free Bet replaces any active
  catalogue pick and vice versa (one active promo at a time, as
  today).

### §5.2 — EV-column conversion display (verify, do not rebuild)

With `promo_type === 'free_bet'` set, the existing EV engine path
already drives the conversion display: `evForRunner` routes
`promo_type === 'free_bet'` to `evFreeBet(bookOdds, bfLay, stake,
mbr)` at `DEFAULT_FB_CONVERSION_RATE = 0.65`, computing the
per-runner free-bet → cash conversion EV where a Betfair lay price
exists. **Do not modify `evEngine.ts`.** Confirm the restored pick
reaches this branch and the EV column shows the conversion (not the
no-promo EV).

The per-promo config fields in `PromoBar` (max stake / return % /
insured / return type) are gated on `insurance` / `bonus_winnings`;
for `free_bet` none of the term fields are relevant. Leaving the
always-on "max stake" / "return type" controls visible is
acceptable; optionally suppress them for the `free_bet` case if
trivial (cosmetic, Code's call — not required).

### §5.3 — Test

Add focused frontend coverage (vitest) without disturbing the
existing 103:

- `PromoBar`: the Free Bet button renders; selecting it calls
  `onChange` with a config whose `promo_type === 'free_bet'` and
  `promo_template_id === null`; re-click clears to empty; selecting
  a catalogue row then Free Bet (and vice versa) leaves exactly one
  active.
- EV path (if not already covered): `promo_type === 'free_bet'`
  with a lay price returns the `evFreeBet` conversion, distinct
  from `evNoPromo`.

## §6 — Sequencing within session

One natural order: §5.1 (button + config wiring) → §5.2 (confirm
the EV branch fires) → §5.3 (tests). All three sit in the same
frontend surface; do them in one pass. If a cleaner order
surfaces, Code may deviate and note it.

## §7 — Empirical verification (before / after)

Capture both states in the report:

- **Frontend:** `tsc -b` clean (exit 0); `vitest run` green — 103
  existing + the new cases, 0 regressions.
- **Backend untouched:** Python `uv run pytest -q` count unchanged
  at **1166** (this fix adds no Python; run once to prove no
  regression).
- **Settlement seam (bet-safety gate):**
  `workflows/bet_entry/v1/settlement.py` SHA-256 byte-identical to
  `9e07a75d3ab85741d5c3346521dbca25d09da632bd1140fcdb6550e55840d4a3`
  (trivially — frontend-only — but proven).
- **Git state:** HEAD `2329604` unchanged; `git status` entry
  count unchanged at 69; no git state-changing command run.

## §8 — Output spec

Single report at
`interface_triage/free_bet_button_restore_report.md`. Structure:
baseline (§0), the change made (§5.1–§5.3 mirrored), empirical
verification (before/after), findings/surprises, files touched
(complete list), self-assessment. Rough length 80–160 lines. **No
recommendations, no next-brief authoring** — findings route to the
next operator-Claude triage. Adelaide timestamps.

## §9 — Hard limits (non-negotiable)

Code does **not**:

- Touch any **Python / backend** file — this fix is frontend-only.
- Change **schema**: do not expand the `promo_template.kind` CHECK
  or the `PromoTemplateKind` enum (the closed set has no `free_bet`
  and altering the CHECK means a table rebuild — out of scope by
  design).
- Add a **catalogue row** or edit `scripts/seed_promos.py` — the
  seed stays at 9 rows; the Free Bet is a picker affordance, not a
  catalogue offering.
- Touch the **`is_free_bet`** path / toggle — it remains the
  independent deployment marker, unchanged.
- Touch **settlement** (`settlement.py`),
  `apply_manual_operator_resolution`, the bet-persistence path, or
  any other backend seam.
- Do any **Build 2** work — no credit-in, no cycle-link, no
  `promo_ev_at_log` change, no idempotency.
- Run any **git state-changing** command, or edit any file outside
  the named §5 anchors.
- Modify `evEngine.ts` — the conversion logic is correct and
  reused as-is.

## §10 — What happens after Code's session

The next operator-Claude session reads
`free_bet_button_restore_report.md`, triages (inventory pass;
confirm the bet-safety gate held / frontend-only; confirm the Free
Bet pick drives the conversion EV; live-validate in the launched
app alongside the queued Log Past Bet check), and on a clean
triage proceeds to the **Build 2 brief** (credit-in + cycle link).
Code does not author the next brief.

## §11 — Cross-references

- **Build 1** — `promo_attach_build1_brief.md` (contract),
  `promo_attach_build1_report.md` (finding F1 reversed here, F6
  substrate reused here).
- **DR-032** (amended S180 — bet promo link =
  `bets.promo_template_id`, the kind-catalogue serial):
  unaffected; the free-bet pick carries no serial
  (`promo_template_id` null), consistent with the closed kind-set.
- **EV engine** — `ui/web/src/ev/evEngine.ts` `evFreeBet` +
  `DEFAULT_FB_CONVERSION_RATE = 0.65` (the 70→65 drop, S166).
- **Excluded (parking-lot / later):** the broader `presets.ts`
  dead-code cleanup (F6) — this fix revives the free-bet slice
  only; a later cleanup brief drops what stays unused.
