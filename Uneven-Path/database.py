import sqlite3

def get_db_connection():
    """Устанавливает соединение с базой данных."""
    return sqlite3.connect('game.db')

def init_db():
    """Инициализирует базу данных с таблицами и обновляет структуру при необходимости."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Проверка и создание таблицы players с добавлением max_health, если его нет
    c.execute("PRAGMA table_info(players)")
    columns = [col[1] for col in c.fetchall()]
    if 'max_health' not in columns:
        c.execute('ALTER TABLE players ADD COLUMN max_health INTEGER DEFAULT 100')
        # Обновление существующих записей
        c.execute("UPDATE players SET max_health = 100 WHERE max_health IS NULL")
    
    # Полное определение таблицы players на случай новой базы
    c.execute('''CREATE TABLE IF NOT EXISTS players
                 (user_id INTEGER PRIMARY KEY, health INTEGER, max_health INTEGER, damage INTEGER, defense INTEGER, gold INTEGER)''')
    
    # Таблица врагов
    c.execute('''CREATE TABLE IF NOT EXISTS enemies
                 (enemy_id INTEGER PRIMARY KEY, name TEXT, health INTEGER, damage INTEGER, defense INTEGER)''')
    
    # Таблица инвентаря
    c.execute('''CREATE TABLE IF NOT EXISTS inventory
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, item_name TEXT, item_type TEXT, item_value INTEGER)''')
    
    # Таблица активных эффектов
    c.execute('''CREATE TABLE IF NOT EXISTS active_effects
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, effect_type TEXT, effect_value INTEGER, rounds_left INTEGER)''')
    
    conn.commit()
    conn.close()