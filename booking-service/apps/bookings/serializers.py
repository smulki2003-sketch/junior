from rest_framework import serializers

from .models import Booking, BookingStatusHistory


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = (
            "id",
            "user_id",
            "unit_id",
            "start_date",
            "end_date",
            "total_price",
            "status",
            "occupancy_reserved",
            "payment_intent_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user_id", "status", "occupancy_reserved", "payment_intent_id", "created_at", "updated_at")


class BookingCreateSerializer(serializers.Serializer):
    unit_id = serializers.IntegerField(min_value=1)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    payer_bank_name = serializers.CharField(max_length=128)
    payer_account_number = serializers.CharField(max_length=64)

    def validate(self, attrs):
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError("start_date cannot be after end_date.")
        if attrs["total_price"] <= 0:
            raise serializers.ValidationError("total_price must be greater than zero.")
        attrs["payer_bank_name"] = str(attrs["payer_bank_name"]).strip()
        attrs["payer_account_number"] = str(attrs["payer_account_number"]).strip()
        if not attrs["payer_bank_name"]:
            raise serializers.ValidationError("payer_bank_name is required.")
        if len(attrs["payer_account_number"]) < 6:
            raise serializers.ValidationError("payer_account_number must be at least 6 characters.")
        return attrs


class BookingStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=(
            Booking.STATUS_PENDING,
            Booking.STATUS_CONFIRMED,
            Booking.STATUS_COMPLETED,
            Booking.STATUS_CANCELLED,
            Booking.STATUS_FAILED,
        )
    )


class BookingStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingStatusHistory
        fields = ("id", "booking_id", "from_status", "to_status", "changed_by_user_id", "changed_at")
        read_only_fields = fields
