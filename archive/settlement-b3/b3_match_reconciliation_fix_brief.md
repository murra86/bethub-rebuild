# B3 match-reconciliation fix brief — SUPERSEDED

**Status:** Superseded 2026-07-05 (S225) — do not action.

This brief proposed "wire the already-built `run_reconciliation_pass` worker, unmodified, and the S224 $0-settle bug is fixed." A read-only verification pass against bethub-v3 @ HEAD `e2638fa` **falsified that premise**:

- The live lay entry `place_lay` (`ui/api/routers/racing.py:~1105-1109`) writes an unmatched lay terminally as `MatchStatus.FINAL_PARTIAL`, but `run_reconciliation_pass` only sweeps `PROVISIONAL`/`PROVISIONAL_PENDING` — so the offending bet is never reconciled. Wiring the worker unmodified does nothing for the bug.
- Settlement is not gated on match-status (races any reconciliation worker); the resolver's absent-from-orders path can mis-resolve a matched-then-absent lay to FAILED off the stale store stake.

The fix is a multi-part money-path correctness problem, not a wiring change. Per operator direction, it goes to a Claude Code **investigation** first (never as simple as it looks).

**→ See `b3_match_reconciliation_investigation_brief.md`** (the read-only investigation commission that replaces this).
