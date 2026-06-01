from django.urls import path
from rest_framework import routers
from clinic.views import SpecializationViewSet, DoctorViewSet, AppointmentViewSet, \
    DetailSlotApiView, ListBulkCreateSlotsApiView

app_name = 'clinic'
router = routers.DefaultRouter()
router.register(r'specializations', SpecializationViewSet, basename='specialization')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('doctors/<pk>/slots/', ListBulkCreateSlotsApiView.as_view(), name='bulk-create-list-slots'),
    path('slots/<pk>/', DetailSlotApiView.as_view(), name='detail-slot'),
]
urlpatterns += router.urls
