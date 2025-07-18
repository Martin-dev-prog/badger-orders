from flask import Flask, request, session, redirect, jsonify, url_for, render_template_string, abort,send_from_directory
from functools import wraps
from flask_cors import CORS
from datetime import date

import os
import stripe
import requests  
import sqlite3
from datetime import date

app = Flask(
    __name__,
    static_folder='static',    # folder on disk
    static_url_path=''         # serve at URL path “/”
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-default")
CORS(app)
import logging
from flask import got_request_exception

DB_PATH = 'daily_spend.db'
daily_spend = 0
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")
PRINTFUL_API_KEY = os.getenv("PRINTFUL_API_KEY")
PRINTFUL_HEADERS = {
    "Authorization": f"Bearer {PRINTFUL_API_KEY}"
}
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


BACKEND_URL = os.getenv("BACKEND_URL")  # e.g. "https://yourbackend.com/products/"
destination_linked_acct  = os.getenv("DESTINATION_STRIPE_LINKED_ACCT")  # e.g. "https://yourbackend.com/products/"
last_reset = date.today()

MAX_DAILY_SPEND = float(os.getenv("MAX_DAILY_SPEND", "100"))

# Log exceptions to the console
logging.basicConfig(level=logging.DEBUG)



def reset_daily_spend_if_needed():
    amount, reset_date = get_daily_state()
    today = date.today().isoformat()
    if reset_date != today:
        amount = 0
        reset_date = today
        save_daily_state(amount, reset_date)
    return amount, reset_date

@app.route('/submit-order', methods=['POST'])
def submit_order():
    amount, reset_date = reset_daily_spend_if_needed()
    if amount >= MAX_DAILY_SPEND:
        return jsonify({
            "error": "Daily order limit reached. Please try again tomorrow."
        }), 429

    # ... process order, compute cost `order_cost` ...
    amount += order_cost
    save_daily_state(amount, reset_date)

    return jsonify({"message": "Order placed!", "new_total": amount})



def log_exception(sender, exception, **extra):
    sender.logger.exception("Unhandled exception:")
got_request_exception.connect(log_exception, app)

# And override the default error handler so you can see the stack trace in-browser:
@app.errorhandler(Exception)
def handle_exception(e):
    # Log it again (optional)
    app.logger.exception("Exception on request:")
    # Return the full stacktrace (only for debugging—remove in prod!)
    import traceback
    return "<pre>" + traceback.format_exc() + "</pre>", 500


def reset_daily_spend_if_needed():
    global daily_spend, last_reset
    today = date.today()
    if today != last_reset:
        daily_spend = 0
        last_reset = today
        
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function
    
def get_daily_state():
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT amount FROM spend WHERE spend_date = ?", (today,))
    row = cur.fetchone()
    conn.close()
    return (row[0] if row else 0.0), today

def save_daily_state(amount, spend_date):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO spend(spend_date, amount)
        VALUES(?, ?)
        ON CONFLICT(spend_date) DO UPDATE SET amount=excluded.amount
    """, (spend_date, amount))
    conn.commit()
    conn.close()

import traceback

def check_password():
    token = request.args.get("token")
    if token != ADMIN_PASSWORD:
        abort(403, description="Unauthorized")

@app.before_first_request
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spend (
            spend_date TEXT PRIMARY KEY,
            amount     REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()
        
@app.route("/")
def index():
    return app.send_static_file('index.html')
def api_index():
    return jsonify({
        "✅ Flask API is running": True,
        "Routes": {
            "/test-api": "🔧 Check connection to Printful API.",
            "/get-product-details/</get-product-ids>": "📦 Get details of a specific Printful product.",
            "/submit-order": "🛒 Submit an order via POST (requires JSON payload).",
            "/debug-env": "🧪 (Optional) Debug: See if the PRINTFUL_API_KEY is loaded.",
            "/admin/set-limit": "Requires password from environment var to set the balance limit for the linked bank acount on printful.",
            "/admin/reset-spend": "Sets the defauly balance back  in the syste for deivery of goods cost.",
            "/admin/dashboard": "Login"
        }
    })

login_form_html = """
<!doctype html>
<title>Admin Login</title>
<h2>Admin Login</h2>
<form method="post">
  <input type="password" name="password" placeholder="Enter admin password" required>
  <button type="submit">Login</button>
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
"""

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template_string(login_form_html, error="Incorrect password")
    return render_template_string(login_form_html)
@app.route("/admin/dashboard", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    message = ""

    if request.method == "POST":
        if "reset_spend" in request.form:
            global daily_spend
            daily_spend = 0
            message = "✅ Daily spend has been reset to 0."

        elif "set_limit" in request.form:
            try:
                new_limit = float(request.form.get("new_limit", ""))
                global MAX_DAILY_SPEND
                MAX_DAILY_SPEND = new_limit
                message = f"✅ MAX_DAILY_SPEND set to {MAX_DAILY_SPEND}."
            except ValueError:
                message = "❌ Invalid limit entered."

    return render_template_string("""
        <h1>Admin Dashboard</h1>
        {% if message %}
          <p style="color:green;">{{ message }}</p>
        {% endif %}
        <form method="post">
            <button name="reset_spend" type="submit">Reset Daily Spend</button>
        </form>
        <hr>
        <form method="post">
            <label for="new_limit">Set New Spend Limit (£):</label>
            <input name="new_limit" type="number" step="0.01" min="0" required>
            <button name="set_limit" type="submit">Set Limit</button>
        </form>
    """, message=message)

@app.route("/admin/reset-spend", methods=["POST"])
def reset_spend():
    check_password()
    global daily_spend
    daily_spend = 0
    return jsonify({"status": "✅ Spend reset to 0"})

@app.route("/admin/set-limit", methods=["POST"])
def set_limit():
    check_password()
    try:
        new_limit = float(request.json.get("limit"))
        global MAX_DAILY_SPEND
        MAX_DAILY_SPEND = new_limit
        return jsonify({"status": f"✅ MAX_DAILY_SPEND set to {MAX_DAILY_SPEND}"})
    except Exception as e:
        return jsonify({"error": f"Invalid limit: {str(e)}"}), 400


@app.route("/submit-order", methods=["POST", "OPTIONS"])
def submit_order():
    if request.method == "OPTIONS":
        return '', 204  # CORS preflight

    amount, today = get_daily_state()
    if amount >= MAX_DAILY_SPEND:
        return jsonify({
            "error": "Daily order limit reached. Please try again tomorrow."
        }), 429

    try:
        data = request.json

        variant_id = data.get("variant_id")
        product_id = data.get("product_id", "Unknown")
        size = data.get("size", "Unknown")
        color = data.get("color", "Unknown")
        name = data.get("name")
        email = data.get("email")
        address = data.get("address")
        city = data.get("city")
        quantity = int(data.get("quantity", 1))

        #if not variant_id or variant_id.strip().upper() == "UNKNOWN":
        #    return jsonify({"error": "Missing or invalid variant_id"}), 400

        unit_price = 3000  # e.g. £30.00 in pence, or adjust as needed
        order_total = unit_price * quantity

        if daily_spend + order_total > MAX_DAILY_SPEND:
            return jsonify({"error": "Daily order limit reached. Please try again tomorrow."}), 429

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "product_data": {
                        "name": f"Product {product_id} - Size {size} - Color {color}",
                    },
                    "unit_amount": unit_price,
                },
                "quantity": quantity,
            }],
            metadata={
                "variant_id": variant_id,
                "product_id": product_id,
                "size": size,
                "color": color,
                "name": name,
                "email": email,
                "address": address,
                "city": city,
            },
            success_url=os.getenv("SUCCESS_URL", "https://yourdomain.com/success"),
            cancel_url=os.getenv("CANCEL_URL", "https://yourdomain.com/cancel"),
        )

        daily_spend += order_total

        return jsonify({"stripe_link": session.url})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to submit order: {str(e)}"}), 500

 
    
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({"error": "Invalid signature"}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get('metadata', {})
        variant_id = metadata.get('variant_id')
        name = metadata.get('name')
        email = metadata.get('email')
        address = metadata.get('address')
        city = metadata.get('city')
        size = metadata.get('size')
        quantity = int(metadata.get('quantity', 1))

        payment_intent_id = session.get('payment_intent')
        if payment_intent_id:
            try:
                payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

                # Create transfer to connected Revolut account
                transfer = stripe.Transfer.create(
                    amount=payment_intent['amount_received'],
                    currency=payment_intent['currency'],  # fix typo here
                    destination=os.getenv("DESTINATION_LINKED_ACCT"),  # put your connected acct ID here or env var
                    transfer_group=payment_intent['id'],
                )
            except Exception as e:
                print(f"Transfer creation failed: {str(e)}")
                # You can choose to return or continue here

        # Create Printful order (simplified example)
        printful_api_key = os.getenv("PRINTFUL_API_KEY")
        if printful_api_key:
            printful_order_url = "https://api.printful.com/orders"
            headers = {
                "Authorization": f"Bearer {printful_api_key}",
                "Content-Type": "application/json",
            }
            order_payload = {
                "recipient": {
                    "name": name,
                    "address1": address,
                    "city": city,
                    "country_code": "GB",  # adjust as needed
                },
                "items": [{
                    "variant_id": int(variant_id),
                    "quantity": quantity,
                }],
                "options": {
                    "printful": {"store_order_number": payment_intent_id}
                }
            }
            try:
                response = requests.post(printful_order_url, json=order_payload, headers=headers)
                response.raise_for_status()
                print("Printful order created:", response.json())
            except Exception as e:
                print(f"Printful order creation failed: {str(e)}")

    return jsonify({"status": "success"})
    
@app.route("/test-api")
def test_api():
    response = requests.get("https://api.printful.com/store/products", headers=PRINTFUL_HEADERS)
    return jsonify(response.json()), response.status_code

@app.route("/get-product-details/<product_id>")
def get_product_details(product_id):
    url = f"https://api.printful.com/store/products/{product_id}"
    response = requests.get(url, headers=PRINTFUL_HEADERS)
    return jsonify(response.json()), response.status_code

@app.route("/get-product-ids")
def get_product_ids():
    url = "https://api.printful.com/store/products"
    all_products = []
    offset = 0
    limit = 20  # Printful API default pagination limit

    while True:
        paged_url = f"{url}?limit={limit}&offset={offset}"
        r = requests.get(paged_url, headers=PRINTFUL_HEADERS)
        if r.status_code != 200:
            return jsonify({"error": "Failed to fetch product list", "status_code": r.status_code}), r.status_code
        data = r.json()
        products = data.get("result", [])
        all_products.extend(products)
        if len(products) < limit:
            break  # No more pages
        offset += limit

    ids = [{"id": p["id"], "name": p["name"]} for p in all_products]
    return jsonify(ids)

@app.route("/debug-env")
def debug_env():
    return jsonify({
        "PRINTFUL_API_KEY exists": bool(PRINTFUL_API_KEY)
    })

# -- Static file serving routes added below --

@app.route('/index.html')
def serve_index_html():
    return send_from_directory('static', 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory('static', filename)

# Optional: serve root '/' to index.html
@app.route('/home')
@app.route('/app')
@app.route('/dashboard')
@app.route('/')
def serve_root():
    return send_from_directory('static', 'index.html')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
