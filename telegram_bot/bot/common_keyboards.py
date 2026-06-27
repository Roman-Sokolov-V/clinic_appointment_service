from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from telegram_bot.bot.common_callback_data_factories import PaginationClickSpecializations, PaginationClickDoctors, \
    PaginationClickMyAppointments

main_menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="doctors", callback_data=PaginationClickDoctors().pack()),],
        [InlineKeyboardButton(text="specializations", callback_data=PaginationClickSpecializations().pack()),],
        [InlineKeyboardButton(text="my appointments", callback_data=PaginationClickMyAppointments().pack()),],
    ],
    resize_keyboard=True,
    input_field_placeholder= "Select a menu item"
)


def add_back_to_main_menu_button(builder: InlineKeyboardBuilder, callback_data: str = "main_menu_keyboard") -> InlineKeyboardBuilder:
    """Adds the 'Main menu' button to a separate line at the very end of the keyboard."""
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back to main menu",
            callback_data=callback_data
        )
    )
    return builder

def add_next_button(builder: InlineKeyboardBuilder, callback_data: str, text: str = "Show next ⏭️")-> InlineKeyboardBuilder:
    builder.row(
        InlineKeyboardButton(
            text=text,
            callback_data=callback_data
        )
    )
    return builder
