# Brief — Log Past Bet: live-proof + drop-counter floor recalibration

**Status:** DRAFT (S209) — operator-approved before Code hand-off.
**Type:** Surgical fix (one constant) + live verification.
**Origin:** S209 triage of `vps_client_api_rewrite_report.md` (Brief 2).
**Session budget:** single bounded Code session.
**Bet-safety expectation:** CLEAN — read-only verification over the
8400 tunnel + one observability-constant edit. No settlement, money,
lay-placement, capture.db open/copy, or VPS-side change.

## 1. What this brief is and is not

This brief closes the two items the S209 triage held back before
marking Log Past Bet **live-proven** (per the S189 live-integration
taxonomy — green tests are only *implemented-not-live*; live-proven
needs the real duplicate-market resolve end-to-end through the app's
request path on live data).

It commissions Code to:
- (§5.1) run the duplicate-market resolve end-to-end through the
  actual route bridge against the **live** tunnel, proving the
  most-complete-fragment fix in the running request path (not just
  the client-layer smoke Brief 2 already did);
- (§5.2) recalibrate the drop-counter floor to the true empirical
  no-market baseline so the `above_floor` signal becomes meaningful.

It is a single bounded Code session. Surprises become findings in the
report, not blockers or scope expansion. Remediation of anything new
routes back to operator-Claude triage, not Code.

## 2. Why this work exists

Brief 2's report passed all three S209 gate questions: the DR-034
[most-complete-fragment] read-time collapse returns the good fragment
(client-layer live smoke), the transport-failure → 503 wrap holds, and
the F9/F10/rebuild launcher fixes verify. Two items remained:

(a) **Live-proof gap.** Brief 2's happy-path smoke (B1) called
`resolve_race()` directly at the client layer over the real tunnel.
The route bridge was only exercised on the *failure* path (the 503
test, against a dead port). The running request path
(route → client → live tunnel → collapse) was never shown returning
the good fragment on a 200. This brief closes that.

(b) **Drop-counter floor mismatch.** The brief's §5.2/§8 anticipated a
~0.3–1.9% no-market drop rate; live it is ~71–76% — and that is
*correct* (most captured races are greyhound/harness/non-Betfair and
legitimately have no Betfair Win market, dropped per DR-032 / DR-034
stance 3). Code correctly surfaced this rather than re-tuning. The
floor constant is now meaningless (`above_floor` structurally True);
this brief recalibrates it empirically.

