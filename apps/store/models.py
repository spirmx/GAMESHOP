from django.db import models
from django.utils.text import slugify

class Game(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="ชื่อเกม")
    slug = models.SlugField(unique=True, blank=True, verbose_name="URL Slug")
    logo = models.ImageField(upload_to='games/logos/', blank=True, null=True, verbose_name="โลโก้เกม")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "เกม"
        verbose_name_plural = "รายชื่อเกม"

class Category(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='categories', verbose_name="เกม")
    name = models.CharField(max_length=100, verbose_name="ชื่อหมวดหมู่")
    parent = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='subcategories'
    )

    def __str__(self):
        return f"{self.game.name} - {self.name}"

    class Meta:
        verbose_name = "หมวดหมู่"
        verbose_name_plural = "หมวดหมู่สินค้า"

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="หมวดหมู่")
    title = models.CharField(max_length=255, verbose_name="ชื่อสินค้า")
    description = models.TextField(verbose_name="รายละเอียดสินค้า")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคา")
    stock = models.PositiveIntegerField(default=1, verbose_name="จำนวนในสต็อก")
    is_active = models.BooleanField(default=True, verbose_name="พร้อมขาย")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.category.game.name}] {self.title}"

    class Meta:
        verbose_name = "สินค้า"
        verbose_name_plural = "รายการสินค้าทั้งหมด"