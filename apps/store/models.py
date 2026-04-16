from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class Game(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="ชื่อเกม")
    slug = models.SlugField(unique=True, blank=True, verbose_name="URL Slug")
    logo = models.ImageField(upload_to='games/logos/', blank=True, null=True, verbose_name="โลโก้เกม")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")
    description = models.TextField(blank=True, null=True, verbose_name="รายละเอียดเกม")

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

    TYPE_CHOICES = [
        ('platform', 'Platform'),
        ('genre', 'Game Category'),
        ('product', 'Product Category'),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='product')

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name="เกม",
        null=True,
        blank=True
    )

    name = models.CharField(max_length=100, verbose_name="ชื่อ")

    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Platform"
    )

    def clean(self):
        # Platform
        if self.type == 'platform':
            if self.game or self.parent:
                raise ValidationError("Platform ห้ามมี game หรือ parent")

        # Game Category
        if self.type == 'genre':
            if not self.game or not self.parent:
                raise ValidationError("Game Category ต้องมี game และ platform")

            if self.parent.type != 'platform':
                raise ValidationError("parent ต้องเป็น Platform เท่านั้น")

        # Product Category
        if self.type == 'product':
            if self.game or self.parent:
                raise ValidationError("Product Category ห้ามมี game หรือ parent")

    def __str__(self):
        if self.type == 'platform':
            return f"[Platform] {self.name}"
        elif self.type == 'genre':
            return f"[{self.game}] {self.parent} - {self.name}"
        return f"[Product] {self.name}"

    class Meta:
        verbose_name = "หมวดหมู่"
        verbose_name_plural = "หมวดหมู่ทั้งหมด"


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="หมวดหมู่")
    title = models.CharField(max_length=255, verbose_name="ชื่อสินค้า")
    description = models.TextField(verbose_name="รายละเอียดสินค้า")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคา")
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    stock = models.PositiveIntegerField(default=1)
    sold_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.category.type != 'genre':
            raise ValidationError("สินค้าต้องอยู่ใน Game Category เท่านั้น")

    def __str__(self):
        return f"{self.title} ({self.category})"