from django.urls import path, re_path
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import RegisterView, LoginView, RefreshView, UserViewSet, UserListView, LogoutView

# --- Swagger Schema View ---
schema_view = get_schema_view(
    openapi.Info(
        title="Online Poll System API",
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
    path("login/", LoginView.as_view(), name="auth_login"),
    path("logout/", LogoutView.as_view(), name="auth_logout"), 
    path("refresh/", RefreshView.as_view(), name="auth_refresh"),
    path("users/", UserListView.as_view(), name="user_list"),

    # Swagger endpoints
    re_path(r'^api/docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

# Include router URLs
urlpatterns += router.urls
