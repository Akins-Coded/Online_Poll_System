from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .serializers import RegisterSerializer, UserSerializer
from django.contrib.auth import get_user_model
from .permissions import IsAdminUser

User = get_user_model()


# Register endpoint
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_context(self):
        """
        Pass request into serializer so it knows if user is admin.
        """
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class AdminCreateView(generics.CreateAPIView):
    """
    Allow only logged-in admins to create another admin.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(role=User.Roles.ADMIN)

        
# Login endpoint (JWT)
class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


# Refresh endpoint (JWT)
class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]