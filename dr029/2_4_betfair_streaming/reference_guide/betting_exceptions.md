# Betting Exceptions

**Source PDF:** `1smk3cen4v3lu3yomq5qye0ni-Betting Exceptions-030526-114450.pdf`
**Captured:** between Sessions 65 and 66 (operator browser session)
**Pages:** 2

---

## Page 1

Betting Exceptions
Exceptions
APINGException
This exception is thrown when an operation fails
Error code Description
TOO_MUCH_DATA The operation requested too much data, exceeding the Market Data
Request Limits. You must adjust your request parameters to stay with the
documented limits.
INVALID_INPUT_DATA The data input is invalid. A specific description is returned via
errorDetails as shown below.  Please note: if the number of placeOrders,
updateOrders, replaceOrders, or cancelOrders instructions exceeds the
documented limit you will also receive this error.
INVALID_SESSION_INFORMATIONThe session token hasn't been provided, is invalid or has expired. Login
again to create a new session
NO_APP_KEY An application key header ('X-Application') has not been provided in the
request.
NO_SESSION A session token header ('X-Authentication') has not been provided in the
request
UNEXPECTED_ERROR An unexpected internal error occurred that prevented successful request
processing.
INVALID_APP_KEY The application key passed is invalid or is not present
TOO_MANY_REQUESTS There are too many pending (in-flght) requests e.g. a listMarketBook
with Order/Match projections is limited to 3 concurrent requests. The
error also applies to:
listCurrentOrders, listMarketProfitAndLoss and listClearedOrders if
you have 3 or more requests currently in execution.
placeOrders, cancelOrders./wiki/spaces/BFAPIBETA/pages/1212452,
/wiki/spaces/BFAPIBETA/pages/1212456 if the number of transactions
(instructions) submitted exceeds 1000 in a single second.
For more details relating to this error please see FAQ's
SERVICE_BUSY The service is currently too busy to service this request.
TIMEOUT_ERROR The Internal call to downstream service timed out. Please note: If
a TIMEOUT error occurs on a placeOrders/replaceOrders request, you

## Page 2

should check listCurrentOrders to verify the status of your bets before
placing further orders. Please Note: Timeouts will occur after 5 seconds
of attempting to process the bet but please allow up to 15 seconds for a
timed out order to appear. After this time any unprocessed bets will
automatically be Lapsed and no longer be available on the Exchange.
REQUEST_SIZE_EXCEEDS_LIMIT The request exceeds the request size limit. Requests are limited to a total
of 250 betIdʼs/marketIdʼs (or a combination of both).
ACCESS_DENIED The calling client is not permitted to perform the specific action e.g. they
have an App Key restriction in place or attempting to place a bet from a
restricted jurisdiction.
Other
parameters
Type RequiredDescription Values
errorDetails String the stack trace of the
error
"market id passed is invalid"
"locale must use valid iso-639 locale names"
"currency must use valid iso2 currency code
name"
"country code must use valid iso2 country code
name"
"text query has invalid content"
"language must use valid iso language name"
requestUUIDString
Generic JSON-RPC Exceptions
Error
Code
Description
-32700Invalid JSON was received by the server. An error occurred on the server while parsing the JSON
text.
-32601Method not found
-32602Problem parsing the parameters, or a mandatory parameter was not found
-32603Internal JSON-RPC error
