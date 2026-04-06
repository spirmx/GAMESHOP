from django.contrib import admin
from .models import Game, Category, Product

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)} # พิมพ์ชื่อเกมแล้ว Slug ขึ้นให้เอง
    list_editable = ('is_active',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'game')
    list_filter = ('game',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'stock', 'is_active')
    list_filter = ('category__game', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('price', 'stock', 'is_active')