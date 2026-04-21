from django.conf import settings
from django.core.management.base import BaseCommand

from apps.gateway.models import GatewayRateLimitPolicy, GatewayRouteRegistry


class Command(BaseCommand):
    help = "Sync gateway route registry and rate limit policies with configured defaults."

    def handle(self, *args, **options):
        for prefix, upstream in settings.GATEWAY_SERVICE_MAP.items():
            GatewayRouteRegistry.objects.update_or_create(
                route_prefix=prefix,
                defaults={
                    "upstream_base_url": upstream,
                    "is_active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS("Gateway route registry synced."))

        for scope, policy in settings.GATEWAY_DEFAULT_RATE_LIMITS.items():
            GatewayRateLimitPolicy.objects.update_or_create(
                scope=scope,
                defaults={
                    "limit_per_minute": policy["limit_per_minute"],
                    "burst_limit": policy["burst_limit"],
                    "is_active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS("Gateway rate limit policies synced."))

