from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem
from apps.store.models import Category, Game, Product
from apps.wallets.models import Wallet


class OrderFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="buyer01",
            password="pass1234",
        )
        self.client.force_login(self.user)

        self.wallet = Wallet.objects.get(user=self.user)
        self.wallet.balance = Decimal("5000.00")
        self.wallet.save(update_fields=["balance"])

        self.game = Game.objects.create(name="Free Fire", slug="free-fire")
        self.product_category = Category.objects.create(type="product", name="Gift Code")

    def test_place_order_for_code_product_reduces_demo_stock_and_creates_order_item(self):
        product = Product.objects.create(
            game=self.game,
            category=self.product_category,
            title="Free Fire Weekly Card",
            description="Weekly card code",
            fulfillment_type="code",
            price=Decimal("150.00"),
            stock=5,
            is_active=True,
        )

        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        response = self.client.post(reverse("orders:place_order"))

        self.assertRedirects(response, reverse("orders:order_detail", args=[1]))

        order = Order.objects.get()
        order_item = OrderItem.objects.get(order=order)
        product.refresh_from_db()
        self.wallet.refresh_from_db()

        self.assertEqual(order.status, "success")
        self.assertEqual(order_item.fulfillment_type, "code")
        self.assertEqual(order_item.delivered_code_list, [])
        self.assertEqual(product.stock, 3)
        self.assertEqual(product.sold_count, 2)
        self.assertEqual(self.wallet.balance, Decimal("4700.00"))
        self.assertFalse(cart.items.exists())

    def test_place_order_for_account_product_uses_delivery_data_and_reduces_stock(self):
        product = Product.objects.create(
            game=self.game,
            category=self.product_category,
            title="Diamond Topup 500",
            description="Topup package",
            fulfillment_type="account",
            account_input_label="Player ID",
            account_input_help="Use for in-game top up",
            price=Decimal("299.00"),
            stock=8,
            is_active=True,
        )

        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
            delivery_data={
                "primary_label": "Player ID",
                "primary_value": "UID-778899",
                "primary_help": "Use for in-game top up",
            },
        )

        response = self.client.post(reverse("orders:place_order"))

        self.assertRedirects(response, reverse("orders:order_detail", args=[1]))

        order_item = OrderItem.objects.get()
        product.refresh_from_db()
        self.wallet.refresh_from_db()

        self.assertEqual(order_item.fulfillment_type, "account")
        self.assertEqual(order_item.delivery_data["primary_value"], "UID-778899")
        self.assertEqual(order_item.delivered_codes, "")
        self.assertEqual(product.stock, 7)
        self.assertEqual(product.sold_count, 1)
        self.assertEqual(self.wallet.balance, Decimal("4701.00"))

    def test_place_order_blocks_account_product_without_required_delivery_data(self):
        product = Product.objects.create(
            game=self.game,
            category=self.product_category,
            title="Diamond Topup 100",
            description="Topup package",
            fulfillment_type="account",
            account_input_label="Player ID",
            price=Decimal("99.00"),
            stock=4,
            is_active=True,
        )

        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=product, quantity=1, delivery_data={})

        response = self.client.post(reverse("orders:place_order"), follow=True)

        product.refresh_from_db()
        self.wallet.refresh_from_db()

        self.assertRedirects(response, reverse("cart:cart_detail"))
        self.assertFalse(Order.objects.exists())
        self.assertEqual(product.stock, 4)
        self.assertEqual(self.wallet.balance, Decimal("5000.00"))
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertTrue(any(product.title in message for message in messages))
