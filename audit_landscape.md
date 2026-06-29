# Audit landscape

**Purpose:** one place that records every audit / event log v3 has, what
each is for, and how they relate. Written S176 after the operator asked
whether the tool's audit functions should be a single holistic thing or
several separate ones.

**The answer in one line:** v3 uses **one shared event-log pattern,
instantiated as several single-purpose logs**. The holism is in the
shared spine, not in a single mega-table. There is no fragmentation risk
from adding a new single-purpose log *as long as it rides that spine*.

---

## The shared spine (architecture.md §A.2)

Every durable audit/event log in v3 is built from one template: a
**per-domain append-only event log** with a common event header and a
discriminated-union `payload` over per-event-type subclasses. Shared
properties across every instance:

- **Append-only.** Entries are never edited or erased. A correction
  adds a new entry that *supersedes* the old one via
  `supersedes_event_id` — the original stays visible in the chain.
- **Common header.** `event_id`, `event_type`, `recorded_at` (when
  logged) + `occurred_at` (when it happened), scope keys, `payload`
  (JSON), `source`, `correlation_id`, `notes`.
- **Source stamp.** `operator` / `system` / `integration` — who or what
  caused the event.
- **Closed event-type enum + DB CHECK constraint.** New event types
  extend both halves via migration; the table never accepts an unlisted
  type.
- **DR-030 layering.** `domain/<x>` holds the typed event models;
  `store/schema/<x>.py` holds the table DDL + CHECK; `store/repositories/<x>.py`
  is row-only append/read; `workflows/<x>/v1/<x>_store_adapter.py` does
  domain<->row translation.

The **W14 cash-flow log is the authoritative shipped template** Code
copies for a new instance.

## Durable instances today (all on the spine)

| Log | Domain / table | What it records | Built |
|---|---|---|---|
| Promos | `domain/promos`, `promos` | promo / free-bet lifecycle | W13 |
| Cash flow | `domain/cash_flow`, `cash_flow_events` | money in / out, external payments | W14 / W14.1 |
| Operations | `domain/ops`, `ops_events` | hedge-state classification (DR-025) — was a bet covered off at Betfair, and how that was decided | W15 |

## Joining the family (S176 ->)

- **Bet-mutation log** (S176 brief) — a fourth instance of the spine.
  Records create / edit / delete of a **bet record** (the hand-touches:
  Log Past Bet creates, BetLog edits/deletes), so a change always leaves
  a trail that survives even the deletion. Bet-axis scope (`bet_id` +
  `cycle_id`, DR-032). Built **decoupled** from the bet-write
  transaction — a logging failure can never roll back a real bet write —
  and with **no hard FK to `bets`**, so a deleted bet's trail persists.
  Coverage is **Option A: hand-touches only** (operator call S176);
  system/auto mutations are a nameable future event type, not in v1.

## Separate by design — NOT on the spine

- **Place-time audit sink** (`AuditLogSink` / `MemoryAuditLogSink`,
  `ui/api/dependencies/composition.py`). Audits bet **placement** in the
  live hot path. Memory-only today — it forgets on restart. That
  durability gap is the parked **F8** item. It is *intentionally* a
  different animal from the durable event logs (hot-path, speed-first),
  so it is not folded into the spine, and F8 is **out of scope** for the
  bet-mutation brief.
- **Settlement transitions** currently log to the module logger only
  (`settlement.py`), not a structured table. A persisted-audit extension
  is a possible future spine event type; not the S176 brief.

## The holism answer

"One way of doing audit, several single-purpose logs" is the deliberate
design — v3 chose many single-purpose logs over one mega-log because each
is easier to reason about. Adding the bet-mutation log on the shared
spine *is* the holistic move. The only genuinely separate mechanism is
the hot-path place-time sink (F8), separate for a real reason.
