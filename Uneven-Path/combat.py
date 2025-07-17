from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_connection
from utils import get_main_keyboard
import logging
import random

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
        await message.answer("Вы не зарегистрированы. Используйте /start.", reply_markup=get_main_keyboard())
        conn.close()
        return
    player_health, player_base_damage, player_base_defense = player
    
    # Получение активных эффектов игрока
    c.execute('SELECT effect_type, effect_value, rounds_left FROM active_effects WHERE user_id = ?', (user_id,))
    effects = c.fetchall()
    player_damage = player_base_damage
    player_defense = player_base_defense
    for effect in effects:
        if effect['effect_type'] == 'damage_buff':
            player_damage += effect['effect_value']
        elif effect['effect_type'] == 'defense_buff':
            player_defense += effect['effect_value']
    
    # Выбор случайного врага
    c.execute('SELECT enemy_id, name, health, damage, defense FROM enemies')
    enemies = c.fetchall()
    if not enemies:
        await message.answer("Враги не найдены. Попробуйте позже.", reply_markup=get_main_keyboard())
        conn.close()
        return
    enemy = random.choice(enemies)
    enemy_id, enemy_name, enemy_health, enemy_damage, enemy_defense = enemy
    
    # Расчёт урона
    damage_to_enemy = max(1, player_damage - enemy_defense)
    damage_to_player = max(1, enemy_damage - player_defense)
    
    # Формирование текста боя с подробными характеристиками
    effects_text = "\n".join([f"🔮 {effect['effect_type'].replace('_buff', '')}: +{effect['effect_value']} ({effect['rounds_left']} раундов)" for effect in effects]) if effects else "Нет активных эффектов"
    fight_text = (
        f"⚔️ *Бой с {enemy_name}!*\n\n"
        f"👤 *Ваши характеристики:*\n"
        f"❤️ Здоровье: {player_health}\n"
        f"⚔️ Урон: {player_damage}\n"
        f"🛡️ Защита: {player_defense}\n"
        f"🔮 Эффекты:\n{effects_text}\n\n"
        f"👹 *Характеристики {enemy_name}:*\n"
        f"❤️ Здоровье: {enemy_health}\n"
        f"⚔️ Урон: {enemy_damage}\n"
        f"🛡️ Защита: {enemy_defense}\n\n"
        f"Что будете делать?"
    )
    
    # Создание инлайн-клавиатуры
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Атаковать", callback_data=f"fight_attack_{enemy_id}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
        [InlineKeyboardButton(text="Использовать зелье", callback_data=f"fight_use_potion_{enemy_id}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
        [InlineKeyboardButton(text="Сбежать", callback_data="fight_flee")]
    ])
    
    # Логирование для отладки
    logger.info(f"Начало боя для пользователя {user_id} против {enemy_name}, callback_data: fight_use_potion_{enemy_id}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")
    
    await message.answer(fight_text, reply_markup=keyboard, parse_mode='Markdown')
    conn.close()

