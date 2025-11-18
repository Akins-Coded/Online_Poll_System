from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import (
    RegisterView,
    AdminCreateView,
    UserViewSet,
    UserListView,
    LogoutView,
    CustomTokenObtainPairView,
    me,
)
# --- Swagger Schema View ---
schema_view = get_schema_view(
    openapi.Info(
        title="Coded Poll System API",
        default_version='v1',
        description="Interactive API docs with JWT authentication",
        terms_of_service="https://example.com/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# --- Router for UserViewSet ---
router = DefaultRouter()
router.register("users", UserViewSet, basename="user")


# --- URL Patterns ---
urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth_register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="auth_logout"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("me/", me, name="auth_me"),
    path("create_admin/", AdminCreateView.as_view(), name="create_admin"),

    # Swagger endpoints
    re_path(r"^docs(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("docs/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
]


# Include router URLs
urlpatterns += router.urls
