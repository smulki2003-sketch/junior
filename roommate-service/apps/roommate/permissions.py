from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        user_id = view.kwargs.get("user_id")
        if user_id is None:
            return False
        if "admin" in getattr(user, "roles", []):
            return True
        return int(user_id) == int(user.id)


class IsAdminOrServiceRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return "admin" in roles or "service" in roles

