from django.urls import path, re_path

from .views import GatewayHealthView, GatewayReadinessView, GatewayRoutesView, ProxyServiceView


urlpatterns = [
    path("gateway/health", GatewayHealthView.as_view(), name="gateway-health"),
    path("gateway/ready", GatewayReadinessView.as_view(), name="gateway-ready"),
    path("gateway/routes", GatewayRoutesView.as_view(), name="gateway-routes"),
    re_path(
        r"^api/v1/(?P<service>[^/]+)(?:/(?P<subpath>.*))?$",
        ProxyServiceView.as_view(),
        name="gateway-proxy",
    ),
]

