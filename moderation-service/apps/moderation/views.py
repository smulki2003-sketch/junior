from __future__ import annotations

from django.conf import settings
from django.db.models import Prefetch
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .integrations import (
    AdminServiceClient,
    BookingServiceClient,
    EnforcementGateway,
    HousingServiceClient,
    NotificationServiceClient,
)
from .models import CaseComment, Complaint, ModerationCase
from .permissions import IsAdminRole, IsReporterOrAdmin
from .serializers import (
    CaseCommentCreateSerializer,
    CaseCommentSerializer,
    ComplaintCreateSerializer,
    ComplaintSerializer,
    ComplaintStatusUpdateSerializer,
    ModerationActionCreateSerializer,
    ModerationActionSerializer,
)
from .services import (
    NotificationTarget,
    apply_moderation_action,
    create_complaint_with_case,
    notify_case_update,
    notify_complaint_created,
    resolve_target_user_id,
    update_complaint_case_status,
)


def _service_clients():
    service_token = settings.INTERNAL_SERVICE_TOKEN
    return {
        "notification": NotificationServiceClient(settings.NOTIFICATION_SERVICE_BASE_URL, service_token),
        "housing": HousingServiceClient(settings.HOUSING_SERVICE_BASE_URL, service_token),
        "booking": BookingServiceClient(settings.BOOKING_SERVICE_BASE_URL, service_token),
        "admin": AdminServiceClient(settings.ADMIN_SERVICE_BASE_URL, service_token),
    }


def _complaint_queryset():
    return Complaint.objects.select_related("moderation_case").prefetch_related(
        "evidence",
        Prefetch("moderation_case__actions"),
        Prefetch("moderation_case__comments"),
    )


def _find_complaint_or_404(complaint_id: int):
    complaint = _complaint_queryset().filter(id=complaint_id).first()
    if complaint is None:
        return None, Response(
            {"error": {"code": "complaint_not_found", "message": "Complaint not found."}},
            status=status.HTTP_404_NOT_FOUND,
        )
    return complaint, None


class ComplaintListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def post(self, request):
        serializer = ComplaintCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        clients = _service_clients()
        if data["target_type"] == Complaint.TARGET_BOOKING:
            booking_code, booking_payload = clients["booking"].fetch_booking(data["target_id"])
            if booking_code != 200 or not isinstance(booking_payload, dict):
                return Response(
                    {"error": {"code": "booking_not_found", "message": "Booking not found for complaint."}},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if int(booking_payload.get("user_id", 0)) != int(request.user.id):
                return Response(status=status.HTTP_403_FORBIDDEN)
            booking_status = str(booking_payload.get("status", "")).strip().lower()
            if booking_status not in {"confirmed", "completed"}:
                return Response(
                    {"error": {"code": "booking_not_eligible", "message": "Only confirmed/completed bookings can submit complaints."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        complaint = create_complaint_with_case(
            reporter_user_id=request.user.id,
            target_type=data["target_type"],
            target_id=data["target_id"],
            reason=data["reason"],
            evidence=data.get("evidence", []),
        )
        target_user_id = resolve_target_user_id(complaint, clients["housing"], clients["booking"])
        notify_complaint_created(
            clients["notification"],
            NotificationTarget(complainant_user_id=request.user.id, target_user_id=target_user_id),
            complaint.id,
        )

        response_payload = ComplaintSerializer(_complaint_queryset().get(id=complaint.id)).data
        return Response(response_payload, status=status.HTTP_201_CREATED)

    def get(self, request):
        queryset = _complaint_queryset().all()
        if not IsAdminRole().has_permission(request, self):
            queryset = queryset.filter(reporter_user_id=request.user.id)
        status_filter = request.query_params.get("status")
        target_type_filter = request.query_params.get("target_type")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if target_type_filter:
            queryset = queryset.filter(target_type=target_type_filter)
        payload = ComplaintSerializer(queryset.order_by("-created_at", "-id"), many=True).data
        return Response(payload, status=status.HTTP_200_OK)


class ComplaintDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, complaint_id: int):
        complaint, error_response = _find_complaint_or_404(complaint_id)
        if error_response:
            return error_response
        if not IsReporterOrAdmin().has_object_permission(request, self, complaint):
            return Response(status=status.HTTP_403_FORBIDDEN)

        payload = ComplaintSerializer(complaint).data
        case = complaint.moderation_case
        payload["actions"] = ModerationActionSerializer(case.actions.order_by("-created_at", "-id"), many=True).data
        payload["comments"] = CaseCommentSerializer(case.comments.order_by("created_at", "id"), many=True).data
        return Response(payload, status=status.HTTP_200_OK)


class ComplaintStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def patch(self, request, complaint_id: int):
        complaint, error_response = _find_complaint_or_404(complaint_id)
        if error_response:
            return error_response

        serializer = ComplaintStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        case = complaint.moderation_case

        try:
            complaint, case = update_complaint_case_status(
                complaint,
                case,
                actor_admin_id=request.user.id,
                status=data.get("status"),
                case_status=data.get("case_status"),
                assigned_admin_id=data.get("assigned_admin_id"),
                set_assignee=("assigned_admin_id" in data),
                priority=data.get("priority"),
                note=data.get("internal_note"),
            )
        except ValueError as exc:
            return Response(
                {"error": {"code": "invalid_status_transition", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        clients = _service_clients()
        target_user_id = resolve_target_user_id(complaint, clients["housing"], clients["booking"])
        notify_case_update(
            clients["notification"],
            NotificationTarget(complainant_user_id=complaint.reporter_user_id, target_user_id=target_user_id),
            complaint,
        )

        payload = ComplaintSerializer(_complaint_queryset().get(id=complaint.id)).data
        payload["case"] = {
            "id": case.id,
            "status": case.status,
            "priority": case.priority,
            "assigned_admin_id": case.assigned_admin_id,
        }
        return Response(payload, status=status.HTTP_200_OK)


class ModerationActionCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request, case_id: int):
        case = ModerationCase.objects.select_related("complaint").filter(id=case_id).first()
        if case is None:
            return Response(
                {"error": {"code": "case_not_found", "message": "Moderation case not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ModerationActionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        clients = _service_clients()
        gateway = EnforcementGateway(
            admin_client=clients["admin"],
            housing_client=clients["housing"],
            booking_client=clients["booking"],
        )
        action = apply_moderation_action(
            case=case,
            actor_admin_id=request.user.id,
            action_type=data["action_type"],
            target_type=data["target_type"],
            target_id=data["target_id"],
            metadata_json=data.get("metadata_json", {}),
            gateway=gateway,
        )
        return Response(ModerationActionSerializer(action).data, status=status.HTTP_201_CREATED)


class CaseCommentCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request, case_id: int):
        case = ModerationCase.objects.filter(id=case_id).first()
        if case is None:
            return Response(
                {"error": {"code": "case_not_found", "message": "Moderation case not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = CaseCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = CaseComment.objects.create(
            case=case,
            admin_user_id=request.user.id,
            comment=serializer.validated_data["comment"],
        )
        return Response(CaseCommentSerializer(comment).data, status=status.HTTP_201_CREATED)
