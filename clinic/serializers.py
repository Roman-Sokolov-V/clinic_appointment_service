from datetime import timedelta

from django.contrib.auth import get_user_model

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from clinic.models import Specialization, Doctor, DoctorSlot, Appointment, APPOINTMENT_STATUS, GlobalClinicSettings


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
    status = serializers.ChoiceField(
        choices=[value for value, _ in APPOINTMENT_STATUS],
        required=False
    )
    from_date = serializers.DateTimeField(required=False)
    to_date = serializers.DateTimeField(required=False)



class StripePaymentDataSerializer(serializers.Serializer):
    frontend_success_url = serializers.URLField(required=False, write_only=True)
    frontend_cancel_url = serializers.URLField(required=False, write_only=True)

class CashPaymentDataSerializer(serializers.Serializer):
    pass


class AppointmentSerializer(serializers.ModelSerializer):
    slot = serializers.PrimaryKeyRelatedField(
        queryset=DoctorSlot.objects.select_related("doctor").all()
    )

    payment_data = serializers.JSONField(write_only=True, required=False)
    patient = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        required=False,
        default=serializers.CurrentUserDefault()
    )
    payment_method = serializers.ChoiceField(
        choices=["STRIPE", "CASH"], # додати якщо з'являться нові методи крім Cash Stripe
        default='STRIPE',
        write_only=True
    )
    class Meta:
        model = Appointment
        fields = (
            'id', 'slot', 'patient', 'status', 'booked_at', 'completed_at', 'price',
            'payment_method', 'payment_data', 'percent_fee', 'window_fee'
        )
        read_only_fields = ('id', 'status', 'booked_at', 'completed_at', 'price', 'percent_fee', 'window_fee')

    def to_internal_value(self, data):
        """
        Цей метод запускається ДО валідації.
        Він дивиться на payment_method і динамічно валідує payment_data.
        """
        # Спочатку запускаємо стандартну збірку даних DRF
        internal_data = super().to_internal_value(data)

        payment_method = data.get('payment_method', 'STRIPE').upper()
        raw_payment_data = data.get('payment_data', {})

        # Мапа: який метод — який серіалізатор викликати
        serializer_mapping = {
            'STRIPE': StripePaymentDataSerializer,
            'CASH': CashPaymentDataSerializer,
        }

        serializer_class = serializer_mapping.get(payment_method)

        if serializer_class:
            serializer = serializer_class(data=raw_payment_data)
            serializer.is_valid(raise_exception=True)

            # Записуємо вже провалідовані та очищені дані назад
            internal_data['payment_data'] = serializer.validated_data

        return internal_data


    def validate_patient(self, value):
        current_user = self.context['request'].user
        if current_user.is_staff and current_user == value:
            raise serializers.ValidationError("Required for admin")
        if value != current_user and not current_user.is_staff:
            raise serializers.ValidationError(
                "You are not allowed to create appointment not for yourself. "
                "To create appointment for yourself, you do not have to fill field 'patient'"
            )
        return value



    def validate(self, attrs):
        Appointment.validate_slot_not_expired(
            attrs["slot"],
            serializers.ValidationError
        )
        Appointment.validate_slot_not_already_booked(
            attrs["slot"],
            serializers.ValidationError
        )
        slot_start = attrs["slot"].start
        payment_method = attrs["payment_method"]
        user = self.context['request'].user
        is_late_to_book_with_stripe = timezone.now() + timedelta(hours=1) > slot_start

        if payment_method == "Stripe" and is_late_to_book_with_stripe:
            if user.is_staff:
                raise serializers.ValidationError(
                    {
                        "booked_at": "Ordering online later than an hour before the start of the appointment"
                                     " is not possible, You can offer the client to pay in cash and create"
                                     " appointment with field payment_method = 'Cash', after client paid"
                    }
                )
            else:
                raise serializers.ValidationError(
                        {
                            "booked_at": "You cannot place an order online less than one hour before the appointment "
                                         "starts, but you can still sign up in person and pay in cash if there are "
                                         "still openings available before the appointment begins."
                        }
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
        self.payment_data: dict = validated_data.pop("payment_data", None)
        self.payment_method: str = validated_data.pop("payment_method", None)
        slot: DoctorSlot = validated_data["slot"]
        validated_data["price"] = slot.doctor.price_per_visit
        settings, _ = GlobalClinicSettings.objects.get_or_create(singleton_id=1)
        validated_data["percent_fee"] = settings.fee
        validated_data["fee_window"] = settings.fee_window

        return Appointment.objects.create(**validated_data)




class GlobalClinicSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalClinicSettings
        fields = ("id", "fee", "fee_window", "singleton_id")
        read_only_fields = ("id", "singleton_id")

    def create(self, validated_data):
        if GlobalClinicSettings.objects.all().exists():
            raise serializers.ValidationError(
                {
                    "settings": "Only 1 instance possible, try update instead create"
                }
            )


class CancelAppointmentSerializer(serializers.Serializer):
    patient = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        required=False,
        default=serializers.CurrentUserDefault()
    )
    manual_cancel_fee = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if not self.context["request"].user.is_staff:
            attrs["manual_cancel_fee"] = False
        return attrs