**Accepted as-built (NOT re-opened here):** Brief 2's completeness
ordering substitution (finding #1) — the list payload's `state` field
is geographic, not settlement status, so Code ranks fragments by
runner-count → source-breadth → recency instead of settled-first.
Operator-Claude triage accepts this: it satisfies the load-bearing
shell-vs-populated correctness property and the mandatory test. The
rare settled-vs-pending-both-populated edge is a tracked follow-up
(§11), not this brief's job.

## 3. Pre-reads

Required:
- `vps_client_api_rewrite_report.md` — the Brief 2 report (the
  anchors, the worked Emerald example, the findings).
- `vps_client_api_rewrite_brief.md` §5.2, §5.6, §5.7 — the collapse,
  results re-key, and 503-wrap specs this verifies against.

Reference-only (not required reads):
- `vps_endpoint_enrichment_report.md` §2/§4 — the duplicate anatomy
  and the `1.259530858` Emerald worked example.
- DR-034 (`decisions.md`) — the identity / most-complete-fragment
  model.

## 4. System access

- **Read-write (Mac):** exactly one constant — the §5.2 drop-counter
  floor threshold in the v3 repo
  (`/Users/tim/Desktop/Projects/bethub-v3`),
  `clients/vps_client/v1/_lookup_api.py` (the value Brief 2 left at
  the implied ~0.3–1.9% floor). Re-confirm its exact name/line at
  session start before editing (Brief 2 §0 re-anchor pattern).
- **Read-only (live tunnel):** the 8400 racing API, over the
  operator-managed SSH tunnel, for the live resolve (§5.1) and the
  empirical floor measurement (§5.2). GET only.
- **Tunnel must be up.** Operator confirms the 8400 tunnel is live
  before Code starts. If down, Code cannot verify — that is a reported
  finding ("unable to live-verify — tunnel down"), not a failure, and
  the floor edit holds for a re-run.
- **No capture.db** open/copy/mount; **no VPS-side** change. Adelaide
  local timestamps (ACST) per DR-021 throughout the report.

## 5. Substantive scope

### 5.1 — Live in-app resolve through the route bridge

Pick the Brief 2 worked example: the duplicate-market date/venue
`2026-06-29` / `Emerald`, market `1.259530858` (the 3-fragment group —
0-runner PENDING shell + the populated SETTLED fragment).

Drive the resolve **through the actual route bridge** against the
**live** tunnel (the in-process app request path — e.g. `TestClient`
invoking the real FastAPI app with `BETHUB_CAPTURE_API_URL` pointed at
the real 8400 tunnel, NOT a mock and NOT a dead port). Confirm:
- `GET …/bets/lookup/races` for the day lists the Emerald race **once**
  (one logical race, no fragment inflation);
- `GET …/bets/lookup/race` for it returns **200** with the
  most-complete fragment (the populated field, ~13 mappable runners),
  **never** the 0-runner shell;
- one clean single-fragment race (the Brief 2 Albury example, or any
  clean race that day) still resolves 200.

This is the live-proven evidence. A literal click-through in the
launched desktop app is optional/manual (the route returns the
shape-stable models the UI renders) — name it as available but not
required for the report.

### 5.2 — Drop-counter floor recalibration (empirical)

Measure the no-market drop fraction empirically over several recent
captured dates (e.g. the last 7–14 days available over the tunnel),
not a single date — capture the central value and the spread. Set the
floor/band constant to flag **genuine deviation** from the observed
normal (~70–76% central per Brief 2), not the dead ~0.3–1.9% value.
Prefer a band (flag when the fraction falls outside an empirically
grounded normal range) over a single magic number, so the signal
catches a real data regression (a meeting source dropping out, an
enrichment break) without firing on every normal day.

Record in the report: the per-date fractions measured, the chosen
band and its reasoning, and a one-line worked example of the signal
firing vs not. Do **not** change any other §5.2 behaviour — only the
floor/band constant.

## 6. Sequencing within session

1. Re-anchor the §5.2 floor constant (confirm name/line).
2. §5.2 measurement first (it grounds the new band from live data).
3. Set the recalibrated band constant.
4. §5.1 live route-bridge resolve (independent; may run first if the
   tunnel is up and it is more convenient).
5. Re-run the touched test suites; single checkpoint commit after
   green.

Code may reorder where cleaner and says so in the report.

## 7. Empirical verification

- **Live resolve (§5.1):** the route-bridge GET returns 200 + the
  populated fragment on the Emerald duplicate date; the day lists it
  once; a clean race still resolves. Capture the actual responses.
- **Floor (§5.2):** the measured per-date fractions; the new band; a
  demonstration that the signal now reads "normal" on a normal date
  and would read "deviation" on a synthetically abnormal one.
- **Regression:** the touched suites stay green; `ruff` clean on the
  one changed file; full-repo count captured before/after.

## 8. Output spec

Single file:
`/Users/tim/Desktop/Projects/bethub-rebuild/log_past_bet_liveproof_report.md`.
Sections: (1) live route-bridge resolve result (the 200 + populated
fragment, the once-listed day, the clean resolve); (2) floor
recalibration (per-date fractions, chosen band + reasoning, the
fire/no-fire demonstration); (3) test/regression confirmation; (4)
self-assessment (anchor re-confirm, scope adherence, anything odd,
bet-safety statement). ~80–150 lines. **No** recommendations, **no**
re-opening the accepted ordering substitution, **no** scope creep
into the non-migrated surfaces or any settlement/promo/cash-modal
work, **no** VPS-side change.

## 9. Hard limits — what is NOT in scope

- **No re-opening finding #1** (the completeness ordering) — accepted
  as-built; the rare settled-vs-pending edge is a §11 follow-up.
- **No other behaviour change** in `_lookup_api.py` beyond the single
  floor/band constant.
- **The four non-migrated `vps_client` surfaces** (`race_metadata`,
  `runner_metadata`, `bracketing`, `starting_price`,
  `identifier_resolution`) stay dead — flagged follow-up, not touched.
- **The broken `by-market` results route** stays in place, unused.
- **No** capture.db open/copy/mount, schema change, migration,
  settlement/promo/cash-modal/v2/recovery work, VPS-side change, or
  new auth/credential.
- **Single bounded session.** Over-budget → stop and report.

## 10. What happens after Code's session

Next operator-Claude session reads
`log_past_bet_liveproof_report.md` and:
- if the route-bridge resolve returned the populated fragment →
  marks **Log Past Bet live-proven** (S189 taxonomy satisfied);
- confirms the recalibrated floor band is sensible (or routes a small
  adjustment).
Then the queue moves to cash-modal → settlement-worker → promo-seed →
W16. Code does not write the next brief.

## 11. Cross-references

- Triage origin: S209 read of `vps_client_api_rewrite_report.md`
  (findings #1, #2; the live-proof gate).
- Specs verified: `vps_client_api_rewrite_brief.md` §5.2 (collapse +
  drop-counter), §5.6 (results re-key), §5.7 (503 wrap).
- DRs: DR-034 (most-complete-fragment identity), DR-032 (Betfair
  market required to log), DR-033 (analytical/settlement split),
  DR-028 (single integration boundary), DR-021 (Adelaide anchors).
- Tracked follow-ups (excluded here): the settled-vs-pending-both-
  populated ordering edge (results-fetch could land on the pending
  sibling); the four non-migrated surfaces; the broken by-market
  route; tunnel auto-start/health-check.

---

*DRAFT (S209). Locks on operator go-ahead; sha/size recorded in
SESSION_209 at close.*
