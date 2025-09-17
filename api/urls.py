from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, RefreshView, UserViewSet, UserListView

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("signup/", RegisterView.as_view(), name="auth_register"),
    path("login/", LoginView.as_view(), name="auth_login"),
    path("refresh/", RefreshView.as_view(), name="auth_refresh"),
    path("users/", UserListView.as_view(), name="user_list"),
]

urlpatterns += router.urls
