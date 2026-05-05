from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from .integrations import BookingServiceClient, EnforcementGateway, HousingServiceClient, NotificationServiceClient
from .models import CaseComment, Complaint, ComplaintEvidence, ModerationAction, ModerationCase


COMPLAINT_TRANSITIONS = {
    Complaint.STATUS_SUBMITTED: {Complaint.STATUS_TRIAGED, Complaint.STATUS_IN_REVIEW, Complaint.STATUS_REJECTED},
    Complaint.STATUS_TRIAGED: {Complaint.STATUS_IN_REVIEW, Complaint.STATUS_RESOLVED, Complaint.STATUS_REJECTED},
    Complaint.STATUS_IN_REVIEW: {Complaint.STATUS_RESOLVED, Complaint.STATUS_REJECTED, Complaint.STATUS_CLOSED},
    Complaint.STATUS_RESOLVED: {Complaint.STATUS_CLOSED},
    Complaint.STATUS_REJECTED: {Complaint.STATUS_CLOSED},
    Complaint.STATUS_CLOSED: set(),
}

CASE_TRANSITIONS = {
    ModerationCase.STATUS_OPEN: {ModerationCase.STATUS_IN_PROGRESS, ModerationCase.STATUS_RESOLVED, ModerationCase.STATUS_CLOSED},
    ModerationCase.STATUS_IN_PROGRESS: {ModerationCase.STATUS_RESOLVED, ModerationCase.STATUS_CLOSED},
    ModerationCase.STATUS_RESOLVED: {ModerationCase.STATUS_CLOSED},
    ModerationCase.STATUS_CLOSED: set(),
}


def can_transition_complaint_status(current_status: str, next_status: str) -> bool:
    if current_status == next_status:
        return True
    return next_status in COMPLAINT_TRANSITIONS.get(current_status, set())


def can_transition_case_status(current_status: str, next_status: str) -> bool:
    if current_status == next_status:
        return True
    return next_status in CASE_TRANSITIONS.get(current_status, set())


@dataclass
class NotificationTarget:
    complainant_user_id: int
    target_user_id: int | None


def resolve_target_user_id(complaint: Complaint, housing_client: HousingServiceClient, booking_client: BookingServiceClient):
    if complaint.target_type == Complaint.TARGET_USER:
        return complaint.target_id
    if complaint.target_type == Complaint.TARGET_HOUSING:
        code, payload = housing_client.fetch_unit(complaint.target_id)
        if code == 200 and isinstance(payload, dict):
            owner = payload.get("owner_user_id")
            if isinstance(owner, int) and owner > 0:
                return owner
    if complaint.target_type == Complaint.TARGET_BOOKING:
        code, payload = booking_client.fetch_booking(complaint.target_id)
        if code == 200 and isinstance(payload, dict):
            booking_user = payload.get("user_id")
            if isinstance(booking_user, int) and booking_user > 0:
                return booking_user
    return None


def create_complaint_with_case(
    *,
    reporter_user_id: int,
    target_type: str,
    target_id: int,
    reason: str,
    evidence: list[dict] | None = None,
):
    with transaction.atomic():
        complaint = Complaint.objects.create(
            reporter_user_id=reporter_user_id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            status=Complaint.STATUS_SUBMITTED,
        )
        ModerationCase.objects.create(
            complaint=complaint,
            status=ModerationCase.STATUS_OPEN,
            priority=ModerationCase.PRIORITY_NORMAL,
        )
        evidence_items = evidence or []
        for item in evidence_items:
            ComplaintEvidence.objects.create(
                complaint=complaint,
                file_url=item["file_url"],
                file_type=item["file_type"],
            )
    return complaint


