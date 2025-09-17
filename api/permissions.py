from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to allow only admins to view the user list.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")
