from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('game/<slug:slug>/', views.game_detail, name='game_detail'),
    path('store/', views.product_list, name='product_list'),
]