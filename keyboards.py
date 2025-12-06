from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import get_categories

# Admin menu
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Kategoriya qo‘shish")],
        [KeyboardButton(text="Kino qo‘shish")],
    ],
    resize_keyboard=True
)

def categories_keyboard():
    kb = InlineKeyboardBuilder()

    for cid, name in get_categories():
        kb.button(text=name, callback_data=f"cat_{cid}")

    kb.adjust(1)
    return kb.as_markup()
