import sqlite3

def init_db():
    """Initialize SQLite database with tables for players, inventory, enemies, and shop."""
    conn = sqlite3.connect('rpg_game.db')
    c = conn.cursor()
    
    # Players table: stores user data
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            health INTEGER DEFAULT 100,
            damage INTEGER DEFAULT 10,
            defense INTEGER DEFAULT 5,
            gold INTEGER DEFAULT 50
        )
    ''')
    
    # Inventory table: stores player items
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT,
            item_type TEXT,  -- e.g., weapon, potion
            item_value INTEGER,  -- e.g., damage for weapons, healing for potions
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    
    # Enemies table: stores enemy data
    c.execute('''
        CREATE TABLE IF NOT EXISTS enemies (
            enemy_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            health INTEGER,
            damage INTEGER,
            defense INTEGER
        )
    ''')
    # Insert sample enemy (Goblin)
    c.execute('INSERT OR IGNORE INTO enemies (enemy_id, name, health, damage, defense) VALUES (?, ?, ?, ?, ?)',
              (1, 'Goblin', 50, 8, 3))
    
    # Shop table: stores items available for purchase
    c.execute('''
        CREATE TABLE IF NOT EXISTS shop (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            item_type TEXT,
            item_value INTEGER,
            price INTEGER
        )
    ''')
    # Insert sample shop items
    c.execute('INSERT OR IGNORE INTO shop (item_name, item_type, item_value, price) VALUES (?, ?, ?, ?)',
              ('Iron Sword', 'weapon', 5, 30))
    c.execute('INSERT OR IGNORE INTO shop (item_name, item_type, item_value, price) VALUES (?, ?, ?, ?)',
              ('Health Potion', 'potion', 20, 20))
    
    # Effects table: for future effects like buffs/debuffs
    c.execute('''
        CREATE TABLE IF NOT EXISTS effects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            effect_name TEXT,
            effect_type TEXT,  -- e.g., buff, debuff
            effect_value INTEGER,  -- e.g., +10 damage
            duration INTEGER,  -- turns or time remaining
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Return a new SQLite connection."""
    return sqlite3.connect('rpg_game.db')