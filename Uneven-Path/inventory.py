from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_connection
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_inventory(message: types.Message, page: int = 1, user_id: int = None):
    """Обрабатывает команду /inventory: показывает инвентарь пользователя с пагинацией."""
    # Используем user_id из аргумента, если он передан, иначе берём из message
    user_id = user_id or message.from_user.id
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
    logger.debug(f"Найдено предметов для user_id={user_id}: {[(item['id'], item['item_name'], item['item_type'], item['item_value']) for item in items]}")
    
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
    logger.debug(f"Отображаемые предметы: страница={page}, start_idx={start_idx}, end_idx={end_idx}, предметы={[item['item_name'] for item in current_items]}")
    
    # Формирование текста инвентаря
    inventory_text = f"*Инвентарь (страница {page}/{total_pages})*\n\n"
    for item in current_items:
        inventory_text += f"📦 *{item['item_name']}* ({item['item_type']}): +{item['item_value']}\n"
    
    # Создание инлайн-клавиатуры для пагинации и использования предметов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for item in current_items:
        if item['item_type'].lower() == 'weapon':
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"Использовать {item['item_name']}",
                    callback_data=f"use_item_{item['id']}"
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

async def handle_inventory_page(callback: types.CallbackQuery):
    """Обрабатывает нажатие на кнопки пагинации инвентаря."""
    try:
        parts = callback.data.split('_')
        page = int(parts[2])
        user_id = int(parts[3])
        logger.debug(f"Обработка пагинации: page={page}, user_id={user_id}")
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка парсинга callback_data для inv_page: {callback.data}, ошибка: {e}")
        await callback.message.edit_text("Ошибка при смене страницы. Попробуйте снова.", reply_markup=None)
        await callback.answer()
        return
    
    await callback.message.delete()
    await handle_inventory(callback.message, page=page, user_id=user_id)
    await callback.answer()

async def handle_use_item(callback: types.CallbackQuery):
    """Обрабатывает использование предмета из инвентаря."""
    user_id = callback.from_user.id
    logger.info(f"Получен callback для использования предмета пользователем {user_id}: {callback.data}")
    
    try:
        item_id = int(callback.data.split('_')[-1])
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка парсинга callback_data для use_item: {callback.data}, ошибка: {e}")
        await callback.message.edit_text("Ошибка. Попробуйте снова.", reply_markup=None)
        await callback.answer()
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Получение предмета
    c.execute('SELECT item_name, item_type, item_value FROM inventory WHERE id = ? AND user_id = ?', (item_id, user_id))
    item = c.fetchone()
    if not item:
        await callback.message.edit_text("Предмет не найден.", reply_markup=None)
        logger.error(f"Предмет с ID {item_id} не найден для пользователя {user_id}")
        conn.close()
        await callback.answer()
        return
    
    item_name, item_type, item_value = item
    
    if item_type.lower() == 'weapon':
        # Применение оружия (увеличивает урон игрока)
        c.execute('UPDATE players SET damage = damage + ? WHERE user_id = ?', (item_value, user_id))
        c.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
        conn.commit()
        await callback.message.edit_text(f"Вы экипировали {item_name}! ⚔️ Урон увеличен на {item_value}.", parse_mode='Markdown')
        logger.info(f"Пользователь {user_id} использовал {item_name}, урон увеличен на {item_value}")
    else:
        await callback.message.edit_text(f"Предмет {item_name} нельзя использовать.", reply_markup=None)
        logger.info(f"Пользователь {user_id} попытался использовать неподходящий предмет: {item_name}")
    
    conn.close()
    await callback.answer()