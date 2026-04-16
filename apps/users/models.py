from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_seller = models.BooleanField(default=False, verbose_name="เป็นผู้ขาย")
    is_verified = models.BooleanField(default=False, verbose_name="ยืนยันตัวตนแล้ว")
    
    profile_image = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True, 
        verbose_name="รูปโปรไฟล์"
    )
    
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")
    class Meta:
        verbose_name = "ผู้ใช้งาน"
        verbose_name_plural = "รายชื่อผู้ใช้งานทั้งหมด"

    def __str__(self):
        return self.username