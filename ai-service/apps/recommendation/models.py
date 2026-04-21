from django.db import models


class HousingFeatureVector(models.Model):
    unit_id = models.PositiveIntegerField(unique=True, db_index=True)
    vector_json = models.JSONField(default=list)
    metadata_json = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "housing_feature_vectors"
        ordering = ["-generated_at", "-id"]


class UserPreferenceVector(models.Model):
    user_id = models.PositiveIntegerField(unique=True, db_index=True)
    vector_json = models.JSONField(default=list)
    metadata_json = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_preference_vectors"
        ordering = ["-generated_at", "-id"]


class HousingRecommendationResult(models.Model):
    user_id = models.PositiveIntegerField(db_index=True)
    unit_id = models.PositiveIntegerField(db_index=True)
    similarity_score = models.FloatField(db_index=True)
    rank = models.PositiveIntegerField()
    reasoning_json = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "housing_recommendation_results"
        ordering = ["rank", "-similarity_score", "unit_id"]
        unique_together = ("user_id", "unit_id", "generated_at")


class RecommendationFeedback(models.Model):
    FEEDBACK_LIKE = "like"
    FEEDBACK_DISLIKE = "dislike"
    FEEDBACK_CHOICES = ((FEEDBACK_LIKE, "Like"), (FEEDBACK_DISLIKE, "Dislike"))

    user_id = models.PositiveIntegerField(db_index=True)
    unit_id = models.PositiveIntegerField(db_index=True)
    feedback_type = models.CharField(max_length=16, choices=FEEDBACK_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendation_feedback"
        ordering = ["-created_at", "-id"]

