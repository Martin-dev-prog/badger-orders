from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

# ✅ Load Printful API key from environment
PRINTFUL_TOKEN = os.getenv("PRINTFUL_API_KEY")
if not PRINTFUL_TOKEN:
    raise ValueError("Missing PRINTFUL_API_KEY environment variable")

headers = {
    "Authorization": f"Bearer {PRINTFUL_TOKEN}"
}

# ✅ Test route
@app.route("/")
def root():
    return jsonify({"message": "Flask is working and CORS is enabled."})

# ✅ Test Printful API connection
@app.route("/test-api")
def test_api():
    url = "https://api.printful.com/store/products"
    r = requests.get(url, headers=headers)
    return jsonify({
        "status_code": r.status_code,
        "result": r.json() if r.status_code == 200 else r.text
    })

# ✅ Get product details by ID
@app.route("/get-product-details/<int:product_id>")
def get_product_details(product_id):
    url = f"https://api.printful.com/store/products/{product_id}"
    r = requests.get(url, headers=headers)
    return jsonify({
        "status_code": r.status_code,
        "result": r.json() if r.status_code == 200 else r.text
    })

# ✅ Get all product IDs (driver route you mentioned)
@app.route("/get-product-ids")
def get_product_ids():
    url = "https://api.printful.com/store/products"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        return jsonify({"error": "Failed to fetch product list", "status_code": r.status_code})
    products = r.json().get("result", [])
    ids = [{"id": p["id"], "name": p["name"]} for p in products]
    return jsonify(ids)

# ✅ Debug env
@app.route("/debug-env")
def debug_env():
    return jsonify({
        "token_found": bool(PRINTFUL_TOKEN),
        "starts_with": PRINTFUL_TOKEN[:8] + "..." if PRINTFUL_TOKEN else "None",
        "length": len(PRINTFUL_TOKEN) if PRINTFUL_TOKEN else 0
    })

# ✅ Required to run Flask on Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
