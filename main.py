from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

PRINTFUL_API_KEY = os.getenv("PRINTFUL_API_KEY")
PRINTFUL_HEADERS = {
    "Authorization": f"Bearer {PRINTFUL_API_KEY}"
}

@app.route("/")
def index():
    return jsonify({
        "✅ Flask API is running": True,
        "Routes": {
            "/test-api": "🔧 Check connection to Printful API",
            "/get-product-details/</get-product-ids>": "📦 Get details of a specific Printful product",
            "/submit-order": "🛒 Submit an order via POST (requires JSON payload)",
            "/debug-env": "🧪 (Optional) Debug: See if the PRINTFUL_API_KEY is loaded"
        }
    })

@app.route("/test-api")
def test_api():
    response = requests.get("https://api.printful.com/store/products", headers=PRINTFUL_HEADERS)
    return jsonify(response.json()), response.status_code

@app.route("/get-product-details/<product_id>")
def get_product_details(product_id):
    url = f"https://api.printful.com/store/products/{product_id}"
    response = requests.get(url, headers=PRINTFUL_HEADERS)
    return jsonify(response.json()), response.status_code

# ✅ Get all product IDs (driver route you mentioned)
@app.route("/get-product-ids")
def get_product_ids():
    url = "https://api.printful.com/store/products"
    all_products = []
    offset = 0
    limit = 20  # Adjust if you know Printful allows more per page
    if res.status_code != 200:
        return jsonify({"error": "❌ Product not found"}), 404

    while True:
        paged_url = f"{url}?limit={limit}&offset={offset}"
        r = requests.get(paged_url, headers=headers)
        if r.status_code != 200:
            return jsonify({"error": "Failed to fetch product list", "status_code": r.status_code})
        data = r.json()
        products = data.get("result", [])
        all_products.extend(products)
        return jsonify({"result": res.json()})
        if len(products) < limit:
            break  # No more pages
        offset += limit

    ids = [{"id": p["id"], "name": p["name"]} for p in all_products]
    return jsonify(ids)

@app.route("/submit-order", methods=["POST"])
def submit_order():
    data = request.json
    response = requests.post(
        "https://api.printful.com/orders",
        headers=PRINTFUL_HEADERS,
        json=data
    )
    return jsonify(response.json()), response.status_code

@app.route("/debug-env")
def debug_env():
    return jsonify({
        "PRINTFUL_API_KEY exists": bool(PRINTFUL_API_KEY)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
