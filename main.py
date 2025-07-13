import requests
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# 👇 INSERT YOUR PRINTFUL TOKEN HERE
PRINTFUL_TOKEN = "pk-ADD API HERE"  # Replace with your real API key

# ✅ HOME PAGE ROUTE
@app.route("/", methods=["GET"])
def home():
    return "✅ Badger Orders API is running. Use POST /submit-order or GET /test-api"

# ✅ TEST API ROUTE
@app.route("/test-api", methods=["GET"])
def test_api():
    headers = {
        "Authorization": f"Bearer {PRINTFUL_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get("https://api.printful.com/store/products", headers=headers)

    try:
        return jsonify({
            "status": response.status_code,
            "result": response.json()
        })
    except Exception as e:
        return jsonify({
            "status": response.status_code,
            "error": str(e),
            "raw": response.text
        })

# ✅ SUBMIT ORDER ROUTE
@app.route("/submit-order", methods=["POST"])
def submit_order():
    data = request.json

    order_payload = {
        "recipient": {
            "name": data["name"],
            "address1": data["address"],
            "city": data["city"],
            "country_code": "GB"
        },
        "items": [
            {
                "variant_id": 4012,  # Replace with your real Printful variant ID
                "quantity": int(data.get("quantity", 1))
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {PRINTFUL_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.printful.com/orders", headers=headers, json=order_payload)
    return jsonify(response.json())

# 🔥 Render-compatible app runner
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
