from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # ฟิลด์สถานะสำหรับ Role
    is_seller = models.BooleanField(default=False, verbose_name="เป็นผู้ขาย")
    
    # ข้อมูลส่วนตัวและที่อยู่สำหรับการจัดส่ง/สมัคร
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")
    address = models.TextField(blank=True, null=True, verbose_name="ที่อยู่")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="จังหวัด")
    postal_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="รหัสไปรษณีย์")

    class Meta:
        verbose_name = "ผู้ใช้งาน"
        verbose_name_plural = "รายชื่อผู้ใช้งานทั้งหมด"

    def __str__(self):
        return self.username