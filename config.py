import os
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# ADMINS ni int listga aylantirish
ADMINS = list(map(int, os.getenv("ADMINS").split(",")))
