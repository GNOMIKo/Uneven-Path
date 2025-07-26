import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import in_fight, API_TOKEN  # Глобальное состояние боя перенесено в config.py
from player import handle_start, handle_profile
from combat import handle_fight, handle_fight_action
from inventory import handle_inventory, handle_use_item, handle_inventory_page, handle_potions, handle_potions_page, handle_show_inventory, handle_use_potion
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
dp = Dispatcher(bot=bot)

# Обработчик команды /help
async def handle_help(message: types.Message):
    """Показывает список доступных команд."""
    if message.from_user.id not in in_fight:
        help_text = (
            "📜 *Список команд:*\n"
            "👤 *Профиль* - Показать характеристики персонажа\n"
            "🧪 *Зелья* - Показать и использовать зелья\n"
            "🏪 *Магазин* - Купить предметы\n"
            "⚔️ *Бой* - Сразиться с врагом\n"
            "📝 *Feedback* - Оставить отзыв\n"
            "❓ *Помощь* - Показать это сообщение"
        )
        await message.answer(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())
    else:
        await message.answer("Вы сейчас в бою! Завершите бой или используйте зелья.", reply_markup=None)

# Регистрация обработчиков
def register_handlers():
    """Регистрирует обработчики команд и callback'ов."""
    dp.message.register(handle_start, Command('start'))
    dp.message.register(handle_profile, Command('profile'))
    dp.message.register(handle_profile, F.text == "Профиль")
    dp.message.register(handle_potions, Command('potions'))
    dp.message.register(handle_potions, F.text == "Зелья")
    dp.message.register(handle_shop, Command('shop'))
    dp.message.register(handle_shop, F.text == "Магазин")
    dp.message.register(handle_fight, Command('fight'))
    dp.message.register(handle_fight, F.text == "Бой")
    dp.message.register(handle_help, Command('help'))
    dp.message.register(handle_help, F.text == "Помощь")
    dp.message.register(handle_feedback, Command('feedback'))
    dp.message.register(handle_feedback, F.text == "Feedback")
    dp.message.register(handle_use_potion, Command('use'))
    dp.message.register(process_feedback, FeedbackStates.waiting_for_feedback)
    
    dp.callback_query.register(handle_fight_action, F.data.startswith('fight_'))
    dp.callback_query.register(handle_buy, F.data.startswith('buy_'))
    dp.callback_query.register(handle_use_item, F.data.startswith('use_item_'))
    dp.callback_query.register(handle_inventory_page, F.data.startswith('inv_page_'))
    dp.callback_query.register(handle_potions_page, F.data.startswith('potion_page_'))
    dp.callback_query.register(handle_show_inventory, F.data.startswith('show_inventory_'))
    dp.callback_query.register(handle_profile, F.data == 'refresh_profile')
    
    logger.info("Все обработчики команд и callback'ов зарегистрированы")

@dp.update()
async def log_update(update: types.Update):
    logger.info(f"Получено обновление: {update}")
    if update.message:
        user_id = update.message.from_user.id
        if user_id in in_fight and update.message.text not in ['/start', '/help', 'Зелья', '/potions']:
            await update.message.answer("Вы сейчас в бою! Завершите бой или используйте зелья.", reply_markup=None)
            return False
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        callback_data = update.callback_query.data
        if user_id in in_fight and not (callback_data.startswith('fight_') or callback_data.startswith('use_item_') or callback_data.startswith('potion_page_')):
            await update.callback_query.message.edit_text("Вы сейчас в бою! Используйте зелья или завершите бой.", reply_markup=None)
            await update.callback_query.answer()
            return False
    return False

async def main():
    init_db()
    register_handlers()
    logger.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())