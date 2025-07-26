from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_connection
import logging
from config import in_fight  # Импорт для проверки состояния боя

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_inventory(message: types.Message, page: int = 1, user_id: int = None):
    """Обрабатывает команду /inventory: показывает инвентарь пользователя с пагинацией."""
    user_id = user_id or message.from_user.id
    if user_id in in_fight:
        await message.answer("Вы сейчас в бою! Завершите бой перед использованием инвентаря.", reply_markup=None)
        return
    logger.debug(f"Обработка инвентаря для user_id={user_id}, страница={page}")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Проверка существования таблицы inventory
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
    if not c.fetchone():
        logger.error("Таблица inventory не существует в базе данных")
        await message.answer("Ошибка: база данных повреждена. Обратитесь к администратору.")
        conn.close()
        return
    
    # Получение всех предметов пользователя
    c.execute('SELECT id, item_name, item_type, item_value FROM inventory WHERE user_id = ?', (user_id,))
    items = c.fetchall()
    logger.debug(f"Найдено предметов для user_id={user_id}: {[(item[0], item[1], item[2], item[3]) for item in items]}")
    
    if not items:
        await message.answer("Ваш инвентарь пуст!", reply_markup=None)
        conn.close()
        logger.info(f"Инвентарь пуст для user_id={user_id}")
        return
    
    # Пагинация
    items_per_page = 5
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    current_items = items[start_idx:end_idx]
    logger.debug(f"Отображаемые предметы: страница={page}, start_idx={start_idx}, end_idx={end_idx}, предметы={[item[1] for item in current_items]}")
    
    # Формирование текста инвентаря
    inventory_text = f"*Инвентарь (страница {page}/{total_pages})*\n\n"
    for item in current_items:
        inventory_text += f"📦 *{item[1]}* ({item[2]}): +{item[3]}\n"
    
    # Создание инлайн-клавиатуры для пагинации и использования предметов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for item in current_items:
        if item[2].lower() in ['weapon', 'potion', 'buff_potion']:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"Использовать {item[1]}",
                    callback_data=f"use_item_{item[0]}"
                )
            ])
    if total_pages > 1:
        buttons = []
        if page > 1:
            buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"inv_page_{page-1}_{user_id}"))
        if page < total_pages:
            buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"inv_page_{page+1}_{user_id}"))
        if buttons:
            keyboard.inline_keyboard.append(buttons)
    
    await message.answer(inventory_text, parse_mode='Markdown', reply_markup=keyboard)
    logger.info(f"Показан инвентарь пользователю {user_id}, страница {page}")
    conn.close()

async def handle_potions(message: types.Message, page: int = 1, user_id: int = None):
    """Обрабатывает команду 'Зелья': показывает только зелья с пагинацией и позволяет их использовать."""
    user_id = user_id or message.from_user.id
    logger.debug(f"Обработка зелий для user_id={user_id}, страница={page}")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Проверка существования таблицы inventory
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
    if not c.fetchone():
        logger.error("Таблица inventory не существует в базе данных")
        await message.answer("Ошибка: база данных повреждена. Обратитесь к администратору.")
        conn.close()
        return
    
    # Получение только зелий пользователя
    c.execute('SELECT id, item_name, item_type, item_value FROM inventory WHERE user_id = ? AND item_type IN (?, ?)', 
              (user_id, 'potion', 'buff_potion'))
    potions = c.fetchall()
    logger.debug(f"Найдено зелий для user_id={user_id}: {[(potion[0], potion[1], potion[2], potion[3]) for potion in potions]}")
    
    if not potions:
        await message.answer("У вас нет зелий!", reply_markup=None)
        conn.close()
        logger.info(f"Зелья отсутствуют для user_id={user_id}")
        return
    
    # Пагинация
    items_per_page = 5
    total_pages = (len(potions) + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    current_potions = potions[start_idx:end_idx]
    logger.debug(f"Отображаемые зелья: страница={page}, start_idx={start_idx}, end_idx={end_idx}, зелья={[potion[1] for potion in current_potions]}")
    
    # Формирование текста зелий
    potions_text = f"*Зелья (страница {page}/{total_pages})*\n\n"
    for potion in current_potions:
        potions_text += f"🧪 *{potion[1]}* ({potion[2]}): +{potion[3]}\n"
    
    # Создание инлайн-клавиатуры для пагинации и использования зелий
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for potion in current_potions:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"Использовать {potion[1]}",
                callback_data=f"use_item_{potion[0]}"
            )
        ])
    if total_pages > 1:
        buttons = []
        if page > 1:
            buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"potion_page_{page-1}_{user_id}"))
        if page < total_pages:
            buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"potion_page_{page+1}_{user_id}"))
        if buttons:
            keyboard.inline_keyboard.append(buttons)
    
    await message.answer(potions_text, parse_mode='Markdown', reply_markup=keyboard)
    logger.info(f"Показаны зелья пользователю {user_id}, страница {page}")
    conn.close()

