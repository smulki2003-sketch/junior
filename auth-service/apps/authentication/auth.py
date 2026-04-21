from __future__ import annotations

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import AuthUser
from .services import TokenError, decode_access_token


class JWTAccessAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return None

        keyword, _, token = auth_header.partition(" ")
        if keyword != self.keyword or not token:
            raise AuthenticationFailed("Invalid authorization header format.")

        try:
            payload = decode_access_token(token)
        except TokenError as exc:
            raise AuthenticationFailed(str(exc)) from exc

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationFailed("Access token missing subject claim.")

        user = AuthUser.objects.filter(id=user_id, is_active=True).first()
        if user is None:
            raise AuthenticationFailed("User not found or inactive.")

        return user, payload

