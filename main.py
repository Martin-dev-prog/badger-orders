#DATE 2025-07-18 v.7-—————————————————————————————————

import os
import logging
import sqlite3
from datetime import date

import stripe
import requests
from flask import (
    Flask, request, session, redirect, jsonify,
    url_for, render_template, render_template_string,
    abort, send_from_directory
)
from flask_cors import CORS
from functools import wraps
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# INITIALISE FLASK -—————————————————————————————————
app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)
DB_PATH = os.path.join(app.instance_path, 'daily_spend.db')
print("Working directory:", os.getcwd())
print("DB path:", os.path.abspath(DB_PATH))

# ——— Configuration —————————————————————————————————
DB_PATH = 'daily_spend.db'
MAX_DAILY_SPEND = float(os.getenv('MAX_DAILY_SPEND', '100'))
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'changeme')
PRINTFUL_API_KEY = os.getenv('PRINTFUL_API_KEY')
PRINTFUL_HEADERS = {'Authorization': f'Bearer {PRINTFUL_API_KEY}'}
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# ——— Flask App Setup —————————————————————————————————
app = Flask(
    __name__,
    static_folder='static',    # on-disk static files
    static_url_path=''         # serve at URL path “/”
)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-default')
CORS(app)
logging.basicConfig(level=logging.DEBUG)

