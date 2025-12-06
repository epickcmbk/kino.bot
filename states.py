from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    """Admin paneli uchun holatlar"""
    
    # Admin boshqaruvi
    add_admin = State()
    remove_admin = State()
    
    # Kanal boshqaruvi
    add_channel_name = State()
    add_channel_url = State()
    remove_channel = State()
    
    # Kategoriya boshqaruvi
    add_category = State()
    remove_category = State()
    
    # Kino boshqaruvi
    movie_name = State()
    movie_code = State()
    movie_category = State()
    movie_year = State()
    movie_language = State()
    movie_country = State()
    movie_file_id = State()

class UserStates(StatesGroup):
    """Foydalanuvchi paneli uchun holatlar"""
    viewing_movies = State()
    watching_movie = State()
    search_by_code = State()