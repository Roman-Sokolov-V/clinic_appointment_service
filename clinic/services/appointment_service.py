from datetime import timedelta
from typing import Any

from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError

from clinic.models import Appointment, DoctorSlot, GlobalClinicSettings
from clinic.utils import get_expires_at
from payment.models import Payment
from payment.payment_services import get_payment_service


class AppointmentService:

    @staticmethod
    def cancel_appointment(*, appointment: Appointment, user):
        with transaction.atomic():
            appointment = Appointment.objects.select_for_update().get(id=appointment.id)
            if appointment.status != "BOOKED":
                raise ValidationError({"appointment": "Only booked appointments can be canceled."})
            if AppointmentService._appointment_has_started(appointment):
                raise ValidationError({"appointment": "Cannot cancel an appointment that has already started."})

            appointment.status = "CANCELED"
            appointment.save(update_fields=["status"])

        paid_payment = AppointmentService._payment_with_status_paid(appointment)
        initializer_is_patient = not user.is_staff
        is_late_cancel = appointment.slot.start <= timezone.now() + timedelta(minutes=appointment.window_fee)

        if paid_payment:
            if paid_payment.method.upper() != "CASH":
                payment_service = get_payment_service(paid_payment.method)
                full_refund_cases = (not initializer_is_patient, not is_late_cancel)
                if any(full_refund_cases):
                    payment_service.initiate_refund(paid_payment)
                else:
                    payment_service.initiate_refund(paid_payment, appointment.fee)
        return appointment


    @staticmethod
    @transaction.atomic
    def complete_appointment(*, appointment: Appointment):
        appointment = Appointment.objects.select_for_update().get(id=appointment.id)
        if appointment.status != "BOOKED":
            raise ValidationError({"appointment": "Only booked appointments can be completed."})
        if not AppointmentService._payment_with_status_paid(appointment):
            raise ValidationError({"appointment": "appointment has not paid, only paid appointments can be completed, otherwise use no_show"})
        if not AppointmentService._appointment_has_started(appointment):
            raise ValidationError({"appointment": "appointment time has not passed, try again later"})
        appointment.status = "COMPLETED"
        appointment.save(update_fields=["status"])
        return appointment

    @staticmethod
    def _payment_with_status_paid(appointment) -> Payment | None:
        return Payment.objects.filter(appointment=appointment, status="PAID").first()

    @staticmethod
    def _appointment_has_started(appointment) -> bool:
        return appointment.slot.start <= timezone.now()


    @staticmethod
    @transaction.atomic
    def create_appointment(
            *, slot_id: int, patient, payment_method: str, payment_data: dict
    ) -> tuple[Appointment, Any]:
        """
        Повністю інкапсулює створення візиту та ініціалізацію платіжної сесії.
        Повертає кортеж (appointment, payment).
        """

        # 1. Блокуємо слот від Race Conditions
        slot = DoctorSlot.objects.select_for_update().get(id=slot_id)
        if slot.is_booked:
            raise ValidationError({"slot": "This slot is already booked."})

        # 2. Завантажуємо налаштування клініки (наш load метод із get_or_create)
        clinic_settings = GlobalClinicSettings.get_or_create(singleton_id=1) # не підтягується імпорт методу

        # 3. Створюємо Appointment із замороженими фінансами
        appointment = Appointment.objects.create(
            slot=slot,
            patient=patient,
            status="BOOKED",
            price=slot.doctor.price,  # Заморожуємо ціну доктора
            percent_fee=clinic_settings.fee,  # Заморожуємо штраф
            window_fee=clinic_settings.fee_window  # Заморожуємо вікно часу
        )

        # 4. Оновлюємо статус слота
        slot.is_booked = True
        slot.save(update_fields=["is_booked"])

        # 5. Ініціалізуємо платіж (твій поточний код, але в чистому вигляді)
        payment_data["expires_at"] = get_expires_at(slot.start)

        PaymentServiceClass = get_payment_service(payment_method)
        payment = PaymentServiceClass(
            appointment=appointment,
            payment_data=payment_data,
            payment_method=payment_method
        ).create_payment()

        return appointment, payment