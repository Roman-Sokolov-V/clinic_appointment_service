from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from clinic.models import DoctorSlot, Appointment, APPOINTMENT_STATUS
from clinic.tests.base import BaseClinicTestCase, mock_payment_service


class AppointmentUnauthenticatedUserTests(BaseClinicTestCase):
    def setUp(self):
        self.view_name = "clinic:appointment"
        self.client = APIClient()

    def test_create_appointment(self):
        payload = {}
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_appointment(self):
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_get_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_update_patch_appointment(self):
        payload = {}
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.put(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.patch(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cancel_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        full_url = url + "cancel/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_cant_mark_complete_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        full_url = url + "complete/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cant_mark_no_show_status(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        full_url = url + "no-show/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AppointmentAuthenticatedUserTests(BaseClinicTestCase):
    def setUp(self):
        self.view_name = "clinic:appointment"
        self.client = APIClient()
        self.request_user = self.first_patient
        self.client.force_authenticate(user=self.request_user)



    def test_create_appointment_stripe(self):
        url = reverse(self.view_name + "-list")
        slots = self.populate_free_slots()
        payload = {
            "slot": slots[0].id,
            "method": "STRIPE"  # за замовченням, але залишу так для прозорості
        }
        expected_url = "https://checkout.stripe.com/c/pay/cs_test_12345"
        provider_metadata = {
            "session_id": "cs_test_12345",
            "session_url": expected_url
        }


        with mock_payment_service(provider_metadata=provider_metadata) as mock_factory:
            response = self.client.post(url, data=payload, format="json")

            # Перевірки API
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            result = self.get_result(response)
            self.assertEqual(result["patient"], self.request_user.id)
            self.assertEqual(result["checkout_url"], expected_url)

            # Перевірка поведінки моку
            self.assertEqual(mock_factory.call_count, 1)  # service called
            payment_service_class = mock_factory.created_service_classes[0]
            payment_service_class.return_value.create_payment.assert_called_once()  # method called


    def test_cant_create_appointment_for_other_patient(self):
        slots = self.populate_free_slots()
        slot = slots[0]
        other_patient = self.second_patient
        payload = {
            "slot": slot.id,
            "patient": other_patient.id,
        }
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_appointment_only_own_appointments(self):
        self.make_slots_and_1_appointment()
        free_slots = DoctorSlot.objects.filter(appointments__isnull=True)
        Appointment.objects.create(
            patient=self.request_user,
            slot=free_slots[0],
            price="22.22"
        )
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["patient"], self.request_user.id)
        print(results)

    def test_list_appointment_with_filter_status(self):
        slots = self.populate_free_slots()
        for slot in slots:
            Appointment.objects.create(
                patient=self.request_user,
                slot=slot,
                price="22.22"
            )
        users_appointments = [
            Appointment.objects.create(
                patient=self.request_user, slot=slot, price="22.22"
            ) for slot in slots
        ]
        status_choices = [value for value, _ in APPOINTMENT_STATUS]

        for i, appointment_status in enumerate(status_choices):
            users_appointments[i].status = appointment_status
            users_appointments[i].save()

        for appointment_status in status_choices:
            full_view_name = self.view_name + "-list"
            url = reverse(full_view_name) + f"?status={appointment_status}"
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = self.get_results(response)
            self.assertTrue(len(results) >= 1)
            for result in results:
                self.assertEqual(result["status"], appointment_status)

    def test_list_appointment_with_filters_from_and_to(self):
        slots = self.populate_free_slots()
        for slot in slots:
            Appointment.objects.create(
                patient=self.request_user, slot=slot, price="22.22"
            )

        all_slots_ordered_by_start = DoctorSlot.objects.order_by("start")
        earliest_slot = all_slots_ordered_by_start.first()
        latest_slot = all_slots_ordered_by_start.last()

        filters = {
            "from": (earliest_slot.start + timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M"),
            "to": (latest_slot.start - timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M"),
        }
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name) + f"?from_date={filters['from']}&to_date={filters['to']}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response)

        self.assertTrue(len(results) > 0)
        for result in results:
            self.assertTrue(result["slot"] not in (latest_slot.id, earliest_slot.id))

    def test_get_own_detail_appointment(self):
        slots = self.populate_free_slots()
        slot = slots[0]
        appointment = Appointment.objects.create(
            patient=self.request_user,
            slot=slot,
            price="22.22",
        )
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        response = self.client.get(url)
        result = self.get_result(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cant_get_another_person_detail_appointment(self):
        slots = self.populate_free_slots()
        another_person = self.second_patient
        another_person_slot = slots[0]
        another_person_appointment = Appointment.objects.create(
            slot=another_person_slot,
            patient=another_person,
            price="22.22",
        )
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{another_person_appointment.id}"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Appointment.objects.filter(slot=another_person_slot).exists())

    def test_delete_appointment(self):
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_patch_appointment(self):
        payload = {}
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": 1})
        response = self.client.put(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.patch(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_not_late_cancel_appointment_stripe(self):
        slot = self.get_slot()
        appointment = self.get_appointment(slot)
        payment = self.get_paid_payment(appointment)

        with mock_payment_service() as mock_factory:
            full_view_name = self.view_name + "-cancel"
            url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
            payload = {}
            response = self.client.post(url, data=payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            payment_service_class = mock_factory.created_service_classes[0]
            payment_service_class.initiate_refund.assert_called_once_with(payment)

            appointment.refresh_from_db()
            self.assertTrue(appointment.status == "CANCELED")

    def test_late_cancel_appointment_stripe(self):
        slot = self.get_slot()
        appointment = self.get_appointment(slot)
        payment = self.get_paid_payment(appointment)
        slot.start = timezone.now() + timedelta(minutes=int(appointment.window_fee / 2))
        slot.save(update_fields=["start"])

        with mock_payment_service() as mock_factory:
            full_view_name = self.view_name + "-cancel"
            url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
            payload = {}
            response = self.client.post(url, data=payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            payment_service_class = mock_factory.created_service_classes[0]
            payment_service_class.initiate_refund.assert_called_once_with(payment, appointment.percent_fee)

            appointment.refresh_from_db()
            self.assertTrue(appointment.status == "CANCELED")

    def test_late_cancel_with_manual_cancellation_fee_appointment_stripe(self):
        slot = self.get_slot()
        appointment = self.get_appointment(slot)
        payment = self.get_paid_payment(appointment)
        slot.start = timezone.now() + timedelta(minutes=int(appointment.window_fee / 2))
        slot.save(update_fields=["start"])

        with mock_payment_service() as mock_factory:
            full_view_name = self.view_name + "-cancel"
            url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
            payload = {
                "manual_cancel_fee": True
            }
            response = self.client.post(url, data=payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            payment_service_class = mock_factory.created_service_classes[0]
            try:
                payment_service_class.initiate_refund.assert_called_once_with(
                    payment,
                    appointment.percent_fee
                )
            except AssertionError as e:
                raise AssertionError(
                    "only admins are able to cancel fee, so if even in payload manual_cancel_fee = True, fee should be set"
                ) from e

            appointment.refresh_from_db()
            self.assertTrue(appointment.status == "CANCELED")


    def test_cant_cancel_not_own_appointment(self):
        slot = self.get_slot()
        another_patient = self.second_patient
        appointment = self.get_appointment(slot=slot, patient=another_patient)
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "cancel/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        appointment.refresh_from_db()
        self.assertFalse(appointment.status == "CANCELED")


    def test_cant_mark_complete_appointment(self):
        slot = self.get_slot()
        appointment = self.get_appointment(slot)
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "complete/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        appointment.refresh_from_db()
        self.assertFalse(appointment.status == "COMPLETED")


    def test_cant_mark_no_show_status(self):
        slot = self.get_slot()
        appointment = self.get_appointment(slot)
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "no-show/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AppointmentAdminUserTests(BaseClinicTestCase):
    def setUp(self):
        self.view_name = "clinic:appointment"
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

    def test_create_appointment_with_patient_in_payload_stripe(self):
        slot = self.get_slot()
        patient = self.first_patient
        payload = {

            "slot": slot.id,
            "patient": patient.id,
            "method": "STRIPE"
        }
        expected_url = "https://checkout.stripe.com/c/pay/cs_test_12345"
        provider_metadata = {
            "session_id": "cs_test_12345",
            "session_url": expected_url
        }
        full_view_name = self.view_name + "-list"
        url = reverse(full_view_name)

        with mock_payment_service(provider_metadata=provider_metadata) as mock_factory:
            response = self.client.post(url, data=payload, format="json")

            # Перевірки API
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            result = self.get_result(response)
            self.assertEqual(result["patient"], patient.id)
            self.assertEqual(result["checkout_url"], expected_url)

            # Перевірка поведінки моку
            self.assertEqual(mock_factory.call_count, 1) # service called
            payment_service_class = mock_factory.created_service_classes[0]
            payment_service_class.return_value.create_payment.assert_called_once() # method called


    def test_not_late_cancel_not_own_appointment(self):
        slot = self.get_slot()
        other_user = self.first_patient
        appointment = self.get_appointment(slot=slot, patient=other_user)
        payment = self.get_paid_payment(appointment)
        with mock_payment_service() as mock_factory:
            full_view_name = self.view_name + "-cancel"
            url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
            payload = {}
            response = self.client.post(url, data=payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            payment_service_class = mock_factory.created_service_classes[0]
            payment_service_class.initiate_refund.assert_called_once_with(payment)

            appointment.refresh_from_db()
            self.assertTrue(appointment.status == "CANCELED")

    def test_late_cancel_not_own_appointment(self):
        slot = self.get_slot()
        other_user = self.first_patient
        appointment = self.get_appointment(slot=slot, patient=other_user)
        payment = self.get_paid_payment(appointment)
        slot.start = timezone.now() + timedelta(minutes=int(appointment.window_fee / 2))
        slot.save(update_fields=["start"])

        with mock_payment_service() as mock_factory:
            full_view_name = self.view_name + "-cancel"
            url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
            payload = {}
            response = self.client.post(url, data=payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            payment_service_class = mock_factory.created_service_classes[0]
            payment_service_class.initiate_refund.assert_called_once_with(payment, appointment.percent_fee)

            appointment.refresh_from_db()
            self.assertTrue(appointment.status == "CANCELED")

    def test_late_cancel_with_manual_cancellation_fee_not_own_appointment(self):
        slot = self.get_slot()
        other_user = self.first_patient
        appointment = self.get_appointment(slot=slot, patient=other_user)
        payment = self.get_paid_payment(appointment)
        slot.start = timezone.now() + timedelta(minutes=int(appointment.window_fee / 2))
        slot.save(update_fields=["start"])

        with mock_payment_service() as mock_factory:
            full_view_name = self.view_name + "-cancel"
            url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
            payload = {
                "manual_cancel_fee": True
            }
            response = self.client.post(url, data=payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            payment_service_class = mock_factory.created_service_classes[0]
            payment_service_class.initiate_refund.assert_called_once_with(payment)

            appointment.refresh_from_db()
            self.assertTrue(appointment.status == "CANCELED")

    def test_try_mark_complete_not_started_appointment(self):
        slot = self.get_slot()
        appointment = self.get_appointment(slot)
        self.get_paid_payment(appointment)
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "complete/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        result = self.get_result(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        appointment.refresh_from_db()
        self.assertTrue(appointment.status == "BOOKED")

    def test_mark_complete_started_appointment(self):
        slot = self.get_slot()
        appointment = self.get_appointment(slot)
        self.get_paid_payment(appointment)
        slot.start = timezone.now() - timedelta(minutes=1)
        slot.save(update_fields=["start"])
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "complete/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        result = self.get_result(response)
        print(result)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment.refresh_from_db()
        self.assertTrue(appointment.status == "COMPLETED")

    def test_mark_complete_not_booked_appointment(self):
        slot = self.get_slot()
        appointment = self.get_appointment(slot)
        self.get_paid_payment(appointment)
        appointment.status = "CANCELED"
        appointment.save(update_fields=["status"])

        slot.start = timezone.now() - timedelta(minutes=1)
        slot.save(update_fields=["start"])
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "complete/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        result = self.get_result(response)
        print(result)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        appointment.refresh_from_db()
        self.assertFalse(appointment.status == "COMPLETED")

    def test_mark_no_show_status(self):
        slot = self.get_slot()
        appointment = self.get_appointment(slot)
        full_view_name = self.view_name + "-detail"
        url = reverse(full_view_name, kwargs={"pk": f"{appointment.id}"})
        full_url = url + "no-show/"
        payload = {}
        response = self.client.post(full_url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appointment.refresh_from_db()
        self.assertTrue(appointment.status == "NO_SHOW")