from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from clinic.models import Specialization
from clinic.serializers import SpecializationSerializer
from clinic.tests.base import BaseClinicTestCase



class SpecializationUnauthenticatedUserTests(BaseClinicTestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("clinic:specialization-list")

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


class SpecializationAuthenticatedUserTests(BaseClinicTestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("clinic:specialization-list")
        self.client.force_authenticate(self.first_patient)


    def test_list(self):
        self.populate_specializations()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 3)
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
        self.populate_specializations()
        s_bd = Specialization.objects.all().first()
        id = s_bd.id
        response = self.client.get(self.url + f"{id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = self.get_result(response)
        serializer = SpecializationSerializer(s_bd, many=False)
        self.assertEqual(result, serializer.data)


    def test_delete_auth_required(self):
        self.populate_specializations()
        s_bd = Specialization.objects.all().first()
        id = s_bd.id
        response = self.client.delete(self.url + f"{id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_auth_required(self):
        self.populate_specializations()
        payload = {
            "name": "test",
            "code": "test",
            "description": "test",
        }
        response = self.client.put(self.url + f"{id}/", payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



class SpecializationAdminTest(BaseClinicTestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("clinic:specialization-list")
        self.client.force_authenticate(self.admin_user)

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
        self.populate_specializations()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 3)
        specializations_db = Specialization.objects.all().order_by('id')
        serializer = SpecializationSerializer(specializations_db, many=True)
        self.assertEqual(results, serializer.data)


    def test_retrieve(self):
        self.populate_specializations()
        s_bd = Specialization.objects.all().first()
        id = s_bd.id
        response = self.client.get(self.url + f"{id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = self.get_result(response)
        serializer = SpecializationSerializer(s_bd, many=False)
        self.assertEqual(result, serializer.data)

    def test_delete(self):
        self.populate_specializations()
        s_bd = Specialization.objects.all().first()
        id = s_bd.id
        response = self.client.delete(self.url + f"{id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update(self):
        self.populate_specializations()
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
        self.populate_specializations()
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