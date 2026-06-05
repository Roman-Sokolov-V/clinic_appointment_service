import logging

import stripe
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

logger = logging.getLogger('clinic_api')
client = stripe.StripeClient(STRIPE_SECRET_KEY)
endpoint_secret = STRIPE_ENDPOINT_SECRET


@api_view(["POST"])
@permission_classes([AllowAny])
#@csrf_exempt
def webhook_view(request, *args, **kwargs):
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

    # випадок коли оплата успішна
    if (
            event["type"] == "checkout.session.completed"
            or event["type"] == "checkout.session.async_payment_succeeded"
    ):
        logger.info("event received, type - completed")
        # get session_id
        session_id = event["data"]["object"]["id"]
        # set payment.status "COMPLETED"
        AppointmentPayment.complete_payment(session_id)

    else:
        # Unexpected event type
        logger.warning("Unexpected payment event.type: %s", event['type'])
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