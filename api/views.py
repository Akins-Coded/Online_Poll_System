from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .tasks import send_welcome_email
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, AdminCreateSerializer, UserSerializer, LogoutSerializer
from .permissions import IsAdminUser

User = get_user_model()


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
        responses={
            201: openapi.Response(
                description="User created successfully",
                schema=RegisterSerializer
            )
        }
    )
    def perform_create(self, serializer):
        user = serializer.save()
        # Send welcome email in a background thread
        send_welcome_email(user.email, user.first_name)


class LoginView(TokenObtainPairView):
    """JWT login view with documented request/response in Swagger."""
    serializer_class = TokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Obtain JWT token pair",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: openapi.Response(
            description='JWT Token Pair',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshView(TokenRefreshView):
    """JWT token refresh view."""
    permission_classes = [permissions.AllowAny]


class UserListView(generics.ListAPIView):
    """List all users — only admins can access this."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]


class UserViewSet(viewsets.GenericViewSet):
    """Viewset for admin-only operations (like creating new admins)."""
    queryset = User.objects.all()
    serializer_class = AdminCreateSerializer

    @swagger_auto_schema(
        operation_description="Create a new admin (admin-only)",
        request_body=AdminCreateSerializer,
        responses={201: AdminCreateSerializer}
    )
    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsAdminUser])
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
                    description="The refresh token to be blacklisted"
                ),
            },
        ),
        responses={
            205: openapi.Response(description="Successfully logged out."),
            400: openapi.Response(description="Invalid or already blacklisted token."),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)