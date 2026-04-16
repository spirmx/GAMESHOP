from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# --- 1. สร้าง Proxy Models เพื่อแยกเมนูทางซ้ายมือ ---
class AdminUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = 'ผู้ดูแลระบบ (Admin)'
        verbose_name_plural = '1. รายชื่อ Admin'

class PlayerUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = 'ผู้เล่น (Player)'
        verbose_name_plural = '2. รายชื่อผู้เล่นทั่วไป'

# --- 2. ตั้งค่าการแสดงผล (Base CustomUserAdmin) ---
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_verified', 'is_staff', 'is_active')
    list_editable = ('is_verified', 'is_active') 
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_verified')
    search_fields = ('username', 'email', 'phone_number')


    fieldsets = (
        ('1. ข้อมูลหลักและความปลอดภัย', {
            'fields': ('username', 'password', 'is_verified', 'profile_image')
        }),
        ('2. ข้อมูลการติดต่อ', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number')
        }),
        ('3. สิทธิ์และการอนุญาต', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('4. ข้อมูลระบบ (Log)', {
            'classes': ('collapse',),
            'fields': ('last_login', 'date_joined'),
        }),
    )

# --- 3. ลงทะเบียนและแยก QuerySet (The Final Polish) ---

@admin.register(AdminUser)
class AdminUserAdmin(CustomUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)

@admin.register(PlayerUser)
class PlayerUserAdmin(CustomUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False)

admin.site.register(CustomUser, CustomUserAdmin)