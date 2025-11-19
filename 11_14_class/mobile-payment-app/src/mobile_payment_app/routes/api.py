from flask import Blueprint, jsonify, request
from ..services.gps import get_user_location
from ..services.qr_scanner import generate_qr_code, scan_qr_code
from ..services.barcode_scanner import generate_barcode, scan_barcode

bp = Blueprint('api', __name__)

@bp.route("/api/location", methods=["GET"])
def location():
    user_location = get_user_location()
    return jsonify(location=user_location)

@bp.route("/api/qr/generate", methods=["POST"])
def qr_generate():
    data = request.json
    qr_code = generate_qr_code(data.get("info"))
    return jsonify(qr_code=qr_code)

@bp.route("/api/qr/scan", methods=["POST"])
def qr_scan():
    image = request.files.get("image")
    scanned_data = scan_qr_code(image)
    return jsonify(scanned_data=scanned_data)

@bp.route("/api/barcode/generate", methods=["POST"])
def barcode_generate():
    data = request.json
    barcode = generate_barcode(data.get("info"))
    return jsonify(barcode=barcode)

@bp.route("/api/barcode/scan", methods=["POST"])
def barcode_scan():
    image = request.files.get("image")
    scanned_data = scan_barcode(image)
    return jsonify(scanned_data=scanned_data)