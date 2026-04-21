from __future__ import annotations

from dataclasses import dataclass

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


@dataclass
class AuthPrincipal:
    user_id: int
    email: str | None
    roles: list[str]

    @property
    def id(self) -> int:
        return self.user_id

    @property
    def is_authenticated(self) -> bool:
        return True


class AuthServiceJWTAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return None
        keyword, _, token = auth_header.partition(" ")
        if keyword != self.keyword or not token:
            raise AuthenticationFailed("Invalid authorization header format.")
        try:
            payload = jwt.decode(
                token,
                settings.AUTH_SERVICE_JWT_SECRET,
                algorithms=[settings.AUTH_SERVICE_JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationFailed("Access token has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed("Access token is invalid.") from exc
        if payload.get("type") != "access":
            raise AuthenticationFailed("Unsupported token type.")
        sub = payload.get("sub")
        if sub is None:
            raise AuthenticationFailed("Access token missing subject.")
        try:
            user_id = int(sub)
        except (TypeError, ValueError) as exc:
            raise AuthenticationFailed("Invalid subject in access token.") from exc
        roles = payload.get("roles", [])
        if not isinstance(roles, list):
            roles = []
        return AuthPrincipal(user_id=user_id, email=payload.get("email"), roles=[str(r) for r in roles]), payload

