from django.urls import path

from payment.views import stripe_webhook_view, success_view, cancel_view

app_name = 'payment'

urlpatterns = [
    path("webhook/", stripe_webhook_view, name="payment_webhook"),
    path("success/", success_view, name="success_payment"),
    path("cancel/", cancel_view, name="cancel_payment"),
]
