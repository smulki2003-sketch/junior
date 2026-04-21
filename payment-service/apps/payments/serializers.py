from rest_framework import serializers

from .models import PaymentAuditLog, PaymentIntent, PaymentRefund, PaymentTransaction


class PaymentIntentCreateSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField(min_value=1)
    user_id = serializers.IntegerField(min_value=1)
    payer_bank_name = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")
    payer_account_number = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=8, required=False, default="USD")

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("amount must be greater than zero.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        bank_name = str(attrs.get("payer_bank_name", "")).strip()
        account_number = str(attrs.get("payer_account_number", "")).strip()
        if not bank_name:
            raise serializers.ValidationError({"payer_bank_name": "Bank name is required."})
        if len(account_number) < 6:
            raise serializers.ValidationError({"payer_account_number": "Account number must be at least 6 characters."})
        attrs["payer_bank_name"] = bank_name
        attrs["payer_account_number"] = account_number
        return attrs


class PaymentCallbackSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField(min_value=1)
    booking_status = serializers.ChoiceField(choices=("confirmed", "failed", "cancelled"))


class RefundCreateSerializer(serializers.Serializer):
    refund_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")

    def validate_refund_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("refund_amount must be greater than zero.")
        return value


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ("id", "payment_intent_id", "transaction_ref", "result", "processed_at")


class PaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRefund
        fields = ("id", "payment_intent_id", "refund_amount", "status", "idempotency_key", "created_at")


class PaymentAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAuditLog
        fields = ("id", "payment_intent_id", "event_type", "payload_json", "created_at")


class PaymentIntentSerializer(serializers.ModelSerializer):
    transactions = PaymentTransactionSerializer(many=True, read_only=True)
    refunds = PaymentRefundSerializer(many=True, read_only=True)

    class Meta:
        model = PaymentIntent
        fields = (
            "id",
            "booking_id",
            "user_id",
            "payer_bank_name",
            "payer_account_number",
            "amount",
            "currency",
            "status",
            "created_at",
            "updated_at",
            "transactions",
            "refunds",
        )
