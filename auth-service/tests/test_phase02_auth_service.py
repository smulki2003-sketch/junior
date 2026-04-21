from django.test import TestCase

from apps.authentication.models import AuthAuditLog, AuthRole, AuthUser, AuthUserRole
from apps.authentication.services import ensure_default_roles


class AuthServiceIntegrationTests(TestCase):
    def setUp(self):
        ensure_default_roles()

    def _register_user(self, email: str, password: str):
        return self.client.post(
            "/auth/register",
            data={"email": email, "password": password},
            content_type="application/json",
        )

    def _login(self, email: str, password: str):
        return self.client.post(
            "/auth/login",
            data={"email": email, "password": password},
            content_type="application/json",
        )

    def test_register_creates_user_with_student_role(self):
        response = self._register_user("student@example.com", "password123")
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["email"], "student@example.com")
        self.assertEqual(payload["roles"], ["student"])

        user = AuthUser.objects.get(email="student@example.com")
        student_role = AuthRole.objects.get(name="student")
        self.assertTrue(AuthUserRole.objects.filter(user=user, role=student_role).exists())

    def test_login_issue_tokens_and_me_endpoint(self):
        self._register_user("login@example.com", "password123")
        login_response = self._login("login@example.com", "password123")
        self.assertEqual(login_response.status_code, 200)
        tokens = login_response.json()["tokens"]
        self.assertIn("access_token", tokens)
        self.assertIn("refresh_token", tokens)

        me_response = self.client.get(
            "/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}",
        )
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["email"], "login@example.com")

    def test_refresh_returns_new_access_token(self):
        self._register_user("refresh@example.com", "password123")
        login_response = self._login("refresh@example.com", "password123")
        refresh_token = login_response.json()["tokens"]["refresh_token"]

        refresh_response = self.client.post(
            "/auth/refresh",
            data={"refresh_token": refresh_token},
            content_type="application/json",
        )
        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn("access_token", refresh_response.json()["tokens"])

    def test_logout_revokes_refresh_token(self):
        self._register_user("logout@example.com", "password123")
        login_response = self._login("logout@example.com", "password123")
        refresh_token = login_response.json()["tokens"]["refresh_token"]

        logout_response = self.client.post(
            "/auth/logout",
            data={"refresh_token": refresh_token},
            content_type="application/json",
        )
        self.assertEqual(logout_response.status_code, 200)
        self.assertTrue(logout_response.json()["token_revoked"])

        refresh_response = self.client.post(
            "/auth/refresh",
            data={"refresh_token": refresh_token},
            content_type="application/json",
        )
        self.assertEqual(refresh_response.status_code, 401)

    def test_password_reset_request_and_confirm(self):
        self._register_user("reset@example.com", "password123")
        request_response = self.client.post(
            "/auth/password-reset/request",
            data={"email": "reset@example.com"},
            content_type="application/json",
        )
        self.assertEqual(request_response.status_code, 200)
        token = request_response.json().get("reset_token")
        self.assertTrue(token)

        confirm_response = self.client.post(
            "/auth/password-reset/confirm",
            data={"token": token, "new_password": "newpassword123"},
            content_type="application/json",
        )
        self.assertEqual(confirm_response.status_code, 200)

        old_login = self._login("reset@example.com", "password123")
        self.assertEqual(old_login.status_code, 401)
        new_login = self._login("reset@example.com", "newpassword123")
        self.assertEqual(new_login.status_code, 200)

    def test_admin_can_update_roles(self):
        self._register_user("admin@example.com", "password123")
        admin_user = AuthUser.objects.get(email="admin@example.com")
        AuthUserRole.objects.filter(user=admin_user).delete()
        admin_role = AuthRole.objects.get(name="admin")
        AuthUserRole.objects.create(user=admin_user, role=admin_role)

        self._register_user("target@example.com", "password123")
        target_user = AuthUser.objects.get(email="target@example.com")

        login_response = self._login("admin@example.com", "password123")
        access_token = login_response.json()["tokens"]["access_token"]

        patch_response = self.client.patch(
            f"/auth/users/{target_user.id}/roles",
            data={"roles": ["student", "admin"]},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(sorted(patch_response.json()["roles"]), ["admin", "student"])

    def test_non_admin_cannot_update_roles(self):
        self._register_user("user1@example.com", "password123")
        self._register_user("user2@example.com", "password123")
        target_user = AuthUser.objects.get(email="user2@example.com")

        login_response = self._login("user1@example.com", "password123")
        access_token = login_response.json()["tokens"]["access_token"]

        patch_response = self.client.patch(
            f"/auth/users/{target_user.id}/roles",
            data={"roles": ["admin"]},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(patch_response.status_code, 403)

    def test_audit_logs_are_written(self):
        self._register_user("audit@example.com", "password123")
        self._login("audit@example.com", "password123")
        self.assertTrue(AuthAuditLog.objects.filter(event_type="register").exists())
        self.assertTrue(AuthAuditLog.objects.filter(event_type="login").exists())

