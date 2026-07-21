# B3 — LAY Bet Money-Path Investigation Report

**Target:** bethub-v3 @ HEAD `e2638fa` (`ui: blank cash-mode back-stake pre-fill; stop piping soft odds into stake (S210)`)
**Mode:** READ-ONLY investigation. No file edited, no test changed, no design locked, no flag flipped, no git write, no place/settle/reconcile/money-move. `BETHUB_SETTLEMENT_WORKER` left OFF. DR-021 Adelaide anchors.
**Author:** investigation pass, 2026-07-05 (Adelaide).

---

## 0. Status & method (READ THIS FIRST — partial due to an environment blocker)

This report is **substantially complete on the placement→match-state→reconciliation chain** (verified first-hand against the committed source) and **corroborated by live logs**, but **four items could not be verified first-hand** because macOS TCC (Privacy & Security → Files and Folders / Full Disk Access) access to `~/Desktop` was **revoked mid-session**. After the revocation, the entire project subtree `~/Desktop/Projects/bethub-v3/**` — including source, `.git`, and the `data/` operational DB — returns `Operation not permitted` to both the file reader and the shell (and `git`, whose `.git` lives under the blocked path). `~/.claude/**` and `/tmp`/`~` logs remain readable, which is how the live-log corroboration below was still possible.

**Confidence tiers used below:**
- **[CONFIRMED]** — read first-hand from the committed/working source during this session (before the access loss), file:line verified.
- **[CORROBORATED]** — supported by live runtime logs (`~/bethub-live.log` = v3; `/tmp/bethub-flask.log` = v2 `betfair_sync`, an independent oracle on the same Betfair account).
- **[GAP — needs access restore]** — could not be read first-hand; stated as inference with the exact artifact that must be re-read to close it.

**To close the gaps:** re-grant the terminal/host app Full Disk Access (or Files-and-Folders → Desktop) in System Settings, then re-read `workflows/bet_entry/v1/settlement.py`, `workflows/bet_entry/v1/betfair_adapter.py`, `ui/api/settlement_worker.py` (untracked), and run one `mode=ro` triage query against `data/*.db`.

---

## 1. The confirmed mechanics (the three leads)

### L1 — Unmatched lay is written TERMINALLY as `FINAL_PARTIAL`, and the reconciliation sweep never revisits it. **[CONFIRMED]**

`place_lay` (`ui/api/routers/racing.py:1014`) writes the hedge record's match status as:

```
match_status=(
    MatchStatus.FINAL_FULL
    if remaining <= Decimal("0")
    else MatchStatus.FINAL_PARTIAL
),          # racing.py:1105-1109
matched_stake=matched_size,   # racing.py:1103  (== placement.initial_size_matched)
```

`matched_size = Decimal(str(placement.initial_size_matched))` and `remaining = Decimal(str(placement.size_remaining))` (racing.py:1085-1086). There is **no PROVISIONAL / PROVISIONAL_PENDING / UNMATCHED branch**. Therefore a lay that is **fully unmatched at placement** (`initial_size_matched == 0`, `remaining == requested`) falls into the `else` and is stored as **`FINAL_PARTIAL` with `matched_stake = 0`** — a *terminal* label carrying a *zero* matched stake.

The record is persisted with `settlement_state = PENDING` **always** (hedge builder stamps it unconditionally — `workflows/bet_entry/v1/record_builder.py:348`, per the map from the entry-path survey), so the row **is** eligible for settlement even though it bypassed the orchestrator.

The reconciliation worker only ever sweeps two statuses:

```
candidate_rows = storage.list_unreconciled_bets(
    statuses=(
        MatchStatus.PROVISIONAL.value,
        MatchStatus.PROVISIONAL_PENDING.value,
    ),
    ...
)          # workflows/bet_entry/v1/reconciliation.py:416-423
```

`FINAL_PARTIAL` is **not** in that tuple. **Consequence:** once a lay is written `FINAL_PARTIAL`, `run_reconciliation_pass` will never select it again, so if Betfair later matches the lay, the store's `matched_stake` **stays frozen at its placement value (0)** forever. **L1 is confirmed exactly as hypothesized.**

### L2 — Settlement selects on `settlement_state` only, with no match-status gate. **[CONFIRMED]**

`list_unsettled_bets` builds its predicate purely from `settlement_state`:

```
where = f"bets.settlement_state IN ({placeholders})"          # store/repositories/bets.py:838
if older_than_event_start is not None:
    where += " AND l.betfair_event_start_time < ?"            # bets.py:839-841
sql = f"SELECT bets.* FROM bets {join} WHERE {where} ORDER BY ... LIMIT ?"   # bets.py:842-845
```

Default `settlement_states=("pending",)` (bets.py:826); the provisional variant uses `("provisional",)` (bets.py:864-872). **There is no `match_status` column in the WHERE clause.** So a `FINAL_PARTIAL`/`matched_stake=0` lay with `settlement_state=PENDING` is fully eligible to be settled, using whatever `matched_stake` currently sits in the row (0). **L2 confirmed:** settlement is blind to whether the match state is trustworthy/reconciled.

### L3 — The resolver's absent-from-orders path trusts the STALE stored `matched_stake`. **[CONFIRMED]**

In `_resolve_one` (`workflows/bet_entry/v1/reconciliation.py:147`), only the **in-orders** branch uses live data:

```
# Step 3 — in-orders fully matched (LIVE snapshot)
if snap.matched_size > Decimal("0") and snap.average_matched_price is not None:
    return ... FINAL_FULL, matched_stake=snap.matched_size ...   # reconciliation.py:251-265
```

Every **absent-from-orders** branch (entered when the order is no longer in `listCurrentOrders`, i.e. matched-then-cleared or lapsed) reads the **record's stored** stake, not a live value:

- Pre-settlement, `record.matched_stake > 0` → `FINAL_FULL` with `matched_stake=record.matched_stake` (reconciliation.py:284-296).
- Pre-settlement, `record.matched_stake == 0` → **`FAILED`**, `matched_stake=0`, `unmatched_stake=record.requested_stake` (reconciliation.py:297-307).
- Post-settlement clean, `record.matched_stake > 0` → `FINAL_FULL` (reconciliation.py:341-356).
- Post-settlement, `record.matched_stake == 0` → **`FAILED`** (reconciliation.py:358-377).

**Consequence:** for a lay that matched on Betfair *after* placement and has since cleared out of currentOrders, the resolver never sees `snap.matched_size`; it trusts `record.matched_stake` (0), and resolves the bet to **`FAILED`** — still $0, and now also *mislabeled failed*. **L3 confirmed.** This is the reason a naïve "just broaden the sweep to include FINAL_PARTIAL" fix does not work and can make things worse (see §5.2).

**Extension beyond the lead:** L1 and L3 are **coupled**. As written, L3 is *dormant* for the quick-lay path because L1 keeps those bets out of the sweep entirely. The moment L1 is "fixed" by feeding these bets into reconciliation (broaden sweep or re-label to PROVISIONAL), L3 activates and can convert a silent $0 into a `FAILED` mislabel unless L3 is hardened at the same time.

---

## 2. Every lay-creating entry path and what it writes

Enums (`domain/bets/__init__.py`): `MatchStatus` = {`FINAL_FULL`, `FINAL_PARTIAL`, `PROVISIONAL`, `PROVISIONAL_PENDING`, `FAILED`} (:91-104) — **there is no `MATCHED`/`UNMATCHED` value**; `SettlementState` = {`PENDING`, `SETTLED_WON`, `SETTLED_LOST`, `VOIDED`, `PROVISIONAL`} (:107-121). `BetSideTag` = {`BACK`, `LAY`} (:149-161); `Construction.LAY_AGAINST_BACK` (:164-173). *(These lines read first-hand by the entry-path survey before the access loss.)*

