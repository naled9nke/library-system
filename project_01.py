import sqlite3
import sys

# Инициализация базы данных SQLite (файл создастся автоматически)
def init_db():
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()
    
    # Таблица пользователей (сотрудники и читатели)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL -- 'admin', 'librarian', 'client'
        )
    """)
    
    # Таблица книг
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT NOT NULL,
            copies INTEGER NOT NULL
        )
    """)
    
    # Таблица выдачи книг (заказы)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            user_id INTEGER,
            status TEXT NOT NULL, -- 'issued' (выдана), 'returned' (возвращена)
            FOREIGN KEY (book_id) REFERENCES books (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Заполним тестовыми данными, если таблицы пустые
    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] == 0:
        sample_books = [
            ("Война и мир", "Л.Н. Толстой", "Роман", 3),
            ("Преступление и наказание", "Ф.М. Достоевский", "Классика", 2),
            ("Мастер и Маргарита", "М.А. Булгаков", "Фантастика", 5),
            ("1984", "Джордж Оруэлл", "Антиутопия", 4),
            ("Гарри Поттер и философский камень", "Дж. К. Роулинг", "Фэнтези", 6),
            ("Властелин Колец", "Дж. Р. Р. Толкин", "Фэнтези", 2),
            ("Мертвые души", "Н.В. Гоголь", "Поэма", 3),
            ("Евгений Онегин", "А.С. Пушкин", "Классика", 4),
            ("Отцы и дети", "И.С. Тургенев", "Роман", 3),
            ("Вишневый сад", "А.П. Чехов", "Пьеса", 2)
        ]
        cursor.executemany("INSERT INTO books (title, author, genre, copies) VALUES (?, ?, ?, ?)", sample_books)
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        sample_users = [
            ("admin", "1234", "admin"),
            ("librarian", "1234", "librarian"),
            ("ivanov", "1234", "client"),
            ("petrov", "1234", "client")
        ]
        cursor.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", sample_users)
        
    conn.commit()
    conn.close()

# Функция авторизации
def login():
    print("=== АВТОРИЗАЦИЯ В ИС 'БИБЛИОТЕКА' ===")
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()
    
    while True:
        username = input("Логин: ").strip()
        password = input("Пароль: ").strip()
        
        cursor.execute("SELECT id, role FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        
        if user:
            print(f"\n Успешный вход! Ваша роль: {user[1].upper()}")
            conn.close()
            return user[0], user[1] # возвращает id и роль
        else:
            print(" Неверный логин или пароль. Попробуйте снова.")

# Просмотр каталога
def view_books():
    conn = sqlite3.connect("library.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    conn.close()
    
    print("\n--- КАТАЛОГ КНИГ ---")
    print(f"{'ID':<4} | {'Название':<32} | {'Автор':<22} | {'Жанр':<15} | {'Остаток'}")
    print("-" * 85)
    for b in books:
        print(f"{b[0]:<4} | {b[1]:<32} | {b[2]:<22} | {b[3]:<15} | {b[4]}")
    print("-" * 85)

# Добавление книги (Админ / Библиотекарь)
def add_book():
    print("\n--- ДОБАВЛЕНИЕ НОВОЙ КНИГИ ---")
    title = input("Название книги: ")
    author = input("Автор: ")
    genre = input("Жанр: ")
    try:
        copies = int(input("Количество экземпляров: "))
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO books (title, author, genre, copies) VALUES (?, ?, ?, ?)", (title, author, genre, copies))
        conn.commit()
        conn.close()
        print(" Книга успешно добавлена в каталог!")
    except ValueError:
        print(" Ошибка: количество экземпляров должно быть числом.")

# Удаление книги
def delete_book():
    view_books()
    try:
        book_id = int(input("\nВведите ID книги для удаления: "))
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        conn.close()
        print(" Книга удалена.")
    except ValueError:
        print(" Ошибка ввода.")

# Выдача книги
def issue_book(user_id):
    view_books()
    try:
        book_id = int(input("\nВведите ID книги, которую хотите взять: "))
        conn = sqlite3.connect("library.db")
        cursor = conn.cursor()
        
        # Проверяем остаток
        cursor.execute("SELECT copies FROM books WHERE id = ?", (book_id,))
        res = cursor.fetchone()
        if res and res[0] > 0:
            cursor.execute("UPDATE books SET copies = copies - 1 WHERE id = ?", (book_id,))
            cursor.execute("INSERT INTO loans (book_id, user_id, status) VALUES (?, ?, 'issued')", (book_id, user_id))
            conn.commit()
            print(" Книга успешно выдана!")
        else:
            print(" К сожалению, этой книги нет в наличии.")
        conn.close()
    except ValueError:
        print(" Ошибка ввода ID.")

# Главный цикл программы
def main():
    init_db()
    user_id, role = login()
    
    while True:
        print("\n================ МЕНЮ ================")
        print("1. Посмотреть каталог книг")
        if role in ['admin', 'librarian']:
            print("2. Добавить новую книгу")
            print("3. Удалить книгу")
        print("4. Взять книгу (оформить выдачу)")
        print("5. Выход")
        
        choice = input("Выберите пункт меню: ").strip()
        
        if choice == '1':
            view_books()
        elif choice == '2' and role in ['admin', 'librarian']:
            add_book()
        elif choice == '3' and role in ['admin', 'librarian']:
            delete_book()
        elif choice == '4':
            issue_book(user_id)
        elif choice == '5':
            print("До свидания!")
            sys.exit()
        else:
            print(" Неверный выбор или недостаточно прав.")

if __name__ == "__main__":
    main()