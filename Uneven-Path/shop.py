from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import get_db_connection

async def handle_shop(message: types.Message):
    """Handle /shop command: display available items for purchase."""
    user_id = message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT item_id, item_name, item_type, item_value, price FROM shop')
    items = c.fetchall()
    keyboard = InlineKeyboardBuilder()
    for item in items:
        item_id, item_name, item_type, item_value, price = item
        keyboard.button(text=f"{item_name} ({price} gold)", callback_data=f"buy_{item_id}")
    keyboard.adjust(1)
    await message.answer("🏪 *Shop:*\nChoose an item to buy:", reply_markup=keyboard.as_markup(), parse_mode='Markdown')
    conn.close()

async def handle_buy_item(callback: types.CallbackQuery):
    """Handle item purchase from shop."""
    user_id = callback.from_user.id
    item_id = int(callback.data.split('_')[1])
    conn = get_db_connection()
    c = conn.cursor()
    # Get player gold
    c.execute('SELECT gold FROM players WHERE user_id = ?', (user_id,))
    player_gold = c.fetchone()[0]
    # Get item details
    c.execute('SELECT item_name, item_type, item_value, price FROM shop WHERE item_id = ?', (item_id,))
    item = c.fetchone()
    if item:
        item_name, item_type, item_value, price = item
        if player_gold >= price:
            # Deduct gold
            c.execute('UPDATE players SET gold = gold - ? WHERE user_id = ?', (price, user_id))
            # Add item to inventory
            c.execute('INSERT INTO inventory (user_id, item_name, item_type, item_value) VALUES (?, ?, ?, ?)',
                      (user_id, item_name, item_type, item_value))
            conn.commit()
            await callback.message.answer(f"You bought {item_name} for {price} gold!")
        else:
            await callback.message.answer("Not enough gold!")
    conn.close()
    await callback.answer()