from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

PRINTFUL_API_KEY = os.getenv("PRINTFUL_API_KEY")
MERCHANT_EMAIL = os.getenv("MERCHANT_EMAIL")

if not PRINTFUL_API_KEY or not MERCHANT_EMAIL:
    raise EnvironmentError("❌ Missing required environment variables.")

@app.route("/")
def home():
    return jsonify({"message": "✅ Printful Order API is running."})

@app.route("/test-api")
def test_api():
    headers = {"Authorization": f"Bearer {PRINTFUL_API_KEY}"}
    res = requests.get("https://api.printful.com/store/products", headers=headers)
    return jsonify(res.json())

@app.route("/get-product-details/<int:product_id>")
def get_product_details(product_id):
    headers = {"Authorization": f"Bearer {PRINTFUL_API_KEY}"}
    res = requests.get(f"https://api.printful.com/store/products/{product_id}", headers=headers)

    if res.status_code != 200:
        return jsonify({"error": "❌ Product not found"}), 404

    return jsonify({"result": res.json()})

@app.route("/submit-order", methods=["POST"])
def submit_order():
    data = request.get_json()
    print("🛒 Order received:", data)
    
    # Optional: Forward order via email, save to file/db, or call Printful's order endpoint here

    return jsonify({"message": "✅ Order submitted successfully"})

@app.route("/index.html")
def redirect_index():
    return Response("This is a placeholder for your index.html if needed.", mimetype='text/html')

if __name__ == "__main__":
    app.run(debug=True)
