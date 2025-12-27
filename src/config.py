import os
from dotenv import load_dotenv

load_dotenv()

# AI Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USE_REAL_LLM = bool(GEMINI_API_KEY) or bool(GROQ_API_KEY)

# Notification Keys
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Plaid Keys (New)
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
# Options: 'sandbox' (Fake), 'development' (Real - Free), 'production' (Real - Paid)
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")