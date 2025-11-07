class PaymentGateway:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def process_payment(self, amount, currency, payment_method):
        # Logic to process payment through the gateway
        pass

    def refund_payment(self, transaction_id, amount):
        # Logic to refund a payment
        pass

    def get_payment_status(self, transaction_id):
        # Logic to get the status of a payment
        pass