from src.mobile_payment_app.app import app

def test_health_endpoint():
    client = app.test_client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json["status"] == "ok"