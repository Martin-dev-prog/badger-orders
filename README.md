🦡 Badger Orders – Printful Order API (Flask)


This is a lightweight Python Flask API for submitting print-on-demand orders (e.g. T-shirts) to the Printful API, built for use with a custom front-end such as a WordPress HTML form.
✅ Key Tools
The current Flask backend script does the following relevant things:

Defines /submit-order POST route that creates a Stripe Checkout session with the order details (product name, size, quantity, customer info, etc.).

Returns the Stripe payment session URL to the frontend.

Handles a Stripe webhook endpoint /webhook for listening to payment completions (checkout.session.completed). Here you could add code to trigger Printful order fulfillment (currently a TODO).

Has routes to fetch product data from Printful API and serves static frontend files.

So your backend currently:

Creates a Stripe checkout payment page link on order submit.

Sends that link back to the frontend for redirection.

Listens to webhook events for payment completion but does not yet trigger Printful orders.

Does NOT automatically pay Printful or integrate payment between Stripe and Printful.

You would manually or programmatically place Printful orders in your webhook handler after payment success.



📦 Only After Payment Success Create Printful order via /submit-order
🔧 Features
Accepts JSON POST requests at /submit-order

Sends order data securely to Printful via their API

Ready to deploy on Render, Replit, or any Python-compatible host

Routes "/test-api": "🔧 Check connection to Printful API", "/get-product-details/<product_id>": "📦 Get details of a specific Printful product", "/submit-order": "🛒 Submit an order via POST (requires JSON payload)", "/debug-env": "🧪 (Optional) Debug: See if the PRINTFUL_API_KEY is loaded"

🧪 Live Demo
✅ Try it: https://badger-orders.onrender.com

Submit POST request to:
