# apps/wallets/urls.py
from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    path('top-up/', views.top_up, name='top_up'),
    path('process-topup/', views.process_topup, name='process_topup'), # 🚨 เพิ่มบรรทัดนี้
    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
]