from django.urls import path

from payment.views import SuccessView, CancelView

# from rest_framework import routers
#
#
app_name = 'payment'
# router = routers.DefaultRouter()
# router.register(r'specializations', SpecializationViewSet, basename='specialization')
# router.register(r'doctors', DoctorViewSet, basename='doctor')
# router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('success/', SuccessView.as_view(), name='success'),
    path('cancel/', CancelView.as_view(), name='cancel'),
]
