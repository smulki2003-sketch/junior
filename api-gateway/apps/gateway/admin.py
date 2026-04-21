from django.contrib import admin

from .models import GatewayRateLimitPolicy, GatewayRequestLog, GatewayRouteRegistry


@admin.register(GatewayRouteRegistry)
class GatewayRouteRegistryAdmin(admin.ModelAdmin):
    list_display = ("route_prefix", "upstream_base_url", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("route_prefix", "upstream_base_url")


@admin.register(GatewayRequestLog)
class GatewayRequestLogAdmin(admin.ModelAdmin):
    list_display = ("request_id", "method", "path", "status_code", "duration_ms", "created_at")
    list_filter = ("method", "status_code")
    search_fields = ("request_id", "path", "user_identifier")
    readonly_fields = (
        "request_id",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "client_ip",
        "user_identifier",
        "created_at",
    )


@admin.register(GatewayRateLimitPolicy)
class GatewayRateLimitPolicyAdmin(admin.ModelAdmin):
    list_display = ("scope", "limit_per_minute", "burst_limit", "is_active", "updated_at")
    list_filter = ("scope", "is_active")
