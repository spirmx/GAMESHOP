from django.core.management.base import BaseCommand

from apps.store.image_utils import optimize_uploaded_image
from apps.store.models import Game, Product
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Optimize existing game, product, and profile images for faster storefront loading."

    def handle(self, *args, **options):
        game_count = 0
        product_count = 0
        user_count = 0

        for game in Game.objects.exclude(logo="").exclude(logo__isnull=True):
            optimize_uploaded_image(game.logo, max_size=(720, 720), quality=84, force=True)
            game.save(update_fields=["logo"])
            game_count += 1

        for product in Product.objects.exclude(image="").exclude(image__isnull=True):
            optimize_uploaded_image(product.image, max_size=(1400, 1400), quality=84, force=True)
            product.save(update_fields=["image"])
            product_count += 1

        for user in CustomUser.objects.exclude(profile_image="").exclude(profile_image__isnull=True):
            optimize_uploaded_image(user.profile_image, max_size=(640, 640), quality=82, force=True)
            user.save(update_fields=["profile_image"])
            user_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Optimized images: games={game_count}, products={product_count}, profiles={user_count}"
            )
        )
