def validate_payment_data(payment_data):
    if not isinstance(payment_data, dict):
        raise ValueError("Payment data must be a dictionary.")

    required_fields = ['amount', 'currency', 'payment_method']
    for field in required_fields:
        if field not in payment_data:
            raise ValueError(f"Missing required field: {field}")

    if payment_data['amount'] <= 0:
        raise ValueError("Amount must be greater than zero.")

    if not isinstance(payment_data['currency'], str) or len(payment_data['currency']) != 3:
        raise ValueError("Currency must be a three-letter string.")

    if payment_data['payment_method'] not in ['credit_card', 'paypal', 'bank_transfer']:
        raise ValueError("Invalid payment method. Must be one of: credit_card, paypal, bank_transfer.")

    return True