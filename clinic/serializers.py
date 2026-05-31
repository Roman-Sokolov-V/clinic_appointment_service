from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from clinic.models import Specialization, Doctor, DoctorSlot, Appointment, Payment, APPOINTMENT_STATUS


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
    #patient_id = serializers.IntegerField(required=False)
    #doctor_id = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(
        choices=[value for value, _ in APPOINTMENT_STATUS],
        required=False
    )
    from_date = serializers.DateTimeField(required=False)
    to_date = serializers.DateTimeField(required=False)




class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ('id', 'slot', 'patient', 'status', 'booked_at', 'completed_at', 'price')
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
        return attrs

    def create(self, validated_data):
        slot = validated_data["slot"]

        price = (
            DoctorSlot.objects
            .filter(pk=slot.id)
            .values_list("doctor__price_per_visit", flat=True)
            .get()
        )
        validated_data["price"] = price
        appointment = Appointment.objects.create(**validated_data)
        return appointment


# todo  POST: appointments/ - create appointment (fails if slot already has a BOOKED appointment)
# todo  GET: appointments/?patient_id=...&doctor_id=...&status=...&from=&to= - list appointments
# todo  GET: appointments/<id>/ - get appointment detail
# todo  POST: appointments/<id>/cancel/ - cancel appointment; late-cancel may create CANCELLATION_FEE
# todo  POST: appointments/<id>/complete/ - mark completed
# todo  POST: appointments/<id>/no-show/ - (staff) mark as NO_SHOW (normally set by scheduled job after slot end)

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment