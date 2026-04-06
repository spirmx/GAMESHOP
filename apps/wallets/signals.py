from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Wallet

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    # ถ้ามีการสร้าง User ใหม่ (created=True) ให้สร้าง Wallet คู่กันทันที
    if created:
        Wallet.objects.create(user=instance)