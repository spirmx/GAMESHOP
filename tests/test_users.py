from django.test import TestCase
from django.contrib.auth import get_user_model

class UserTests(TestCase):
    def test_create_custom_user(self):
        User = get_user_model()
        user = User.objects.create_user(username='arm_tester', password='password123')
        self.assertEqual(user.username, 'arm_tester')
        self.assertTrue(user.is_active)
        self.assertTrue(hasattr(user, 'wallet'))