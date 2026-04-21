from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = "Admin role is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and getattr(user, "is_authenticated", False) and "admin" in getattr(user, "roles", []))


class IsOwnerOrAdmin(BasePermission):
    message = "Only unit owner or admin can modify this listing."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return int(obj.owner_user_id) == int(user.id) or "admin" in getattr(user, "roles", [])

