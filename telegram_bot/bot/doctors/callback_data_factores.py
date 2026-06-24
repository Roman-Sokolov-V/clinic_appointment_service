from aiogram.filters.callback_data import CallbackData


class DocClick(CallbackData, prefix="doc"):
    doctor_id: int

