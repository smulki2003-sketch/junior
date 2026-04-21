from django.db import models
from django.utils import timezone


class AuthUser(models.Model):
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "auth_users"
        ordering = ["id"]

    def __str__(self) -> str:
        return self.email

    @property
    def is_authenticated(self) -> bool:
        return True


class AuthRole(models.Model):
    ROLE_STUDENT = "student"
    ROLE_ADMIN = "admin"

    name = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auth_roles"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class AuthUserRole(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name="role_links")
    role = models.ForeignKey(AuthRole, on_delete=models.CASCADE, related_name="user_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auth_user_roles"
        unique_together = ("user", "role")
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.role_id}"


class AuthRefreshToken(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_jti = models.CharField(max_length=64, unique=True)
    is_revoked = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "auth_refresh_tokens"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.token_jti}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at


class AuthPasswordResetToken(models.Model):
    user = models.ForeignKey(AuthUser, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "auth_password_reset_tokens"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.token}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at


class AuthAuditLog(models.Model):
    user = models.ForeignKey(
        AuthUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    event_type = models.CharField(max_length=64)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auth_audit_logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.event_type}:{self.user_id}"
