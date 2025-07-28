import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./giftbot.db")
CURRENCY = "XTR"
LOGGING_CHAT_ID = os.getenv("LOGGING_CHAT_ID")
NEW_USERS_THREAD_ID = os.getenv("NEW_USERS_THREAD_ID")
DEPOSITS_THREAD_ID = os.getenv("DEPOSITS_THREAD_ID")
REFUNDS_THREAD_ID = os.getenv("REFUNDS_THREAD_ID")
NEW_GIFTS_THREAD_ID = os.getenv("NEW_GIFTS_THREAD_ID")
