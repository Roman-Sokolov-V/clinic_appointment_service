from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

from user.serializers import UserSerializer


class UserViewsTest(TestCase):
    def setUp(self):
        self.payload = {
            "email":'test@test.com',
            "password": 'STRONGpassword123#',
            "first_name":"test",
            "last_name":"test",
            "username":"test"
        }
        self.client = self.client = APIClient()

    def test_register_user(self):
        url = reverse('user:register')
        response = self.client.post(url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        db_user = get_user_model().objects.get(email=self.payload['email'])
        serializer = UserSerializer(db_user)
        self.assertEqual(serializer.data, response.data)


    def test_get_token_pair(self):
        url = reverse('user:token_obtain_pair')
        response = self.client.post(url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data['access']
        refresh_token = response.data['refresh']
        url_verify = reverse("user:token_verify")
        response_verify = self.client.post(
            url_verify,
            {"token": access_token},
            format='json'
        )
        self.assertEqual(response_verify.status_code, status.HTTP_200_OK)
        url_refresh = reverse("user:token_refresh")
        response_refresh = self.client.post(
            url_refresh,
            {"refresh": refresh_token},
            format='json'
        )
        self.assertEqual(response_refresh.status_code, status.HTTP_200_OK)
        self.assertIn('access', response_refresh.data)

        # (Опціонально) Перевіряємо, що новий токен дійсно працює
        new_access_token = response_refresh.data['access']
        url_verify = reverse("user:token_verify")
        response_verify = self.client.post(
            url_verify,
            {"token": new_access_token},
            format='json'
        )
        self.assertEqual(response_verify.status_code, status.HTTP_200_OK)

    def test_get_me_endpoint(self):
        user = get_user_model().objects.create_user(**self.payload)
        url = reverse('user:token_obtain_pair')
        response = self.client.post(url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = "Bearer " + response.data['access']
        url = reverse('user:me')
        response = self.client.get(url, headers={'Authorization': access_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        serializer = UserSerializer(user)
        self.assertEqual(serializer.data, response.data)

    def test_get_me_endpoint(self):
        user = get_user_model().objects.create_user(**self.payload)
        url = reverse('user:token_obtain_pair')
        response = self.client.post(url, self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = "Bearer " + response.data['access']
        url = reverse('user:me')
        response = self.client.get(url, headers={'Authorization': access_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        serializer = UserSerializer(user)
        self.assertEqual(serializer.data, response.data)