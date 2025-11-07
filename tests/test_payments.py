import unittest
from src.mobile_payment_app.api.payments import create_payment, get_payment

class TestPayments(unittest.TestCase):

    def test_create_payment(self):
        # Test creating a payment
        payment_data = {
            'amount': 100,
            'currency': 'USD',
            'method': 'credit_card'
        }
        response = create_payment(payment_data)
        self.assertEqual(response['status'], 'success')
        self.assertIn('payment_id', response)

    def test_get_payment(self):
        # Test retrieving a payment
        payment_id = '12345'
        response = get_payment(payment_id)
        self.assertEqual(response['status'], 'success')
        self.assertEqual(response['payment_id'], payment_id)

if __name__ == '__main__':
    unittest.main()