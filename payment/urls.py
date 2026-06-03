from django.urls import path

from payment.views import webhook_view

app_name = 'payment'

urlpatterns = [
    path("webhook/", webhook_view, name="payment_webhook"),
]
