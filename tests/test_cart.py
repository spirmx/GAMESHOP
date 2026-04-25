from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from apps.cart.models import Cart, CartItem
from apps.store.models import Category, Game, Product


class CartFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="cart_user",
            password="pass1234",
        )
        self.client.force_login(self.user)

        self.game = Game.objects.create(name="Valorant", slug="valorant")
        self.category = Category.objects.create(type="product", name="Topup")

    def test_add_code_product_to_cart_creates_item(self):
        product = Product.objects.create(
            game=self.game,
            category=self.category,
            title="VP 420",
            description="Code delivery",
            fulfillment_type="code",
            price="129.00",
            stock=5,
            is_active=True,
        )

        response = self.client.post(reverse("cart:add_to_cart", args=[product.id]), {"quantity": "1"})

        self.assertRedirects(response, reverse("cart:cart_detail"))
        cart = Cart.objects.get(user=self.user)
        item = CartItem.objects.get(cart=cart, product=product)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.delivery_data, {})

    def test_add_account_product_requires_delivery_data(self):
        product = Product.objects.create(
            game=self.game,
            category=self.category,
            title="Topup 300",
            description="Account delivery",
            fulfillment_type="account",
            price="99.00",
            stock=10,
            is_active=True,
        )

        response = self.client.post(
            reverse("cart:add_to_cart", args=[product.id]),
            {"quantity": "1"},
            follow=True,
        )

        self.assertTrue(Cart.objects.filter(user=self.user).exists())
        self.assertFalse(Cart.objects.get(user=self.user).items.exists())
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertTrue(any("Please enter" in message for message in messages))

    def test_add_account_product_saves_delivery_data(self):
        product = Product.objects.create(
            game=self.game,
            category=self.category,
            title="Topup 650",
            description="Account delivery",
            fulfillment_type="account",
            account_input_label="Player ID",
            account_input_secondary_label="Server",
            price="199.00",
            stock=10,
            is_active=True,
        )

        response = self.client.post(
            reverse("cart:add_to_cart", args=[product.id]),
            {
                "quantity": "1",
                "account_input_value": "UID-456789",
                "account_input_secondary_value": "SEA-1",
            },
        )

        self.assertRedirects(response, reverse("cart:cart_detail"))
        cart = Cart.objects.get(user=self.user)
        item = CartItem.objects.get(cart=cart, product=product)
        self.assertEqual(item.delivery_data["primary_value"], "UID-456789")
        self.assertEqual(item.delivery_data["secondary_value"], "SEA-1")

    def test_decrease_quantity_removes_item_when_reaches_zero(self):
        product = Product.objects.create(
            game=self.game,
            category=self.category,
            title="VP 900",
            description="Code delivery",
            fulfillment_type="code",
            price="249.00",
            stock=3,
            is_active=True,
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        response = self.client.post(reverse("cart:decrease_quantity", args=[product.id]), follow=True)

        self.assertRedirects(response, reverse("cart:cart_detail"))
        self.assertFalse(cart.items.exists())
