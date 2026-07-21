# Consolidated frontend fix brief — pre-cutover interface polish

**Drafted:** Session 193 (2026-06-25 ACST).
**Target repo:** `bethub-v3` (frontend only — `ui/web/src`).
**Type:** surgical fix, single bounded Code session.
**Anchor baseline:** HEAD `2329604`, branch `main`, working tree dirty
(~69 entries — the expected uncommitted build substrate from the
promo-attach / account-ref arc). **`ui/web/src/` is UNTRACKED in git**
(shows as `?? ui/web/src/`) — see §9 for what that means for
verification and git discipline.

---

## §1 — What this brief is and is not

This brief commissions **seven frontend fixes** to the v3 racing
interface, surfaced in the Session 189 pre-cutover live-validation
sweep. It is a single bounded Code session.

- It **is** a frontend-only polish + one flow-rebuild (item 3) against
  named React components.
- It is **not** a backend change. No settlement, no money-path, no
  credit-in / consume logic, no schema, no API contract change. The
  free-bet cycle-linkage machinery (consume + qualifier-cycle
  inheritance) already exists server-side and is **read/used, never
  modified** (§5.3).
- Surprises become **findings** in the report, not mid-session
  escalations or scope creep. Remediation routes to the next
  operator-Claude triage session, not Code's report.

## §2 — Why this work exists

The S189 sweep was the operator's first full live walk of the launched
v3 app. No 500s fired, but seven interface deficiencies were logged.
Six are small polish; one (item 3, the lay→log flow) is a deliberate
rebuild of v2's proven "Place Lay & Log" sequence — the operator places
the Betfair lay first to lock the price, then logs the soft-book leg.
All seven are pre-cutover must-clears for a clean daily-driver
interface. Interface-refinement stream.

## §3 — Pre-reads

Required, in order:
1. This brief, in full.
2. `ui/web/src/routes/Racing.tsx` — the race-screen orchestrator (owns
   `manualOdds`, the modal + log-panel wiring).
3. `ui/web/src/components/HedgeModal.tsx` — the Betfair quick-lay modal.
4. `ui/web/src/components/LogBetPanel.tsx` — the soft-book log panel.
5. `ui/web/src/components/OddsTable.tsx` — the odds column.
6. `ui/web/src/components/PromoBar.tsx` — the top-of-page promo bar.
7. `ui/web/src/App.tsx` + `App.module.css` — the shell / nav bar.

Reference-only (requirements, NOT to port code from):
- `bethub-v2/frontend/src/components/HedgeModal.jsx` — v2's proven
  Place-Lay-&-Log flow (the `handlePlaceAndLog` path, the
  partial-fill banner, the stop-polling-on-log behaviour, the T/H/G
  PERSIST/LAPSE split). Item 3 mirrors this shape.
- `operator_workflow_map.md` (rebuild root) — the live betting workflow.

## §4 — System access

- **Mac filesystem**, read-write, scoped to `bethub-v3/ui/web/src` +
  `App.module.css` and the per-component `.module.css` files named in
  §5. No file outside `ui/web` is edited.
- **No DB access, no VPS, no Betfair API.** This is pure frontend.
- Adelaide local timestamps (ACST/ACDT) per DR-021 in the report.

## §5 — The seven fixes

### §5.1 — Sticky top nav (banner "freeze")

**Symptom:** the top banner with the menu options scrolls away / does
not stay put.
**Anchor:** `App.tsx` `NavBar` + `App.module.css` `.nav`.
**Change:** make `.nav` stay pinned to the top of the viewport
(sticky/fixed header, `top: 0`, an appropriate `z-index` above the
page content). Confirm no content is hidden behind it (add top
offset/padding to the page container if the sticky nav overlaps the
first row).
**Note:** "freeze" is read as "keep it pinned." If Code finds the nav
instead *locks up / becomes unresponsive* (a different fault), that is
a **finding** — report it, do not guess a fix.

### §5.2 — Odds column: accept "1" + Delete-to-clear

