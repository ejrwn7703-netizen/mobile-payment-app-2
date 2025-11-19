from datetime import datetime

class Transaction:
    def __init__(self, transaction_id, amount, user_id, payment_method, status='pending'):
        self.transaction_id = transaction_id
        self.amount = amount
        self.user_id = user_id
        self.payment_method = payment_method
        self.status = status
        self.timestamp = datetime.utcnow()

    def complete_transaction(self):
        self.status = 'completed'

    def cancel_transaction(self):
        self.status = 'canceled'

    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'user_id': self.user_id,
            'payment_method': self.payment_method,
            'status': self.status,
            'timestamp': self.timestamp.isoformat()
        }