async def handle_inventory_page(callback: types.CallbackQuery):
    """Обрабатывает нажатие на кнопки пагинации инвентаря."""
    if callback.from_user.id in in_fight:
        await callback.message.edit_text("Вы сейчас в бою! Завершите бой перед использованием инвентаря.", reply_markup=None)
        await callback.answer()
        return
    try:
        parts = callback.data.split('_')
        page = int(parts[2])
        user_id = int(parts[3])
        logger.debug(f"Обработка пагинации инвентаря: page={page}, user_id={user_id}")
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка парсинга callback_data для inv_page: {callback.data}, ошибка: {e}")
        await callback.message.edit_text("Ошибка при смене страницы. Попробуйте снова.", reply_markup=None)
        await callback.answer()
        return
    
    await callback.message.delete()
    await handle_inventory(callback.message, page=page, user_id=user_id)
    await callback.answer()

async def handle_potions_page(callback: types.CallbackQuery):
    """Обрабатывает нажатие на кнопки пагинации зелий."""
    try:
        parts = callback.data.split('_')
        page = int(parts[2])
        user_id = int(parts[3])
        logger.debug(f"Обработка пагинации зелий: page={page}, user_id={user_id}")
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка парсинга callback_data для potion_page: {callback.data}, ошибка: {e}")
        await callback.message.edit_text("Ошибка при смене страницы. Попробуйте снова.", reply_markup=None)
        await callback.answer()
        return
    
    await callback.message.delete()
    await handle_potions(callback.message, page=page, user_id=user_id)
    await callback.answer()

async def handle_show_inventory(callback: types.CallbackQuery):
    """Обрабатывает нажатие на кнопку 'Инвентарь' из профиля."""
    if callback.from_user.id in in_fight:
        await callback.message.edit_text("Вы сейчас в бою! Завершите бой перед использованием инвентаря.", reply_markup=None)
        await callback.answer()
        return
    try:
        parts = callback.data.split('_')
        user_id = int(parts[2])
        logger.debug(f"Обработка показа инвентаря для user_id={user_id}")
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка парсинга callback_data для show_inventory: {callback.data}, ошибка: {e}")
        await callback.message.edit_text("Ошибка при открытии инвентаря. Попробуйте снова.", reply_markup=None)
        await callback.answer()
        return
    
    await callback.message.delete()
    await handle_inventory(callback.message, page=1, user_id=user_id)
    await callback.answer()

