from django.contrib import admin

from .models import PaymentAuditLog, PaymentIntent, PaymentRefund, PaymentTransaction

admin.site.register(PaymentIntent)
admin.site.register(PaymentTransaction)
admin.site.register(PaymentRefund)
admin.site.register(PaymentAuditLog)