| # | Path | Entry point | Side | `match_status` written | `matched_stake` written | `settlement_state` | Reconciled later? |
|---|------|-------------|------|------------------------|--------------------------|--------------------|-------------------|
| **A** | **Quick-lay HTTP route** | `POST /v1/racing/lay` → `place_lay` (`racing.py:1014`) | LAY (Construction.LAY_AGAINST_BACK, racing.py:1116) | `FINAL_FULL` if `remaining<=0` else **`FINAL_PARTIAL`** (racing.py:1105-1109) — *terminal, even when 0 matched* | `initial_size_matched` (racing.py:1103) — **frozen at placement** | `PENDING` always (record_builder.py:348) | **NO** — `FINAL_PARTIAL`/`FINAL_FULL` not in sweep (reconciliation.py:416-423) |
| **B** | **Orchestrator hedge entry** (async) | `workflows/bet_entry/v1/orchestrator.py` (`_hedge_inputs_from` ~:1372) | LAY or BACK | **`PROVISIONAL`** at create (orchestrator.py:1392); later rewritten by `_map_order_state_to_match_status` (:1480-1535) to FINAL_FULL / FINAL_PARTIAL / PROVISIONAL_PENDING / FAILED | `initial_size_matched` at create, then updated by reconcile | `PENDING` (builder) | **YES** — starts PROVISIONAL, in sweep set; also inline Trigger-B reconcile |
| **C** | **Manual "log past bet"** | bets router → `build_manual_bet_record` (`record_builder.py:515`) | operator-supplied, may be LAY (:493, written :589) | default `FINAL_FULL` (:483) | `inputs.matched_stake` (:577) | **required terminal** SETTLED_* / VOIDED (:497, validated :531-536) | N/A (settled at entry) |

**The critical asymmetry:** Path B (orchestrator) writes `PROVISIONAL` and therefore *is* reconciled; Path A (quick-lay `/racing/lay`) writes a *terminal* `FINAL_*` and is *never* reconciled. The live incident (§4) came through **Path A**. Soft-book records (`build_soft_book_bet_record`, record_builder.py:359) are always BACK, never LAY, and don't write `settlement_state` — out of scope.

---

## 3. How `matched_stake=0` becomes "$0 money" (the derived-P&L link)

**[CONFIRMED (structure) / GAP (exact formula)]** Settlement lay detection exists at `workflows/bet_entry/v1/settlement.py:572` (`_is_lay_bet(record)`), and balance/liability derivation branches on side at `workflows/balances/v1/balance_derivation.py:164` (`_is_lay(row)`) / `:171` (`_lay_liability(row)`). The exact arithmetic that turns a settled lay's `matched_stake` into a won/lost cash amount lives in `settlement.py` and **could not be re-read first-hand after the access loss**.

The mechanism is nonetheless near-certain: a lay's settled P&L is a function of its **matched** backer stake and price (win → collect backer stake × (1−commission); lose → pay backer stake × (price−1)). With `matched_stake = 0`, **every term in that function is 0**, so the bet settles with the *correct win/loss direction* (driven by the market result, independent of stake) but a **$0 magnitude** — exactly the reported symptom ("settled with the correct result but $0 money").

**This is the one remaining unverified link in the chain** (see §8, gap G1). It is corroborated end-to-end by §4.

---

## 4. Live incident evidence [CORROBORATED]

Two lays were placed via v3's `POST /api/v1/racing/lay` on 2026-07-05. `~/bethub-live.log` is the v3 (FastAPI/uvicorn) process; `/tmp/bethub-flask.log` is v2's `bethub.betfair_sync`, an **independent** settler on the **same Betfair account** (useful as an oracle for what *actually* happened on Betfair).

