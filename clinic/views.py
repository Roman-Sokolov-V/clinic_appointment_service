from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.response import Response

from clinic.models import Specialization, Doctor, DoctorSlot, Appointment
from clinic.serializers import SpecializationSerializer, DoctorSerializer, BulkCreateSlotsSerializer, \
    SlotDateSerializer, SlotSerializer


# @api_view(["POST", "GET"])
# def specialization_view(request):
#     if request.method == 'POST':
#         serializer = SpecializationSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     elif request.method == 'GET':
#         specializations = Specialization.objects.all()
#         serializer = SpecializationSerializer(specializations, many=True)
#         return Response(serializer.data)
#
#
# @api_view(["GET", "DELETE", "PUT", "PATCH"])
# def specialization_detail_view(request, pk):
#     specialization = get_object_or_404(Specialization, pk=pk)
#     if request.method == 'GET':
#         serializer = SpecializationSerializer(specialization)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     elif request.method == 'DELETE':
#         specialization.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
#
#     elif request.method == 'PUT':
#         serializer = SpecializationSerializer(specialization, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     elif request.method == 'PATCH':
#         serializer = SpecializationSerializer(specialization, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_200_OK)


class SpecializationViewSet(viewsets.ModelViewSet):
    model = Specialization
    serializer_class = SpecializationSerializer
    queryset = Specialization.objects.all()


class DoctorViewSet(viewsets.ModelViewSet):
    model = Doctor
    serializer_class = DoctorSerializer
    queryset = Doctor.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
                if specialization := self.request.query_params.get("specialization"):
                    queryset = Doctor.objects.all().prefetch_related('specializations')
                    if specialization.isdigit():
                        queryset = queryset.filter(specializations=int(specialization))
                    else:
                        queryset = queryset.filter(specializations__code__iexact=specialization.strip())
        return queryset


class ListBulkCreateSlotsApiView(ListCreateAPIView):


    def get_serializer_class(self):
        if self.request.method == "GET":
            return SlotSerializer
        return BulkCreateSlotsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"doctor_id": self.kwargs["pk"]}
        )
        serializer.is_valid(raise_exception=True)
        created_slots = serializer.save()

        return Response(
            SlotDateSerializer(created_slots, many=True).data,
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
                # queryset = queryset.filter(end__lte=to_)
                queryset = queryset.filter(end__lte=to_.strip())
            if available_only is not None:
                if available_only.strip().lower() == "true":
                    queryset = queryset.exclude(
                        id__in=Appointment.objects.filter(
                            status="BOOKED"
                        ).values_list("doctor_slot_id", flat=True)
                    )
        return queryset


class DetailSlotApiView(RetrieveDestroyAPIView):
    serializer_class = SlotSerializer

    def perform_destroy(self, instance):
        appointment = Appointment.objects.filter(
            doctor_slot_id=instance.id,
            status="BOOKED" #  в завданні без цього, але логічніше так
        ).first()
        if appointment:
            raise ValidationError(
                 f"Cannot delete slot because it has a booked appointment (ID: {appointment.id})."
            )
        instance.delete()



