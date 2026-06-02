from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView


class SuccessView(APIView):
    pass


class CancelView(APIView):
    pass
