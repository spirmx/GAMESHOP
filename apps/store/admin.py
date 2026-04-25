from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html

from core.admin_mixins import PapayaAdminMixin

from .models import Category, Game, Product


admin.site.site_header = "PAPAYA GAME SHOP หลังบ้าน"
admin.site.site_title = "PAPAYA GAME SHOP หลังบ้าน"
admin.site.index_title = "ระบบจัดการร้านค้า"


class BaseTabAdmin(PapayaAdminMixin, admin.ModelAdmin):
    """ฐานกลางสำหรับเมนูจัดการข้อมูลใน Django Admin"""

    def display_custom_id(self, obj):
        prefix = ""
        if isinstance(obj, Category):
            if obj.type == "platform":
                prefix = "X"
            elif obj.type == "genre":
                prefix = "M"
            elif obj.type == "product":
                prefix = "P"
        return self.admin_chip(f"{prefix}{obj.id}", "id")

    display_custom_id.short_description = "รหัส"


class GameBaseAdmin(BaseTabAdmin):
    list_display = ("game_code", "game_block", "genre", "platform", "game_status", "edit_action")
    list_filter = ("platform", "genre", "is_active")
    search_fields = ("name", "genre__name", "platform__name")
    ordering = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    fields = ("name", "genre", "platform", "slug", "logo", "is_active", "description")

    def game_code(self, obj):
        return self.admin_chip(f"#{obj.id:04d}", "id")

    game_code.short_description = "รหัส"
    game_code.admin_order_field = "id"

    def game_block(self, obj):
        description = (obj.description or "").strip()
        preview = description[:70] + ("..." if len(description) > 70 else "")
        preview = preview or "ยังไม่มีรายละเอียดเกมเพิ่มเติม"

        image_html = ""
        if obj.logo and hasattr(obj.logo, "url"):
            image_html = format_html(
                '<span class="admin-avatar"><img src="{}" alt="{}"></span>',
                obj.logo.url,
                obj.name,
            )

        return format_html(
            """
            <div class="admin-avatar-name">
                {}
                <div class="admin-stack">
                    <span class="admin-main-text">{}</span>
                    <span class="admin-sub-text">{}</span>
                </div>
            </div>
            """,
            image_html,
            obj.name,
            preview,
        )

    game_block.short_description = "รายชื่อเกม"
    game_block.admin_order_field = "name"

    def edit_action(self, obj):
        return self.admin_edit_button(self.admin_change_url(obj))

    edit_action.short_description = "แก้ไข"

    def game_status(self, obj):
        if obj.is_active:
            return self.admin_chip("พร้อมขาย", "success")
        return self.admin_chip("ไม่พร้อมขาย", "muted")

    game_status.short_description = "สถานะ"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "genre":
            kwargs["queryset"] = Category.objects.filter(type="genre")
        if db_field.name == "platform":
            kwargs["queryset"] = Category.objects.filter(type="platform")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProductBaseAdmin(BaseTabAdmin):
    list_display = (
        "product_code",
        "title_block",
        "game",
        "category",
        "fulfillment_badge",
        "formatted_price",
        "formatted_stock",
        "formatted_sold_count",
        "product_status",
        "edit_action",
    )
    list_filter = ("game", "category", "is_active")
    search_fields = ("title", "game__name", "category__name", "description")
    ordering = ("game__name", "category__name", "title")
    readonly_fields = ("sold_count",)
    fields = (
        "game",
        "category",
        "title",
        "description",
        "fulfillment_type",
        "price",
        "image",
        "stock",
        "sold_count",
        "is_active",
    )

    def product_code(self, obj):
        return self.admin_chip(f"#{obj.id:04d}", "id")

    product_code.short_description = "รหัสสินค้า"
    product_code.admin_order_field = "id"

    def title_block(self, obj):
        description = (obj.description or "").strip()
        preview = description[:70] + ("..." if len(description) > 70 else "")
        preview = preview or "ยังไม่มีรายละเอียดสินค้าเพิ่มเติม"

        image_html = ""
        if obj.image and hasattr(obj.image, "url"):
            image_html = format_html(
                '<span class="admin-avatar"><img src="{}" alt="{}"></span>',
                obj.image.url,
                obj.title,
            )

        return format_html(
            """
            <div class="admin-avatar-name">
                {}
                <div class="admin-stack">
                    <span class="admin-main-text">{}</span>
                    <span class="admin-sub-text">{}</span>
                </div>
            </div>
            """,
            image_html,
            obj.title,
            preview,
        )

    title_block.short_description = "รายการสินค้า"
    title_block.admin_order_field = "title"

    def formatted_price(self, obj):
        return self.admin_money(obj.price)

    formatted_price.short_description = "ราคา"
    formatted_price.admin_order_field = "price"

    def fulfillment_badge(self, obj):
        if obj.is_code_product:
            return self.admin_chip("โค้ด / คีย์สินค้า", "info")
        return self.admin_chip("เติมเข้าบัญชีเกม", "warning")

    fulfillment_badge.short_description = "รูปแบบสินค้า"
    fulfillment_badge.admin_order_field = "fulfillment_type"

    def formatted_stock(self, obj):
        if obj.stock > 0:
            return self.admin_chip(f"เหลือ {obj.stock} ชิ้น", "info")
        return self.admin_chip("หมดสต็อก", "danger")

    formatted_stock.short_description = "สต็อก"
    formatted_stock.admin_order_field = "stock"

    def formatted_sold_count(self, obj):
        return self.admin_chip(f"ขายแล้ว {obj.sold_count} ชิ้น", "warning")

    formatted_sold_count.short_description = "จำนวนที่ขายได้"
    formatted_sold_count.admin_order_field = "sold_count"

    def product_status(self, obj):
        if not obj.game_is_available_for_sale:
            return self.admin_chip("ไม่พร้อมขาย", "muted")
        if not obj.is_active:
            return self.admin_chip("ไม่พร้อมขาย", "muted")
        if obj.stock <= 0:
            return self.admin_chip("สินค้าหมด", "danger")
        return self.admin_chip("พร้อมขาย", "success")

    product_status.short_description = "สถานะสินค้า"
    product_status.admin_order_field = "is_active"

    def edit_action(self, obj):
        return self.admin_edit_button(self.admin_change_url(obj))

    edit_action.short_description = "แก้ไข"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            kwargs["queryset"] = Category.objects.filter(type="product")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class Tab01ProductAll(Product):
    class Meta:
        proxy = True
        verbose_name_plural = "01. สินค้าพร้อมขาย"


