from django.contrib import admin

from .models import (
    Question,
    QuestionOption,
    Questionnaire,
    RoommateMatchResult,
    UserLifestyleVector,
    UserQuestionnaireAnswer,
)

admin.site.register(Questionnaire)
admin.site.register(Question)
admin.site.register(QuestionOption)
admin.site.register(UserQuestionnaireAnswer)
admin.site.register(UserLifestyleVector)
admin.site.register(RoommateMatchResult)

