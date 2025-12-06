# kino_bot.py
"""
To'liq kino-bot (aiogram v3 + SQLite) — bitta faylda.
Funktsiyalar:
- Admin: kategoriya qo'shish/o'chirish, kino qo'shish/o'chirish, kanal qo'shish/o'chirish, statistika
- Foydalanuvchi: kino kodiga qarab video olish
- Foydalanuvchi: barcha kanallarga obuna bo'lishi kerak (adminlar uchun tekshirish yo'q)
Ishga tushirish:
  pip install aiogram
  python kino_bot.py
Token va admin IDlarini sozlang.
"""

import asyncio
import logging
import sqlite3
from typing import Optional, List, Tuple

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup
)

# ---------------- CONFIG ----------------
BOT_TOKEN = "8103108987:AAFmXKSVR_1GYlp0nLQZRupbVvr0R_vxM_k"         # <<--- shu joyga tokenni qo'ying
ADMIN_IDS: List[int] = [7987528056]       # <<--- admin ID lar ro'yxati (integer)
DB_PATH = "kino_bot.db"

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- ROUTER / STATES ----------------
router = Router()

class AdminStates(StatesGroup):
    waiting_channel = State()
    waiting_category = State()
    waiting_movie_code = State()
    waiting_movie_title = State()
    waiting_movie_file = State()

