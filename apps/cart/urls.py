# apps/cart/urls.py
from django.urls import path
from . import views

# 🚨 เพิ่มบรรทัดนี้ลงไปครับ เพื่อจดทะเบียน Namespace ให้แอป
app_name = 'cart' 

urlpatterns = [

    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('', views.cart_detail, name='cart_detail'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('decrease/<int:product_id>/', views.decrease_quantity, name='decrease_quantity'),
]