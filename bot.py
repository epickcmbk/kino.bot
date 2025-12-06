import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import TOKEN, ADMINS
from database import (
    init_db, add_admin, remove_admin, get_admins,
    add_channel, remove_channel, get_all_channels, check_user_subscription,
    add_category, remove_category, get_all_categories,
    add_movie, remove_movie, get_movies_by_category, get_movie_details,
    get_all_movies, add_user
)
from keyboards import (
    get_start_keyboard, get_admin_menu_keyboard,
    get_user_main_keyboard, get_categories_keyboard
)
from states import AdminStates, UserStates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ============ START COMMAND ============

@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    """Bot boshlanishi"""
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or "no_username"
    full_name = message.from_user.first_name or "User"
    
    add_user(user_id, username, full_name)
    
    is_admin = user_id in ADMINS
    
    if is_admin:
        text = f"🙋 Assalomualaikum <b>{full_name}</b>!\n\n👨‍💼 Admin paneliga xush kelibsiz!"
    else:
        text = f"🙋 Assalomualaikum <b>{full_name}</b>!\n\n🎬 Kino katalogiga xush kelibsiz!"
    
    keyboard = get_start_keyboard(is_admin=is_admin)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# ============ START BUTTON ============

@dp.callback_query(F.data == "start")
async def start_button(query: CallbackQuery, state: FSMContext):
    """Bosh menyuga qaytish"""
    await state.clear()
    user_id = query.from_user.id
    is_admin = user_id in ADMINS
    
    if is_admin:
        text = "👨‍💼 <b>Admin paneliga xush kelibsiz!</b>"
    else:
        text = "🎬 <b>Kino katalogiga xush kelibsiz!</b>"
    
    keyboard = get_start_keyboard(is_admin=is_admin)
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await query.answer()

# ============ ADMIN PANEL ============

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(query: CallbackQuery, state: FSMContext):
    """Admin paneliga kirish"""
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    await state.clear()
    keyboard = get_admin_menu_keyboard()
    await query.message.edit_text(
        "<b>👨‍💼 ADMIN PANEL</b>\n\nNima qilishni xohlaysiz?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

# ============ ADMIN BOSHQARUVI ============

@dp.callback_query(F.data == "manage_admins")
async def manage_admins(query: CallbackQuery, state: FSMContext):
    """Admin boshqaruvi menyusi"""
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Ruxsatiniz yo'q!", show_alert=True)
        return
    
    await state.clear()
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ ADMIN QO'SHISH", callback_data="add_admin")],
        [types.InlineKeyboardButton(text="➖ ADMIN O'CHIRISH", callback_data="remove_admin")],
        [types.InlineKeyboardButton(text="📋 ADMINLAR RO'YXATI", callback_data="list_admins")],
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="admin_panel")]
    ])
    await query.message.edit_text(
        "<b>👮 ADMIN BOSHQARUVI</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

@dp.callback_query(F.data == "add_admin")
async def add_admin_start(query: CallbackQuery, state: FSMContext):
    """Admin qo'shish boshlash"""
    if query.from_user.id not in ADMINS:
        return
    
    await state.set_state(AdminStates.add_admin)
    await query.message.edit_text(
        "✏️ <b>Adminning Telegram ID sini kiriting:</b>\n\n"
        "<i>Misol: 123456789</i>",
        parse_mode="HTML"
    )
    await query.answer()

@dp.message(AdminStates.add_admin)
async def add_admin_process(message: Message, state: FSMContext):
    """Admin qo'shish jarayoni"""
    try:
        admin_id = int(message.text)
        if add_admin(admin_id):
            await message.answer(f"✅ <b>{admin_id}</b> admin qilindi!", parse_mode="HTML")
        else:
            await message.answer(f"⚠️ <b>{admin_id}</b> allaqachon admin!", parse_mode="HTML")
    except ValueError:
        await message.answer("❌ <b>ID raqam bo'lishi kerak!</b>", parse_mode="HTML")
        return
    
    await state.clear()

@dp.callback_query(F.data == "remove_admin")
async def remove_admin_start(query: CallbackQuery, state: FSMContext):
    """Admin o'chirish boshlash"""
    if query.from_user.id not in ADMINS:
        return
    
    await state.set_state(AdminStates.remove_admin)
    await query.message.edit_text(
        "✏️ <b>O'chirish uchun admin ID sini kiriting:</b>",
        parse_mode="HTML"
    )
    await query.answer()

@dp.message(AdminStates.remove_admin)
async def remove_admin_process(message: Message, state: FSMContext):
    """Admin o'chirish jarayoni"""
    try:
        admin_id = int(message.text)
        if remove_admin(admin_id):
            await message.answer(f"✅ <b>{admin_id}</b> admindan olib tashlandi!", parse_mode="HTML")
        else:
            await message.answer(f"⚠️ <b>{admin_id}</b> admin topilmadi!", parse_mode="HTML")
    except ValueError:
        await message.answer("❌ <b>ID raqam bo'lishi kerak!</b>", parse_mode="HTML")
        return
    
    await state.clear()

@dp.callback_query(F.data == "list_admins")
async def list_admins(query: CallbackQuery):
    """Adminlar ro'yxati"""
    if query.from_user.id not in ADMINS:
        return
    
    admins = get_admins()
    if admins:
        text = "<b>👮 ADMINLAR RO'YXATI</b>\n\n"
        for i, admin in enumerate(admins, 1):
            text += f"{i}. <code>{admin}</code>\n"
    else:
        text = "<b>❌ Hechqanday admin yo'q</b>"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="manage_admins")]
    ])
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await query.answer()

