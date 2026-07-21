# updateOrders

**Source PDF:** `1smk3cen4v3lu3yomq5qye0ni-updateOrders-030526-114557.pdf`
**Captured:** between Sessions 65 and 66 (operator browser session)
**Pages:** 1

---

## Page 1

updateOrders
Operation
updateOrders
UpdateExecutionReportupdateOrders#updateOrders(StringmarketId , List<
UpdateInstruction >instructions ,StringcustomerRef )throws APINGException
Update non-exposure changing fields
Parameter
name
Type RequiredDescription
marketId String
 The market id these orders are to be
placed on
instructions List<
UpdateInstruction
>
The number of update instructions.  The
limit of update instructions per request is
60
customerRef String Optional parameter allowing the client to
pass a unique string (up to 32 chars) that
is used to de-dupe mistaken re-
submissions.
Return type Description
UpdateExecutionReport
Throws Description
APINGExceptionGeneric exception that is thrown if this operation fails for any reason.
Since 1.0.0
