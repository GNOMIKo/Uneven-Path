from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    """Возвращает ReplyKeyboardMarkup с человеко-читаемыми названиями команд."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Профиль"), KeyboardButton(text="Инвентарь")],
            [KeyboardButton(text="Магазин"), KeyboardButton(text="Бой")],
            [KeyboardButton(text="Помощь")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard