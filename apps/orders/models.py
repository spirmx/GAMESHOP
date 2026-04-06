# apps/orders/models.py
from django.db import models
from django.conf import settings
from apps.store.models import Product

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'รอดำเนินการ'),
        ('success', 'สำเร็จ'),
        ('failed', 'ล้มเหลว'),
    )
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "คำสั่งซื้อ"
        verbose_name_plural = "รายการคำสั่งซื้อทั้งหมด"

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # บันทึกราคา ณ วันที่ซื้อ

    def __str__(self):
        return f"{self.product.title} (x{self.quantity})"