async def handle_fight_action(callback: types.CallbackQuery):
    """Обрабатывает действия в бою (атака, использование зелья, побег)."""
    user_id = callback.from_user.id
    logger.info(f"Получен callback для пользователя {user_id}: {callback.data}")
    
    # Проверка callback_data
    if not callback.data.startswith('fight_'):
        logger.error(f"Некорректный callback_data, ожидается префикс 'fight_': {callback.data}")
        await callback.message.edit_text("Ошибка: неверные данные действия. Попробуйте снова.", reply_markup=None)
        await callback.answer()
        return
    
    # Парсинг callback_data
    try:
        parts = callback.data.split('_')
        action = parts[1]
        logger.debug(f"Извлечённое действие: {action}, полные части: {parts}")
    except IndexError:
        logger.error(f"Ошибка парсинга callback_data: {callback.data}")
        await callback.message.edit_text("Ошибка: неверные данные действия. Попробуйте снова.", reply_markup=None)
        await callback.answer()
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Проверка существования таблицы inventory
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
    if not c.fetchone():
        logger.error("Таблица inventory не существует в базе данных")
        await callback.message.edit_text("Ошибка: база данных повреждена. Обратитесь к администратору.", reply_markup=None)
        conn.close()
        await callback.answer()
        return
    
    # Получение характеристик игрока
    c.execute('SELECT health, damage, defense FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    if not player:
        await callback.message.edit_text("Вы не зарегистрированы. Используйте /start.", reply_markup=None)
        conn.close()
        await callback.answer()
        return
    player_health, player_base_damage, player_base_defense = player
    
    # Получение активных эффектов
    c.execute('SELECT effect_type, effect_value, rounds_left FROM active_effects WHERE user_id = ?', (user_id,))
    effects = c.fetchall()
    player_damage = player_base_damage
    player_defense = player_base_defense
    for effect in effects:
        if effect['effect_type'] == 'damage_buff':
            player_damage += effect['effect_value']
        elif effect['effect_type'] == 'defense_buff':
            player_defense += effect['effect_value']
    
    if action == 'flee':
        logger.debug(f"Пользователь {user_id} выбрал действие: flee")
        # Обновление эффектов (уменьшение раундов)
        for effect in effects:
            rounds_left = effect['rounds_left'] - 1
            if rounds_left <= 0:
                c.execute('DELETE FROM active_effects WHERE user_id = ? AND effect_type = ?', (user_id, effect['effect_type']))
            else:
                c.execute('UPDATE active_effects SET rounds_left = ? WHERE user_id = ? AND effect_type = ?',
                          (rounds_left, user_id, effect['effect_type']))
        conn.commit()
        await callback.message.edit_text("Вы попытались сбежать... Успех!", reply_markup=None)
        logger.info(f"Пользователь {user_id} сбежал из боя")
        conn.close()
        await callback.answer()
        return
    
    if action == 'use_potion':
        logger.debug(f"Пользователь {user_id} выбрал действие: use_potion")
        # Извлечение параметров из callback.data
        try:
            enemy_id = int(parts[2])
            enemy_health = int(parts[3])
            damage_to_enemy = int(parts[4])
            damage_to_player = int(parts[5])
            logger.debug(f"Параметры use_potion: enemy_id={enemy_id}, enemy_health={enemy_health}, damage_to_enemy={damage_to_enemy}, damage_to_player={damage_to_player}")
        except (IndexError, ValueError) as e:
            logger.error(f"Ошибка разбора callback.data для use_potion: {callback.data}, ошибка: {e}")
            await callback.message.edit_text("Ошибка. Попробуйте снова.", reply_markup=None)
            conn.close()
            await callback.answer()
            return
        
        # Получение всех предметов из инвентаря для отладки
        c.execute('SELECT id, item_name, item_type, item_value FROM inventory WHERE user_id = ?', (user_id,))
        all_items = c.fetchall()
        logger.debug(f"Все предметы в инвентаре пользователя {user_id}: {[(p['id'], p['item_name'], p['item_type'], p['item_value']) for p in all_items]}")
        
        # Получение зелий из инвентаря
        c.execute('SELECT id, item_name, item_type, item_value FROM inventory WHERE user_id = ? AND LOWER(item_type) IN (?, ?)',
                  (user_id, 'potion', 'buff_potion'))
        potions = c.fetchall()
        logger.debug(f"Зелья пользователя {user_id}: {[(p['id'], p['item_name'], p['item_type'], p['item_value']) for p in potions]}")
        
        if not potions:
            await callback.message.edit_text("У вас нет зелий!", reply_markup=None)
            logger.info(f"У пользователя {user_id} нет зелий в инвентаре")
            conn.close()
            await callback.answer()
            return
        
        # Создание инлайн-клавиатуры для выбора зелья
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for potion in potions:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{potion['item_name']} (+{potion['item_value']})",
                    callback_data=f"fight_apply_potion_{potion['id']}_{enemy_id}_{enemy_health}_{damage_to_enemy}_{damage_to_player}"
                )
            ])
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text="Назад",
                callback_data=f"fight_back_{enemy_id}_{enemy_health}_{damage_to_enemy}_{damage_to_player}"
            )
        ])
        
        try:
            await callback.message.edit_text("Выберите зелье:", reply_markup=keyboard, parse_mode='Markdown')
            logger.info(f"Показан список зелий пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения для списка зелий: {e}")
            await callback.message.answer("Ошибка при отображении зелий. Попробуйте снова.", reply_markup=None)
        
        conn.close()
        await callback.answer()
        return
    
    if action == 'back':
        logger.debug(f"Пользователь {user_id} выбрал действие: back")
        # Извлечение параметров
        try:
            enemy_id = int(parts[2])
            enemy_health = int(parts[3])
            damage_to_enemy = int(parts[4])
            damage_to_player = int(parts[5])
        except (IndexError, ValueError) as e:
            logger.error(f"Ошибка разбора callback.data для back: {callback.data}, ошибка: {e}")
            await callback.message.edit_text("Ошибка. Попробуйте снова.", reply_markup=None)
            conn.close()
            await callback.answer()
            return
        
        # Получение характеристик врага
        c.execute('SELECT name, health, damage, defense FROM enemies WHERE enemy_id = ?', (enemy_id,))
        enemy = c.fetchone()
        if not enemy:
            await callback.message.edit_text("Враг не найден. Попробуйте позже.", reply_markup=None)
            conn.close()
            await callback.answer()
            return
        enemy_name, _, enemy_damage, enemy_defense = enemy
        
        # Формирование текста боя
        effects_text = "\n".join([f"🔮 {effect['effect_type'].replace('_buff', '')}: +{effect['effect_value']} ({effect['rounds_left']} раундов)" for effect in effects]) if effects else "Нет активных эффектов"
        fight_text = (
            f"⚔️ *Бой с {enemy_name}!*\n\n"
            f"👤 *Ваши характеристики:*\n"
            f"❤️ Здоровье: {player_health}\n"
            f"⚔️ Урон: {player_damage}\n"
            f"🛡️ Защита: {player_defense}\n"
            f"🔮 Эффекты:\n{effects_text}\n\n"
            f"👹 *Характеристики {enemy_name}:*\n"
            f"❤️ Здоровье: {enemy_health}\n"
            f"⚔️ Урон: {enemy_damage}\n"
            f"🛡️ Защита: {enemy_defense}\n\n"
            f"Что будете делать?"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Атаковать", callback_data=f"fight_attack_{enemy_id}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
            [InlineKeyboardButton(text="Использовать зелье", callback_data=f"fight_use_potion_{enemy_id}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
            [InlineKeyboardButton(text="Сбежать", callback_data="fight_flee")]
        ])
        
        await callback.message.edit_text(fight_text, reply_markup=keyboard, parse_mode='Markdown')
        conn.close()
        await callback.answer()
        return
    
    if action == 'apply_potion':
        logger.debug(f"Пользователь {user_id} выбрал действие: apply_potion")
        # Извлечение параметров
        try:
            potion_id = int(parts[3])
            enemy_id = int(parts[4])
            enemy_health = int(parts[5])
            damage_to_enemy = int(parts[6])
            damage_to_player = int(parts[7])
        except (IndexError, ValueError) as e:
            logger.error(f"Ошибка разбора callback.data для apply_potion: {callback.data}, ошибка: {e}")
            await callback.message.edit_text("Ошибка. Попробуйте снова.", reply_markup=None)
            conn.close()
            await callback.answer()
            return
        
        # Получение зелья
        c.execute('SELECT id, item_name, item_type, item_value FROM inventory WHERE id = ? AND user_id = ?', (potion_id, user_id))
        potion = c.fetchone()
        if not potion:
            await callback.message.answer("Зелье не найдено.", reply_markup=None)
            logger.error(f"Зелье с ID {potion_id} не найдено для пользователя {user_id}")
            conn.close()
            await callback.answer()
            return
        item_name, item_type, item_value = potion
        
        # Применение зелья
        if item_type.lower() == 'potion':
            new_health = min(player_health + item_value, 100)
            c.execute('UPDATE players SET health = ? WHERE user_id = ?', (new_health, user_id))
            c.execute('DELETE FROM inventory WHERE id = ?', (potion_id,))
            await callback.message.answer(f"Вы использовали {item_name}! ❤️ Здоровье восстановлено до {new_health}.")
            logger.info(f"Пользователь {user_id} использовал {item_name} в бою, здоровье: {new_health}")
        elif item_type.lower() == 'buff_potion':
            effect_type = 'damage_buff' if 'Strength' in item_name else 'defense_buff'
            c.execute('INSERT OR REPLACE INTO active_effects (user_id, effect_type, effect_value, rounds_left) VALUES (?, ?, ?, ?)',
                      (user_id, effect_type, item_value, 3))
            c.execute('DELETE FROM inventory WHERE id = ?', (potion_id,))
            await callback.message.answer(f"Вы использовали {item_name}! 🔮 Эффект применён на 3 раунда.")
            logger.info(f"Пользователь {user_id} использовал {item_name} в бою, эффект: {effect_type}, значение: {item_value}")
        
        conn.commit()
        
        # Возврат к бою
        c.execute('SELECT name, damage, defense FROM enemies WHERE enemy_id = ?', (enemy_id,))
        enemy = c.fetchone()
        if not enemy:
            await callback.message.edit_text("Враг не найден. Попробуйте позже.", reply_markup=None)
            conn.close()
            await callback.answer()
            return
        enemy_name, enemy_damage, enemy_defense = enemy
        
        # Обновление характеристик игрока после использования зелья
        c.execute('SELECT health FROM players WHERE user_id = ?', (user_id,))
        player_health = c.fetchone()[0]
        c.execute('SELECT effect_type, effect_value, rounds_left FROM active_effects WHERE user_id = ?', (user_id,))
        effects = c.fetchall()
        player_damage = player_base_damage
        player_defense = player_base_defense
        for effect in effects:
            if effect['effect_type'] == 'damage_buff':
                player_damage += effect['effect_value']
            elif effect['effect_type'] == 'defense_buff':
                player_defense += effect['effect_value']
        
        damage_to_enemy = max(1, player_damage - enemy_defense)
        damage_to_player = max(1, enemy_damage - player_defense)
        
        effects_text = "\n".join([f"🔮 {effect['effect_type'].replace('_buff', '')}: +{effect['effect_value']} ({effect['rounds_left']} раундов)" for effect in effects]) if effects else "Нет активных эффектов"
        fight_text = (
            f"⚔️ *Бой с {enemy_name}!*\n\n"
            f"👤 *Ваши характеристики:*\n"
            f"❤️ Здоровье: {player_health}\n"
            f"⚔️ Урон: {player_damage}\n"
            f"🛡️ Защита: {player_defense}\n"
            f"🔮 Эффекты:\n{effects_text}\n\n"
            f"👹 *Характеристики {enemy_name}:*\n"
            f"❤️ Здоровье: {enemy_health}\n"
            f"⚔️ Урон: {enemy_damage}\n"
            f"🛡️ Защита: {enemy_defense}\n\n"
            f"Что будете делать?"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Атаковать", callback_data=f"fight_attack_{enemy_id}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
            [InlineKeyboardButton(text="Использовать зелье", callback_data=f"fight_use_potion_{enemy_id}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
            [InlineKeyboardButton(text="Сбежать", callback_data="fight_flee")]
        ])
        
        await callback.message.edit_text(fight_text, reply_markup=keyboard, parse_mode='Markdown')
        conn.close()
        await callback.answer()
        return
    
    if action == 'attack':
        logger.debug(f"Пользователь {user_id} выбрал действие: attack")
        # Извлечение параметров
        try:
            enemy_id = int(parts[2])
            enemy_health = int(parts[3])
            damage_to_enemy = int(parts[4])
            damage_to_player = int(parts[5])
        except (IndexError, ValueError) as e:
            logger.error(f"Ошибка разбора callback.data для attack: {callback.data}, ошибка: {e}")
            await callback.message.edit_text("Ошибка. Попробуйте снова.", reply_markup=None)
            conn.close()
            await callback.answer()
            return
    
        # Получение характеристик врага
        c.execute('SELECT name, damage, defense FROM enemies WHERE enemy_id = ?', (enemy_id,))
        enemy = c.fetchone()
        if not enemy:
            await callback.message.edit_text("Враг не найден. Попробуйте позже.", reply_markup=None)
            conn.close()
            await callback.answer()
            return
        enemy_name, enemy_damage, enemy_defense = enemy
        
        # Обновление здоровья
        enemy_health -= damage_to_enemy
        player_health -= damage_to_player
        
        # Обновление эффектов (уменьшение раундов)
        for effect in effects:
            rounds_left = effect['rounds_left'] - 1
            if rounds_left <= 0:
                c.execute('DELETE FROM active_effects WHERE user_id = ? AND effect_type = ?', (user_id, effect['effect_type']))
            else:
                c.execute('UPDATE active_effects SET rounds_left = ? WHERE user_id = ? AND effect_type = ?',
                          (rounds_left, user_id, effect['effect_type']))
        
        if enemy_health <= 0:
            # Победа игрока
            c.execute('UPDATE players SET gold = gold + 20 WHERE user_id = ?', (user_id,))
            c.execute('UPDATE players SET health = ? WHERE user_id = ?', (player_health, user_id))
            conn.commit()
            await callback.message.edit_text(f"🎉 Вы победили {enemy_name}! +20 золота", reply_markup=None)
            logger.info(f"Пользователь {user_id} победил {enemy_name}")
            conn.close()
            await callback.answer()
            return
        
        if player_health <= 0:
            # Поражение игрока
            c.execute('DELETE FROM active_effects WHERE user_id = ?', (user_id,))
            c.execute('UPDATE players SET health = 50 WHERE user_id = ?', (user_id,))
            conn.commit()
            await callback.message.edit_text("💀 Вы побеждены! Здоровье сброшено до 50.", reply_markup=None)
            logger.info(f"Пользователь {user_id} проиграл бой")
            conn.close()
            await callback.answer()
            return
        
        # Продолжение боя
        c.execute('UPDATE players SET health = ? WHERE user_id = ?', (player_health, user_id))
        conn.commit()
        
        # Обновление характеристик игрока
        c.execute('SELECT effect_type, effect_value, rounds_left FROM active_effects WHERE user_id = ?', (user_id,))
        effects = c.fetchall()
        player_damage = player_base_damage
        player_defense = player_base_defense
        for effect in effects:
            if effect['effect_type'] == 'damage_buff':
                player_damage += effect['effect_value']
            elif effect['effect_type'] == 'defense_buff':
                player_defense += effect['effect_value']
        
        damage_to_enemy = max(1, player_damage - enemy_defense)
        damage_to_player = max(1, enemy_damage - player_defense)
        
        effects_text = "\n".join([f"🔮 {effect['effect_type'].replace('_buff', '')}: +{effect['effect_value']} ({effect['rounds_left']} раундов)" for effect in effects]) if effects else "Нет активных эффектов"
        fight_text = (
            f"⚔️ *Бой с {enemy_name}!*\n\n"
            f"👤 *Ваши характеристики:*\n"
            f"❤️ Здоровье: {player_health}\n"
            f"⚔️ Урон: {player_damage}\n"
            f"🛡️ Защита: {player_defense}\n"
            f"🔮 Эффекты:\n{effects_text}\n\n"
            f"👹 *Характеристики {enemy_name}:*\n"
            f"❤️ Здоровье: {enemy_health}\n"
            f"⚔️ Урон: {enemy_damage}\n"
            f"🛡️ Защита: {enemy_defense}\n\n"
            f"Вы нанесли {damage_to_enemy} урона!\n"
            f"{enemy_name} нанёс вам {damage_to_player} урона!\n"
            f"Что будете делать?"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Атаковать", callback_data=f"fight_attack_{enemy_id}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
            [InlineKeyboardButton(text="Использовать зелье", callback_data=f"fight_use_potion_{enemy_id}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
            [InlineKeyboardButton(text="Сбежать", callback_data="fight_flee")]
        ])
        
        await callback.message.edit_text(fight_text, reply_markup=keyboard, parse_mode='Markdown')
        conn.close()
        await callback.answer()