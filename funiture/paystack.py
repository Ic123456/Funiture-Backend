import requests
from django.conf import settings

def checkout(payload):
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        'https://api.paystack.co/transaction/initialize',
        json=payload,  # ✅ use 'json=' instead of 'data=json.dumps(...)'
        headers=headers
    )

    try:
        response_data = response.json()
    except Exception:
        return False, f"Invalid JSON response from Paystack: {response.text}"

    if response_data.get("status") is True:
        return True, response_data["data"]["authorization_url"]
    else:
        # ✅ Return Paystack's real error message for debugging
        message = response_data.get("message", "Unknown error")
        return False, f"Paystack error: {message}"
