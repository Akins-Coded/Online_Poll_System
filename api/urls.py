from django.urls import path
from .views import RegisterView, LoginView, RefreshView

urlpatterns = [
    path("signup/", RegisterView.as_view(), name="auth_register"),
    path("login/", LoginView.as_view(), name="auth_login"),
    path("refresh/", RefreshView.as_view(), name="auth_refresh"),
]
