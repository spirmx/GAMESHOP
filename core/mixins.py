from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect

class SellerRequiredMixin(UserPassesTestMixin):
    """Mixin สำหรับเช็คว่า User เป็นผู้ขาย (Seller) หรือไม่"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_seller

    def handle_no_permission(self):
        return redirect('home')

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin สำหรับเช็คว่าเป็น Staff หรือไม่ (ใช้ใน Dashboard)"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff