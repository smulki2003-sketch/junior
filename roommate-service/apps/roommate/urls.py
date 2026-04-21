from django.urls import path

from .views import (
    QuestionnaireAnswerSubmissionView,
    QuestionnaireView,
    RoommateExplainView,
    RoommateMatchesListView,
    RoommateMatchesRefreshView,
)

urlpatterns = [
    path("ai/roommates/questionnaire", QuestionnaireView.as_view(), name="ai-roommates-questionnaire"),
    path("ai/roommates/answers/<int:user_id>", QuestionnaireAnswerSubmissionView.as_view(), name="ai-roommates-answers"),
    path("ai/roommates/matches/<int:user_id>/refresh", RoommateMatchesRefreshView.as_view(), name="ai-roommates-matches-refresh"),
    path("ai/roommates/matches/<int:user_id>", RoommateMatchesListView.as_view(), name="ai-roommates-matches-list"),
    path(
        "ai/roommates/matches/<int:user_id>/explain/<int:candidate_user_id>",
        RoommateExplainView.as_view(),
        name="ai-roommates-matches-explain",
    ),
]

