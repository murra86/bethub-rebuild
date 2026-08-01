# v3 DATA RESET — Runbook (S241, Fri 17 Jul 2026) — OPERATOR-PRESENT ONLY

Scope confirmed by operator S240 (memory 8j): fresh transactional start, accepting ~a
week's data loss over reconciling drift. Saturday's big day runs on the reset store.
**Claude executes each step with the operator watching; a verification gate closes each
step before the next opens. Nothing here runs automatically.**

Precondition (VERIFIED 07:07 today): all 139 bets terminal (86 lost / 52 won / 1 void),
manual queue EMPTY, settlement review clean. VPS capture data is NOT touched by this
reset — capture.db keeps its 98k races.

## What is wiped vs kept (bethub.db)

| WIPE (transactional) | KEEP (setup) |
|---|---|
| bets | accounts |
| bet_legs | accounts_at_book |
| bet_mutation_events | books |
| cash_flow_events | payees |
| promo_events | promo_template (catalogue) |
| promo (instances) | warning_catalogue |

## Steps

1. **App DOWN.** Quit BetHub; confirm `lsof -ti tcp:8787` prints nothing.
2. **Timestamped backup (archive, never destroy).**
   `sqlite3 data/bethub.db ".backup '~/.bethub/backups/bethub-pre-reset-YYYYMMDD-HHMMSS.db'"`
   → `PRAGMA integrity_check` = ok AND `SELECT COUNT(*) FROM bets` = 139 on the copy.
   (Dry-run of exactly this was staged + verified 07:08 today.)
3. **Scoped wipe** (single transaction, FK-safe order):
   `DELETE FROM bet_legs; DELETE FROM bet_mutation_events; DELETE FROM promo_events;
   DELETE FROM cash_flow_events; DELETE FROM promo; DELETE FROM bets;`
   then clear their `sqlite_sequence` rows; `VACUUM`; `PRAGMA integrity_check`.
   **Gate:** wiped tables count 0; kept tables counts unchanged (snapshot counts before).
4. **Relaunch app** (fresh launch also takes its own automatic backup — harmless).
   **Gate:** app up, BetLog empty, accounts/books/pairings all present, promo catalogue
   intact, balances screen shows zeros.
5. **Day-0 re-seed from operator balances (S232 method).** Operator reads out the real
   current balance per account-at-book (incl. any live bonus balances); each is seeded
   as a signed day-0 event on the normal cash-flow door — no direct table writes.
6. **Verify to the cent on the live read path.** The balances screen must equal the
   operator's actual book balances exactly, per account-at-book, including FB inventory.
   Any mismatch: fix via a signed correction event (S232 precedent — derivation doesn't
   filter superseded events), never by editing rows.
7. **Close-out:** record reset completion + seeded totals in the session log; the
   pre-reset backup filename goes in the record. Old data remains fully readable in the
   archive copy forever.

## Aborts

Any gate failure → stop, keep the app down, restore per `ops/RESTORE.md` from the step-2
backup, reconvene. The backup is the whole prior record; nothing is unrecoverable.

## S232 lessons encoded

Never rebuild the served frontend under a running app (no frontend work during reset);
pre-seed bet history double-counts day-0 balances (why the wipe precedes seeding);
seed and verify on the LIVE read path, not synthetic queries.
