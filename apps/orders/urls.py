from django.urls import path
from . import views

app_name = 'orders' # 🚨 สำคัญมาก: ต้องมีเพื่อให้ Namespace 'orders:' ทำงาน

urlpatterns = [
    # หน้าสรุปรายการก่อนจ่ายเงิน
    path('checkout/', views.checkout, name='checkout'), 
    # Logic การสร้างคำสั่งซื้อในฐานข้อมูล
    path('place-order/', views.place_order, name='place_order'),
    # หน้าประวัติการซื้อทั้งหมด
    path('history/', views.order_list, name='order_list'),
    # หน้าใบเสร็จ/รหัสไอเท็ม
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('all-transactions/', views.all_transactions, name='all_transactions'),
]