# ---------------- DATABASE ----------------
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        full_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS kanal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT UNIQUE NOT NULL,
        channel_url TEXT NOT NULL
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS kategoriya (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL UNIQUE
    )""")
    # jadvalda created_by bor — ilgari xatolik chiqmasligi uchun
    c.execute("""
    CREATE TABLE IF NOT EXISTS kino (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        category_id INTEGER,
        file_id TEXT NOT NULL,
        language TEXT,
        country TEXT,
        year INTEGER,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES kategoriya(id)
    )""")
    conn.commit()
    conn.close()

# --- users
def add_user(user_id: int, username: Optional[str], full_name: Optional[str]):
    conn = _get_conn()
    try:
        conn.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
                     (user_id, username or "", full_name or ""))
        conn.commit()
    except Exception:
        logger.exception("add_user xatosi")
    finally:
        conn.close()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# --- channels
def get_all_channels():
    conn = _get_conn()
    rows = conn.execute("SELECT id, channel_id, channel_url FROM kanal ORDER BY id").fetchall()
    conn.close()
    return rows

def add_channel(channel_id: str, channel_url: str) -> Tuple[bool, str]:
    conn = _get_conn()
    try:
        conn.execute("INSERT INTO kanal (channel_id, channel_url) VALUES (?, ?)", (channel_id, channel_url))
        conn.commit()
        return True, "Kanal qo'shildi"
    except sqlite3.IntegrityError:
        return False, "Bu kanal allaqachon mavjud"
    except Exception:
        logger.exception("add_channel xato")
        return False, "Xatolik yuz berdi"
    finally:
        conn.close()

def delete_channel(db_id: int) -> bool:
    conn = _get_conn()
    try:
        cur = conn.execute("DELETE FROM kanal WHERE id = ?", (db_id,))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        logger.exception("delete_channel xato")
        return False
    finally:
        conn.close()

# --- categories
def get_all_categories():
    conn = _get_conn()
    rows = conn.execute("SELECT id, title FROM kategoriya ORDER BY title").fetchall()
    conn.close()
    return rows

def add_category(title: str) -> Tuple[bool, str]:
    title = (title or "").strip()
    if not title:
        return False, "Kategoriya nomi bo'sh bo'lishi mumkin emas"
    conn = _get_conn()
    try:
        conn.execute("INSERT INTO kategoriya (title) VALUES (?)", (title,))
        conn.commit()
        return True, "Kategoriya qo'shildi"
    except sqlite3.IntegrityError:
        return False, "Bu kategoriya allaqachon mavjud"
    except Exception:
        logger.exception("add_category xato")
        return False, "Xatolik yuz berdi"
    finally:
        conn.close()

def delete_category(cat_id: int) -> Tuple[bool, str]:
    conn = _get_conn()
    try:
        count = conn.execute("SELECT COUNT(*) FROM kino WHERE category_id = ?", (cat_id,)).fetchone()[0]
        if count > 0:
            return False, "Bu kategoriyada kinolar mavjud — avval kinolarni o'chiring yoki ularni boshqa kategoriya ostiga o'tkazing."
        cur = conn.execute("DELETE FROM kategoriya WHERE id = ?", (cat_id,))
        conn.commit()
        if cur.rowcount == 0:
            return False, "Kategoriya topilmadi"
        return True, "Kategoriya o'chirildi"
    except Exception:
        logger.exception("delete_category xato")
        return False, "Xatolik yuz berdi"
    finally:
        conn.close()

# --- movies
def movie_code_exists(code: str) -> bool:
    conn = _get_conn()
    exists = conn.execute("SELECT 1 FROM kino WHERE code = ?", (code,)).fetchone() is not None
    conn.close()
    return exists

def add_movie(title: str, code: str, category_id: int, file_id: str, user_id: int) -> Tuple[bool, str]:
    title = (title or "").strip()
    code = (code or "").strip()
    if not title or not code or not file_id:
        return False, "Nomi, kodi va fayl talab qilinadi"
    if movie_code_exists(code):
        return False, "Kodni boshqa kino allaqachon ishlatgan"
    conn = _get_conn()
    try:
        conn.execute("""INSERT INTO kino (title, code, category_id, file_id, created_by)
                        VALUES (?, ?, ?, ?, ?)""", (title, code, category_id, file_id, user_id))
        conn.commit()
        return True, "Kino qo'shildi"
    except Exception:
        logger.exception("add_movie xato")
        return False, "Xatolik yuz berdi"
    finally:
        conn.close()

def get_movie_by_code(code: str):
    conn = _get_conn()
    row = conn.execute("SELECT * FROM kino WHERE code = ?", (code,)).fetchone()
    conn.close()
    return row

def get_all_movies():
    conn = _get_conn()
    rows = conn.execute("SELECT id, title, code FROM kino ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows

def delete_movie(movie_id: int) -> bool:
    conn = _get_conn()
    try:
        cur = conn.execute("DELETE FROM kino WHERE id = ?", (movie_id,))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        logger.exception("delete_movie xato")
        return False
    finally:
        conn.close()

# --- stats
def get_statistics():
    conn = _get_conn()
    c = conn.cursor()
    users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    movies = c.execute("SELECT COUNT(*) FROM kino").fetchone()[0]
    cats = c.execute("SELECT COUNT(*) FROM kategoriya").fetchone()[0]
    chans = c.execute("SELECT COUNT(*) FROM kanal").fetchone()[0]
    conn.close()
    return {'users': users, 'movies': movies, 'categories': cats, 'channels': chans}

# ---------------- SUBSCRIPTION CHECK ----------------
async def check_subscription(bot: Bot, user_id: int) -> bool:
    if is_admin(user_id):
        return True
    channels = get_all_channels()
    if not channels:
        return True
    for row in channels:
        channel = row["channel_id"]
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ('member', 'administrator', 'creator'):
                continue
            else:
                return False
        except Exception as e:
            logger.warning(f"check_subscription: kanal {channel} tekshirilishda xato: {e}")
            continue
    return True

# ---------------- KEYBOARDS ----------------
def get_admin_keyboard():
    keyboard = [
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📢 Kanallar")],
        [KeyboardButton(text="🎬 Kino qo'shish"), KeyboardButton(text="📁 Kategoriya qo'shish")],
        [KeyboardButton(text="🗂 Kategoriya boshqaruvi"), KeyboardButton(text="🎞 Kino boshqaruvi")],
        [KeyboardButton(text="🔍 Kino qidirish")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_user_keyboard():
    keyboard = [[KeyboardButton(text="🔍 Kino qidirish")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_subscription_keyboard():
    channels = get_all_channels()
    buttons = []
    for row in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 {row['channel_id']}", url=row['channel_url'])])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_categories_keyboard():
    cats = get_all_categories()
    buttons = []
    for row in cats:
        buttons.append([InlineKeyboardButton(text=row['title'], callback_data=f"cat_{row['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None

def get_channels_manage_keyboard():
    channels = get_all_channels()
    buttons = []
    for row in channels:
        buttons.append([
            InlineKeyboardButton(text=f"📢 {row['channel_id']}", callback_data=f"viewchan_{row['id']}"),
            InlineKeyboardButton(text="❌", callback_data=f"delchan_{row['id']}")
        ])
    buttons.append([InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_movies_manage_keyboard():
    movies = get_all_movies()
    buttons = []
    for row in movies:
        buttons.append([
            InlineKeyboardButton(text=f"{row['title']} ({row['code']})", callback_data=f"viewmov_{row['id']}"),
            InlineKeyboardButton(text="❌", callback_data=f"delmov_{row['id']}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None

def get_categories_manage_keyboard():
    cats = get_all_categories()
    buttons = []
    for row in cats:
        buttons.append([
            InlineKeyboardButton(text=row['title'], callback_data=f"viewcat_{row['id']}"),
            InlineKeyboardButton(text="❌", callback_data=f"delcat_{row['id']}")
        ])
    buttons.append([InlineKeyboardButton(text="➕ Kategoriya qo'shish", callback_data="add_category")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ---------------- HANDLERS ----------------

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = message.from_user
    add_user(user.id, user.username, user.full_name)
    await state.clear()
    if is_admin(user.id):
        await message.answer(f"Assalomu aleykum, Admin {user.first_name}! 👋\n\n🎛 Admin panel:", reply_markup=get_admin_keyboard())
        return
    if not await check_subscription(message.bot, user.id):
        await message.answer("🎬 Botdan foydalanish uchun avval kanallarimizga a'zo bo'ling:", reply_markup=get_subscription_keyboard())
        return
    await message.answer(f"Assalomu aleykum, {user.first_name}! 👋\n\n🎬 Kino kodini yuboring:", reply_markup=get_user_keyboard())

# --- Statistics
@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu buyruq faqat adminlar uchun!")
        return
    stats = get_statistics()
    stats_text = (f"📊 <b>Statistika:</b>\n\n"
                  f"👥 Foydalanuvchilar: <b>{stats['users']}</b>\n"
                  f"🎬 Kinolar: <b>{stats['movies']}</b>\n"
                  f"📁 Kategoriyalar: <b>{stats['categories']}</b>\n"
                  f"📢 Kanallar: <b>{stats['channels']}</b>")
    await message.answer(stats_text, parse_mode="HTML")

# --- Channels management
@router.message(F.text == "📢 Kanallar")
async def manage_channels(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Faqat adminlar!")
        return
    await message.answer("📢 <b>Kanallar boshqaruvi:</b>\n\nKanalni o'chirish uchun ❌ tugmasini bosing:", reply_markup=get_channels_manage_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "add_channel")
async def add_channel_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Faqat adminlar!", show_alert=True)
        return
    await callback.message.answer("📢 <b>Kanal qo'shish:</b>\nKanal ID va URL ni quyidagi formatda yuboring:\n<code>@kanal_ismi,https://t.me/kanal_ismi</code>", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_channel)
    await callback.answer()

@router.message(AdminStates.waiting_channel)
async def process_add_channel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Faqat adminlar!")
        await state.clear()
        return
    parts = message.text.split(',')
    if len(parts) != 2:
        await message.answer("❌ Noto'g'ri format! To'g'ri format: <code>@kanal,https://t.me/kanal</code>", parse_mode="HTML")
        return
    channel_id = parts[0].strip()
    channel_url = parts[1].strip()
    ok, text = add_channel(channel_id, channel_url)
    await message.answer(("✅ " if ok else "❌ ") + text)
    await state.clear()

@router.callback_query(F.data.startswith("delchan_"))
async def delete_channel_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Faqat adminlar!", show_alert=True)
        return
    db_id = int(callback.data.split("_")[1])
    if delete_channel(db_id):
        await callback.answer("✅ Kanal o'chirildi!", show_alert=True)
        try:
            await callback.message.edit_text("📢 <b>Kanallar boshqaruvi:</b>\n\nKanalni o'chirish uchun ❌ tugmasini bosing:", reply_markup=get_channels_manage_keyboard(), parse_mode="HTML")
        except Exception:
            await callback.message.answer("📢 Kanal o'chirildi!", reply_markup=get_channels_manage_keyboard())
    else:
        await callback.answer("❌ Kanal o'chirishda xato!", show_alert=True)

# --- Category add/delete
@router.message(F.text == "📁 Kategoriya qo'shish")
async def add_category_start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Faqat adminlar!")
        return
    await message.answer("📁 <b>Kategoriya nomini yuboring:</b>", parse_mode="HTML")
    await message.set_state(AdminStates.waiting_category)

@router.message(AdminStates.waiting_category)
async def process_add_category(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Faqat adminlar!")
        await state.clear()
        return
    ok, text = add_category(message.text)
    await message.answer(("✅ " if ok else "❌ ") + text)
    await state.clear()

@router.message(F.text == "🗂 Kategoriya boshqaruvi")
async def categories_manage(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Faqat adminlar!")
        return
    await message.answer("📁 <b>Kategoriya boshqaruvi:</b>", reply_markup=get_categories_manage_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("delcat_"))
async def delete_category_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Faqat adminlar!", show_alert=True)
        return
    cat_id = int(callback.data.split("_")[1])
    ok, text = delete_category(cat_id)
    await callback.answer(("✅ " if ok else "❌ ") + text, show_alert=True)
    try:
        await callback.message.edit_text("📁 <b>Kategoriya boshqaruvi:</b>", reply_markup=get_categories_manage_keyboard(), parse_mode="HTML")
    except Exception:
        pass

# --- Movie add/delete
@router.message(F.text == "🎬 Kino qo'shish")
async def add_movie_start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Faqat adminlar!")
        return
    kb = get_categories_keyboard()
    if not kb:
        await message.answer("❌ Avval kategoriya qo'shing!")
        return
    await message.answer("🎬 <b>Kino qo'shish:</b>\nKategoriya tanlang:", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("cat_"))
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Faqat adminlar!", show_alert=True)
        return
    category_id = int(callback.data.split("_")[1])
    await state.update_data(selected_category=category_id)
    await state.set_state(AdminStates.waiting_movie_code)
    await callback.message.answer("📝 Kino uchun kod kiriting (masalan: <code>kino001</code>):", parse_mode="HTML")
    await callback.answer()

@router.message(AdminStates.waiting_movie_code)
async def process_movie_code(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Faqat adminlar!")
        await state.clear()
        return
    code = message.text.strip()
    if movie_code_exists(code):
        await message.answer("❌ Bu kod allaqachon mavjud! Boshqa kod kiriting.")
        return
    await state.update_data(movie_code=code)
    await state.set_state(AdminStates.waiting_movie_title)
    await message.answer("🎬 Kino nomini kiriting:")

@router.message(AdminStates.waiting_movie_title)
async def process_movie_title(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Faqat adminlar!")
        await state.clear()
        return
    await state.update_data(movie_title=message.text.strip())
    await state.set_state(AdminStates.waiting_movie_file)
    await message.answer("📹 Kino faylini yuboring (video yoki fayl sifatida):")

@router.message(AdminStates.waiting_movie_file, F.video | F.document)
async def process_movie_file(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Faqat adminlar!")
        await state.clear()
        return
    data = await state.get_data()
    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    if not file_id:
        await message.answer("❌ Iltimos, video yoki fayl yuboring!")
        return
    ok, text = add_movie(title=data.get('movie_title', 'NoName'),
                         code=data.get('movie_code'),
                         category_id=data.get('selected_category'),
                         file_id=file_id,
                         user_id=message.from_user.id)
    if ok:
        await message.answer(f"✅ Kino muvaffaqiyatli qo'shildi!\n\n🎬 Nomi: <b>{data.get('movie_title')}</b>\n📝 Kod: <code>{data.get('movie_code')}</code>", parse_mode="HTML")
    else:
        await message.answer("❌ " + text)
    await state.clear()

@router.message(AdminStates.waiting_movie_file)
async def process_wrong_file_type(message: Message, state: FSMContext):
    await message.answer("❌ Iltimos, faqat video yoki fayl yuboring!")

@router.message(F.text == "🎞 Kino boshqaruvi")
async def movies_manage(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Faqat adminlar!")
        return
    kb = get_movies_manage_keyboard()
    if not kb:
        await message.answer("🎞 Kinolar topilmadi.")
        return
    await message.answer("🎞 <b>Kino boshqaruvi:</b>", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("delmov_"))
async def delete_movie_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Faqat adminlar!", show_alert=True)
        return
    mid = int(callback.data.split("_")[1])
    if delete_movie(mid):
        await callback.answer("✅ Kino o'chirildi!", show_alert=True)
        try:
            await callback.message.edit_text("🎞 <b>Kino boshqaruvi:</b>", reply_markup=get_movies_manage_keyboard(), parse_mode="HTML")
        except Exception:
            pass
    else:
        await callback.answer("❌ Kino o'chirishda xato!", show_alert=True)

# --- subscription check callback for users
@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery):
    if await check_subscription(callback.bot, callback.from_user.id):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer("✅ Tasdiqlandi! Endi botdan foydalanishingiz mumkin.\n\n🎬 Kino kodini yuboring:", reply_markup=get_user_keyboard())
        await callback.answer()
    else:
        await callback.answer("❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)

# --- user search
@router.message(F.text == "🔍 Kino qidirish")
async def search_movie_button(message: Message):
    await message.answer("🔍 Iltimos, kino kodini yuboring:")

@router.message(StateFilter(None))
async def search_movie_by_code(message: Message):
    text = (message.text or "").strip()
    menu_texts = {"📊 Statistika", "📢 Kanallar", "🎬 Kino qo'shish", "📁 Kategoriya qo'shish",
                  "🗂 Kategoriya boshqaruvi", "🎞 Kino boshqaruvi", "🔍 Kino qidirish"}
    if text in menu_texts:
        return

    if not is_admin(message.from_user.id):
        if not await check_subscription(message.bot, message.from_user.id):
            await message.answer("🎬 Botdan foydalanish uchun avval kanallarimizga a'zo bo'ling:", reply_markup=get_subscription_keyboard())
            return

    movie = get_movie_by_code(text)
    if not movie:
        await message.answer("❌ Bu kod bilan kino topilmadi!\n\nKodni tekshiring va qayta urinib ko'ring.")
        return

    file_id = movie["file_id"]
    title = movie["title"]
    code = movie["code"]
    language = movie["language"]
    country = movie["country"]
    year = movie["year"]

    caption = f"🎬 <b>{title}</b>\n\n📝 Kod: <code>{code}</code>"
    if language:
        caption += f"\n🗣 Til: {language}"
    if country:
        caption += f"\n🌍 Mamlakat: {country}"
    if year:
        caption += f"\n📅 Yil: {year}"

    try:
        await message.answer_video(video=file_id, caption=caption, parse_mode="HTML")
    except Exception:
        try:
            await message.answer_document(document=file_id, caption=caption, parse_mode="HTML")
        except Exception:
            logger.exception("Faylni yuborishda xato")
            await message.answer("❌ Faylni yuborishda xatolik yuz berdi.")

# ---------------- MAIN ----------------
async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    logger.info("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
