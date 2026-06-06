import logging

import stripe
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ParseError
from rest_framework.permissions import AllowAny

from rest_framework.response import Response


from config.settings import STRIPE_SECRET_KEY
from config.settings import STRIPE_ENDPOINT_SECRET
from payment.models import Payment
from payment.payment_services.base import AppointmentPayment
from payment.payment_services.stripe_service import StripePayment

logger = logging.getLogger('clinic_api')
client = stripe.StripeClient(STRIPE_SECRET_KEY)
endpoint_secret = STRIPE_ENDPOINT_SECRET


@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhook_view(request, *args, **kwargs):
    logger.info("start webhook")
    payload = request.stream.read() # instead request.body to get raw request data

    if endpoint_secret is None:
        logger.error("Webhook endpoint_secret not provided")
        raise ParseError("⚠️  Webhook endpoint_secret not provided.")

    sig_header = request.headers.get('stripe-signature')
    if not sig_header:
        logger.error("Stripe signature header is missing.")
        raise ParseError("⚠️  Stripe signature header is missing.")

    try:
        event = client.construct_event(  # client.construct_event
            payload, sig_header, endpoint_secret
        )

    except stripe.error.SignatureVerificationError as e:
        logger.error("⚠️  Webhook signature verification failed. %s", e)
        raise ParseError(f"⚠️  Webhook signature verification failed. {str(e)}")


    event_dict = event.to_dict()
    event_type = event_dict["type"]

    # Список подій, які ми свідомо ігноруємо, щоб не смітити в WARNING
    IGNORED_EVENTS = [
        "payment_intent.created",
        "payment_intent.succeeded",
        "charge.succeeded",
        "charge.updated"
    ]

    # 💡Успішна оплата
    if event_type in ["checkout.session.completed", "checkout.session.async_payment_succeeded"]:
        session = event_dict["data"]["object"]
        session_id = session.get("id")
        intent_id = session.get("payment_intent")
        payment_status = session.get("payment_status")

        # Перевіряємо умови успіху
        is_completed_and_paid = (event_type == "checkout.session.completed" and payment_status == "paid")
        is_async_success = (event_type == "checkout.session.async_payment_succeeded")

        if is_completed_and_paid or is_async_success:
            StripePayment.complete_payment(session_id, intent_id)
            logger.info(f"Payment successful for session: {session_id} via {event_type}")

        elif event_type == "checkout.session.completed":
            # Сюди потрапляємо, якщо сесія завершена, але payment_status != 'paid' (асинхронний платіж)
            logger.info(f"Checkout completed. Waiting for bank clearing for session: {session_id}")

    #  повернення коштів
        if event_type == "refund.created":
            refund_obj = event_dict["data"]["object"]
            refund_status = refund_obj.get("status")

            # Дістаємо токен, який створили під час створення refund
            stripe_metadata = refund_obj.get("metadata", {})
            local_refund_token = stripe_metadata.get("local_refund_token")

            if refund_status == "succeeded" and local_refund_token:
                with transaction.atomic():
                    # Шукаємо платіж за нашим токеном
                    payment = Payment.objects.select_for_update().filter(
                        provider_metadata__refund_token=local_refund_token
                    ).first()

                    if payment and payment.status != "REFUNDED":
                        # Додатково зберігаємо refund.id від Stripe
                        payment.provider_metadata["refund_id"] = refund_obj.get("id")
                        payment.status = "REFUNDED"
                        payment.save(update_fields=["status", "provider_metadata"])
                        logger.info(f"Payment {payment.id} REFUNDED via token match.")

            elif refund_status == "failed":
                with transaction.atomic():
                    payment = Payment.objects.select_for_update().filter(
                        provider_metadata__refund_token=local_refund_token
                    ).first()
                    if payment:
                        payment.status = "PAID"  # Повертаємо назад, бо гроші не пішли
                        payment.save(update_fields=["status"])
                        logger.warning(f"Refund failed for payment {payment.id}. Status reverted to PAID.")


    elif event_type in IGNORED_EVENTS:
        # Тихо пропускаємо технічні івенти Stripe
        logger.info(f"Stripe event {event_type} received and skipped intentionally.")

    else:
        # Отут дійсно неочікувані або критичні івенти (наприклад, refund, dispute, чи failure)
        logger.warning("Unexpected payment event.type: %s", event_type)

    return Response({"status": "success"}, status=status.HTTP_200_OK)

@api_view(["GET"])
@permission_classes([AllowAny])
def success_view(request, *args, **kwargs):
    query_params_dict = request.query_params
    logger.info("Received a success request from Stripe with parameters:%s", query_params_dict)

    payment_id = request.query_params.get("payment_id")

    if not payment_id:
        logger.warning("The payment_id parameter is missing from the request")
        return Response({"error": "Missing payment_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment = Payment.objects.get(id=int(payment_id))
        logger.info("Payment found for payment_id: %s, current status: %s", payment_id, payment.status)
    except Payment.DoesNotExist:
        logger.error("Payment with payment_id %s not found in the database", payment_id)
        return Response({"error": f"Payment  with id {payment_id} not found"}, status=status.HTTP_404_NOT_FOUND)

    if payment.status == "PAID":
        logger.info("Payment %s is confirmed. Initializing sending a message to Telegram...", payment_id)
        # TODO: task telegram message success
        pass

    return Response({"status": payment.status}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def cancel_view(request, *args, **kwargs):
    """
    Stub endpoint to handle synchronous Stripe checkout cancellations within the Browsable API.

    🎯 ARCHITECTURAL NOTE (STUB ENDPOINT):
    This view serves strictly as a development stub to fulfill the project's non-functional
    requirement of being "fully functional through a browsable API interface" without a
    dedicated frontend application.

    In a standard production architecture with a decoupled frontend (Web/Mobile):
    1. This endpoint is completely redundant and SHOULD BE REMOVED.
    2. The frontend application passes its own URL (e.g., https://my-clinic.com/booking/cancel)
       as the `frontend_cancel_url`.
    3. Stripe will redirect the user's browser directly back to the frontend interface.
    4. The frontend handles the cancellation UX state entirely client-side without pinging
       the backend, as the local database tracking item already correctly remains 'PENDING'.

    Current Browsable API Behavior:
    Intercepts the user's browser when they click "Cancel and return to merchant" on the
    Stripe Checkout page, preventing a 404 error in the browser. It extracts the `payment_id`
    from the query parameters to confirm the transaction status remains unchanged.

    :param request: Django REST Framework Request instance containing `payment_id` query token.
    :return: Response object with HTTP 200 OK and a structural placeholder JSON message.
    """
    payment_id = request.query_params.get("payment_id")

    if not payment_id:
        logger.warning("The payment_id parameter is missing from the cancel request")
        return Response({"error": "Missing payment_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment = Payment.objects.get(id=int(payment_id))
        logger.info("User cancelled checkout for payment_id: %s. Status remains PENDING.", payment_id)
    except Payment.DoesNotExist:
        logger.error("Payment with payment_id %s not found during cancel redirection", payment_id)
        return Response({"error": f"Payment with id {payment_id} not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "status": payment.status,  # Гарантовано поверне "PENDING"
        "message": "Payment was paused or cancelled by the user. The slot is held for 24 hours.",
        "hint": "This is a backend stub view. In production, Stripe will redirect directly to the frontend application."
    }, status=status.HTTP_200_OK)