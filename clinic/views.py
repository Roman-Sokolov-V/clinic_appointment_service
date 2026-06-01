from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView, get_object_or_404
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from clinic.models import Specialization, Doctor, DoctorSlot, Appointment, APPOINTMENT_STATUS
from clinic.permissions import IsOwnerOrAdmin
from clinic.serializers import SpecializationSerializer, DoctorSerializer, BulkCreateSlotsSerializer, \
    SlotDateSerializer, SlotSerializer, AppointmentSerializer, AppointmentFilterSerializer
from clinic.services.appointment_service import AppointmentService


class SpecializationViewSet(viewsets.ModelViewSet):
    model = Specialization
    serializer_class = SpecializationSerializer
    queryset = Specialization.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            permission_classes = [IsAuthenticated()]
        else:
            permission_classes = [IsAdminUser()]
        return permission_classes


class DoctorViewSet(viewsets.ModelViewSet):
    model = Doctor
    serializer_class = DoctorSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            permission_classes = [IsAuthenticated()]
        else:
            permission_classes = [IsAdminUser()]
        return permission_classes


    def get_queryset(self):
        queryset = Doctor.objects.all()
        if self.action == 'list':
            if query_filter := self.request.query_params.get("specialization"):
                queryset = queryset.prefetch_related('specializations')
                if query_filter.isdigit():
                    queryset = queryset.filter(specializations__id=int(query_filter))
                else:
                    queryset = queryset.filter(specializations__code__icontains=query_filter.strip())

        return queryset


class ListBulkCreateSlotsApiView(ListCreateAPIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return SlotSerializer
        return BulkCreateSlotsSerializer

    def create(self, request, *args, **kwargs):
        doctor = get_object_or_404(Doctor, id=self.kwargs["pk"])
        serializer = self.get_serializer(data=request.data, context={"doctor": doctor})
        serializer.is_valid(raise_exception=True)
        created_slots = serializer.save()

        return Response(
            SlotSerializer(created_slots, many=True).data,
            status=status.HTTP_201_CREATED,
        )

    def get_queryset(self):
        doctor_id = self.kwargs["pk"]
        queryset = DoctorSlot.objects.filter(doctor_id=doctor_id)
        if self.request.method == "GET":
            from_ = self.request.query_params.get("from")
            to_ = self.request.query_params.get("to")
            available_only = self.request.query_params.get("available_only")

            if from_ is not None:
                queryset = queryset.filter(start__gte=from_.strip())
            if to_ is not None:
                queryset = queryset.filter(end__lte=to_.strip())
            if available_only is not None:
                if available_only.strip().lower() == "true":
                    queryset = queryset.exclude(
                        id__in=Appointment.objects.filter(
                            status="BOOKED"
                        ).values_list("slot", flat=True)
                    )

        return queryset


class DetailSlotApiView(RetrieveDestroyAPIView):
    serializer_class = SlotSerializer
    queryset = DoctorSlot.objects.all()

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]

    def perform_destroy(self, instance):
        appointment = Appointment.objects.filter(
            slot=instance.id,
            # status="BOOKED" # в завданні якщо взагалі appointment існує не зважаючи на статус
        ).first()
        if appointment:
            raise ValidationError(
                 f"Cannot delete slot because it has an appointment (ID: {appointment.id})."
            )
        instance.delete()

class AppointmentViewSet(
    CreateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    GenericViewSet
):
    model = Appointment
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.select_related("slot").all()

    def get_permissions(self):
        if self.action  in ('list', 'create'):
            return [IsAuthenticated()]
        if self.action in ('retrieve', 'cancel'):
            return [IsOwnerOrAdmin()]

        return [IsAdminUser()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            filter_serializer = AppointmentFilterSerializer(
                data=self.request.query_params
            )
            filter_serializer.is_valid(raise_exception=False)
            filters = filter_serializer.validated_data
            patient_id = filters.get("patient_id")
            doctor_id = filters.get("doctor_id")
            status_ = filters.get("status")
            from_date = filters.get("from_date")
            to_date = filters.get("to_date")


            if patient_id:
                queryset = queryset.filter(patient_id=patient_id)
            if doctor_id:
                queryset = queryset.filter(slot__doctor_id=doctor_id)
            if status_:
                queryset = queryset.filter(status=status_)
            if from_date:
                queryset = queryset.filter(slot__start__gte=from_date)
            if to_date:
                queryset = queryset.filter(slot__start__lte=to_date)

            # casual users can see own appointments only
            if not self.request.user.is_staff:
                queryset = queryset.filter(patient=self.request.user)
        return queryset


    def perform_create(self, serializer):
        """
        Fill patient_id fields before creating appointment
        """
        user = self.request.user
        patient = serializer.validated_data.get("patient")
        if user.is_staff:
            if not patient:
                raise ValidationError({"patient": "Required for admin"})
            serializer.save()
        else:
            if patient and patient != user:
                raise ValidationError(
                    {
                        "patient": "You are not allowed to create appointment not for yourself."
                                   " To create appointment for yourself, you do not have to fill field 'patient'"
                    }
                )
            serializer.save(patient=user)

    def cancellation_fee(self, appointment):
        pass

    @action(methods=["POST"], detail=True)
    def cancel(self, request, pk=None):
        appointment = self.get_object()

        self.check_object_permissions(request, appointment)

        appointment = AppointmentService.cancel_appointment(
            appointment=appointment,
            user=request.user
        )

        return Response(
            {"status": appointment.status},
            status=status.HTTP_200_OK
        )

    @action(methods=["POST"], detail=True)
    def complete(self, request, pk=None):
        appointment = self.get_object()
        appointment = AppointmentService.complete_appointment(appointment)
        return Response(
            {"status": appointment.status},
            status=status.HTTP_200_OK
        )


# todo  POST: appointments/<id>/complete/ - mark completed
# todo  POST: appointments/<id>/no-show/ - (staff) mark as NO_SHOW (normally set by scheduled job after slot end)

