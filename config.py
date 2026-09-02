import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "").strip()
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Javoh2323..")

# Web App sozlamalari
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://telefon-bozor.onrender.com").strip()
PORT = int(os.getenv("PORT", 8080))

# Database Settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/telefon_bozor_db")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "telefon_bozor_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Owner Information
OWNER_TELEGRAM = os.getenv("OWNER_TELEGRAM", "@JOVIDZE")
OWNER_INSTAGRAM = os.getenv("OWNER_INSTAGRAM", "@KURGANSKY_")
OWNER_PHONE = os.getenv("OWNER_PHONE", "+998947762528")

# Payment Card Information
CARD_NUMBER = os.getenv("CARD_NUMBER", "5614-6818-7592-1300")
CARD_HOLDER = os.getenv("CARD_HOLDER", "MAVLONOV JAVOHIR")

# VIP Pricing
VIP_PRICE_1_DAY = int(os.getenv("VIP_PRICE_1_DAY", 2999))
VIP_PRICE_2_DAYS = int(os.getenv("VIP_PRICE_2_DAYS", 3999))
VIP_PRICE_3_DAYS = int(os.getenv("VIP_PRICE_3_DAYS", 5999))

VIP_PLANS = {
    "1": {"days": 1, "price": VIP_PRICE_1_DAY, "title": "⭐️ 1 Kunlik VIP (2 999 so'm)"},
    "2": {"days": 2, "price": VIP_PRICE_2_DAYS, "title": "⭐️ 2 Kunlik VIP (3 999 so'm)"},
    "3": {"days": 3, "price": VIP_PRICE_3_DAYS, "title": "⭐️ 3 Kunlik VIP (5 999 so'm)"},
}
