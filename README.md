Dear Stripe 

Removal of Bank Details
On July 18, 2025, at 8:23 PM, I requested that you remove my bank details from your system. To date, this request remains unfulfilled. Please delete all of my banking information from Stripe’s records without further delay.

Account Closure
As of today, July 19, 2025, I hereby declare my intention to close my Stripe account, effective immediately. Despite having asked on at least four separate occasions for Stripe to close my account, no action has been taken.

GDPR Data Request
Under Article 15 of the General Data Protection Regulation (GDPR), I request that you provide me with all personal data you hold concerning my account, including transaction histories and any other related information, in a machine‑readable format.

Unjust Charges and Breach of Contract
You have charged my account for services that were never delivered. My numerous attempts to resolve these discrepancies have met with unsatisfactory responses. Retaining my funds under these circumstances is unacceptable and may constitute criminal misconduct.

Operational Failures
I was informed that funds could not be released to pay my wholesaler until the transactions were “fully reconciled.” Frankly, this policy is arbitrary. Had this been a genuine emergency affecting real customers, your failure to expedite the process would have left them without goods—an egregious breach of contract.July 19, 2025

Subject: Closure of Stripe Account & Data Request

To Whom It May Concern,

As of today, July 19, 2025, I hereby declare my intention to close my Stripe account, effective immediately. I have repeatedly requested—on at least four separate occasions—that Stripe close my account and provide me with all personal data you hold, in accordance with my rights under GDPR Article 15.

These requests follow the fact that Stripe has charged my account for services that were never delivered, and despite my multiple attempts to resolve this, no satisfactory recourse or product has been provided. I regard Stripe’s continued retention of my funds and refusal to honor my data requests as unacceptable and believe these actions may constitute criminal misconduct.

Please process this account closure without further delay and deliver to me, in machine‐readable form, all personal data and transaction records associated with my account. I will be publishing this statement and all relevant correspondence on GitHub to document my experience and inform others of my efforts.

Sincerely,
Martin Newbold

I was told that I couldn’t release the funds to pay the wholesaler until they had been fully reconciled. Frankly, that’s preposterous and feels utterly arbitrary. If this had been a genuine emergency affecting real customers, you wouldn’t have aided the process, and they’d have been left without goods—effectively a breach of contract.

🦡 Badger Orders – Printful Order API (Flask)
--------------------------------------------------------------------------
This is a lightweight Python Flask API designed to handle print-on-demand orders (like T-shirts) via the Printful API. It integrates seamlessly with a custom frontend (e.g., a WordPress HTML form).

✅ Key Features
Order Submission:
Defines a /submit-order POST endpoint that creates a Stripe Checkout session with order details including product, size, quantity, and customer information.

✅ Stripe Payment Integration:
Returns the Stripe payment session URL to the frontend for redirection, enabling smooth payment processing.

✅ Webhook Listener:
Implements a /webhook endpoint to listen for Stripe payment completion events (checkout.session.completed). This moves the puchase money to the Link bank account to enable  funds to purchase Printful order fulfillment it required Stripe eent to trigger this webhook on completion of the purchase  othersies n fulfilment of the ordder will take places.

✅ Product Data Fetching:
Provides routes to fetch product data directly from the Printful API.

✅ Static File Serving:
Serves frontend static files to support the user interface.

--------------------------------------------------------------------------

What the Backend Does Currently:

✔ Creates a Stripe Checkout payment page link upon order submission.

✔ Returns this payment link to the frontend for customer redirection.

✔ Listens to Stripe webhook events to confirm payment success.

✔ Does not yet automatically submit orders to Printful or handle payments from Stripe to Printful.

✔ Printful order submission needs to be triggered manually or added programmatically in the webhook handler after payment success.

✔ Limits the number of purchase quatity depending on the capatital avaiable to it from the Linked Stripe Bank acount 

✅ Environment Variables Used
Key	Description
BACKEND_URL	Your backend base URL
DESTINATION_STRIPE_LINKED_ACCT_	Stripe connected account ID (e.g., Revolut account)
MAX_DAILY_SPEND	Daily spend limit (e.g., 600)
MERCHANT_EMAIL	Your merchant email
PRINTFUL_API_KEY	API key from Printful
STRIPE_PUBLISHABLE_KEY	Your Stripe publishable key
STRIPE_SECRET_KEY	Your Stripe secret key (account)

--------------------------------------------------------------------------

✅ How It Works End-to-End

✔ Customer submits an order on the frontend.

✔ Backend creates a Stripe checkout session and sends the payment URL back.

✔ Customer completes payment on Stripe.

✔ Stripe sends a webhook event to your backend confirming payment.

✔ You then trigger the Printful order submission manually or automate it in the webhook.

✔ Optionally, you transfer funds to your connected Revolut Stripe account after payment.

✅ API Endpoints Overview
Endpoint	Purpose
/test-api	Test connection to Printful API
/get-product-details/<product_id>	Get details for a specific product
/submit-order	Submit an order (accepts JSON POST payload)
/debug-env	Debug endpoint to check environment variables


✅ Now has complete and corrected /submit-order route, with your fallback logic properly embedded — and no steps skipped.

✔You’ll have:

✔CORS and OPTIONS handling

✔Variant + fallback + fallback-to-original-variant retry

✔Stripe checkout logic

✔Proper error handling


--------------------------------------------------------------------------

Deployment & Demo
Ready to deploy on any Python-compatible hosting service such as Render or Replit.

✔ Live demo available at: (https://badger-orders.onrender.com/admin/login)

✔ Support & Contributions
If you find this project useful as a small-scale commerce solution, please consider supporting my social welfare efforts through my crowdfunding page:
JustGiving – Stealing of Emily https://www.justgiving.com/crowdfunding/stealing-of-emily




