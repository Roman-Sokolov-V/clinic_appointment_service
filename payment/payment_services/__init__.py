from rest_framework.exceptions import ValidationError

from payment.payment_services.stripe_service import StripePayment


def get_payment_service(payment_method: str):
    if payment_method.upper() == 'STRIPE':
        return StripePayment
    # elif payment_method.upper() == 'CASH':
    #     return CashPayment
    else:
        raise ValidationError(
            {
                "payment_method": f"Payment method {payment_method} is not supported"
            },
        )
