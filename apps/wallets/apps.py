from django.apps import AppConfig

class WalletsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.wallets'
    verbose_name = 'ระบบกระเป๋าเงิน'

    def ready(self):
        # นำเข้า Signals เพื่อให้ระบบสร้าง Wallet อัตโนมัติเมื่อมี User ใหม่
        import apps.wallets.signals