from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import get_db_connection
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_shop(message: types.Message):
    """Обрабатывает команду /shop: показывает доступные предметы для покупки."""
    user_id = message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT item_id, item_name, item_type, item_value, price FROM shop')
    items = c.fetchall()
    
    # Проверка, что предметы найдены
    if not items:
        await message.answer("Магазин пуст! Попробуйте позже.")
        conn.close()
        return
    
    # Создание инлайн-клавиатуры
    keyboard = InlineKeyboardBuilder()
    for item in items:
        item_id, item_name, item_type, item_value, price = item
        keyboard.button(text=f"{item_name} ({price} золота)", callback_data=f"buy_{item_id}")
    keyboard.adjust(1)
    
    # Логирование для отладки
    logger.info(f"Показываю магазин для пользователя {user_id}: {len(items)} предметов")
    
    await message.answer(
        "🏪 *Магазин:*\nВыберите предмет для покупки:",
        reply_markup=keyboard.as_markup(),
        parse_mode='Markdown'
    )
    conn.close()

async def handle_buy_item(callback: types.CallbackQuery):
    """Обрабатывает покупку предмета из магазина."""
    user_id = callback.from_user.id
    item_id = int(callback.data.split('_')[1])
    conn = get_db_connection()
    c = conn.cursor()
    
    # Получение золота игрока
    c.execute('SELECT gold FROM players WHERE user_id = ?', (user_id,))
    player_gold = c.fetchone()
    if not player_gold:
        await callback.message.answer("Вы не зарегистрированы. Используйте /start.")
        conn.close()
        await callback.answer()
        return
    player_gold = player_gold[0]
    
    # Получение данных о предмете
    c.execute('SELECT item_name, item_type, item_value, price FROM shop WHERE item_id = ?', (item_id,))
    item = c.fetchone()
    if item:
        item_name, item_type, item_value, price = item
        if player_gold >= price:
            # Вычитаем золото
            c.execute('UPDATE players SET gold = gold - ? WHERE user_id = ?', (price, user_id))
            # Добавляем предмет в инвентарь
            c.execute('INSERT INTO inventory (user_id, item_name, item_type, item_value) VALUES (?, ?, ?, ?)',
                      (user_id, item_name, item_type, item_value))
            conn.commit()
            await callback.message.answer(f"Вы купили {item_name} за {price} золота!")
            logger.info(f"Пользователь {user_id} купил {item_name} за {price} золота")
        else:
            await callback.message.answer("Недостаточно золота!")
            logger.warning(f"Пользователь {user_id} пытался купить {item_name}, но не хватило золота")
    else:
        await callback.message.answer("Предмет не найден.")
        logger.error(f"Предмет с ID {item_id} не найден для пользователя {user_id}")
    
    conn.close()
    await callback.answer()