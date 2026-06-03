from django.db import models

from clinic.models import Appointment

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
    status = models.CharField(max_length=100, choices=PAYMENT_STATUS, default='PENDING')
    type = models.CharField(max_length=100, choices=PAYMENT_TYPE)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='payments')
    session_url = models.URLField(max_length=500)
    session_id = models.CharField(max_length=100)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)
