
from django.db import models

from config.settings import AUTH_USER_MODEL


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

class Doctor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    description = models.TextField()
    price_per_visit = models.DecimalField(max_digits=10, decimal_places=2)
    specializations = models.ManyToManyField(Specialization, related_name='doctors')
    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class DoctorSlot(models.Model):
    doctor_id = models.IntegerField() # чому не ForeignKey
    start = models.DateTimeField()
    end = models.DateTimeField()

APPOINTMENT_STATUS = (
    ('BOOKED', 'booked'),
    ('COMPLETED', 'completed'),
    ('CANCELED', 'Canceled'),
    ('NO_SHOW', 'no_show'),
)

class Appointment(models.Model):
    doctor_slot_id = models.IntegerField() # чому не ForeignKey
    patient_id = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    status = models.CharField(max_length=100, choices=APPOINTMENT_STATUS)
    booked_at = models.DateField()
    completed_at = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

PAYMENT_STATUS = (
    ('PENDING', 'pending'),
    ('PAID', 'paid'),
    ('EXPIRED', 'expired'),
)

PAYMENT_TYPE = (
    ('CONSULTATION', 'consultation'),
    ('CANCELLATION_FEE', 'cancellation fee'),
    ('NO_SHOW_FEE', 'no show fee'),
)

class Payment(models.Model):
    status = models.CharField(max_length=100, choices=PAYMENT_STATUS)
    type = models.CharField(max_length=100, choices=PAYMENT_TYPE)
    appointment_id = models.IntegerField() # чому не OneToOne?
    session_url = models.URLField()
    session_id = models.CharField(max_length=100)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)