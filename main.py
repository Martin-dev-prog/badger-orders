import os
import requests
import JSONResponse



app = Flask(__name__)

# 👇 INSERT YOUR PRINTFUL TOKEN HERE

#PRINTFUL_TOKEN = "pk-ADD API HERE"  # Replace with your real API key
PRINTFUL_TOKEN = os.getenv("PRINTFUL_API_KEY")
if not PRINTFUL_TOKEN:
    raise ValueError("Missing PRINTFUL_API_KEY environment variable")

# ✅ HOME PAGE ROUTE
@app.route("/", methods=["GET"])
def home():
    return "✅ Badger Orders API is running. Use POST /submit-order or GET /test-api or /get-products or /get-variants"

# ✅ TEST API ROUTE
@app.route("/test-api", methods=["GET"])
def test_api():
    headers = {
        "Authorization": f"Bearer {PRINTFUL_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get("https://api.printful.com/store/products", headers=headers)
    return jsonify({
        "status": response.status_code,
        "response": response.json()
    })

# ✅ GET PRODUCTS ROUTE
@app.route("/get-products", methods=["GET"])
def get_products():
    headers = {
        "Authorization": f"Bearer {PRINTFUL_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get("https://api.printful.com/store/products", headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Failed to retrieve products", "status": response.status_code})

    products = response.json().get("result", [])
    output = []

    for product in products:
        name = product.get("name", "Unnamed")
        product_id = product.get("id", "Unknown")
        output.append({"name": name, "id": product_id})

    return jsonify(output)

# ✅ GET VARIANTS ROUTE
@app.route("/get-variants", methods=["GET"])
def get_variants():
    headers = {
        "Authorization": f"Bearer {PRINTFUL_TOKEN}",
        "Content-Type": "application/json"
    }

    # Step 1: Get all products
    products_resp = requests.get("https://api.printful.com/store/products", headers=headers)
    if products_resp.status_code != 200:
        return jsonify({"error": "Failed to fetch products", "status": products_resp.status_code})

    result = []

    for product in products_resp.json().get("result", []):
        product_id = product.get("id")
        product_name = product.get("name")

        # Step 2: Get variants for each product
        variant_resp = requests.get(f"https://api.printful.com/store/products/{product_id}", headers=headers)
        if variant_resp.status_code != 200:
            continue

        variants = variant_resp.json().get("result", {}).get("variants", [])
        simplified_variants = [
            {
                "variant_id": v["id"],
                "name": v["name"]
            }
            for v in variants
        ]

        result.append({
            "product_id": product_id,
            "name": product_name,
            "variants": simplified_variants
        })

    return jsonify(result)

# ✅ ORDER SUBMISSION ROUTE
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
                "variant_id": 4012,  # Replace with actual variant ID
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

# 🔥 DEPLOYMENT ENTRY POINT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
