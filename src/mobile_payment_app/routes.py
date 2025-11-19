from flask import Blueprint, request, jsonify
from .services.naverpay import NaverPayGateway
from flask import current_app

bp = Blueprint("api", __name__, url_prefix="/api")

# simple in-memory gateway instance (mock)
gateway = NaverPayGateway()


@bp.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok")


@bp.route("/payments", methods=["POST"])
def create_payment():
    data = request.get_json() or {}
    required = ["amount", "currency", "payment_method"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": "missing_fields", "missing": missing}), 400

    amount = data["amount"]
    currency = data["currency"]
    payment_method = data["payment_method"]
    order_id = data.get("order_id")

    # Build a return URL for the mock redirect (use host from request if not provided)
    provided_return = data.get("return_url")
    if provided_return:
        return_url = provided_return
    else:
        # request.host_url has a trailing slash; produce a reasonable default
        return_url = request.host_url.rstrip("/")

    result = gateway.process_payment(
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        order_id=order_id,
        return_url=return_url + "/payments/complete",
    )

    return jsonify({"payment_id": result["payment_id"], "redirect_url": result["redirect_url"]}), 201


@bp.route("/payments/<payment_id>", methods=["GET"])
def get_payment(payment_id):
    status = gateway.get_payment_status(payment_id)
    if status is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"payment_id": payment_id, "status": status})


@bp.route("/payments/callback", methods=["POST"])
def payment_callback():
    data = request.get_json() or {}
    ok = gateway.handle_callback(data)
    if not ok:
        return jsonify({"error": "invalid_callback"}), 400
    return jsonify({"status": "ok"})


@bp.route("/checkout", methods=["GET"])
def checkout_page():
    # Serve the static checkout page placed under package static/
    return current_app.send_static_file('checkout.html')