from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import stripe
from datetime import date
app = Flask(__name__)
CORS(app)


daily_spend = 0
last_reset = date.today()

MAX_DAILY_SPEND = float(os.getenv("MAX_DAILY_SPEND", "100"))

def reset_daily_spend_if_needed():
    global daily_spend, last_reset
    today = date.today()
    if today != last_reset:
        daily_spend = 0
        last_reset = today


PRINTFUL_API_KEY = os.getenv("PRINTFUL_API_KEY")
PRINTFUL_HEADERS = {
    "Authorization": f"Bearer {PRINTFUL_API_KEY}"
}

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

BACKEND_URL = os.getenv("BACKEND_URL")  # e.g. "https://yourbackend.com/products/"
destination_linked_acct  = os.getenv("DESTINATION_STRIPE_LINKED_ACCT")  # e.g. "https://yourbackend.com/products/"

import traceback

@app.route("/submit-order", methods=["POST"])
def submit_order():
    global daily_spend

    reset_daily_spend_if_needed()

    data = request.json
    quantity = int(data.get("quantity", 1))
    unit_price = 30.0  # Your unit price here, or fetch dynamically

    order_total = unit_price * quantity

    if daily_spend + order_total > MAX_DAILY_SPEND:
        return jsonify({"error": "Daily order limit reached. Please try again tomorrow."}), 429

    # Otherwise, proceed with order creation
    daily_spend += order_total
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

    #
    # Fetch variant details from Printful API for checkout
    #
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
        return jsonify({"error - Failed to open Stripe": str(e)}), 400

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


    
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({"error": "Invalid signature"}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get('metadata', {})
        variant_id = metadata.get('variant_id')
        name = metadata.get('name')
        email = metadata.get('email')
        address = metadata.get('address')
        city = metadata.get('city')
        size = metadata.get('size')
        quantity = int(metadata.get('quantity', 1))

        payment_intent_id = session.get('payment_intent')
        if payment_intent_id:
            try:
                payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

                # Create transfer to connected Revolut account
                transfer = stripe.Transfer.create(
                    amount=payment_intent['amount_received'],
                    currency=payment_intent['currency'],  # fix typo here
                    destination=os.getenv("DESTINATION_LINKED_ACCT"),  # put your connected acct ID here or env var
                    transfer_group=payment_intent['id'],
                )
            except Exception as e:
                print(f"Transfer creation failed: {str(e)}")
                # You can choose to return or continue here

        # Create Printful order (simplified example)
        printful_api_key = os.getenv("PRINTFUL_API_KEY")
        if printful_api_key:
            printful_order_url = "https://api.printful.com/orders"
            headers = {
                "Authorization": f"Bearer {printful_api_key}",
                "Content-Type": "application/json",
            }
            order_payload = {
                "recipient": {
                    "name": name,
                    "address1": address,
                    "city": city,
                    "country_code": "GB",  # adjust as needed
                },
                "items": [{
                    "variant_id": int(variant_id),
                    "quantity": quantity,
                }],
                "options": {
                    "printful": {"store_order_number": payment_intent_id}
                }
            }
            try:
                response = requests.post(printful_order_url, json=order_payload, headers=headers)
                response.raise_for_status()
                print("Printful order created:", response.json())
            except Exception as e:
                print(f"Printful order creation failed: {str(e)}")

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
