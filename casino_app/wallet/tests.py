from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Wallet, Transaction
from decimal import Decimal
from rest_framework.test import APIClient

User = get_user_model()


class WalletTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pw')
        self.wallet = Wallet.objects.create(utilisateur=self.user, balance=Decimal('1000.00'))
        self.client = APIClient()

    def test_credit(self):
        balance, tx = self.wallet.credit('250.50', description='test credit')
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1250.50'))
        self.assertEqual(tx.type_transaction, 'depot')
        self.assertEqual(tx.montant, Decimal('250.50'))

    def test_debit(self):
        balance, tx = self.wallet.debit('200.00', description='test debit')
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('800.00'))
        self.assertEqual(tx.type_transaction, 'mise')
        self.assertEqual(tx.montant, Decimal('200.00'))

    def test_debit_insufficient(self):
        with self.assertRaises(ValueError):
            self.wallet.debit('2000.00')

    def test_api_credit_view_requires_auth(self):
        # Unauthenticated calls should be rejected
        resp = self.client.post('/api/wallet/credit/', {'username': 'testuser', 'amount': '10.00'})
        self.assertEqual(resp.status_code, 401)

    def test_api_debit_view_requires_auth(self):
        resp = self.client.post('/api/wallet/debit/', {'username': 'testuser', 'amount': '20.00'})
        self.assertEqual(resp.status_code, 401)

    def test_api_credit_view_authenticated_with_jwt(self):
        # user can credit own wallet with JWT
        resp = self.client.post('/api/token/', {'username': 'testuser', 'password': 'pw'})
        self.assertEqual(resp.status_code, 200)
        access = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.post('/api/wallet/credit/', {'amount': '10.00'})
        self.assertEqual(resp.status_code, 200)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1010.00'))

    def test_api_debit_view_authenticated_with_jwt(self):
        resp = self.client.post('/api/token/', {'username': 'testuser', 'password': 'pw'})
        access = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.post('/api/wallet/debit/', {'amount': '20.00'})
        self.assertEqual(resp.status_code, 200)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('980.00'))

    def test_staff_can_credit_other_user_with_jwt(self):
        staff = User.objects.create_user(username='staff', password='pw')
        staff.is_staff = True
        staff.save()
        resp = self.client.post('/api/token/', {'username': 'staff', 'password': 'pw'})
        access = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.post('/api/wallet/credit/', {'username': 'testuser', 'amount': '50.00'})
        self.assertEqual(resp.status_code, 200)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1050.00'))

    def test_nonstaff_cannot_credit_other_user_with_jwt(self):
        other = User.objects.create_user(username='other', password='pw')
        resp = self.client.post('/api/token/', {'username': 'other', 'password': 'pw'})
        access = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.post('/api/wallet/credit/', {'username': 'testuser', 'amount': '50.00'})
        self.assertEqual(resp.status_code, 403)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))