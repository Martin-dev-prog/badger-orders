# 🦡 Badger Orders – Printful Order API (Flask)

This is a lightweight Python Flask API for submitting print-on-demand orders (e.g. T-shirts) to the [Printful API](https://www.printful.com/docs), built for use with a custom front-end such as a WordPress HTML form.

---
✅ What we have:
A GitHub-hosted front-end (HTML form)

A Render backend that pulls product data from Printful

A product ID system working via query strings

A merchant service check (email env var test) for readiness

✅ Merchant Services Display What's Being Ordered
A Product name Variant Size

email

address

Quantity

Price (calculated per unit × quantity)

Show image preview

2. 💳 Display Payment Options
A secure PayPal button

A secure Stripe card input

One must be completed before order submission

3. 📦 Only After Payment Success
Create Printful order via /submit-order

## 🔧 Features

- Accepts JSON POST requests at `/submit-order`
- Sends order data securely to Printful via their API
- Ready to deploy on Render, Replit, or any Python-compatible host

- Routes
            "/test-api": "🔧 Check connection to Printful API",
            "/get-product-details/<product_id>": "📦 Get details of a specific Printful product",
            "/submit-order": "🛒 Submit an order via POST (requires JSON payload)",
            "/debug-env": "🧪 (Optional) Debug: See if the PRINTFUL_API_KEY is loaded"
      
  

---

## 🧪 Live Demo

> ✅ Try it: [https://badger-orders.onrender.com](https://badger-orders.onrender.com)

Submit POST request to:
