import stripe

from config.settings import STRIPE_SECRET_KEY
from payment.models import Payment
from payment.payment_services.base import AppointmentPayment

stripe.api_key = STRIPE_SECRET_KEY

class StripePayment(AppointmentPayment):
    """
    Concrete implementation of the AppointmentPayment service utilizing the Stripe payment gateway.
    """

    def _generate_gateway_transaction(self, payment: Payment):
        """
        Invoke the external Stripe Checkout API to generate a secure payment session.

        Maps the local payment metadata to Stripe's `line_items`. It appends the
        unique internal database payment tracking identifier (`?payment_id=<id>`)
        as a URL query parameter to both the `success_url` and `cancel_url`.

        This URL modification allows whichever client landing on those pages (Web/Mobile)
        to intercept the query token and execute standard background API verification loops
        against our backend.

        :param payment: Payment instance previously persisted locally.
        :return: stripe.checkout.Session object returned directly from Stripe's Python SDK
                 which implements `.id` and `.url` interfaces.
        """
        print("start create session")
        query_params = f"?payment_id={payment.id}"
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            success_url=self.success_url + query_params,
            cancel_url=self.cancel_url + query_params,
            expires_at=self.expires_at,
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


