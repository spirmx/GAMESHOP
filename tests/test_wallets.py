from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.wallets.models import Wallet, WalletTransaction


class WalletTests(TestCase):
    def test_wallet_created_automatically_for_new_user(self):
        user = get_user_model().objects.create_user(username="wallet_user", password="pass1234")

        self.assertTrue(Wallet.objects.filter(user=user).exists())
        self.assertEqual(user.wallet.balance, Decimal("0.00"))

    def test_wallet_transaction_string_contains_username(self):
        user = get_user_model().objects.create_user(username="wallet_tx_user", password="pass1234")
        transaction = WalletTransaction.objects.create(
            wallet=user.wallet,
            transaction_type="DEPOSIT",
            amount=Decimal("250.00"),
            note="Top up",
        )

        self.assertIn("wallet_tx_user", str(transaction))
