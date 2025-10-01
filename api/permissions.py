from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission: only users with role='admin' can access.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "admin"
        )
