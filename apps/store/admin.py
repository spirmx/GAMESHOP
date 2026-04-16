from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Game, Category, Product


class BaseTabAdmin(admin.ModelAdmin):
    def display_custom_id(self, obj):
        prefix = ""
        if isinstance(obj, Category):
            if obj.type == 'platform': prefix = "X"
            elif obj.type == 'genre': prefix = "M"
            elif obj.type == 'product': prefix = "P"
        return format_html('<b>{}{}</b>', prefix, obj.id)

    display_custom_id.short_description = 'รหัส'


# =========================
# CATEGORY (สำคัญสุด)
# =========================
@admin.register(Category)
class CategoryAdmin(BaseTabAdmin):
    list_display = ('display_custom_id', 'name', 'type', 'parent', 'game')
    list_filter = ('type',)
    fields = ('type', 'name', 'parent', 'game')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "parent":
            kwargs["queryset"] = Category.objects.filter(type='platform')

        if db_field.name == "game":
            kwargs["queryset"] = Game.objects.all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# =========================
# GAME
# =========================
@admin.register(Game)
class GameAdmin(BaseTabAdmin):
    list_display = ('id', 'name', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


# =========================
# PRODUCT
# =========================
@admin.register(Product)
class ProductAdmin(BaseTabAdmin):
    list_display = ('id', 'title', 'category', 'price', 'stock', 'is_active')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "category":
            kwargs["queryset"] = Category.objects.filter(type='genre')

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# =========================
# PROXY (10 ตาราง)
# =========================

class Tab01ProductAll(Product):
    class Meta:
        proxy = True
        verbose_name_plural = "01. สินค้าทั้งหมด"
@admin.register(Tab01ProductAll)
class Tab01Admin(ProductAdmin): pass


class Tab02GameAll(Game):
    class Meta:
        proxy = True
        verbose_name_plural = "02. เกมทั้งหมด"
@admin.register(Tab02GameAll)
class Tab02Admin(GameAdmin): pass


class Tab03GamePC(Game):
    class Meta:
        proxy = True
        verbose_name_plural = "03. เกม PC"
@admin.register(Tab03GamePC)
class Tab03Admin(GameAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(categories__parent__name__iexact="pc").distinct()


class Tab04GameMobile(Game):
    class Meta:
        proxy = True
        verbose_name_plural = "04. เกม Mobile"
@admin.register(Tab04GameMobile)
class Tab04Admin(GameAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(categories__parent__name__iexact="mobile").distinct()


class Tab08Platform(Category):
    class Meta:
        proxy = True
        verbose_name_plural = "08. Platform"
@admin.register(Tab08Platform)
class Tab08Admin(CategoryAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(type='platform')


class Tab09Genre(Category):
    class Meta:
        proxy = True
        verbose_name_plural = "09. หมวดเกม"
@admin.register(Tab09Genre)
class Tab09Admin(CategoryAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(type='genre')


class Tab10ProductCat(Category):
    class Meta:
        proxy = True
        verbose_name_plural = "10. หมวดสินค้า"
@admin.register(Tab10ProductCat)
class Tab10Admin(CategoryAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(type='product')