@admin.register(Tab01ProductAll)
class Tab01Admin(ProductBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(stock__gt=0).select_related("game", "category")


class Tab02GameAll(Game):
    class Meta:
        proxy = True
        verbose_name_plural = "02. รายชื่อเกมทั้งหมด"


@admin.register(Tab02GameAll)
class Tab02Admin(GameBaseAdmin):
    pass


class Tab03GamePC(Game):
    class Meta:
        proxy = True
        verbose_name_plural = "03. เกมเฉพาะ PC"


@admin.register(Tab03GamePC)
class Tab03Admin(GameBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(platform__name__iexact="pc")


class Tab04GameMobile(Game):
    class Meta:
        proxy = True
        verbose_name_plural = "04. เกมเฉพาะ Mobile"


@admin.register(Tab04GameMobile)
class Tab04Admin(GameBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(platform__name__iexact="mobile")


class Tab05Platform(Category):
    class Meta:
        proxy = True
        verbose_name_plural = "05. จัดการ Platform"


@admin.register(Tab05Platform)
class Tab05Admin(BaseTabAdmin):
    list_display = ("display_custom_id", "name")
    search_fields = ("name",)
    ordering = ("name",)
    fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(type="platform")

    def save_model(self, request, obj, form, change):
        obj.type = "platform"
        super().save_model(request, obj, form, change)


class Tab06Genre(Category):
    class Meta:
        proxy = True
        verbose_name_plural = "06. จัดการหมวดเกม"


@admin.register(Tab06Genre)
class Tab06Admin(BaseTabAdmin):
    list_display = ("display_custom_id", "name")
    search_fields = ("name",)
    ordering = ("name",)
    fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(type="genre")

    def save_model(self, request, obj, form, change):
        obj.type = "genre"
        super().save_model(request, obj, form, change)


class Tab07ProductCat(Category):
    class Meta:
        proxy = True
        verbose_name_plural = "07. จัดการหมวดสินค้า"


@admin.register(Tab07ProductCat)
class Tab07Admin(BaseTabAdmin):
    list_display = ("display_custom_id", "name")
    search_fields = ("name",)
    ordering = ("name",)
    fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(type="product")

    def save_model(self, request, obj, form, change):
        obj.type = "product"
        super().save_model(request, obj, form, change)


class Tab08OutOfStock(Product):
    class Meta:
        proxy = True
        verbose_name_plural = "08. สินค้าหมดสต็อก"


@admin.register(Tab08OutOfStock)
class Tab08Admin(ProductBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(Q(stock=0) | Q(stock__isnull=True)).select_related("game", "category")
