from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_category_name = State()

    waiting_movie_title = State()
    waiting_movie_code = State()
    waiting_movie_category = State()
    waiting_movie_video = State()
