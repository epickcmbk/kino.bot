import sqlite3
from config import DATABASE_NAME, ADMINS

conn = None

def get_connection():
    """Database ulanishini olish"""
    global conn
    if conn is None:
        conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
        conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Database jadvallarini yaratish"""
    cursor = get_connection().cursor()
    
    # Users jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            chat_id INTEGER UNIQUE,
            full_name TEXT,
            phone_number TEXT
        )
    ''')
    
    # Admins jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY
        )
    ''')
    
    # Kanallar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kanals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT UNIQUE,
            channel_url TEXT
        )
    ''')
    
    # Kategoriyalar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kategoryas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE
        )
    ''')
    
    # Kinolar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kinos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            code TEXT UNIQUE,
            category_id INTEGER,
            file_id TEXT,
            language TEXT,
            country TEXT,
            year INTEGER,
            FOREIGN KEY (category_id) REFERENCES kategoryas(id)
        )
    ''')
    
    # Obuna jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER,
            channel_id INTEGER,
            PRIMARY KEY (user_id, channel_id),
            FOREIGN KEY (channel_id) REFERENCES kanals(id)
        )
    ''')
    
    # Asosiy adminlarni qo'shish
    for admin_id in ADMINS:
        try:
            cursor.execute('INSERT OR IGNORE INTO admins (id) VALUES (?)', (admin_id,))
        except:
            pass
    
    get_connection().commit()

# ============ ADMIN FUNCTIONS ============

def add_admin(admin_id):
    """Admin qo'shish"""
    try:
        cursor = get_connection().cursor()
        cursor.execute('INSERT INTO admins (id) VALUES (?)', (admin_id,))
        get_connection().commit()
        return True
    except sqlite3.IntegrityError:
        return False

def remove_admin(admin_id):
    """Adminni o'chirish"""
    cursor = get_connection().cursor()
    cursor.execute('DELETE FROM admins WHERE id = ?', (admin_id,))
    get_connection().commit()
    return cursor.rowcount > 0

def get_admins():
    """Barcha adminlarni olish"""
    cursor = get_connection().cursor()
    cursor.execute('SELECT id FROM admins')
    return [row[0] for row in cursor.fetchall()]

# ============ CHANNEL FUNCTIONS ============

def add_channel(channel_name, channel_url):
    """Kanal qo'shish"""
    try:
        # URL'ni toza qilish - https:// bitta bo'lishi kerak
        channel_url = channel_url.strip()
        if not channel_url.startswith('http'):
            channel_url = 'https://' + channel_url
        
        cursor = get_connection().cursor()
        cursor.execute(
            'INSERT INTO kanals (channel_id, channel_url) VALUES (?, ?)',
            (channel_name, channel_url)
        )
        get_connection().commit()
        return True
    except sqlite3.IntegrityError:
        return False

def remove_channel(channel_name):
    """Kanalni o'chirish"""
    cursor = get_connection().cursor()
    cursor.execute('DELETE FROM kanals WHERE channel_id = ?', (channel_name,))
    get_connection().commit()
    return cursor.rowcount > 0

def get_all_channels():
    """Barcha kanallarni olish"""
    cursor = get_connection().cursor()
    cursor.execute('SELECT id, channel_id, channel_url FROM kanals')
    return cursor.fetchall()

def check_user_subscription(user_id, channel_id):
    """Foydalanuvchi kanalni obuna qilib olganini tekshirish"""
    cursor = get_connection().cursor()
    cursor.execute(
        'SELECT 1 FROM subscriptions WHERE user_id = ? AND channel_id = ?',
        (user_id, channel_id)
    )
    return cursor.fetchone() is not None

def add_subscription(user_id, channel_id):
    """Obunani qo'shish"""
    try:
        cursor = get_connection().cursor()
        cursor.execute(
            'INSERT INTO subscriptions (user_id, channel_id) VALUES (?, ?)',
            (user_id, channel_id)
        )
        get_connection().commit()
        return True
    except sqlite3.IntegrityError:
        return False

# ============ CATEGORY FUNCTIONS ============

def add_category(title):
    """Kategoriya qo'shish"""
    try:
        cursor = get_connection().cursor()
        cursor.execute('INSERT INTO kategoryas (title) VALUES (?)', (title,))
        get_connection().commit()
        return True
    except sqlite3.IntegrityError:
        return False

def remove_category(category_id):
    """Kategoriyani o'chirish"""
    cursor = get_connection().cursor()
    cursor.execute('DELETE FROM kategoryas WHERE id = ?', (category_id,))
    get_connection().commit()
    return cursor.rowcount > 0

def get_all_categories():
    """Barcha kategoriyalarni olish"""
    cursor = get_connection().cursor()
    cursor.execute('SELECT id, title FROM kategoryas')
    return cursor.fetchall()

def get_category_by_id(category_id):
    """ID bo'yicha kategoriya olish"""
    cursor = get_connection().cursor()
    cursor.execute('SELECT * FROM kategoryas WHERE id = ?', (category_id,))
    return cursor.fetchone()

# ============ MOVIE FUNCTIONS ============

def add_movie(title, code, category_id, year, language, country, file_id):
    """Kino qo'shish"""
    try:
        cursor = get_connection().cursor()
        cursor.execute(
            '''INSERT INTO kinos 
            (title, code, category_id, year, language, country, file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (title, code, category_id, year, language, country, file_id)
        )
        get_connection().commit()
        return True
    except sqlite3.IntegrityError:
        return False

def remove_movie(movie_id):
    """Kinoni o'chirish"""
    cursor = get_connection().cursor()
    cursor.execute('DELETE FROM kinos WHERE id = ?', (movie_id,))
    get_connection().commit()
    return cursor.rowcount > 0

def get_movies_by_category(category_id):
    """Kategoriya bo'yicha kinolarni olish"""
    cursor = get_connection().cursor()
    cursor.execute(
        'SELECT id, title, code FROM kinos WHERE category_id = ? ORDER BY title',
        (category_id,)
    )
    return cursor.fetchall()

def get_movie_details(movie_id):
    """Kino detallarini olish"""
    cursor = get_connection().cursor()
    cursor.execute(
        '''SELECT id, title, code, category_id, year, language, country, file_id 
        FROM kinos WHERE id = ?''',
        (movie_id,)
    )
    return cursor.fetchone()

def get_all_movies():
    """Barcha kinolarni olish"""
    cursor = get_connection().cursor()
    cursor.execute('SELECT id, title, code FROM kinos ORDER BY title')
    return cursor.fetchall()

# ============ USER FUNCTIONS ============

def add_user(user_id, username, full_name, phone_number=None):
    """Foydalanuvchini qo'shish"""
    try:
        cursor = get_connection().cursor()
        cursor.execute(
            '''INSERT OR REPLACE INTO users 
            (id, chat_id, username, full_name, phone_number)
            VALUES (?, ?, ?, ?, ?)''',
            (user_id, user_id, username, full_name, phone_number)
        )
        get_connection().commit()
        return True
    except:
        return False

def get_user(user_id):
    """Foydalanuvchini olish"""
    cursor = get_connection().cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone()