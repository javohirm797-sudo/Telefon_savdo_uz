import asyncio
import logging
import sys
import ssl

# Windows console UTF-8 sozlamasi
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import certifi
import aiohttp
from aiohttp import TCPConnector
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

import config
from database import db
from handlers import setup_routers

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CertifiAiohttpSession(AiohttpSession):
    """Windows tizimlarida SSL sertifikat xatolarini to'g'irlash uchun maxsus sessiya"""
    async def create_session(self) -> aiohttp.ClientSession:
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        # Agar tizimda SSL tekshiruvi bloklangan bo'lsa
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connector = TCPConnector(ssl=ssl_ctx)
        return aiohttp.ClientSession(
            connector=connector,
            json_serialize=self.json_dumps,
        )

async def set_bot_commands(bot: Bot):
    """Bot menyusidagi buyruqlar"""
    commands = [
        BotCommand(command="start", description="🔄 Botni qayta ishga tushirish"),
        BotCommand(command="market", description="🛍 Telefonlar bozori (E'lonlar)"),
        BotCommand(command="post_ad", description="➕ Yangi e'lon joylash"),
        BotCommand(command="my_ads", description="📋 Mening e'lonlarim"),
        BotCommand(command="vip", description="⭐️ VIP e'lon xizmati"),
        BotCommand(command="contact", description="👨‍💻 Admin bilan bog'lanish")
    ]
    await bot.set_my_commands(commands)

async def main():
    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ XATOLIK: .env faylida BOT_TOKEN ko'rsatilmagan! Iltimos, @BotFather orqali token oling va .env fayliga yozing.")
        print("\n=======================================================")
        print("❌ XATOLIK: BOT_TOKEN topilmadi!")
        print("1. .env faylini oching.")
        print("2. BOT_TOKEN=qismiga @BotFather bergan tokenni yozing.")
        print("=======================================================\n")
        return

    session = CertifiAiohttpSession()

    # Bot va Dispatcher yaratish
    bot = Bot(
        token=config.BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlarni ulash
    main_router = setup_routers()
    dp.include_router(main_router)

    # Ma'lumotlar bazasini ishga tushirish (PostgreSQL / SQLite)
    logger.info("Ma'lumotlar bazasiga ulanish...")
    await db.connect()

    # Buyruqlarni o'rnatish
    await set_bot_commands(bot)

    bot_info = await bot.get_me()
    logger.info(f"🚀 Bot muvaffaqiyatli ishga tushdi: @{bot_info.username}")
    print(f"\n=======================================================")
    print(f"✅ BOT ISHLADI: @{bot_info.username}")
    print(f"👨‍💻 Admin Telegram: {config.OWNER_TELEGRAM}")
    print(f"💳 To'lov karta: {config.CARD_NUMBER} ({config.CARD_HOLDER})")
    print("=======================================================\n")

    # Pollingni boshlash
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
