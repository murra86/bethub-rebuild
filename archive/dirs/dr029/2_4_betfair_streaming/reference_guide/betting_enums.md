# Betting Enums

**Source PDF:** `1smk3cen4v3lu3yomq5qye0ni-Betting Enums-030526-114416.pdf`
**Captured:** between Sessions 65 and 66 (operator browser session)
**Pages:** 17

---

## Page 1

Betting Enums
Enums
MarketProjection
Value Description
COMPETITION If not selected then the competition will not be returned with
marketCatalogue
EVENT If not selected then the event will not be returned with
marketCatalogue
EVENT_TYPE If not selected then the eventType will not be returned with
marketCatalogue
MARKET_START_TIME If not selected then the start time will not be returned with
marketCatalogue
MARKET_DESCRIPTIONIf not selected then the description will not be returned with
marketCatalogue
RUNNER_DESCRIPTIONIf not selected then the runners will not be returned with
marketCatalogue
RUNNER_METADATA If not selected then the runner metadata will not be returned with
marketCatalogue. If selected then RUNNER_DESCRIPTION will
also be returned regardless of whether it is included as a market
projection.
PriceData
Value Description
SP_AVAILABLE Amount available for the BSP auction.

## Page 2

SP_TRADED Amount traded in the BSP auction.
EX_BEST_OFFERSOnly the best prices available for each runner, to requested price depth.
EX_ALL_OFFERSEX_ALL_OFFERS trumps EX_BEST_OFFERS if both settings are present
EX_TRADED Amount traded on the exchange.
MatchProjection
Value Description
NO_ROLLUP No rollup, return raw fragments
ROLLED_UP_BY_PRICE Rollup matched amounts by distinct matched prices per side.
ROLLED_UP_BY_AVG_PRICERollup matched amounts by average matched price per side
OrderProjection
Value Description
ALL EXECUTABLE and EXECUTION_COMPLETE orders
EXECUTABLE An order that has a remaining unmatched portion. This is either a
fully unmatched or partially matched bet (order)
EXECUTION_COMPLETEAn order that does not have any remaining unmatched portion.
 This is a fully matched bet (order).
MarketStatus
Value Description

## Page 3

INACTIVE The market has been created but isn't yet available.
OPEN The market is open for betting.
SUSPENDED The market is suspended and not available for betting.
CLOSED The market has been settled and is no longer available for betting.
RunnerStatus
Value Description
ACTIVE ACTIVE
WINNER WINNER
LOSER LOSER
PLACED The runner was placed, applies to EACH_WAY marketTypes only.
REMOVED_VACANTREMOVED_VACANT applies to Greyhounds. Greyhound markets
always return a fixed number of runners (traps). If a dog has been
removed, the trap is shown as vacant.
REMOVED REMOVED
HIDDEN The selection is hidden from the market.  This occurs in Horse Racing
markets were runners is hidden when it is doesnʼt hold an official entry
following an entry stage. This could be because the horse was never
entered or because they have been scratched from a race at a
declaration stage. All matched customer bet prices are set to 1.0 even
if there are later supplementary stages. Should it appear likely that a
specific runner may actually be supplemented into the race this
runner will be reinstated with all matched customer bets set back to
the original prices.

## Page 4

TimeGranularity
Value Description
DAYS
HOURS
MINUTES
Side
ValueDescription
BACKTo back a team, horse or outcome is to bet on the selection to win. For LINE
markets a Back bet refers to a SELL line. A SELL line will win if the outcome
is LESS THAN the taken line (price)  
LAYTo lay a team, horse, or outcome is to bet on the selection to lose. For LINE markets
a Lay bet refers to a BUY line. A BUY line will win if the outcome is MORE THAN the
taken line (price) 
OrderStatus
Value Description
PENDING An asynchronous order is yet to be processed. Once the bet has
been processed by the exchange 
(including waiting for any in-play delay), the result will be
reported and available on the 
Exchange Stream API and API NG. 
Not a valid search criteria on MarketFilter
EXECUTION_COMPLETEAn order that does not have any remaining unmatched portion.

## Page 5

