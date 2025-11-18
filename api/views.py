from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.contrib.auth import get_user_model

from .tasks import send_welcome_email
from .serializers import (
    RegisterSerializer,
    AdminCreateSerializer,
    UserSerializer,
    LogoutSerializer,
)
from .permissions import IsAdminUser
from .token import CustomTokenObtainPairSerializer

User = get_user_model()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return current authenticated user profile."""
    user = request.user
    return Response(
        {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "surname": user.surname,
            "role": user.role,
        }
    )


class RegisterView(generics.CreateAPIView):
    """Open registration; non-admins can only register voters."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_context(self):
        return {"request": self.request}

    @swagger_auto_schema(
        operation_description="Register a new user (voter by default). Sends a welcome email asynchronously.",
        request_body=RegisterSerializer,
        responses={201: RegisterSerializer},
    )
    def perform_create(self, serializer):
        user = serializer.save()
        send_welcome_email(user.email, user.first_name)

class AdminCreateView(generics.CreateAPIView):
    serializer_class = AdminCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

class RefreshView(TokenRefreshView):
    """JWT token refresh view."""
    permission_classes = [permissions.AllowAny]


class UserListView(generics.ListAPIView):
    """List all users — only admins can access this."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


class UserViewSet(viewsets.GenericViewSet):
    """Admin-only operations (e.g., create new admins)."""

    @swagger_auto_schema(
        operation_description="Create a new admin (admin-only)",
        request_body=AdminCreateSerializer,
        responses={201: AdminCreateSerializer},
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated, IsAdminUser],
    )
    def create_admin(self, request):
        serializer = AdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "surname": user.surname,
                "role": user.role,
            },
            status=status.HTTP_201_CREATED,
        )
     # ✅ Count users by role (admin-only)
    @swagger_auto_schema(
        operation_description="Get user counts by role (admin-only). Returns a JSON object with role counts.",
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            additional_properties=openapi.Schema(type=openapi.TYPE_INTEGER),
            example={"admin": 3, "voter": 42},
        )},
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated, IsAdminUser],
        url_path="role-counts",
    )
    def role_counts(self, request):
        """Return a dictionary of user counts by role."""
        role_data = (
            User.objects.values("role")
            .annotate(count=Count("role"))
            .order_by()
        )
        response_data = {item["role"]: item["count"] for item in role_data}
        return Response(response_data, status=status.HTTP_200_OK)

class LogoutView(generics.GenericAPIView):
    """Logout by blacklisting the refresh token."""
    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logout a user by blacklisting their refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The refresh token to be blacklisted",
                ),
            },
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_205_RESET_CONTENT,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT login view with extra claims (email, role)."""
    serializer_class = CustomTokenObtainPairSerializer
