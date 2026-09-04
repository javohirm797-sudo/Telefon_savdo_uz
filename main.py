import asyncio
import logging
import sys
import os
from aiohttp import web

from webapp.api import setup_webapp_routes

async def start_webapp_server(bot):
    """Web App va API serverini ishga tushirish"""
    app = web.Application()
    setup_webapp_routes(app, bot)
    runner = web.AppRunner(app)
    await runner.setup()
    port = config.PORT
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.getLogger(__name__).info(f"🌐 Web App server ishga tushdi: http://localhost:{port}")
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
from utils import auction_background_checker

# Logging sozlamalari
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CertifiAiohttpSession(AiohttpSession):
    """SSL va yopiq sessiyalarni to'g'ri boshqaruvchi xavfsiz sessiya"""
    async def create_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            connector = TCPConnector(ssl=ssl_ctx)
            self._session = aiohttp.ClientSession(
                connector=connector,
                json_serialize=self.json_dumps,
            )
        return self._session

async def set_bot_commands(bot: Bot):
    """Bot menyusidagi buyruqlar"""
    commands = [
        BotCommand(command="start", description="🔄 Botni qayta ishga tushirish"),
        BotCommand(command="market", description="🛍 Telefonlar bozori (E'lonlar)")
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

    # Auksion tekshiruvchi background vazifasini ishga tushirish
    asyncio.create_task(auction_background_checker(bot))

    bot_info = await bot.get_me()
    logger.info(f"🚀 Bot muvaffaqiyatli ishga tushdi: @{bot_info.username}")
    print(f"\n=======================================================")
    print(f"✅ BOT ISHLADI: @{bot_info.username}")
    print(f"👨‍💻 Admin Telegram: {config.OWNER_TELEGRAM}")
    print(f"💳 To'lov karta: {config.CARD_NUMBER} ({config.CARD_HOLDER})")
    print("=======================================================\n")

    # Web App serveri va Pollingni boshlash
    await start_webapp_server(bot)
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