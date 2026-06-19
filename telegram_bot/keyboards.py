from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# main_menu_keyboard = InlineKeyboardMarkup(
#     inline_keyboard=[
#         [InlineKeyboardButton(text="doctors", callback_data="doctors_data"),],
#         [InlineKeyboardButton(text="specializations", callback_data="specializations"),],
#     ],
#     resize_keyboard=True,
#     input_field_placeholder= "Select a menu item"
# )


register_required_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="register in clinic", callback_data="register_in_clinic"),
            #InlineKeyboardButton(text="add telegram account", callback_data="add_telegram_account"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder= "Select a menu item"
)


main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="doctors")],
        [KeyboardButton(text="specializations"),],
    ],
    resize_keyboard=True,
    input_field_placeholder= "Select a menu item"
)

# register_required_menu = ReplyKeyboardMarkup(
#     keyboard=[
#         [
#             KeyboardButton(text="register in clinic"),
#             KeyboardButton(text="add telegram account"),
#         ],
#     ],
#     resize_keyboard=True,
#     input_field_placeholder= "Select a menu item"
# )