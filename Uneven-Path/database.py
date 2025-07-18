import sqlite3
import logging

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Создаёт и возвращает соединение с базой данных."""
    conn = sqlite3.connect('game.db')
    conn.row_factory = sqlite3.Row
    logger.debug("Установлено соединение с базой данных game.db")
    return conn

def init_db():
    """Инициализирует базу данных, создавая необходимые таблицы и добавляя начальные данные."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Проверка существования таблиц
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row['name'] for row in c.fetchall()]
    logger.info(f"Существующие таблицы в базе данных: {tables}")
    
    # Таблица игроков
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            strength INTEGER DEFAULT 10,
            agility INTEGER DEFAULT 10,
            intelligence INTEGER DEFAULT 10,
            health INTEGER DEFAULT 100,
            damage INTEGER DEFAULT 10,
            defense INTEGER DEFAULT 5,
            gold INTEGER DEFAULT 50,
            aegis INTEGER DEFAULT 3,
            debuff_end_time DATETIME,
            debuff_strength REAL DEFAULT 1.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_players_user_id ON players (user_id)')
    
    # Таблица навыков игрока
    c.execute('''
        CREATE TABLE IF NOT EXISTS player_skills (
            user_id INTEGER,
            skill_type TEXT NOT NULL,
            skill_points INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, skill_type),
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_player_skills_user_id ON player_skills (user_id)')
    
    # Таблица фракций
    c.execute('''
        CREATE TABLE IF NOT EXISTS factions (
            faction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            currency_id INTEGER,
            description TEXT,
            FOREIGN KEY (currency_id) REFERENCES currencies (currency_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_factions_region ON factions (region)')
    
    # Таблица репутации с фракциями
    c.execute('''
        CREATE TABLE IF NOT EXISTS player_factions (
            user_id INTEGER,
            faction_id INTEGER,
            reputation INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, faction_id),
            FOREIGN KEY (user_id) REFERENCES players (user_id),
            FOREIGN KEY (faction_id) REFERENCES factions (faction_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_player_factions_user_id ON player_factions (user_id)')
    
    # Таблица валют
    c.execute('''
        CREATE TABLE IF NOT EXISTS currencies (
            currency_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            region TEXT NOT NULL
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_currencies_region ON currencies (region)')
    
    # Таблица инвентаря
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_name TEXT NOT NULL,
            item_type TEXT NOT NULL,
            item_value INTEGER NOT NULL,
            durability INTEGER DEFAULT 100,
            rarity TEXT DEFAULT 'common',
            req_strength INTEGER DEFAULT 0,
            req_agility INTEGER DEFAULT 0,
            req_intelligence INTEGER DEFAULT 0,
            damage_type TEXT,
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_inventory_user_id ON inventory (user_id)')
    
    # Таблица магазина
    c.execute('''
        CREATE TABLE IF NOT EXISTS shop (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            item_type TEXT NOT NULL,
            item_value INTEGER NOT NULL,
            price INTEGER NOT NULL,
            currency_id INTEGER,
            faction_id INTEGER,
            durability INTEGER DEFAULT 100,
            rarity TEXT DEFAULT 'common',
            req_strength INTEGER DEFAULT 0,
            req_agility INTEGER DEFAULT 0,
            req_intelligence INTEGER DEFAULT 0,
            damage_type TEXT,
            FOREIGN KEY (currency_id) REFERENCES currencies (currency_id),
            FOREIGN KEY (faction_id) REFERENCES factions (faction_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_shop_currency_id ON shop (currency_id)')
    
    # Таблица врагов
    c.execute('''
        CREATE TABLE IF NOT EXISTS enemies (
            enemy_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            health INTEGER NOT NULL,
            damage INTEGER NOT NULL,
            defense INTEGER NOT NULL,
            location TEXT NOT NULL,
            damage_type TEXT,
            weakness_type TEXT,
            is_boss BOOLEAN DEFAULT FALSE,
            level INTEGER DEFAULT 1
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_enemies_location ON enemies (location)')
    
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
            effect_type TEXT NOT NULL,
            effect_value INTEGER NOT NULL,
            rounds_left INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_active_effects_user_id ON active_effects (user_id)')
    
    # Таблица квестов
    c.execute('''
        CREATE TABLE IF NOT EXISTS quests (
            quest_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            goal_type TEXT NOT NULL,
            goal_value INTEGER NOT NULL,
            reward_gold INTEGER DEFAULT 0,
            reward_currency_id INTEGER,
            reward_item_id INTEGER,
            reward_reputation INTEGER DEFAULT 0,
            faction_id INTEGER,
            type TEXT NOT NULL,
            level_required INTEGER DEFAULT 1,
            FOREIGN KEY (reward_currency_id) REFERENCES currencies (currency_id),
            FOREIGN KEY (reward_item_id) REFERENCES shop (item_id),
            FOREIGN KEY (faction_id) REFERENCES factions (faction_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_quests_type ON quests (type)')
    
    # Таблица прогресса квестов
    c.execute('''
        CREATE TABLE IF NOT EXISTS player_quests (
            user_id INTEGER,
            quest_id INTEGER,
            status TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            choice_made TEXT,
            PRIMARY KEY (user_id, quest_id),
            FOREIGN KEY (user_id) REFERENCES players (user_id),
            FOREIGN KEY (quest_id) REFERENCES quests (quest_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_player_quests_user_id ON player_quests (user_id)')
    
    # Таблица убежища
    c.execute('''
        CREATE TABLE IF NOT EXISTS shelters (
            shelter_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            owner_type TEXT NOT NULL,
            style TEXT DEFAULT 'basic',
            storage_capacity INTEGER DEFAULT 10,
            health_regen_bonus REAL DEFAULT 0.0,
            FOREIGN KEY (owner_id) REFERENCES players (user_id) ON DELETE CASCADE,
            FOREIGN KEY (owner_id) REFERENCES guilds (guild_id) ON DELETE CASCADE
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_shelters_owner_id ON shelters (owner_id)')
    
    # Таблица гильдий
    c.execute('''
        CREATE TABLE IF NOT EXISTS guilds (
            guild_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            leader_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            storage_capacity INTEGER DEFAULT 20,
            bonus_type TEXT,
            bonus_value REAL DEFAULT 0.0,
            FOREIGN KEY (leader_id) REFERENCES players (user_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_guilds_leader_id ON guilds (guild_id)')
    
    # Таблица участников гильдий
    c.execute('''
        CREATE TABLE IF NOT EXISTS guild_members (
            guild_id INTEGER,
            user_id INTEGER,
            role TEXT DEFAULT 'member',
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (guild_id, user_id),
            FOREIGN KEY (guild_id) REFERENCES guilds (guild_id),
            FOREIGN KEY (user_id) REFERENCES players (user_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_guild_members_user_id ON guild_members (user_id)')
    
    # Таблица рынка
    c.execute('''
        CREATE TABLE IF NOT EXISTS market (
            listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_id INTEGER,
            price INTEGER NOT NULL,
            currency_id INTEGER,
            listed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES players (user_id),
            FOREIGN KEY (item_id) REFERENCES inventory (id),
            FOREIGN KEY (currency_id) REFERENCES currencies (currency_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_market_user_id ON market (user_id)')
    
    # Таблица контрактов наёмников
    c.execute('''
        CREATE TABLE IF NOT EXISTS mercenary_contracts (
            contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            mercenary_id INTEGER,
            employer_id INTEGER,
            task_type TEXT NOT NULL,
            duration INTEGER NOT NULL,
            price INTEGER NOT NULL,
            currency_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (mercenary_id) REFERENCES players (user_id),
            FOREIGN KEY (employer_id) REFERENCES players (user_id),
            FOREIGN KEY (currency_id) REFERENCES currencies (currency_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_mercenary_contracts_mercenary_id ON mercenary_contracts (mercenary_id)')
    
    # Таблица достижений
    c.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            goal_type TEXT NOT NULL,
            goal_value INTEGER NOT NULL,
            reward_gold INTEGER DEFAULT 0,
            reward_currency_id INTEGER,
            reward_item_id INTEGER,
            reward_reputation INTEGER DEFAULT 0,
            FOREIGN KEY (reward_currency_id) REFERENCES currencies (currency_id),
            FOREIGN KEY (reward_item_id) REFERENCES shop (item_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_achievements_goal_type ON achievements (goal_type)')
    
    # Таблица прогресса достижений
    c.execute('''
        CREATE TABLE IF NOT EXISTS player_achievements (
            user_id INTEGER,
            achievement_id INTEGER,
            progress INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            completed_at DATETIME,
            PRIMARY KEY (user_id, achievement_id),
            FOREIGN KEY (user_id) REFERENCES players (user_id),
            FOREIGN KEY (achievement_id) REFERENCES achievements (achievement_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_player_achievements_user_id ON player_achievements (user_id)')
    
    # Таблица динамических событий
    c.execute('''
        CREATE TABLE IF NOT EXISTS dynamic_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            location TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            type TEXT NOT NULL,
            reward_gold INTEGER DEFAULT 0,
            reward_currency_id INTEGER,
            reward_item_id INTEGER,
            FOREIGN KEY (reward_currency_id) REFERENCES currencies (currency_id),
            FOREIGN KEY (reward_item_id) REFERENCES shop (item_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_dynamic_events_location ON dynamic_events (location)')
    
    # Таблица погоды
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            location TEXT PRIMARY KEY,
            weather_type TEXT NOT NULL,
            effect_type TEXT,
            effect_value REAL DEFAULT 0.0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_weather_location ON weather (location)')
    
    # Таблица ролей в рейдах
    c.execute('''
        CREATE TABLE IF NOT EXISTS raid_roles (
            raid_id INTEGER,
            user_id INTEGER,
            role TEXT NOT NULL,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (raid_id, user_id),
            FOREIGN KEY (user_id) REFERENCES players (user_id),
            FOREIGN KEY (raid_id) REFERENCES dynamic_events (event_id)
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_raid_roles_user_id ON raid_roles (user_id)')
    
    # Проверка и добавление начальных данных валют
    c.execute('SELECT COUNT(*) FROM currencies')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO currencies (name, region) VALUES (?, ?)', ('Золотые монеты', 'forest'))
        c.execute('INSERT INTO currencies (name, region) VALUES (?, ?)', ('Кристаллы', 'mountain'))
        c.execute('INSERT INTO currencies (name, region) VALUES (?, ?)', ('Песочные жемчужины', 'desert'))
        c.execute('INSERT INTO currencies (name, region) VALUES (?, ?)', ('Болотные талисманы', 'swamp'))
        logger.info("Добавлены начальные валюты")
    
    # Проверка и добавление начальных данных фракций
    c.execute('SELECT COUNT(*) FROM factions')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO factions (name, region, currency_id, description) VALUES (?, ?, ?, ?)',
                  ('Лесной союз', 'forest', 1, 'Фракция лесных жителей, торгующих древесиной и травами'))
        c.execute('INSERT INTO factions (name, region, currency_id, description) VALUES (?, ?, ?, ?)',
                  ('Горные кланы', 'mountain', 2, 'Горняки, добывающие кристаллы и металлы'))
        logger.info("Добавлены начальные фракции")
    
    # Проверка и добавление начальных данных магазина
    c.execute('SELECT COUNT(*) FROM shop')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO shop (item_name, item_type, item_value, price, currency_id, durability, rarity, req_strength, damage_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  ('Iron Sword', 'weapon', 5, 30, 1, 100, 'common', 5, 'physical'))
        c.execute('INSERT INTO shop (item_name, item_type, item_value, price, currency_id, durability, rarity, req_intelligence, damage_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  ('Health Potion', 'potion', 20, 15, 1, 100, 'common', None, None))
        c.execute('INSERT INTO shop (item_name, item_type, item_value, price, currency_id, durability, rarity, req_intelligence, damage_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  ('Fire Spell', 'spell', 15, 25, 2, 100, 'rare', 10, 'fire'))
        logger.info("Добавлены начальные предметы в магазин")
    
    # Проверка и добавление начальных врагов
    c.execute('SELECT COUNT(*) FROM enemies')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO enemies (name, health, damage, defense, location, damage_type, weakness_type, level) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                  ('Гоблин', 30, 8, 2, 'forest', 'physical', 'fire', 1))
        c.execute('INSERT INTO enemies (name, health, damage, defense, location, damage_type, weakness_type, level, is_boss) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  ('Орк', 50, 12, 4, 'forest', 'physical', 'water', 2, 0))
        c.execute('INSERT INTO enemies (name, health, damage, defense, location, damage_type, weakness_type, level, is_boss) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  ('Песочный дракон', 200, 20, 10, 'desert', 'fire', 'water', 5, 1))
        logger.info("Добавлены начальные враги")
    
    # Проверка и добавление начальных квестов
    c.execute('SELECT COUNT(*) FROM quests')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO quests (name, description, goal_type, goal_value, reward_gold, reward_currency_id, reward_reputation, type, level_required) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  ('Охота на гоблинов', 'Убейте 10 гоблинов в лесу.', 'kill_enemy', 10, 50, 1, 20, 'side', 1))
        c.execute('INSERT INTO quests (name, description, goal_type, goal_value, reward_gold, reward_currency_id, reward_reputation, type, level_required, faction_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  ('Древний артефакт', 'Найдите артефакт в горных руинах.', 'collect_item', 1, 100, 2, 50, 'main', 3, 2))
        logger.info("Добавлены начальные квесты")
    
    # Проверка и добавление начальных достижений
    c.execute('SELECT COUNT(*) FROM achievements')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO achievements (name, description, goal_type, goal_value, reward_gold, reward_currency_id, reward_reputation) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  ('Истребитель гоблинов', 'Убейте 100 гоблинов.', 'kill_enemy', 100, 200, 1, 50))
        c.execute('INSERT INTO achievements (name, description, goal_type, goal_value, reward_item_id, reward_reputation) VALUES (?, ?, ?, ?, ?, ?)',
                  ('Мастер меча', 'Используйте 10 мечей.', 'use_item', 10, 1, 30))
        logger.info("Добавлены начальные достижения")
    
    # Проверка и добавление начальной погоды
    c.execute('SELECT COUNT(*) FROM weather')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO weather (location, weather_type, effect_type, effect_value) VALUES (?, ?, ?, ?)',
                  ('forest', 'clear', None, 0.0))
        c.execute('INSERT INTO weather (location, weather_type, effect_type, effect_value) VALUES (?, ?, ?, ?)',
                  ('desert', 'storm', 'reduced_accuracy', 0.2))
        logger.info("Добавлена начальная погода")
    
    # Проверка содержимого инвентаря для пользователя 847381967
    c.execute('SELECT * FROM inventory WHERE user_id = ?', (847381967,))
    inventory_items = c.fetchall()
    logger.info(f"Содержимое инвентаря пользователя 847381967: {[(item['id'], item['item_name'], item['item_type'], item['item_value']) for item in inventory_items]}")
    
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")