import requests
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# 👇 INSERT YOUR PRINTFUL TOKEN HERE
PRINTFUL_TOKEN = "pk-ADD API HERE"  # ← Replace with your actual Printful API key

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
                "variant_id": 4012,  # Replace with your actual product variant ID from Printful
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

# 🔥 THIS PART IS REQUIRED FOR DEPLOYMENT
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
