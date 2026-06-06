from rest_framework import serializers
from payment.models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "method",
            "type",
            "appointment",
            "money_to_pay",
            "provider_metadata"
        )
        read_only_fields = ("id",)