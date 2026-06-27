from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

reg_log_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="register in clinic", callback_data="register_in_clinic"),
            InlineKeyboardButton(text="login in clinic", callback_data="login_in_clinic"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder= "Select a menu item"
)