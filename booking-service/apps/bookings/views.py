from __future__ import annotations

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .integrations import HousingServiceClient, NotificationServiceClient, PaymentServiceClient
from .models import Booking, BookingEvent, BookingLock, BookingStatusHistory
from .permissions import IsAdminOrServiceRole, IsOwnerOrAdmin, IsUserOrAdminByPath
from .serializers import (
    BookingCreateSerializer,
    BookingSerializer,
    BookingStatusHistorySerializer,
    BookingStatusUpdateSerializer,
)
from .services import can_transition_status, overlapping_date_filter


def _is_admin(request) -> bool:
    user = request.user
    return bool(user and getattr(user, "is_authenticated", False) and "admin" in getattr(user, "roles", []))


def _is_service_role(request) -> bool:
    user = request.user
    return bool(user and getattr(user, "is_authenticated", False) and "service" in getattr(user, "roles", []))


def _append_status_history(booking: Booking, to_status: str, changed_by_user_id: int | None):
    BookingStatusHistory.objects.create(
        booking=booking,
        from_status=booking.status,
        to_status=to_status,
        changed_by_user_id=changed_by_user_id,
    )


def _append_event(booking: Booking, event_type: str, payload: dict | None = None):
    BookingEvent.objects.create(
        booking=booking,
        event_type=event_type,
        payload_json=payload or {},
    )


