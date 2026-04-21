from __future__ import annotations

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .banks import SYRIAN_BANKS
from .integrations import BookingServiceClient, NotificationServiceClient
from .models import PaymentIntent
from .permissions import IsAdminOrServiceRole, IsOwnerAdminOrService
from .serializers import (
    PaymentCallbackSerializer,
    PaymentIntentCreateSerializer,
    PaymentIntentSerializer,
    RefundCreateSerializer,
)
from .services import create_payment_intent, create_refund, mark_payment_result


def _is_admin(request) -> bool:
    return bool(request.user and getattr(request.user, "is_authenticated", False) and "admin" in getattr(request.user, "roles", []))


def _is_service_role(request) -> bool:
    return bool(request.user and getattr(request.user, "is_authenticated", False) and "service" in getattr(request.user, "roles", []))


class PaymentIntentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (_is_admin(request) or _is_service_role(request)):
            return Response(status=status.HTTP_403_FORBIDDEN)

        queryset = PaymentIntent.objects.all().order_by("-created_at", "-id")
        user_id = request.query_params.get("user_id")
        booking_id = request.query_params.get("booking_id")
        status_filter = request.query_params.get("status")
        payment_ids_raw = request.query_params.get("payment_ids", "")

        if user_id and user_id.isdigit():
            queryset = queryset.filter(user_id=int(user_id))
        if booking_id and booking_id.isdigit():
            queryset = queryset.filter(booking_id=int(booking_id))
        if status_filter:
            queryset = queryset.filter(status=str(status_filter).strip().lower())

        payment_ids = []
        for item in str(payment_ids_raw).split(","):
            value = item.strip()
            if value.isdigit():
                payment_ids.append(int(value))
        if payment_ids:
            queryset = queryset.filter(id__in=payment_ids)

        limit = request.query_params.get("limit")
        if limit and str(limit).isdigit():
            queryset = queryset[: max(1, min(int(limit), 500))]
        else:
            queryset = queryset[:200]

        return Response(PaymentIntentSerializer(list(queryset), many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PaymentIntentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not (_is_admin(request) or _is_service_role(request)):
            if int(serializer.validated_data["user_id"]) != int(request.user.id):
                return Response(status=status.HTTP_403_FORBIDDEN)
        payment = create_payment_intent(**serializer.validated_data)
        return Response(
            {
                "payment_intent_id": payment.id,
                "status": payment.status,
                "booking_id": payment.booking_id,
                "amount": str(payment.amount),
                "currency": payment.currency,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_id: int):
        payment = PaymentIntent.objects.filter(id=payment_id).first()
        if payment is None:
            return Response({"error": {"code": "payment_not_found", "message": "Payment not found."}}, status=404)
        if not IsOwnerAdminOrService().has_object_permission(request, self, payment):
            return Response(status=403)
        return Response(PaymentIntentSerializer(payment).data, status=200)


class _SimulationBaseView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_payment(self, payment_id: int):
        payment = PaymentIntent.objects.filter(id=payment_id).first()
        if payment is None:
            return None, Response({"error": {"code": "payment_not_found", "message": "Payment not found."}}, status=404)
        if not IsOwnerAdminOrService().has_object_permission(self.request, self, payment):
            return None, Response(status=403)
        return payment, None

    def _post_outcome(self, payment: PaymentIntent, success: bool):
        payment = mark_payment_result(payment, success=success)

        booking_status = "confirmed" if payment.status == PaymentIntent.STATUS_SUCCEEDED else "failed"
        booking_client = BookingServiceClient(settings.BOOKING_SERVICE_BASE_URL, settings.INTERNAL_SERVICE_TOKEN)
        booking_client.update_booking_status(payment.booking_id, booking_status)

        notification_client = NotificationServiceClient(
            settings.NOTIFICATION_SERVICE_BASE_URL,
            settings.INTERNAL_SERVICE_TOKEN,
        )
        notification_client.send_payment_notification(
            payment.user_id,
            "payment.succeeded" if success else "payment.failed",
            {"payment_id": payment.id, "booking_id": payment.booking_id, "amount": str(payment.amount)},
        )
        return payment


class PaymentSimulateSuccessView(_SimulationBaseView):
    def post(self, request, payment_id: int):
        payment, error_response = self._get_payment(payment_id)
        if error_response:
            return error_response
        payment = self._post_outcome(payment, success=True)
        return Response(PaymentIntentSerializer(payment).data, status=200)


class PaymentSimulateFailureView(_SimulationBaseView):
    def post(self, request, payment_id: int):
        payment, error_response = self._get_payment(payment_id)
        if error_response:
            return error_response
        payment = self._post_outcome(payment, success=False)
        return Response(PaymentIntentSerializer(payment).data, status=200)


class PaymentRefundView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_id: int):
        payment = PaymentIntent.objects.filter(id=payment_id).first()
        if payment is None:
            return Response({"error": {"code": "payment_not_found", "message": "Payment not found."}}, status=404)
        if not (IsOwnerAdminOrService().has_object_permission(request, self, payment) or _is_admin(request)):
            return Response(status=403)
        serializer = RefundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refund = create_refund(payment, **serializer.validated_data)

        NotificationServiceClient(
            settings.NOTIFICATION_SERVICE_BASE_URL,
            settings.INTERNAL_SERVICE_TOKEN,
        ).send_payment_notification(
            payment.user_id,
            "payment.refunded",
            {"payment_id": payment.id, "refund_id": refund.id, "refund_amount": str(refund.refund_amount)},
        )
        return Response({"refund_id": refund.id, "status": refund.status}, status=201)


class PaymentBookingCallbackView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def post(self, request):
        serializer = PaymentCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = PaymentIntent.objects.filter(id=serializer.validated_data["payment_id"]).first()
        if payment is None:
            return Response({"error": {"code": "payment_not_found", "message": "Payment not found."}}, status=404)

        booking_client = BookingServiceClient(settings.BOOKING_SERVICE_BASE_URL, settings.INTERNAL_SERVICE_TOKEN)
        code, payload = booking_client.update_booking_status(payment.booking_id, serializer.validated_data["booking_status"])
        return Response({"booking_service_status": code, "booking_response": payload}, status=200)


class PaymentBanksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"banks": SYRIAN_BANKS}, status=200)
