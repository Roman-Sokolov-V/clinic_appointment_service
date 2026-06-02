from django.contrib import admin

from clinic.models import Specialization, Doctor, DoctorSlot, Appointment


admin.site.register(Specialization)
admin.site.register(Doctor)
admin.site.register(DoctorSlot)
admin.site.register(Appointment)