# ============ KANAL BOSHQARUVI ============

@dp.callback_query(F.data == "manage_channels")
async def manage_channels(query: CallbackQuery, state: FSMContext):
    """Kanal boshqaruvi menyusi"""
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Ruxsatiniz yo'q!", show_alert=True)
        return
    
    await state.clear()
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ KANAL QO'SHISH", callback_data="add_channel")],
        [types.InlineKeyboardButton(text="➖ KANAL O'CHIRISH", callback_data="remove_channel")],
        [types.InlineKeyboardButton(text="📋 KANALLAR RO'YXATI", callback_data="list_channels")],
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="admin_panel")]
    ])
    await query.message.edit_text(
        "<b>📺 KANAL BOSHQARUVI</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

@dp.callback_query(F.data == "add_channel")
async def add_channel_start(query: CallbackQuery, state: FSMContext):
    """Kanal qo'shish boshlash"""
    if query.from_user.id not in ADMINS:
        return
    
    await state.set_state(AdminStates.add_channel_name)
    await query.message.edit_text(
        "✏️ <b>Kanal nomini kiriting:</b>\n\n"
        "<i>Misol: @kinolar</i>",
        parse_mode="HTML"
    )
    await query.answer()

@dp.message(AdminStates.add_channel_name)
async def add_channel_get_name(message: Message, state: FSMContext):
    """Kanal nomini olish"""
    channel_name = message.text
    await state.update_data(channel_name=channel_name)
    await state.set_state(AdminStates.add_channel_url)
    await message.answer(
        "✏️ <b>Kanal URL sini kiriting:</b>\n\n"
        "<i>Misol: https://t.me/kinolar</i>",
        parse_mode="HTML"
    )

@dp.message(AdminStates.add_channel_url)
async def add_channel_process(message: Message, state: FSMContext):
    """Kanal qo'shish jarayoni"""
    data = await state.get_data()
    channel_url = message.text
    
    if add_channel(data['channel_name'], channel_url):
        await message.answer(
            f"✅ <b>Kanal qo'shildi!</b>\n\n"
            f"🔗 {data['channel_name']}",
            parse_mode="HTML"
        )
    else:
        await message.answer(f"⚠️ <b>Kanal allaqachon mavjud!</b>", parse_mode="HTML")
    
    await state.clear()

@dp.callback_query(F.data == "remove_channel")
async def remove_channel_start(query: CallbackQuery, state: FSMContext):
    """Kanal o'chirish boshlash"""
    if query.from_user.id not in ADMINS:
        return
    
    channels = get_all_channels()
    if not channels:
        await query.answer("❌ Kanal yo'q!", show_alert=True)
        return
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"❌ {ch[1]}", callback_data=f"del_ch_{ch[0]}")]
        for ch in channels
    ] + [[types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="manage_channels")]])
    
    await query.message.edit_text(
        "<b>❌ O'CHIRISH UCHUN KANAL TANLANG</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

@dp.callback_query(F.data.startswith("del_ch_"))
async def remove_channel_confirm(query: CallbackQuery):
    """Kanal o'chirish tasdiqlash"""
    if query.from_user.id not in ADMINS:
        return
    
    channel_id = int(query.data.split("_")[2])
    channels = get_all_channels()
    channel = next((ch for ch in channels if ch[0] == channel_id), None)
    
    if channel and remove_channel(channel[1]):
        await query.answer(f"✅ {channel[1]} o'chirildi!")
        await query.message.delete()
    else:
        await query.answer("❌ Xato yuz berdi!", show_alert=True)

@dp.callback_query(F.data == "list_channels")
async def list_channels(query: CallbackQuery):
    """Kanallar ro'yxati"""
    if query.from_user.id not in ADMINS:
        return
    
    channels = get_all_channels()
    if channels:
        text = "<b>📺 KANALLAR RO'YXATI</b>\n\n"
        for i, ch in enumerate(channels, 1):
            text += f"{i}. <b>{ch[1]}</b>\n🔗 {ch[2]}\n\n"
    else:
        text = "<b>❌ Hechqanday kanal yo'q</b>"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="manage_channels")]
    ])
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await query.answer()

