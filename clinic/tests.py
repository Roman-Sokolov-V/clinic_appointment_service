from datetime import datetime
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model

from django.test import TestCase
from django.utils import timezone
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from clinic.models import Specialization, Doctor, DoctorSlot, Appointment, APPOINTMENT_STATUS
from clinic.serializers import SpecializationSerializer, DoctorSerializer, SlotSerializer, SlotDateSerializer


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


class SpecializationMixin():
    url = reverse("clinic:specialization-list")

    @staticmethod
    def get_results(response: Response):
        return response.data.get("results")

    @staticmethod
    def get_result(response: Response):
        return response.data

class SpecializationUnauthenticatedUserTests(SpecializationMixin, TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_auth_required(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_auth_required(self):
        payload = {
            "name": "test",
            "code": "test",
            "description": "test",
        }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_auth_required(self):
        response = self.client.get(self.url + '1/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_auth_required(self):
        response = self.client.delete(self.url + '1/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_auth_required(self):
        payload = {
            "name": "test",
            "code": "test",
            "description": "test",
        }
        response = self.client.put(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SpecializationAuthenticatedUserTests(SpecializationMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="test",
            email="test@test.com",
            password="testpassword"
        )
        self.client.force_authenticate(self.user)


    def test_list(self):
        populate_specializations()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 2)
        specializations_db = Specialization.objects.all().order_by('id')
        serializer = SpecializationSerializer(specializations_db, many=True)
        self.assertEqual(results, serializer.data)

    def test_create(self):
        payload = {
            "name": "test",
            "code": "test",
            "description": "test",
        }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_retrieve(self):
        populate_specializations()
        s_bd = Specialization.objects.all().first()
        id = s_bd.id
        response = self.client.get(self.url + f"{id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = self.get_result(response)
        serializer = SpecializationSerializer(s_bd, many=False)
        self.assertEqual(result, serializer.data)


    def test_delete_auth_required(self):
        populate_specializations()
        s_bd = Specialization.objects.all().first()
        id = s_bd.id
        response = self.client.delete(self.url + f"{id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_auth_required(self):
        populate_specializations()
        payload = {
            "name": "test",
            "code": "test",
            "description": "test",
        }
        response = self.client.put(self.url + f"{id}/", payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



class SpecializationAdminTest(SpecializationMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="test",
            email="test@test.com",
            password="testpassword",
            is_staff=True,

        )
        self.client.force_authenticate(self.user)

    def test_create(self):
        payload = {
            "name": "test",
            "code": "test",
            "description": "test",
        }
        response = self.client.post(self.url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = self.get_result(response)
        self.assertEqual(result["name"], payload["name"])
        self.assertEqual(result["code"], payload["code"])
        self.assertEqual(result["description"], payload["description"])
        self.assertEqual(result["id"], 1)

    def test_list(self):
        populate_specializations()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 2)
        specializations_db = Specialization.objects.all().order_by('id')
        serializer = SpecializationSerializer(specializations_db, many=True)
        self.assertEqual(results, serializer.data)


    def test_retrieve(self):
        populate_specializations()
        s_bd = Specialization.objects.all().first()
        id = s_bd.id
        response = self.client.get(self.url + f"{id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = self.get_result(response)
        serializer = SpecializationSerializer(s_bd, many=False)
        self.assertEqual(result, serializer.data)

    def test_delete(self):
        populate_specializations()
        s_bd = Specialization.objects.all().first()
        id = s_bd.id
        response = self.client.delete(self.url + f"{id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        populate_specializations()
        payload = {
            "name": "New",
            "code": "New",
            "description": "New",
        }
        s_bd = Specialization.objects.all().first()
        id = s_bd.id
        response = self.client.put(self.url + f"{id}/", payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = self.get_result(response)
        for key in payload.keys():
            self.assertEqual(result[key], payload[key])

    def test_partial_update(self):
        populate_specializations()
        payload = {
            "name": "New",
        }
        s_bd = Specialization.objects.all().first()
        id = s_bd.id
        response = self.client.patch(self.url + f"{id}/", payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = self.get_result(response)
        self.assertEqual(result["name"], payload["name"])
        self.assertEqual(result["code"], s_bd.code)
        self.assertEqual(result["description"], s_bd.description)

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


#Slots####doctors/<id>/slots/############################################################
class DoctorsSlotsUnauthenticatedUserTests(DoctorMixin, TestCase):
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


class DoctorsSlotsAuthenticatedUserTests(DoctorMixin, TestCase):
    def setUp(self):
        self.view_name = "clinic:bulk-create-list-slots"
        self.client = APIClient()
        user = get_user_model().objects.create_user(
            email="test",
            password="test"
        )
        self.client.force_authenticate(user=user)

    def test_slots_create_with_valid_data(self):
        payload = {}
        full_url = reverse(self.view_name, kwargs={"pk": 1})
        response = self.client.post(f"{full_url}", data=payload, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_slots_list_with_filter_from(self):
        first_date = timezone.now() + timedelta(hours=1)
        make_slots_and_1_appointment(first_date)
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
        make_slots_and_1_appointment(first_date)
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
        first_date = timezone.now() + timedelta(hours=1)
        make_slots_and_1_appointment(first_date)
        doctor = Doctor.objects.first()

        db_slots = DoctorSlot.objects.filter(doctor=doctor).exclude(
                        id__in=Appointment.objects.filter(
                            status="BOOKED"
                        ).values_list("slot", flat=True)
                    )
        url = reverse(self.view_name, kwargs={"pk": f"{doctor.id}"})
        full_url = url + f"?available=true"
        response = self.client.get(full_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        serializer = SlotSerializer(db_slots, many=True)
        self.assertEqual(results, serializer.data)


class DoctorsSlotsAdminUserTests(DoctorMixin, TestCase):
    def setUp(self):
        self.view_name = "clinic:bulk-create-list-slots"
        self.client = APIClient()
        user = get_user_model().objects.create_user(
            email="test",
            password="test",
            is_staff=True,
        )
        self.client.force_authenticate(user=user)


    def test_slots_create_with_valid_data(self):
        populate_doctors()
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
        populate_doctors()
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
        populate_doctors()
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
        populate_doctors()
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


class SlotAuthenticatedUserTests(ResultMixin, TestCase):
    def setUp(self):
        self.view_name = "clinic:detail-slot"
        self.client = APIClient()
        user = get_user_model().objects.create_user(
            email="Test",
            password="test",
        )
        self.client.force_authenticate(user=user)

    def test_get_slot(self):
        make_slots_and_1_appointment()
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


class SlotAdminUserTests(ResultMixin, TestCase):
    def setUp(self):
        self.view_name = "clinic:detail-slot"
        self.client = APIClient()
        admin = get_user_model().objects.create_user(
            email="Test",
            password="test",
            is_staff=True,
        )
        self.client.force_authenticate(user=admin)


    def test_delete_free_slot(self):
        make_slots_and_1_appointment()
        slot = DoctorSlot.objects.exclude(
            id__in=Appointment.objects.all().values_list("slot", flat=True)
        ).first()
        url = reverse(self.view_name, kwargs={"pk": slot.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DoctorSlot.objects.filter(id=slot.id).exists())

    def test_try_delete_slot_with_appointment(self):
        make_slots_and_1_appointment()
        slot = DoctorSlot.objects.filter(
            id__in=Appointment.objects.all().values_list("slot", flat=True)
        ).first()
        url = reverse(self.view_name, kwargs={"pk": slot.id})
        print(url)
        response = self.client.delete(url)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(DoctorSlot.objects.filter(id=slot.id).exists())


#Appointments################################################
class AppointmentUnauthenticatedUserTests(TestCase):
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



########
class AppointmentAuthenticatedUserTests(ResultMixin, TestCase):
    def setUp(self):
        self.view_name = "clinic:appointment"
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="Test",
            password="test",
        )
        self.client.force_authenticate(user=self.user)

    def test_create_appointment(self):
        slots = populate_free_slots()
        slot = slots[0]
        payload = {
            "slot": slot.id,
        }
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = self.get_result(response)
        # check price automatically got from doctors                  price_per_visit
        self.assertEqual(
            Decimal(result["price"]),
            Doctor.objects.get(id=slot.doctor_id).price_per_visit
        )

    def test_cant_create_appointment_for_other_patient(self):
        slots = populate_free_slots()
        slot = slots[0]
        other_patient = create_patient()
        payload = {
            "slot": slot.id,
            "patient": other_patient.id,
        }
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_appointment_only_own_appointments(self):
        make_slots_and_1_appointment()
        free_slots = DoctorSlot.objects.filter(appointments__isnull=True)
        Appointment.objects.create(
            patient=self.user,
            slot=free_slots[0],
            price="22.22"
        )
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["patient"], self.user.id)
        print(results)

    def test_list_appointment_with_filter_status(self):
        slots = populate_free_slots()
        for slot in slots:
            Appointment.objects.create(
                patient=self.user,
                slot=slot,
                price="22.22"
            )
        users_appointments = [
            Appointment.objects.create(
                patient=self.user, slot=slot, price="22.22"
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
        slots = populate_free_slots()
        for slot in slots:
            Appointment.objects.create(
                patient=self.user, slot=slot, price="22.22"
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
        slots = populate_free_slots()
        slot = slots[0]
        appointment = Appointment.objects.create(
            patient=self.user,
            slot=slot,
            price="22.22",
        )
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        print(url)
        response = self.client.get(url)
        result = self.get_result(response)
        print(result)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cant_get_another_person_detail_appointment(self):
        slots = populate_free_slots()
        another_person = get_user_model().objects.create_user(
            email="another_person@gmail.com",
            password="STrong12password#",
        )
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

    def test_cancel_appointment(self):
        slots = populate_free_slots()
        slot = slots[0]
        appointment = Appointment.objects.create(
            patient=self.user,
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

    def test_cant_cancel_not_own_appointment(self):
        slots = populate_free_slots()
        slot = slots[0]
        other_user = create_patient()
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
        slots = populate_free_slots()
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


class AppointmentAdminUserTests(ResultMixin, TestCase):
    def setUp(self):
        self.view_name = "clinic:appointment"
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            email="Test",
            password="test",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.admin)

    def test_create_appointment_with_patient_in_payload(self):
        slots = populate_free_slots()
        patient = create_patient()
        print(patient)
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
        slots = populate_free_slots()
        slot = slots[0]
        other_user = create_patient()
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
            slots = populate_free_slots()
            patient = create_patient()
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