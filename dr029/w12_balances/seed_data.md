# Seed data spec — promo_template + warning_catalogue (W12 pre-build)

**Status:** Content spec, locked at Session 132 (2026-05-13 ACST).
**Purpose:** Operator-confirmed content for the v3
`promo_template` and `warning_catalogue` reference tables.
Defines what rows exist at seed-time; the W12 brief picks up
this spec and specs the Code-side seed mechanism as a build
task.
**Path:** `dr029/w12_balances/seed_data.md`.

**Cross-references:**
- W13 report (Code's ship):
  `dr029/w13_promos/w13_promos_report.md`
- W13 brief (the substrate spec):
  `dr029/w13_promos/w13_promos_brief.md`
- Slug-flip dependency: `warning_type_id` flips from `UUID` to
  `str` in `domain/promos/__init__.py` before warning entries
  can be written via the typed Pydantic path. Slug-flip is W12
  brief step zero per Session 131 call.

---

## 1 — Approach

Templates are catalogued by *mechanic shape*, not by literal
advertised offering. Specific per-instance values (cap, %,
places when variant, payout type when variant) live on per-promo
observation events, not on the template row. The template
defines what shape the mechanic takes and carries typical
default values via the `default_terms` JSON field.

This means:

- The catalogue is stable (~7 rows today, ~10–30 long-term per
  the model docstring) and doesn't need a new row every time a
  book offers $35 instead of $25.
- Per-instance terms (the actual cap, %, places this time
  around) are captured in `promo_observed` event payloads as
  `terms_at_observation`. Those are the operationally-binding
  values for any specific bet placed against the promo.
- Template `default_terms` provides typical values so the
  catalogue is navigable — "Cash refund if 2nd, default cap
  $25" reads cleanly without forcing the operator to look up
  every Promo instance.

Five template categories exist in the shipped schema:
`INSURANCE`, `BONUS_WINNINGS`, `PRICE_BOOST`, `EW_CASHBACK`,
`OTHER`. Seven rows are seeded across four of those
(`INSURANCE` × 3, `BONUS_WINNINGS` × 2, `PRICE_BOOST` × 1,
`OTHER` × 1). `EW_CASHBACK` is left empty pending operator use.

---

## 2 — Promo templates (7 rows)

### T1 — Cash refund if 2nd

- **kind:** `INSURANCE`
- **name:** "Cash refund if 2nd"
- **default_terms:**
  ```json
  {
    "payout_type": "cash",
    "places_refunded": [2],
    "refund_cap_default": 25,
    "refund_cap_currency": "AUD"
  }
  ```
- **mechanic_description:** Cash refund of stake up to a stated
  cap if your runner finishes 2nd. Refund is paid as cash, not
  a free bet. Refund equals the lesser of actual stake and
  stated cap. Typical caps observed: $25, $50.
- **operational notes:** the more common of the two cash-based
  insurance promos in current rotation. Cash refund means the
  cycle short-circuits at outcome 3 (insurance triggers) — no
  follow-on free bet leg.
- **per-instance variation:** actual cap (often $25 or $50)
  captured in the observation event's `terms_at_observation`.

### T2 — Free bet if 2nd

- **kind:** `INSURANCE`
- **name:** "Free bet if 2nd"
- **default_terms:**
  ```json
  {
    "payout_type": "free_bet",
    "places_refunded": [2],
    "refund_cap_default": 25,
    "refund_cap_currency": "AUD"
  }
  ```
- **mechanic_description:** Free bet equal to stake up to a
  stated cap if your runner finishes 2nd. Free bet pays winnings
  only (stake not returned on use). Typical caps observed: $25,
  $50.
- **operational notes:** the most-frequent free-bet-based
  insurance variant. Cycle continues — follow-on free bet leg
  typically converts ~70% of face value per the standing
  single-cycle convention.
- **per-instance variation:** actual cap (often $25 or $50)
  captured in the observation event.

### T3 — Free bet if 2nd or 3rd

- **kind:** `INSURANCE`
- **name:** "Free bet if 2nd or 3rd"
- **default_terms:**
  ```json
  {
    "payout_type": "free_bet",
    "places_refunded": [2, 3],
    "refund_cap_default": 25,
    "refund_cap_currency": "AUD"
  }
  ```
- **mechanic_description:** Free bet equal to stake up to a
  stated cap if your runner finishes 2nd or 3rd. Free bet pays
  winnings only. Typical caps observed: $25, $50.
- **operational notes:** broader-places variant of T2;
  insurance triggers more often (two place positions vs one) so
  the effective expected value of the insurance layer is higher
  per cycle. Less common than T2 in current rotation.
- **per-instance variation:** actual cap captured in the
  observation event. If a rare 2nd/3rd/4th variant surfaces at
  a book (or the rare any-non-winner variant), the wider places
  list is captured at observation-time via `places_refunded` in
  `terms_at_observation` rather than needing a new template.

### T4 — Goodwill free bet

- **kind:** `OTHER`
- **name:** "Goodwill free bet"
- **default_terms:**
  ```json
  {
    "payout_type": "free_bet",
    "trigger": "standalone_goodwill_issue",
    "common_sources": [
      "signup_bonus",
      "deposit_bonus",
      "random_gift",
      "compensation_for_service_issue"
    ]
  }
  ```
- **mechanic_description:** Free bet issued by the bookmaker as
  a standalone gift, not triggered by another promo. Sources
  include signup bonuses, deposit bonuses, random goodwill
  issues, and service-issue compensation. Free bet pays winnings
  only on use.
- **operational notes:** rare in volume terms but worth
  cataloguing because the cycle shape differs — there's no
  upstream original-bet leg, so the cycle starts at the free bet
  placement rather than at an insurance-triggered free bet.
- **per-instance variation:** face value of the free bet is
  captured at the `free_bet_credited` event (event-level
  `amount` field), not on the template. Source (signup vs
  deposit vs random vs compensation) can be tagged via the
  observation event's `terms_at_observation` or via a
  `promo_journey_annotation` tag.

### T5 — Price boost (straight uplift)

- **kind:** `PRICE_BOOST`
- **name:** "Price boost (straight uplift)"
- **default_terms:**
  ```json
  {
    "payout_type": "cash",
    "boost_mechanic": "price_uplift",
    "typical_uplift_range": "5% to 30%"
  }
  ```
- **mechanic_description:** Advertised-price uplift on a specific
  runner (e.g. $3.00 advertised, $3.50 after boost). Cash payout
  at the boosted price on win. Typically a click-to-activate
  boost on the book's promo surface.
- **operational notes:** the simplest of the three boosted-odds
  variants — no cycle, no free bet leg, no parameter beyond the
  uplift itself. Strategy 2 (Price Booster) bread-and-butter.
- **per-instance variation:** original odds, boosted odds, the
  specific runner, and the race are captured in the observation
  event's `terms_at_observation`. No template-level uplift value
  because every boost is runner-specific.

### T6 — Bonus winnings (free bet)

- **kind:** `BONUS_WINNINGS`
- **name:** "Bonus winnings (free bet)"
- **default_terms:**
  ```json
  {
    "payout_type": "free_bet",
    "bonus_pct_default": 100,
    "bonus_cap_default": 50,
    "bonus_cap_currency": "AUD",
    "common_examples": "PickleBet 100% bonus winnings as FB"
  }
  ```
- **mechanic_description:** On a win, pays advertised odds in
  cash plus a free bet equal to a percentage of winnings, up to
  a stated cap. Free bet pays winnings only on subsequent use.
- **operational notes:** cycle-shaped per the standing single-
  cycle convention — original cash payout plus follow-on free
  bet leg (which itself converts ~70% on use). Bonus % varies
  by book and offering; cap commonly $50 but varies.
- **per-instance variation:** actual `bonus_pct` and `bonus_cap`
  captured in the observation event. Where a book runs the
  promo on specific events (spring carnival, AFL grand final,
  etc.), the event identity may also be captured via observation
  scope.

### T7 — Bonus winnings (cash)

- **kind:** `BONUS_WINNINGS`
- **name:** "Bonus winnings (cash)"
- **default_terms:**
  ```json
  {
    "payout_type": "cash",
    "bonus_pct_default": 25,
    "bonus_cap_default": 50,
    "bonus_cap_currency": "AUD",
    "common_examples": "Bet365 25% bonus winnings as cash"
  }
  ```
- **mechanic_description:** On a win, pays advertised odds in
  cash plus an additional cash payment equal to a percentage of
  winnings, up to a stated cap.
- **operational notes:** structurally a price-uplift cousin — no
  follow-on cycle, no free bet leg, just a bonus cash payout on
  the original win outcome. Strategy 2 sub-shape; the most-used
  bonus-winnings variant in v2 today.
- **per-instance variation:** actual `bonus_pct` and `bonus_cap`
  captured in the observation event.

---

## 3 — Warning catalogue (5 entries)

Slug IDs per Session 131 call (`warning_type_id` flips from
`UUID` to `str` in `domain/promos/__init__.py` as W12 brief
step zero before any of these can be written via the typed
Pydantic path).

Severities below are baseline per the DR-015 three-tier scheme
(`red` / `amber` / `yellow`). Specific raise events can override
via `severity_at_raise` on the raise event payload.

### W1 — `rapid_promo_turnover`

- **label:** "Rapid promo turnover"
- **severity:** `amber`
- **description:** Turnover velocity on promotional bets at a
  single bookmaker has exceeded normal pace. Note: this is
  promo-specific. High turnover on non-promotional bets is not
  flagged — that's what bookmakers expect from mug-punter
  accounts and is a positive signal, not a warning. The warning
  fires only when the velocity is on bets carrying a promo
  reference.
- **default_clearance_criteria:** Reduce promo-bet frequency at
  this book for a sustained period (specific threshold defined
  during AccountCare automation work).

### W2 — `large_deposit_burst`

- **label:** "Large deposit burst"
- **severity:** `amber`
- **description:** Multiple deposits to a single bookmaker within
  a single day. Typical retail behaviour is one or two deposits
  spread across longer time windows; same-day multi-deposit
  patterns look suspect to a bookmaker's review systems.
- **default_clearance_criteria:** No new deposits at this
  bookmaker for a sustained period (specific threshold defined
  during AccountCare automation work).

### W3 — `big_win_pattern`

- **label:** "Big win pattern"
- **severity:** `red`
- **description:** Two or more free-bet wins at the same softbook
  within a short time window. Strong signal to the bookmaker
  that the account is exploiting promo mechanics rather than
  recreational punting. Operator framed at Session 132 as
  "definitely a flag."
- **default_clearance_criteria:** Sustained period of normal-bet
  activity at this book with no further free-bet wins (specific
  threshold defined during AccountCare automation work).

### W4 — `multi_account_signal`

- **label:** "Multi-account signal"
- **severity:** `red`
- **description:** Behavioural fingerprint risk across linked
  personas — patterns that could allow a bookmaker to correlate
  accounts (shared IP, device fingerprint, deposit/withdrawal
  patterns, betting pattern similarity). Detection trigger is
  future AccountCare workstream territory ("the constellation of
  apps" per operator framing); this entry exists so the warning
  kind is pre-defined in the catalogue when AccountCare ships.
- **default_clearance_criteria:** Out of scope for W12 — defined
  during AccountCare workstream.

### W5 — `promo_chasing_pattern`

- **label:** "Promo chasing pattern"
- **severity:** `red`
- **description:** High count of promotional bets taken at a
  single bookmaker within a short time window (e.g. 50+ promos
  within a couple of days). Strong signal that the account is
  bonus-hunting rather than recreational punting. Operator
  framed at Session 132 as "probably the most important"
  warning.
- **default_clearance_criteria:** Extended period with no
  promotional bets at this book; resume slowly (specific
  threshold defined during AccountCare automation work).

---

## 4 — How this seed flows into W12 derivations

The seed enables W12 read-side derivations to surface meaningful
operator-facing state at v3 build proper:

- **Free-bet inventory state** (derived from `promo_events`):
  events carry `promo_template_id` references; the inventory
  derivation surfaces current FB holdings grouped by template
  category (cash insurance-cycle FBs vs goodwill FBs vs
  bonus-winnings FBs).
- **AccountCare warning state** (derived from
  `accountcare_warning_raised` − `accountcare_warning_cleared`
  per account_at_book): events carry `warning_type_id` slug
  references; the warning state derivation joins through to the
  catalogue for label and severity display.
- **Promo journey state** (derived from `promo_observed` event
  flow per `(promo_template_id, book_id, account_at_book_id)`
  triple): joins through to the catalogue for template name and
  category.

The seed is mutable reference data per the model docstring — the
operator can update fields (severities, descriptions, default
terms) after seed-time without code changes. A re-seed is cheap
if the catalogue shape needs revision once W12 derivations are
exercised against real data.

---

## 5 — What this spec does NOT cover

- **Detection triggers / thresholds for warnings.** When each
  warning fires (50 promos in 2 days = `promo_chasing_pattern`
  raised; N deposits in 1 day = `large_deposit_burst` raised)
  is downstream AccountCare workstream territory. The catalogue
  only declares what kinds of warnings can exist.
- **Each-way cashback templates.** `EW_CASHBACK` kind exists in
  the shipped schema but no templates are seeded — not currently
  used per Session 132 operator framing. Add when first observed
  at a book.
- **Abstract / event-driven promos.** TAB's win-or-2nd at $3.50
  example (Harville-derived place-market EV), spring carnival /
  AFL grand final special offers, SGM/SRM bonus-back promos all
  belong to the post-v3 analytical layer. The template schema
  has the flexibility to express them via `default_terms` JSON
  when they're modelled later, without schema changes.
- **The seed mechanism itself.** Whether the rows land via raw
  SQL, via Pydantic-via-adapter, or via a one-off seed script is
  W12 brief territory. This document specifies *what* to seed,
  not *how*.

---

## 6 — Slug-flip dependency

`warning_type_id` is currently typed `UUID` in
`domain/promos/__init__.py` (shipped W13). Session 131 call:
flip to `str` to support slug IDs as the catalogue's canonical
identifier. Slug-flip is **W12 brief step zero** — must land
before any of W1–W5 above can be written via the typed Pydantic
path.

The underlying SQL column is already `TEXT` and accepts either
shape, so a raw-SQL seed mechanism could in principle land
before the slug-flip if needed. The W12 brief will spec the
chosen approach (Pydantic-via-adapter recommended for type
safety and ledger consistency with the rest of the W13 surface).

---

**Spec locked at Session 132.**
