from django.db import models
from django.db.models import F, CheckConstraint, Q

from clinic.models import Appointment

PAYMENT_STATUS = (
    ('PENDING', 'pending'),
    ('PAID', 'paid'),
    ('EXPIRED', 'expired'),
    ('REFUNDED', 'refunded'),
    ('REFUND_PENDING', 'refund_pending'),
)

PAYMENT_TYPE = (
    ('CONSULTATION', 'consultation'),
    #('CANCELLATION_FEE', 'cancellation fee'),
    ('NO_SHOW_FEE', 'no show fee'),
)
PAYMENT_METHOD = (
    ('CASH', 'Cash'),
    ('STRIPE', 'Stripe'),
)
class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending payment'
    PAID = 'PAID', 'Paid'
    FAILED = 'FAILED', 'Payment failed'

class Payment(models.Model):
    status = models.CharField(max_length=100, choices=PAYMENT_STATUS, default='PENDING')
    type = models.CharField(max_length=100, choices=PAYMENT_TYPE)
    method = models.CharField(max_length=100, choices=PAYMENT_METHOD, default='STRIPE')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='payments')
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)
    provider_metadata = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        indexes = [
            # Створюємо індекс для ключа session_id всередині JSONField
            models.Index(
                F('provider_metadata__session_id'),  # Django сам трансформує це в потрібний SQL для Postgres
                name='payment_stripe_sid_idx'
            ),
        ]
        constraints = [
            CheckConstraint(condition=Q(status__in=[item[0] for item in PAYMENT_STATUS]), name='check_payment_status_valid')
        ]

    @property
    def stripe_session_id(self):
        if self.type == 'STRIPE':
            return self.provider_metadata.get('session_id')
        return None

    @property
    def stripe_session_url(self):
        if self.type == 'STRIPE':
            return self.provider_metadata.get('session_url')
        return None