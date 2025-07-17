from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_connection
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_fight(message: types.Message):
    """Обрабатывает команду /fight: начинает бой с врагом."""
    user_id = message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    
    # Получение характеристик игрока
    c.execute('SELECT health, damage, defense FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    if not player:
        await message.answer("Вы не зарегистрированы. Используйте /start.")
        conn.close()
        return
    player_health, player_damage, player_defense = player
    
    # Получение характеристик врага (Гоблин для MVP)
    c.execute('SELECT name, health, damage, defense FROM enemies WHERE enemy_id = ?', (1,))
    enemy = c.fetchone()
    if not enemy:
        await message.answer("Враг не найден. Попробуйте позже.")
        conn.close()
        return
    enemy_name, enemy_health, enemy_damage, enemy_defense = enemy

    # Расчёт урона
    damage_to_enemy = max(1, player_damage - enemy_defense)
    damage_to_player = max(1, enemy_damage - player_defense)

    # Формирование текста боя
    fight_text = (
        f"⚔️ *Вы столкнулись с {enemy_name}!*\n"
        f"HP врага: {enemy_health}\n"
        f"Ваш HP: {player_health}\n"
        f"Что будете делать?"
    )
    
    # Создание инлайн-клавиатуры
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Атаковать", callback_data=f"fight_attack_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
        [InlineKeyboardButton(text="Сбежать", callback_data="fight_flee")]
    ])
    
    # Логирование для отладки
    logger.info(f"Начало боя для пользователя {user_id} против {enemy_name}")
    
    await message.answer(fight_text, reply_markup=keyboard, parse_mode='Markdown')
    conn.close()

async def handle_fight_action(callback: types.CallbackQuery):
    """Обрабатывает действия в бою (атака или побег)."""
    user_id = callback.from_user.id
    action = callback.data.split('_')[1]
    conn = get_db_connection()
    c = conn.cursor()
    
    # Получение текущего здоровья игрока
    c.execute('SELECT health FROM players WHERE user_id = ?', (user_id,))
    player_health = c.fetchone()
    if not player_health:
        await callback.message.answer("Вы не зарегистрированы. Используйте /start.")
        conn.close()
        await callback.answer()
        return
    player_health = player_health[0]

    if action == 'flee':
        await callback.message.answer("Вы попытались сбежать... Успех!")
        logger.info(f"Пользователь {user_id} сбежал из боя")
        conn.close()
        await callback.answer()
        return

    # Действие атаки
    enemy_health = int(callback.data.split('_')[2])
    damage_to_enemy = int(callback.data.split('_')[3])
    damage_to_player = int(callback.data.split('_')[4])

    # Обновление здоровья
    enemy_health -= damage_to_enemy
    player_health -= damage_to_player

    if enemy_health <= 0:
        # Победа игрока
        c.execute('UPDATE players SET gold = gold + 20 WHERE user_id = ?', (user_id,))
        c.execute('UPDATE players SET health = ? WHERE user_id = ?', (player_health, user_id))
        conn.commit()
        await callback.message.answer("🎉 Вы победили Гоблина! +20 золота")
        logger.info(f"Пользователь {user_id} победил Гоблина")
        conn.close()
        await callback.answer()
        return

    if player_health <= 0:
        # Поражение игрока
        c.execute('UPDATE players SET health = 50 WHERE user_id = ?', (user_id,))
        conn.commit()
        await callback.message.answer("💀 Вы побеждены! Здоровье сброшено до 50.")
        logger.info(f"Пользователь {user_id} проиграл бой")
        conn.close()
        await callback.answer()
        return

    # Продолжение боя
    c.execute('UPDATE players SET health = ? WHERE user_id = ?', (player_health, user_id))
    conn.commit()
    fight_text = (
        f"⚔️ Вы нанесли {damage_to_enemy} урона Гоблину!\n"
        f"Гоблин нанёс вам {damage_to_player} урона!\n"
        f"HP врага: {enemy_health}\n"
        f"Ваш HP: {player_health}\n"
        f"Что будете делать?"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Атаковать", callback_data=f"fight_attack_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
        [InlineKeyboardButton(text="Сбежать", callback_data="fight_flee")]
    ])
    
    # Логирование для отладки
    logger.info(f"Продолжение боя для пользователя {user_id}: HP врага {enemy_health}, HP игрока {player_health}")
    
    await callback.message.edit_text(fight_text, reply_markup=keyboard, parse_mode='Markdown')
    conn.close()
    await callback.answer()