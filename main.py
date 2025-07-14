from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

# ✅ Load Printful API key from environment
PRINTFUL_TOKEN = os.getenv("PRINTFUL_API_KEY")
if not PRINTFUL_TOKEN:
    raise ValueError("Missing PRINTFUL_API_KEY environment variable")

# ✅ Authorization headers
headers = {
    "Authorization": f"Bearer {PRINTFUL_TOKEN}"
}


# ✅ Setup Flask and CORS
app = Flask(__name__)
CORS(app)

# ✅ Test route
@app.get("/")
def root():
    return {"message": "FastAPI is working and CORS is enabled."}

# ✅ Product details route
@app.get("/get-product-details/{product_id}")
def get_product_details(product_id: int):
    url = f"https://api.printful.com/store/products/{product_id}"
    r = requests.get(url, headers=headers)
    return {
        "status_code": r.status_code,
        "result": r.json() if r.status_code == 200 else r.text
    }

# ✅ Optional: check environment key
@app.get("/debug-env")
def debug_env():
    return {
        "token_found": bool(PRINTFUL_TOKEN),
        "starts_with": PRINTFUL_TOKEN[:8] + "..." if PRINTFUL_TOKEN else "None",
        "length": len(PRINTFUL_TOKEN) if PRINTFUL_TOKEN else 0
    }
