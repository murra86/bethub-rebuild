# Free Bet button restore — Build 1 follow-up — report

**Session:** single bounded Claude Code session, 2026-06-23 (Adelaide
local, ACST). Start ~19:55 ACST, close ~20:04 ACST.
**Brief:** `interface_triage/free_bet_button_restore_brief.md` (LOCKED).
**Repo:** `/Users/tim/Desktop/Projects/bethub-v3` @ `main` (HEAD
`2329604`, unchanged at close).
**Outcome:** the bare "Free Bet" pick is restored to the race-screen
promo bar; selecting it drives the EV column into free-bet → cash
conversion mode via the intact `evFreeBet` path. Frontend-only. Zero
backend change. Settlement byte-identical. No regressions.

Findings route to the next operator-Claude triage (per §8 / §10); this
report makes no recommendations and authors no next brief.

---

## §0 — Baseline

- **HEAD:** `2329604` at start and close (no commit/checkout/reset).
- **Settlement seam (bet-safety gate):**
  `workflows/bet_entry/v1/settlement.py` SHA-256 unchanged at close —
  `9e07a75d3ab85741d5c3346521dbca25d09da632bd1140fcdb6550e55840d4a3`
  (trivially, frontend-only — proven anyway, §7).
- **Dirty-tree substrate (expected):** HEAD `2329604`, **69** `git status`
  entries at start and close. `ui/web/src/` is an untracked directory, so
  the three edited/added files add no new top-level git entry. The
  uncommitted Build 1 work + in-flight `betfair_client` work were left
  byte-identical (no git state-changing command run).
- **Test baseline:** Python `uv run pytest -q` **1166** at start and
  close (this fix adds no Python). Frontend `vitest run` 103 → **109**;
  `tsc -b` clean.

Sequence followed the §6 order (§5.1 → §5.2 → §5.3) in one pass.

---

## §5.1 — Restore the Free Bet pick on the promo bar

**Built.** A single fixed **"Free Bet"** button now renders alongside the
catalogue-driven buttons in `PromoBar.tsx`, inside the same `presetGrid`,
immediately after the `catalogue.map(...)` block. It is a built-in picker
affordance — it renders regardless of catalogue contents and is **not** a
catalogue row.

Wiring (the `presetId`-vs-null choice the brief left to my discretion):
**I added a small dedicated `FREE_BET_CONFIG` constant** to `presets.ts`
rather than revive `buildConfigFromPreset(findPreset('free_bet'))` — tidier
(no lookup that can return null, minimal imports) and it narrows the
finding-F6 reversal to *exactly* the free-bet slice (the unused
`buildConfigFromPreset` / `findPreset` / `PROMO_PRESETS` helpers stay dead,
left for the §11 cleanup brief). The constant carries `promo_type:
'free_bet'`, `promo_template_id: null`, all terms null; `presetId:
'free_bet'` is provenance-only (no active-state logic reads it).

Behaviour (all per §5.1):

- **Active state** keys on `config.promo_type === 'free_bet'` (catalogue
  buttons key on `config.promo_template_id`), surfaced via the same
  `presetActive` class + `aria-pressed`.