**Symptom:** typing `1` into an empty soft-odds box does nothing
(2–9 work); the keyboard Delete key does not clear a selected box.
**Anchor:** `OddsTable.tsx` — the soft-odds `<input className={styles.stepperVal}>`
`onChange` handler. The current guard
`if (Number.isFinite(n) && n > 1) setManualOdds(...)` rejects every
keystroke whose running value is ≤ 1, so the leading `1` of `1.50`
is dropped and entry is blocked.
**Change (a):** let the operator type freely — hold the raw input
string locally so intermediate values (`1`, `1.`) display, and commit
to `setManualOdds` when the parsed value is a valid price (`> 1`).
Do not lose the keystroke. The `>1` rule still governs what is
*committed*, not what can be *typed*.
**Change (b):** add an `onKeyDown` on the same input so the keyboard
**Delete** (and Backspace-to-empty) clears the box — clears the
manual odds for that runner (`setManualOdds(selectionId, 0)` / removes
the entry) when the field is emptied via Delete.
**Anchor file:** `OddsTable.tsx` (+ `OddsTable.module.css` only if a
focus style is needed).

### §5.3 — Place Lay & Log flow (the v2 rebuild) — the substantial item

This rebuilds the lay→log handoff to mirror v2's proven
`handlePlaceAndLog`. Four parts; all are frontend state/flow only.

**Anchors:** `HedgeModal.tsx` (the modal), `Racing.tsx` (the
orchestrator — `handleQuickLay`, the `HedgeModal` `onPlaced`,
`handleLogged`, the `LogBetPanel` props), `LogBetPanel.tsx` (the
soft-book log).

**(a) Freeze on placement — stop the post-placement drift.**
Today the modal's `livePricesQuery` keeps polling Betfair every
`HEDGE_MODAL_POLL_MS` (500 ms) *after* placement, so the partial-fill
line's denominator (`laySize`) and `%` keep recomputing off a moving
price — a settled bet looks like it is still moving. **Fix:** once
`response != null`, disable the poll (`refetchInterval: false` / stop
the query) and compute the result line ONLY from the frozen placement
`response` (`matched_size`, `size_remaining`), never from the live
`laySize`. The displayed matched/unmatched figures must not change
after placement.

**(b) Honest frozen result.**
- Full match (`size_remaining` ≈ 0) → green "Matched in full — $0
  unmatched."
- Partial (`size_remaining > threshold`) → "Matched $X — $Y still
  unmatched on Betfair," with `$Y` (the real exposure) **held still
  and visually called out** (amber/red). No moving denominator.

**(c) Persistence auto-set by race code.**
v2 sets PERSIST/LAPSE by Thoroughbred/Harness/Greyhound (greyhounds
have no Betfair in-play, so the remainder cannot persist). **Fix:**
derive the persistence default from the race code (the modal already
has `catalogue.event_type_name` / sport+code context) — PERSIST for
thoroughbred + harness, LAPSE for greyhound — instead of the static
`PERSIST` default. The operator can still override via the existing
dropdown. Where the code cannot be determined, default to the safe
existing behaviour and surface it.

**(d) Hand straight into the soft-book log.**
On placement, the modal stops polling, shows the frozen result, then
**auto-closes** and lands the operator in the `LogBetPanel` (the
runner is already set via the existing `onPlaced` →
`setSelectedRunner`). The matched/unmatched result is **lifted to
`Racing.tsx`** and rendered as a **banner above the log panel that
stays visible the whole time the operator logs the soft-book leg**
(v2's floating-banner behaviour) — not a 1-second flash. The banner
clears on the next lay or next successful log.

**(e) Free-bet handoff — preserve the cycle link; handle empty
inventory gracefully.**

When the lay was placed in **free-bet mode** (`mode === 'free_bet'`),
the handoff must land the `LogBetPanel` in free-bet mode
(`isFreeBet = true`) so the FB inventory picker is shown and the
operator is prompted to select the triggered free bet. This is what
makes the deployment **consume the correct credit AND inherit the
qualifier's cycle** (server-side: `log_bet` → `resolve_inherited_cycle`
on `consumed_credit_event_ids` when `cycle_id` is None).

Three hard requirements:
1. **The soft-book free-bet log must NOT pass a `cycle_id`.** The
   existing `postLogBet` body already omits `cycle_id` — keep it that
   way. Passing one (e.g. the hedge lay's) would suppress the
   qualifier-cycle inheritance and break the link. Do not add a
   `cycle_id` to the free-bet log path.
2. **Pre-select only on an unambiguous match.** Once the operator
   picks the soft-book account+book, if exactly one inventory free bet
   matches the deployed face value, pre-tick it; otherwise leave the
   selection to the operator. Never auto-consume.
3. **Empty inventory must not trap or mislead.** If the operator is in
   free-bet mode but the FB inventory is empty (the qualifier has not
   been settled/credited yet — see "OUT OF SCOPE" below), the panel
   must (i) NOT hard-trap the operator with no path forward, and (ii)
   NOT let a free-bet deployment be silently logged as a plain cash
   bet. Show a clear inline message — e.g. "No free bet booked in at
   this account-at-book yet; settle the qualifier first or log as a
   plain bet deliberately." The operator chooses; nothing is consumed
   or mislinked silently.

**Explicitly OUT OF SCOPE (separate piece — do NOT build here):** the
"deploy a free bet before its qualifier is settled" capability (the
provisional/IOU credit). That is a backend credit-in/settlement design
question routed to the settlement-worker piece. This brief only makes
the empty-inventory case *graceful*, per (3).

### §5.4 — Log box drops and closes on successful log

**Symptom:** after a successful soft-book log the panel stays open with
the runner still selected and stake cleared, so `canSubmit()` shows
"Stake required" next to Log/Clear.
**Anchor:** `Racing.tsx` `handleLogged` (currently only invalidates the
log-context query) + the `LogBetPanel` `onLogged` flow.
**Change:** on a successful log, after the green success message shows
briefly, **drop the log box** — set `selectedRunner` to `null` in
`Racing.tsx` (this nulls the panel back to "Select a runner," i.e. the
box clears and closes back to the race screen). Sequence: show the
green success message (§5.5) for a short beat, then close.
**Hard requirement — preserve race + typed odds:** `manualOdds` and
`selectedMarket` must NOT be touched on log success. The current race
stays; the operator's typed soft odds in the column persist. (Today
`manualOdds` resets only on a *market* change — keep it that way.)

### §5.5 — Clean success message

**Anchor:** `LogBetPanel.tsx` `submit()` — `setSuccess(\`Logged ${result.bet_id} ✓\`)`.
**Change:** replace with a plain green **"Bet logged successfully"**
(drop the raw bet-id). Ensure it renders green (the `successMsg` style;
confirm/adjust in `LogBetPanel.module.css`).

### §5.6 — Drop the Free Bet return-type selector

**Anchor:** `PromoBar.tsx` — the `return type` `<select>` rendered
inside the `config.promo_type && (...)` block.
**Change:** hide the return-type selector when the built-in Free Bet
pick is active (`config.promo_type === 'free_bet'`) — a free bet
always returns cash, so the choice is redundant and confusing there.
Leave it visible for insurance / bonus-winnings (where return type is
a real choice).

### §5.7 — Free-bet quick-amount buttons (top-primary, modal-fallback)

**Symptom / want:** quick buttons for common free-bet face values
(\$25 / \$50 / \$100) plus a free-entry box.
**Primary location — top of the race page (`PromoBar.tsx`):** when the
Free Bet pick is active, show \$25 / \$50 / \$100 quick buttons + a
free-entry amount input. This sets the FB face value up front.
**Fallback — the lay modal (`HedgeModal.tsx`):** the modal's existing
"FB face value" field shows the same quick buttons **only when no
amount was set up top**; when an amount was set up top, the modal
pre-fills from it (the existing `initialBackStake` path carries it).
So the operator sets it once — up top by default, in the modal only if
they skipped it.

## §6 — Sequencing within session

Suggested order (Code may reorder if cleaner, noting why):
1. The independent small fixes first — §5.1 (nav), §5.2 (odds input),
   §5.5 (success text), §5.6 (return-type) — low-risk, isolated.
2. §5.7 (free-bet amount, top + modal fallback) — touches PromoBar +
   HedgeModal.
3. §5.3 + §5.4 last — the lay→log flow rebuild + the on-success close,
   since they are the most interconnected (HedgeModal + Racing +
   LogBetPanel) and benefit from the rest being stable first.

