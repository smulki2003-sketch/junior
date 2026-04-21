from django.urls import path

from .views import (
    CaseCommentCreateView,
    ComplaintDetailView,
    ComplaintListCreateView,
    ComplaintStatusUpdateView,
    ModerationActionCreateView,
)


urlpatterns = [
    path("moderation/complaints", ComplaintListCreateView.as_view(), name="moderation-complaints-list-create"),
    path("moderation/complaints/<int:complaint_id>", ComplaintDetailView.as_view(), name="moderation-complaint-detail"),
    path(
        "moderation/complaints/<int:complaint_id>/status",
        ComplaintStatusUpdateView.as_view(),
        name="moderation-complaint-status-update",
    ),
    path(
        "moderation/cases/<int:case_id>/actions",
        ModerationActionCreateView.as_view(),
        name="moderation-case-action-create",
    ),
    path(
        "moderation/cases/<int:case_id>/comments",
        CaseCommentCreateView.as_view(),
        name="moderation-case-comment-create",
    ),
]

