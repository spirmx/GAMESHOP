from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.orders.models import Order
from apps.store.models import Category, Game, Product


class AdminPageTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="pass1234",
        )
        self.client.force_login(self.admin_user)

        self.game = Game.objects.create(name="Genshin Impact", slug="genshin-impact")
        self.category = Category.objects.create(type="product", name="Crystal")
        self.product = Product.objects.create(
            game=self.game,
            category=self.category,
            title="Genesis Crystals 300",
            description="Admin test product",
            fulfillment_type="code",
            price="149.00",
            stock=5,
            is_active=True,
        )
        self.order = Order.objects.create(
            buyer=self.admin_user,
            total_price="149.00",
            status="success",
        )

    def test_admin_index_loads_with_custom_branding(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PAPAYA GAME SHOP")

    def test_store_proxy_changelist_loads(self):
        response = self.client.get("/admin/store/tab01productall/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.title)

    def test_store_proxy_change_form_loads(self):
        response = self.client.get(f"/admin/store/tab01productall/{self.product.id}/change/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.title)
        self.assertNotContains(response, "คลังโค้ดสินค้า")

    def test_orders_admin_changelist_loads(self):
        response = self.client.get(reverse("admin:orders_order_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ORD-")
