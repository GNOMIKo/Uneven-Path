import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import API_TOKEN
from player import handle_start, handle_profile
from combat import handle_fight, handle_fight_action
from inventory import handle_inventory
from shop import handle_shop, handle_buy_item
from database import init_db
import logging
import aiogram

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка версии aiogram
logger.info(f"Используемая версия aiogram: {aiogram.__version__}")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создание постоянной клавиатуры внизу чата
def get_main_keyboard():
    """Возвращает ReplyKeyboardMarkup с человеко-читаемыми названиями команд."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Профиль"), KeyboardButton(text="Инвентарь")],
            [KeyboardButton(text="Магазин"), KeyboardButton(text="Бой")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

# Регистрация обработчиков
def register_handlers():
    """Регистрирует обработчики команд и callback'ов."""
    # Обработчики команд
    dp.message.register(handle_start, Command('start'))
    dp.message.register(handle_profile, Command('profile'))
    dp.message.register(handle_profile, F.text == "Профиль")
    dp.message.register(handle_inventory, Command('inventory'))
    dp.message.register(handle_inventory, F.text == "Инвентарь")
    dp.message.register(handle_shop, Command('shop'))
    dp.message.register(handle_shop, F.text == "Магазин")
    dp.message.register(handle_fight, Command('fight'))
    dp.message.register(handle_fight, F.text == "Бой")
    
    # Обработчики callback'ов для инлайн-кнопок
    dp.callback_query.register(handle_fight_action, F.data.startswith('fight_'))
    dp.callback_query.register(handle_buy_item, F.data.startswith('buy_'))
    dp.callback_query.register(handle_inventory, F.data == 'open_inventory')
    
    # Логирование регистрации обработчиков
    logger.info("Все обработчики команд и callback'ов зарегистрированы")

async def main():
    # Инициализация базы данных
    init_db()
    # Регистрация обработчиков
    register_handlers()
    # Логирование старта бота
    logger.info("Бот запускается...")
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())