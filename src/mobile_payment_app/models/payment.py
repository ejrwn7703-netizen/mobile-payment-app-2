class Payment:
    def __init__(self, amount, currency, payment_method, status='pending'):
        self.amount = amount
        self.currency = currency
        self.payment_method = payment_method
        self.status = status

    def process_payment(self):
        # Logic to process the payment
        pass

    def refund_payment(self):
        # Logic to refund the payment
        pass

    def update_status(self, new_status):
        self.status = new_status

    def __repr__(self):
        return f"<Payment(amount={self.amount}, currency={self.currency}, method={self.payment_method}, status={self.status})>"