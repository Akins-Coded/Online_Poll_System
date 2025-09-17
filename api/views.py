from rest_framework import generics, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, AdminCreateSerializer, UserSerializer
from .permissions import IsAdminUser

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Open registration, Non-admins can only Register Voters. Coded-Something"""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_context(self):
        return {"request": self.request}


class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class RefreshView(TokenRefreshView):
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

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsAdminUser])
    def create_admin(self, request):
        """Allow only admins to create another admin."""
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
