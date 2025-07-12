import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# 👇 INSERT YOUR PRINTFUL TOKEN HERE
PRINTFUL_TOKEN = "pk-7uN9Z5mKhDrpFooAXDbwgSKbHSw5GsWb55wA18VH"  # ← your real token

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
                "variant_id": 4012,  # ← Replace with your actual product variant ID from Printful
                "quantity": 1
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {PRINTFUL_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.printful.com/orders", headers=headers, json=order_payload)
    return jsonify(response.json())