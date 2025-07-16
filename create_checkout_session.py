from flask import Flask, request, jsonify
import stripe
import os

app = Flask(__name__)

# Stripe secret key loaded from environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.json
    item_name = data.get("item")
    amount = data.get("amount")
    quantity = int(data.get("quantity", 1))

    # Validate input
    if not item_name or not amount:
        return jsonify(error="Missing 'item' or 'amount' in request"), 400

    try:
        # Convert amount to pence (int)
        amount_pence = int(float(amount) * 100)

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "product_data": {
                        "name": item_name,
                    },
                    "unit_amount": amount_pence,
                },
                "quantity": quantity,
            }],
            metadata={
                "item": item_name,
                "quantity": quantity
            },
            success_url=os.getenv("SUCCESS_URL", "https://yourdomain.com/success"),
            cancel_url=os.getenv("CANCEL_URL", "https://yourdomain.com/cancel"),
        )

        # Return Stripe checkout URL to frontend
        return jsonify({"stripe_link": session.url})

    except Exception as e:
        return jsonify(error=str(e)), 400

if __name__ == "__main__":
    app.run(debug=True)
