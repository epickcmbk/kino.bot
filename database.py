import sqlite3

DB_NAME = "kino.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Category table
    c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    # Movies table
    c.execute("""
        CREATE TABLE IF NOT EXISTS kino (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            code TEXT UNIQUE,
            category_id INTEGER,
            file_id TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    """)

    conn.commit()
    conn.close()


def add_category(name):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def get_categories():
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("SELECT id, name FROM categories").fetchall()
    conn.close()
    return rows


def add_movie(title, code, category_id, file_id):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        INSERT INTO kino (title, code, category_id, file_id)
        VALUES (?, ?, ?, ?)
    """, (title, code, category_id, file_id))
    conn.commit()
    conn.close()


def get_movies_by_category(category_id):
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("SELECT id, title FROM kino WHERE category_id=?", (category_id,)).fetchall()
    conn.close()
    return rows


def get_movie_by_code(code):
    conn = sqlite3.connect(DB_NAME)
    movie = conn.execute("SELECT title, file_id FROM kino WHERE code=?", (code,)).fetchone()
    conn.close()
    return movie
