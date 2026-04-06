from django.contrib import admin
from .models import Wallet, WalletTransaction

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_role', 'balance')
    search_fields = ('user__username', 'user__email')

    def get_role(self, obj):
        return "ผู้ขาย (Admin)" if obj.user.is_staff else "Player"
    get_role.short_description = 'Role'

    def get_readonly_fields(self, request, obj=None):
        # 🚨 ถ้าผู้ใช้คนนี้มีการทำรายการผ่าน PromptPay/TrueMoney ให้ Lock ช่องยอดเงิน (ห้ามแอดมินแก้ตรงๆ)
        if obj and WalletTransaction.objects.filter(wallet=obj, transaction_type='EXTERNAL').exists():
            return ['balance']
        return []

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')