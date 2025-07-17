from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_connection
from utils import get_main_keyboard
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_inventory(message: types.Message | types.CallbackQuery, page: int = 0):
    """Обрабатывает команду /inventory: показывает предметы игрока с пагинацией."""
    user_id = message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, item_name, item_type, item_value FROM inventory WHERE user_id = ?', (user_id,))
    items = c.fetchall()
    
    is_callback = isinstance(message, types.CallbackQuery)
    msg = message.message if is_callback else message

    if not items:
        if is_callback:
            await msg.edit_text("🎒 Ваш инвентарь пуст.", reply_markup=None)
        else:
            await msg.answer("🎒 Ваш инвентарь пуст.", reply_markup=get_main_keyboard())
        conn.close()
        return
    
    # Пагинация: максимум 5 предметов на страницу
    items_per_page = 5
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    page = max(0, min(page, total_pages - 1))  # Ограничение номера страницы
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_items = items[start_idx:end_idx]
    
    inventory_text = "🎒 *Инвентарь:*\n"
    for item in current_items:
        item_id, item_name, item_type, item_value = item
        inventory_text += f"- {item_name} ({item_type}, +{item_value})\n"
    
    if total_pages > 1:
        inventory_text += f"\n📄 Страница {page + 1} из {total_pages}"
    
    # Создание инлайн-кнопок для использования предметов и пагинации
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for item in current_items:
        item_id, item_name, item_type, item_value = item
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=f"Использовать {item_name}", callback_data=f"use_item_{item_id}_{page}")])
    
    # Кнопки пагинации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"inv_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"inv_page_{page+1}"))
    if nav_buttons:
        keyboard.inline_keyboard.append(nav_buttons)
    
    # Кнопка "Обновить"
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔄 Обновить", callback_data=f"inv_page_{page}")])
    
    # Проверка текущего сообщения для избежания TelegramBadRequest
    if is_callback:
        try:
            current_text = msg.text or ""
            current_reply_markup = msg.reply_markup
            if current_text != inventory_text or current_reply_markup != keyboard:
                await msg.edit_text(inventory_text, parse_mode='Markdown', reply_markup=keyboard)
            else:
                logger.debug(f"Пропуск редактирования: сообщение инвентаря не изменилось для пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения инвентаря для {user_id}: {e}")
            await msg.answer(inventory_text, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await msg.answer(inventory_text, parse_mode='Markdown', reply_markup=keyboard)
    
    conn.close()

async def handle_use_item(callback: types.CallbackQuery):
    """Обрабатывает использование предмета из инвентаря (вне боя)."""
    user_id = callback.from_user.id
    item_id = int(callback.data.split('_')[2])
    page = int(callback.data.split('_')[3])
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Получение предмета
    c.execute('SELECT item_name, item_type, item_value FROM inventory WHERE id = ? AND user_id = ?', (item_id, user_id))
    item = c.fetchone()
    
    if not item:
        await callback.message.answer("Предмет не найден.", reply_markup=get_main_keyboard())
        logger.error(f"Предмет с ID {item_id} не найден для пользователя {user_id}")
        conn.close()
        await callback.answer()
        return
    
    item_name, item_type, item_value = item
    
    # Логика использования предмета
    if item_type == 'potion':
        # Зелье: восстанавливает здоровье
        c.execute('SELECT health FROM players WHERE user_id = ?', (user_id,))
        current_health = c.fetchone()[0]
        new_health = min(current_health + item_value, 100)  # Ограничение здоровья до 100
        c.execute('UPDATE players SET health = ? WHERE user_id = ?', (new_health, user_id))
        c.execute('DELETE FROM inventory WHERE id = ?', (item_id,))  # Удаление использованного предмета
        conn.commit()
        await callback.message.answer(f"Вы использовали {item_name}! ❤️ Здоровье восстановлено до {new_health}.")
        logger.info(f"Пользователь {user_id} использовал {item_name}, здоровье: {new_health}")
    elif item_type == 'weapon':
        # Оружие: увеличивает урон
        c.execute('UPDATE players SET damage = damage + ? WHERE user_id = ?', (item_value, user_id))
        c.execute('DELETE FROM inventory WHERE id = ?', (item_id,))  # Удаление предмета после экипировки
        conn.commit()
        await callback.message.answer(f"Вы экипировали {item_name}! ⚔️ Урон увеличен на {item_value}.")
        logger.info(f"Пользователь {user_id} экипировал {item_name}, урон увеличен на {item_value}")
    elif item_type == 'buff_potion':
        # Зелье с эффектом: добавляет временный бафф
        effect_type = 'damage_buff' if 'Strength' in item_name else 'defense_buff'
        c.execute('INSERT OR REPLACE INTO active_effects (user_id, effect_type, effect_value, rounds_left) VALUES (?, ?, ?, ?)',
                  (user_id, effect_type, item_value, 3))
        c.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
        conn.commit()
        await callback.message.answer(f"Вы использовали {item_name}! 🔮 Эффект применён на 3 раунда.")
        logger.info(f"Пользователь {user_id} использовал {item_name}, эффект: {effect_type}, значение: {item_value}")
    else:
        await callback.message.answer(f"Пока нельзя использовать предметы типа {item_type}.", reply_markup=get_main_keyboard())
        logger.warning(f"Попытка использовать неподдерживаемый тип предмета {item_type} пользователем {user_id}")
    
    conn.close()
    # Обновление инвентаря
    await handle_inventory(callback, page=page)
    await callback.answer()

async def handle_inventory_page(callback: types.CallbackQuery):
    """Обрабатывает переключение страниц инвентаря."""
    page = int(callback.data.split('_')[2])
    await handle_inventory(callback, page=page)
    await callback.answer()