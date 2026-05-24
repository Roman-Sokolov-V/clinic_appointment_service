from django.urls import path
from rest_framework import routers
from clinic.views import SpecializationViewSet, DoctorViewSet, ListBulkCreateSlotsApiView


app_name = 'clinic'
router = routers.DefaultRouter()
router.register(r'specializations', SpecializationViewSet, basename='specialization')
router.register(r'doctors', DoctorViewSet, basename='doctor')

urlpatterns = [
    path('doctors/<pk>/slots/', ListBulkCreateSlotsApiView.as_view(), name='bulk-create-slots'),
]
urlpatterns += router.urls
