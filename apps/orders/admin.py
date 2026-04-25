from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from core.admin_mixins import PapayaAdminMixin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "price", "subtotal_display")
    fields = ("product", "quantity", "price", "subtotal_display")

    def subtotal_display(self, obj):
        return f"฿ {obj.subtotal:,.2f}"

    subtotal_display.short_description = "รวมรายการ"


@admin.register(Order)
class OrderAdmin(PapayaAdminMixin, admin.ModelAdmin):
    list_display = (
        "order_code",
        "buyer_block",
        "items_summary",
        "total_price_display",
        "status_badge",
        "created_at_display",
    )
    list_filter = ("status", "created_at")
    search_fields = ("buyer__username", "buyer__email", "id")
    ordering = ("-created_at",)
    inlines = [OrderItemInline]

    def order_code(self, obj):
        return self.admin_chip(f"ORD-{obj.id:04d}", "id")

    order_code.short_description = "เลขที่คำสั่งซื้อ"
    order_code.admin_order_field = "id"

    def buyer_block(self, obj):
        email = obj.buyer.email or "ไม่มีอีเมล"
        return format_html(
            """
            <div class="admin-stack">
                <span class="admin-main-text">{}</span>
                <span class="admin-sub-text">{}</span>
            </div>
            """,
            obj.buyer.username,
            email,
        )

    buyer_block.short_description = "ลูกค้า"
    buyer_block.admin_order_field = "buyer__username"

    def items_summary(self, obj):
        count = obj.items.count()
        suffix = "รายการ" if count else "ยังไม่มีสินค้า"
        return self.admin_chip(f"{count} {suffix}", "info" if count else "muted")

    items_summary.short_description = "สินค้าในออเดอร์"

    def total_price_display(self, obj):
        return self.admin_money(obj.total_price)

    total_price_display.short_description = "ยอดรวม"
    total_price_display.admin_order_field = "total_price"

    def status_badge(self, obj):
        mapping = {
            "success": ("สำเร็จ", "success"),
            "pending": ("รอดำเนินการ", "warning"),
            "failed": ("ล้มเหลว", "danger"),
        }
        label, variant = mapping.get(obj.status, (obj.get_status_display(), "muted"))
        return self.admin_chip(label, variant)

    status_badge.short_description = "สถานะ"
    status_badge.admin_order_field = "status"

    def created_at_display(self, obj):
        local_time = timezone.localtime(obj.created_at)
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

    created_at_display.short_description = "เวลาสั่งซื้อ"
    created_at_display.admin_order_field = "created_at"
