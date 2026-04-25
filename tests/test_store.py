from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.store.models import Category, Game, Product, ProductCode


class StoreTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create(name="Elden Ring", slug="elden-ring")
        self.cat = Category.objects.create(game=self.game, name="RPG")
        self.product_category = Category.objects.create(type="product", name="Game Code")

    def test_product_creation(self):
        product = Product.objects.create(
            game=self.game,
            category=self.cat,
            title="Runes x999",
            description="Test product",
            price=100.00,
            stock=10,
        )
        self.assertEqual(product.category.game.name, "Elden Ring")

    def test_code_product_keeps_manual_stock_even_when_product_codes_exist(self):
        product = Product.objects.create(
            game=self.game,
            category=self.product_category,
            title="Steam Wallet 300",
            description="Gift code",
            fulfillment_type="code",
            price=Decimal("300.00"),
            stock=7,
        )

        ProductCode.objects.create(product=product, code="STEAM-001")
        ProductCode.objects.create(product=product, code="STEAM-002")
        product.refresh_from_db()
        self.assertEqual(product.stock, 7)

        first_code = ProductCode.objects.filter(product=product).order_by("id").first()
        first_code.mark_as_used()
        product.refresh_from_db()
        self.assertEqual(product.stock, 7)

    def test_account_product_helpers_reflect_secondary_input_state(self):
        product = Product.objects.create(
            game=self.game,
            category=self.product_category,
            title="Account Topup",
            description="Topup service",
            fulfillment_type="account",
            account_input_secondary_label="Server",
            price=Decimal("59.00"),
            stock=5,
        )

        self.assertTrue(product.is_account_product)
        self.assertFalse(product.is_code_product)
        self.assertTrue(product.has_secondary_input)

    def test_product_detail_recommends_best_matching_products_first(self):
        product = Product.objects.create(
            game=self.game,
            category=self.product_category,
            title="Main Product",
            description="Main",
            price=Decimal("300.00"),
            stock=5,
            sold_count=10,
        )
        best_match = Product.objects.create(
            game=self.game,
            category=self.product_category,
            title="Best Match",
            description="Same game and category",
            price=Decimal("250.00"),
            stock=8,
            sold_count=40,
        )
        weaker_match = Product.objects.create(
            game=self.game,
            category=self.product_category,
            title="Weaker Match",
            description="Same game but low stock score",
            price=Decimal("420.00"),
            stock=0,
            sold_count=2,
        )
        other_game = Game.objects.create(name="Valorant", slug="valorant")
        Product.objects.create(
            game=other_game,
            category=self.product_category,
            title="Other Game Product",
            description="Other",
            price=Decimal("199.00"),
            stock=9,
            sold_count=5,
        )

        response = self.client.get(reverse("product_detail", args=[product.id]))

        self.assertEqual(response.status_code, 200)
        recommended_products = response.context["recommended_products"]
        self.assertGreaterEqual(len(recommended_products), 2)
        self.assertEqual(recommended_products[0].id, best_match.id)
        self.assertEqual(recommended_products[1].id, weaker_match.id)
        self.assertIn("เกมเดียวกัน", recommended_products[0].recommendation_reason)
