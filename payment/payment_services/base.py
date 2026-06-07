import logging
from abc import ABC, abstractmethod
from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from clinic.models import Appointment
from payment.models import Payment
from payment.serializers import PaymentSerializer

logger = logging.getLogger("clinic_api")


class AppointmentPayment(ABC):
    def __init__(
            self,
            appointment: Appointment,
            fee: Decimal | None = None,
            payment_data: dict | None = None,
            payment_method: str | None = None,
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
        self.payment_method = payment_method
        self.payment_data = payment_data


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
    @abstractmethod
    def initiate_refund(payment: Payment, *args, **kwargs):
        pass

    @staticmethod
    @abstractmethod
    def complete_payment(*args, **kwargs):
        pass

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

        basic_payload = {
            "appointment": self.appointment.id,
            "money_to_pay": self.amount / 100,
            "type": self.payment_type,
            "method": self.payment_method,
            # status PENDING за замовченням
        }
        if self.payment_method == 'Cash':
            return self.cash_payment(basic_payload)

        serializer = PaymentSerializer(data=basic_payload)
        if serializer.is_valid(raise_exception=True):
            payment = serializer.save()
            with transaction.atomic():
                provider_metadata = self._generate_gateway_transaction(payment)
                payment.provider_metadata = provider_metadata
                payment.save(update_fields=["provider_metadata"])
                return payment
        raise ValidationError(serializer.errors)

    def cash_payment(self, payload: dict):
        payload["status"] = "PAID"
        serializer = PaymentSerializer(data=payload)
        if serializer.is_valid(raise_exception=True):
            return serializer.save()



