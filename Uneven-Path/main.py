import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from config import API_TOKEN
from player import handle_start, handle_profile
from combat import handle_fight, handle_fight_action
from inventory import handle_inventory
from shop import handle_shop, handle_buy_item
from database import init_db

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Register handlers
def register_handlers():
    dp.message.register(handle_start, Command('start'))
    dp.message.register(handle_profile, Command('profile'))
    dp.message.register(handle_inventory, Command('inventory'))
    dp.message.register(handle_shop, Command('shop'))
    dp.message.register(handle_fight, Command('fight'))
    dp.callback_query.register(handle_fight_action, lambda c: c.data.startswith('fight_'))
    dp.callback_query.register(handle_buy_item, lambda c: c.data.startswith('buy_'))

async def main():
    # Initialize database
    init_db()
    # Register command and callback handlers
    register_handlers()
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())