# Login & Session Management

**Source PDF:** `1smk3cen4v3lu3yomq5qye0ni-Login & Session Management-030526-114340.pdf`
**Captured:** between Sessions 65 and 66 (operator browser session)
**Pages:** 7

---

## Page 1

Login & Session Management
Home | API Status | Historical Data | Vendor Program | Developer Forum
Login & Session Management
Login | Login Method Summary | Keep Alive | Logout
Login
The Betfair API offers three login flows for developers, depending on the use case for your
application.
All API requests should be sent as POST.
Non-Interactive login
If you are building an application that will run autonomously, there is a separate login flow to
follow to ensure your account remains secure.
Interactive login
If you are building an application that will be used interactively, then this is the flow for you. This
flow has two variants:
Interactive login - Desktop Application
This login flow makes use of Betfair's login pages and allows your app to gracefully handle all
errors and redirections in the same way as the Betfair website. 
Interactive login - API method
This flow makes use of a JSON API endpoint and is the simplest way to get started if you are
looking to create your own login form.
If you're looking for the quickest way to get started, try the curl example in the Interactive
login - API Method.

## Page 2

Login Request Limits
Login Method Summary
Login
Type
Use Case Method Pros Cons Recommendatio
Non-
interactive
Login
Applications
running
autonomously
(e.g., bots).
Non-
interactive
endpoint
with SSL
certificate.
Secure for
automation.
Recommended
for bots.
Requires
certificate
setup.
✅  Use if your app
runs without user
interaction (e.g.,
bots, scheduled
tasks).
Interactive
Login –
API Login
Applications
needing a
simple
integration
with minimal
development
time.
API login
endpoint
(username
+
password,
or
username
+
password
+ 2FA if
enabled).
Easiest to
implement.
Good for most
apps.
Less flexible
for handling
edge cases
compared to
the
embedded
login page.
✅  Use if you wan
quick setup and
donʼt need T&Cs o
jurisdiction
workflows.
Interactive
Login –
Desktop
App
Applications
used
interactively
by a wide
range of users.
Embedded
Betfair
login
pages.
Handles
workflows like
T&Cs updates
and
jurisdiction
checks. More
flexible for 3rd
party apps.
Requires
embedding
Betfairʼs
login page.
More
development
effort
compared to
API login.
✅  Use if your app
is for many users
and must handle
extra workflows
securely.
Keep Alive
You can use Keep-Alive to extend the session timeout period.


## Page 3

On the international (.com) Exchange the current session expiry time is 12 hours for all
customers (excluding UK & Ireland) and 24 hours for UK & Ireland customers.
The session expiry time is currently 20 minutes on the Italian & Spanish Exchange.
You should request Keep Alive within this time to prevent session expiry. If you don't call Keep
Alive within the specified timeout period, the session will expire.
Session times aren't determined or extended based on API activity.
Please note: You can configure the timeout via My Account > Logout Preferences if required
Headers
Name Description Sample
Accept (mandatory) Header that signals that
the response should be
returned as JSON
application/json
X-Authentication (mandatory) Header that represents
the session token that
needs to be keep alive
Session Token
X-Application (optional) Header the Application
Key used by the
customer to identify the
product.
App Key
The presence of the "Accept: application/json" header will signal that the service should
respond with JSON and not an HTML page
URL Definition (Global)
https://identitysso.betfair.com/api/keepAlive
Other Jurisdictions
Please use the below if your country of residence is in one of the list jurisdictions.
Jurisdiction Endpoint
Australia & New Zealand https://identitysso.betfair.au/api/keepAlive
Italy https://identitysso.betfair.it/api/keepAlive

## Page 4

Spain https://identitysso.betfair.es/api/keepAlive
Romania https://identitysso.betfair.ro/api/keepAlive
Parameters
 The Keep-Alive operation requires no parameters.
Response structure
{
  "token":"<token_passed_as_header>",
  "product":"product_passed_as_header",
  "status":"<status>",
  "error":"<error>"
}
Status values
SUCCESS
FAIL
Error values
INPUT_VALIDATION_ERROR
INTERNAL_ERROR
NO_SESSION
Call sample
Request
curl -k -i -H "Accept: application/json"-H "X-Application: AppKey"-
H "X-Authentication: <token>"https://identitysso.betfair.com/api/keepAlive
Response

## Page 5

curl -k -i -H "Accept: application/json"-H "X-Application: AppKey"-
H "X-Authentication: SESSIONTOKEN"https://identitysso.betfair.com/api/keepAlive
{
  "token":"SESSIONTOKEN",
  "product":"AppKey",
  "status":"SUCCESS",
  "error":""
}
Logout
You can use Logout to terminate your existing session.
URL Definition
The presence of the "Accept: application/json" header will signal that the service should
respond with JSON and not an HTML page
Headers
Name Description Sample
Accept (mandatory) Header that signals that
the response should be
returned as JSON
application/json
X-Authentication (mandatory) Header that represents
the session token
created at login.
Session Token
https://identitysso.betfair.com/api/logout

## Page 6

X-Application (optional) Header the Application
Key used by the
customer to identify the
product.
App Key
Response structure
{
  "token":"<token_passed_as_header>",
  "product":"product_passed_as_header",
  "status":"<status>",
  "error":"<error>"
}
Status values
SUCCESS
FAIL
Error values
INPUT_VALIDATION_ERROR
INTERNAL_ERROR
NO_SESSION
Call sample
# full request
curl -k -i -H "Accept: application/json"-H "X-Application: AppKey"-
H "X-Authentication: <token>"https://identitysso.betfair.com/api/logout
Login | Login Method Summary | Keep Alive | Logout

## Page 7


