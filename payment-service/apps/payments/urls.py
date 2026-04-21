from django.urls import path

from .views import (
    PaymentBanksView,
    PaymentBookingCallbackView,
    PaymentDetailView,
    PaymentIntentCreateView,
    PaymentRefundView,
    PaymentSimulateFailureView,
    PaymentSimulateSuccessView,
)

urlpatterns = [
    path("payments", PaymentIntentCreateView.as_view(), name="payments-list"),
    path("payments/intents", PaymentIntentCreateView.as_view(), name="payments-intents-create"),
    path("payments/<int:payment_id>", PaymentDetailView.as_view(), name="payments-detail"),
    path("payments/<int:payment_id>/simulate-success", PaymentSimulateSuccessView.as_view(), name="payments-sim-success"),
    path("payments/<int:payment_id>/simulate-failure", PaymentSimulateFailureView.as_view(), name="payments-sim-failure"),
    path("payments/<int:payment_id>/refund", PaymentRefundView.as_view(), name="payments-refund"),
    path("payments/callbacks/booking-status", PaymentBookingCallbackView.as_view(), name="payments-booking-callback"),
    path("payments/banks", PaymentBanksView.as_view(), name="payments-banks"),
]