EXECUTABLE An order that has a remaining unmatched portion.
EXPIRED The order is no longer available for execution due to its time in
force constraint. 
In the case of FILL_OR_KILL orders, this means the order has
been killed because it could not be filled to your specifications. 
Not a valid search criteria on MarketFilter
OrderBy
Value Description
BY_BET @Deprecated Use BY_PLACE_TIME instead. Order by placed time,
then bet id.
BY_MARKET Order by market id, then placed time, then bet id.
BY_MATCH_TIMEOrder by time of last matched fragment (if any), then placed time, then
bet id. Filters out orders which have no matched date. The dateRange
filter (if specified) is applied to the matched date.
BY_PLACE_TIME Order by placed time, then bet id. This is an alias of to be deprecated
BY_BET. The dateRange filter (if specified) is applied to the placed
date.
BY_SETTLED_TIMEOrder by time of last settled fragment (if any due to partial market
settlement), then by last match time, then placed time, then bet id.
Filters out orders which have not been settled. The dateRange filter (if
specified) is applied to the settled date.
BY_VOID_TIME Order by time of last voided fragment (if any), then by last match time,
then placed time, then bet id. Filters out orders which have not been
voided. The dateRange filter (if specified) is applied to the voided date.

## Page 6

SortDir
Value Description
EARLIEST_TO_LATESTOrder from earliest value to latest e.g. lowest betId is first in the
results.
LATEST_TO_EARLIESTOrder from the latest value to the earliest e.g. highest betId is first
in the results.
OrderType
Value Description
LIMIT A normal exchange limit order for immediate execution
LIMIT_ON_CLOSE Limit order for the auction (SP)
MARKET_ON_CLOSE Market order for the auction (SP)
MarketSort
Value Description
MINIMUM_TRADED Minimum traded volume
MAXIMUM_TRADED Maximum traded volume
MINIMUM_AVAILABLE Minimum available to match
MAXIMUM_AVAILABLE Maximum available to match
FIRST_TO_START The closest markets based on their expected start time
LAST_TO_START The most distant markets based on their expected start time

## Page 7

MarketBettingType
Value Description
ODDS Odds Market - Any market that doesn't fit any any of
the below categories.
LINE Line Market - LINE markets operate at even-money
odds of 2.0. However, price for these markets refers to
the line positions available as defined by the markets
min-max range and interval steps. Customers either
Buy a line (LAY bet, winning if outcome is greater than
the taken line (price)) or Sell a line (BACK bet, winning
if outcome is less than the taken line (price)). If settled
outcome equals the taken line, stake is returned. 
RANGE Range Market - Now Deprecated
ASIAN_HANDICAP_DOUBLE_LINEAsian Handicap Market - A traditional Asian handicap
market. Can be identified by marketType
ASIAN_HANDICAP
ASIAN_HANDICAP_SINGLE_LINEAsian Single Line Market - A market in which there can
be 0 or multiple winners. e,.g marketType
TOTAL_GOALS
FIXED_ODDS Sportsbook Odds Market. This type is deprecated and
will be removed in future releases, when Sportsbook
markets will be represented as ODDS market but with
a different product type
ExecutionReportStatus
Value Description

## Page 8

SUCCESS Order processed successfully
FAILURE Order failed.
PROCESSED_WITH_ERRORSThe order itself has been accepted, but at least one
(possibly all) actions have generated errors. This error only
occurs for replaceOrders, cancelOrders and updateOrders
operations.
In normal circumstances the
/wiki/spaces/BFAPIBETA/pages/1212454 operation will not
return PROCESSED_WITH_ERRORS status as it is an atomic
operation.  PLEASE NOTE: if the 'Best Execution' features is
switched off, placeOrders can return
‘PROCESSED_WITH_ERRORSʼ meaning that some bets can
be rejected and other placed when submitted in the same
PlaceInstruction
TIMEOUT The order timed out & the status of the bet is unknown. If
a TIMEOUT error occurs on
a placeOrders/replaceOrders request, you should
check listCurrentOrders to verify the status of your bets
before placing further orders. Please Note: Timeouts will
occur after 5 seconds of attempting to process the bet but
please allow up to 15 seconds for a timed out order to
appear. After this time any unprocessed bets will
automatically be Lapsed and no longer be available on the
Exchange.
ExecutionReportErrorCode
Value Description
ERROR_IN_MATCHER The matcher is not healthy. Please note: The error
will also be returned is you attempt concurrent

## Page 9

