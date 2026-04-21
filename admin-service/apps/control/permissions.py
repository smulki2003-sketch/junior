from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = "Admin role is required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return "admin" in getattr(user, "roles", [])

