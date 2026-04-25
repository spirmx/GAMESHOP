from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .image_utils import optimize_uploaded_image


class Game(models.Model):
    name = models.CharField(max_length=500, unique=True, verbose_name="ชื่อเกม")
    genre = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"type": "genre"},
        verbose_name="หมวดเกม (Genre)",
        related_name="game_genres",
    )
    platform = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"type": "platform"},
        verbose_name="แพลตฟอร์ม",
        related_name="game_platforms",
    )
    slug = models.SlugField(unique=True, blank=True, verbose_name="URL Slug")
    logo = models.ImageField(upload_to="games/logos/", blank=True, null=True, verbose_name="โลโก้เกม")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")
    description = models.TextField(blank=True, verbose_name="รายละเอียดเกม")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if self.logo:
            optimize_uploaded_image(self.logo, max_size=(720, 720), quality=84)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def is_available_for_sale(self):
        return self.is_active

    @property
    def storefront_status_label(self):
        return "พร้อมขาย" if self.is_available_for_sale else "ไม่พร้อมขาย"

    class Meta:
        verbose_name = "เกม"
        verbose_name_plural = "รายชื่อเกม"


class Category(models.Model):
    TYPE_CHOICES = [
        ("platform", "Platform"),
        ("genre", "Game Category"),
        ("product", "Product Category"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="product", verbose_name="ประเภทหมวดหมู่")
    name = models.CharField(max_length=100, verbose_name="ชื่อหมวดหมู่")
    slug = models.SlugField(max_length=140, unique=True, blank=True, null=True, verbose_name="URL Slug")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="categories", verbose_name="เกม", null=True, blank=True)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subcategories", verbose_name="Platform")

    def clean(self):
        if self.type == "platform":
            if self.game or self.parent:
                raise ValidationError("Platform ต้องระบุแค่ชื่อเท่านั้น")
        elif self.type == "product":
            if self.game or self.parent:
                raise ValidationError("หมวดสินค้าไม่ต้องผูกกับเกมหรือแพลตฟอร์ม")

    def save(self, *args, **kwargs):
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "หมวดหมู่"
        verbose_name_plural = "หมวดหมู่ทั้งหมด"


class Product(models.Model):
    FULFILLMENT_TYPE_CHOICES = [
        ("code", "ส่งโค้ด / คีย์สินค้า"),
        ("account", "เติมเข้าบัญชีเกม"),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="products", verbose_name="เกม", null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="หมวดหมู่สินค้า")
    title = models.CharField(max_length=255, verbose_name="ชื่อสินค้า")
    description = models.TextField(verbose_name="รายละเอียดสินค้า")
    fulfillment_type = models.CharField(
        max_length=20,
        choices=FULFILLMENT_TYPE_CHOICES,
        default="code",
        verbose_name="รูปแบบการส่งมอบสินค้า",
    )

    account_input_label = models.CharField(max_length=120, blank=True, verbose_name="Extra setting")
    account_input_placeholder = models.CharField(max_length=180, blank=True, verbose_name="Extra setting")
    account_input_help = models.CharField(max_length=255, blank=True, default="", verbose_name="Extra setting")
    account_input_secondary_label = models.CharField(max_length=120, blank=True, verbose_name="Extra setting")
    account_input_secondary_placeholder = models.CharField(max_length=180, blank=True, verbose_name="Extra setting")
    account_input_secondary_help = models.CharField(max_length=255, blank=True, verbose_name="Extra setting")


    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคา")
    image = models.ImageField(upload_to="products/", null=True, blank=True, verbose_name="รูปภาพสินค้า")
    stock = models.PositiveIntegerField(default=1, verbose_name="จำนวนในสต็อก")
    sold_count = models.PositiveIntegerField(default=0, verbose_name="ยอดขาย")
    is_active = models.BooleanField(default=True, verbose_name="พร้อมขาย")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่เพิ่ม")

    def save(self, *args, **kwargs):
        if self.image:
            optimize_uploaded_image(self.image, max_size=(1400, 1400), quality=84)
        super().save(*args, **kwargs)

    def __str__(self):
        game_name = self.game.name if self.game else "No Game"
        return f"{self.title} ({game_name})"

    @property
    def is_code_product(self):
        return self.fulfillment_type == "code"

    @property
    def is_account_product(self):
        return self.fulfillment_type == "account"

    @property
    def has_secondary_input(self):
        return bool((self.account_input_secondary_label or "").strip())

    @property
    def related_game(self):
        if self.game_id:
            return self.game
        if self.category_id and getattr(self.category, "game_id", None):
            return self.category.game
        return None

    @property
    def game_is_available_for_sale(self):
        game = self.related_game
        return game.is_available_for_sale if game else True

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def is_available_for_sale(self):
        return self.is_active and self.game_is_available_for_sale and self.is_in_stock

    @property
    def is_visible_but_blocked(self):
        return not self.is_available_for_sale

    @property
    def storefront_status_label(self):
        if not self.game_is_available_for_sale:
            return "ไม่พร้อมขาย"
        if not self.is_active:
            return "ไม่พร้อมขาย"
        if not self.is_in_stock:
            return "สินค้าหมด"
        return "พร้อมขาย"

    class Meta:
        verbose_name = "สินค้า"
        verbose_name_plural = "คลังสินค้า"


class ProductCode(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="code_items", verbose_name="สินค้า")
    code = models.TextField(verbose_name="โค้ด / คีย์สินค้า")
    note = models.CharField(max_length=255, blank=True, default="", verbose_name="หมายเหตุ")
    is_used = models.BooleanField(default=False, verbose_name="ถูกใช้งานแล้ว")
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="เวลาที่ถูกใช้งาน")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่เพิ่มโค้ด")

    def __str__(self):
        return f"Code #{self.pk} - {self.product.title}"

    def mark_as_used(self):
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=["is_used", "used_at"])

    class Meta:
        verbose_name = "โค้ดสินค้า"
        verbose_name_plural = "คลังโค้ดสินค้า"
