from rest_framework.permissions import BasePermission


class IsAdminOrServiceRole(BasePermission):
    message = "Admin or service role is required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return "admin" in roles or "service" in roles


class IsOwnerAdminOrService(BasePermission):
    message = "Only payment owner, admin, or service role can access this resource."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return int(obj.user_id) == int(user.id) or "admin" in roles or "service" in roles

