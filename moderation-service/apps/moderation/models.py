from django.db import models


class Complaint(models.Model):
    TARGET_USER = "user"
    TARGET_HOUSING = "housing"
    TARGET_BOOKING = "booking"
    TARGET_CHOICES = (
        (TARGET_USER, "User"),
        (TARGET_HOUSING, "Housing"),
        (TARGET_BOOKING, "Booking"),
    )

    STATUS_SUBMITTED = "submitted"
    STATUS_TRIAGED = "triaged"
    STATUS_IN_REVIEW = "in_review"
    STATUS_RESOLVED = "resolved"
    STATUS_REJECTED = "rejected"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = (
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_TRIAGED, "Triaged"),
        (STATUS_IN_REVIEW, "In Review"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CLOSED, "Closed"),
    )

    reporter_user_id = models.PositiveIntegerField(db_index=True)
    target_type = models.CharField(max_length=16, choices=TARGET_CHOICES, db_index=True)
    target_id = models.PositiveIntegerField(db_index=True)
    reason = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_SUBMITTED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "complaints"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["reporter_user_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"complaint:{self.id}:{self.status}"


class ComplaintEvidence(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="evidence")
    file_url = models.URLField(max_length=500)
    file_type = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "complaint_evidence"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"complaint-evidence:{self.complaint_id}:{self.file_type}"


class ModerationCase(models.Model):
    PRIORITY_LOW = "low"
    PRIORITY_NORMAL = "normal"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"
    PRIORITY_CHOICES = (
        (PRIORITY_LOW, "Low"),
        (PRIORITY_NORMAL, "Normal"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    )

    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = (
        (STATUS_OPEN, "Open"),
        (STATUS_IN_PROGRESS, "In Progress"),
        (STATUS_RESOLVED, "Resolved"),
        (STATUS_CLOSED, "Closed"),
    )

    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, related_name="moderation_case")
    assigned_admin_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "moderation_cases"
        ordering = ["-updated_at", "-id"]

    def __str__(self) -> str:
        return f"case:{self.id}:{self.status}"


class ModerationAction(models.Model):
    ACTION_WARN = "warn"
    ACTION_SUSPEND = "suspend"
    ACTION_REJECT_LISTING = "reject_listing"
    ACTION_CHOICES = (
        (ACTION_WARN, "Warn"),
        (ACTION_SUSPEND, "Suspend"),
        (ACTION_REJECT_LISTING, "Reject Listing"),
    )

    case = models.ForeignKey(ModerationCase, on_delete=models.CASCADE, related_name="actions")
    action_type = models.CharField(max_length=32, choices=ACTION_CHOICES, db_index=True)
    target_type = models.CharField(max_length=16, choices=Complaint.TARGET_CHOICES, db_index=True)
    target_id = models.PositiveIntegerField(db_index=True)
    created_by_admin_id = models.PositiveIntegerField(db_index=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "moderation_actions"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"action:{self.id}:{self.action_type}"


class CaseComment(models.Model):
    case = models.ForeignKey(ModerationCase, on_delete=models.CASCADE, related_name="comments")
    admin_user_id = models.PositiveIntegerField(db_index=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "case_comments"
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return f"case-comment:{self.case_id}:{self.admin_user_id}"

