from django.urls import path
from . import views

app_name = 'wallets' 

urlpatterns = [
    path('home/', views.wallet_home_view, name='wallet_home'),
    path('top-up/', views.top_up, name='top_up'),
    path('process/', views.process_topup, name='process_topup'),
    path('confirm-topup/', views.confirm_topup, name='confirm_topup'), # ✅ URL สำหรับยืนยัน Demo
    path('pay/<int:order_id>/', views.payment_page, name='payment_page'),
]