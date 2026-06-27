from aiogram.filters.callback_data import CallbackData


class SpecClick(CallbackData, prefix="spec"):
    spec_id: int
    spec_name: str = ""