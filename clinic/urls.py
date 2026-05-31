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
# todo  POST: appointments/ - create appointment (fails if slot already has a BOOKED appointment)
# todo  GET: appointments/?patient_id=...&doctor_id=...&status=...&from=&to= - list appointments
# todo  GET: appointments/<id>/ - get appointment detail
# todo  POST: appointments/<id>/cancel/ - cancel appointment; late-cancel may create CANCELLATION_FEE
# todo  POST: appointments/<id>/complete/ - mark completed
# todo  POST: appointments/<id>/no-show/ - (staff) mark as NO_SHOW (normally set by scheduled job after slot end)