**v3's settlement worker was ON in this run:** `bethub-live.log:12` — *"Settlement worker opted in (live mode + BETHUB_SETTLEMENT_WORKER on); starting periodic settlement + provisional passes."* (Note: my own investigation kept the flag OFF; this line is from the operator's live run that produced the symptom.)

### Incident bet #1 — `betfair_bet_id=434175139855` — the textbook $0 case
- **v3 placement** `bethub-live.log:102` (15:34:09): `betfair placement confirmed ... bet_id=434175139855 matched=0.0 remaining=4.98` → **placed FULLY UNMATCHED** → Path A writes `FINAL_PARTIAL`, `matched_stake=0`, `settlement_state=PENDING`. `POST /racing/lay 200 OK` (:103).
- **Betfair reality (v2 oracle)** `flask.log:249871` (15:34:43, ~34s later): *"New Betfair bet synced: 434175139855 on '8. Rubbleonthedouble' @ 4.40 (stake 4.98, lay)"* → **the lay matched in full (4.98) on Betfair.**
- **Settled** `flask.log:250076` (15:46:41): *"Auto-settled Betfair bet 434175139855 (BetHub #2128): W (profit=4.98)"* → **the lay WON; correct magnitude ≈ +4.98 (pre-commission).**
- **v3's store:** `matched_stake` never left 0 (Path A terminal label → never reconciled, L1). Settled by v3's live settlement worker → correct direction, **$0 magnitude.** ← the reported symptom, reproduced with real data.

### Incident bet #2 — `betfair_bet_id=434175982101` — partial fill that did NOT mis-value
- **v3 placement** `bethub-live.log:626` (16:03:49): `... bet_id=434175982101 matched=3.08 remaining=3.08` → **partially matched** (requested ≈ 6.16; 3.08 matched, 3.08 open) → Path A writes `FINAL_PARTIAL`, `matched_stake=3.08`.
- **Betfair reality (v2 oracle)** `flask.log:250367` (16:04:44): *"New Betfair bet synced: 434175982101 ... (stake 3.08, lay)"*; settled `flask.log:250584` (16:16:41): *"W (profit=3.08)"* → **only 3.08 ever matched** (the open 3.08 lapsed at market close), settled +3.08.
- **v3's store:** `matched_stake=3.08` happens to **equal reality** → this bet likely settled **correctly**.

