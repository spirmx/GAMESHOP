from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from core.admin_mixins import PapayaAdminMixin

from .models import Wallet, WalletTransaction


@admin.register(Wallet)
class WalletAdmin(PapayaAdminMixin, admin.ModelAdmin):
    list_display = ("user_block", "role_badge", "balance_display", "wallet_status")
    search_fields = ("user__username", "user__email")
    ordering = ("-balance", "user__username")

    def user_block(self, obj):
        return format_html(
            """
            <div class="admin-stack">
                <span class="admin-main-text">{}</span>
                <span class="admin-sub-text">{}</span>
            </div>
            """,
            obj.user.username,
            obj.user.email or "ยังไม่ระบุอีเมล",
        )

    user_block.short_description = "เจ้าของกระเป๋า"
    user_block.admin_order_field = "user__username"

    def role_badge(self, obj):
        if obj.user.is_superuser:
            return self.admin_chip("เจ้าของระบบ", "warning")
        if obj.user.is_staff:
            return self.admin_chip("แอดมิน", "info")
        return self.admin_chip("ผู้เล่น", "muted")

    role_badge.short_description = "ประเภทผู้ใช้"

    def balance_display(self, obj):
        return self.admin_money(obj.balance)

    balance_display.short_description = "ยอดเงินคงเหลือ"
    balance_display.admin_order_field = "balance"

    def wallet_status(self, obj):
        if obj.balance > 0:
            return self.admin_chip("มีเงินคงเหลือ", "success")
        return self.admin_chip("ยอดคงเหลือ 0", "muted")

    wallet_status.short_description = "สถานะกระเป๋า"

    def get_readonly_fields(self, request, obj=None):
        if obj and WalletTransaction.objects.filter(wallet=obj, transaction_type="EXTERNAL").exists():
            return ["balance"]
        return []


@admin.register(WalletTransaction)
class WalletTransactionAdmin(PapayaAdminMixin, admin.ModelAdmin):
    list_display = (
        "wallet_owner",
        "transaction_badge",
        "amount_display",
        "note_display",
        "timestamp_display",
    )
    list_filter = ("transaction_type", "timestamp")
    search_fields = ("wallet__user__username", "wallet__user__email", "note")
    ordering = ("-timestamp",)

    def wallet_owner(self, obj):
        return format_html(
            """
            <div class="admin-stack">
                <span class="admin-main-text">{}</span>
                <span class="admin-sub-text">{}</span>
            </div>
            """,
            obj.wallet.user.username,
            obj.wallet.user.email or "ยังไม่ระบุอีเมล",
        )

    wallet_owner.short_description = "เจ้าของรายการ"
    wallet_owner.admin_order_field = "wallet__user__username"

    def transaction_badge(self, obj):
        mapping = {
            "DEPOSIT": ("เติมเงิน", "success"),
            "WITHDRAW": ("ตัดยอด / ถอนเงิน", "danger"),
        }
        label, variant = mapping.get(obj.transaction_type, (obj.get_transaction_type_display(), "muted"))
        return self.admin_chip(label, variant)

    transaction_badge.short_description = "ประเภทรายการ"
    transaction_badge.admin_order_field = "transaction_type"

    def amount_display(self, obj):
        return self.admin_money(obj.amount)

    amount_display.short_description = "จำนวนเงิน"
    amount_display.admin_order_field = "amount"

    def note_display(self, obj):
        return self.admin_soft(obj.note or "ไม่มีหมายเหตุ")

    note_display.short_description = "หมายเหตุ"

    def timestamp_display(self, obj):
        local_time = timezone.localtime(obj.timestamp)
        return format_html(
            """
            <div class="admin-stack">
                <span class="admin-main-text">{}</span>
                <span class="admin-sub-text">{}</span>
            </div>
            """,
            local_time.strftime("%d/%m/%Y"),
            local_time.strftime("%H:%M:%S น."),
        )

    timestamp_display.short_description = "เวลาทำรายการ"
    timestamp_display.admin_order_field = "timestamp"
