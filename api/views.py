from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .serializers import RegisterSerializer
from .models import User


# Register endpoint
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# Login endpoint (JWT)
class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


# Refresh endpoint (JWT)
class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