**Adversarial takeaway:** the defect is *structural* (no post-placement reconciliation of `matched_stake` for Path A lays), but it only produces *wrong money* when the **open portion later matches on Betfair** (bet #1). Bet #2's open portion lapsed, so its frozen value stayed correct. **Do not assume every `FINAL_PARTIAL` lay is mis-valued** — each must be checked against what actually matched.

---

## 5. Root cause(s) and blast-radius map (options framed — NOT chosen)

### 5.1 Root-cause set

- **PRIMARY:** Path A (`place_lay`, racing.py:1105-1109) assigns a **terminal** match status (`FINAL_PARTIAL`) with a **frozen** `matched_stake` to lays that are not fully matched at placement, and **nothing ever revisits them** (reconciliation sweep excludes terminal statuses, reconciliation.py:416-423). The store's `matched_stake` cannot track a post-placement Betfair match. This single fact is sufficient to produce the $0 settlement.
- **CONTRIBUTING C1 (L2):** settlement has no match-status/freshness gate (bets.py:838), so it will settle the stale-stake row rather than waiting for (or forcing) a trustworthy matched value.
- **CONTRIBUTING C2 (L3):** the resolver's absent-path trusts stored `matched_stake` (reconciliation.py:284-377), so the "obvious" fix of feeding these bets into reconciliation misfires (→ `FAILED`) unless hardened.
- **CONTRIBUTING C3 (design asymmetry):** Path B writes `PROVISIONAL` and reconciles; Path A does not. The quick-lay route was built as if placement is the final word on match state, which is false for an exchange lay that can match after the placement call returns.

### 5.2 Blast radius of each candidate fix DIRECTION (framed for the operator; none endorsed here)

**Option R1 — Re-label placement status** (write `PROVISIONAL`/`PROVISIONAL_PENDING` instead of `FINAL_PARTIAL` when `remaining > 0` at racing.py:1105-1109).
- *Fixes:* L1 at the source — the bet enters the sweep set.
- *Blast radius / new exposure:* (a) activates **L3** immediately — a matched-then-cleared lay first seen absent-from-orders with stored `matched_stake=0` resolves to `FAILED`; must pair with R4. (b) The bet is now `PROVISIONAL` **and** `settlement_state=PENDING` → settlement (no gate, C1) may settle it *while still provisional* → must pair with R3 or ordering control (§6). (c) UI surfaces (`GET /bets/provisional`, seen live at `bethub-live.log:197`) will now show these lays as provisional. (d) The `FINAL_FULL` (fully matched at placement) branch should stay terminal.

**Option R2 — Broaden the reconciliation sweep** (add `FINAL_PARTIAL` to reconciliation.py:416-423).
- *Fixes:* picks up already-placed `FINAL_PARTIAL` lays without touching the write path.
- *Blast radius / new exposure:* (a) walks **straight into L3** (stale-stake trust) → matched-then-absent lay → `FAILED`, still $0 and now mislabeled. (b) `FINAL_PARTIAL` is a legitimately *terminal* status used by settlement/balance/UI; sweeping it re-opens bets that genuinely finished partial — the code **cannot currently distinguish** "FINAL_PARTIAL = done, matched<requested" from "FINAL_PARTIAL = unmatched mislabel." (c) Re-entrancy: a swept row resolved to `FINAL_FULL` changes `matched_stake` *after* settlement may already have run → retroactive-change / double-count risk (ties to §6).

**Option R3 — Gate settlement on match-status/freshness** (add a predicate to `list_unsettled_bets`/`run_settlement_pass`).
- *Fixes:* C1 / the settle-vs-reconcile race — stops settling un-trustworthy rows.
- *Blast radius / new exposure:* (a) `FINAL_PARTIAL` is *terminal*, so a gate that merely requires "terminal" still lets the stale row through → the gate must key on *reconciliation freshness* (`last_reconciled_at`) or a "verified-matched" marker, not just status. (b) risk of **stalling settlement** for bets that never reconcile (structural anomalies with no `betfair_bet_id`, reconciliation.py:200-213) → bets stuck unsettled. (c) must be coordinated with the provisional settlement pass (`list_provisional_settlement_bets`, bets.py:864).

**Option R4 — Harden the resolver absent-path** (reconciliation.py:284-377 — stop trusting stored `matched_stake`; re-derive true matched size).
- *Fixes:* L3 / C2 — a matched-then-absent lay resolves to `FINAL_FULL` with the *real* matched size.
- *Blast radius / new exposure:* (a) needs a data source for matched size when the order is **absent** from `listCurrentOrders` — the synthesized absent shape has `average_matched_price is None` (reconciliation.py:172-173) and may not carry a matched size at all; likely requires a **new `listClearedOrders` read** (a larger change than a resolver tweak). (b) does nothing on its own unless the bet is actually swept (must pair with R1 or R2). (c) changes the `FAILED`-vs-`FINAL_FULL` classification → risk of flipping genuinely-failed bets the wrong way.

**Cross-cutting conclusion (framed, not decided):** no single option is sufficient. R1/R2 (get the bet reconciled) are **coupled** to R4 (don't mis-resolve it) and to R3/ordering (don't settle it stale). A durable fix is a *coordinated* change across placement-label + sweep + resolver + settlement-gate, plus a backfill (§7). "These fixes are never as simple as they look" is borne out: the visible one-liner (broaden the sweep, R2) is the **most dangerous** option in isolation.

---

## 6. Settle-vs-reconcile ordering & concurrency

**For the incident bet specifically there is no race** — because Path A wrote `FINAL_PARTIAL`, reconciliation never touches it (L1); settlement acts *alone* on a stale `matched_stake=0`. The "race" is latent for **Path B / PROVISIONAL** bets and for **any future state where quick-lay bets are made reconcilable** (Options R1/R2): settlement selects on `settlement_state` only (bets.py:838) while reconciliation selects on `match_status` (reconciliation.py:416-419); the two workers share no ordering guarantee, so a settlement pass can settle a bet before a reconciliation pass has corrected its `matched_stake`, or a reconciliation pass can change `matched_stake` *after* settlement already computed P&L.

**Mechanism options to resolve ordering (framed, not chosen):**
1. **Status/freshness gate on settlement** (R3) — settlement refuses rows that aren't reconciliation-fresh.
2. **Sequenced worker** — run a reconciliation pass immediately before each settlement pass within the same worker tick (relevant to the untracked `settlement_worker.py`, gap G3).
3. **Settle from a live read** — settlement re-reads matched size at settle time instead of trusting the stored value (removes the dependence on reconciliation ordering but adds a Betfair read to the settle path).

**Live-log signal worth noting:** the v3 worker announced *"starting periodic settlement + provisional passes"* (`bethub-live.log:12`) — it names **settlement** and **provisional** passes but **not** a match-status reconciliation pass, and no `reconciliation pass start/finished` lines (reconciliation.py:410/508 emit these) appear anywhere in the v3 log. **Open question G3:** whether the live worker wires `run_reconciliation_pass` at all. If it does not, then *no* worker updates `matched_stake` post-placement in the live config (Path B relies on the orchestrator's inline Trigger-B reconcile, not the periodic worker), which would further explain the frozen value.

---

## 7. Current operational-store state / backfill [GAP — needs access restore]

The `data/*.db` operational store is under the blocked `~/Desktop` subtree and **could not be read** (`mode=ro` query not runnable this session). From the live logs, concrete candidates:

- **`betfair_bet_id=434175139855`** (v2 #2128): **confirmed mis-valued** — placed 0-matched, matched 4.98 on Betfair, won +4.98, v3 froze `matched_stake=0`. Needs backfill of the true matched stake (4.98) and re-derivation of settled P&L.
- **`betfair_bet_id=434175982101`** (v2 #2129): **likely correct** (frozen 3.08 == actual matched 3.08). Illustrates that triage must compare stored vs actually-matched, not blanket-correct all `FINAL_PARTIAL` lays.

**Exact triage query to run once access is restored (read-only):**
```sql
-- enumerate candidate mislabeled/mis-valued lays
SELECT b.bet_id, b.betfair_bet_id, b.side, b.match_status,
       b.matched_stake, b.unmatched_stake, b.requested_stake,
       b.settlement_state
FROM bets b
WHERE b.side = 'LAY'
  AND b.match_status IN ('final_partial')   -- and optionally 'final_full' to audit
ORDER BY b.placed_at;
```
Then cross-check each against Betfair's actual matched size (v2's `betfair_sync` history / `listClearedOrders`) before any backfill. **No write/backfill performed or designed here** — flagged for the operator.

---

## 8. Open questions / gaps requiring restored `~/Desktop` access

- **G1 — settlement P&L formula.** Re-read `workflows/bet_entry/v1/settlement.py` (esp. around `_is_lay_bet:572` and the SETTLED_WON/SETTLED_LOST amount computation) to *verify first-hand* that settled cash scales linearly with `matched_stake` (the last unverified link in §3). Near-certain but not code-confirmed.
- **G2 — resolver absent-path data availability.** Re-read `workflows/bet_entry/v1/betfair_adapter.py` (`get_order_state` and the synthesized absent-from-orders shape) to confirm whether any matched-size signal survives when the order is absent — determines how large R4 must be (resolver tweak vs new `listClearedOrders` read).
- **G3 — live worker wiring.** Read the untracked `ui/api/settlement_worker.py` to confirm whether the live worker runs `run_reconciliation_pass` at all, and the settlement/reconciliation pass ordering within a tick (§6). *(Untracked → not at HEAD; it is part of the in-progress dirty-tree work, consistent with the "settlement worker live-proof" workstream.)*
- **G4 — store enumeration.** Run §7's `mode=ro` query to enumerate actually-affected lays for backfill scoping.

*(Dirty-tree note: `record_builder.py`, `settlement.py`, `betfair_adapter.py`, `clients/betfair_client/v1/settlement.py` and others carry uncommitted modifications — the in-flight settlement-worker/post-settlement-void work. This report is anchored to **HEAD `e2638fa`**; the dirty versions were treated as read-only context and, for the blocked files, could not be diffed this session. When access is restored, confirm whether the dirty changes already move any of the anchors above.)*

---

## 9. Recommended next step (framed for the operator — decision is yours)

1. **Restore Desktop access** (System Settings → Privacy & Security → Full Disk Access / Files-and-Folders → Desktop for the host app), then close **G1–G4** — G1 (settlement math) and G4 (store enumeration) are the two that turn "near-certain" into "proven" and scope the backfill.
2. **Treat the fix as coupled, not a one-liner.** Any change that makes these lays reconcilable (R1 re-label or R2 broaden-sweep) must ship *together with* R4 (resolver absent-path) and a settlement ordering/freshness control (R3 or a sequenced worker), or it risks trading a silent $0 for a `FAILED` mislabel or a settle-vs-reconcile race (§5.2, §6).
3. **Plan a backfill** for confirmed mis-valued lays (§7) as a separate, audited step — `434175139855` is already a confirmed candidate.
4. **Keep `BETHUB_SETTLEMENT_WORKER` OFF** until the coupled fix + backfill are designed and proven. (It was ON in the incident run — `bethub-live.log:12` — which is how the symptom reached money.)

---

### Anchor index (primary)
- `ui/api/routers/racing.py:1014` place_lay; `:1085-1086` matched/remaining; `:1103` matched_stake; `:1105-1109` FINAL_FULL/FINAL_PARTIAL; `:1116` LAY construction; `:1122-1123` persist.
- `workflows/bet_entry/v1/reconciliation.py:416-423` sweep statuses; `:147` `_resolve_one`; `:251-265` in-orders live; `:284-307` pre-settlement stored-stake; `:341-377` post-settlement stored-stake; `:200-213` structural anomaly.
- `store/repositories/bets.py:823-862` list_unsettled_bets; `:838` WHERE (no match gate); `:864-872` provisional variant.
- `domain/bets/__init__.py:91-104` MatchStatus; `:107-121` SettlementState.
- `workflows/bet_entry/v1/record_builder.py:348` settlement_state=PENDING (hedge); `:515` manual builder; `:359` soft-book (BACK).
- `workflows/bet_entry/v1/orchestrator.py:1392` PROVISIONAL at create; `:1480-1535` order-state→status map.
- `workflows/bet_entry/v1/settlement.py:572` `_is_lay_bet`; `workflows/balances/v1/balance_derivation.py:164/171` lay/liability.
- Live: `~/bethub-live.log:12,102-103,626,197`; oracle `/tmp/bethub-flask.log:249871,250076,250367,250584`.

---

## 10. S225 governance-triage addendum — G1–G4 CLOSED first-hand (2026-07-05 ACST)

The four gaps were blocked only by the Code session's host-app TCC revocation on `~/Desktop`. The governance (Claude Code) session retains `~/Desktop` access, so it closed all four by direct read-only reads at HEAD `e2638fa` + a `mode=ro` store query. Report relocated from `/Users/tim/` to `bethub-rebuild/`.

- **G1 — settlement P&L scales linearly with `matched_stake`. [CONFIRMED first-hand.]** `workflows/balances/v1/balance_derivation.py`: `_lay_liability = matched_stake × (matched_price − 1)` (:185-186); lay-won cash return `= liability + matched_stake × (1 − commission)` (:241); lost → 0 net −L; void → L (:229-247). Every term scales with `matched_stake`, so `matched_stake=0` → **every lay figure = $0**. The *direction* (SETTLED_WON/LOST) is set independently by the result resolver's lay inversion (`settlement.py:580-608`, `_winner_terminal_state`/`_loser_terminal_state`), which is why the symptom is "right direction, $0 magnitude." §3's last unverified link is now closed. Note (DR-019): money is derived **on read** from the stored columns — there is no stored P&L to recompute, so a row backfill auto-corrects the money.
- **G2 — no live matched-size signal for an absent order; R4 needs `listClearedOrders`. [CONFIRMED first-hand.]** `betfair_adapter.py::get_order_state` (:214-278) wraps only `list_current_orders`; when the bet-id is absent it **synthesises** `matched_size=original_size, average_matched_price=None, found_in_unmatched=False` (:262-267). The `None` price fails `_resolve_one`'s in-orders test (`reconciliation.py:251`), routing to the absent path that trusts the stale stored stake (L3). The adapter does **no** `listClearedOrders` read. **⇒ R4 (harden the absent-path to recover the true matched size) requires a new cleared-orders Betfair read — a larger change than a resolver tweak, as §5.2/R4 suspected.**
- **G3 — the live periodic worker runs NO reconciliation pass. [CONFIRMED first-hand.]** `ui/api/settlement_worker.py::settlement_worker_cycle` (:68-85) runs only `run_settlement_pass` + `run_provisional_resolution_pass`. `run_reconciliation_pass` is not called anywhere in the worker. So in the live config **nothing periodically reconciles `matched_stake` post-placement** — Path B relies solely on the orchestrator's inline reconcile, and Path A is never reconciled at all. Confirms §6's G3 concern.
- **G4 — store enumeration: exactly ONE mis-valued lay; backfill scope = 1 row. [CONFIRMED first-hand, `mode=ro`.]** `data/bethub.db` holds 3 LAY bets, all `final_partial`/`settled_won`:
  | bet_id | betfair_bet_id | matched_stake | unmatched | requested | matched_price | verdict |
  |---|---|---|---|---|---|---|
  | bet-df31… | 433957436009 (Gossamer, 07-03) | 5.26 | 0 | 5.26 | 3.5 | **correct** (fully matched at placement) |
  | **bet-4287…** | **434175139855 (07-05 15:34)** | **0.0** | 4.98 | 4.98 | **0.0** | **MIS-VALUED** — matched 4.98 @ ~4.40 on Betfair, won; store froze $0 |
  | bet-8b90… | 434175982101 (07-05 16:03) | 3.08 | 0 | 3.08 | 3.15 | **correct** (frozen 3.08 == actually matched) |

  **Only `434175139855` needs backfill:** set `matched_stake=4.98`, `matched_price=4.40` (Betfair actual avg per v2 oracle `flask.log:249871`), `unmatched_stake=0`. Because money is derived on read (DR-019), that single row-correction restores the true settled P&L with no recompute. Backfill is a Cat-4 store write — **designed/executed later, not here.** (`reconciliation_attempts=11` on the Gossamer row vs `1` on the two 07-05 bets is consistent with Path-A lays never being meaningfully reconciled.)

**Net:** all three leads confirmed, the P&L link proven, R4 scoped as the largest sub-part (needs a cleared-orders read), the live worker confirmed to run no reconciliation, and the live-data blast radius bounded to a single mis-valued bet. The fix remains **coupled** (§5.2) and money-path/Cat-4 sensitive → next step is a **design pass**, not a code change. `BETHUB_SETTLEMENT_WORKER` stays OFF.

<!-- INVESTIGATION COMPLETE -->

