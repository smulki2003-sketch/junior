from django.contrib import admin

from .models import AdminActionLog, AdminNote, AdminSavedView


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "admin_user_id", "action_key", "target_type", "target_id", "created_at")
    list_filter = ("action_key", "target_type")


@admin.register(AdminSavedView)
class AdminSavedViewAdmin(admin.ModelAdmin):
    list_display = ("id", "admin_user_id", "name", "updated_at")


@admin.register(AdminNote)
class AdminNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "admin_user_id", "target_type", "target_id", "created_at")