async def handle_use_item(callback: types.CallbackQuery):
    """Обрабатывает использование предмета из инвентаря."""
    user_id = callback.from_user.id
    logger.info(f"Получен callback для использования предмета пользователем {user_id}: {callback.data}")
    
    parts = callback.data.split('_')
    item_id = int(parts[2])
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Получение предмета и максимального здоровья
    c.execute('SELECT item_name, item_type, item_value FROM inventory WHERE id = ? AND user_id = ?', (item_id, user_id))
    item = c.fetchone()
    if not item:
        await callback.message.edit_text("Предмет не найден.", reply_markup=None)
        logger.error(f"Предмет с ID {item_id} не найден для пользователя {user_id}")
        conn.close()
        await callback.answer()
        return
    
    item_name, item_type, item_value = item
    c.execute('SELECT health, max_health, damage, defense FROM players WHERE user_id = ?', (user_id,))
    player_data = c.fetchone()
    if not player_data:
        await callback.message.edit_text("Ошибка: данные игрока не найдены.", reply_markup=None)
        conn.close()
        await callback.answer()
        return
    current_health, max_health, player_base_damage, player_base_defense = player_data
    
    # Проверка, находится ли игрок в бою
    is_in_fight = user_id in in_fight
    fight_data = None
    if is_in_fight:
        # Получение данных текущего боя из callback_data последнего сообщения боя
        # Предполагается, что последнее сообщение боя содержит callback_data вида fight_*
        try:
            parts = callback.message.reply_markup.inline_keyboard[-1][0].callback_data.split('_')
            if parts[0] == 'fight':
                enemy_id = int(parts[2])
                enemy_name = parts[3]
                enemy_health = int(parts[4])
                damage_to_enemy = int(parts[5])
                damage_to_player = int(parts[6])
                c.execute('SELECT damage, defense FROM enemies WHERE enemy_id = ?', (enemy_id,))
                enemy_data = c.fetchone()
                if enemy_data:
                    enemy_damage, enemy_defense = enemy_data
                    fight_data = {
                        'enemy_id': enemy_id,
                        'enemy_name': enemy_name,
                        'enemy_health': enemy_health,
                        'enemy_damage': enemy_damage,
                        'enemy_defense': enemy_defense,
                        'damage_to_enemy': damage_to_enemy,
                        'damage_to_player': damage_to_player
                    }
        except Exception as e:
            logger.error(f"Ошибка при получении данных боя для user_id={user_id}: {e}")
            is_in_fight = False  # Отключаем режим боя, если данные недоступны

    if item_type.lower() == 'weapon':
        if is_in_fight:
            await callback.message.edit_text("Вы не можете экипировать оружие во время боя!", reply_markup=None)
            logger.info(f"Пользователь {user_id} попытался использовать оружие {item_name} в бою")
            conn.close()
            await callback.answer()
            return
        # Применение оружия (увеличивает урон игрока)
        c.execute('UPDATE players SET damage = damage + ? WHERE user_id = ?', (item_value, user_id))
        c.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
        conn.commit()
        await callback.message.edit_text(f"Вы экипировали {item_name}! ⚔️ Урон увеличен на {item_value}.", parse_mode='Markdown')
        logger.info(f"Пользователь {user_id} использовал {item_name}, урон увеличен на {item_value}")
    
    elif item_type.lower() == 'potion':
        # Применение зелья здоровья
        new_health = min(current_health + item_value, max_health)
        c.execute('UPDATE players SET health = ? WHERE user_id = ?', (new_health, user_id))
        c.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
        conn.commit()
        
        if is_in_fight and fight_data:
            # Обновление интерфейса боя
            c.execute('SELECT effect_type, effect_value, rounds_left FROM active_effects WHERE user_id = ?', (user_id,))
            effects = c.fetchall()
            player_damage = player_base_damage
            player_defense = player_base_defense
            for effect in effects:
                if effect[0] == 'damage_buff':
                    player_damage += effect[1]
                elif effect[0] == 'defense_buff':
                    player_defense += effect[1]
            damage_to_enemy = max(1, player_damage - fight_data['enemy_defense'])
            damage_to_player = max(1, fight_data['enemy_damage'] - player_defense)
            effects_text = "\n".join([f"🔮 {effect[0].replace('_buff', '').title()}: +{effect[1]} ({effect[2]} раундов)" for effect in effects]) if effects else "Нет активных эффектов"
            fight_text = (
                f"⚔️ *Бой с {fight_data['enemy_name']}!*\n\n"
                f"👤 *Ваши характеристики:*\n"
                f"❤️ Здоровье: {new_health}/{max_health}\n"
                f"⚔️ Урон: {player_damage}\n"
                f"🛡️ Защита: {player_defense}\n"
                f"🔮 Эффекты:\n{effects_text}\n\n"
                f"👹 *Характеристики {fight_data['enemy_name']}:*\n"
                f"❤️ Здоровье: {fight_data['enemy_health']}\n"
                f"⚔️ Урон: {fight_data['enemy_damage']}\n"
                f"🛡️ Защита: {fight_data['enemy_defense']}\n\n"
                f"Вы использовали {item_name}! ❤️ Здоровье восстановлено на {new_health - current_health}.\n"
                f"Что будете делать?"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="Атаковать", callback_data=f"fight_attack_{fight_data['enemy_id']}_{fight_data['enemy_name']}_{fight_data['enemy_health']}_{damage_to_enemy}_{damage_to_player}")
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="Сбежать", callback_data=f"fight_flee_{fight_data['enemy_id']}_{fight_data['enemy_name']}_{fight_data['enemy_health']}_{damage_to_enemy}_{damage_to_player}")
            ])
            await callback.message.edit_text(fight_text, parse_mode='Markdown', reply_markup=keyboard)
            logger.info(f"Пользователь {user_id} использовал {item_name} в бою, здоровье восстановлено до {new_health}")
        else:
            await callback.message.edit_text(f"Вы использовали {item_name}! ❤️ Здоровье восстановлено на {new_health - current_health} (максимум {max_health}).", parse_mode='Markdown')
            logger.info(f"Пользователь {user_id} использовал {item_name}, здоровье восстановлено до {new_health}")
    
    elif item_type.lower() == 'buff_potion':
        # Применение бафф-зелья
        effect_duration = 3  # Эффект длится 3 раунда
        effect_type = 'damage_buff' if 'strength' in item_name.lower() else 'defense_buff'
        c.execute(
            'INSERT INTO active_effects (user_id, effect_type, effect_value, rounds_left) VALUES (?, ?, ?, ?)',
            (user_id, effect_type, item_value, effect_duration)
        )
        c.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
        conn.commit()
        
        if is_in_fight and fight_data:
            # Обновление интерфейса боя
            c.execute('SELECT effect_type, effect_value, rounds_left FROM active_effects WHERE user_id = ?', (user_id,))
            effects = c.fetchall()
            player_damage = player_base_damage
            player_defense = player_base_defense
            for effect in effects:
                if effect[0] == 'damage_buff':
                    player_damage += effect[1]
                elif effect[0] == 'defense_buff':
                    player_defense += effect[1]
            damage_to_enemy = max(1, player_damage - fight_data['enemy_defense'])
            damage_to_player = max(1, fight_data['enemy_damage'] - player_defense)
            effects_text = "\n".join([f"🔮 {effect[0].replace('_buff', '').title()}: +{effect[1]} ({effect[2]} раундов)" for effect in effects]) if effects else "Нет активных эффектов"
            fight_text = (
                f"⚔️ *Бой с {fight_data['enemy_name']}!*\n\n"
                f"👤 *Ваши характеристики:*\n"
                f"❤️ Здоровье: {current_health}/{max_health}\n"
                f"⚔️ Урон: {player_damage}\n"
                f"🛡️ Защита: {player_defense}\n"
                f"🔮 Эффекты:\n{effects_text}\n\n"
                f"👹 *Характеристики {fight_data['enemy_name']}:*\n"
                f"❤️ Здоровье: {fight_data['enemy_health']}\n"
                f"⚔️ Урон: {fight_data['enemy_damage']}\n"
                f"🛡️ Защита: {fight_data['enemy_defense']}\n\n"
                f"Вы использовали {item_name}! 🔮 {effect_type.replace('_buff', '').title()}: +{item_value} на {effect_duration} раундов.\n"
                f"Что будете делать?"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="Атаковать", callback_data=f"fight_attack_{fight_data['enemy_id']}_{fight_data['enemy_name']}_{fight_data['enemy_health']}_{damage_to_enemy}_{damage_to_player}")
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="Сбежать", callback_data=f"fight_flee_{fight_data['enemy_id']}_{fight_data['enemy_name']}_{fight_data['enemy_health']}_{damage_to_enemy}_{damage_to_player}")
            ])
            await callback.message.edit_text(fight_text, parse_mode='Markdown', reply_markup=keyboard)
            logger.info(f"Пользователь {user_id} использовал {item_name} в бою, эффект {effect_type} +{item_value} на {effect_duration} раундов")
        else:
            await callback.message.edit_text(f"Вы использовали {item_name}! 🔮 {effect_type.replace('_buff', '').title()}: +{item_value} на {effect_duration} раундов.", parse_mode='Markdown')
            logger.info(f"Пользователь {user_id} использовал {item_name}, эффект {effect_type} +{item_value} на {effect_duration} раундов")
    
    else:
        await callback.message.edit_text(f"Предмет {item_name} нельзя использовать.", reply_markup=None)
        logger.info(f"Пользователь {user_id} попытался использовать неподходящий предмет: {item_name}")
    
    conn.close()
    await callback.answer()

