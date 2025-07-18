import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import API_TOKEN
from player import handle_start, handle_profile
from combat import handle_fight, handle_fight_action
from inventory import handle_inventory, handle_use_item, handle_inventory_page
from shop import handle_shop, handle_buy
from feedback import handle_feedback, process_feedback, FeedbackStates
from database import init_db
from utils import get_main_keyboard
import logging
import aiogram

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Проверка версии aiogram
logger.info(f"Используемая версия aiogram: {aiogram.__version__}")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot)  # Передаём bot в Dispatcher

# Обработчик команды /help
async def handle_help(message: types.Message):
    """Показывает список доступных команд."""
    help_text = (
        "📜 *Список команд:*\n"
        "👤 *Профиль* - Показать характеристики персонажа\n"
        "🎒 *Инвентарь* - Показать и использовать предметы\n"
        "🏪 *Магазин* - Купить предметы\n"
        "⚔️ *Бой* - Сразиться с врагом\n"
        "📝 *Feedback* - Оставить отзыв\n"
        "❓ *Помощь* - Показать это сообщение"
    )
    await message.answer(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

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
    dp.message.register(handle_help, Command('help'))
    dp.message.register(handle_help, F.text == "Помощь")
    dp.message.register(handle_feedback, Command('feedback'))
    dp.message.register(handle_feedback, F.text == "Feedback")
    dp.message.register(process_feedback, FeedbackStates.waiting_for_feedback)
    
    # Обработчики callback'ов для инлайн-кнопок
    dp.callback_query.register(handle_fight_action, F.data.startswith('fight_'))
    dp.callback_query.register(handle_buy, F.data.startswith('buy_'))
    dp.callback_query.register(handle_use_item, F.data.startswith('use_item_'))
    dp.callback_query.register(handle_inventory_page, F.data.startswith('inv_page_'))
    dp.callback_query.register(handle_profile, F.data == 'refresh_profile')
    
    # Логирование регистрации обработчиков
    logger.info("Все обработчики команд и callback'ов зарегистрированы")

@dp.update()
async def log_update(update: types.Update):
    logger.info(f"Получено обновление: {update}")
    return False

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