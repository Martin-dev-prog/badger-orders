import os
import requests
from flask import Flask, request, jsonify

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
@app.route("/get-product-details/<int:product_id>", methods=["GET"])
def get_product_details(product_id):
    headers = {
        "Authorization": f"Bearer {PRINTFUL_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get(f"https://api.printful.com/store/products/{product_id}", headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Product not found", "status": response.status_code})

    return jsonify(response.json())
✅ This will let your form fetch product data by ID like:

arduino
Copy
Edit
https://badger-orders.onrender.com/get-product-details/386786171
✅ Frontend Form Logic (boris-form)
Now update your GitHub page's boris-form.html to:

Grab the id from URL

Call your /get-product-details API

Inject product name/image/variant into the form

✅ Add this JS snippet to your boris-form.html:
html
Copy
Edit
<script>
async function loadProduct() {
  const urlParams = new URLSearchParams(window.location.search);
  const id = urlParams.get("id");

  if (!id) {
    document.getElementById("product-info").innerHTML = "❌ No product ID specified.";
    return;
  }

  const response = await fetch(`https://badger-orders.onrender.com/get-product-details/${id}`);
  const data = await response.json();

  if (data.error) {
    document.getElementById("product-info").innerHTML = "❌ Failed to load product.";
    return;
  }

  const product = data.result;
  const variants = product.variants || [];

  document.getElementById("product-name").innerText = product.name;
  document.getElementById("product-thumb").src = product.thumbnail_url;
  
  // Build variant dropdown
  const variantSelect = document.getElementById("variant-select");
  variants.forEach(v => {
    const option = document.createElement("option");
    option.value = v.id;
    option.text = v.name;
    variantSelect.appendChild(option);
  });
}
window.onload = loadProduct;
</script>
✅ Update HTML in boris-form.html
Add placeholders to fill in:

html
Copy
Edit
<h2 id="product-name">Loading product...</h2>
<img id="product-thumb"


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