# ============ KATEGORIYA BOSHQARUVI ============

@dp.callback_query(F.data == "manage_categories")
async def manage_categories(query: CallbackQuery, state: FSMContext):
    """Kategoriya boshqaruvi menyusi"""
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Ruxsatiniz yo'q!", show_alert=True)
        return
    
    await state.clear()
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ KATEGORIYA QO'SHISH", callback_data="add_category")],
        [types.InlineKeyboardButton(text="➖ KATEGORIYA O'CHIRISH", callback_data="remove_category")],
        [types.InlineKeyboardButton(text="📋 KATEGORIYALAR RO'YXATI", callback_data="list_categories")],
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="admin_panel")]
    ])
    await query.message.edit_text(
        "<b>📂 KATEGORIYA BOSHQARUVI</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

@dp.callback_query(F.data == "add_category")
async def add_category_start(query: CallbackQuery, state: FSMContext):
    """Kategoriya qo'shish boshlash"""
    if query.from_user.id not in ADMINS:
        return
    
    await state.set_state(AdminStates.add_category)
    await query.message.edit_text(
        "✏️ <b>Kategoriya nomini kiriting:</b>\n\n"
        "<i>Misol: Aksyon, Drama, Komediya</i>",
        parse_mode="HTML"
    )
    await query.answer()

@dp.message(AdminStates.add_category)
async def add_category_process(message: Message, state: FSMContext):
    """Kategoriya qo'shish jarayoni"""
    category_name = message.text.strip()
    
    if add_category(category_name):
        await message.answer(
            f"✅ <b>Kategoriya qo'shildi!</b>\n\n"
            f"📂 {category_name}",
            parse_mode="HTML"
        )
    else:
        await message.answer(f"⚠️ <b>Kategoriya allaqachon mavjud!</b>", parse_mode="HTML")
    
    await state.clear()

@dp.callback_query(F.data == "remove_category")
async def remove_category_start(query: CallbackQuery, state: FSMContext):
    """Kategoriya o'chirish boshlash"""
    if query.from_user.id not in ADMINS:
        return
    
    categories = get_all_categories()
    if not categories:
        await query.answer("❌ Kategoriya yo'q!", show_alert=True)
        return
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"❌ {cat[1]}", callback_data=f"del_cat_{cat[0]}")]
        for cat in categories
    ] + [[types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="manage_categories")]])
    
    await query.message.edit_text(
        "<b>❌ O'CHIRISH UCHUN KATEGORIYA TANLANG</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

@dp.callback_query(F.data.startswith("del_cat_"))
async def remove_category_confirm(query: CallbackQuery):
    """Kategoriya o'chirish tasdiqlash"""
    if query.from_user.id not in ADMINS:
        return
    
    category_id = int(query.data.split("_")[2])
    categories = get_all_categories()
    category = next((cat for cat in categories if cat[0] == category_id), None)
    
    if category and remove_category(category[0]):
        await query.answer(f"✅ {category[1]} o'chirildi!")
        await query.message.delete()
    else:
        await query.answer("❌ Xato yuz berdi!", show_alert=True)

@dp.callback_query(F.data == "list_categories")
async def list_categories(query: CallbackQuery):
    """Kategoriyalar ro'yxati"""
    if query.from_user.id not in ADMINS:
        return
    
    categories = get_all_categories()
    if categories:
        text = "<b>📂 KATEGORIYALAR RO'YXATI</b>\n\n"
        for i, cat in enumerate(categories, 1):
            text += f"{i}. {cat[1]}\n"
    else:
        text = "<b>❌ Hechqanday kategoriya yo'q</b>"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="manage_categories")]
    ])
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await query.answer()

