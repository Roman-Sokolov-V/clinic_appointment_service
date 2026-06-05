from abc import ABC, abstractmethod
from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from clinic.models import Appointment
from config.settings import BACKEND_SUCCESS_URL, BACKEND_CANCEL_URL
from payment.models import Payment
from payment.serializers import PaymentSerializer


class AppointmentPayment(ABC):
    def __init__(
            self,
            appointment: Appointment,
            fee: Decimal | None = None,
            frontend_success_url: str | None = None,
            frontend_cancel_url: str | None = None,
            expires_at: int | None = None,
    ):
        """
        Initialize the Payment Service Coordinator.

        Determines the transaction financial figures and mapping rules for the
        upcoming gateway session.

        - If a 'fee' is provided, it handles a 'CANCELLATION_FEE' penalty scenario.
        - If 'fee' is None, it defaults to the full consultation 'PRICE' of the appointment.

        Redirection Fallback Strategy:
        Accepts dynamic runtime redirection destinations from the frontend. If the
        frontend client did not supply specific routing parameters, the service
        automatically falls back to standard URLs configured in the application environment
        (`settings.BACKEND_SUCCESS_URL` / `settings.BACKEND_CANCEL_URL`).

        :param appointment: Appointment instance being processed.
        :param fee: Decimal (optional), custom charge amount for cancellations.
        :param frontend_success_url: str (optional), custom frontend landing URL on success.
        :param frontend_cancel_url: str (optional), custom frontend landing URL on cancellation.
        """
        self.appointment = appointment
        self.amount = int(fee * 100) if fee else int(appointment.price * 100)
        self.payment_type = 'CANCELLATION_FEE' if fee else 'CONSULTATION'
        self.expires_at = expires_at
        if frontend_success_url:
            self.success_url = frontend_success_url
        else:
            self.success_url = BACKEND_SUCCESS_URL
        if frontend_cancel_url:
            self.cancel_url = frontend_cancel_url
        else:
            self.cancel_url = BACKEND_CANCEL_URL



    @abstractmethod
    def _generate_gateway_transaction(self, payment: Payment):
        """
        Abstract method to register the transaction within the external payment provider.

        Every concrete payment service integration subclass (e.g., Stripe, PayPal, LiqPay)
        MUST implement this method. It is responsible for translating local payment context
        into provider-specific API payloads, executing the network request, and returning
        an object that encapsulates at least an external unique identifier (`id`) and
        a destination checkout address (`url`).

        :param payment: Payment instance previously persisted locally.
        :return: An object or dataclass containing `id` and `url` attributes from the gateway.
        """
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
        """
        Execute the localized logging and external generation of the payment transaction.

        This orchestration workflow enforces a strict template pattern:
        1. Validates structural attributes via an internal PaymentSerializer.
        2. Within an atomic transaction block, it records a local Payment log
           tracked as 'PENDING'.
        3. Invokes the polymorphic `_generate_gateway_transaction` method, which
           must be implemented by concrete subclasses to handle specific gateway logic.
        4. Links the acquired gateway transaction credentials (`session_id` and `session_url`)
           directly back into the payment record, committing these mutations immediately.

        This guarantees that even if the network fails during the external API callback,
        the internal database maintains full integrity regarding generated transaction IDs.

        :raises ValidationError: If internal serializer constraints fail.
        :return: Updated Payment model instance containing the gateway properties.
        """

        payload = {
            "appointment": self.appointment.id,
            "money_to_pay": self.amount / 100,
            "type": self.payment_type,
        }
        serializer = PaymentSerializer(data=payload)
        if serializer.is_valid():
            with transaction.atomic():
                payment = serializer.save()
                session = self._generate_gateway_transaction(payment)
                payment.session_id = session.id
                payment.session_url = session.url
                payment.save(update_fields=["session_id", "session_url"])
                return payment
        raise ValidationError(serializer.errors)