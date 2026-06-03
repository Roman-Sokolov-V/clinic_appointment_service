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
from payment.payment_services.base import AppointmentPayment

logger = logging.getLogger('clinic_api')
client = stripe.StripeClient(STRIPE_SECRET_KEY)
endpoint_secret = STRIPE_ENDPOINT_SECRET


@api_view(["POST"])
@permission_classes([AllowAny])
#@csrf_exempt
def webhook_view(request, *args, **kwargs):
    print("start webhook")  # todo remove
    payload = request.stream.read() # instead request.body to get raw request data

    if endpoint_secret is None:
        raise ParseError("⚠️  Webhook endpoint_secret not provided.")

    sig_header = request.headers.get('stripe-signature')
    if not sig_header:
        raise ParseError("⚠️  Stripe signature header is missing.")

    try:
        event = client.webhooks.construct_event(  # client.construct_event
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
        # get session_id
        session_id = event["data"]["object"]["id"]
        # set payment.status "COMPLETED"
        AppointmentPayment.complete_payment(session_id)

    else:
        # Unexpected event type
        logger.info("Unexpected payment event.type: %s", event['type'])
    return Response({"status": "success"}, status=status.HTTP_200_OK)
