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
            "session_url",
            "session_id",
            "money_to_pay",
        )
        read_only_fields = ("id",)