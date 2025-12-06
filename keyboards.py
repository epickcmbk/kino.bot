from aiogram import types

def get_start_keyboard(is_admin=False):
    """Bosh ekran tugmalari"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    
    if is_admin:
        keyboard.inline_keyboard.append(
            [types.InlineKeyboardButton(text="👨‍💼 ADMIN PANEL", callback_data="admin_panel")]
        )
    
    keyboard.inline_keyboard.append(
        [types.InlineKeyboardButton(text="👤 USER PANEL", callback_data="user_panel")]
    )
    
    return keyboard

def get_admin_menu_keyboard():
    """Admin panel asosiy tugmalari"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="👮 ADMIN BOSHQARUVI", callback_data="manage_admins")],
        [types.InlineKeyboardButton(text="📺 KANAL BOSHQARUVI", callback_data="manage_channels")],
        [types.InlineKeyboardButton(text="📂 KATEGORIYA BOSHQARUVI", callback_data="manage_categories")],
        [types.InlineKeyboardButton(text="🎬 KINO BOSHQARUVI", callback_data="manage_movies")],
        [types.InlineKeyboardButton(text="🏠 BOSH MENYU", callback_data="start")]
    ])
    return keyboard

def get_manage_menu_keyboard(menu_type):
    """Boshqaruv menyusining tugmalari"""
    if menu_type == "admin":
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="➕ ADMIN QO'SHISH", callback_data="add_admin")],
            [types.InlineKeyboardButton(text="➖ ADMIN O'CHIRISH", callback_data="remove_admin")],
            [types.InlineKeyboardButton(text="📋 ADMINLAR RO'YXATI", callback_data="list_admins")],
            [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="admin_panel")]
        ])
    
    return keyboard

def get_user_main_keyboard():
    """Foydalanuvchi paneli tugmalari"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎬 KINOLARNI KO'RISH", callback_data="browse_movies")],
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="back_to_menu")]
    ])
    return keyboard

def get_categories_keyboard(categories, callback_prefix="cat"):
    """Kategoriyalar ro'yxati tugmalari - Outline style"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"📂 {cat[1]}", callback_data=f"{callback_prefix}_{cat[0]}")]
        for cat in categories
    ])
    
    if callback_prefix == "browse_cat":
        keyboard.inline_keyboard.append(
            [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="back_to_menu")]
        )
    elif callback_prefix == "movie_cat":
        keyboard.inline_keyboard.append(
            [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="cancel")]
        )
    
    return keyboard

def get_movies_keyboard(movies):
    """Kinolar ro'yxati tugmalari - Outline style"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=f"🎬 {movie[1]}", callback_data=f"movie_{movie[0]}")]
        for movie in movies
    ])
    
    keyboard.inline_keyboard.append(
        [types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="browse_movies")]
    )
    
    return keyboard

def get_channel_keyboard(unsubscribed_channels, movie_id, can_watch):
    """Kanal obunasi tugmalari - Outline style"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    
    if not can_watch and unsubscribed_channels:
        for channel in unsubscribed_channels:
            keyboard.inline_keyboard.append([
                types.InlineKeyboardButton(
                    text=f"📢 {channel[1]}",
                    url=channel[2]
                )
            ])
        
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(
                text="✅ OBUNANI TEKSHIRISH",
                callback_data="check_subscription"
            )
        ])
    elif can_watch:
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(
                text="▶️ KINONI KO'RISH",
                callback_data=f"watch_{movie_id}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        types.InlineKeyboardButton(text="🔙 ORQAGA", callback_data="browse_movies")
    ])
    
    return keyboard