# ============ KINO BOSHQARUVI ============

@dp.callback_query(F.data == "manage_movies")
async def manage_movies(query: CallbackQuery, state: FSMContext):
    """Kino boshqaruvi menyusi"""
    if query.from_user.id not in ADMINS:
        await query.answer("❌ Ruxsatiniz yo'q!", show_alert=True)
        return
    
    await state.clear()
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ KINO QO'SHISH", callback_data="add_movie")],
        [types.InlineKeyboardButton(text="➖ KINO O'CHIRISH", callback_data="remove_movie")],
        [types.InlineKeyboardButton(text="📋 KINOLAR RO'YXATI", callback_data="list_movies")],
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="admin_panel")]
    ])
    await query.message.edit_text(
        "<b>🎬 KINO BOSHQARUVI</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

@dp.callback_query(F.data == "add_movie")
async def add_movie_start(query: CallbackQuery, state: FSMContext):
    """Kino qo'shish boshlash"""
    if query.from_user.id not in ADMINS:
        return
    
    categories = get_all_categories()
    if not categories:
        await query.answer("❌ Avval kategoriya qo'shing!", show_alert=True)
        return
    
    await state.set_state(AdminStates.movie_name)
    await query.message.edit_text(
        "✏️ <b>Kino nomini kiriting:</b>\n\n"
        "<i>Misol: Avatar 2</i>",
        parse_mode="HTML"
    )
    await query.answer()

@dp.message(AdminStates.movie_name)
async def movie_get_name(message: Message, state: FSMContext):
    """Kino nomini olish"""
    await state.update_data(movie_name=message.text)
    await state.set_state(AdminStates.movie_code)
    await message.answer(
        "✏️ <b>Kino kodini kiriting:</b>\n\n"
        "<i>Misol: KIN001</i>",
        parse_mode="HTML"
    )

@dp.message(AdminStates.movie_code)
async def movie_get_code(message: Message, state: FSMContext):
    """Kino kodini olish"""
    await state.update_data(movie_code=message.text)
    await state.set_state(AdminStates.movie_year)
    await message.answer(
        "✏️ <b>Yilni kiriting:</b>\n\n"
        "<i>Misol: 2023</i>",
        parse_mode="HTML"
    )

@dp.message(AdminStates.movie_year)
async def movie_get_year(message: Message, state: FSMContext):
    """Kino yilini olish"""
    try:
        year = int(message.text)
        await state.update_data(movie_year=year)
        await state.set_state(AdminStates.movie_language)
        await message.answer(
            "✏️ <b>Tilni kiriting:</b>\n\n"
            "<i>Misol: O'zbek, Inglizcha</i>",
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer(
            "❌ <b>Yil raqam bo'lishi kerak!</b>\n\n"
            "Qayta kiriting:",
            parse_mode="HTML"
        )

@dp.message(AdminStates.movie_language)
async def movie_get_language(message: Message, state: FSMContext):
    """Kino tilini olish"""
    await state.update_data(movie_language=message.text)
    await state.set_state(AdminStates.movie_country)
    await message.answer(
        "✏️ <b>Davlatni kiriting:</b>\n\n"
        "<i>Misol: USA, Koreyasi</i>",
        parse_mode="HTML"
    )

@dp.message(AdminStates.movie_country)
async def movie_get_country(message: Message, state: FSMContext):
    """Kino davlatini olish"""
    await state.update_data(movie_country=message.text)
    
    categories = get_all_categories()
    keyboard = get_categories_keyboard(categories, "movie_cat")
    
    await state.set_state(AdminStates.movie_category)
    await message.answer(
        "📂 <b>Kategoriyani tanlang:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(AdminStates.movie_category)
async def movie_get_category(query: CallbackQuery, state: FSMContext):
    """Kino kategoriyasini olish"""
    category_id = int(query.data.split("_")[2])
    await state.update_data(movie_category=category_id)
    await state.set_state(AdminStates.movie_file_id)
    await query.message.edit_text(
        "📹 <b>Video yuklang yoki File ID kiriting:</b>\n\n"
        "<i>1️⃣ Video faylni yuboring (Rekomendlyalanadi)\n"
        "YOKI\n"
        "2️⃣ File ID metnini kiriting</i>",
        parse_mode="HTML"
    )
    await query.answer()

@dp.message(AdminStates.movie_file_id)
async def movie_get_file_id(message: Message, state: FSMContext):
    """Kino file ID sini olish va qo'shish"""
    data = await state.get_data()
    
    file_id = None
    
    # Agar video yuborilib bo'lsa, file_id sini olish
    if message.video:
        file_id = message.video.file_id
        video_info = f"✅ <b>Video yuklandi!</b>\n\n"
        video_info += f"Kino nomi: {data['movie_name']}\n"
        video_info += f"Kod: {data['movie_code']}\n"
    else:
        # Agar text bo'lsa (File ID deb hisobla)
        file_id = message.text.strip()
        video_info = f"📝 <b>File ID qabul qilindi!</b>\n\n"
        video_info += f"File ID: <code>{file_id}</code>\n"
    
    if add_movie(
        data['movie_name'],
        data['movie_code'],
        data['movie_category'],
        data['movie_year'],
        data['movie_language'],
        data['movie_country'],
        file_id
    ):
        await message.answer(
            f"✅ <b>Kino qo'shildi!</b>\n\n"
            f"🎬 {data['movie_name']}\n"
            f"📝 Kod: {data['movie_code']}\n"
            f"📅 Yil: {data['movie_year']}",
            parse_mode="HTML"
        )
    else:
        await message.answer(f"⚠️ <b>Bu kod allaqachon mavjud!</b>", parse_mode="HTML")
    
    await state.clear()

@dp.callback_query(F.data == "remove_movie")
async def remove_movie_start(query: CallbackQuery, state: FSMContext):
    """Kino o'chirish boshlash"""
    if query.from_user.id not in ADMINS:
        return
    
    movies = get_all_movies()
    if not movies:
        await query.answer("❌ Kino yo'q!", show_alert=True)
        return
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"❌ {movie[1]}", callback_data=f"del_mov_{movie[0]}")]
        for movie in movies[:15]
    ] + [[types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="manage_movies")]])
    
    await query.message.edit_text(
        "<b>❌ O'CHIRISH UCHUN KINO TANLANG</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

@dp.callback_query(F.data.startswith("del_mov_"))
async def remove_movie_confirm(query: CallbackQuery):
    """Kino o'chirish tasdiqlash"""
    if query.from_user.id not in ADMINS:
        return
    
    movie_id = int(query.data.split("_")[2])
    movies = get_all_movies()
    movie = next((m for m in movies if m[0] == movie_id), None)
    
    if movie and remove_movie(movie_id):
        await query.answer(f"✅ {movie[1]} o'chirildi!")
        await query.message.delete()
    else:
        await query.answer("❌ Xato yuz berdi!", show_alert=True)

@dp.callback_query(F.data == "list_movies")
async def list_movies(query: CallbackQuery):
    """Kinolar ro'yxati"""
    if query.from_user.id not in ADMINS:
        return
    
    movies = get_all_movies()
    if movies:
        text = "<b>🎬 KINOLAR RO'YXATI</b>\n\n"
        for i, movie in enumerate(movies[:20], 1):
            text += f"{i}. {movie[1]}\n"
    else:
        text = "<b>❌ Hechqanday kino yo'q</b>"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="manage_movies")]
    ])
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await query.answer()

