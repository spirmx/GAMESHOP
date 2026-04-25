from django.test import TestCase
from django.urls import reverse

from apps.users.forms import SignUpForm
from apps.users.models import CustomUser


class SignUpFormValidationTests(TestCase):
    def test_signup_form_accepts_english_and_numeric_username(self):
        form = SignUpForm(
            data={
                "username": "Player2026",
                "email": "player2026@gmail.com",
                "phone_number": "0891234567",
                "password1": "securepass8",
                "password2": "securepass8",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_signup_form_rejects_special_character_username(self):
        form = SignUpForm(
            data={
                "username": "player_2026",
                "email": "player2026@gmail.com",
                "phone_number": "0891234567",
                "password1": "securepass8",
                "password2": "securepass8",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_signup_form_rejects_invalid_email_format(self):
        form = SignUpForm(
            data={
                "username": "Player2026",
                "email": "player2026@gmail",
                "phone_number": "0891234567",
                "password1": "securepass8",
                "password2": "securepass8",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_signup_form_rejects_invalid_phone(self):
        form = SignUpForm(
            data={
                "username": "Player2026",
                "email": "player2026@gmail.com",
                "phone_number": "08A123",
                "password1": "securepass8",
                "password2": "securepass8",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("phone_number", form.errors)


class LoginSecurityTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="VerifyUser2026",
            email="verifyuser@gmail.com",
            password="securepass8",
            phone_number="0891234567",
        )

    def test_failed_login_three_times_sets_cooldown(self):
        for _ in range(3):
            self.client.post(
                reverse("users:login"),
                data={"username": self.user.username, "password": "wrongpass"},
            )

        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 3)
        self.assertIsNotNone(self.user.lockout_until)

    def test_successful_login_resets_security_counters(self):
        self.user.failed_login_attempts = 2
        self.user.save(update_fields=["failed_login_attempts"])

        response = self.client.post(
            reverse("users:login"),
            data={"username": self.user.username, "password": "securepass8"},
        )

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)


class ForgotPasswordFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="ResetUser2026",
            email="resetuser@gmail.com",
            password="securepass8",
            phone_number="0891234567",
        )

    def test_forgot_password_updates_password_and_counter(self):
        session = self.client.session
        session["reset_captcha"] = {"question": "3 + 4 = ?", "answer": "7"}
        session.save()

        verify_response = self.client.post(
            reverse("users:forgot_password"),
            data={
                "identifier": "ResetUser2026",
                "reset_action": "verify_identity",
                "captcha_answer": "7",
            },
        )

        self.assertRedirects(
            verify_response,
            f"{reverse('users:forgot_password')}?identifier=ResetUser2026",
        )

        response = self.client.post(
            reverse("users:forgot_password"),
            data={
                "identifier": "ResetUser2026",
                "reset_action": "change_password",
                "new_password1": "newsecurepass8",
                "new_password2": "newsecurepass8",
            },
        )

        self.assertRedirects(response, reverse("users:login"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.password_change_count, 1)
        self.assertTrue(self.user.check_password("newsecurepass8"))

    def test_forgot_password_allows_authenticated_user_to_finish_reset_flow(self):
        self.client.force_login(self.user)
        session = self.client.session
        session["reset_captcha"] = {"question": "1 + 2 = ?", "answer": "3"}
        session.save()

        verify_response = self.client.post(
            reverse("users:forgot_password"),
            data={
                "identifier": "ResetUser2026",
                "reset_action": "verify_identity",
                "captcha_answer": "3",
            },
        )

        self.assertRedirects(
            verify_response,
            f"{reverse('users:forgot_password')}?identifier=ResetUser2026",
        )

        reset_response = self.client.post(
            reverse("users:forgot_password"),
            data={
                "identifier": "ResetUser2026",
                "reset_action": "change_password",
                "new_password1": "anotherpass88",
                "new_password2": "anotherpass88",
            },
        )

        self.assertRedirects(reset_response, reverse("users:login"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("anotherpass88"))


class ProfileVerificationTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="ProfileUser2026",
            email="profileuser@gmail.com",
            password="securepass8",
            phone_number="0891234567",
        )
        self.client.force_login(self.user)

    def test_profile_edit_with_complete_data_and_captcha_sets_verified(self):
        session = self.client.session
        session["profile_captcha"] = {"question": "5 + 7 = ?", "answer": "12"}
        session.save()

        response = self.client.post(
            reverse("users:profile_edit"),
            data={
                "first_name": "Sora",
                "last_name": "Test",
                "email": "profileuser@gmail.com",
                "phone_number": "0891234567",
                "captcha_answer": "12",
            },
        )

        self.assertRedirects(response, reverse("users:profile"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertTrue(self.user.phone_verified)
        self.assertTrue(self.user.verification_complete)
