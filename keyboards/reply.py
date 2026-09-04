from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import config

def get_main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Bosh menyu klaviaturasi - faqat Web App va Telefonlar bozori"""
    buttons = [
        [
            KeyboardButton(
                text="🌐 Mobil Bozor (Web App)", 
                web_app=WebAppInfo(url=config.WEBAPP_URL)
            )
        ],
        [KeyboardButton(text="🛍 Telefonlar bozori (E'lonlar)")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_phone_share_kb() -> ReplyKeyboardMarkup:
    """Telefon raqamni yuborish klaviaturasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_cancel_kb() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )

def get_skip_or_cancel_kb() -> ReplyKeyboardMarkup:
    """O'tkazib yuborish yoki bekor qilish"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏩ O'tkazib yuborish")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
