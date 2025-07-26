from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_connection
from utils import get_main_keyboard
import logging
import random
from config import in_fight

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_fight(message: types.Message):
    """Обрабатывает команду /fight: начинает бой с врагом."""
    user_id = message.from_user.id
    if user_id in in_fight:
        await message.answer("Вы уже в бою! Завершите текущий бой.", reply_markup=None)
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Получение характеристик игрока
    c.execute('SELECT health, max_health, damage, defense FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    if not player:
        await message.answer("Вы не зарегистрированы. Используйте /start.", reply_markup=get_main_keyboard())
        conn.close()
        return
    player_health, max_health, player_base_damage, player_base_defense = player
    
    # Получение активных эффектов игрока
    c.execute('SELECT effect_type, effect_value, rounds_left FROM active_effects WHERE user_id = ?', (user_id,))
    effects = c.fetchall()
    player_damage = player_base_damage
    player_defense = player_base_defense
    for effect in effects:
        if effect[0] == 'damage_buff':
            player_damage += effect[1]
        elif effect[0] == 'defense_buff':
            player_defense += effect[1]
    
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
    
    # Формирование текста боя
    effects_text = "\n".join([f"🔮 {effect[0].replace('_buff', '').title()}: +{effect[1]} ({effect[2]} раундов)" for effect in effects]) if effects else "Нет активных эффектов"
    fight_text = (
        f"⚔️ *Бой с {enemy_name}!*\n\n"
        f"👤 *Ваши характеристики:*\n"
        f"❤️ Здоровье: {player_health}/{max_health}\n"
        f"⚔️ Урон: {player_damage}\n"
        f"🛡️ Защита: {player_defense}\n"
        f"🔮 Эффекты:\n{effects_text}\n\n"
        f"👹 *Характеристики {enemy_name}:*\n"
        f"❤️ Здоровье: {enemy_health}\n"
        f"⚔️ Урон: {enemy_damage}\n"
        f"🛡️ Защита: {enemy_defense}\n\n"
        f"Что будете делать?"
    )
    
    # Создание инлайн-клавиатуры (только Атаковать и Сбежать)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="Атаковать", callback_data=f"fight_attack_{enemy_id}_{enemy_name}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")
    ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="Сбежать", callback_data=f"fight_flee_{enemy_id}_{enemy_name}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")
    ])
    
    await message.answer(fight_text, parse_mode='Markdown', reply_markup=keyboard)
    in_fight[user_id] = True  # Устанавливаем состояние боя
    logger.info(f"Начало боя для пользователя {user_id} против {enemy_name}")
    conn.close()

