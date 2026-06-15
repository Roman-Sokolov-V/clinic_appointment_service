from celery import shared_task
from celery.utils.log import get_task_logger

from clinic.services.appointment_service import AppointmentService
import logging

logger = get_task_logger(__name__)

@shared_task
def mark_no_show():
    updated = AppointmentService.automatically_mark_no_show_appointments()
    if updated:
        logger.info("Successfully updated appointments: ", updated)
    else:
        logger.info("Not found appointments to update")

# @shared_task
# def add(x, y):
#     return x + y
#
#
# @shared_task
# def mul(x, y):
#     return x * y
#
#
# @shared_task
# def xsum(numbers):
#     return sum(numbers)


# @shared_task
# def count_specializations():
#     sp = Specialization.objects.count()
#     print("Specializations: ", sp)
#     return sp



#
# @shared_task
# def rename_widget(widget_id, name):
#     w = Specialization.objects.get(id=widget_id)
#     w.name = name
#     w.save()
#
#
# @shared_task(
#     bind=True,
#     autoretry_for=(Exception,),
#     retry_kwargs={"max_retries": 2, "countdown": 10 * 60},  # retry up to 2 times with 10 minutes between retries
# )
# def error_task(self):
#     raise Exception("Test error")
#
#
# @shared_task(
#     bind=True,
#     autoretry_for=(Exception,),
#     retry_backoff=5,  # Factor in seconds (first retry: 5s, second: 10s, third: 20s, etc.)
#     retry_jitter=False,  # Set False to disable randomization (use exact values: 5s, 10s, 20s)
#     retry_kwargs={"max_retries": 3},
# )
# def error_backoff_test(self):
#     raise Exception("Test error")