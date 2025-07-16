import requests
import os

def move_funds_from_revolut():
    token = os.getenv("REVOLUT_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    
    body = {
        "request_id": "move-001",
        "source_account_id": "xxx",  # your main GBP account
        "target_account_id": "yyy",  # your holding/savings subaccount
        "amount": 18.50,
        "currency": "GBP",
        "reference": "Boris Shirt Order 443"
    }

    response = requests.post("https://b2b.revolut.com/api/1.0/transfer", headers=headers, json=body)
    print(response.status_code, response.json())
