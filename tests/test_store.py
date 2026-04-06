from django.test import TestCase
from apps.store.models import Game, Category, Product

class StoreTests(TestCase):
    def setUp(self):
        self.game = Game.objects.create(name="Elden Ring", slug="elden-ring")
        self.cat = Category.objects.create(game=self.game, name="RPG")

    def test_product_creation(self):
        product = Product.objects.create(
            category=self.cat, title="Runes x999", price=100.00, stock=10
        )
        self.assertEqual(product.category.game.name, "Elden Ring")