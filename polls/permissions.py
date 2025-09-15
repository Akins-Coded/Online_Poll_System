from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """
    Allow safe methods for everyone, allow create/update/delete only for admins.
    Checks user.is_staff or user.role == 'admin' (if role exists).
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # admin if is_staff or role set to admin
        if getattr(user, "is_staff", False):
            return True
        if getattr(user, "role", None) == getattr(user.__class__, "Role", None).ADMIN if hasattr(user.__class__, "Role") else False:
            return True
        # fallback: deny
        return False
