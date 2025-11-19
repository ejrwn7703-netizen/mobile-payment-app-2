"""Simple smoke test using Flask test_client to exercise the mock payment flow."""
from mobile_payment_app.app import app


def run_smoke():
    client = app.test_client()

    # create payment
    resp = client.post(
        "/api/payments",
        json={"amount": 100, "currency": "KRW", "payment_method": "naverpay"},
    )
    print("create status", resp.status_code, resp.get_json())
    data = resp.get_json() or {}
    pid = data.get("payment_id")

    if not pid:
        print("Payment creation failed; aborting smoke test")
        return

    # get status
    resp2 = client.get(f"/api/payments/{pid}")
    print("status get", resp2.status_code, resp2.get_json())

    # callback simulate
    resp3 = client.post("/api/payments/callback", json={"payment_id": pid, "status": "completed"})
    print("callback", resp3.status_code, resp3.get_json())

    resp4 = client.get(f"/api/payments/{pid}")
    print("status after callback", resp4.status_code, resp4.get_json())


if __name__ == "__main__":
    run_smoke()
