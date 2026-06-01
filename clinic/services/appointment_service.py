from datetime import timedelta

from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError

from clinic.models import Appointment


class AppointmentService:

    @staticmethod
    @transaction.atomic
    def cancel_appointment(*, appointment: Appointment, user):
        #AppointmentService._check_permission(appointment, user)

        initializer_is_user = AppointmentService.cancellation_initializer_is_user(user)
        late_cancel = AppointmentService._is_late_cancel(appointment)

        if late_cancel and initializer_is_user:
            AppointmentService._apply_cancellation_fee(appointment)

        appointment.status = "CANCELED"
        appointment.save(update_fields=["status"])

        return appointment

    # @staticmethod
    # def _check_permission(appointment, user):
    #
    #     if appointment.patient_id != user.id and not user.is_staff:
    #         raise ValidationError({
    #             "detail": "You are not allowed to cancel this appointment"
    #         })

    @staticmethod
    def cancellation_initializer_is_user(user):
        return not user.is_staff

    @staticmethod
    def _is_late_cancel(appointment):
        return appointment.slot.start <= timezone.now() + timedelta(hours=1)

    @staticmethod
    def _apply_cancellation_fee(appointment):
        # TODO: Stripe / internal billing logic
        pass

    def complete_appointment(*, appointment: Appointment):
        appointment.status = "COMPLETED"
        appointment.save(update_fields=["status"])