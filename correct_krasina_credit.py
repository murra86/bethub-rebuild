"""S250 one-off — correct the Krasina FB credit $11 → $12 (round-up fix).

Append-only: writes a corrective free_bet_credited event that
SUPERSEDES the original $11 credit, amount $12.00, payload otherwise
copied verbatim. The W12.1 inventory walk reads the chain terminal, so
the FB becomes $12 and the $11 event is preserved in history. No delete,
no edit. Idempotent: refuses if the original is already superseded.
"""

from decimal import Decimal
from uuid import uuid4

from domain.promos import PromoEventBase, PromoEventSource, PromoEventType
from workflows.promos.v1.promo_store_adapter import PromoStoreAdapter

import sqlite3

ORIG_CREDIT_ID = "f9852c4a-354a-498e-8b24-22ca6d2b36e5"
NEW_AMOUNT = Decimal("12.00")
REASON = (
    "S250 correction — TAB rounds bonus-winnings UP to the whole "
    "dollar; Krasina ($50 @ 1.90 won, $45 winnings, 25% = $11.25) was "
    "credited $11 (half-up) but TAB gave $12. Engine rule fixed to "
    "ROUND_CEILING same session; this trues the one affected credit."
)

conn = sqlite3.connect("data/bethub.db")
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON;")
adapter = PromoStoreAdapter(conn)

from uuid import UUID

orig = adapter.get_event(UUID(ORIG_CREDIT_ID))
print(f"original: {orig.event_type.value} amount={orig.payload.amount} "
      f"source={orig.payload.credit_source.value}")
assert orig.event_type is PromoEventType.FREE_BET_CREDITED
assert orig.payload.amount == Decimal("11.00"), "expected $11 original"

# Refuse if already superseded (idempotent).
already = conn.execute(
    "SELECT event_id FROM promo_events WHERE supersedes_event_id = ?",
    (ORIG_CREDIT_ID,),
).fetchone()
if already:
    print(f"ALREADY corrected by {already['event_id']} — no-op.")
    conn.close()
    raise SystemExit(0)

corrected_payload = orig.payload.model_copy(update={"amount": NEW_AMOUNT})
now = orig.recorded_at  # keep the credit's own timing semantics
from datetime import datetime
from zoneinfo import ZoneInfo
now = datetime.now(ZoneInfo("Australia/Adelaide"))

corrective = PromoEventBase(
    event_id=uuid4(),
    event_type=PromoEventType.FREE_BET_CREDITED,
    recorded_at=now,
    occurred_at=now,
    account_id=orig.account_id,
    book_id=orig.book_id,
    account_at_book_id=orig.account_at_book_id,
    supersedes_event_id=orig.event_id,
    payload=corrected_payload,
    source=PromoEventSource.OPERATOR,
    correlation_id=orig.correlation_id,
    notes=REASON,
)
adapter.append_event(corrective)
conn.commit()
print(f"corrective event {corrective.event_id} written: ${NEW_AMOUNT} "
      f"supersedes {ORIG_CREDIT_ID}")

# Verify inventory now reads $12 on that account-at-book.
from workflows.promos.v1.promo_derivations import compute_free_bet_inventory
inv = compute_free_bet_inventory(conn, orig.account_at_book_id)
krasina_fb = [
    fb for fb in inv.available
    if str(fb.credit_event_id) == str(corrective.event_id)
]
print("inventory terminal for the chain:",
      [(str(fb.credit_event_id)[:8], str(fb.face_value)) for fb in krasina_fb])
conn.close()
