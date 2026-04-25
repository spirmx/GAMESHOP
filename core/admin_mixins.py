from django.utils.html import format_html
from django.urls import reverse


class PapayaAdminMixin:
    list_per_page = 25

    class Media:
        css = {"all": ("css/admin_papaya.css", "css/admin_store_tabs.css")}

    @staticmethod
    def admin_chip(label, variant="muted"):
        return format_html(
            '<span class="admin-chip admin-chip-{}">{}</span>',
            variant,
            label,
        )

    @staticmethod
    def admin_money(value):
        amount = value if value is not None else 0
        return format_html(
            '<span class="admin-price">฿ {}</span>',
            f"{amount:,.2f}",
        )

    @staticmethod
    def admin_soft(value, extra_class=""):
        classes = f"admin-soft-text {extra_class}".strip()
        return format_html('<span class="{}">{}</span>', classes, value)

    @staticmethod
    def admin_edit_button(url):
        return format_html(
            '<a href="{}" class="admin-icon-button" title="แก้ไขรายการ" aria-label="แก้ไขรายการ">✎</a>',
            url,
        )

    def admin_change_url(self, obj):
        return reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
            args=[obj.pk],
        )
