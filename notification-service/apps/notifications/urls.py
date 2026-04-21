from django.urls import path

from .views import (
    NotificationEventsBridgeView,
    NotificationInboxView,
    NotificationPreferenceUpdateView,
    NotificationReadAllView,
    NotificationReadView,
    NotificationSendView,
    NotificationTemplateListCreateView,
)

urlpatterns = [
    path("notifications/send", NotificationSendView.as_view(), name="notifications-send"),
    path("notifications/events", NotificationEventsBridgeView.as_view(), name="notifications-events-bridge"),
    path("notifications/users/<int:user_id>", NotificationInboxView.as_view(), name="notifications-inbox"),
    path("notifications/<int:notification_id>/read", NotificationReadView.as_view(), name="notifications-read"),
    path("notifications/users/<int:user_id>/read-all", NotificationReadAllView.as_view(), name="notifications-read-all"),
    path("notifications/templates", NotificationTemplateListCreateView.as_view(), name="notifications-templates"),
    path(
        "notifications/users/<int:user_id>/preferences",
        NotificationPreferenceUpdateView.as_view(),
        name="notifications-preferences",
    ),
]

