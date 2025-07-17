import sqlite3
import argparse

def get_db_connection():
    """Создаёт и возвращает соединение с базой данных."""
    conn = sqlite3.connect('game.db')
    conn.row_factory = sqlite3.Row
    return conn

def add_item(name, item_type, value, price):
    """Добавляет новый предмет в магазин."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO shop (item_name, item_type, item_value, price) VALUES (?, ?, ?, ?)',
              (name, item_type, value, price))
    conn.commit()
    conn.close()
    print(f"Предмет '{name}' добавлен в магазин (тип: {item_type}, значение: {value}, цена: {price})")

def add_enemy(name, health, damage, defense):
    """Добавляет нового врага."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO enemies (name, health, damage, defense) VALUES (?, ?, ?, ?)',
              (name, health, damage, defense))
    conn.commit()
    conn.close()
    print(f"Враг '{name}' добавлен (здоровье: {health}, урон: {damage}, защита: {defense})")

def list_items():
    """Выводит список всех предметов в магазине."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT item_id, item_name, item_type, item_value, price FROM shop')
    items = c.fetchall()
    conn.close()
    if not items:
        print("Магазин пуст.")
        return
    print("Предметы в магазине:")
    for item in items:
        print(f"ID: {item['item_id']}, Название: {item['item_name']}, Тип: {item['item_type']}, Значение: {item['item_value']}, Цена: {item['price']}")

def list_enemies():
    """Выводит список всех врагов."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT enemy_id, name, health, damage, defense FROM enemies')
    enemies = c.fetchall()
    conn.close()
    if not enemies:
        print("Враги не найдены.")
        return
    print("Враги:")
    for enemy in enemies:
        print(f"ID: {enemy['enemy_id']}, Название: {enemy['name']}, Здоровье: {enemy['health']}, Урон: {enemy['damage']}, Защита: {enemy['defense']}")

def delete_item(item_id):
    """Удаляет предмет из магазина по ID."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM shop WHERE item_id = ?', (item_id,))
    if c.rowcount == 0:
        print(f"Предмет с ID {item_id} не найден.")
    else:
        conn.commit()
        print(f"Предмет с ID {item_id} удалён.")
    conn.close()

def delete_enemy(enemy_id):
    """Удаляет врага по ID."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM enemies WHERE enemy_id = ?', (enemy_id,))
    if c.rowcount == 0:
        print(f"Враг с ID {enemy_id} не найден.")
    else:
        conn.commit()
        print(f"Враг с ID {enemy_id} удалён.")
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Утилита для управления предметами и врагами в игре Uneven Path")
    parser.add_argument('--add-item', nargs=4, metavar=('name', 'type', 'value', 'price'),
                        help="Добавить предмет: название, тип (weapon/potion/buff_potion), значение, цена")
    parser.add_argument('--add-enemy', nargs=4, metavar=('name', 'health', 'damage', 'defense'),
                        help="Добавить врага: название, здоровье, урон, защита")
    parser.add_argument('--list-items', action='store_true', help="Показать все предметы в магазине")
    parser.add_argument('--list-enemies', action='store_true', help="Показать всех врагов")
    parser.add_argument('--delete-item', type=int, help="Удалить предмет по ID")
    parser.add_argument('--delete-enemy', type=int, help="Удалить врага по ID")
    args = parser.parse_args()

    if args.add_item:
        name, item_type, value, price = args.add_item
        add_item(name, item_type, int(value), int(price))
    elif args.add_enemy:
        name, health, damage, defense = args.add_enemy
        add_enemy(name, int(health), int(damage), int(defense))
    elif args.list_items:
        list_items()
    elif args.list_enemies:
        list_enemies()
    elif args.delete_item:
        delete_item(args.delete_item)
    elif args.delete_enemy:
        delete_enemy(args.delete_enemy)
    else:
        parser.print_help()