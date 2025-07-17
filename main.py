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

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

def check_password():
    token = request.args.get("token")
    if token != ADMIN_PASSWORD:
        abort(403, description="Unauthorized")

@app.route("/admin/reset-spend", methods=["POST"])
def reset_spend():
    check_password()
    global daily_spend
    daily_spend = 0
    return jsonify({"status": "✅ Spend reset to 0"})

@app.route("/admin/set-limit", methods=["POST"])
def set_limit():
    check_password()
    try:
        new_limit = float(request.json.get("limit"))
        global MAX_DAILY_SPEND
        MAX_DAILY_SPEND = new_limit
        return jsonify({"status": f"✅ MAX_DAILY_SPEND set to {MAX_DAILY_SPEND}"})
    except Exception as e:
        return jsonify({"error": f"Invalid limit: {str(e)}"}), 400

PRINTFUL_API_KEY = os.getenv("PRINTFUL_API_KEY")
PRINTFUL_HEADERS = {
    "Authorization": f"Bearer {PRINTFUL_API_KEY}"
}

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

BACKEND_URL = os.getenv("BACKEND_URL")  # e.g. "https://yourbackend.com/products/"
destination_linked_acct  = os.getenv("DESTINATION_STRIPE_LINKED_ACCT")  # e.g. "https://yourbackend.com/products/"

import traceback

@app.route("/submit-order", methods=["POST", "GET", "OPTIONS"])
def submit_order():
    if request.method == "OPTIONS":
        return '', 204  # CORS preflight
    if request.method != "POST":
        return jsonify({"error": "This route only accepts POST requests"}), 405

    global daily_spend
    reset_daily_spend_if_needed()

    try:
        data = request.json
        quantity = int(data.get("quantity", 1))
        unit_price = 30.0
        order_total = unit_price * quantity

        if daily_spend + order_total > MAX_DAILY_SPEND:
            return jsonify({"error": "Daily order limit reached. Please try again tomorrow."}), 429

        variant_id = data.get("variant_id")
        name = data.get("name")
        email = data.get("email")
        address = data.get("address")
        city = data.get("city")
        size = data.get("size", "N/A")
        product_id = data.get("product_id", "N/A")

        if variant_id =="UNKNOWN":
          print(f"📦 Checking  ID: {variant_id}")
          variant_url =  url = f"https://api.printful.com/store/products/{product_id}"
          product_response = requests.get(product_url, headers=PRINTFUL_HEADERS)
          product_response.raise_for_status()
          product_data = product_response.json().get("result", {})

          # Extract product details directly
          product_name = product_data.get("name", "Unnamed Product")
          retail_price = float(product_data.get("retail_price", 0.0))  # Price on the product level
          currency = product_data.get("currency", "GBP")  # Default currency if not provided

          # Use product_id as variant_id since no variants exist
          variant_id = product_id
        else:
          # Try to fetch the variant
          print(f"📦 Checking variant ID: {variant_id}")
          variant_url = f"https://api.printful.com/store/variant/{variant_id}"
          printful_response = requests.get(variant_url, headers=PRINTFUL_HEADERS)

        if printful_response.status_code == 404:
            print("⚠️ Variant not found. Trying product fallback...")

            # Try as a product ID
            product_url = f"https://api.printful.com/store/products/{variant_id}"
            product_response = requests.get(product_url, headers=PRINTFUL_HEADERS)

            if product_response.status_code == 404:
                print("⚠️ Product not found either. Fallback to original ID as variant.")
                # Retry original variant ID one last time
                variant_url = f"https://api.printful.com/store/variant/{variant_id}"
                printful_response = requests.get(variant_url, headers=PRINTFUL_HEADERS)
                printful_response.raise_for_status()
            else:
                product_data = product_response.json().get("result", {})
                variants = product_data.get("variants", [])

                if not variants:
                    print("⚠️ No variants found in product. Fallback to original ID as variant.")
                    # Retry original ID as variant
                    variant_url = f"https://api.printful.com/store/variant/{variant_id}"
                    printful_response = requests.get(variant_url, headers=PRINTFUL_HEADERS)
                    printful_response.raise_for_status()
                else:
                    # Use first variant
                    variant_id = variants[0]["id"]
                    print(f"✅ Using fallback variant ID: {variant_id}")
                    variant_url = f"https://api.printful.com/store/variant/{variant_id}"
                    printful_response = requests.get(variant_url, headers=PRINTFUL_HEADERS)
                    printful_response.raise_for_status()
        else:
            printful_response.raise_for_status()

        variant_info = printful_response.json().get("result")
        product_name = variant_info.get("product", {}).get("name", "Unnamed Product")
        variant_name = variant_info.get("name", f"Size {size}")
        retail_price = variant_info.get("retail_price", 29.00)

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "product_data": {
                        "name": f"{product_name} - {variant_name}",
                    },
                    "unit_amount": int(float(retail_price) * 100),
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

        # Only update spend after successful session creation
        daily_spend += order_total
        return jsonify({"stripe_link": session.url})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to submit order: {str(e)}"}), 500

    
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
