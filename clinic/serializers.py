from django.db import transaction
from rest_framework import serializers

from clinic.models import Specialization, Doctor, DoctorSlot, Appointment, Payment


class SpecializationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Specialization
        fields = ('id', 'name', 'code', 'description')



class DoctorSerializer(serializers.ModelSerializer):
    specializations = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )
    class Meta:
        model = Doctor
        fields = (
            'id', 'first_name', 'last_name', 'description', 'price_per_visit', 'specializations'
        )

class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSlot
        fields = ('id', 'doctor_id', 'start', 'end')

class SlotDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSlot
        fields = ('start', 'end')

class BulkCreateSlotsSerializer(serializers.Serializer):
    slots = SlotDateSerializer(many=True)

    def create(self, validated_data):
        doctor_id = self.context["doctor_id"]
        slots = [
            DoctorSlot(
                doctor_id=int(doctor_id),
                **slot_data
            )
            for slot_data in validated_data["slots"]
        ]

        with transaction.atomic():
            created_slots = DoctorSlot.objects.bulk_create(slots)
            return created_slots


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment

