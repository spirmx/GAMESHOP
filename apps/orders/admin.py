# apps/orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('buyer__username', 'id')
    inlines = [OrderItemInline] # แสดงรายการสินค้าที่ซื้อภายในหน้า Order เลย
    ordering = ('-created_at',)