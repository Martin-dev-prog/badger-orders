from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

PRINTFUL_API_KEY = os.getenv("PRINTFUL_API_KEY")
PRINTFUL_HEADERS = {
    "Authorization": f"Bearer {PRINTFUL_API_KEY}"
}


    return jsonify({
        "✅ Flask API is running": True,
        "Available Routes": {
            "/test-api": "🔧 Check Printful API connection",
            "/get-product-details/<product_id>": "📦 Get full details for one product",
            "/get-product-ids": "📋 Get list of all product IDs (and names)",
            "/submit-order": "🛒 Submit order (POST JSON)",
            "/debug-env": "🧪 Debug API token"
        },
        "Examples": {
            "Test API": "/test-api",
            "Product Details": "/get-product-details/386786171",
            "Product List": "/get-product-ids",
            "Order Submission": {
                "Method": "POST",
                "URL": "/submit-order",
                "Body Format": {
                    "recipient": {
                        "name": "John Doe",
                        "address1": "123 Main St",
                        "city": "London",
                        "zip": "W1A 1AA",
                        "country_code": "GB"
                    },
                    "items": [
                        {
                            "variant_id": 1234,
                            "quantity": 1
                        }
                    ]
                }
            }
        }
    })
@app.route("/get-product-details/<int:product_id>")
def get_product_details(product_id):
    try:
        url = f"https://api.printful.com/store/products/{product_id}"
        response = requests.get(url, headers=PRINTFUL_HEADERS)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch product"}), response.status_code

        product_data = response.json()

        # Optionally, fetch variant details too
        variant_url = f"https://api.printful.com/store/products/{product_id}/sync-variants"
        variant_response = requests.get(variant_url, headers=PRINTFUL_HEADERS)

        if variant_response.status_code == 200:
            product_data["result"]["sync_variants"] = variant_response.json().get("result", [])

        return jsonify({"result": product_data["result"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/submit-order", methods=["POST"])
def submit_order():
    data = request.get_json()
    print("🛒 Order received:", data)

    required_fields = ["name", "email", "address", "city", "size", "quantity", "variant_id"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # You can add logic here to send order to Printful using /orders endpoint
    return jsonify({"message": "✅ Order submitted successfully"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
