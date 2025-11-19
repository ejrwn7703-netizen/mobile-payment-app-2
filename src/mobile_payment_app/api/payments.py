from flask import Blueprint, request, jsonify

bp = Blueprint("payments", __name__, url_prefix="/api/payments")

def _create_payment_logic(data: dict) -> dict:
    """
    결제 생성 비즈니스 로직(테스트용/라우트용 공용).
    """
    payment_id = "mock-payment-id"
    return {
        "id": payment_id,
        "payment_id": payment_id,  # 테스트가 기대하는 키 추가
        "status": "success",
        "amount": data.get("amount"),
        "currency": data.get("currency"),
        "method": data.get("method")
    }

def create_payment(data: dict) -> dict:
    """
    테스트나 내부 호출이 사용할 수 있는 함수.
    Flask 컨텍스트 불필요.
    """
    return _create_payment_logic(data)

@bp.route("", methods=["POST"])
def create_payment_route():
    data = request.get_json() or {}
    result = _create_payment_logic(data)
    return jsonify(result), 201

def _get_payment_logic(payment_id: str) -> dict:
    """
    결제 조회 비즈니스 로직(테스트/라우트 공용).
    """
    return {
        "status": "success",
        "message": "Payment details",
        "payment_id": payment_id
    }

def get_payment(payment_id: str) -> dict:
    """
    테스트나 내부 호출이 사용할 수 있는 함수(Flask 컨텍스트 불필요).
    """
    return _get_payment_logic(payment_id)

@bp.route("/<payment_id>", methods=["GET"])
def get_payment_route(payment_id: str):
    result = _get_payment_logic(payment_id)
    return jsonify(result)