async def handle_use_potion(message: types.Message):
    """Обрабатывает команду /use <item_name>: использует зелье по имени."""
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите название зелья: /use <название>", reply_markup=None)
        logger.info(f"Пользователь {user_id} не указал название зелья для команды /use")
        return
    
    item_name = ' '.join(args[1:]).strip()
    logger.debug(f"Обработка команды /use для user_id={user_id}, item_name={item_name}")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Проверка существования зелья
    c.execute('SELECT id, item_type, item_value FROM inventory WHERE user_id = ? AND item_name = ?', (user_id, item_name))
    item = c.fetchone()
    if not item:
        await message.answer(f"Зелье '{item_name}' не найдено в вашем инвентаре.", reply_markup=None)
        logger.error(f"Зелье {item_name} не найдено для user_id={user_id}")
        conn.close()
        return
    
    item_id, item_type, item_value = item
    c.execute('SELECT health, max_health FROM players WHERE user_id = ?', (user_id,))
    player_data = c.fetchone()
    if not player_data:
        await message.answer("Ошибка: данные игрока не найдены.", reply_markup=None)
        conn.close()
        return
    current_health, max_health = player_data
    
    if item_type.lower() not in ['potion', 'buff_potion']:
        await message.answer(f"Предмет {item_name} не является зельем.", reply_markup=None)
        logger.info(f"Пользователь {user_id} попытался использовать неподходящий предмет: {item_name}")
        conn.close()
        return
    
    if item_type.lower() == 'potion':
        # Применение зелья здоровья
        new_health = min(current_health + item_value, max_health)
        c.execute('UPDATE players SET health = ? WHERE user_id = ?', (new_health, user_id))
        c.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
        conn.commit()
        await message.answer(f"Вы использовали {item_name}! ❤️ Здоровье восстановлено на {new_health - current_health} (максимум {max_health}).", parse_mode='Markdown')
        logger.info(f"Пользователь {user_id} использовал {item_name}, здоровье восстановлено до {new_health}")
    
    elif item_type.lower() == 'buff_potion':
        # Применение бафф-зелья
        effect_duration = 3  # Эффект длится 3 раунда
        effect_type = 'damage_buff' if 'strength' in item_name.lower() else 'defense_buff'
        c.execute(
            'INSERT INTO active_effects (user_id, effect_type, effect_value, rounds_left) VALUES (?, ?, ?, ?)',
            (user_id, effect_type, item_value, effect_duration)
        )
        c.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
        conn.commit()
        await message.answer(f"Вы использовали {item_name}! 🔮 {effect_type.replace('_buff', '').title()}: +{item_value} на {effect_duration} раундов.", parse_mode='Markdown')
        logger.info(f"Пользователь {user_id} использовал {item_name}, эффект {effect_type} +{item_value} на {effect_duration} раундов")
    
    conn.close()