# ============ USER PANEL ============

@dp.callback_query(F.data == "user_panel")
async def user_panel(query: CallbackQuery, state: FSMContext):
    """User paneliga kirish"""
    await state.clear()
    user_id = query.from_user.id
    channels = get_all_channels()
    
    if not channels:
        await query.message.answer("❌ Kanallar qo'yilmagan!", parse_mode="HTML")
        await query.answer()
        return
    
    # Hozircha obunani tekshirmay, to'gridan-to'g'ri menyuga o'tkazish
    # Yoki kanal linkini ko'rsatish
    text = "<b>📢 OBUNAGA QOWUSH MAJBURIY</b>\n\n"
    text += "Quyidagi kanallarga obuna bo'ling:\n\n"
    
    keyboard_buttons = []
    for ch in channels:
        url = str(ch[2]).strip()
        if url.startswith('https://https://'):
            url = url.replace('https://https://', 'https://')
        
        keyboard_buttons.append([
            types.InlineKeyboardButton(text=f"📌 {ch[1]}", url=url)
        ])
    
    keyboard_buttons.append([
        types.InlineKeyboardButton(text="✅ OBUNANI TEKSHIRISH", callback_data="check_sub")
    ])
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await query.answer()

# ============ OBUNA TEKSHIRUVI ============

