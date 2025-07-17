from aiogram import types
from database import get_db_connection

async def handle_inventory(message: types.Message):
    """Handle /inventory command: display player's items."""
    user_id = message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT item_name, item_type, item_value FROM inventory WHERE user_id = ?', (user_id,))
    items = c.fetchall()
    if not items:
        await message.answer("Your inventory is empty.")
    else:
        inventory_text = "🎒 *Inventory:*\n"
        for item in items:
            item_name, item_type, item_value = item
            inventory_text += f"- {item_name} ({item_type}, +{item_value})\n"
        await message.answer(inventory_text, parse_mode='Markdown')
    conn.close()