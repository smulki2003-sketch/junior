from rest_framework.permissions import BasePermission


class IsAdminOrServiceRole(BasePermission):
    message = "Admin or service role is required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return "admin" in roles or "service" in roles


class IsOwnerOrAdminByPath(BasePermission):
    message = "You can only access your own saved filters unless you are an admin."

    def has_permission(self, request, view):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        path_user_id = view.kwargs.get("user_id")
        if path_user_id is None:
            return False
        if "admin" in getattr(user, "roles", []):
            return True
        return int(path_user_id) == int(user.id)


class IsSavedFilterOwnerOrAdmin(BasePermission):
    message = "Only saved-filter owner or admin can delete this filter."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return int(obj.user_id) == int(user.id) or "admin" in getattr(user, "roles", [])

