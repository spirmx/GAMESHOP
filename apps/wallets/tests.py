from django.test import TestCase
from django.urls import reverse

from apps.users.models import CustomUser


class TopUpIdentityGateTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="WalletUser2026",
            email="walletuser@gmail.com",
            password="securepass8",
            phone_number="0891234567",
        )
        self.client.force_login(self.user)

    def test_top_up_redirects_when_identity_profile_is_incomplete(self):
        response = self.client.get(reverse("wallets:top_up"))

        self.assertRedirects(response, reverse("users:profile_edit"))

    def test_top_up_redirects_when_not_verified(self):
        self.user.first_name = "Sora"
        self.user.last_name = "Test"
        self.user.save(update_fields=["first_name", "last_name"])

        response = self.client.get(reverse("wallets:top_up"))

        self.assertRedirects(response, reverse("users:profile_edit"))

    def test_top_up_allows_verified_user(self):
        self.user.first_name = "Sora"
        self.user.last_name = "Test"
        self.user.is_verified = True
        self.user.save(update_fields=["first_name", "last_name", "is_verified"])

        response = self.client.get(reverse("wallets:top_up"))

        self.assertEqual(response.status_code, 200)
