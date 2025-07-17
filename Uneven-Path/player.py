from aiogram import types
from database import get_db_connection

async def handle_start(message: types.Message):
    """Handle /start command: register new player or welcome returning player."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
    if not c.fetchone():
        # Register new player
        c.execute('INSERT INTO players (user_id, username, health, damage, defense, gold) VALUES (?, ?, ?, ?, ?, ?)',
                  (user_id, username, 100, 10, 5, 50))
        conn.commit()
        await message.answer(f"Welcome, {username}! You are now an adventurer. Use /profile to see your stats.")
    else:
        await message.answer(f"Welcome back, {username}! Ready to adventure? Use /profile to check your stats.")
    conn.close()

async def handle_profile(message: types.Message):
    """Handle /profile command: display player stats."""
    user_id = message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT username, health, damage, defense, gold FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    if player:
        username, health, damage, defense, gold = player
        profile_text = (
            f"🧙‍♂️ *{username}*\n"
            f"❤️ Health: {health}\n"
            f"⚔️ Damage: {damage}\n"
            f"🛡️ Defense: {defense}\n"
            f"💰 Gold: {gold}"
        )
        await message.answer(profile_text, parse_mode='Markdown')
    else:
        await message.answer("You are not registered. Use /start to begin.")
    conn.close()