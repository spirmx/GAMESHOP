from django.urls import path
from django.contrib.auth import views as auth_views
from .views import signup_view, admin_dashboard, profile_view

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', signup_view, name='signup'),
    path('profile/', profile_view, name='profile'),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
]