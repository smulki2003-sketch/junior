from django.db import models


class NotificationTemplate(models.Model):
    event_key = models.CharField(max_length=100, unique=True, db_index=True)
    title_template = models.CharField(max_length=255)
    body_template = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_templates"
        ordering = ["event_key"]


class Notification(models.Model):
    user_id = models.PositiveIntegerField(db_index=True)
    event_key = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at", "-id"]


class UserNotificationPreference(models.Model):
    user_id = models.PositiveIntegerField(db_index=True)
    event_key = models.CharField(max_length=100, db_index=True)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_notification_preferences"
        unique_together = ("user_id", "event_key")
        ordering = ["user_id", "event_key"]


class NotificationDeliveryLog(models.Model):
    CHANNEL_IN_APP = "in_app"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    CHANNEL_CHOICES = ((CHANNEL_IN_APP, "In App"),)
    STATUS_CHOICES = ((STATUS_SENT, "Sent"), (STATUS_FAILED, "Failed"))

    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="delivery_logs")
    channel = models.CharField(max_length=32, choices=CHANNEL_CHOICES, default=CHANNEL_IN_APP)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_SENT)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification_delivery_logs"
        ordering = ["-created_at", "-id"]

