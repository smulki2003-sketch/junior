from __future__ import annotations

from dataclasses import dataclass

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication


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
            return None

        try:
            payload = jwt.decode(
                token,
                settings.AUTH_SERVICE_JWT_SECRET,
                algorithms=[settings.AUTH_SERVICE_JWT_ALGORITHM],
            )
        except jwt.InvalidTokenError:
            return None

        if payload.get("type") != "access":
            return None

        sub = payload.get("sub")
        if sub is None:
            return None
        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            return None

        roles = payload.get("roles", [])
        if not isinstance(roles, list):
            roles = []

        principal = AuthPrincipal(
            user_id=user_id,
            email=payload.get("email"),
            roles=[str(role) for role in roles],
        )
        return principal, payload