- **Toggle off:** clicking the active Free Bet button clears to
  `EMPTY_PROMO_CONFIG` (new `selectFreeBet` handler, mirroring
  `selectCatalogue`'s re-click toggle).
- **Mutual exclusion** is automatic: `onChange` replaces the whole config,
  so selecting Free Bet (serial null, `promo_type` free_bet) deactivates
  every catalogue button, and selecting a catalogue row (serial set,
  `promo_type` insurance/etc) deactivates Free Bet. Verified in tests.

## §5.2 — EV-column conversion display (verified, not rebuilt)

`evEngine.ts` was **not touched** (read-only per §4 / §9). Confirmed the
restored pick reaches the conversion branch: `OddsTable` calls `promoEV`
whenever `promoConfig.promo_type` is truthy, and `promoEV`
(`evEngine.ts:488`) routes `promo_type === 'free_bet'` (with a Betfair lay
price) to `evFreeBet(bookOdds, bfLay, stake, mbr)` at
`DEFAULT_FB_CONVERSION_RATE = 0.65`. A unit test asserts this path returns
the `evFreeBet` figure, distinct from `evNoPromo` (§5.3).

Cosmetic: with `promo_type === 'free_bet'`, the always-on "max stake" and
"return type" controls in `PromoBar`'s config row remain visible but inert
(the free-bet EV ignores them; the insurance/bonus-specific fields are
already gated off). Per §5.2 suppression is optional and not required — I
**left them visible** to keep the change maximally surgical (no edit to the
config-panel JSX, no risk to the existing render tests). Noted as F1.

## §5.3 — Test

**New file `ui/web/src/components/PromoBar.test.tsx`** (6 tests; the
existing `evEngine.test.ts` / `OddsTable.test.tsx` were left
byte-unchanged):

- the Free Bet button renders alongside the catalogue;
- selecting it emits a config with `promo_type === 'free_bet'` and
  `promo_template_id === null`;
- re-clicking the active button clears to empty (`promo_type` null);
- selecting Free Bet replaces an active catalogue pick (asserts the
  catalogue button is active before, Free Bet active after — exactly one);
- selecting a catalogue row replaces an active Free Bet pick;
- **EV path:** `promoEV(..., { promo_type: 'free_bet' }, bfLay, mbr)`
  returns the `evFreeBet` conversion, `not` equal to `evNoPromo`.

---

## §7 — Empirical verification (before / after)

| Check | Before | After |
|---|---|---|
| `tsc -b` | clean | **clean (exit 0)** |
| `vitest run` | 16 files / 103 tests | **17 files / 109 tests, 0 regressions** |
| Python `uv run pytest -q` | 1166 passed | **1166 passed (unchanged)** |
| `settlement.py` SHA-256 | `9e07a75d…40d4a3` | **identical** |
| HEAD / `git status` count | `2329604` / 69 | **`2329604` / 69** |
| git state-changing commands | — | **none run** |

---

## §8 — Findings / surprises

**F1 — Inert term controls left visible for the free-bet case (cosmetic,
by choice).** `PromoBar`'s "max stake" / "return type" controls are gated
only on `config.promo_type` being truthy, so they show for `free_bet` too,
though the free-bet EV ignores them. §5.2 made suppression optional; I left
the config-panel JSX untouched to stay surgical. A later pass could gate
those two controls on `promo_type !== 'free_bet'` if the operator finds
them misleading — flagged, not chased.

**F2 — F6 dead code only partially reversed (intended).** Build 1's finding
F6 named `PROMO_PRESETS` / `buildConfigFromPreset` / `findPreset` as
unreferenced. This fix did **not** revive them — it added a fresh
`FREE_BET_CONFIG` constant instead — so those three remain dead code (the
`free_bet` *entry* in `PROMO_PRESETS` is now duplicated in spirit by the
constant). Consistent with §11's "revive the free-bet slice only; a later
cleanup brief drops what stays unused."

**F3 — Mutual exclusion needs no extra logic.** Because the picker is a
single controlled `config` that `onChange` replaces wholesale, catalogue ↔
Free-Bet exclusivity falls out of the active-keying (serial vs
`promo_type`) with no cross-clearing code. Confirmed by test.

No surprises touching backend, settlement, or persistence; the work fit one
session comfortably.

---

## §9 — Files touched (complete list)

**Production (frontend only, all under the named §5 anchors):**
- `ui/web/src/promos/presets.ts` — added the `FREE_BET_CONFIG` constant
  (§5.1).
- `ui/web/src/components/PromoBar.tsx` — import `FREE_BET_CONFIG`, new
  `selectFreeBet` toggle, the "Free Bet" button in the preset grid (§5.1).

**Tests (new):**
- `ui/web/src/components/PromoBar.test.tsx` — 6 tests (§5.3).

**Deliberately NOT touched:** `ui/web/src/ev/evEngine.ts` (read-only —
conversion logic reused as-is); any Python / backend / schema / seed /
catalogue file; `scripts/seed_promos.py` (stays at 9 rows); the
`is_free_bet` path; `settlement.py` (SHA-proven). No git state-changing
command.

---

## §10 — Self-assessment

- **Coverage:** §5.1 built; §5.2 verified by a unit test that the restored
  pick reaches `evFreeBet`; §5.3 adds 6 tests, 0 regressions. Every §7
  check captured before/after.
- **Confidence:** high on the wiring + EV routing (tsc clean; the `promoEV`
  free-bet branch asserted against `evFreeBet` and `evNoPromo`) and on the
  disciplines (settlement SHA identical, Python 1166 unchanged, 69 git
  entries, ui/web-only edits).
- **Not done (honest):** no live-app render check (out of scope; the §10
  triage live-validates) — the conversion-vs-no-promo distinction is proven
  at the unit level, not pixel-confirmed. The optional cosmetic suppression
  of the inert term controls (F1) was not done.
- **Repo integrity:** HEAD unchanged; no `git add`/`commit`/`stash`/
  `restore`/`checkout`/`reset`; only the three named `ui/web/src/` anchors
  changed; the uncommitted Build 1 + in-flight `betfair_client` work left
  byte-identical; `settlement.py` byte-identical; no DB access. Adelaide
  timestamps throughout.
