import stripe

from config.settings import STRIPE_SECRET_KEY
from payment.payment_services.base import AppointmentPayment

stripe.api_key = STRIPE_SECRET_KEY

class StripePayment(AppointmentPayment):
    def create_payment_session(self):
        """
        Creates a Stripe Payment Session for payment.
        :return StripePaymentSession
        """
        print("start create session")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            success_url="http://localhost:8000/success/",
            cancel_url="http://localhost:8000/cancel/",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Appointment id: {self.appointment.id} ",
                            "description": self.payment_type,
                        },
                        "unit_amount": self.amount,
                    },
                    "quantity": 1,
                }
            ],
        )
        return session


