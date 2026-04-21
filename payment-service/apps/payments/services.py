from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from django.db import transaction

from .models import PaymentAuditLog, PaymentIntent, PaymentRefund, PaymentTransaction


def _log(payment_intent: PaymentIntent, event_type: str, payload: dict):
    PaymentAuditLog.objects.create(payment_intent=payment_intent, event_type=event_type, payload_json=payload)


def create_payment_intent(
    *,
    booking_id: int,
    user_id: int,
    payer_bank_name: str,
    payer_account_number: str,
    amount: Decimal,
    currency: str,
) -> PaymentIntent:
    payment_intent = PaymentIntent.objects.create(
        booking_id=booking_id,
        user_id=user_id,
        payer_bank_name=payer_bank_name,
        payer_account_number=payer_account_number,
        amount=amount,
        currency=currency.upper(),
        status=PaymentIntent.STATUS_PENDING,
    )
    _log(
        payment_intent,
        "payment_intent_created",
        {
            "booking_id": booking_id,
            "user_id": user_id,
            "payer_bank_name": payer_bank_name,
            "payer_account_number": payer_account_number[-4:],
            "amount": str(amount),
            "currency": currency.upper(),
        },
    )
    return payment_intent


@transaction.atomic
def mark_payment_result(payment_intent: PaymentIntent, *, success: bool) -> PaymentIntent:
    if payment_intent.status in {PaymentIntent.STATUS_REFUNDED, PaymentIntent.STATUS_SUCCEEDED, PaymentIntent.STATUS_FAILED}:
        return payment_intent

    if success:
        payment_intent.status = PaymentIntent.STATUS_SUCCEEDED
        tx_result = PaymentTransaction.RESULT_SUCCESS
        event = "payment_succeeded"
    else:
        payment_intent.status = PaymentIntent.STATUS_FAILED
        tx_result = PaymentTransaction.RESULT_FAILURE
        event = "payment_failed"
    payment_intent.save(update_fields=["status", "updated_at"])

    PaymentTransaction.objects.create(
        payment_intent=payment_intent,
        transaction_ref=f"txn_{uuid4().hex[:16]}",
        result=tx_result,
    )
    _log(payment_intent, event, {"status": payment_intent.status})
    return payment_intent


@transaction.atomic
def create_refund(payment_intent: PaymentIntent, *, refund_amount: Decimal, idempotency_key: str = "") -> PaymentRefund:
    if idempotency_key:
        existing = PaymentRefund.objects.filter(
            payment_intent=payment_intent,
            idempotency_key=idempotency_key,
        ).first()
        if existing:
            return existing

    refund = PaymentRefund.objects.create(
        payment_intent=payment_intent,
        refund_amount=refund_amount,
        status=PaymentRefund.STATUS_SUCCEEDED,
        idempotency_key=idempotency_key,
    )
    payment_intent.status = PaymentIntent.STATUS_REFUNDED
    payment_intent.save(update_fields=["status", "updated_at"])
    _log(
        payment_intent,
        "payment_refunded",
        {"refund_id": refund.id, "refund_amount": str(refund_amount), "idempotency_key": idempotency_key},
    )
    return refund
