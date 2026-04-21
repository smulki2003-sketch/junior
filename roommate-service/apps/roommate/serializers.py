from rest_framework import serializers

from .models import Question, Questionnaire, QuestionOption, RoommateMatchResult, UserQuestionnaireAnswer


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ("id", "label", "numeric_value", "order_index")


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True)

    class Meta:
        model = Question
        fields = ("id", "dimension_key", "prompt", "weight", "order_index", "options")


class QuestionnaireSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Questionnaire
        fields = ("id", "title", "version", "is_active", "questions")


class QuestionnaireAdminUpsertSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    version = serializers.IntegerField(min_value=1)
    is_active = serializers.BooleanField(required=False, default=True)
    questions = serializers.ListField(child=serializers.DictField(), min_length=1)


class AnswerSubmissionSerializer(serializers.Serializer):
    answers = serializers.ListField(child=serializers.DictField(), min_length=1)


class RefreshMatchesSerializer(serializers.Serializer):
    top_n = serializers.IntegerField(min_value=1, max_value=100, required=False, default=10)
    scoring_mode = serializers.ChoiceField(choices=("cosine", "euclidean"), required=False, default="cosine")
    location = serializers.CharField(required=False, allow_blank=True, default="")


class MatchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoommateMatchResult
        fields = ("user_id", "candidate_user_id", "score", "rank", "scoring_mode", "explanation_json", "generated_at")


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuestionnaireAnswer
        fields = ("id", "user_id", "question_id", "selected_option_id", "created_at")
        read_only_fields = ("id", "created_at")

