from django.urls import path

from .views import (
    HousingPreferenceView,
    LifestylePreferenceView,
    ProfileMetadataView,
    ProfileCompletionView,
    UserProfileView,
)


urlpatterns = [
    path("users/metadata/profile-options", ProfileMetadataView.as_view(), name="profile-metadata"),
    path("users/<int:user_id>/profile", UserProfileView.as_view(), name="user-profile"),
    path(
        "users/<int:user_id>/preferences/housing",
        HousingPreferenceView.as_view(),
        name="housing-preference",
    ),
    path(
        "users/<int:user_id>/preferences/lifestyle",
        LifestylePreferenceView.as_view(),
        name="lifestyle-preference",
    ),
    path(
        "users/<int:user_id>/profile-completion",
        ProfileCompletionView.as_view(),
        name="profile-completion",
    ),
]
