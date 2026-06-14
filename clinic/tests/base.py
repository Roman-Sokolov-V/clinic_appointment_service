from contextlib import contextmanager
from datetime import timedelta, datetime
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from rest_framework.response import Response

from clinic.models import GlobalClinicSettings, Specialization, Doctor, DoctorSlot, Appointment
from django.contrib.auth import get_user_model

from payment.models import Payment

User = get_user_model()


class BaseClinicTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Цей метод виконується ОДИН раз для всього класу тестів.
        Дані записуються в базу один раз і шерояться між усіма тестами класу,
        що неймовірно прискорює тестування.
        """
        cls.settings = GlobalClinicSettings.objects.create(
            singleton_id=1,
            fee=10,
            fee_window=60
        )
        cls.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@clinic.com",
            password="STRONG23password#",
            is_staff=True,
        )
        cls.first_patient = User.objects.create_user(
            username="first_patient",
            email="first_patient@clinic.com",
            password="STRONG23password#",
        )
        cls.second_patient = User.objects.create_user(
            username="second_patient",
            email="second_patient@clinic.com",
            password="STRONG23password#",
        )

    @staticmethod
    def get_results(response: Response) -> list[dict]:
        return response.data.get("results")

    @staticmethod
    def get_result(response: Response) -> list[dict]:
        return response.data

    def populate_specializations(self, extra: list[dict] = None) -> list[Specialization]:
        params = [
            {
                "name": "name1",
                "code": "code1",
                "description": "description1",
            },
            {
                "name": "name2",
                "code": "code2",
                "description": "description2",

            },
            {
                "name": "name3",
                "code": "code3",
                "description": "description3",

            },

        ]
        if extra:
            params.extend(extra)
        sp_s = [Specialization(**param) for param in params]
        specializations = Specialization.objects.bulk_create(sp_s)
        return specializations

    def populate_doctors(self, extra: list[dict] = None) -> list[Doctor]:
        params = [
            {
                "first_name": "fname1",
                "last_name": "lname1",
                "description": "desc_1",
                "price_per_visit": "10.11"
            },
            {
                "first_name": "fname2",
                "last_name": "lname2",
                "description": "desc_2",
                "price_per_visit": "20.11"
            },
            {
                "first_name": "fname3",
                "last_name": "lname3",
                "description": "desc_3",
                "price_per_visit": "30.11"
            },
        ]
        if extra:
            params.extend(extra)

        specializations = Specialization.objects.all()

        doctors_list = [Doctor(**param) for param in params]
        doctors = Doctor.objects.bulk_create(doctors_list)
        if specializations:
            for i in range(min(len(doctors), len(specializations))):
                doctors[i].specializations.add(specializations[i])
        return doctors

    def populate_free_slots(self, first_date: datetime = None) -> list[DoctorSlot]:
        doctors = self.populate_doctors()
        if not first_date:
            first_date = timezone.now() + timedelta(hours=1)
        date = first_date
        slots = []
        for i in range(3):
            for doctor in doctors:
                doctor_data = {
                    "doctor": doctor,
                    "start": date,
                    "end": date + timedelta(hours=1),
                }
                slot = DoctorSlot.objects.create(**doctor_data)
                slots.append(slot)
            date = date + timedelta(minutes=90)
        return slots

    def make_slots_and_1_appointment(self, first_date: datetime = None):
        if not first_date:
            first_date = timezone.now() + timedelta(hours=1)
        self.populate_doctors()
        doctor = Doctor.objects.first()
        other_doctor = Doctor.objects.exclude(id=doctor.id).first()
        date = first_date
        # create slots with 1 hour duration and 1 hour gaps
        for i in range(5):
            doctor_data = {
                "doctor": doctor,
                "start": date,
                "end": date + timedelta(hours=1),
            }
            other_doctor_data = {
                "doctor": other_doctor,
                "start": date + timedelta(minutes=2),
                "end": date + timedelta(minutes=62),
            }
            DoctorSlot.objects.create(**doctor_data)
            DoctorSlot.objects.create(**other_doctor_data)
            date = date + timedelta(hours=2)
        # make first slot booked:
        first_slot = DoctorSlot.objects.filter(doctor=doctor).first()
        patient = get_user_model().objects.create_user(
            email="test@test.com",
            password="STRONG124#password",
        )

        Appointment.objects.create(
            patient=patient,
            slot=first_slot,
            price=doctor.price_per_visit
        )

    def get_slot(self) -> DoctorSlot:
        slots = self.populate_free_slots()
        slot = slots[0]
        start = timezone.now() + timedelta(hours=10)
        end = start + timedelta(hours=1)
        slot.start = start
        slot.end = end
        slot.save(update_fields=["start", "end"])
        return slot

    def get_appointment(self, slot, patient: User | None = None) -> Appointment:
        appointment = Appointment.objects.create(
            slot=slot,
            patient=patient if patient else self.first_patient,
            price=slot.doctor.price_per_visit
        )
        appointment.save()
        return appointment

    def get_paid_payment(self, appointment: Appointment, method: str = "STRIPE") -> Payment:
        payment = Payment.objects.create(
            status="PAID",
            method=method,
            appointment=appointment,
            money_to_pay=appointment.price
        )
        payment.save()
        return payment

captured_service_class = None

@contextmanager
def mock_payment_service(**kwargs):
    """
    Context manager to isolate API/integration tests from real payment gateways.

    This utility mocks the payment service factory (`get_payment_service`),
    intercepts the creation of the payment class, and bypasses any external HTTP
    requests (e.g., to Stripe API). Instead of communicating with the provider,
    it automatically creates and saves a valid `Payment` record directly in the
    test database, maintaining database integrity and foreign key relationships.

    It dynamically captures the `payment_method` and the created `Appointment`
    instance from the application's runtime context.

    Args:
        provider_metadata (dict): Mocked data that the payment provider would
            normally return (e.g., Stripe session ID and checkout URL).

    Yields:
        unittest.mock.MagicMock: The mocked factory function, allowing assertions
            on call counts or captured arguments.
    """
    target = 'clinic.services.appointment_service.get_payment_service'

    with patch(target) as mock_get_payment_service:
        created_service_classes = []

        def mock_get_service_behavior(payment_method):
            mock_service_class = MagicMock()
            created_service_classes.append(mock_service_class)

            def fake_create_payment():
                constructor_kwargs = mock_service_class.call_args_list[-1].kwargs
                constructor_args = mock_service_class.call_args_list[-1].args
                real_appointment = constructor_kwargs.get('appointment') or constructor_args[0]

                return Payment.objects.create(
                    appointment=real_appointment,
                    money_to_pay=10,
                    type="CONSULTATION",
                    method=payment_method,
                    provider_metadata=kwargs.get("provider_metadata", {})
                )

            mock_service_class.return_value.create_payment = MagicMock(side_effect=fake_create_payment)
            mock_service_class.initiate_refund = MagicMock(return_value=None)

            return mock_service_class

        mock_get_payment_service.side_effect = mock_get_service_behavior
        mock_get_payment_service.created_service_classes = created_service_classes

        yield mock_get_payment_service