from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    message = "You can only access your own profile resources unless you are an admin."

    def has_permission(self, request, view):
        user = request.user
        if user is None or not getattr(user, "is_authenticated", False):
            return False

        path_user_id = view.kwargs.get("user_id")
        if path_user_id is None:
            return False

        if "admin" in getattr(user, "roles", []):
            return True
        return int(path_user_id) == int(user.id)

