
from django.db import models
from django.db.models import Q, F
from django.db.models.constraints import CheckConstraint, UniqueConstraint
from django.utils import timezone

from config.settings import AUTH_USER_MODEL


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=100, unique=True) # name i code по суті дублюють один одного, для чого?
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
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='slots')
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        constraints = [
            CheckConstraint(condition=Q(end__gt=F("start")), name='doctor_slot_end_later_start'),
        ]

    @staticmethod
    def validate_slots_not_intersect(doctor, start, end, error_to_raise, pk):
        queryset = DoctorSlot.objects.filter(
            doctor=doctor, start__lt=end, end__gt=start
        )
        if pk:
            queryset = queryset.exclude(pk=pk)

        has_intersect = queryset.exists()

        if has_intersect:
            raise error_to_raise(
                f"Slot (start: {start}, end: {end}) has intersection with existing doctor slots",
            )

    def clean(self):
        self.validate_slots_not_intersect(
            doctor=self.doctor,
            start=self.start,
            end=self.end,
            error_to_raise=ValueError,
            pk=self.pk if self.pk else None,
        )

APPOINTMENT_STATUS = (
    ('BOOKED', 'booked'),
    ('COMPLETED', 'completed'),
    ('CANCELED', 'canceled'),
    ('NO_SHOW', 'no_show'),
)

class Appointment(models.Model):
    slot = models.ForeignKey(DoctorSlot, on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    status = models.CharField(max_length=100, choices=APPOINTMENT_STATUS, default='BOOKED')
    booked_at = models.DateField(auto_now_add=True)
    completed_at = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # під час створення з Doctor.price_per_visit але не змінюється автоматично якщо зміниться price_per_visit

    @staticmethod
    def validate_slot_not_expired(slot: DoctorSlot, error_to_raise):
        if timezone.now() >= slot.start:
            raise error_to_raise(
                {
                    f"slot_id": f"doctor_slot with id {slot.id} is expired",
                }
            )

    @staticmethod
    def validate_slot_not_already_booked(slot: DoctorSlot, error_to_raise):
        same_slot_appointments = Appointment.objects.filter(slot=slot)
        for appointment in same_slot_appointments:
            if appointment.status == 'BOOKED':
                raise error_to_raise(
                    {
                        "slot": f"doctor_slot with id {slot.id} has already booked",
                    }
                )

    def clean(self):
        self.validate_slot_not_expired(self.slot, ValueError)
        self.validate_slot_not_already_booked(self.slot, ValueError)


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