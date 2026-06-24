from aiogram.filters.callback_data import CallbackData


class SlotClick(CallbackData, prefix="slot"):
    slot_id: int
    doctor_id: int

class PaymentMethodClick(CallbackData, prefix="pay_method"):
    slot_id: int
    method: str