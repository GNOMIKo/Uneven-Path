from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db_connection

async def handle_fight(message: types.Message):
    """Handle /fight command: start a battle against an enemy."""
    user_id = message.from_user.id
    conn = get_db_connection()
    c = conn.cursor()
    # Get player stats
    c.execute('SELECT health, damage, defense FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    if not player:
        await message.answer("You are not registered. Use /start to begin.")
        conn.close()
        return
    player_health, player_damage, player_defense = player
    # Get enemy stats (Goblin for MVP)
    c.execute('SELECT name, health, damage, defense FROM enemies WHERE enemy_id = ?', (1,))
    enemy = c.fetchone()
    enemy_name, enemy_health, enemy_damage, enemy_defense = enemy

    # Calculate damage
    damage_to_enemy = max(1, player_damage - enemy_defense)
    damage_to_player = max(1, enemy_damage - player_defense)

    # Start fight
    fight_text = (
        f"⚔️ *You face a {enemy_name}!*\n"
        f"Enemy HP: {enemy_health}\n"
        f"Your HP: {player_health}\n"
        f"What do you do?"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Attack", callback_data=f"fight_attack_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
        [InlineKeyboardButton(text="Flee", callback_data="fight_flee")]
    ])
    await message.answer(fight_text, reply_markup=keyboard, parse_mode='Markdown')
    conn.close()

async def handle_fight_action(callback: types.CallbackQuery):
    """Handle combat actions (attack or flee)."""
    user_id = callback.from_user.id
    action = callback.data.split('_')[1]
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT health FROM players WHERE user_id = ?', (user_id,))
    player_health = c.fetchone()[0]

    if action == 'flee':
        await callback.message.answer("You attempt to flee... Success!")
        conn.close()
        await callback.answer()
        return

    # Attack action
    enemy_health = int(callback.data.split('_')[2])
    damage_to_enemy = int(callback.data.split('_')[3])
    damage_to_player = int(callback.data.split('_')[4])

    # Update health
    enemy_health -= damage_to_enemy
    player_health -= damage_to_player

    if enemy_health <= 0:
        # Player wins
        c.execute('UPDATE players SET gold = gold + 20 WHERE user_id = ?', (user_id,))
        c.execute('UPDATE players SET health = ? WHERE user_id = ?', (player_health, user_id))
        conn.commit()
        await callback.message.answer("🎉 You defeated the Goblin! +20 gold")
        conn.close()
        await callback.answer()
        return

    if player_health <= 0:
        # Player loses
        c.execute('UPDATE players SET health = 50 WHERE user_id = ?', (user_id,))
        conn.commit()
        await callback.message.answer("💀 You were defeated! Health reset to 50.")
        conn.close()
        await callback.answer()
        return

    # Continue fight
    c.execute('UPDATE players SET health = ? WHERE user_id = ?', (player_health, user_id))
    conn.commit()
    fight_text = (
        f"⚔️ You deal {damage_to_enemy} damage to the Goblin!\n"
        f"Goblin deals {damage_to_player} damage to you!\n"
        f"Enemy HP: {enemy_health}\n"
        f"Your HP: {player_health}\n"
        f"What do you do?"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Attack", callback_data=f"fight_attack_{enemy_health}_{damage_to_enemy}_{damage_to_player}")],
        [InlineKeyboardButton(text="Flee", callback_data="fight_flee")]
    ])
    await callback.message.edit_text(fight_text, reply_markup=keyboard, parse_mode='Markdown')
    conn.close()
    await callback.answer()