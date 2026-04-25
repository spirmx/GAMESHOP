from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from apps.store.image_utils import optimize_uploaded_image


class CustomUser(AbstractUser):
    is_seller = models.BooleanField(default=False, verbose_name="เป็นผู้ขาย")
    is_verified = models.BooleanField(default=False, verbose_name="ยืนยันตัวตนแล้ว")
    email_verified = models.BooleanField(default=False, verbose_name="ยืนยันอีเมลแล้ว")
    phone_verified = models.BooleanField(default=False, verbose_name="ยืนยันเบอร์แล้ว")
    password_change_count = models.PositiveIntegerField(default=0, verbose_name="จำนวนครั้งที่เปลี่ยนรหัสผ่าน")
    failed_login_attempts = models.PositiveIntegerField(default=0, verbose_name="จำนวนครั้งที่ล็อกอินผิด")
    lockout_until = models.DateTimeField(null=True, blank=True, verbose_name="ล็อกอินได้อีกครั้งเมื่อ")
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name="เวลาใช้งานล่าสุด")
    profile_image = models.ImageField(
        upload_to="profile_pics/",
        null=True,
        blank=True,
        verbose_name="รูปโปรไฟล์",
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="เบอร์โทรศัพท์",
    )

    class Meta:
        verbose_name = "ผู้ใช้งาน"
        verbose_name_plural = "รายชื่อผู้ใช้งานทั้งหมด"

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.profile_image:
            optimize_uploaded_image(self.profile_image, max_size=(640, 640), quality=82)
        super().save(*args, **kwargs)

    @property
    def avatar_url(self):
        if self.profile_image and hasattr(self.profile_image, "url"):
            return self.profile_image.url
        return (
            f"https://ui-avatars.com/api/?name={self.username}"
            "&background=070A10&color=3b82f6&bold=true&format=svg"
        )

    @property
    def has_identity_profile(self):
        required_values = [
            self.first_name,
            self.last_name,
            self.email,
            self.phone_number,
        ]
        return all(str(value or "").strip() for value in required_values)

    @property
    def verification_complete(self):
        return bool(
            self.is_verified
            or (self.has_identity_profile and self.email_verified and self.phone_verified)
        )

    @property
    def is_online(self):
        if not self.last_seen:
            return False
        return self.last_seen >= timezone.now() - timedelta(minutes=5)

    @property
    def active_lockout_seconds(self):
        if not self.lockout_until:
            return 0
        remaining = int((self.lockout_until - timezone.now()).total_seconds())
        return max(remaining, 0)
