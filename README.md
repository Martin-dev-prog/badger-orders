# 🦡 Badger Orders – Printful Order API (Flask)

This is a lightweight Python Flask API for submitting print-on-demand orders (e.g. T-shirts) to the [Printful API](https://www.printful.com/docs), built for use with a custom front-end such as a WordPress HTML form.

---

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
