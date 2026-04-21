from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone as django_timezone

from .models import AuthAuditLog, AuthPasswordResetToken, AuthRefreshToken, AuthRole, AuthUser, AuthUserRole


class TokenError(Exception):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_default_roles() -> None:
    for role_name in (AuthRole.ROLE_STUDENT, AuthRole.ROLE_ADMIN):
        AuthRole.objects.get_or_create(name=role_name)


def get_user_roles(user: AuthUser) -> list[str]:
    return list(
        AuthRole.objects.filter(user_links__user=user).values_list("name", flat=True).order_by("name")
    )


def set_user_roles(user: AuthUser, role_names: list[str]) -> list[str]:
    ensure_default_roles()
    with transaction.atomic():
        AuthUserRole.objects.filter(user=user).delete()
        role_objects = list(AuthRole.objects.filter(name__in=role_names))
        missing = sorted(set(role_names) - {role.name for role in role_objects})
        if missing:
            raise ValueError(f"Unknown roles: {', '.join(missing)}")
        for role in role_objects:
            AuthUserRole.objects.create(user=user, role=role)
    return get_user_roles(user)


def hash_password(raw_password: str) -> str:
    return make_password(raw_password)


def verify_password(raw_password: str, password_hash: str) -> bool:
    return check_password(raw_password, password_hash)


def build_access_token(user: AuthUser, roles: list[str]) -> tuple[str, datetime]:
    issued_at = utc_now()
    expires_at = issued_at + timedelta(minutes=settings.JWT_ACCESS_TTL_MINUTES)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "roles": roles,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_at


def build_refresh_token(user: AuthUser) -> tuple[str, str, datetime]:
    issued_at = utc_now()
    expires_at = issued_at + timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    token_jti = str(uuid.uuid4())
    payload = {
        "sub": str(user.id),
        "type": "refresh",
        "jti": token_jti,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, token_jti, expires_at


def issue_token_pair(user: AuthUser) -> dict:
    roles = get_user_roles(user)
    access_token, access_expires_at = build_access_token(user, roles)
    refresh_token, token_jti, refresh_expires_at = build_refresh_token(user)
    AuthRefreshToken.objects.create(
        user=user,
        token_jti=token_jti,
        expires_at=refresh_expires_at,
        is_revoked=False,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "access_expires_at": access_expires_at.isoformat(),
        "refresh_expires_at": refresh_expires_at.isoformat(),
        "roles": roles,
    }


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Token is invalid.") from exc


def decode_refresh_token(token: str) -> dict:
    payload = decode_jwt(token)
    if payload.get("type") != "refresh":
        raise TokenError("Token type is not refresh.")
    return payload


def decode_access_token(token: str) -> dict:
    payload = decode_jwt(token)
    if payload.get("type") != "access":
        raise TokenError("Token type is not access.")
    return payload


def rotate_access_token(refresh_token: str) -> dict:
    payload = decode_refresh_token(refresh_token)
    token_jti = payload.get("jti")
    user_id = payload.get("sub")
    if not token_jti or not user_id:
        raise TokenError("Refresh token payload is missing required claims.")

    refresh_record = AuthRefreshToken.objects.filter(token_jti=token_jti, user_id=user_id).first()
    if refresh_record is None:
        raise TokenError("Refresh token session not found.")
    if refresh_record.is_revoked:
        raise TokenError("Refresh token session has been revoked.")
    if refresh_record.expires_at <= django_timezone.now():
        raise TokenError("Refresh token session has expired.")

    user = AuthUser.objects.filter(id=user_id, is_active=True).first()
    if user is None:
        raise TokenError("User not found or inactive.")
    roles = get_user_roles(user)
    access_token, access_expires_at = build_access_token(user, roles)
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "access_expires_at": access_expires_at.isoformat(),
        "roles": roles,
    }


def revoke_refresh_token(refresh_token: str) -> bool:
    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError:
        return False

    if payload.get("type") != "refresh":
        return False

    token_jti = payload.get("jti")
    user_id = payload.get("sub")
    if not token_jti or not user_id:
        return False

    refresh_record = AuthRefreshToken.objects.filter(token_jti=token_jti, user_id=user_id).first()
    if refresh_record is None:
        return False

    refresh_record.is_revoked = True
    refresh_record.revoked_at = django_timezone.now()
    refresh_record.save(update_fields=["is_revoked", "revoked_at"])
    return True


def create_password_reset_token(user: AuthUser) -> AuthPasswordResetToken:
    token = secrets.token_urlsafe(32)
    expires_at = django_timezone.now() + timedelta(minutes=settings.PASSWORD_RESET_TTL_MINUTES)
    return AuthPasswordResetToken.objects.create(
        user=user,
        token=token,
        expires_at=expires_at,
        is_used=False,
    )


def use_password_reset_token(token: str, new_password: str) -> AuthUser:
    reset_record = AuthPasswordResetToken.objects.select_related("user").filter(token=token).first()
    if reset_record is None:
        raise ValueError("Reset token is invalid.")
    if reset_record.is_used:
        raise ValueError("Reset token has already been used.")
    if reset_record.expires_at <= django_timezone.now():
        raise ValueError("Reset token has expired.")

    user = reset_record.user
    user.password_hash = hash_password(new_password)
    user.save(update_fields=["password_hash", "updated_at"])

    reset_record.is_used = True
    reset_record.used_at = django_timezone.now()
    reset_record.save(update_fields=["is_used", "used_at"])

    AuthRefreshToken.objects.filter(user=user, is_revoked=False).update(
        is_revoked=True,
        revoked_at=django_timezone.now(),
    )
    return user


def log_auth_event(
    event_type: str,
    user: AuthUser | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
) -> None:
    AuthAuditLog.objects.create(
        user=user,
        event_type=event_type,
        ip_address=ip_address,
        metadata_json=metadata or {},
    )

