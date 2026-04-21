from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    message = "Admin role is required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return "admin" in getattr(user, "roles", [])


class IsReporterOrAdmin(BasePermission):
    message = "Only complaint reporter or admin can access this complaint."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return int(obj.reporter_user_id) == int(user.id) or "admin" in getattr(user, "roles", [])

