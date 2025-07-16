from flask import Flask, request, jsonify
import stripe
import os

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
BACKEND_URL = os.getenv("BACKEND_URL")  # URL for product info endpoint

@app.route("/submit-order", methods=["POST"])
def submit_order():
    data = request.json
    variant_id = data.get("variant_id")
    if not variant_id:
        return jsonify({"error": "Missing variant_id"}), 400

    try:
        # Fetch product info from your backend or API
        response = requests.get(f"{BACKEND_URL}{variant_id}")
        product_info = response.json()
    except Exception as e:
        return jsonify({"error": f"Failed to fetch product info: {str(e)}"}), 500

    try:
        product_name = product_info.get("name", "Badger Shirt")
        unit_price = int(float(product_info.get("price", 15.00)) * 100)  # pence
        quantity = int(data.get("quantity", 1))

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "unit_amount": unit_price,
                    "product_data": {
                        "name": product_name,
                        "images": [product_info.get("image_url", "")],
                    },
                },
                "quantity": quantity,
            }],
            mode="payment",
            success_url="https://yourdomain.com/thanks?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://yourdomain.com/cancelled",
            metadata={
                "variant_id": variant_id,
                "name": data.get("name"),
                "email": data.get("email"),
                "address": data.get("address"),
                "city": data.get("city"),
                "size": data.get("size"),
                "quantity": quantity,
            }
        )

        return jsonify({"stripe_link": session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
