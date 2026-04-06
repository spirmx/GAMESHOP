# apps/cart/apps.py

from django.apps import AppConfig

class CartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cart' # ✅ ต้องมี apps. นำหน้า
    verbose_name = 'ระบบตะกร้าสินค้า'