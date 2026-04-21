from django.db import models


class PaymentIntent(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
    )

    booking_id = models.PositiveIntegerField(db_index=True)
    user_id = models.PositiveIntegerField(db_index=True)
    payer_bank_name = models.CharField(max_length=128, blank=True, default="")
    payer_account_number = models.CharField(max_length=64, blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment_intents"
        ordering = ["-created_at", "-id"]


class PaymentTransaction(models.Model):
    RESULT_SUCCESS = "success"
    RESULT_FAILURE = "failure"
    RESULT_CHOICES = (
        (RESULT_SUCCESS, "Success"),
        (RESULT_FAILURE, "Failure"),
    )

    payment_intent = models.ForeignKey(PaymentIntent, on_delete=models.CASCADE, related_name="transactions")
    transaction_ref = models.CharField(max_length=64, unique=True)
    result = models.CharField(max_length=16, choices=RESULT_CHOICES)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_transactions"
        ordering = ["-processed_at", "-id"]


class PaymentRefund(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
    )

    payment_intent = models.ForeignKey(PaymentIntent, on_delete=models.CASCADE, related_name="refunds")
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_SUCCEEDED)
    idempotency_key = models.CharField(max_length=128, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_refunds"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["payment_intent", "idempotency_key"],
                condition=~models.Q(idempotency_key=""),
                name="unique_refund_idempotency_per_intent",
            )
        ]


class PaymentAuditLog(models.Model):
    payment_intent = models.ForeignKey(PaymentIntent, on_delete=models.CASCADE, related_name="audit_logs")
    event_type = models.CharField(max_length=64, db_index=True)
    payload_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_audit_logs"
        ordering = ["-created_at", "-id"]
