from django.db import models


class AdminActionLog(models.Model):
    admin_user_id = models.PositiveIntegerField(db_index=True)
    action_key = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=64, db_index=True)
    target_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "admin_action_logs"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"admin-action:{self.id}:{self.action_key}"


class AdminSavedView(models.Model):
    admin_user_id = models.PositiveIntegerField(db_index=True)
    name = models.CharField(max_length=150)
    filters_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "admin_saved_views"
        ordering = ["name", "-updated_at"]
        unique_together = ("admin_user_id", "name")

    def __str__(self) -> str:
        return f"admin-saved-view:{self.admin_user_id}:{self.name}"


class AdminNote(models.Model):
    admin_user_id = models.PositiveIntegerField(db_index=True)
    target_type = models.CharField(max_length=64, db_index=True)
    target_id = models.CharField(max_length=64, db_index=True)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "admin_notes"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"admin-note:{self.target_type}:{self.target_id}"

