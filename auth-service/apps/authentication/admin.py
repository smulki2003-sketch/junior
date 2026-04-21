from django.contrib import admin

from .models import (
    AuthAuditLog,
    AuthPasswordResetToken,
    AuthRefreshToken,
    AuthRole,
    AuthUser,
    AuthUserRole,
)


@admin.register(AuthUser)
class AuthUserAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("email",)


@admin.register(AuthRole)
class AuthRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)


@admin.register(AuthUserRole)
class AuthUserRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role", "created_at")
    list_filter = ("role__name",)


@admin.register(AuthRefreshToken)
class AuthRefreshTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "token_jti", "is_revoked", "expires_at", "created_at")
    list_filter = ("is_revoked",)
    search_fields = ("token_jti", "user__email")


@admin.register(AuthPasswordResetToken)
class AuthPasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "token", "is_used", "expires_at", "created_at")
    list_filter = ("is_used",)
    search_fields = ("token", "user__email")


@admin.register(AuthAuditLog)
class AuthAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "user", "ip_address", "created_at")
    search_fields = ("event_type", "user__email", "ip_address")
