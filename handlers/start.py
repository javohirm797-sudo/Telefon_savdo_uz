from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, MenuButtonWebApp, WebAppInfo
from aiogram.fsm.context import FSMContext

from database import db
from states import RegisterStates
from keyboards import get_main_menu, get_cancel_kb
import config

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    is_admin = user_id in config.ADMIN_IDS

    # Chat pastidagi Menyu tugmasini Web App ga sozlaymiz
    try:
        await message.bot.set_chat_menu_button(
            chat_id=user_id,
            menu_button=MenuButtonWebApp(
                text="📱 E'lon bering",
                web_app=WebAppInfo(url=config.WEBAPP_URL)
            )
        )
    except Exception:
        pass

    if not user:
        await message.answer(
            f"Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
            f"📱 <b>Telefon Savdo va Bozor Botiga</b> xush kelibsiz.\n\n"
            f"Botdan to'liq foydalanish va e'lon berish uchun iltimos, <b>Ismingiz va Familiyangizni</b> kiriting:",
            reply_markup=get_cancel_kb()
        )
        await state.set_state(RegisterStates.full_name)
    else:
        await message.answer(
            f"Assalomu alaykum, <b>{user.get('full_name', message.from_user.full_name)}</b>!\n\n"
            f"Kerakli bo'limni tanlang yoki <b>🌐 E'lon bering (Web App)</b> tugmasini bosing:",
            reply_markup=get_main_menu(is_admin=is_admin)
        )

@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.id in config.ADMIN_IDS
    await message.answer(
        "Amal bekor qilindi. Bosh menyudasiz.",
        reply_markup=get_main_menu(is_admin=is_admin)
    )

@router.callback_query(F.data == "cancel_action")
async def cb_cancel_action(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    is_admin = call.from_user.id in config.ADMIN_IDS
    await call.message.answer(
        "Amal bekor qilindi.",
        reply_markup=get_main_menu(is_admin=is_admin)
    )
    await call.answer()

@router.callback_query(F.data == "close_view")
async def cb_close_view(call: CallbackQuery):
    await call.message.delete()
    await call.answer("Yopildi")
