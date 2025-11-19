from flask import Blueprint, jsonify, request
from ..services.qr_scanner import generate_qr_code, scan_qr_code
from ..services.barcode_scanner import generate_barcode, scan_barcode

bp = Blueprint('payments', __name__)

@bp.route("/generate-qr", methods=["POST"])
def create_qr():
    data = request.json
    if 'amount' not in data:
        return jsonify({"error": "Amount is required"}), 400
    qr_code = generate_qr_code(data['amount'])
    return jsonify({"qr_code": qr_code}), 200

@bp.route("/scan-qr", methods=["POST"])
def process_qr():
    data = request.json
    if 'image' not in data:
        return jsonify({"error": "Image is required"}), 400
    result = scan_qr_code(data['image'])
    return jsonify({"result": result}), 200

@bp.route("/generate-barcode", methods=["POST"])
def create_barcode():
    data = request.json
    if 'amount' not in data:
        return jsonify({"error": "Amount is required"}), 400
    barcode = generate_barcode(data['amount'])
    return jsonify({"barcode": barcode}), 200

@bp.route("/scan-barcode", methods=["POST"])
def process_barcode():
    data = request.json
    if 'image' not in data:
        return jsonify({"error": "Image is required"}), 400
    result = scan_barcode(data['image'])
    return jsonify({"result": result}), 200