from __future__ import annotations

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuthRole, AuthUser
from .permissions import IsAdminRole
from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshSerializer,
    RegisterSerializer,
    RoleUpdateSerializer,
    UserListQuerySerializer,
)
from .services import (
    create_password_reset_token,
    ensure_default_roles,
    get_user_roles,
    hash_password,
    issue_token_pair,
    log_auth_event,
    revoke_refresh_token,
    rotate_access_token,
    set_user_roles,
    use_password_reset_token,
    verify_password,
)


def get_request_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def user_payload(user: AuthUser) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "roles": get_user_roles(user),
        "created_at": user.created_at.isoformat(),
    }


def _parse_user_ids_csv(raw: str | None) -> list[int]:
    if not raw:
        return []
    values: list[int] = []
    for piece in raw.split(","):
        chunk = piece.strip()
        if chunk.isdigit():
            values.append(int(chunk))
    return values


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()
        password = serializer.validated_data["password"]

        ensure_default_roles()
        if AuthUser.objects.filter(email=email).exists():
            return Response(
                {"error": {"code": "email_in_use", "message": "Email is already registered."}},
                status=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            user = AuthUser.objects.create(
                email=email,
                password_hash=hash_password(password),
                is_active=True,
            )
            set_user_roles(user, [AuthRole.ROLE_STUDENT])

        log_auth_event("register", user=user, ip_address=get_request_ip(request))
        return Response(user_payload(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()
        password = serializer.validated_data["password"]

        user = AuthUser.objects.filter(email=email).first()
        if user is None or not verify_password(password, user.password_hash):
            log_auth_event("login_failed", ip_address=get_request_ip(request), metadata={"email": email})
            return Response(
                {"error": {"code": "invalid_credentials", "message": "Invalid email or password."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {"error": {"code": "inactive_user", "message": "User account is inactive."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        tokens = issue_token_pair(user)
        log_auth_event("login", user=user, ip_address=get_request_ip(request))
        return Response(
            {
                "user": user_payload(user),
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh_token"]
        revoked = revoke_refresh_token(refresh_token)

        log_auth_event(
            "logout",
            ip_address=get_request_ip(request),
            metadata={"token_revoked": revoked},
        )
        return Response({"token_revoked": revoked}, status=status.HTTP_200_OK)


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh_token"]

        try:
            new_access = rotate_access_token(refresh_token)
        except Exception as exc:
            return Response(
                {"error": {"code": "invalid_refresh_token", "message": str(exc)}},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        log_auth_event("token_refresh", ip_address=get_request_ip(request))
        return Response({"tokens": new_access}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(user_payload(request.user), status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()

        user = AuthUser.objects.filter(email=email).first()
        token = None
        if user is not None:
            token_obj = create_password_reset_token(user)
            token = token_obj.token
            log_auth_event("password_reset_requested", user=user, ip_address=get_request_ip(request))
        else:
            log_auth_event(
                "password_reset_requested_unknown_email",
                ip_address=get_request_ip(request),
                metadata={"email": email},
            )

        payload = {"message": "If the account exists, a reset token has been generated."}
        if token and settings.EXPOSE_PASSWORD_RESET_TOKEN:
            payload["reset_token"] = token
        return Response(payload, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = use_password_reset_token(token, new_password)
        except ValueError as exc:
            return Response(
                {"error": {"code": "invalid_reset_token", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_auth_event("password_reset_confirmed", user=user, ip_address=get_request_ip(request))
        return Response(
            {
                "message": "Password has been reset successfully.",
                "user_id": user.id,
                "timestamp": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class UserRolesUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def patch(self, request, user_id: int):
        serializer = RoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role_names = serializer.validated_data["roles"]

        target_user = AuthUser.objects.filter(id=user_id).first()
        if target_user is None:
            return Response(
                {"error": {"code": "user_not_found", "message": "Target user does not exist."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            updated_roles = set_user_roles(target_user, role_names)
        except ValueError as exc:
            return Response(
                {"error": {"code": "invalid_roles", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_auth_event(
            "roles_updated",
            user=target_user,
            ip_address=get_request_ip(request),
            metadata={
                "actor_user_id": request.user.id,
                "roles": updated_roles,
            },
        )
        return Response(
            {
                "user_id": target_user.id,
                "roles": updated_roles,
            },
            status=status.HTTP_200_OK,
        )


class UsersListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        serializer = UserListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        user_ids = _parse_user_ids_csv(serializer.validated_data.get("user_ids"))
        limit = serializer.validated_data.get("limit", 100)

        queryset = AuthUser.objects.all().order_by("id")
        if user_ids:
            queryset = queryset.filter(id__in=user_ids)
        else:
            queryset = queryset[:limit]

        results = [user_payload(user) for user in queryset]
        return Response({"count": len(results), "results": results}, status=status.HTTP_200_OK)
