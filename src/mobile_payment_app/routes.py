from flask import Blueprint, request, jsonify
from .services.naverpay import NaverPayGateway
from .services.barcode import get_barcode_scanner
from .services.auth import auth_service
from flask import current_app
import os

bp = Blueprint("api", __name__, url_prefix="/api")

# Gateway 인스턴스 (환경 변수에서 모드 자동 감지)
gateway = NaverPayGateway(
    client_id=os.environ.get("NAVER_PAY_CLIENT_ID"),
    client_secret=os.environ.get("NAVER_PAY_CLIENT_SECRET"),
    mode=os.environ.get("NAVER_PAY_MODE", "mock")
)
scanner = get_barcode_scanner()


@bp.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok")


@bp.route("/scan", methods=["POST"])
def scan_barcode():
    """바코드 스캔 API"""
    data = request.get_json() or {}
    
    # 필수 필드 검증
    barcode = data.get("barcode")
    if not barcode:
        return jsonify({
            "success": False,
            "error_code": "MISSING_BARCODE",
            "message": "바코드가 필요합니다."
        }), 400
    
    # 바코드 스캔
    store_id = data.get("store_id")
    result = scanner.scan_product(barcode, store_id)
    
    if not result["success"]:
        return jsonify(result), 404 if result["error_code"] == "PRODUCT_NOT_FOUND" else 400
    
    return jsonify(result), 200


@bp.route("/products", methods=["GET"])
def get_products():
    """상품 목록 조회 또는 검색 API"""
    query = request.args.get("q")
    
    if query:
        # 검색
        limit = int(request.args.get("limit", 10))
        products = scanner.search_products(query, limit)
        return jsonify({
            "success": True,
            "query": query,
            "count": len(products),
            "products": products
        }), 200
    else:
        # 전체 목록
        products = scanner.get_all_products()
        return jsonify({
            "success": True,
            "count": len(products),
            "products": products
        }), 200


@bp.route("/products/<barcode>", methods=["GET"])
def get_product_detail(barcode):
    """특정 상품 상세 정보 조회 API"""
    product = scanner.get_product_by_barcode(barcode)
    
    if not product:
        return jsonify({
            "success": False,
            "error_code": "PRODUCT_NOT_FOUND",
            "message": "상품을 찾을 수 없습니다.",
            "barcode": barcode
        }), 404
    
    return jsonify({
        "success": True,
        "product": product
    }), 200


@bp.route("/products/<barcode>/stock", methods=["GET"])
def check_product_stock(barcode):
    """상품 재고 확인 API"""
    quantity = int(request.args.get("quantity", 1))
    result = scanner.check_stock(barcode, quantity)
    
    status_code = 200 if result.get("available") else 400
    return jsonify(result), status_code


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
    
    # 선택적 인증: 토큰이 있으면 사용자 정보 포함
    user_info = auth_service.get_current_user()
    if user_info:
        # 로그인된 사용자의 결제
        order_id = order_id or f"ORDER-{user_info['user_id']}-{data.get('timestamp', '')}"

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

    return jsonify({
        "payment_id": result["payment_id"], 
        "redirect_url": result["redirect_url"],
        "user": user_info.get('username') if user_info else 'guest'
    }), 201


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