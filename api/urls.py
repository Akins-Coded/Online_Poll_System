from django.urls import path
from .views import RegisterView, LoginView, RefreshView, UserListView, AdminCreateView

urlpatterns = [
    path("signup/", RegisterView.as_view(), name="auth_register"),
    path("login/", LoginView.as_view(), name="auth_login"),
    path("refresh/", RefreshView.as_view(), name="auth_refresh"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("admin/create/", AdminCreateView.as_view(), name="admin_create"),
]
