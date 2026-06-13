from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.db.models import Model

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from clinic.models import Specialization, Doctor, DoctorSlot, Appointment, APPOINTMENT_STATUS
from clinic.tests.base import BaseClinicTestCase, mock_payment_service
from payment.models import Payment
from payment.serializers import PaymentSerializer


#
#
#
# def populate_specializations(extra: list[dict] = None) -> list[Specialization]:
#     params = [
#         {
#             "name": "name1",
#             "code": "code1",
#             "description": "description1",
#         },
#         {
#             "name": "name2",
#             "code": "code2",
#             "description": "description2",
#
#         },
#         {
#             "name": "name3",
#             "code": "code3",
#             "description": "description3",
#
#         },
#
#     ]
#     if extra:
#         params.extend(extra)
#     sp_s = [Specialization(**param) for param in params]
#     specializations = Specialization.objects.bulk_create(sp_s)
#     return specializations
#
# def populate_doctors(extra: list[dict] = None) -> list[Doctor]:
#     params = [
#         {
#             "first_name": "fname1",
#             "last_name": "lname1",
#             "description": "desc_1",
#             "price_per_visit": "10.11"
#         },
#         {
#             "first_name": "fname2",
#             "last_name": "lname2",
#             "description": "desc_2",
#             "price_per_visit": "20.11"
#         },
#         {
#             "first_name": "fname3",
#             "last_name": "lname3",
#             "description": "desc_3",
#             "price_per_visit": "30.11"
#         },
#     ]
#     if extra:
#         params.extend(extra)
#
#     specializations = Specialization.objects.all()
#
#     doctors_list = [Doctor(**param) for param in params]
#     doctors = Doctor.objects.bulk_create(doctors_list)
#     if specializations:
#         for i in range(min(len(doctors), len(specializations))):
#             doctors[i].specializations.add(specializations[i])
#     return doctors
#
# def create_patient(email: str="test@test", password: str="STRong#password#"):
#     return get_user_model().objects.create_user(email, password)
#
# def populate_free_slots(first_date: datetime=None) -> list[DoctorSlot]:
#     doctors = populate_doctors()
#     if not first_date:
#         first_date = timezone.now() + timedelta(hours=1)
#     date = first_date
#     slots = []
#     for i in range(3):
#         for doctor in doctors:
#             doctor_data = {
#                 "doctor": doctor,
#                 "start": date,
#                 "end": date + timedelta(hours=1),
#             }
#             slot = DoctorSlot.objects.create(**doctor_data)
#             slots.append(slot)
#         date = date + timedelta(minutes=90)
#     return slots
#
# def make_slots_and_1_appointment(first_date: datetime=None):
#     if not first_date:
#         first_date = timezone.now() + timedelta(hours=1)
#     populate_doctors()
#     doctor = Doctor.objects.first()
#     other_doctor = Doctor.objects.exclude(id=doctor.id).first()
#     date = first_date
#     # create slots with 1 hour duration and 1 hour gaps
#     for i in range(5):
#         doctor_data = {
#             "doctor": doctor,
#             "start": date,
#             "end": date + timedelta(hours=1),
#         }
#         other_doctor_data = {
#             "doctor": other_doctor,
#             "start": date + timedelta(minutes=2),
#             "end": date + timedelta(minutes=62),
#         }
#         DoctorSlot.objects.create(**doctor_data)
#         DoctorSlot.objects.create(**other_doctor_data)
#
#         date = date + timedelta(hours=2)
#     # make first slot booked:
#     first_slot = DoctorSlot.objects.filter(doctor=doctor).first()
#     patient = get_user_model().objects.create_user(
#         email="test@test.com",
#         password="STRONG124#password",
#     )
#
#     Appointment.objects.create(
#         patient=patient,
#         slot=first_slot,
#         price = doctor.price_per_visit
#     )
#
#
# class ResultMixin:
#
#     @staticmethod
#     def get_results(response: Response) -> list[dict]:
#         return response.data.get("results")
#
#     @staticmethod
#     def get_result(response: Response) -> list[dict]:
#         return response.data



