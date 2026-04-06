from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # กำหนดคอลัมน์ที่จะแสดงในหน้ารวม
    list_display = ['username', 'email', 'is_seller', 'is_staff']
    list_filter = ['is_seller', 'is_staff', 'is_superuser']
    
    # เพิ่มส่วน Gamer Info เข้าไปในหน้าแก้ไขข้อมูล
    fieldsets = UserAdmin.fieldsets + (
        ('Gamer Info', {'fields': ('is_seller', 'phone_number', 'address', 'city', 'postal_code')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)