@dp.callback_query(F.data == "check_sub")
async def check_subscription(query: CallbackQuery):
    """Obunani tekshirish"""
    user_id = query.from_user.id
    channels = get_all_channels()
    
    # Manua obunani tekshirish uchun /start yozing deb aytish
    text = "<b>✅ OBUNANI TEKSHIRISH</b>\n\n"
    text += "Agar barcha kanallarga obuna bo'lgan bo'lsangiz, /start yozib qayta kiriting!\n\n"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎬 KINOLARGA O'TISH", callback_data="go_to_movies")],
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="user_panel")]
    ])
    
    try:
        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await query.answer("✅ Obuna bo'lganingizni tasdiqlash uchun /start yozing!")
    except:
        await query.answer("✅ Obuna bo'lganingizni tasdiqlash uchun /start yozing!")

@dp.callback_query(F.data == "go_to_movies")
async def go_to_movies(query: CallbackQuery, state: FSMContext):
    """Kinolarga o'tish"""
    await state.clear()
    keyboard = get_user_main_keyboard()
    await query.message.edit_text(
        "<b>✅ OBUNADA SIZA!</b>\n\n"
        "<b>🎬 KINO KATALOGI</b>\n\n"
        "Nima qilishni xohlaysiz?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

# ============ KINOLAR BROWSING ============

@dp.callback_query(F.data == "browse_movies")
async def browse_movies(query: CallbackQuery, state: FSMContext):
    """Kinolarni ko'rish - kategoriya tanlash yoki kod orqali qidirish"""
    await state.clear()
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📂 KATEGORIYA BO'YICHA", callback_data="by_category")],
        [types.InlineKeyboardButton(text="🔍 KOD BO'YICHA QIDIRISH", callback_data="by_code")],
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="back_to_menu")]
    ])
    
    await query.message.edit_text(
        "<b>🎬 KINOLARNI QANDAY KO'RISH?</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

@dp.callback_query(F.data == "by_category")
async def by_category(query: CallbackQuery, state: FSMContext):
    """Kategoriya bo'yicha qidirish"""
    await state.clear()
    categories = get_all_categories()
    
    if not categories:
        await query.answer("❌ Kategoriya topilmadi!", show_alert=True)
        return
    
    keyboard = get_categories_keyboard(categories, "browse_cat")
    await query.message.edit_text(
        "<b>📂 KATEGORIYA TANLANG</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

@dp.callback_query(F.data == "by_code")
async def by_code(query: CallbackQuery, state: FSMContext):
    """Kod bo'yicha qidirish boshlash"""
    await state.set_state(UserStates.search_by_code)
    await query.message.edit_text(
        "✏️ <b>Kino kodini kiriting:</b>\n\n"
        "<i>Misol: KIN001</i>",
        parse_mode="HTML"
    )
    await query.answer()

@dp.message(UserStates.search_by_code)
async def search_movie_by_code(message: Message, state: FSMContext):
    """Kod bo'yicha kinoni qidirish"""
    code = message.text.strip().upper()
    
    all_movies = get_all_movies()
    movie = next((m for m in all_movies if m[2].upper() == code), None)
    
    if movie:
        movie_details = get_movie_details(movie[0])
        text = f"<b>🎬 {movie_details[1]}</b>\n\n"
        text += f"<b>📝 Kod:</b> <code>{movie_details[2]}</code>\n"
        text += f"<b>📅 Yil:</b> {movie_details[4]}\n"
        text += f"<b>🗣️ Til:</b> {movie_details[5]}\n"
        text += f"<b>🌍 Davlat:</b> {movie_details[6]}\n"
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="browse_movies")]
        ])
        
        # File ID tekshirish
        if not movie_details[7] or movie_details[7].strip() == "":
            await message.answer(
                text + f"\n\n❌ <b>Video File ID topilmadi!</b>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await state.clear()
            return
        
        try:
            # Video yuborish
            await bot.send_video(
                chat_id=message.from_user.id,
                video=movie_details[7],
                caption=text,
                parse_mode="HTML"
            )
            await message.answer("✅ Video yuborildi!", parse_mode="HTML")
        except Exception as e:
            error_msg = str(e)
            await message.answer(
                text + f"\n\n❌ <b>Xato:</b> {error_msg[:100]}\n\n"
                f"<i>Admin bilan murojaat qiling.</i>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            logger.error(f"Video send error: {error_msg}")
    else:
        await message.answer(
            f"❌ <b>{code}</b> kodida kino topilmadi!\n\n"
            "Iltimos, kodni qayta kiriting:",
            parse_mode="HTML"
        )
        return
    
    await state.clear()

@dp.callback_query(F.data.startswith("browse_cat_"))
async def show_movies_by_category(query: CallbackQuery, state: FSMContext):
    """Kategoriya bo'yicha kinolarni ko'rsatish"""
    category_id = int(query.data.split("_")[2])
    movies = get_movies_by_category(category_id)
    
    if not movies:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="browse_movies")]
        ])
        await query.message.edit_text(
            "<b>❌ Bu kategoriyada kino yo'q</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await query.answer()
        return
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"🎬 {movie[1]}", callback_data=f"watch_{movie[0]}")]
        for movie in movies
    ] + [[types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="browse_movies")]])
    
    await state.set_state(UserStates.viewing_movies)
    await query.message.edit_text(
        "<b>🎬 KINOLAR</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

# ============ KINO KO'RISH ============

@dp.callback_query(F.data.startswith("watch_"))
async def watch_movie(query: CallbackQuery, state: FSMContext):
    """Kino detallarini ko'rsatish va videoni yuborish"""
    movie_id = int(query.data.split("_")[1])
    movie = get_movie_details(movie_id)
    
    if not movie:
        await query.answer("❌ Kino topilmadi!", show_alert=True)
        return
    
    text = f"<b>🎬 {movie[1]}</b>\n\n"
    text += f"<b>📝 Kod:</b> <code>{movie[2]}</code>\n"
    text += f"<b>📅 Yil:</b> {movie[4]}\n"
    text += f"<b>🗣️ Til:</b> {movie[5]}\n"
    text += f"<b>🌍 Davlat:</b> {movie[6]}\n"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="browse_movies")]
    ])
    
    # File ID tekshirish
    if not movie[7] or movie[7].strip() == "":
        await query.message.edit_text(
            text + f"\n\n❌ <b>Video topilmadi!</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await query.answer("❌ Video topilmadi!")
        return
    
    try:
        # Video yuborish - file_id yoki URL bo'lsa ishlasin
        await bot.send_video(
            chat_id=query.from_user.id,
            video=movie[7],
            caption=text,
            parse_mode="HTML"
        )
        await query.answer("✅ Video yuborildi!")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Video send error: {error_msg}")
        
        # Agar video xatosi bo'lsa, xato ko'rsatish
        if "not found" in error_msg.lower() or "invalid" in error_msg.lower():
            await query.message.edit_text(
                text + f"\n\n❌ <b>Video mavjud emas yoki noto'g'ri!</b>\n"
                f"<i>Admin bilan murojaat qiling.</i>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await query.message.edit_text(
                text + f"\n\n❌ <b>Xato:</b> Video yuborilmadi\n"
                f"<i>Admin bilan murojaat qiling.</i>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    
    await state.clear()

@dp.callback_query(F.data.startswith("play_"))
async def play_movie(query: CallbackQuery):
    """Videoni qayta yuborish (eski, ishlatilmaydi)"""
    await query.answer("Video allaqachon yuborilgan!", show_alert=False)

# ============ BACK BUTTONS ============

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(query: CallbackQuery, state: FSMContext):
    """Menuga qaytish"""
    await state.clear()
    keyboard = get_user_main_keyboard()
    await query.message.edit_text(
        "<b>🎬 KINO KATALOGI</b>\n\n"
        "Nima qilishni xohlaysiz?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await query.answer()

# ============ MAIN ============

async def main():
    """Bot ishga tushirish"""
    init_db()
    print("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())