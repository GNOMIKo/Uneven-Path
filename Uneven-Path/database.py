import sqlite3

def get_db_connection():
    """Создаёт и возвращает соединение с базой данных."""
    conn = sqlite3.connect('game.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализирует базу данных, создавая необходимые таблицы."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Таблица игроков
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            health INTEGER DEFAULT 100,
            damage INTEGER DEFAULT 10,
            defense INTEGER DEFAULT 5,
            gold INTEGER DEFAULT 50
        )
    ''')
    
    # Таблица инвентаря
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT NOT NULL,
            item_type TEXT NOT NULL,
            item_value INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    
    # Таблица магазина
    c.execute('''
        CREATE TABLE IF NOT EXISTS shop (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            item_type TEXT NOT NULL,
            item_value INTEGER NOT NULL,
            price INTEGER NOT NULL
        )
    ''')
    
    # Таблица врагов
    c.execute('''
        CREATE TABLE IF NOT EXISTS enemies (
            enemy_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            health INTEGER NOT NULL,
            damage INTEGER NOT NULL,
            defense INTEGER NOT NULL
        )
    ''')
    
    # Таблица отзывов
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT NOT NULL,
            feedback_text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    
    # Таблица активных эффектов
    c.execute('''
        CREATE TABLE IF NOT EXISTS active_effects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            effect_type TEXT NOT NULL,  -- 'damage_buff' или 'defense_buff'
            effect_value INTEGER NOT NULL,
            rounds_left INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    
    # Проверка и добавление начальных данных магазина
    c.execute('SELECT COUNT(*) FROM shop')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO shop (item_name, item_type, item_value, price) VALUES (?, ?, ?, ?)',
                  ('Iron Sword', 'weapon', 5, 30))
        c.execute('INSERT INTO shop (item_name, item_type, item_value, price) VALUES (?, ?, ?, ?)',
                  ('Health Potion', 'potion', 20, 15))
        c.execute('INSERT INTO shop (item_name, item_type, item_value, price) VALUES (?, ?, ?, ?)',
                  ('Strength Potion', 'buff_potion', 10, 20))  # Увеличивает урон на 10 на 3 раунда
        c.execute('INSERT INTO shop (item_name, item_type, item_value, price) VALUES (?, ?, ?, ?)',
                  ('Shield Potion', 'buff_potion', 8, 20))  # Увеличивает защиту на 8 на 3 раунда
    
    # Проверка и добавление начальных врагов
    c.execute('SELECT COUNT(*) FROM enemies')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO enemies (name, health, damage, defense) VALUES (?, ?, ?, ?)',
                  ('Гоблин', 30, 8, 2))
        c.execute('INSERT INTO enemies (name, health, damage, defense) VALUES (?, ?, ?, ?)',
                  ('Орк', 50, 12, 4))
    
    conn.commit()
    conn.close()