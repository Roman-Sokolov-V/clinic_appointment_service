from datetime import datetime
from datetime import timedelta

from django.contrib.auth import get_user_model

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from clinic.models import Specialization, Doctor, DoctorSlot, Appointment
from clinic.serializers import DoctorSerializer


def populate_specializations(extra: list[dict] = None) -> list[Specialization]:
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

def populate_doctors(extra: list[dict] = None) -> list[Doctor]:
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

def create_patient(email: str="test@test", password: str="STRong#password#"):
    return get_user_model().objects.create_user(email, password)

def populate_free_slots(first_date: datetime=None) -> list[DoctorSlot]:
    doctors = populate_doctors()
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

def make_slots_and_1_appointment(first_date: datetime=None):
    if not first_date:
        first_date = timezone.now() + timedelta(hours=1)
    populate_doctors()
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
        price = doctor.price_per_visit
    )


class ResultMixin:

    @staticmethod
    def get_results(response: Response) -> list[dict]:
        return response.data.get("results")

    @staticmethod
    def get_result(response: Response) -> list[dict]:
        return response.data



#Doctor###############################################################
class DoctorMixin():
    url = reverse("clinic:doctor-list")

    @staticmethod
    def get_results(response: Response):
        return response.data.get("results")

    @staticmethod
    def get_result(response: Response):
        return response.data

class DoctorUnauthenticatedUserTests(DoctorMixin, TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_auth_required(self):
        payload = {}
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_auth_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_auth_required(self):
        response = self.client.get(self.url + "1/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_auth_required(self):
        payload = {}
        response = self.client.put(self.url + "1/", payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_partial_update_auth_required(self):
        payload = {}
        response = self.client.patch(self.url + "1/", payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)



class DoctorAuthenticatedUserTests(DoctorMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        user = get_user_model().objects.create_user(
            username="test",
            email="test",
            password="test"
        )
        self.client.force_authenticate(user=user)

    def test_create_auth_required(self):
        payload = {}
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list(self):
        populate_specializations()
        populate_doctors()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        doctors_db = Doctor.objects.all().order_by("id")
        serializer = DoctorSerializer(doctors_db, many=True)
        self.assertEqual(results, serializer.data)

    def test_detail(self):
        populate_specializations()
        populate_doctors()
        doctor = Doctor.objects.all().first()
        id = doctor.id
        response = self.client.get(self.url + f"{id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = self.get_result(response)
        serializer = DoctorSerializer(doctor, many=False)
        self.assertEqual(result, serializer.data)

    def test_update_admin_required(self):
        payload = {}
        response = self.client.put(self.url + "1/", payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_admin_required(self):
        payload = {}
        response = self.client.patch(self.url + "1/", payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



class DoctorAdminUserTests(DoctorMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        admin_user = get_user_model().objects.create_user(
            username="test",
            email="test",
            password="test",
            is_staff=True,
        )
        self.client.force_authenticate(user=admin_user)

    def test_create(self):
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "description": "Test",
            "price_per_visit": "11.11"
        }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list(self):
        populate_specializations()
        populate_doctors()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        doctors_db = Doctor.objects.all().order_by("id")
        serializer = DoctorSerializer(doctors_db, many=True)
        self.assertEqual(results, serializer.data)

    def test_detail(self):
        populate_specializations()
        populate_doctors()
        doctor = Doctor.objects.all().first()
        id = doctor.id
        response = self.client.get(self.url + f"{id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = self.get_result(response)
        serializer = DoctorSerializer(doctor, many=False)
        self.assertEqual(result, serializer.data)

    def test_update(self):
        populate_doctors()
        db_doctor = Doctor.objects.all().first()
        id = db_doctor.id
        payload = {
            "first_name": "New",
            "last_name": "New",
            "description": "New",
            "price_per_visit": "100.01"
        }
        response = self.client.put(self.url + f"{id}/", payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = self.get_result(response)
        for key, value in payload.items():
            self.assertEqual(value, result.get(key))

    def test_partial_update(self):
        populate_doctors()
        db_doctor = Doctor.objects.all().first()
        id = db_doctor.id
        payload = {
            "first_name": "New",
        }
        response = self.client.patch(self.url + f"{id}/", payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = self.get_result(response)
        db_doctor.refresh_from_db()
        self.assertEqual(result.get("first_name"), payload.get("first_name"))
        self.assertEqual(result.get("last_name"), db_doctor.last_name)
        self.assertEqual(result.get("description"), db_doctor.description)


    def test_delete(self):
        populate_doctors()
        db_doctor = Doctor.objects.all().first()
        id = db_doctor.id
        response = self.client.delete(self.url + f"{id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        db_doctor_exist = Doctor.objects.filter(id=id).exists()
        self.assertFalse(db_doctor_exist)