If the work does not fit one clean Code session, that is a **finding**
— stop at a coherent point and report, do not push past budget
(partial-but-coherent beats complete-but-lost-coherence).

## §7 — Verification

- `npx tsc -b` clean (no type errors) and `npx vitest run` green across
  the affected component test files (`HedgeModal.test.tsx`,
  `LogBetPanel.test.tsx`, `OddsTable.test.tsx`, `PromoBar.test.tsx`,
  `Racing.picker.test.tsx`, `App.test.tsx`). Net test delta reported.
- Add/extend tests for the behavioural changes: the odds input accepts
  a typed "1.x", Delete clears a box, the modal freezes the result on
  placement (no post-placement recompute), the free-bet handoff lands
  the panel in free-bet mode and does NOT pass a `cycle_id`, the
  log-success path nulls `selectedRunner` while leaving `manualOdds`
  intact.
- **No Python suite change is expected** (frontend-only). Confirm the
  Python settlement seam is untouched by construction (no backend file
  edited) rather than by re-hashing — but if any backend file *is*
  touched, that is a hard-limit breach (see §9), stop and report.

## §8 — Output spec

Single report at `interface_triage/consolidated_frontend_fix_report.md`
(rebuild root). Sections: run header (HEAD, dirty state, files
touched); per-fix outcome (§5.1–§5.7, what changed + the anchor);
test delta (tsc + vitest before/after); findings (surprises, incl. the
§5.1 "freeze" check and any empty-inventory UX decisions); a
self-assessment of what could not be verified in-session (e.g. live
Betfair partial-fill behaviour). Rough length 150–280 lines. **No**
recommendations for follow-on work and **no** scope creep into the
out-of-scope items.

## §9 — Hard limits (non-negotiable)

- **Frontend only.** Edit only files under `bethub-v3/ui/web/src` (+ the
  named `.module.css`). No backend file (`ui/api`, `workflows`,
  `domain`, `store`, `clients`, `migrations`) is touched. No schema, no
  migration, no API-contract change.
- **No settlement / money-path / credit-in / consume logic change.**
  The free-bet consume + qualifier-cycle inheritance is EXISTING
  backend behaviour — used, never modified. The §5.3(e) work is
  frontend state only.
- **The lay-placement bet-safety rules in `HedgeModal` are preserved
  verbatim** — explicit stake + price (never a profit-target order
  type), the liability soft-cap + tick-divergence confirm guard. None
  of these are weakened by the freeze/flow changes.
- **Deploy-before-settle / IOU credit is OUT** — separate piece. §5.3(e)
  only makes empty inventory graceful.
- **Untracked frontend + dirty tree:** `ui/web/src` is untracked in git.
  Do **not** run `git add` (it would stage the whole src tree), commit,
  stash, restore, checkout, or reset. Verify changes by file read +
  the test suite, not `git diff`. Leave git state as found (HEAD
  `2329604`, ~69 dirty, `?? ui/web/src/`). Edit only the named anchors.
- **No operator escalation mid-session.** Surprises → findings.

## §10 — What happens after Code's session

The next operator-Claude (Chat) session reads
`consolidated_frontend_fix_report.md`, triages it (inventory pass:
every fix landed? any finding with operational/usability impact? the
free-bet handoff's no-`cycle_id` rule honoured? §5.1 "freeze" actually
a sticky issue?), surfaces the operator-relevant items, and routes on
to the next pre-cutover queue item. Code does not write the next brief.

## §11 — Cross-references

- **Stream:** interface-refinement (pre-cutover).
- **DR-033** (data-source roles — Betfair operational/settlement;
  placings manual): unaffected; this is UI only.
- **DR-030** (module boundaries): respected — frontend components only.
- **Built free-bet machinery used, not modified:** promo-attach
  Build 1/2 (`promo_template_id` on the bet; credit-in / consume;
  `resolve_inherited_cycle` qualifier-cycle inheritance).
- **Excluded / routed elsewhere:** Log Past Bet (→ launcher capture-data
  provisioning brief); empty promo buttons (→ promo-seed item);
  deploy-before-settle / IOU free bet (→ settlement-worker piece,
  parking-lot).
