from django.urls import path
from . import views

app_name = 'orders' # 🚨 สำคัญมาก: ต้องมีเพื่อให้ Namespace 'orders:' ทำงาน

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'), 
    path('place-order/', views.place_order, name='place_order'),
    path('history/', views.order_list, name='order_list'),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('all-transactions/', views.all_transactions, name='all_transactions'),
    path('payment/', views.payment_confirmation, name='payment_confirmation'),
]