async def handle_fight_action(callback: types.CallbackQuery):
    """Обрабатывает действия в бою (атака, побег)."""
    user_id = callback.from_user.id
    logger.info(f"Получен callback для пользователя {user_id}: {callback.data}")
    
    try:
        parts = callback.data.split('_')
        action = parts[1]
        logger.debug(f"Извлечённое действие: {action}, полные части: {parts}")
    except IndexError:
        logger.error(f"Ошибка парсинга callback_data: {callback.data}")
        await callback.message.edit_text("Ошибка: неверные данные действия. Попробуйте снова.", reply_markup=None)
        del in_fight[user_id]  # Очищаем состояние боя при ошибке
        await callback.answer()
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Получение характеристик игрока
    c.execute('SELECT health, max_health, damage, defense FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    if not player:
        await callback.message.edit_text("Вы не зарегистрированы. Используйте /start.", reply_markup=None)
        del in_fight[user_id]  # Очищаем состояние боя при ошибке
        conn.close()
        await callback.answer()
        return
    player_health, max_health, player_base_damage, player_base_defense = player
    
    # Получение активных эффектов
    c.execute('SELECT effect_type, effect_value, rounds_left FROM active_effects WHERE user_id = ?', (user_id,))
    effects = c.fetchall()
    player_damage = player_base_damage
    player_defense = player_base_defense
    for effect in effects:
        if effect[0] == 'damage_buff':
            player_damage += effect[1]
        elif effect[0] == 'defense_buff':
            player_defense += effect[1]
    
    enemy_id = int(parts[2])
    enemy_name = parts[3]
    enemy_health = int(parts[4])
    damage_to_enemy = int(parts[5])
    damage_to_player = int(parts[6])
    
    try:
        # Получение характеристик врага для расчётов
        c.execute('SELECT damage, defense FROM enemies WHERE enemy_id = ?', (enemy_id,))
        enemy_data = c.fetchone()
        if not enemy_data:
            await callback.message.edit_text("Враг не найден. Попробуйте позже.", reply_markup=None)
            del in_fight[user_id]  # Очищаем состояние боя при ошибке
            conn.commit()
            conn.close()
            await callback.answer()
            return
        enemy_damage, enemy_defense = enemy_data

        if action == 'flee':
            logger.debug(f"Пользователь {user_id} выбрал действие: flee")
            # Случайность сбегания (50% шанс)
            if random.random() < 0.5:
                for effect in effects:
                    rounds_left = effect[2] - 1
                    if rounds_left <= 0:
                        c.execute('DELETE FROM active_effects WHERE user_id = ? AND effect_type = ?', (user_id, effect[0]))
                    else:
                        c.execute('UPDATE active_effects SET rounds_left = ? WHERE user_id = ? AND effect_type = ?',
                                  (rounds_left, user_id, effect[0]))
                conn.commit()
                await callback.message.edit_text("Вы попытались сбежать... Успех!", reply_markup=None)
                del in_fight[user_id]  # Очищаем состояние боя
                logger.info(f"Пользователь {user_id} сбежал из боя")
            else:
                player_health -= damage_to_player
                c.execute('UPDATE players SET health = ? WHERE user_id = ?', (player_health, user_id))
                conn.commit()
                
                # Проверка на поражение игрока
                if player_health <= 0:
                    c.execute('DELETE FROM active_effects WHERE user_id = ?', (user_id,))
                    c.execute('UPDATE players SET health = 50 WHERE user_id = ?', (user_id,))
                    conn.commit()
                    await callback.message.edit_text("💀 Вы побеждены! Здоровье сброшено до 50.", reply_markup=None)
                    del in_fight[user_id]  # Очищаем состояние боя
                    logger.info(f"Пользователь {user_id} проиграл бой при попытке сбежать")
                    conn.close()
                    await callback.answer()
                    return
                
                # Обновляем интерфейс боя после неудачного побега
                c.execute('SELECT effect_type, effect_value, rounds_left FROM active_effects WHERE user_id = ?', (user_id,))
                effects = c.fetchall()
                player_damage = player_base_damage
                player_defense = player_base_defense
                for effect in effects:
                    if effect[0] == 'damage_buff':
                        player_damage += effect[1]
                    elif effect[0] == 'defense_buff':
                        player_defense += effect[1]
                damage_to_enemy = max(1, player_damage - enemy_defense)
                damage_to_player = max(1, enemy_damage - player_defense)
                effects_text = "\n".join([f"🔮 {effect[0].replace('_buff', '').title()}: +{effect[1]} ({effect[2]} раундов)" for effect in effects]) if effects else "Нет активных эффектов"
                fight_text = (
                    f"⚔️ *Бой с {enemy_name}!*\n\n"
                    f"👤 *Ваши характеристики:*\n"
                    f"❤️ Здоровье: {player_health}/{max_health}\n"
                    f"⚔️ Урон: {player_damage}\n"
                    f"🛡️ Защита: {player_defense}\n"
                    f"🔮 Эффекты:\n{effects_text}\n\n"
                    f"👹 *Характеристики {enemy_name}:*\n"
                    f"❤️ Здоровье: {enemy_health}\n"
                    f"⚔️ Урон: {enemy_damage}\n"
                    f"🛡️ Защита: {enemy_defense}\n\n"
                    f"Вы попытались сбежать, но не смогли! {enemy_name} нанёс {damage_to_player} урона.\n"
                    f"Что будете делать?"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(text="Атаковать", callback_data=f"fight_attack_{enemy_id}_{enemy_name}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")
                ])
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(text="Сбежать", callback_data=f"fight_flee_{enemy_id}_{enemy_name}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")
                ])
                await callback.message.edit_text(fight_text, parse_mode='Markdown', reply_markup=keyboard)
                logger.info(f"Пользователь {user_id} не смог сбежать, здоровье уменьшено до {player_health}")
            conn.close()
            await callback.answer()
            return
        
        if action == 'attack':
            logger.debug(f"Пользователь {user_id} выбрал действие: attack")
            
            # Обновление здоровья
            enemy_health -= damage_to_enemy
            player_health -= damage_to_player
            
            # Обновление эффектов (уменьшение раундов)
            for effect in effects:
                rounds_left = effect[2] - 1
                if rounds_left <= 0:
                    c.execute('DELETE FROM active_effects WHERE user_id = ? AND effect_type = ?', (user_id, effect[0]))
                else:
                    c.execute('UPDATE active_effects SET rounds_left = ? WHERE user_id = ? AND effect_type = ?',
                              (rounds_left, user_id, effect[0]))
            
            if enemy_health <= 0:
                # Победа игрока
                c.execute('UPDATE players SET gold = gold + 20 WHERE user_id = ?', (user_id,))
                c.execute('UPDATE players SET health = ? WHERE user_id = ?', (player_health, user_id))
                conn.commit()
                await callback.message.edit_text(f"🎉 Вы победили {enemy_name}! +20 золота", parse_mode='Markdown', reply_markup=None)
                del in_fight[user_id]  # Очищаем состояние боя
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
                del in_fight[user_id]  # Очищаем состояние боя
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
                if effect[0] == 'damage_buff':
                    player_damage += effect[1]
                elif effect[0] == 'defense_buff':
                    player_defense += effect[1]
            
            damage_to_enemy = max(1, player_damage - enemy_defense)
            damage_to_player = max(1, enemy_damage - player_defense)
            
            effects_text = "\n".join([f"🔮 {effect[0].replace('_buff', '').title()}: +{effect[1]} ({effect[2]} раундов)" for effect in effects]) if effects else "Нет активных эффектов"
            fight_text = (
                f"⚔️ *Бой с {enemy_name}!*\n\n"
                f"👤 *Ваши характеристики:*\n"
                f"❤️ Здоровье: {player_health}/{max_health}\n"
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
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="Атаковать", callback_data=f"fight_attack_{enemy_id}_{enemy_name}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="Сбежать", callback_data=f"fight_flee_{enemy_id}_{enemy_name}_{enemy_health}_{damage_to_enemy}_{damage_to_player}")
            ])
            
            await callback.message.edit_text(fight_text, parse_mode='Markdown', reply_markup=keyboard)
            conn.close()
            await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при обработке действия в бою: {str(e)}")
        await callback.message.edit_text("Произошла ошибка в бою. Бой завершён.", reply_markup=None)
        del in_fight[user_id]  # Очищаем состояние боя при любой ошибке
        conn.close()
        await callback.answer()