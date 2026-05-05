from datetime import date
from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import serializers

from .models import AIMetricsDaily, BookingMetricsDaily, KPIDaily, ModerationMetricsDaily, PaymentMetricsDaily


class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.CharField(required=False)
    end_date = serializers.CharField(required=False)

    def validate(self, attrs):
        range_value = str(self.initial_data.get("range", "") or "").strip().lower()
        today = timezone.now().date()
        if range_value:
            if range_value == "today":
                attrs["start_date"] = today.isoformat()
                attrs["end_date"] = today.isoformat()
            elif range_value.endswith("d") and range_value[:-1].isdigit():
                days = int(range_value[:-1])
                days = max(1, min(days, 365))
                attrs["start_date"] = (today - timedelta(days=days - 1)).isoformat()
                attrs["end_date"] = today.isoformat()

        start_date_raw = attrs.get("start_date")
        end_date_raw = attrs.get("end_date")

        parsed_start = parse_date(start_date_raw) if start_date_raw else None
        parsed_end = parse_date(end_date_raw) if end_date_raw else None
        if start_date_raw and parsed_start is None:
            raise serializers.ValidationError("Invalid start_date. Expected YYYY-MM-DD.")
        if end_date_raw and parsed_end is None:
            raise serializers.ValidationError("Invalid end_date. Expected YYYY-MM-DD.")
        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise serializers.ValidationError("start_date cannot be greater than end_date.")

        attrs["start_date"] = parsed_start
        attrs["end_date"] = parsed_end
        return attrs


class KPIDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = KPIDaily
        fields = "__all__"
        read_only_fields = (
            "id",
            "date",
            "active_users",
            "new_registrations",
            "total_bookings",
            "gross_volume",
            "pending_housing_count",
            "approved_housing_count",
            "notification_sent_count",
            "created_at",
            "updated_at",
        )


class BookingMetricsDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingMetricsDaily
        fields = "__all__"
        read_only_fields = ("id", "date", "pending_count", "confirmed_count", "cancelled_count", "created_at", "updated_at")


class PaymentMetricsDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMetricsDaily
        fields = "__all__"
        read_only_fields = ("id", "date", "success_count", "failure_count", "refund_count", "created_at", "updated_at")


class AIMetricsDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMetricsDaily
        fields = "__all__"
        read_only_fields = (
            "id",
            "date",
            "recommendation_click_rate",
            "match_accept_rate",
            "recommendation_events",
            "roommate_match_events",
            "created_at",
            "updated_at",
        )


class ModerationMetricsDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationMetricsDaily
        fields = "__all__"
        read_only_fields = (
            "id",
            "date",
            "complaints_opened",
            "complaints_resolved",
            "avg_resolution_hours",
            "created_at",
            "updated_at",
        )


class ExportQuerySerializer(DateRangeSerializer):
    report_type = serializers.ChoiceField(
        choices=(
            "kpis",
            "bookings",
            "payments",
            "housing",
            "ai_recommendations",
            "ai_roommates",
            "moderation",
        )
    )


def apply_date_range(queryset, start_date: date | None, end_date: date | None):
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    return queryset
