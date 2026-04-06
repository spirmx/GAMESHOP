from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum
from .forms import SignUpForm
from .models import CustomUser
from apps.store.models import Product, Category
from apps.orders.models import Order

# =========================================================
# ✨ ระบบสมาชิก (Signup & Profile)
# =========================================================

def signup_view(request):
    """หน้าสมัครสมาชิก รองรับข้อมูลเพิ่มเติมจาก CustomUser"""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'สร้างบัญชีสมาชิกสำเร็จ! เข้าสู่ระบบได้เลย')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'auth/signup.html', {'form': form})

@login_required
def profile_view(request):
    """หน้าข้อมูลส่วนตัวของ User เรียกใช้ templates/profile.html"""
    return render(request, 'profile.html')

# =========================================================
# 🚀 ระบบแผงควบคุม (Admin Management Dashboard)
# =========================================================

# ใช้ lambda เช็คสิทธิ์ is_staff เพื่อความปลอดภัยสูงสุด
@user_passes_test(lambda u: u.is_staff, login_url='login')
def admin_dashboard(request):
    """
    หน้า Dashboard สำหรับ Admin จัดการยอดขาย คลังสินค้า และสมาชิก
    """
    # 💰 1. วิเคราะห์ยอดขาย (Revenue Analytics)
    # รวมยอดเงินทั้งหมดจาก Order ที่สถานะเป็น success หรือ paid
    total_revenue = Order.objects.filter(status__in=['success', 'paid']).aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # 👥 2. จัดการผู้ใช้งาน (Customer Management)
    # นับจำนวนสมาชิกที่ไม่ใช่ Admin
    total_customers = CustomUser.objects.filter(is_staff=False).count()
    recent_users = CustomUser.objects.all().order_by('-date_joined')[:5]

    # 📦 3. จัดการคลังสินค้า (Inventory & Analytics)
    # แจ้งเตือนสินค้าสต็อกต่ำ (เหลือต่ำกว่า 5 ชิ้น)
    low_stock_items = Product.objects.filter(stock__lt=5).order_by('stock')
    
    # สรุปจำนวนสินค้าแยกตามหมวดหมู่
    category_summary = Category.objects.annotate(product_count=Count('products'))

    # 🧾 4. ประวัติการทำรายการล่าสุด
    recent_orders = Order.objects.all().order_by('-created_at')[:8]

    context = {
        # สถิติหลัก (Top Stats Cards)
        'total_revenue': total_revenue,
        'total_orders': Order.objects.count(),
        'total_products': Product.objects.count(),
        'total_customers': total_customers,
        
        # ข้อมูลการจัดการ (Management Data)
        'category_summary': category_summary,
        'low_stock_items': low_stock_items,
        'recent_users': recent_users,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)