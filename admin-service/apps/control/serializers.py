from rest_framework import serializers

from .models import AdminActionLog, AdminNote, AdminSavedView


class AdminActionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminActionLog
        fields = ("id", "admin_user_id", "action_key", "target_type", "target_id", "metadata_json", "created_at")
        read_only_fields = fields


class AdminSavedViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminSavedView
        fields = ("id", "admin_user_id", "name", "filters_json", "created_at", "updated_at")
        read_only_fields = ("id", "admin_user_id", "created_at", "updated_at")


class AdminNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminNote
        fields = ("id", "admin_user_id", "target_type", "target_id", "note", "created_at")
        read_only_fields = ("id", "admin_user_id", "created_at")


class AdminUserStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("active", "suspended"))
    reason = serializers.CharField(min_length=3, max_length=2000)


class HousingApprovalUpdateSerializer(serializers.Serializer):
    approval = serializers.ChoiceField(choices=("approved", "rejected"))
    reason = serializers.CharField(min_length=3, max_length=2000, required=False, allow_blank=True)


class BookingStatusOverrideSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=("pending", "confirmed", "completed", "cancelled", "failed"))
    reason = serializers.CharField(min_length=3, max_length=2000)


class BroadcastSerializer(serializers.Serializer):
    title = serializers.CharField(min_length=3, max_length=255)
    body = serializers.CharField(min_length=3, max_length=2000)
    target_user_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )
    event_key = serializers.CharField(max_length=100, required=False, default="admin.broadcast")
