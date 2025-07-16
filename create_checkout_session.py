
from flask import Flask, request, jsonify
import stripe
import os

app = Flask(__name__)

# Set your Stripe secret key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.json
    item_name = data.get("item")
    amount = float(data.get("amount", 0))

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "product_data": {
                        "name": item_name
                    },
                    "unit_amount": int(amount * 100),  # Stripe requires pence
                },
                "quantity": 1,
            }],
            metadata={
                "item": item_name
            },
            success_url="https://yourdomain.com/success",
            cancel_url="https://yourdomain.com/cancel",
        )
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify(error=str(e)), 400