def update_complaint_case_status(
    complaint: Complaint,
    case: ModerationCase,
    *,
    actor_admin_id: int,
    status: str | None = None,
    case_status: str | None = None,
    assigned_admin_id: int | None = None,
    set_assignee: bool = False,
    priority: str | None = None,
    note: str | None = None,
):
    with transaction.atomic():
        if status:
            if not can_transition_complaint_status(complaint.status, status):
                raise ValueError("Complaint status transition is not allowed.")
            previous = complaint.status
            complaint.status = status
            complaint.save(update_fields=["status", "updated_at"])
            CaseComment.objects.create(
                case=case,
                admin_user_id=actor_admin_id,
                comment=f"[system] complaint status: {previous} -> {status}",
            )

        if case_status:
            if not can_transition_case_status(case.status, case_status):
                raise ValueError("Case status transition is not allowed.")
            previous_case_status = case.status
            case.status = case_status
            case.save(update_fields=["status", "updated_at"])
            CaseComment.objects.create(
                case=case,
                admin_user_id=actor_admin_id,
                comment=f"[system] case status: {previous_case_status} -> {case_status}",
            )

        if set_assignee:
            case.assigned_admin_id = assigned_admin_id
            case.save(update_fields=["assigned_admin_id", "updated_at"])
            CaseComment.objects.create(
                case=case,
                admin_user_id=actor_admin_id,
                comment=f"[system] assigned_admin_id set to {assigned_admin_id}",
            )

        if priority:
            old_priority = case.priority
            case.priority = priority
            case.save(update_fields=["priority", "updated_at"])
            CaseComment.objects.create(
                case=case,
                admin_user_id=actor_admin_id,
                comment=f"[system] priority: {old_priority} -> {priority}",
            )

        if note:
            CaseComment.objects.create(
                case=case,
                admin_user_id=actor_admin_id,
                comment=note,
            )

    complaint.refresh_from_db()
    case.refresh_from_db()
    return complaint, case


def apply_moderation_action(
    *,
    case: ModerationCase,
    actor_admin_id: int,
    action_type: str,
    target_type: str,
    target_id: int,
    metadata_json: dict | None,
    gateway: EnforcementGateway,
):
    reason = str((metadata_json or {}).get("reason", "")).strip() or f"Moderation action {action_type} applied."
    enforcement_result = gateway.apply_action(action_type, target_type, target_id, reason)
    with transaction.atomic():
        action = ModerationAction.objects.create(
            case=case,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            created_by_admin_id=actor_admin_id,
            metadata_json={**(metadata_json or {}), "enforcement_result": enforcement_result},
        )
        CaseComment.objects.create(
            case=case,
            admin_user_id=actor_admin_id,
            comment=f"[system] action `{action_type}` applied to {target_type}:{target_id}",
        )
    return action


def notify_complaint_created(notification_client: NotificationServiceClient, targets: NotificationTarget, complaint_id: int):
    notification_client.send_notification(
        targets.complainant_user_id,
        "moderation.complaint.submitted",
        {"complaint_id": complaint_id},
    )
    if targets.target_user_id and targets.target_user_id != targets.complainant_user_id:
        notification_client.send_notification(
            targets.target_user_id,
            "moderation.complaint.targeted",
            {"complaint_id": complaint_id},
        )


def notify_case_update(notification_client: NotificationServiceClient, targets: NotificationTarget, complaint: Complaint):
    notification_client.send_notification(
        targets.complainant_user_id,
        "moderation.complaint.updated",
        {"complaint_id": complaint.id, "status": complaint.status},
    )
    if targets.target_user_id and targets.target_user_id != targets.complainant_user_id:
        notification_client.send_notification(
            targets.target_user_id,
            "moderation.complaint.updated",
            {"complaint_id": complaint.id, "status": complaint.status},
        )


def notify_case_comment(
    notification_client: NotificationServiceClient,
    targets: NotificationTarget,
    complaint: Complaint,
    comment_text: str,
):
    excerpt = str(comment_text or "").strip()
    if len(excerpt) > 180:
        excerpt = f"{excerpt[:177]}..."
    notification_client.send_notification(
        targets.complainant_user_id,
        "moderation.complaint.reply",
        {"complaint_id": complaint.id, "status": complaint.status, "comment": excerpt},
        title=f"Reply on complaint #{complaint.id}",
        body=excerpt or "Admin added a new reply on your complaint.",
    )
