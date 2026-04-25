from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.utils.html import format_html

from core.admin_mixins import PapayaAdminMixin

from .models import CustomUser


class AdminUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = "ผู้ดูแลระบบ"
        verbose_name_plural = "1. รายชื่อแอดมิน"


class PlayerUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = "ผู้เล่น"
        verbose_name_plural = "2. รายชื่อผู้เล่น"


class CustomUserAdmin(PapayaAdminMixin, UserAdmin):
    list_display = (
        "profile_block",
        "contact_block",
        "role_badge",
        "verify_badge",
        "contact_verify_badge",
        "password_change_stat",
        "online_badge",
        "last_seen_display",
        "is_active",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "is_verified",
        "email_verified",
        "phone_verified",
        "last_seen",
    )
    list_editable = ("is_active",)
    search_fields = ("username", "email", "phone_number", "first_name", "last_name")
    ordering = ("-last_seen", "-date_joined")
    fieldsets = (
        (
            "1. ข้อมูลหลักและความปลอดภัย",
            {
                "fields": (
                    "username",
                    "password",
                    "is_verified",
                    "email_verified",
                    "phone_verified",
                    "password_change_count",
                    "failed_login_attempts",
                    "lockout_until",
                    "profile_image",
                )
            },
        ),
        (
            "2. ข้อมูลติดต่อ",
            {
                "fields": ("first_name", "last_name", "email", "phone_number"),
            },
        ),
        (
            "3. สิทธิ์การใช้งาน",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        (
            "4. สถานะการเข้าใช้งาน",
            {
                "fields": ("last_seen",),
            },
        ),
        (
            "5. ข้อมูลระบบ",
            {
                "classes": ("collapse",),
                "fields": ("last_login", "date_joined"),
            },
        ),
    )
    readonly_fields = ("last_seen", "last_login", "date_joined")

    def profile_block(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip() or "ยังไม่ได้ระบุชื่อจริง"
        return format_html(
            """
            <div class="admin-avatar-name">
                <span class="admin-avatar"><img src="{}" alt="{}"></span>
                <div class="admin-stack">
                    <span class="admin-main-text">{}</span>
                    <span class="admin-sub-text">@{}</span>
                </div>
            </div>
            """,
            obj.avatar_url,
            obj.username,
            full_name,
            obj.username,
        )

    profile_block.short_description = "ผู้ใช้งาน"
    profile_block.admin_order_field = "username"

    def contact_block(self, obj):
        email = obj.email or "ยังไม่ได้ระบุอีเมล"
        phone = obj.phone_number or "ยังไม่ได้ระบุเบอร์โทร"
        return format_html(
            """
            <div class="admin-stack">
                <span class="admin-main-text">{}</span>
                <span class="admin-sub-text">{}</span>
            </div>
            """,
            email,
            phone,
        )

    contact_block.short_description = "ข้อมูลติดต่อ"

    def role_badge(self, obj):
        if obj.is_superuser:
            return self.admin_chip("เจ้าของระบบ", "warning")
        if obj.is_staff:
            return self.admin_chip("แอดมิน", "info")
        return self.admin_chip("ผู้เล่น", "muted")

    role_badge.short_description = "บทบาท"

    def verify_badge(self, obj):
        return (
            self.admin_chip("ยืนยันแล้ว", "success")
            if obj.verification_complete
            else self.admin_chip("ยังไม่ยืนยัน", "danger")
        )

    verify_badge.short_description = "สถานะ Verify"

    def contact_verify_badge(self, obj):
        email_state = "อีเมลผ่าน" if obj.email_verified else "อีเมลรอ"
        phone_state = "เบอร์ผ่าน" if obj.phone_verified else "เบอร์รอ"
        tone = "success" if obj.email_verified and obj.phone_verified else "muted"
        return self.admin_chip(f"{email_state} / {phone_state}", tone)

    contact_verify_badge.short_description = "ยืนยันอีเมล/เบอร์"

    def password_change_stat(self, obj):
        return format_html(
            """
            <div class="admin-stack">
                <span class="admin-main-text">{} ครั้ง</span>
                <span class="admin-sub-text">ล็อกอินผิดสะสม: {} ครั้ง</span>
            </div>
            """,
            obj.password_change_count,
            obj.failed_login_attempts,
        )

    password_change_stat.short_description = "ประวัติรหัสผ่าน"

    def online_badge(self, obj):
        return self.admin_chip("ออนไลน์", "success") if obj.is_online else self.admin_chip("ออฟไลน์", "muted")

    online_badge.short_description = "สถานะตอนนี้"

    def last_seen_display(self, obj):
        if not obj.last_seen:
            return self.admin_soft("ยังไม่มีข้อมูล")
        local_time = timezone.localtime(obj.last_seen)
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

    last_seen_display.short_description = "ใช้งานล่าสุด"
    last_seen_display.admin_order_field = "last_seen"


@admin.register(AdminUser)
class AdminUserAdmin(CustomUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)


@admin.register(PlayerUser)
class PlayerUserAdmin(CustomUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False)


admin.site.register(CustomUser, CustomUserAdmin)
