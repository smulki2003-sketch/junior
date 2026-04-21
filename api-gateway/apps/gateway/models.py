from django.db import models


class GatewayRouteRegistry(models.Model):
    route_prefix = models.CharField(max_length=64, unique=True)
    upstream_base_url = models.URLField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gateway_route_registry"
        ordering = ["route_prefix"]

    def __str__(self) -> str:
        return f"{self.route_prefix} -> {self.upstream_base_url}"


class GatewayRequestLog(models.Model):
    request_id = models.CharField(max_length=64, db_index=True)
    method = models.CharField(max_length=16)
    path = models.CharField(max_length=255)
    status_code = models.PositiveSmallIntegerField()
    duration_ms = models.PositiveIntegerField()
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_identifier = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gateway_request_logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.request_id} {self.method} {self.path} {self.status_code}"


class GatewayRateLimitPolicy(models.Model):
    SCOPE_IP = "ip"
    SCOPE_USER = "user"
    SCOPE_CHOICES = (
        (SCOPE_IP, "IP Address"),
        (SCOPE_USER, "User Identifier"),
    )

    scope = models.CharField(max_length=16, unique=True, choices=SCOPE_CHOICES)
    limit_per_minute = models.PositiveIntegerField()
    burst_limit = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gateway_rate_limit_policies"
        ordering = ["scope"]

    def __str__(self) -> str:
        return f"{self.scope}: {self.limit_per_minute}+{self.burst_limit}"
