from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_connection
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_shop(message: types.Message):
    """Обрабатывает команду /shop: показывает товары в магазине."""
    user_id = message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    
    # Проверка существования таблицы shop
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shop'")
    if not c.fetchone():
        logger.error("Таблица shop не существует в базе данных")
        await message.answer("Ошибка: магазин недоступен. Обратитесь к администратору.", reply_markup=None)
        conn.close()
        return
    
    # Получение товаров из магазина
    c.execute('SELECT item_id, item_name, item_type, item_value, price FROM shop')
    items = c.fetchall()
    logger.debug(f"Товары в магазине: {[(item['item_id'], item['item_name'], item['item_type'], item['item_value'], item['price']) for item in items]}")
    
    if not items:
        await message.answer("Магазин пуст!", reply_markup=None)
        conn.close()
        return
    
    # Получение золота игрока
    c.execute('SELECT gold FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    if not player:
        await message.answer("Вы не зарегистрированы. Используйте /start.", reply_markup=None)
        conn.close()
        return
    gold = player['gold']
    
    # Создание инлайн-клавиатуры
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for item in items:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{item['item_name']} (+{item['item_value']}) - {item['price']} золота",
                callback_data=f"buy_{item['item_id']}"
            )
        ])
    
    await message.answer(f"🏪 *Магазин*\nВаше золото: {gold}\n\nВыберите предмет для покупки:", reply_markup=keyboard, parse_mode='Markdown')
    logger.info(f"Показываю магазин для пользователя {user_id}: {len(items)} предметов")
    conn.close()

async def handle_buy(callback: types.CallbackQuery):
    """Обрабатывает покупку предмета из магазина."""
    user_id = callback.from_user.id
    item_id = int(callback.data.split('_')[1])
    conn = get_db_connection()
    c = conn.cursor()
    
    # Получение информации о предмете
    c.execute('SELECT item_name, item_type, item_value, price FROM shop WHERE item_id = ?', (item_id,))
    item = c.fetchone()
    if not item:
        await callback.message.edit_text("Предмет не найден.", reply_markup=None)
        logger.error(f"Предмет с ID {item_id} не найден для пользователя {user_id}")
        conn.close()
        await callback.answer()
        return
    item_name, item_type, item_value, price = item
    
    # Получение золота игрока
    c.execute('SELECT gold FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    if not player:
        await callback.message.edit_text("Вы не зарегистрированы. Используйте /start.", reply_markup=None)
        conn.close()
        await callback.answer()
        return
    gold = player['gold']
    
    if gold < price:
        await callback.message.edit_text(f"Недостаточно золота! Нужно: {price}, у вас: {gold}.", reply_markup=None)
        logger.info(f"У пользователя {user_id} недостаточно золота для покупки {item_name}: {gold} < {price}")
        conn.close()
        await callback.answer()
        return
    
    # Покупка предмета
    c.execute('UPDATE players SET gold = gold - ? WHERE user_id = ?', (price, user_id))
    c.execute('INSERT INTO inventory (user_id, item_name, item_type, item_value) VALUES (?, ?, ?, ?)',
              (user_id, item_name, item_type, item_value))
    conn.commit()
    
    # Проверка добавленного предмета
    c.execute('SELECT id, item_name, item_type, item_value FROM inventory WHERE user_id = ? AND item_name = ?',
              (user_id, item_name))
    added_item = c.fetchone()
    logger.debug(f"Добавлен предмет в инвентарь пользователя {user_id}: {added_item['id'], added_item['item_name'], added_item['item_type'], added_item['item_value']}")
    
    await callback.message.edit_text(f"Вы купили {item_name} за {price} золота!", reply_markup=None)
    logger.info(f"Пользователь {user_id} купил {item_name} за {price} золота")
    conn.close()
    await callback.answer()