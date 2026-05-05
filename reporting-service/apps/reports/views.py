from __future__ import annotations

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AIMetricsDaily, BookingMetricsDaily, KPIDaily, ModerationMetricsDaily, PaymentMetricsDaily
from .permissions import IsAdminOrServiceRole
from .serializers import (
    AIMetricsDailySerializer,
    BookingMetricsDailySerializer,
    DateRangeSerializer,
    ExportQuerySerializer,
    KPIDailySerializer,
    ModerationMetricsDailySerializer,
    PaymentMetricsDailySerializer,
    apply_date_range,
)
from .services import aggregate_daily_metrics, csv_from_rows
from .services import compute_live_kpi_rows, summarize_kpi_rows


def _validated_range(query_params):
    serializer = DateRangeSerializer(data=query_params)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data["start_date"], serializer.validated_data["end_date"]


class ReportsKPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        if request.query_params.get("refresh", "").lower() in {"1", "true", "yes"}:
            aggregate_daily_metrics()
        start_date, end_date = _validated_range(request.query_params)
        data = compute_live_kpi_rows(start_date, end_date)
        has_live_signal = any(
            int(item.get("active_users", 0)) > 0
            or int(item.get("new_registrations", 0)) > 0
            or int(item.get("total_bookings", 0)) > 0
            for item in data
        )
        if not has_live_signal:
            queryset = apply_date_range(KPIDaily.objects.all().order_by("date"), start_date, end_date)
            data = KPIDailySerializer(queryset, many=True).data
        summary = summarize_kpi_rows(data)
        return Response({"summary": summary, "results": data}, status=status.HTTP_200_OK)


class ReportsBookingsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        start_date, end_date = _validated_range(request.query_params)
        queryset = apply_date_range(BookingMetricsDaily.objects.all().order_by("date"), start_date, end_date)
        return Response(BookingMetricsDailySerializer(queryset, many=True).data, status=status.HTTP_200_OK)


class ReportsPaymentsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        start_date, end_date = _validated_range(request.query_params)
        queryset = apply_date_range(PaymentMetricsDaily.objects.all().order_by("date"), start_date, end_date)
        data = PaymentMetricsDailySerializer(queryset, many=True).data
        enriched = []
        for item in data:
            success = item["success_count"]
            failure = item["failure_count"]
            total = success + failure
            conversion = (success / total) if total else 0.0
            enriched.append({**item, "conversion_rate": round(conversion, 4)})
        return Response(enriched, status=status.HTTP_200_OK)


class ReportsHousingView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        start_date, end_date = _validated_range(request.query_params)
        queryset = apply_date_range(KPIDaily.objects.all().order_by("date"), start_date, end_date)
        rows = []
        for item in queryset:
            inventory_total = item.pending_housing_count + item.approved_housing_count
            occupancy = (item.total_bookings / inventory_total) if inventory_total else 0
            rows.append(
                {
                    "date": item.date,
                    "pending_housing_count": item.pending_housing_count,
                    "approved_housing_count": item.approved_housing_count,
                    "inventory_total": inventory_total,
                    "occupancy_metric": round(occupancy, 4),
                }
            )
        return Response(rows, status=status.HTTP_200_OK)


class ReportsAIRecommendationsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        start_date, end_date = _validated_range(request.query_params)
        queryset = apply_date_range(AIMetricsDaily.objects.all().order_by("date"), start_date, end_date)
        data = AIMetricsDailySerializer(queryset, many=True).data
        for item in data:
            item["quality_score"] = round(float(item["recommendation_click_rate"]) * 100, 2)
        return Response(data, status=status.HTTP_200_OK)


class ReportsAIRoommatesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        start_date, end_date = _validated_range(request.query_params)
        queryset = apply_date_range(AIMetricsDaily.objects.all().order_by("date"), start_date, end_date)
        data = AIMetricsDailySerializer(queryset, many=True).data
        for item in data:
            item["match_quality_score"] = round(float(item["match_accept_rate"]) * 100, 2)
        return Response(data, status=status.HTTP_200_OK)


class ReportsModerationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        start_date, end_date = _validated_range(request.query_params)
        queryset = apply_date_range(ModerationMetricsDaily.objects.all().order_by("date"), start_date, end_date)
        return Response(ModerationMetricsDailySerializer(queryset, many=True).data, status=status.HTTP_200_OK)


class ReportsExportView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        serializer = ExportQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        report_type = serializer.validated_data["report_type"]
        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]

        if report_type == "kpis":
            queryset = apply_date_range(KPIDaily.objects.all().order_by("date"), start_date, end_date)
            headers = ["date", "active_users", "new_registrations", "total_bookings", "gross_volume", "notification_sent_count"]
            rows = [
                [item.date, item.active_users, item.new_registrations, item.total_bookings, item.gross_volume, item.notification_sent_count]
                for item in queryset
            ]
        elif report_type == "bookings":
            queryset = apply_date_range(BookingMetricsDaily.objects.all().order_by("date"), start_date, end_date)
            headers = ["date", "pending_count", "confirmed_count", "cancelled_count"]
            rows = [[item.date, item.pending_count, item.confirmed_count, item.cancelled_count] for item in queryset]
        elif report_type == "payments":
            queryset = apply_date_range(PaymentMetricsDaily.objects.all().order_by("date"), start_date, end_date)
            headers = ["date", "success_count", "failure_count", "refund_count"]
            rows = [[item.date, item.success_count, item.failure_count, item.refund_count] for item in queryset]
        elif report_type == "housing":
            queryset = apply_date_range(KPIDaily.objects.all().order_by("date"), start_date, end_date)
            headers = ["date", "pending_housing_count", "approved_housing_count"]
            rows = [[item.date, item.pending_housing_count, item.approved_housing_count] for item in queryset]
        elif report_type == "ai_recommendations":
            queryset = apply_date_range(AIMetricsDaily.objects.all().order_by("date"), start_date, end_date)
            headers = ["date", "recommendation_click_rate", "recommendation_events"]
            rows = [[item.date, item.recommendation_click_rate, item.recommendation_events] for item in queryset]
        elif report_type == "ai_roommates":
            queryset = apply_date_range(AIMetricsDaily.objects.all().order_by("date"), start_date, end_date)
            headers = ["date", "match_accept_rate", "roommate_match_events"]
            rows = [[item.date, item.match_accept_rate, item.roommate_match_events] for item in queryset]
        else:
            queryset = apply_date_range(ModerationMetricsDaily.objects.all().order_by("date"), start_date, end_date)
            headers = ["date", "complaints_opened", "complaints_resolved", "avg_resolution_hours"]
            rows = [[item.date, item.complaints_opened, item.complaints_resolved, item.avg_resolution_hours] for item in queryset]

        content = csv_from_rows(headers, rows)
        response = HttpResponse(content, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{report_type}_report.csv"'
        return response
