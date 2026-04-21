from django.urls import path

from .views import (
    HousingRecommendationExplainView,
    HousingRecommendationFeedbackView,
    HousingRecommendationListView,
    HousingRecommendationRefreshView,
)

urlpatterns = [
    path(
        "ai/recommendations/housing/<int:user_id>/refresh",
        HousingRecommendationRefreshView.as_view(),
        name="ai-housing-recommendations-refresh",
    ),
    path(
        "ai/recommendations/housing/<int:user_id>",
        HousingRecommendationListView.as_view(),
        name="ai-housing-recommendations-list",
    ),
    path(
        "ai/recommendations/housing/<int:user_id>/feedback",
        HousingRecommendationFeedbackView.as_view(),
        name="ai-housing-recommendations-feedback",
    ),
    path(
        "ai/recommendations/housing/<int:user_id>/explain/<int:unit_id>",
        HousingRecommendationExplainView.as_view(),
        name="ai-housing-recommendations-explain",
    ),
]

