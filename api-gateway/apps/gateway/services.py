from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from django.conf import settings
from django.db import DatabaseError

from .models import GatewayRouteRegistry


@dataclass
class RouteConfig:
    route_prefix: str
    upstream_base_url: str
    is_active: bool = True


def get_route_config(route_prefix: str) -> RouteConfig | None:
    try:
        route = GatewayRouteRegistry.objects.filter(route_prefix=route_prefix, is_active=True).first()
        if route:
            return RouteConfig(
                route_prefix=route.route_prefix,
                upstream_base_url=route.upstream_base_url.rstrip("/"),
                is_active=route.is_active,
            )
    except DatabaseError:
        pass

    upstream = settings.GATEWAY_SERVICE_MAP.get(route_prefix)
    if not upstream:
        return None
    return RouteConfig(route_prefix=route_prefix, upstream_base_url=upstream.rstrip("/"))


def list_active_routes() -> list[RouteConfig]:
    try:
        routes = list(
            GatewayRouteRegistry.objects.filter(is_active=True).values_list(
                "route_prefix",
                "upstream_base_url",
                "is_active",
            )
        )
        if routes:
            return [
                RouteConfig(route_prefix=route_prefix, upstream_base_url=upstream_base_url, is_active=is_active)
                for route_prefix, upstream_base_url, is_active in routes
            ]
    except DatabaseError:
        pass

    return [
        RouteConfig(route_prefix=key, upstream_base_url=value, is_active=True)
        for key, value in sorted(settings.GATEWAY_SERVICE_MAP.items())
    ]


def build_upstream_url(base_url: str, subpath: str) -> str:
    if not subpath:
        return base_url
    return urljoin(f"{base_url.rstrip('/')}/", subpath.lstrip("/"))