'cancel all' bets requests using cancelOrders which
isn't permitted.
PROCESSED_WITH_ERRORS The order itself has been accepted, but at least one
(possibly all) actions have generated errors
BET_ACTION_ERROR There is an error with an action that has caused the
entire order to be rejected. Check the
instructionReports errorCode for the reason for the
rejection of the order.
INVALID_ACCOUNT_STATE Order rejected due to the account's status
(suspended, inactive, dup cards)
INVALID_WALLET_STATUS Order rejected due to the account's wallet's status
INSUFFICIENT_FUNDS Account has exceeded its exposure limit or available
to bet limit
LOSS_LIMIT_EXCEEDED The account has exceed the self imposed loss limit
MARKET_SUSPENDED Market is suspended
MARKET_NOT_OPEN_FOR_BETTINGMarket is not open for betting. It is either not yet
active, suspended or closed awaiting settlement.
DUPLICATE_TRANSACTION Duplicate customer reference data submitted -
Please note: There is a time window associated with
the de-duplication of duplicate submissions which is
60 second
INVALID_ORDER Order cannot be accepted by the matcher due to the
combination of actions. For example, bets being
edited are not on the same market, or order includes
both edits and placement
INVALID_MARKET_ID Market doesn't exist
PERMISSION_DENIED Business rules do not allow order to be placed. You
are either attempting to place the order using a
Delayed Application Key or from a restricted
jurisdiction (i.e. USA)

## Page 10

DUPLICATE_BETIDS Duplicate bet ids found. For example, you've
included the same betId more than once in a single
cancelOrders request.
NO_ACTION_REQUIRED Order hasn't been passed to matcher as system
detected there will be no state change
SERVICE_UNAVAILABLE The requested service is unavailable
REJECTED_BY_REGULATOR The regulator rejected the order. On the Italian
Exchange this error will occur if more than 50 bets
are sent in a single placeOrders request.
NO_CHASING A specific error code that relates to Spanish
Exchange markets only which indicates that the bet
placed contravenes the Spanish regulatory rules
relating to loss chasing.
REGULATOR_IS_NOT_AVAILABLE The underlying regulator service is not available.
TOO_MANY_INSTRUCTIONS The amount of orders exceeded the maximum
amount allowed to be executed
INVALID_MARKET_VERSION The supplied market version is invalid. Max length
allowed for market version is 12.
INVALID_PROFIT_RATIO The order falls outside the permitted price and size
combination.
NO_CHANGE Trying to update the persistence type to the one it
already has.
PersistenceType
Value Description
LAPSE Lapse (cancel) the order automatically when the market is turned
in play if the bet is unmatched

## Page 11

PERSIST Persist the unmatched order to in-play. The bet will be placed
automatically into the in-play market at the start of the event. 
Once in play, the bet won't be cancelled by Betfair if a material
event takes place and will be available until matched or cancelled
by the user
MARKET_ON_CLOSE Put the order into the auction (SP) at turn-in-play
InstructionReportStatus
Value Description
SUCCESSThe instruction was successful.
FAILUREThe instruction failed.
TIMEOUTThe order timed out & the status of the bet is unknown. If a TIMEOUT error
occurs on a placeOrders/replaceOrders request, you should
check listCurrentOrders to verify the status of your bets before placing further
orders. Please Note: Timeouts will occur after 5 seconds of attempting to
process the bet but please allow up to 15 seconds for a timed out order to
appear. After this time any unprocessed bets will automatically be Lapsed and
no longer be available on the Exchange.
InstructionReportErrorCode
Value Description
INVALID_BET_SIZE bet size is invalid for your currency or yo
INVALID_RUNNER Runner does not exist, includes vacant tr
racing

## Page 12

BET_TAKEN_OR_LAPSED Bet cannot be cancelled or modified as i
taken or has been cancelled/lapsed Incl
cancel/modify market on close BSP bets
on close BSP bets. The error may be retu
placeOrders request if for example a bet
point when a market admin event takes p
turned in-play). 
The error will also be returned if a marke
submitted and a material change has tak
bet was submitted causing the bet to be
BET_IN_PROGRESS No result was received from the matche
configured for the system
RUNNER_REMOVED Runner has been removed from the even
MARKET_NOT_OPEN_FOR_BETTING Attempt to edit a bet on a market that ha
LOSS_LIMIT_EXCEEDED The action has caused the account to ex
imposed loss limit
MARKET_NOT_OPEN_FOR_BSP_BETTING Market now closed to bsp betting. Turne
been reconciled
INVALID_PRICE_EDIT Attempt to edit down the price of a bsp l
or edit up the price of a limit on close ba
INVALID_ODDS Odds not on price ladder - either edit or 
INSUFFICIENT_FUNDS Insufficient funds available to cover the 
exposure limit or available to bet limit wo
INVALID_PERSISTENCE_TYPE Invalid persistence type for this market, 
in-play market or KEEP for markets with 
betDelayModels.
ERROR_IN_MATCHER A problem with the matcher prevented th
completing successfully
INVALID_BACK_LAY_COMBINATION The order contains a back and a lay for t
overlapping prices. This would guarantee
also applies to BSP limit on close bets

