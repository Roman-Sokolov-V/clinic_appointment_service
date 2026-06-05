from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from clinic.models import Specialization, Doctor, DoctorSlot, Appointment, APPOINTMENT_STATUS


class SpecializationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Specialization
        fields = ('id', 'name', 'code', 'description')



class DoctorSerializer(serializers.ModelSerializer):
    specializations = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Doctor.objects.all(),
        required = False
    )
    class Meta:
        model = Doctor
        fields = (
            'id', 'first_name', 'last_name', 'description', 'price_per_visit', 'specializations'
        )


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSlot
        fields = ('id', 'doctor', 'start', 'end')

class SlotDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSlot
        fields = ('start', 'end')

    def validate(self, attrs):
        if attrs["start"] < timezone.now():
            raise ValidationError(
                "Start can not be less than current time"
            )
        if attrs["start"] >= attrs["end"]:
            raise serializers.ValidationError(
                "start must be less than end"
            )
        return attrs

class BulkCreateSlotsSerializer(serializers.Serializer):
    slots = SlotDateSerializer(many=True)

    def create(self, validated_data):
        doctor = self.context['doctor']
        slots_data = validated_data["slots"]
        created_slots = []
        with transaction.atomic():
            for slot_data in slots_data:
                DoctorSlot.validate_slots_not_intersect(
                    pk=None,
                    doctor=doctor,
                    error_to_raise=serializers.ValidationError,
                    **slot_data
                )
                created_slot = DoctorSlot.objects.create(doctor=doctor, **slot_data)
                created_slots.append(created_slot)
            return created_slots



class AppointmentFilterSerializer(serializers.Serializer):
    """serializer for filtering appointments"""

    #patient_id = serializers.IntegerField(required=False)
    #doctor_id = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(
        choices=[value for value, _ in APPOINTMENT_STATUS],
        required=False
    )
    from_date = serializers.DateTimeField(required=False)
    to_date = serializers.DateTimeField(required=False)




class AppointmentSerializer(serializers.ModelSerializer):
    frontend_success_url = serializers.URLField(required=False, write_only=True)
    frontend_cancel_url = serializers.URLField(required=False, write_only=True)
    patient = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        required=False
    )
    class Meta:
        model = Appointment
        fields = (
            'id', 'slot', 'patient', 'status', 'booked_at', 'completed_at', 'price',
            'frontend_success_url', 'frontend_cancel_url'
        )
        read_only_fields = ('id', 'status', 'booked_at', 'completed_at', 'price')


    def validate(self, attrs):
        Appointment.validate_slot_not_expired(
            attrs["slot"],
            serializers.ValidationError
        )
        Appointment.validate_slot_not_already_booked(
            attrs["slot"],
            serializers.ValidationError
        )
        now = timezone.now()
        slot_start = DoctorSlot.objects.get(attrs["slot"]).start
        if now + timedelta(hours=1) > slot_start:
            raise serializers.ValidationError(
                {"booked_at": "You cannot create an appointment with payment later than an hour before slot.start"}
            )
        return attrs


    def create(self, validated_data):
        """
        Create and return a new Appointment instance.

        This method extracts frontend redirection URLs from the validated data
        and temporarily stores them as instance attributes (`self.frontend_success_url`
        and `self.frontend_cancel_url`). This allows the calling View/ViewSet to
        retrieve these URLs later and pass them to the payment gateway service.

        The extracted URLs are popped out of `validated_data` to prevent Django's
        ORM from throwing an unexpected keyword argument error, as these fields
        do not exist in the Appointment database model.

        Additionally, it automatically fetches the doctor's current consultation
        price from the related DoctorSlot and assigns it to the appointment before saving.

        :param validated_data: dict, validated fields from the incoming request.
        :return: Appointment instance.
        """
        self.frontend_success_url = validated_data.pop("frontend_success_url", None)
        self.frontend_cancel_url = validated_data.pop("frontend_cancel_url", None)
        slot = validated_data["slot"]
        price = (
            DoctorSlot.objects
            .filter(pk=slot.id)
            .values_list("doctor__price_per_visit", flat=True)
            .get()
        )
        validated_data["price"] = price
        return Appointment.objects.create(**validated_data)

