from django.contrib import admin

from .models import CaseComment, Complaint, ComplaintEvidence, ModerationAction, ModerationCase


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter_user_id", "target_type", "target_id", "status", "created_at")
    list_filter = ("target_type", "status")
    search_fields = ("reason",)


@admin.register(ComplaintEvidence)
class ComplaintEvidenceAdmin(admin.ModelAdmin):
    list_display = ("id", "complaint_id", "file_type", "created_at")


@admin.register(ModerationCase)
class ModerationCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "complaint_id", "assigned_admin_id", "priority", "status", "updated_at")
    list_filter = ("priority", "status")


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ("id", "case_id", "action_type", "target_type", "target_id", "created_at")
    list_filter = ("action_type", "target_type")


@admin.register(CaseComment)
class CaseCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "case_id", "admin_user_id", "created_at")

