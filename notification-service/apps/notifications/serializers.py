from rest_framework import serializers

from .models import Notification, NotificationDeliveryLog, NotificationTemplate, UserNotificationPreference


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = ("id", "event_key", "title_template", "body_template", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("id", "user_id", "event_key", "title", "body", "is_read", "created_at", "read_at")
        read_only_fields = ("id", "is_read", "created_at", "read_at")


class NotificationSendSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    event_key = serializers.CharField(max_length=100)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    body = serializers.CharField(required=False, allow_blank=True, default="")
    context = serializers.JSONField(required=False, default=dict)


class PreferencesUpdateSerializer(serializers.Serializer):
    preferences = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )

    def validate_preferences(self, value):
        normalized = []
        for item in value:
            event_key = str(item.get("event_key", "")).strip()
            if not event_key:
                raise serializers.ValidationError("event_key is required.")
            normalized.append(
                {
                    "event_key": event_key,
                    "is_enabled": bool(item.get("is_enabled", True)),
                }
            )
        return normalized


class DeliveryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationDeliveryLog
        fields = ("id", "notification_id", "channel", "status", "error_message", "created_at")


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationPreference
        fields = ("id", "user_id", "event_key", "is_enabled", "created_at", "updated_at")

