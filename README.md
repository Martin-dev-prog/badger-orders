

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

--------------------------------------------------------------------------

Deployment & Demo
Ready to deploy on any Python-compatible hosting service such as Render or Replit.

✔ Live demo available at: https://badger-orders.onrender.com/

✔ Support & Contributions
If you find this project useful as a small-scale commerce solution, please consider supporting my social welfare efforts through my crowdfunding page:
JustGiving – Stealing of Emily https://www.justgiving.com/crowdfunding/stealing-of-emily