#Appointments################################################
class AppointmentUnauthenticatedUserTests(BaseClinicTestCase):
    def setUp(self):
        self.view_name = "clinic:appointment"
        self.client = APIClient()

    def test_create_appointment(self):
        payload = {}
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_appointment(self):
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_get_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_update_patch_appointment(self):
        payload = {}
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.put(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.patch(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cancel_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        full_url = url + "cancel/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_cant_mark_complete_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        full_url = url + "complete/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cant_mark_no_show_status(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        full_url = url + "no-show/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



########
class AppointmentAuthenticatedUserTests(BaseClinicTestCase):
    def setUp(self):
        self.view_name = "clinic:appointment"
        self.client = APIClient()
        self.request_user = self.first_patient
        self.client.force_authenticate(user=self.request_user)



    def test_create_appointment_stripe(self):
        url = reverse(self.view_name + "-list")
        slots = self.populate_free_slots()
        payload = {
            "slot": slots[0].id,
            "method": "STRIPE"  # за замовченням, але залишу так для прозорості
        }
        expected_url = "https://checkout.stripe.com/c/pay/cs_test_12345"
        provider_metadata = {
            "session_id": "cs_test_12345",
            "session_url": expected_url
        }


        with mock_payment_service(provider_metadata=provider_metadata) as mock_service:
            response = self.client.post(url, data=payload, format="json")

            # Перевірки API
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            result = self.get_result(response)
            self.assertEqual(result["patient"], self.request_user.id)
            self.assertEqual(result["checkout_url"], expected_url)

            # Перевірка поведінки моку
            self.assertEqual(mock_service.call_count, 1)

# todo continue check from this line

    def test_cant_create_appointment_for_other_patient(self):
        slots = self.populate_free_slots()
        slot = slots[0]
        other_patient = self.second_patient
        payload = {
            "slot": slot.id,
            "patient": other_patient.id,
        }
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_appointment_only_own_appointments(self):
        self.make_slots_and_1_appointment()
        free_slots = DoctorSlot.objects.filter(appointments__isnull=True)
        Appointment.objects.create(
            patient=self.request_user,
            slot=free_slots[0],
            price="22.22"
        )
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["patient"], self.request_user.id)
        print(results)

    def test_list_appointment_with_filter_status(self):
        slots = self.populate_free_slots()
        for slot in slots:
            Appointment.objects.create(
                patient=self.request_user,
                slot=slot,
                price="22.22"
            )
        users_appointments = [
            Appointment.objects.create(
                patient=self.request_user, slot=slot, price="22.22"
            ) for slot in slots
        ]
        status_choices = [value for value, _ in APPOINTMENT_STATUS]

        for i, appointment_status in enumerate(status_choices):
            users_appointments[i].status = appointment_status
            users_appointments[i].save()

        for appointment_status in status_choices:
            full_view_name = self.view_name + "-list"
            url = reverse(full_view_name) + f"?status={appointment_status}"
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = self.get_results(response)
            self.assertTrue(len(results) >= 1)
            for result in results:
                self.assertEqual(result["status"], appointment_status)

    def test_list_appointment_with_filters_from_and_to(self):
        slots = self.populate_free_slots()
        for slot in slots:
            Appointment.objects.create(
                patient=self.request_user, slot=slot, price="22.22"
            )

        all_slots_ordered_by_start = DoctorSlot.objects.order_by("start")
        earliest_slot = all_slots_ordered_by_start.first()
        latest_slot = all_slots_ordered_by_start.last()

        filters = {
            "from": (earliest_slot.start + timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M"),
            "to": (latest_slot.start - timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M"),
        }
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name) + f"?from_date={filters['from']}&to_date={filters['to']}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)

        self.assertTrue(len(results) > 0)
        for result in results:
            self.assertTrue(result["slot"] not in (latest_slot.id, earliest_slot.id))

    def test_get_own_detail_appointment(self):
        slots = self.populate_free_slots()
        slot = slots[0]
        appointment = Appointment.objects.create(
            patient=self.request_user,
            slot=slot,
            price="22.22",
        )
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        response = self.client.get(url)
        result = self.get_result(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cant_get_another_person_detail_appointment(self):
        slots = self.populate_free_slots()
        another_person = self.second_patient
        another_person_slot = slots[0]
        another_person_appointment = Appointment.objects.create(
            slot=another_person_slot,
            patient=another_person,
            price="22.22",
        )
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{another_person_appointment.id}"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Appointment.objects.filter(slot=another_person_slot).exists())

    def test_delete_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_patch_appointment(self):
        payload = {}
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.put(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.patch(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_late_cancel_appointment_stripe(self):
        slots = self.populate_free_slots()
        slot = slots[0]
        start = timezone.now() + timedelta(hours=10)
        end = start + timedelta(hours=1)
        slot.start = start
        slot.end = end
        slot.save(update_fields=["start", "end"])
        payload = {
            "slot": slot.id,
            "method": "STRIPE"
        }
        expected_url = "https://checkout.stripe.com/c/pay/cs_test_12345"
        provider_metadata = {
            "session_id": "cs_test_12345",
            "session_url": expected_url,
        }
        create_url = reverse(self.view_name + "-list")
        with mock_payment_service(provider_metadata=provider_metadata) as mock_service:
            response = self.client.post(create_url, data=payload, format="json")
            # Перевірки API
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            result = self.get_result(response)
            appointment = Appointment.objects.first()
            self.assertTrue(appointment is not None)
            payment = Payment.objects.first()
            self.assertTrue(payment is not None)
            price = payment.money_to_pay
            percent_fee= appointment.percent_fee
            window_fee = appointment.window_fee
            payment.status = "PAID"
            payment.save(update_fields=["status"])
            print(price, percent_fee, window_fee)
            self.assertTrue(start - timedelta(minutes=window_fee) > timezone.now(), "should be true to start cancellation, without fee")


        # with mock_payment_service() as mock_service:
        #     full_view_name = self.view_name + "-detail"
        #     url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        #     full_url = url + "cancel/"
        #     payload = {}
        #     response = self.client.post(full_url, data=payload, format="json")
        #     self.assertEqual(response.status_code, status.HTTP_200_OK)
        #     mock_instance = mock_service.return_value.return_value
        #
        #     # 2. Перевіряємо, що метод викликався РІВНО ОДИН РАЗ і саме з цим платежем
        #     mock_instance.initiate_refund.assert_called_once_with(payment)
        #
        #     appointment.refresh_from_db()
        #     self.assertTrue(appointment.status == "CANCELED")
        #     # todo  late-cancel may create CANCELLATION_FEE

    def test_cant_cancel_not_own_appointment(self):
        slots = self.populate_free_slots()
        slot = slots[0]
        other_user = self.create_patient()
        appointment = Appointment.objects.create(
            patient=other_user,
            slot=slot,
            price="22.22",
        )
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "cancel/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        appointment.refresh_from_db()
        self.assertFalse(appointment.status == "CANCELED")
        # todo  late-cancel may create CANCELLATION_FEE

    def test_cant_mark_complete_appointment(self):
        slots = self.populate_free_slots()
        appointment = Appointment.objects.create(
            patient=self.user,
            slot=slots[0],
            price="22.22",
        )
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "complete/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        appointment.refresh_from_db()
        self.assertFalse(appointment.status == "COMPLETED")


    def test_cant_mark_no_show_status(self):
        slots = self.populate_free_slots()
        slot = slots[0]
        appointment = Appointment.objects.create(
            patient=self.user,
            slot=slot,
            price="22.22",
        )
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "no-show/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


####

class AppointmentAdminUserTests(BaseClinicTestCase):
    def setUp(self):
        self.view_name = "clinic:appointment"
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

    def test_create_appointment_with_patient_in_payload(self):
        slots = self.populate_free_slots()
        patient = self.first_patient
        payload = {

            "slot": slots[0].id,
            "patient": patient.id,
        }
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = self.get_result(response)
        print(result)

    def test_cancel_not_own_appointment(self):
        slots = self.populate_free_slots()
        slot = slots[0]
        other_user = self.create_patient()
        appointment = Appointment.objects.create(
            patient=other_user,
            slot=slot,
            price="22.22",
        )
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "cancel/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment.refresh_from_db()
        self.assertTrue(appointment.status == "CANCELED")
        # todo  late-cancel may create CANCELLATION_FEE

    def test_mark_complete_appointment(self):
        def test_cant_mark_complete_appointment(self):
            slots = self.populate_free_slots()
            patient = self.create_patient()
            appointment = Appointment.objects.create(
                patient=patient,
                slot=slots[0],
                price="22.22",
            )
            full_view_name = self.view_name + "-detail"
            url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
            full_url = url + "complete/"
            payload = {}
            response = self.client.post(full_url, data=payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            appointment.refresh_from_db()
            self.assertTrue(appointment.status == "COMPLETED")

    def test_mark_no_show_status(self):
        slots = self.populate_free_slots()
        slot = slots[0]
        patient = self.create_patient()
        appointment = Appointment.objects.create(
            patient=patient,
            slot=slot,
            price="22.22",
        )
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "no-show/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment.refresh_from_db()
        self.assertTrue(appointment.status == "NO_SHOW")