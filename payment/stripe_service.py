from abc import ABC, abstractmethod
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError

from clinic.models import Appointment
from payment.models import Payment
from payment.serializers import PaymentSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY



class AppointmentPayment(ABC):
    def __init__(
            self,
            appointment: Appointment,
            fee: Decimal | None = None
    ):
        self.appointment = appointment
        self.amount = int(fee * 100) if fee else int(appointment.price * 100)
        self.payment_type = 'CANCELLATION_FEE' if fee else 'CONSULTATION'


    @abstractmethod
    def create_payment_session(self):
        """Returns a session object from the payment gateway (Stripe/others)"""
        pass

    @staticmethod
    def complete_payment(session_id):
        """
        A static method called in success/ View changes the status to 'COMPLETED'
        """
        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(session_id=session_id)
                payment.status = "COMPLETED"
                payment.save(update_fields=["status"])
                return payment
            except Payment.DoesNotExist:
                raise ValidationError({"error": "Payment session not found"})

    def create_payment(self):
        """creates a session in the gateway and logs the payment in the database with the status PENDING by default."""

        session = self.create_payment_session()

        payload = {
            "appointment": self.appointment.id,
            "money_to_pay": self.amount / 100,
            "type": self.payment_type,
            "session_id": session.id,
            "session_url": session.url,
        }
        serializer = PaymentSerializer(data=payload)
        if serializer.is_valid():
            payment_obj = serializer.save()
            print("Payment created successfully")
            return payment_obj
            # return redirect(session.url, code=303)
        raise ValidationError(serializer.errors)


class StripePayment(AppointmentPayment):
    def create_payment_session(self):
        """
        Creates a Stripe Payment Session for payment.
        :return StripePaymentSession
        """
        print("start create session")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            success_url="http://localhost:8000/success/",
            cancel_url="http://localhost:8000/cancel/",
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
        return session


