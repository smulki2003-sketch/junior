from rest_framework.permissions import BasePermission

from .services import get_user_roles


class IsAdminRole(BasePermission):
    message = "Admin role is required for this action."

    def has_permission(self, request, view):
        user = request.user
        if user is None:
            return False
        if hasattr(request, "auth") and isinstance(request.auth, dict):
            roles = request.auth.get("roles", [])
            if "admin" in roles:
                return True
        return "admin" in get_user_roles(user)

