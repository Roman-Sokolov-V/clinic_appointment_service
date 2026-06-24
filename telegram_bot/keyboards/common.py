from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def add_main_menu_button(builder: InlineKeyboardBuilder, callback_data: str = "main_menu_keyboard") -> InlineKeyboardBuilder:
    """Adds the 'Main menu' button to a separate line at the very end of the keyboard."""
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Back to main menu",
            callback_data=callback_data
        )
    )
    return builder

def add_next_button(builder: InlineKeyboardBuilder, callback_data: str, obj: str = "") -> InlineKeyboardBuilder:
    builder.row(
        InlineKeyboardButton(
            text=f"Show next {obj} ⏭️",
            callback_data=callback_data
        )
    )
    return builder

# def add_prev_menu_button(builder: InlineKeyboardBuilder, callback_data: str = "prev_menu") -> InlineKeyboardBuilder:
#     builder.row(
#         InlineKeyboardButton(
#             text=f""
#         )

)