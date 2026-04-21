from django.db import models


class Questionnaire(models.Model):
    title = models.CharField(max_length=200)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questionnaires"
        ordering = ["-version", "-id"]


class Question(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name="questions")
    dimension_key = models.CharField(max_length=64, db_index=True)
    prompt = models.CharField(max_length=300)
    weight = models.FloatField(default=1.0)
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "questions"
        ordering = ["order_index", "id"]


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=120)
    numeric_value = models.FloatField()
    order_index = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "question_options"
        ordering = ["order_index", "id"]


class UserQuestionnaireAnswer(models.Model):
    user_id = models.PositiveIntegerField(db_index=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    selected_option = models.ForeignKey(QuestionOption, on_delete=models.CASCADE, related_name="selected_answers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_questionnaire_answers"
        ordering = ["-created_at", "-id"]
        unique_together = ("user_id", "question")


class UserLifestyleVector(models.Model):
    user_id = models.PositiveIntegerField(unique=True, db_index=True)
    vector_json = models.JSONField(default=list)
    dimensions_json = models.JSONField(default=list)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_lifestyle_vectors"
        ordering = ["-generated_at", "-id"]


class RoommateMatchResult(models.Model):
    user_id = models.PositiveIntegerField(db_index=True)
    candidate_user_id = models.PositiveIntegerField(db_index=True)
    score = models.FloatField(db_index=True)
    rank = models.PositiveIntegerField()
    scoring_mode = models.CharField(max_length=16, default="cosine")
    explanation_json = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "roommate_match_results"
        ordering = ["rank", "-score", "candidate_user_id"]

