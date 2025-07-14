from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

# ✅ Load Printful token
PRINTFUL_TOKEN = os.getenv("PRINTFUL_API_KEY") or os.getenv("PRINTFUL_TOKEN")
if not PRINTFUL_TOKEN:
    raise ValueError("Missing PRINTFUL_API_KEY or PRINTFUL_TOKEN")

headers = {
    "Authorization": f"Bearer {PRINTFUL_TOKEN}"
}

# ✅ Set up Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# ✅ Health check route
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask API running with CORS"})

# ✅ Product details route — returns raw Printful data
@app.route("/get-product-details/<int:product_id>", methods=["GET"])
def get_product_details(product_id):
    url = f"https://api.printful.com/store/products/{product_id}"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return jsonify(r.json())  # ✅ Return raw Printful data
    else:
        return jsonify({"error": "Product not found", "status": r.status_code})

# ✅ Optional debug route
@app.route("/debug-env", methods=["GET"])
def debug_env():
    return {
        "token_found": bool(PRINTFUL_TOKEN),
        "starts_with": PRINTFUL_TOKEN[:8] + "..." if PRINTFUL_TOKEN else "None",
        "length": len(PRINTFUL_TOKEN) if PRINTFUL_TOKEN else 0
    }

# ✅ Required entry point for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
