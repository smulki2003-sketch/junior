from django.contrib import admin

from .models import Notification, NotificationDeliveryLog, NotificationTemplate, UserNotificationPreference

admin.site.register(NotificationTemplate)
admin.site.register(Notification)
admin.site.register(UserNotificationPreference)
admin.site.register(NotificationDeliveryLog)

