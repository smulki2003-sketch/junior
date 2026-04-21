from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from .models import Notification, NotificationDeliveryLog, NotificationTemplate, UserNotificationPreference


def _render(template_text: str, context: dict) -> str:
    rendered = template_text
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered


def is_event_enabled_for_user(user_id: int, event_key: str) -> bool:
    preference = UserNotificationPreference.objects.filter(user_id=user_id, event_key=event_key).first()
    if preference is None:
        return True
    return preference.is_enabled


@transaction.atomic
def create_notification(*, user_id: int, event_key: str, title: str, body: str, context: dict) -> Notification:
    if not is_event_enabled_for_user(user_id, event_key):
        raise ValueError("Notification preference disabled for this event.")

    if not title or not body:
        template = NotificationTemplate.objects.filter(event_key=event_key, is_active=True).first()
        if template:
            title = title or _render(template.title_template, context)
            body = body or _render(template.body_template, context)

    if not title:
        title = event_key
    if not body:
        body = f"Event received: {event_key}"

    notification = Notification.objects.create(
        user_id=user_id,
        event_key=event_key,
        title=title,
        body=body,
    )
    NotificationDeliveryLog.objects.create(
        notification=notification,
        channel=NotificationDeliveryLog.CHANNEL_IN_APP,
        status=NotificationDeliveryLog.STATUS_SENT,
    )
    return notification


def mark_notification_read(notification: Notification) -> Notification:
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
    return notification


def mark_all_read(user_id: int) -> int:
    unread = Notification.objects.filter(user_id=user_id, is_read=False)
    count = unread.count()
    if count:
        unread.update(is_read=True, read_at=timezone.now())
    return count

