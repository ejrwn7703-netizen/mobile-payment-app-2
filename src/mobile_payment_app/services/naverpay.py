"""Mock NaverPay gateway for local development and tests.

This module provides a lightweight in-memory mock of a payment gateway.
It is intentionally simple and should be replaced with a real integration
when moving to sandbox/live environments.
"""
import uuid
import json
import os
from typing import Dict

# File-based store path (can be customized via env var)
DEFAULT_STORE_PATH = os.environ.get("MOBILE_PAYMENTS_STORE", "data/payments.json")


def _ensure_store_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _load_store(path: str) -> Dict[str, Dict]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_store(path: str, store: Dict[str, Dict]):
    # atomic write
    _ensure_store_dir(path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


class NaverPayGateway:
    def __init__(self, client_id: str = None, client_secret: str = None, mode: str = "sandbox", store_path: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.mode = mode
        self.store_path = store_path or DEFAULT_STORE_PATH
        # load into memory for faster access; persist on modifications
        self._store = _load_store(self.store_path)

    def _persist(self):
        _save_store(self.store_path, self._store)

    def process_payment(self, amount, currency, payment_method, order_id=None, return_url=None):
        """Create a mock payment, persist it, and return a redirect URL for the buyer.

        Returns a dict with keys: payment_id, redirect_url
        """
        payment_id = f"mock-{uuid.uuid4().hex}"
        token = uuid.uuid4().hex
        # Build redirect URL using provided return_url or APP_BASE_URL env var
        redirect_url = self._make_redirect_url(payment_id, token, return_url)

        self._store[payment_id] = {
            "payment_id": payment_id,
            "amount": amount,
            "currency": currency,
            "method": payment_method,
            "order_id": order_id,
            "status": "created",
            "redirect_url": redirect_url,
            "token": token,
        }
        self._persist()

        return {"payment_id": payment_id, "redirect_url": redirect_url}

    def get_payment_status(self, payment_id: str):
        p = self._store.get(payment_id)
        if not p:
            return None
        return p.get("status")

    def handle_callback(self, payload: Dict):
        """Mock handler for payment gateway callbacks/webhooks.

        Expected payload: {"payment_id": ..., "status": "completed"}
        """
        payment_id = payload.get("payment_id")
        status = payload.get("status")
        if not payment_id or not status:
            return False
        p = self._store.get(payment_id)
        if not p:
            return False
        p["status"] = status
        self._store[payment_id] = p
        self._persist()
        return True

    # testing helper
    def _dump_store(self):
        return self._store

    def _make_redirect_url(self, payment_id: str, token: str, return_url: str = None) -> str:
        """Construct redirect URL.

        Priority:
          1. explicit return_url (if provided)
          2. APP_BASE_URL environment variable
          3. default http://127.0.0.1:8000
        """
        if return_url:
            base = return_url.rstrip('/')
            # If return_url already contains query params, append with &
            sep = '&' if '?' in base else '?'
            return f"{base}{sep}payment_id={payment_id}&token={token}"

        base = os.environ.get("APP_BASE_URL", "http://127.0.0.1:8000").rstrip('/')
        return f"{base}/payments/complete?payment_id={payment_id}&token={token}"