## Page 13

ERROR_IN_ORDER The action failed because the parent ord
INVALID_BID_TYPE Bid type is mandatory
INVALID_BET_ID Bet for id supplied has not been found
CANCELLED_NOT_PLACED Bet cancelled but replacement bet was n
RELATED_ACTION_FAILED Action failed due to the failure of a action
action is dependent
NO_ACTION_REQUIRED the action does not result in any state ch
persistence to it's current value
TIME_IN_FORCE_CONFLICT You may only specify a time in force on e
request OR on individual limit order instr
since the implied behaviors are incompa
UNEXPECTED_PERSISTENCE_TYPE You have specified a persistence type fo
order, which is nonsensical because no u
can remain after the order has been plac
INVALID_ORDER_TYPE You have specified a time in force of FIL
have included a non-LIMIT order type.
UNEXPECTED_MIN_FILL_SIZE You have specified a minFillSize on a lim
limit order's time in force is not FILL_OR_
Using minFillSize is not supported where
the request (as opposed to an order) is F
INVALID_CUSTOMER_ORDER_REF The supplied customer order reference i
INVALID_MIN_FILL_SIZE The minFillSize must be greater than zer
equal to the order's size. 
The minFillSize cannot be less than the m
your currency
BET_LAPSED_PRICE_IMPROVEMENT_TOO_LARGEYour bet is lapsed. There is better odds t
available in the market, but your 
preferences don't allow the system to m
against better odds. Change your betting
preferences to accept better odds if you
receive this error. Please see

## Page 14

https://support.betfair.com/app/answe
for more details regarding Best Execut
update your settings.
GroupBy
Value Description
EVENT_TYPEA roll up of settled P&L, commission paid and number of bet orders, on a
specified event type
EVENT A roll up of settled P&L, commission paid and number of bet orders, on a
specified event
MARKET A roll up of settled P&L, commission paid and number of bet orders, on a
specified market
SIDE An averaged roll up of settled P&L, and number of bets, on the specified side
of a specified selection within a specified market, that are either settled or
voided
BET The P&L, side and regulatory information etc, about each individual bet order.
BetStatus
Value Description
SETTLED A matched bet that was settled normally

## Page 15

VOIDED A matched bet that was subsequently voided by Betfair, before, during or
after settlement
LAPSED Unmatched bet that was cancelled by Betfair (for example at turn in play).
CANCELLEDUnmatched bet that was cancelled by an explicit customer action.
marketType - Legacy Data
Value Description
A Asian Handicap
L Line market
O Odds market
R Range market.
NOT_APPLICABLE The market does not have an applicable marketType.
TimeInForce
Value Description
FILL_OR_KILLExecute the transaction immediately and completely (filled to size or
between minFillSize and size) or not at all (cancelled).
For LINE markets Volume Weighted Average Price (VWAP) functionality is
disabled
BetTargetType

## Page 16

Value Description
BACKERS_PROFITThe payout requested minus the calculated size at which this
LimitOrder is to be placed. BetTargetType bets are invalid for LINE
markets
PAYOUT The total payout requested on a LimitOrder
PriceLadderType
Value Description
CLASSIC Price ladder increments traditionally used for Odds Markets.
FINEST Price ladder with the finest available increment, traditionally used for 
Asian Handicap markets.
LINE_RANGEPrice ladder used for LINE markets. Refer to MarketLineRangeInfo for more
details.
BetDelayModel
Value Description
PASSIVEFor in-play markets where betDelay > 0, orders that are guaranteed not to
match immediately are accepted straight away, bypassing the bet delay wait.
Order requirements (otherwise bets will be subject to the usual bet delay before
being placed).
Only plain LIMIT orders are supported.
Allowed persistenceType: LAPSE
The following attributes are not supported and must be omitted: timeInForce,
minFillSize, betTargetType

## Page 17

DYNAMICIndicates market is subject to dynamic in-play bet delays. This mean that the
in-play betDelay will vary while the market is turned in-play.
Please note: Currently returned for Tennis markets only. Specifically, every
game 3,5,7,9,11 or game which decides a set (potentially 6,8,10,12) the betDelay
is reduced to 1 second.
