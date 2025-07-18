import os
import logging
import sqlite3
from datetime import date

import stripe
import requests
from flask import (
    Flask, request, session, redirect, jsonify,
    url_for, render_template_string, abort,
    send_from_directory, got_request_exception
)
from flask_cors import CORS
from functools import wraps

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
    static_folder='static',
    static_url_path=''
)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-default')
CORS(app)
logging.basicConfig(level=logging.DEBUG)

def log_exception(sender, exception, **extra):
    sender.logger.exception('Unhandled exception:')
got_request_exception.connect(log_exception, app)

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

# ——— SQLite Helpers —————————————————————————————————
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
_db_initialized = False
@app.before_request
def _ensure_db():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True

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

# ——— Routes —————————————————————————————————————
@app.route('/')
@app.route('/index.html')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/api')
def api_index():
    return jsonify({
        '✅ Flask API is running': True,
        'Routes': {
            '/test-api': 'Check Printful connectivity',
            '/get-product-ids': 'List Printful products',
            '/get-product-details/<product_id>': 'Product details',
            '/submit-order': 'Submit an order (POST JSON)',
            '/admin/set-limit': 'Set spend limit (POST token+limit)',
            '/admin/reset-spend': 'Reset daily counter (POST token)',
            '/admin/dashboard': 'Admin web UI'
        }
    })

login_form = '''<!doctype html>
<title>Admin Login</title>
<h2>Admin Login</h2>
<form method="post">
  <input type="password" name="password" placeholder="Admin password" required>
  <button type="submit">Login</button>
</form>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}'''

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        if request.form.get('password')==ADMIN_PASSWORD:
            session['admin_logged_in']=True
            return redirect(url_for('admin_dashboard'))
        return render_template_string(login_form, error='Incorrect password')
    return render_template_string(login_form)

@app.route('/admin/dashboard', methods=['GET','POST'])
@admin_required
def admin_dashboard():
    msg=''
    if request.method=='POST':
        if 'reset_spend' in request.form:
            save_daily_state(0.0, date.today().isoformat())
            msg='✅ Daily spend reset.'
        elif 'set_limit' in request.form:
            try:
                new=float(request.form['new_limit'])
                global MAX_DAILY_SPEND
                MAX_DAILY_SPEND=new
                msg=f'✅ Limit set to {new}.'
            except:
                msg='❌ Invalid limit.'
    return render_template_string('''<h1>Dashboard</h1>
{{msg}}<form method="post"><button name="reset_spend">Reset Spend</button></form>
<form method="post">Limit: <input name="new_limit" type="number" step="0.01" required>
<button name="set_limit">Set Limit</button></form>''', msg=msg)

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

@app.route('/test-api')
def test_api():
    r=requests.get('https://api.printful.com/store/products', headers=PRINTFUL_HEADERS)
    return jsonify(r.json()), r.status_code

@app.route('/get-product-ids')
def get_product_ids():
    url='https://api.printful.com/store/products'
    allp,off,lim=[],0,20
    while True:
        r=requests.get(f"{url}?limit={lim}&offset={off}",headers=PRINTFUL_HEADERS)
        if r.status_code!=200:
            return jsonify({'error':'Failed'}),r.status_code
        data=r.json().get('result',[])
        allp+=data
        if len(data)<lim:break
        off+=lim
    return jsonify([{'id':p['id'],'name':p['name']} for p in allp])

@app.route('/get-product-details/<product_id>')
def get_product_details(product_id):
    try:
        r=requests.get(f"https://api.printful.com/store/products/{product_id}",
                       headers=PRINTFUL_HEADERS,timeout=5)
        r.raise_for_status()
        return jsonify(r.json()),r.status_code
    except Exception as e:
        app.logger.exception("Error loading product")
        return jsonify({'error':'Failed to load','details':str(e)}),502

@app.route('/submit-order',methods=['POST','OPTIONS'])
def submit_order():
    if request.method=='OPTIONS':return '',204
    amt,today=reset_daily_spend_if_needed()
    if amt>=MAX_DAILY_SPEND:
        return jsonify({'error':'Daily order limit reached'}),429
    d=request.json or {}
    qty=int(d.get('quantity',1))
    cost=3000*qty
    if amt+cost>MAX_DAILY_SPEND:
        return jsonify({'error':'Daily order limit reached'}),429
    sess=stripe.checkout.Session.create(
        payment_method_types=['card'],mode='payment',
        line_items=[{'price_data':{'currency':'gbp',
                    'product_data':{'name':d.get('name','')},
                    'unit_amount':cost//qty},
                    'quantity':qty}],
        metadata={k:d.get(k) for k in('variant_id','product_id','size','color','name','email','address','city')},
        success_url=os.getenv('SUCCESS_URL',''),cancel_url=os.getenv('CANCEL_URL','')
    )
    amt+=cost
    save_daily_state(amt,today)
    return jsonify({'stripe_link':sess.url})

@app.route('/stripe/webhook',methods=['POST'])
def stripe_webhook():
    payload, sig = request.data, request.headers.get('stripe-signature')
