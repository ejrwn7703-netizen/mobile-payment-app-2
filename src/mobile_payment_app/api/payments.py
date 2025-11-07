from flask import Blueprint, request, jsonify

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/payments', methods=['POST'])
def create_payment():
    data = request.json
    # Here you would typically validate the data and create a payment
    return jsonify({"message": "Payment created", "data": data}), 201

@payments_bp.route('/payments/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    # Here you would typically retrieve the payment details by payment_id
    return jsonify({"message": "Payment details", "payment_id": payment_id})