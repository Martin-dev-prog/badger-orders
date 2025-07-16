
from flask import Flask, request, jsonify
import stripe
import requests
import os

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        item = session["metadata"].get("item")

        # You can extend this with order database logic
        order_payload = {
            "recipient": {
                "name": session.get("customer_details", {}).get("name", "Unknown"),
                "email": session.get("customer_email", "unknown@example.com")
            },
            "items": [{
                "variant_id": 0000,  # Replace with your actual variant ID logic
                "name": item,
                "quantity": 1
            }]
        }

        # Call your Printful submit-order endpoint
        printful_response = requests.post(
            "http://localhost:5000/submit-order",  # Replace with your actual endpoint
            headers={"Content-Type": "application/json"},
            json=order_payload
        )
        print("Printful response:", printful_response.status_code, printful_response.json())

    return jsonify({"status": "success"})

