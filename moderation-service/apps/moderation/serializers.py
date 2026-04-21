from rest_framework import serializers

from .models import CaseComment, Complaint, ComplaintEvidence, ModerationAction, ModerationCase


class ComplaintEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintEvidence
        fields = ("id", "complaint_id", "file_url", "file_type", "created_at")
        read_only_fields = ("id", "complaint_id", "created_at")


class CaseCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseComment
        fields = ("id", "case_id", "admin_user_id", "comment", "created_at")
        read_only_fields = ("id", "case_id", "admin_user_id", "created_at")


class ModerationActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationAction
        fields = (
            "id",
            "case_id",
            "action_type",
            "target_type",
            "target_id",
            "created_by_admin_id",
            "metadata_json",
            "created_at",
        )
        read_only_fields = ("id", "case_id", "created_by_admin_id", "created_at")


class ModerationCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationCase
        fields = (
            "id",
            "complaint_id",
            "assigned_admin_id",
            "priority",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "complaint_id", "created_at", "updated_at")


class ComplaintSerializer(serializers.ModelSerializer):
    evidence = ComplaintEvidenceSerializer(many=True, read_only=True)
    moderation_case = ModerationCaseSerializer(read_only=True)

    class Meta:
        model = Complaint
        fields = (
            "id",
            "reporter_user_id",
            "target_type",
            "target_id",
            "reason",
            "status",
            "created_at",
            "updated_at",
            "evidence",
            "moderation_case",
        )
        read_only_fields = ("id", "reporter_user_id", "status", "created_at", "updated_at", "evidence", "moderation_case")


class ComplaintCreateSerializer(serializers.Serializer):
    class EvidenceItemSerializer(serializers.Serializer):
        file_url = serializers.URLField(max_length=500)
        file_type = serializers.CharField(max_length=64)

    target_type = serializers.ChoiceField(choices=(Complaint.TARGET_USER, Complaint.TARGET_HOUSING, Complaint.TARGET_BOOKING))
    target_id = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(min_length=10, max_length=4000)
    evidence = EvidenceItemSerializer(many=True, required=False, allow_empty=True)


class ComplaintStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[choice[0] for choice in Complaint.STATUS_CHOICES], required=False)
    case_status = serializers.ChoiceField(choices=[choice[0] for choice in ModerationCase.STATUS_CHOICES], required=False)
    assigned_admin_id = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    priority = serializers.ChoiceField(choices=[choice[0] for choice in ModerationCase.PRIORITY_CHOICES], required=False)
    internal_note = serializers.CharField(required=False, allow_blank=False, max_length=2000)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one field must be provided.")
        return attrs


class ModerationActionCreateSerializer(serializers.Serializer):
    action_type = serializers.ChoiceField(choices=[choice[0] for choice in ModerationAction.ACTION_CHOICES])
    target_type = serializers.ChoiceField(choices=(Complaint.TARGET_USER, Complaint.TARGET_HOUSING, Complaint.TARGET_BOOKING))
    target_id = serializers.IntegerField(min_value=1)
    metadata_json = serializers.JSONField(required=False)


class CaseCommentCreateSerializer(serializers.Serializer):
    comment = serializers.CharField(min_length=2, max_length=4000)

