from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .integrations import (
    AuthServiceClient,
    BookingServiceClient,
    HousingServiceClient,
    ModerationServiceClient,
    NotificationServiceClient,
    PaymentServiceClient,
    RoommateServiceClient,
    UserServiceClient,
)
from .permissions import IsAdminOrServiceRole, IsAdminRole
from .models import AdminActionLog
from .serializers import (
    AdminUserStatusUpdateSerializer,
    BookingStatusOverrideSerializer,
    BroadcastSerializer,
    HousingApprovalUpdateSerializer,
)
from .services import DashboardOverview, create_admin_note, log_admin_action, parse_id_csv, recent_action_counts


def _clients(request=None):
    token = settings.INTERNAL_SERVICE_TOKEN
    if request is not None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip() or token
    return {
        "user": UserServiceClient(settings.USER_SERVICE_BASE_URL, token),
        "auth": AuthServiceClient(settings.AUTH_SERVICE_BASE_URL, token),
        "housing": HousingServiceClient(settings.HOUSING_SERVICE_BASE_URL, token),
        "booking": BookingServiceClient(settings.BOOKING_SERVICE_BASE_URL, token),
        "payment": PaymentServiceClient(settings.PAYMENT_SERVICE_BASE_URL, token),
        "notification": NotificationServiceClient(settings.NOTIFICATION_SERVICE_BASE_URL, token),
        "moderation": ModerationServiceClient(settings.MODERATION_SERVICE_BASE_URL, token),
        "roommate": RoommateServiceClient(settings.ROOMMATE_SERVICE_BASE_URL, token),
    }


def _admin_permissions():
    return [IsAuthenticated(), IsAdminRole()]


def _as_bool(value, default: bool) -> bool:
    if value is None:
        return default
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


def _chunked(values: list[int], size: int = 100) -> list[list[int]]:
    if not values:
        return []
    return [values[index : index + size] for index in range(0, len(values), size)]


class AdminDashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        clients = _clients(request)
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        trend_start = (now - timedelta(days=29)).date()
        trend_buckets: dict[str, int] = defaultdict(int)
        bookings_this_month = 0
        total_users = 0

        with ThreadPoolExecutor(max_workers=6) as executor:
            pending_future = executor.submit(clients["housing"].list_pending)
            approved_future = executor.submit(clients["housing"].list_by_status, "approved")
            rejected_future = executor.submit(clients["housing"].list_by_status, "rejected")
            complaints_future = executor.submit(clients["moderation"].list_complaints)
            auth_users_future = executor.submit(clients["auth"].list_users, None, 500)
            questionnaire_future = executor.submit(clients["roommate"].questionnaire)

            pending_housing_code, pending_housing_payload = pending_future.result()
            approved_code, approved_payload = approved_future.result()
            rejected_code, rejected_payload = rejected_future.result()
            complaints_code, complaints_payload = complaints_future.result()
            auth_code, auth_payload = auth_users_future.result()
            questionnaire_code, questionnaire_payload = questionnaire_future.result()

        pending_housing_count = len(pending_housing_payload) if pending_housing_code == 200 and isinstance(pending_housing_payload, list) else 0
        approved_listings = len(approved_payload) if approved_code == 200 and isinstance(approved_payload, list) else 0
        rejected_listings = len(rejected_payload) if rejected_code == 200 and isinstance(rejected_payload, list) else 0
        open_complaints_count = (
            len([item for item in complaints_payload if item.get("status") not in {"resolved", "rejected", "closed"}])
            if complaints_code == 200 and isinstance(complaints_payload, list)
            else 0
        )
        users = auth_payload.get("results", []) if auth_code == 200 and isinstance(auth_payload, dict) else []
        total_users = len(users)

        booking_activity = (
            AdminActionLog.objects.filter(action_key="booking.status_override", created_at__date__gte=trend_start)
            .order_by("created_at")
            .only("created_at")
        )
        for item in booking_activity:
            day_key = item.created_at.date().isoformat()
            trend_buckets[day_key] += 1
            if item.created_at >= month_start:
                bookings_this_month += 1

        booking_trend = []
        for offset in range(30):
            day = trend_start + timedelta(days=offset)
            day_key = day.isoformat()
            booking_trend.append({"label": day.strftime("%m/%d"), "value": trend_buckets.get(day_key, 0)})

        activity = []
        recent_logs = AdminActionLog.objects.all().order_by("-created_at", "-id")[:20]
        for log in recent_logs:
            action = (log.action_key or "").replace(".", " ").strip().title() or "Admin Action"
            activity.append(
                {
                    "id": log.id,
                    "description": action,
                    "entity": f"{log.target_type}:{log.target_id}" if log.target_id else log.target_type,
                    "created_at": log.created_at.isoformat(),
                }
            )

        questionnaire_available = bool(questionnaire_payload.get("questions")) if questionnaire_code == 200 and isinstance(questionnaire_payload, dict) else False

        overview = DashboardOverview(
            total_users=total_users,
            active_listings=approved_listings,
            bookings_this_month=bookings_this_month,
            revenue=0.0,
            approved_listings=approved_listings,
            rejected_listings=rejected_listings,
            booking_trend=booking_trend,
            activity=activity,
            pending_housing_count=pending_housing_count,
            open_complaints_count=open_complaints_count,
            recent_admin_actions=recent_action_counts(),
            questionnaire_available=questionnaire_available,
        )
        return Response(overview.to_dict(), status=status.HTTP_200_OK)


class AdminUsersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        user_ids = parse_id_csv(request.query_params.get("user_ids"))
        include_staff = str(request.query_params.get("include_staff", "")).strip().lower() in {"1", "true", "yes"}
        include_profiles = _as_bool(request.query_params.get("include_profiles"), True)
        include_booking_counts = _as_bool(request.query_params.get("include_booking_counts"), True)
        limit_raw = request.query_params.get("limit")
        limit = 200
        if str(limit_raw or "").isdigit():
            limit = max(1, min(int(limit_raw), 1000))
        clients = _clients(request)
        results = []

        auth_code, auth_payload = clients["auth"].list_users(user_ids=user_ids, limit=limit)
        users = auth_payload.get("results", []) if auth_code == 200 and isinstance(auth_payload, dict) else []

        filtered_auth_users = []
        for auth_user in users:
            user_id = auth_user.get("id")
            if not isinstance(user_id, int):
                continue
            roles = auth_user.get("roles", [])
            role_list = [str(role).strip().lower() for role in roles] if isinstance(roles, list) else []
            if not include_staff and any(role in {"admin", "service"} for role in role_list):
                continue
            filtered_auth_users.append(auth_user)

        profile_map: dict[int, dict] = {}
        if include_profiles and filtered_auth_users:
            def fetch_profile(user_id: int):
                code, payload = clients["user"].fetch_profile(user_id)
                if code == 200 and isinstance(payload, dict):
                    return user_id, payload
                return user_id, {}

            with ThreadPoolExecutor(max_workers=min(16, len(filtered_auth_users))) as executor:
                profile_rows = list(executor.map(lambda row: fetch_profile(int(row["id"])), filtered_auth_users))
            profile_map = dict(profile_rows)

        booking_counts: dict[int, int] = defaultdict(int)
        if include_booking_counts and filtered_auth_users:
            list_code, list_payload = clients["booking"].list_bookings(limit=3000)
            all_bookings = list_payload if list_code == 200 and isinstance(list_payload, list) else []
            if all_bookings:
                tracked_ids = {int(row["id"]) for row in filtered_auth_users if isinstance(row.get("id"), int)}
                for booking in all_bookings:
                    row_user_id = booking.get("user_id")
                    if isinstance(row_user_id, int) and row_user_id in tracked_ids:
                        booking_counts[row_user_id] += 1
            else:
                def fetch_booking_count(user_id: int):
                    code, payload = clients["booking"].list_user_bookings(user_id)
                    if code == 200 and isinstance(payload, list):
                        return user_id, len(payload)
                    return user_id, 0

                with ThreadPoolExecutor(max_workers=min(16, len(filtered_auth_users))) as executor:
                    count_rows = list(executor.map(lambda row: fetch_booking_count(int(row["id"])), filtered_auth_users))
                booking_counts = defaultdict(int, dict(count_rows))

        for auth_user in filtered_auth_users:
            user_id = auth_user.get("id")
            if not isinstance(user_id, int):
                continue
            roles = auth_user.get("roles", [])
            profile_payload = profile_map.get(user_id, {}) if include_profiles else {}
            bookings_count = int(booking_counts.get(user_id, 0)) if include_booking_counts else 0
            primary_role = roles[0] if isinstance(roles, list) and roles else "student"
            results.append(
                {
                    "user_id": user_id,
                    "email": auth_user.get("email", ""),
                    "is_active": bool(auth_user.get("is_active", True)),
                    "status": "active" if bool(auth_user.get("is_active", True)) else "suspended",
                    "role": primary_role,
                    "roles": roles if isinstance(roles, list) else [primary_role],
                    "created_at": auth_user.get("created_at"),
                    "profile": profile_payload,
                    "bookings": bookings_count,
                }
            )

        return Response({"results": results, "count": len(results)}, status=status.HTTP_200_OK)


class AdminUserStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def patch(self, request, user_id: int):
        serializer = AdminUserStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        clients = _clients(request)

        if payload["status"] == "active":
            role_update_code, role_update_payload = clients["auth"].update_user_roles(user_id, ["student"])
        else:
            role_update_code, role_update_payload = clients["auth"].update_user_roles(user_id, ["student"])

        log_admin_action(
            admin_user_id=request.user.id,
            action_key="user.status_update",
            target_type="user",
            target_id=str(user_id),
            metadata={"status": payload["status"], "reason": payload["reason"], "auth_response_code": role_update_code},
        )
        create_admin_note(
            admin_user_id=request.user.id,
            target_type="user",
            target_id=str(user_id),
            note=f"user status changed to {payload['status']}: {payload['reason']}",
        )
        return Response(
            {
                "user_id": user_id,
                "status": payload["status"],
                "reason": payload["reason"],
                "integration": {"auth_status_code": role_update_code, "auth_response": role_update_payload},
            },
            status=status.HTTP_200_OK,
        )


class AdminHousingPendingView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        code, payload = _clients(request)["housing"].list_pending()
        if code != 200 or not isinstance(payload, list):
            return Response({"results": [], "count": 0}, status=status.HTTP_200_OK)
        return Response({"results": payload, "count": len(payload)}, status=status.HTTP_200_OK)


class AdminHousingApprovalUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def patch(self, request, unit_id: int):
        serializer = HousingApprovalUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        code, integration_payload = _clients(request)["housing"].update_approval(unit_id, payload["approval"], payload.get("reason", ""))

        log_admin_action(
            admin_user_id=request.user.id,
            action_key="housing.approval_update",
            target_type="housing",
            target_id=str(unit_id),
            metadata={"approval": payload["approval"], "reason": payload.get("reason", ""), "housing_status_code": code},
        )
        if payload.get("reason"):
            create_admin_note(
                admin_user_id=request.user.id,
                target_type="housing",
                target_id=str(unit_id),
                note=f"housing approval set to {payload['approval']}: {payload['reason']}",
            )
        return Response(
            {"unit_id": unit_id, "approval": payload["approval"], "integration_status_code": code, "integration_payload": integration_payload},
            status=status.HTTP_200_OK,
        )


class AdminBookingsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        booking_ids = parse_id_csv(request.query_params.get("booking_ids"))
        user_id = request.query_params.get("user_id")
        include_user_details = _as_bool(request.query_params.get("include_user_details"), True)
        clients = _clients(request)

        booking_rows = []
        if user_id and user_id.isdigit():
            code, payload = clients["booking"].list_user_bookings(int(user_id))
            if code == 200 and isinstance(payload, list):
                booking_rows = payload
        if not booking_rows:
            code, payload = clients["booking"].list_bookings(booking_ids=booking_ids or None, limit=300)
            if code == 200 and isinstance(payload, list):
                booking_rows = payload

        if not booking_rows:
            return Response({"results": [], "count": 0}, status=status.HTTP_200_OK)

        auth_user_map: dict[int, dict] = {}
        profile_map: dict[int, dict] = {}
        if include_user_details:
            user_ids = sorted({booking.get("user_id") for booking in booking_rows if isinstance(booking.get("user_id"), int)})
            for chunk in _chunked(user_ids, 120):
                auth_code, auth_payload = clients["auth"].list_users(user_ids=chunk, limit=max(120, len(chunk)))
                auth_rows = auth_payload.get("results", []) if auth_code == 200 and isinstance(auth_payload, dict) else []
                for row in auth_rows:
                    row_id = row.get("id")
                    if isinstance(row_id, int):
                        auth_user_map[row_id] = row

            if user_ids:
                def fetch_profile(user_id: int):
                    code, payload = clients["user"].fetch_profile(user_id)
                    if code == 200 and isinstance(payload, dict):
                        return user_id, payload
                    return user_id, {}

                with ThreadPoolExecutor(max_workers=min(16, len(user_ids))) as executor:
                    profile_rows = list(executor.map(fetch_profile, user_ids))
                profile_map = dict(profile_rows)

        payment_code, payment_payload = clients["payment"].list_payments(limit=500)
        payment_rows = payment_payload if payment_code == 200 and isinstance(payment_payload, list) else []
        payment_by_booking = {}
        for payment in payment_rows:
            booking_key = payment.get("booking_id")
            if not isinstance(booking_key, int):
                continue
            if booking_key not in payment_by_booking:
                payment_by_booking[booking_key] = payment

        enriched = []
        for booking in booking_rows:
            payment = payment_by_booking.get(booking.get("id"), {})
            row_user_id = booking.get("user_id")
            profile = profile_map.get(row_user_id, {}) if isinstance(row_user_id, int) else {}
            auth_user = auth_user_map.get(row_user_id, {}) if isinstance(row_user_id, int) else {}
            first_name = str(profile.get("first_name", "")).strip()
            last_name = str(profile.get("last_name", "")).strip()
            full_name = f"{first_name} {last_name}".strip()
            user_name = full_name or auth_user.get("email", "")
            enriched.append(
                {
                    **booking,
                    "payment_status": payment.get("status", "pending"),
                    "payment_id": payment.get("id"),
                    "payer_bank_name": payment.get("payer_bank_name", ""),
                    "payer_account_number": payment.get("payer_account_number", ""),
                    "user_name": (user_name or f"User {row_user_id}") if include_user_details else "",
                    "user_email": (auth_user.get("email", "") or profile.get("email", "")) if include_user_details else "",
                }
            )
        return Response({"results": enriched, "count": len(enriched)}, status=status.HTTP_200_OK)


class AdminBookingStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def patch(self, request, booking_id: int):
        serializer = BookingStatusOverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        clients = _clients(request)
        booking_code, booking_payload = clients["booking"].fetch_booking(booking_id)
        booking = booking_payload if booking_code == 200 and isinstance(booking_payload, dict) else {}
        if not booking:
            return Response({"error": {"code": "booking_not_found", "message": "Booking not found."}}, status=status.HTTP_404_NOT_FOUND)

        if payload["status"] in {"confirmed", "completed"}:
            payment_code, payment_payload = clients["payment"].list_payments(booking_id=booking_id, limit=10)
            payments = payment_payload if payment_code == 200 and isinstance(payment_payload, list) else []
            has_success = any(str(item.get("status", "")).lower() == "succeeded" for item in payments)
            if not has_success:
                return Response(
                    {"error": {"code": "payment_not_completed", "message": "Cannot confirm/complete booking before successful payment."}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        code, integration_payload = clients["booking"].override_status(booking_id, payload["status"])
        if payload["status"] == "completed" and isinstance(booking.get("user_id"), int):
            clients["notification"].send_notification(
                int(booking["user_id"]),
                "booking.housing.ready",
                {
                    "booking_id": booking_id,
                    "unit_id": booking.get("unit_id"),
                    "message": "Your housing booking is completed and ready.",
                },
            )

        log_admin_action(
            admin_user_id=request.user.id,
            action_key="booking.status_override",
            target_type="booking",
            target_id=str(booking_id),
            metadata={
                "status": payload["status"],
                "reason": payload["reason"],
                "booking_status_code": code,
            },
        )
        create_admin_note(
            admin_user_id=request.user.id,
            target_type="booking",
            target_id=str(booking_id),
            note=f"booking status overridden to {payload['status']}: {payload['reason']}",
        )
        return Response(
            {"booking_id": booking_id, "status": payload["status"], "integration_status_code": code, "integration_payload": integration_payload},
            status=status.HTTP_200_OK,
        )


class AdminPaymentsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        payment_ids = parse_id_csv(request.query_params.get("payment_ids"))
        include_user_details = _as_bool(request.query_params.get("include_user_details"), True)
        clients = _clients(request)
        code, payload = clients["payment"].list_payments(payment_ids=payment_ids or None, limit=300)
        if code == 200 and isinstance(payload, list):
            payments = payload
            if not include_user_details:
                return Response({"results": payments, "count": len(payments)}, status=status.HTTP_200_OK)
            booking_ids = sorted({item.get("booking_id") for item in payments if isinstance(item.get("booking_id"), int)})
            user_ids = sorted({item.get("user_id") for item in payments if isinstance(item.get("user_id"), int)})

            booking_map: dict[int, dict] = {}
            if booking_ids:
                booking_code, booking_payload = clients["booking"].list_bookings(booking_ids=booking_ids, limit=max(300, len(booking_ids) + 20))
                booking_rows = booking_payload if booking_code == 200 and isinstance(booking_payload, list) else []
                booking_map = {
                    row["id"]: row for row in booking_rows if isinstance(row, dict) and isinstance(row.get("id"), int)
                }

            auth_user_map: dict[int, dict] = {}
            for chunk in _chunked(user_ids, 120):
                auth_code, auth_payload = clients["auth"].list_users(user_ids=chunk, limit=max(120, len(chunk)))
                auth_rows = auth_payload.get("results", []) if auth_code == 200 and isinstance(auth_payload, dict) else []
                for row in auth_rows:
                    row_id = row.get("id")
                    if isinstance(row_id, int):
                        auth_user_map[row_id] = row

            profile_map: dict[int, dict] = {}
            if user_ids:
                def fetch_profile(user_id: int):
                    user_code, user_payload = clients["user"].fetch_profile(user_id)
                    if user_code == 200 and isinstance(user_payload, dict):
                        return user_id, user_payload
                    return user_id, {}

                with ThreadPoolExecutor(max_workers=min(16, len(user_ids))) as executor:
                    profile_rows = list(executor.map(fetch_profile, user_ids))
                profile_map = dict(profile_rows)

            enriched = []
            for payment in payments:
                row_user_id = payment.get("user_id")
                row_booking_id = payment.get("booking_id")
                booking = booking_map.get(row_booking_id, {}) if isinstance(row_booking_id, int) else {}
                profile = profile_map.get(row_user_id, {}) if isinstance(row_user_id, int) else {}
                auth_user = auth_user_map.get(row_user_id, {}) if isinstance(row_user_id, int) else {}
                first_name = str(profile.get("first_name", "")).strip()
                last_name = str(profile.get("last_name", "")).strip()
                full_name = f"{first_name} {last_name}".strip()
                user_name = full_name or auth_user.get("email", "")
                enriched.append(
                    {
                        **payment,
                        "booking_status": booking.get("status", ""),
                        "unit_id": booking.get("unit_id"),
                        "user_name": user_name or f"User {row_user_id}",
                        "user_email": auth_user.get("email", "") or profile.get("email", ""),
                    }
                )

            return Response({"results": enriched, "count": len(enriched)}, status=status.HTTP_200_OK)
        return Response({"results": [], "count": 0}, status=status.HTTP_200_OK)


class AdminNotificationsBroadcastView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        serializer = BroadcastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        user_ids = payload.get("target_user_ids", [])
        event_key = payload.get("event_key", "admin.broadcast")
        notification_client = _clients(request)["notification"]
        if not user_ids:
            return Response(
                {"error": {"code": "no_recipients", "message": "No recipients were selected for this broadcast."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deliveries = []
        for user_id in user_ids:
            code, response_payload = notification_client.send_notification(
                user_id,
                event_key,
                {"title": payload["title"], "body": payload["body"]},
                title=payload["title"],
                body=payload["body"],
            )
            deliveries.append({"user_id": user_id, "status_code": code, "payload": response_payload})

        log_admin_action(
            admin_user_id=request.user.id,
            action_key="notification.broadcast",
            target_type="notification",
            target_id="bulk",
            metadata={"event_key": event_key, "recipient_count": len(user_ids)},
        )
        return Response(
            {
                "event_key": event_key,
                "title": payload["title"],
                "body": payload["body"],
                "recipient_count": len(user_ids),
                "deliveries": deliveries,
            },
            status=status.HTTP_201_CREATED,
        )


class AdminComplaintsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def get(self, request):
        code, payload = _clients(request)["moderation"].list_complaints()
        if code != 200 or not isinstance(payload, list):
            return Response({"results": [], "count": 0}, status=status.HTTP_200_OK)
        return Response({"results": payload, "count": len(payload)}, status=status.HTTP_200_OK)
