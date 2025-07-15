@app.route("/test-api", methods=["GET"])
def test_api():
    headers = {
        "Authorization": f"Bearer {PRINTFUL_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get("https://api.printful.com/store/products", headers=headers)
    return jsonify({
        "status_code": response.status_code,
        "text": response.text
    })
