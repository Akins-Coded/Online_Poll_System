# permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminOrReadOnly(BasePermission):
    """
    Read: everyone
    Write: only admins (is_staff / is_superuser / role='Admin')
    """

    def has_permission(self, request, view):
        # SAFE methods → list/retrieve allowed for all
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Classic Django admin check
        if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
            return True

        # If you have a Roles enum, e.g., User.Roles.ADMIN
        if hasattr(User, "Roles") and getattr(user, "role", None) == User.Roles.ADMIN:
            return True

        # Fallback string-based check
        if str(getattr(user, "role", "")).lower() == "admin":
            return True

        return False