# ——— Initialize daily_spend database —————————————————————————
DB_PATH = os.path.join(app.instance_path, 'daily_spend.db')
with sqlite3.connect(DB_PATH) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spend (
            spend_date TEXT PRIMARY KEY,
            amount     REAL NOT NULL
        )
    """)


# ——— Initialize SQLite DB —————————————————————————————
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS spend (
            spend_date TEXT PRIMARY KEY,
            amount     REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Ensure DB is initialized once
init_db()

# ——— Helper Functions ——————————————————————————————————
def get_daily_state():
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT amount FROM spend WHERE spend_date = ?', (today,))
    row = cur.fetchone()
    conn.close()
    return (row[0] if row else 0.0), today


def save_daily_state(amount, spend_date):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        INSERT INTO spend(spend_date, amount)
        VALUES(?, ?)
        ON CONFLICT(spend_date) DO UPDATE SET amount=excluded.amount
    ''', (spend_date, amount))
    conn.commit()
    conn.close()


def reset_daily_spend_if_needed():
    amount, spend_date = get_daily_state()
    today = date.today().isoformat()
    if spend_date != today:
        amount, spend_date = 0.0, today
        save_daily_state(amount, spend_date)
    return amount, spend_date

# ——— Auth Decorators ————————————————————————————————
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


def check_password():
    token = request.args.get('token') or (request.json or {}).get('token')
    if token != ADMIN_PASSWORD:
        abort(403)

def create_printful_order(name, email, address, city, variant_id, qty, image_url=None):
    """
    Creates a new order on Printful.
    Returns the JSON response from Printful on success.
    Raises if the API call fails.
    """
    url = "https://api.printful.com/orders"
    headers = {
        "Authorization": f"Bearer {os.getenv('PRINTFUL_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "recipient": {
            "name":    name,
            "address1": address,
            "city":    city,
            "country_code": "GB",       # adjust as needed
            "email":   email
        },
        "items": [{
            "variant_id": int(variant_id),
            "quantity":   int(qty),
            # override the print file if you want to ensure the correct image:
            **({"files": [{"url": image_url}]} if image_url else {})
        }]
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("code") == 200 and "result" not in data:
        # Printful returns {"code": 400, "result": {...}} on error
        raise RuntimeError(f"Printful error: {data}")
    return data["result"]

# ——— Error Handling —————————————————————————————————
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception('Exception on request:')
    api_paths = (
        '/test-api', '/get-product-details', '/get-product-ids',
        '/submit-order', '/debug-env', '/admin/set-limit', '/admin/reset-spend'
    )
    if any(request.path.startswith(p) for p in api_paths):
        resp = jsonify({'error': 'Internal Server Error', 'message': str(e)})
        resp.status_code = getattr(e, 'code', 500)
        return resp
    import traceback
    return '<pre>' + traceback.format_exc() + '</pre>', 500

# ——— Routes —————————————————————————————————————
# Serve static files and index
@app.route('/')
@app.route('/index.html')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# API index
@app.route('/api', methods=['GET'])
def api_index():
    return jsonify({
        '✅ Flask API is running': True,
        'Routes': {
            '/test-api': 'Check Printful connectivity',
            '/get-product-ids': 'List Printful products',
            '/get-product-details/<product_id>': 'Product details',
            '/submit-order': 'Submit an order (POST JSON)',
            '/debug-env': 'Debug environment flags',
            '/admin/set-limit': 'Set spend limit (POST token+limit)',
            '/admin/reset-spend': 'Reset daily counter (POST token)',
            '/admin/dashboard': 'Admin web UI'
        }
    })

# Admin UI
login_form = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Admin Login</title>
  <style>
    html, body { height: 100%; margin: 0; display: flex; align-items: center; justify-content: center; background: #f0f0f0; }
    .login-box {
      background: #fff;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      width: 320px;
      font-family: sans-serif;
    }
    .login-box h2 { margin-top: 0; text-align: center; }
    .login-box form { display: flex; flex-direction: column; }
    .login-box input, .login-box button {
      padding: 0.5rem;
      margin-bottom: 1rem;
      font-size: 1rem;
      border-radius: 4px;
    }
    .login-box input { border: 1px solid #ccc; }
    .login-box button {
      border: none;
      background: #007bff;
      color: #fff;
      cursor: pointer;
    }
    .login-box button:hover { background: #0056b3; }
    .login-box .error { color: red; text-align: center; }
  </style>
</head>
<body>
  <div class="login-box">
    <h2>Admin Login</h2>
    <form method="post">
      <input type="password" name="password" placeholder="Admin password" required>
      <button type="submit">Login</button>
    </form>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
  </div>
</body>
</html>'''

@app.route('/favicon.ico')
def favicon():
    # Return “No Content” so browsers don’t keep retrying
    return '', 204
    
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    error=None
    if request.method=='POST':
        if request.form.get('password')==ADMIN_PASSWORD:
            session['admin_logged_in']=True
            return redirect(url_for('admin_dashboard'))
        error='Incorrect password'
    return render_template_string(login_form, error=error)

@app.route('/admin/dashboard', methods=['GET','POST'])
@admin_required
def admin_dashboard():
    message=''
    if request.method=='POST':
        if 'reset_spend' in request.form:
            save_daily_state(0.0, date.today().isoformat())
            message='✅ Daily spend reset.'
        elif 'set_limit' in request.form:
            try:
                new=float(request.form.get('new_limit',''))
                global MAX_DAILY_SPEND
                MAX_DAILY_SPEND=new
                message=f'✅ Limit set to {new}.'
            except ValueError:
                message='❌ Invalid limit.'
            return render_template_string('''
<!doctype html>
<html lang="en">
<head>
  <style>
    #dashboard {
      max-width: 320px;
      margin: 40px auto;
      padding: 20px;
      background: #fff;
      border-radius: 6px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.1);
      text-align: center;
      font-family: sans-serif;
      font-size: 14px;
      color: #333;
    }
    #dashboard h1 {
      margin-bottom: 10px;
      font-size: 18px;
    }
    #dashboard form {
      margin: 12px 0;
    }
    #dashboard input[type="number"] {
      width: 80px;
      margin-left: 6px;
    }
    #dashboard button {
      padding: 6px 12px;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div id="dashboard">
    <h1>Dashboard</h1>
    {% if message %}
      <p>{{ message }}</p>
    {% endif %}
    <form method="post">
      <button name="reset_spend">Reset Spend</button>
    </form>
    <form method="post">
      Limit:
      <input name="new_limit" type="number" step="0.01" required>
      <button name="set_limit">Set Limit</button>
    </form>
  </div>
</body>
</html>
''', message=message)


# Admin API
@app.route('/admin/reset-spend', methods=['POST'])
def api_reset_spend():
    check_password()
    save_daily_state(0.0, date.today().isoformat())
    return jsonify({'status':'✅ Spend reset'})

@app.route('/admin/set-limit', methods=['POST'])
def api_set_limit():
    check_password()
    try:
        new=float(request.json.get('limit'))
        global MAX_DAILY_SPEND
        MAX_DAILY_SPEND=new
        return jsonify({'status':f'✅ Limit set to {new}'})
    except:
        return jsonify({'error':'Invalid limit'}),400

# Printful & Test API
@app.route('/test-api')
def test_api():
    r=requests.get('https://api.printful.com/store/products', headers=PRINTFUL_HEADERS)
    return jsonify(r.json()), r.status_code

@app.route('/get-product-ids')
def get_product_ids():
    url='https://api.printful.com/store/products'
    allp,off,lim=[],0,20
    while True:
        r=requests.get(f"{url}?limit={lim}&offset={off}", headers=PRINTFUL_HEADERS)
        if r.status_code!=200:
            return jsonify({'error':'Failed'}),r.status_code
        data=r.json().get('result',[])
        allp+=data
        if len(data)<lim: break
        off+=lim
    return jsonify([{'id':p['id'],'name':p['name']} for p in allp])

@app.route('/get-product-details/<product_id>')
def get_product_details(product_id):
    try:
        r=requests.get(f"https://api.printful.com/store/products/{product_id}", headers=PRINTFUL_HEADERS, timeout=5)
        r.raise_for_status()
        return jsonify(r.json()), r.status_code
    except Exception as e:
        app.logger.exception("Error loading product details")
        return jsonify({'error':'Failed to load','details':str(e)}),502

# Order Submission
@app.route('/submit-order', methods=['POST','OPTIONS'])
def submit_order_full():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        # 1) Load/reset today’s spend
        amount, today = reset_daily_spend_if_needed()

        # 2) Parse input
        data     = request.json or {}
        qty      = int(data.get('quantity', 1))
        raw_cost = data.get('cost', None)
        print("◀️ Raw cost from payload:", raw_cost)
        base_cost = float(data.get('cost', 0.0))
        product_name = data.get('product_name', '')
        size      = data.get('size', '')
        image_url = data.get('image_url', '')

        # 3) Build combined name: "<name_var> - <qty><size>"
        combined_name = "{} - {} x {}".format( product_name, qty, size)

        # 4) Convert unit cost (pounds) to pence
        from decimal import Decimal, ROUND_HALF_UP
        unit_cost_pence = int(
            (Decimal(str(base_cost)) * 100)
            .to_integral_value(ROUND_HALF_UP)
        )

        # 5) Compute total cost and enforce cap
        cost_pence = unit_cost_pence * qty
        import os
        cap_pence = int(
            (Decimal(os.getenv('MAX_DAILY_SPEND', '100')) * 100)
            .to_integral_value(ROUND_HALF_UP)
        )
        if amount + cost_pence > cap_pence:
            return jsonify({'error': 'Daily order limit reached'}), 429

        # 6) Create Stripe session
        session_obj = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': combined_name,
                        'images': [ image_url ],    # ← images *inside* product_data
                    },
                    'unit_amount': unit_cost_pence ,
                },
                'quantity': qty,
            }],
            metadata={
                'name':       product_name ,
                'size':       size,
                'quantity':   str(qty),
                'price':   str(cost_pence),
                'product_id': data.get('product_id', ''),
                'variant_id': data.get('variant_id', '')
            },
            success_url=os.getenv('SUCCESS_URL', ''),
            cancel_url = os.getenv('CANCEL_URL', '')
        )

        # 7) Persist updated spend
        save_daily_state(amount + cost_pence, today)

        # 8) Return the checkout link
        return jsonify({'stripe_link': session_obj.url})

    except Exception:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        return jsonify({
            'error': 'Internal Server Error',
            'traceback': tb
        }), 500

# Stripe Webhook
@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload, sig = request.data, request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except Exception:
        return jsonify({'error': 'Invalid webhook'}), 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']  # the Stripe session object
        # 1) Pull out your metadata
        metadata = session.get('metadata', {})
        customer_name  = metadata.get('name')
        customer_email = metadata.get('email')
        product_id     = metadata.get('product_id')
        variant_id     = metadata.get('variant_id')
        size           = metadata.get('size')
        qty            = int(metadata.get('quantity', 1))

        # 2) Create a Printful order
        #    (requires you have a function that wraps the Printful API)
        try:
            pf_order = create_printful_order(
                customer_name,
                customer_email,
                metadata.get('address'),
                metadata.get('city'),
                variant_id,
                qty,
                image_url=metadata.get('image_url')
            )
            # 3) Persist the Printful order ID and mark the Stripe session as handled
            save_fulfillment(session['id'], pf_order['id'])
        except Exception as e:
            # Log the error so you can retry fulfillment later
            app.logger.exception("Printful order creation failed for session %s", session['id'])
            # You can choose to return a 200 here so Stripe doesn't keep retrying,
            # or return a non‐200 to force another webhook attempt.
            return jsonify({'status': 'printful_error'}), 500

    return jsonify({'status': 'success'}), 200
# Run
if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT',5000)), debug=True)
