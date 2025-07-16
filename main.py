from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import stripe

app = Flask(__name__)
CORS(app)

PRINTFUL_API_KEY = os.getenv("PRINTFUL_API_KEY")
PRINTFUL_HEADERS = {
    "Authorization": f"Bearer {PRINTFUL_API_KEY}"
}

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

BACKEND_URL = os.getenv("BACKEND_URL")  # e.g. "https://yourbackend.com/products/"
destination_linked_acct_  = os.getenv("DESTINATION_STRIPE_LINKED_ACCT_")  # e.g. "https://yourbackend.com/products/"

app.route("/submit-order", methods=["POST"])
def submit_order():
    data = request.json
    variant_id = data.get("variant_id")
    name = data.get("name")
    email = data.get("email")
    address = data.get("address")
    city = data.get("city")
    quantity = int(data.get("quantity", 1))
    size = data.get("size", "N/A")

    if not variant_id:
        return jsonify({"error": "Missing variant_id"}), 400

    # Fetch variant details from Printful API
    try:
        printful_response = requests.get(
            f"https://api.printful.com/store/variant/{variant_id}",
            headers={"Authorization": f"Bearer {PRINTFUL_API_KEY}"}
        )
        printful_response.raise_for_status()
        variant_info = printful_response.json().get("result")
    except Exception as e:
        return jsonify({"error": f"Failed to fetch variant info: {str(e)}"}), 500

    # Extract price and name from variant_info
    product_name = variant_info.get("product", {}).get("name", "Badger Shirt")
    variant_name = variant_info.get("name", f"Size {size}")
    retail_price = variant_info.get("retail_price", 29.00)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "product_data": {
                        "name": f"{product_name} - {variant_name}",
                    },
                    "unit_amount": int(float(retail_price) * 100),  # amount in pence
                },
                "quantity": quantity,
            }],
            metadata={
                "variant_id": variant_id,
                "name": name,
                "email": email,
                "address": address,
                "city": city,
                "size": size,
            },
            success_url=os.getenv("SUCCESS_URL", "https://yourdomain.com/success"),
            cancel_url=os.getenv("CANCEL_URL", "https://yourdomain.com/cancel"),
        )
        return jsonify({"stripe_link": session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 400



def move_funds_from_stripe():
    try:
        # Retrieve the Stripe balance
        balance = stripe.Balance.retrieve()
        available = balance["available"][0]
        amount = available["amount"] / 100  # Convert from pence to GBP
        currency = available["currency"].upper()

        print(f"✅ Available in Stripe: £{amount:.2f} {currency}")

        # Optional: trigger payout manually (Stripe usually auto-payouts)
        # Uncomment below if you want to control payout manually
        # payout = stripe.Payout.create(
        #     amount=int(amount * 100),
        #     currency=currency.lower(),
        #     method="standard",
        #     statement_descriptor="Badger Order Payout"
        # )
        # print("Payout triggered:", payout)

    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {e.user_message}")
    except Exception as ex:
        print(f"❌ Unexpected error: {ex}")

if __name__ == "__main__":
    move_funds_from_stripe()
@app.route("/")
def api_index():
    return jsonify({
        "✅ Flask API is running": True,
        "Routes": {
            "/test-api": "🔧 Check connection to Printful API",
            "/get-product-details/</get-product-ids>": "📦 Get details of a specific Printful product",
            "/submit-order": "🛒 Submit an order via POST (requires JSON payload)",
            "/debug-env": "🧪 (Optional) Debug: See if the PRINTFUL_API_KEY is loaded"
        }
    })

@app.route('/api/revolut-link')
def get_revolut_link():
    revolut_link = os.getenv("REVOLUT_LINK", "")
    return {"revolut_link": revolut_link}
    
@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")  # Make sure this is set in your environment

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({"error": "Invalid signature"}), 400

    # Handle checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        variant_id = session['metadata'].get('variant_id')
        name = session['metadata'].get('name')
        email = session['metadata'].get('email')
        # TODO: trigger Printful order, store data, notify user, etc.

        # Retrieve the PaymentIntent ID from the session to get payment details
        payment_intent_id = session.get('payment_intent')
        if payment_intent_id:
            try:
                payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

                # Create a transfer to the connected Revolut account
                transfer = stripe.Transfer.create(
                    amount=payment_intent['amount_received'],
                    currency=payment_intent['gdp'],
                    destination= destination_linked_acct_,  # <-- Replace with your Revolut connected account ID on stripe
                    transfer_group=payment_intent['id'],  # payment intent ID string,
                )
            except Exception as e:
                # Log or handle the transfer error accordingly
                print(f"Transfer creation failed: {str(e)}")
                # You may choose to return an error here or continue gracefully

    return jsonify({"status": "success"})
    
@app.route("/test-api")
def test_api():
    response = requests.get("https://api.printful.com/store/products", headers=PRINTFUL_HEADERS)
    return jsonify(response.json()), response.status_code

@app.route("/get-product-details/<product_id>")
def get_product_details(product_id):
    url = f"https://api.printful.com/store/products/{product_id}"
    response = requests.get(url, headers=PRINTFUL_HEADERS)
    return jsonify(response.json()), response.status_code

@app.route("/get-product-ids")
def get_product_ids():
    url = "https://api.printful.com/store/products"
    all_products = []
    offset = 0
    limit = 20  # Printful API default pagination limit

    while True:
        paged_url = f"{url}?limit={limit}&offset={offset}"
        r = requests.get(paged_url, headers=PRINTFUL_HEADERS)
        if r.status_code != 200:
            return jsonify({"error": "Failed to fetch product list", "status_code": r.status_code}), r.status_code
        data = r.json()
        products = data.get("result", [])
        all_products.extend(products)
        if len(products) < limit:
            break  # No more pages
        offset += limit

    ids = [{"id": p["id"], "name": p["name"]} for p in all_products]
    return jsonify(ids)

@app.route("/debug-env")
def debug_env():
    return jsonify({
        "PRINTFUL_API_KEY exists": bool(PRINTFUL_API_KEY)
    })

# -- Static file serving routes added below --

@app.route('/index.html')
def serve_index_html():
    return send_from_directory('static', 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory('static', filename)

# Optional: serve root '/' to index.html
@app.route('/home')
@app.route('/app')
@app.route('/dashboard')
@app.route('/')
def serve_root():
    return send_from_directory('static', 'index.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
