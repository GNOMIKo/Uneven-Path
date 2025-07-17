import sqlite3

def init_db():
    """Инициализация базы данных SQLite с таблицами для игроков, инвентаря, врагов и магазина."""
    conn = sqlite3.connect('rpg_game.db')
    c = conn.cursor()
    
    # Таблица игроков: хранит данные пользователя
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
    
    # Таблица инвентаря: хранит предметы игрока
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT,
            item_type TEXT,  -- например, weapon, potion
            item_value INTEGER,  -- например, урон для оружия, лечение для зелий
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    
    # Таблица врагов: хранит данные врагов
    c.execute('''
        CREATE TABLE IF NOT EXISTS enemies (
            enemy_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,  -- Уникальное имя врага
            health INTEGER,
            damage INTEGER,
            defense INTEGER
        )
    ''')
    # Вставка тестового врага (Гоблин), избегаем дублирования
    c.execute('INSERT OR IGNORE INTO enemies (name, health, damage, defense) VALUES (?, ?, ?, ?)',
              ('Goblin', 50, 8, 3))
    
    # Таблица магазина: хранит предметы для покупки
    c.execute('''
        CREATE TABLE IF NOT EXISTS shop (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT UNIQUE,  -- Уникальное имя предмета
            item_type TEXT,
            item_value INTEGER,
            price INTEGER
        )
    ''')
    # Вставка тестовых предметов в магазин, избегаем дублирования
    c.execute('INSERT OR IGNORE INTO shop (item_name, item_type, item_value, price) VALUES (?, ?, ?, ?)',
              ('Iron Sword', 'weapon', 5, 30))
    c.execute('INSERT OR IGNORE INTO shop (item_name, item_type, item_value, price) VALUES (?, ?, ?, ?)',
              ('Health Potion', 'potion', 20, 20))
    
    # Таблица эффектов: для будущих баффов/дебаффов
    c.execute('''
        CREATE TABLE IF NOT EXISTS effects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            effect_name TEXT,
            effect_type TEXT,  -- например, buff, debuff
            effect_value INTEGER,  -- например, +10 урона
            duration INTEGER,  -- количество ходов или времени
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Возвращает новое соединение с базой данных SQLite."""
    return sqlite3.connect('rpg_game.db')