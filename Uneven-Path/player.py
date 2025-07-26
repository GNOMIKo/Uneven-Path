from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_connection
from utils import get_main_keyboard
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_start(message: types.Message):
    """Обрабатывает команду /start: регистрирует нового игрока или приветствует вернувшегося."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
    if not c.fetchone():
        # Регистрация нового игрока
        c.execute('INSERT INTO players (user_id, username, health, damage, defense, gold) VALUES (?, ?, ?, ?, ?, ?)',
                  (user_id, username, 100, 10, 5, 50))
        conn.commit()
        await message.answer(
            f"Добро пожаловать, {username}! Ты теперь искатель приключений. Используй кнопки ниже для навигации.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            f"С возвращением, {username}! Готов к приключениям? Используй кнопки ниже.",
            reply_markup=get_main_keyboard()
        )
    conn.close()

async def handle_profile(message: types.Message):
    """Обрабатывает команду /profile: показывает характеристики игрока."""
    user_id = message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT username, health, damage, defense, gold FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    if player:
        username, health, damage, defense, gold = player
        profile_text = (
            f"👤 *Профиль: {username}*\n"
            f"❤️ Здоровье: {health}\n"
            f"⚔️ Урон: {damage}\n"
            f"🛡️ Защита: {defense}\n"
            f"💰 Золото: {gold}"
        )
        # Добавление кнопок "Обновить" и "Инвентарь"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_profile"),
                InlineKeyboardButton(text="🎒 Инвентарь", callback_data=f"show_inventory_{user_id}")
            ]
        ])
        await message.answer(
            profile_text,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        logger.info(f"Показал профиль пользователю {user_id}")
    else:
        await message.answer("Вы не зарегистрированы. Используйте /start.", reply_markup=get_main_keyboard())
    conn.close()