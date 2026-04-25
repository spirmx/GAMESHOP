from django.urls import path

from . import views


app_name = "users"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("signup/", views.signup_view, name="signup"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/game/<int:category_id>/", views.admin_category_stock, name="admin_category_stock"),
    path("dashboard/users/", views.admin_user_list, name="admin_user_list"),
]
