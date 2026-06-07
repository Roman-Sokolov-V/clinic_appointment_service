import uuid

import stripe
from django.db import transaction
from rest_framework.exceptions import ValidationError

from config.settings import STRIPE_SECRET_KEY, BACKEND_SUCCESS_URL, BACKEND_CANCEL_URL
from payment.models import Payment
from payment.payment_services.base import AppointmentPayment

stripe.api_key = STRIPE_SECRET_KEY

class StripePayment(AppointmentPayment):
    """
    Concrete implementation of the AppointmentPayment service utilizing the Stripe payment gateway.
    """

    def _generate_gateway_transaction(self, payment: Payment) -> dict:
        """
        Invoke the external Stripe Checkout API to generate a secure payment session.

        Maps the local payment metadata to Stripe's `line_items`. It appends the
        unique internal database payment tracking identifier (`?payment_id=<id>`)
        as a URL query parameter to both the `success_url` and `cancel_url`.

        This URL modification allows whichever client landing on those pages (Web/Mobile)
        to intercept the query token and execute standard background API verification loops
        against our backend.

        :param payment: Payment instance previously persisted locally.
        :return: dict with session id and session url
        """
        print("start create session")
        query_params = f"?payment_id={payment.id}"
        success_url = self.payment_data.get("frontend_success_url", BACKEND_SUCCESS_URL) + query_params
        cancel_url = self.payment_data.get("frontend_cancel_url", BACKEND_CANCEL_URL) + query_params
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            expires_at=self.payment_data["expires_at"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Appointment id: {self.appointment.id} ",
                            "description": self.payment_type,
                        },
                        "unit_amount": self.amount,
                    },
                    "quantity": 1,
                }
            ],
        )
        return {"session_id": session.id, "session_url": session.url}

    @staticmethod
    def complete_payment(session_id, intent_id):
        """
        A method called in success/ View changes the status to 'COMPLETED'
        """
        with transaction.atomic():
            payment = Payment.objects.select_for_update().filter(
                provider_metadata__session_id=session_id
            ).first()

            if not payment:
                raise ValidationError({"error": "Payment session not found"})

            payment.status = "PAID"
            metadata = payment.provider_metadata
            metadata["intent_id"] = intent_id
            payment.provider_metadata = metadata
            payment.save(update_fields=["status", "provider_metadata"])
            return payment



    @staticmethod
    def initiate_refund(payment: Payment, fee: int = 0, *args, **kwargs) -> None:
        if payment.status != "PAID":
            raise ValidationError({"error": "Refund impossible"})

        # 1. Створюємо унікальну мітку рефанду НАШОЇ системи заздалегідь
        local_refund_token = str(uuid.uuid4())

        # 2. Одразу записуємо її в базу і міняємо статус (швидка транзакція)
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(pk=payment.pk)

            provider_metadata = payment.provider_metadata or {}
            provider_metadata["refund_token"] = local_refund_token

            payment.provider_metadata = provider_metadata
            payment.status = "REFUND_PENDING"
            payment.save(update_fields=["status", "provider_metadata"])

        # --- З цього моменту база вже має токен і статус REFUND_PENDING ---

        client = stripe.StripeClient(STRIPE_SECRET_KEY)
        intent_id = payment.provider_metadata.get('intent_id')

        refund_args = {
            "payment_intent": intent_id,
            # Передаємо наш токен всередину Stripe як метадані!
            "metadata": {"local_refund_token": local_refund_token}
        }
        if fee > 0:
            cents_to_refund = (payment.money_to_pay * 100) * (100 - fee) / 100
            refund_args["amount"] = int(round(cents_to_refund))

        try:
            # Відправляємо в Stripe.
            client.v1.refunds.create(**refund_args)
        except Exception as e:
            # Ролбек статусу, якщо Stripe відмовив
            with transaction.atomic():
                payment = Payment.objects.select_for_update().get(pk=payment.pk)
                payment.status = "PAID"
                payment.save(update_fields=["status"])
            raise ValidationError({"error": f"Stripe rejected refund: {str(e)}"})

