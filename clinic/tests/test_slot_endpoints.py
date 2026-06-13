from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from clinic.models import Doctor, DoctorSlot, Appointment
from clinic.serializers import SlotSerializer
from clinic.tests.base import BaseClinicTestCase


#Slots####doctors/<id>/slots/############################################################
class DoctorsSlotsUnauthenticatedUserTests(BaseClinicTestCase):
    def setUp(self):
        self.view_name = "clinic:bulk-create-list-slots"
        self.client = APIClient()

    def test_slots_create_with_valid_data(self):
        payload = {}
        full_url = reverse(self.view_name, kwargs={"pk": 1})
        response = self.client.post(f"{full_url}", data=payload, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_slots_list(self):
        url =  reverse(self.view_name, kwargs={"pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DoctorsSlotsAuthenticatedUserTests(BaseClinicTestCase):
    def setUp(self):
        self.view_name = "clinic:bulk-create-list-slots"
        self.client = APIClient()
        self.client.force_authenticate(user=self.first_patient)

    def test_slots_create_with_valid_data(self):
        payload = {}
        full_url = reverse(self.view_name, kwargs={"pk": 1})
        response = self.client.post(f"{full_url}", data=payload, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_slots_list_with_filter_from(self):
        first_date = timezone.now() + timedelta(hours=1)
        self.make_slots_and_1_appointment(first_date)
        doctor = Doctor.objects.first()
        start = first_date + timedelta(minutes=90)
        from_ = start.strftime("%Y-%m-%d %H:%M")

        db_slots = DoctorSlot.objects.filter(doctor=doctor, start__gte=from_)
        url =  reverse(self.view_name, kwargs={"pk": f"{doctor.id}"})
        full_url = url + f"?from={from_}"
        response = self.client.get(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        serializer = SlotSerializer(db_slots, many=True)
        self.assertEqual(results, serializer.data)

    def test_slots_list_with_filter_to(self):
        first_date = timezone.now() + timedelta(hours=1)
        self.make_slots_and_1_appointment(first_date)
        doctor = Doctor.objects.first()

        start = first_date + timedelta(minutes=90)
        end = start + timedelta(hours=3)
        to_ = end.strftime("%Y-%m-%d %H:%M")

        db_slots = DoctorSlot.objects.filter(doctor=doctor, end__lte=to_)
        url = reverse(self.view_name, kwargs={"pk": f"{doctor.id}"})
        full_url = url + f"?to={to_}"
        response = self.client.get(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        serializer = SlotSerializer(db_slots, many=True)
        self.assertEqual(results, serializer.data)

    def test_slots_list_with_filter_available_only(self):
        self.make_slots_and_1_appointment()
        doctor = Doctor.objects.first()

        db_slots = DoctorSlot.objects.filter(doctor=doctor).exclude(appointments__status="BOOKED").order_by("start")
        print("db_slots", len(db_slots))

        url = reverse(self.view_name, kwargs={"pk": f"{doctor.id}"})
        full_url = url + f"?available_only=true"
        print("full_url", full_url)
        response = self.client.get(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        print("results", len(results))
        serializer = SlotSerializer(db_slots, many=True)
        print("serializer.data", len(serializer.data))
        self.assertEqual(results, serializer.data)


class DoctorsSlotsAdminUserTests(BaseClinicTestCase):
    def setUp(self):
        self.view_name = "clinic:bulk-create-list-slots"
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)


    def test_slots_create_with_valid_data(self):
        self.populate_doctors()
        db_doctor = Doctor.objects.all().first()
        id = db_doctor.id
        now = timezone.now()
        payload = {
          "slots": [
            {
              "start": now + timedelta(hours=1),
              "end": now + timedelta(hours=2),
            },
            {
              "start": now + timedelta(hours=3),
              "end": now + timedelta(hours=4),
            }
          ]
        }
        full_url = reverse(self.view_name, kwargs={"pk": id})
        response = self.client.post(f"{full_url}", data=payload, format="json",)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = self.get_result(response)
        db_slots = DoctorSlot.objects.filter(doctor=db_doctor)
        serializer = SlotSerializer(db_slots, many=True)
        self.assertEqual(result, serializer.data)

    def test_slots_create_with_end_before_start(self):
        self.populate_doctors()
        db_doctor = Doctor.objects.all().first()
        id = db_doctor.id
        now = timezone.now()
        payload = {
          "slots": [
            {
              "start": now + timedelta(hours=3),
              "end": now + timedelta(hours=2),
            },
          ]
        }
        full_url = reverse(self.view_name, kwargs={"pk": id})
        response = self.client.post(f"{full_url}", data=payload, format="json",)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_slots_create_with_intersection_existed_slot(self):
        self.populate_doctors()
        db_doctor = Doctor.objects.all().first()
        id = db_doctor.id
        now = timezone.now()
        data = {
            "doctor": db_doctor,
            "start": now + timedelta(hours=2),
            "end": now + timedelta(hours=5),
        }
        DoctorSlot.objects.create(**data)

        case_1 = {
            "slots": [
                {
                    "start": now + timedelta(hours=7), # valid
                    "end": now + timedelta(hours=8),   # valid
                },
                {
                    "start": now + timedelta(hours=1), # valid
                    "end": now + timedelta(hours=3),   # invalid (inside)
                },
            ]
        }
        case_2 = {
            "slots": [
                {
                    "start": now + timedelta(hours=3), # invalid (inside)
                    "end": now + timedelta(hours=6),   # valid
                },
            ]
        }
        case_3 = {
            "slots": [
                {
                    "start": now + timedelta(hours=3),  # invalid
                    "end": now + timedelta(hours=4),  # invalid (both inside)
                },
            ]
        }
        case_4 = {
            "slots": [
                {
                    "start": now + timedelta(hours=1),  # invalid
                    "end": now + timedelta(hours=6),  # invalid (both outside)
                },
            ]
        }

        full_url = reverse(self.view_name, kwargs={"pk": id})
        response = self.client.post(f"{full_url}", data=case_1, format="json",)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(f"{full_url}", data=case_2, format="json", )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(f"{full_url}", data=case_3, format="json", )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(f"{full_url}", data=case_4, format="json", )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        #all new slots should be not created if at list one not correct (case_1):
        self.assertEqual(DoctorSlot.objects.filter(doctor=db_doctor).count(), 1)

    def test_slots_create_with_intersection_with_other_doctor_slot(self):
        self.populate_doctors()
        first_doctor = Doctor.objects.all().first()
        now = timezone.now()
        data = {
            "doctor": first_doctor,
            "start": now + timedelta(hours=2),
            "end": now + timedelta(hours=5),
        }
        DoctorSlot.objects.create(**data)
        # case intersection with first doctor slot
        case = {
            "slots": [
                {
                    "start": now + timedelta(hours=1),
                    "end": now + timedelta(hours=3)
                },
            ]
        }
        other_doctor = Doctor.objects.exclude(id=first_doctor.id).first()
        full_url = reverse(self.view_name, kwargs={"pk": f"{other_doctor.id}"})
        response = self.client.post(full_url, data=case, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

#Slot detail#####slots/<id>/ ##########################

class SlotUnauthenticatedUserTests(TestCase):
    def setUp(self):
        self.view_name = "clinic:detail-slot"
        self.client = APIClient()


    def test_get_slot(self):
        url = reverse(self.view_name, kwargs={"pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_slot(self):
        url = reverse(self.view_name, kwargs={"pk": 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SlotAuthenticatedUserTests(BaseClinicTestCase):
    def setUp(self):
        self.view_name = "clinic:detail-slot"
        self.client = APIClient()
        self.client.force_authenticate(user=self.first_patient)

    def test_get_slot(self):
        self.make_slots_and_1_appointment()
        db_slot = DoctorSlot.objects.first()
        url = reverse(self.view_name, kwargs={"pk": db_slot.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = self.get_result(response)
        serializer = SlotSerializer(db_slot, many=False)
        self.assertEqual(result, serializer.data)

    def test_delete_slot(self):
        url = reverse(self.view_name, kwargs={"pk": 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SlotAdminUserTests(BaseClinicTestCase):
    def setUp(self):
        self.view_name = "clinic:detail-slot"
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)


    def test_delete_free_slot(self):
        self.make_slots_and_1_appointment()
        slot = DoctorSlot.objects.exclude(
            id__in=Appointment.objects.all().values_list("slot", flat=True)
        ).first()
        url = reverse(self.view_name, kwargs={"pk": slot.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DoctorSlot.objects.filter(id=slot.id).exists())

    def test_try_delete_slot_with_appointment(self):
        self.make_slots_and_1_appointment()
        slot = DoctorSlot.objects.filter(
            id__in=Appointment.objects.all().values_list("slot", flat=True)
        ).first()
        url = reverse(self.view_name, kwargs={"pk": slot.id})
        print(url)
        response = self.client.delete(url)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(DoctorSlot.objects.filter(id=slot.id).exists())