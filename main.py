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

@app.route("/submit-order", methods=["POST"])
def submit_order():
    data = request.json
    variant_id = data.get("variant_id")

    if not variant_id:
        return jsonify({"error": "Missing variant_id"}), 400

    # Fetch product info from your backend
    try:
        response = requests.get(f"{BACKEND_URL}{variant_id}")
        response.raise_for_status()
        product_info = response.json()
    except Exception as e:
        return jsonify({"error": f"Failed to fetch product info: {str(e)}"}), 500

    try:
        # Extract product details
        product_name = product_info.get("name", "Badger Shirt")
        unit_price = int(float(product_info.get("price", 15.00)) * 100)  # in pence
        quantity = int(data.get("quantity", 1))

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "unit_amount": unit_price,
                    "product_data": {
                        "name": product_name,
                        "images": [product_info.get("image_url", "")],
                    },
                },
                "quantity": quantity,
            }],
            mode="payment",
            success_url="https://martinnewbold.co.uk/thanks?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://martinnewbold.co.uk/cancelled",
            metadata={
                "variant_id": variant_id,
                "name": data.get("name"),
                "email": data.get("email"),
                "address": data.get("address"),
                "city": data.get("city"),
                "size": data.get("size"),
                "quantity": quantity,
            }
        )

        # Optionally: send order to Printful here, or only after payment confirmation webhook

        return jsonify({"stripe_link": session.url})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


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
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")  # ✅ Make sure this is defined in your env

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({"error": "Invalid signature"}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        variant_id = session['metadata'].get('variant_id')
        name = session['metadata'].get('name')
        email = session['metadata'].get('email')
        # 🚧 TODO: trigger Printful order, store data, notify user, etc.

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
