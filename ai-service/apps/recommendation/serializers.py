from rest_framework import serializers

from .models import HousingRecommendationResult, RecommendationFeedback


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationFeedback
        fields = ("id", "user_id", "unit_id", "feedback_type", "created_at")
        read_only_fields = ("id", "created_at")


class RecommendationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingRecommendationResult
        fields = ("user_id", "unit_id", "similarity_score", "rank", "reasoning_json", "generated_at")
        read_only_fields = fields


class RefreshRequestSerializer(serializers.Serializer):
    top_n = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)