class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsAdminOrServiceRole().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)

        queryset = Booking.objects.all().order_by("-created_at", "-id")
        user_id = request.query_params.get("user_id")
        status_filter = request.query_params.get("status")
        booking_ids_raw = request.query_params.get("booking_ids", "")

        if user_id and user_id.isdigit():
            queryset = queryset.filter(user_id=int(user_id))
        if status_filter:
            queryset = queryset.filter(status=str(status_filter).strip().lower())

        booking_ids = []
        for item in str(booking_ids_raw).split(","):
            value = item.strip()
            if value.isdigit():
                booking_ids.append(int(value))
        if booking_ids:
            queryset = queryset.filter(id__in=booking_ids)

        limit = request.query_params.get("limit")
        if limit and str(limit).isdigit():
            queryset = queryset[: max(1, min(int(limit), 500))]
        else:
            queryset = queryset[:200]

        return Response(BookingSerializer(list(queryset), many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        housing_client = HousingServiceClient(settings.HOUSING_SERVICE_BASE_URL)
        payment_client = PaymentServiceClient(settings.PAYMENT_SERVICE_BASE_URL)
        notification_client = NotificationServiceClient(settings.NOTIFICATION_SERVICE_BASE_URL)

        with transaction.atomic():
            conflict_exists = Booking.objects.filter(
                unit_id=payload["unit_id"],
                status__in={Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED, Booking.STATUS_COMPLETED},
            ).filter(
                overlapping_date_filter(payload["start_date"], payload["end_date"])
            ).exists()
            if conflict_exists:
                return Response(
                    {"error": {"code": "booking_overlap", "message": "Overlapping booking already exists for this unit."}},
                    status=status.HTTP_409_CONFLICT,
                )

            if not housing_client.is_unit_available(
                unit_id=payload["unit_id"],
                start_date=payload["start_date"],
                end_date=payload["end_date"],
            ):
                return Response(
                    {"error": {"code": "unit_unavailable", "message": "Unit is unavailable for selected dates."}},
                    status=status.HTTP_409_CONFLICT,
                )

            if not housing_client.adjust_unit_occupancy(unit_id=payload["unit_id"], delta=1):
                return Response(
                    {"error": {"code": "unit_full", "message": "Housing unit is fully occupied."}},
                    status=status.HTTP_409_CONFLICT,
                )

            booking = Booking.objects.create(
                user_id=request.user.id,
                unit_id=payload["unit_id"],
                start_date=payload["start_date"],
                end_date=payload["end_date"],
                total_price=payload["total_price"],
                status=Booking.STATUS_PENDING,
                occupancy_reserved=True,
            )
            BookingStatusHistory.objects.create(
                booking=booking,
                from_status=None,
                to_status=Booking.STATUS_PENDING,
                changed_by_user_id=request.user.id,
            )
            _append_event(
                booking,
                "booking_created",
                payload={
                    "user_id": request.user.id,
                    "unit_id": payload["unit_id"],
                },
            )

            payment_intent_id = payment_client.create_payment_intent(
                booking_id=booking.id,
                user_id=booking.user_id,
                payer_bank_name=payload["payer_bank_name"],
                payer_account_number=payload["payer_account_number"],
                amount=booking.total_price,
            )
            if payment_intent_id:
                booking.payment_intent_id = payment_intent_id
                booking.save(update_fields=["payment_intent_id", "updated_at"])
                _append_event(
                    booking,
                    "payment_intent_created",
                    payload={"payment_intent_id": payment_intent_id},
                )
            else:
                _append_event(booking, "payment_intent_failed")

            notification_client.publish_booking_event(
                "booking_created",
                {
                    "booking_id": booking.id,
                    "user_id": booking.user_id,
                    "status": booking.status,
                },
            )

        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id: int):
        booking = Booking.objects.filter(id=booking_id).first()
        if booking is None:
            return Response(
                {"error": {"code": "booking_not_found", "message": "Booking not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not IsOwnerOrAdmin().has_object_permission(request, self, booking):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)


class BookingUserHistoryView(APIView):
    permission_classes = [IsAuthenticated, IsUserOrAdminByPath]

    def get(self, request, user_id: int):
        bookings = Booking.objects.filter(user_id=user_id).order_by("-created_at", "-id")
        return Response(BookingSerializer(bookings, many=True).data, status=status.HTTP_200_OK)


class BookingStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def patch(self, request, booking_id: int):
        booking = Booking.objects.filter(id=booking_id).first()
        if booking is None:
            return Response(
                {"error": {"code": "booking_not_found", "message": "Booking not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BookingStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        next_status = serializer.validated_data["status"]

        admin_override = _is_admin(request)
        if not can_transition_status(booking.status, next_status, is_admin_override=admin_override):
            return Response(
                {"error": {"code": "invalid_status_transition", "message": "Status transition is not allowed."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            housing_client = HousingServiceClient(settings.HOUSING_SERVICE_BASE_URL)
            previous_status = booking.status
            _append_status_history(
                booking,
                to_status=next_status,
                changed_by_user_id=request.user.id if not _is_service_role(request) else None,
            )
            booking.status = next_status
            if (
                booking.occupancy_reserved
                and previous_status in {Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED, Booking.STATUS_COMPLETED}
                and next_status in {Booking.STATUS_CANCELLED, Booking.STATUS_FAILED}
            ):
                if housing_client.adjust_unit_occupancy(unit_id=booking.unit_id, delta=-1):
                    booking.occupancy_reserved = False

            booking.save(update_fields=["status", "occupancy_reserved", "updated_at"])
            if next_status in {Booking.STATUS_CONFIRMED, Booking.STATUS_COMPLETED, Booking.STATUS_CANCELLED, Booking.STATUS_FAILED}:
                BookingLock.objects.filter(
                    unit_id=booking.unit_id,
                    start_date=booking.start_date,
                    end_date=booking.end_date,
                ).delete()
            _append_event(booking, "booking_status_updated", payload={"to_status": next_status})
            if next_status == Booking.STATUS_COMPLETED:
                _append_event(booking, "housing_ready", payload={"booking_id": booking.id, "user_id": booking.user_id})

            NotificationServiceClient(settings.NOTIFICATION_SERVICE_BASE_URL).publish_booking_event(
                "booking_status_updated",
                {
                    "booking_id": booking.id,
                    "status": booking.status,
                    "user_id": booking.user_id,
                    "unit_id": booking.unit_id,
                    "housing_ready": next_status == Booking.STATUS_COMPLETED,
                },
            )

        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)


class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id: int):
        booking = Booking.objects.filter(id=booking_id).first()
        if booking is None:
            return Response(
                {"error": {"code": "booking_not_found", "message": "Booking not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not IsOwnerOrAdmin().has_object_permission(request, self, booking):
            return Response(status=status.HTTP_403_FORBIDDEN)

        if not can_transition_status(booking.status, Booking.STATUS_CANCELLED, is_admin_override=_is_admin(request)):
            return Response(
                {"error": {"code": "invalid_status_transition", "message": "Booking cannot be cancelled."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            housing_client = HousingServiceClient(settings.HOUSING_SERVICE_BASE_URL)
            _append_status_history(
                booking,
                to_status=Booking.STATUS_CANCELLED,
                changed_by_user_id=request.user.id,
            )
            if booking.occupancy_reserved and housing_client.adjust_unit_occupancy(unit_id=booking.unit_id, delta=-1):
                booking.occupancy_reserved = False
            booking.status = Booking.STATUS_CANCELLED
            booking.save(update_fields=["status", "occupancy_reserved", "updated_at"])
            BookingLock.objects.filter(
                unit_id=booking.unit_id,
                start_date=booking.start_date,
                end_date=booking.end_date,
            ).delete()
            _append_event(booking, "booking_cancelled", payload={"cancelled_by_user_id": request.user.id})

            NotificationServiceClient(settings.NOTIFICATION_SERVICE_BASE_URL).publish_booking_event(
                "booking_cancelled",
                {"booking_id": booking.id, "status": booking.status},
            )

        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)


class BookingTimelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id: int):
        booking = Booking.objects.filter(id=booking_id).first()
        if booking is None:
            return Response(
                {"error": {"code": "booking_not_found", "message": "Booking not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not IsOwnerOrAdmin().has_object_permission(request, self, booking):
            return Response(status=status.HTTP_403_FORBIDDEN)

        timeline = BookingStatusHistory.objects.filter(booking=booking).order_by("changed_at", "id")
        return Response(BookingStatusHistorySerializer(timeline, many=True).data, status=status.HTTP_200_OK)
