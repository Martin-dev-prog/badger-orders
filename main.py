from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

# Load Printful API key
PRINTFUL_TOKEN = os.getenv("PRINTFUL_API_KEY")
if not PRINTFUL_TOKEN:
    raise ValueError("Missing PRINTFUL_API_KEY environment variable")

headers = {
    "Authorization": f"Bearer {PRINTFUL_TOKEN}"
}

# ✅ Test endpoint
@app.route("/test-api")
def test_api():
    return {
        "status": "✅ Flask API is live",
        "token_prefix": PRINTFUL_TOKEN[:6] + "..." if PRINTFUL_TOKEN else "Not found"
    }

# ✅ Get ALL product IDs
@app.route("/get-product-ids")
def get_product_ids():
    url = "https://api.printful.com/store/products"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": f"Failed to fetch products: {response.text}"}, response.status_code

    data = response.json().get("result", [])
    simplified = [
        {
            "id": item["id"],
            "name": item["name"],
            "thumbnail": item.get("thumbnail_url", "")
        }
        for item in data
    ]
    return jsonify({"products": simplified})

# ✅ Get product details by ID
@app.route("/get-product-details/<int:product_id>")
def get_product_details(product_id):
    url = f"https://api.printful.com/store/products/{product_id}"
    r = requests.get(url, headers=headers)
    try:
        return {"result": r.json()}
    except:
        return {"error": "Could not parse response", "raw": r.text}, 500

# ✅ Submit order
@app.route("/submit-order", methods=["POST"])
def submit_order():
    data = request.form

    payload = {
        "recipient": {
            "name": data.get("name"),
            "email": data.get("email"),
            "address1": data.get("address"),
            "city": data.get("city"),
            "country_code": "GB"
        },
        "items": [
            {
                "variant_id": int(data.get("variant_id")),
                "quantity": int(data.get("quantity", 1))
            }
        ]
    }

    response = requests.post("https://api.printful.com/orders", json=payload, headers=headers)
    return response.json(), response.status_code
