import re
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import db
from states import RegisterStates
from keyboards import get_main_menu, get_phone_share_kb
import config

router = Router()

@router.message(RegisterStates.full_name)
async def process_full_name(message: Message, state: FSMContext):
    name = message.text.strip() if message.text else ""
    if len(name) < 3:
        await message.answer("Iltimos, haqiqiy ism va familiyangizni to'liq kiriting (kamida 3 ta belgi):")
        return

    await state.update_data(full_name=name)
    await state.set_state(RegisterStates.phone_number)
    await message.answer(
        f"Rahmat, <b>{name}</b>!\n\n"
        f"Endi telefon raqamingizni tasdiqlash uchun quyidagi <b>«📱 Telefon raqamimni yuborish»</b> tugmasini bosing yoki qo'lda kiriting (masalan: <code>+998901234567</code>):",
        reply_markup=get_phone_share_kb()
    )

@router.message(RegisterStates.phone_number, F.contact)
async def process_contact(message: Message, state: FSMContext):
    phone_number = message.contact.phone_number
    if not phone_number.startswith("+"):
        phone_number = "+" + phone_number

    data = await state.get_data()
    full_name = data.get("full_name", message.from_user.full_name)
    username = message.from_user.username

    await db.add_user(
        telegram_id=message.from_user.id,
        full_name=full_name,
        phone_number=phone_number,
        username=username
    )
    await state.clear()

    is_admin = message.from_user.id in config.ADMIN_IDS
    await message.answer(
        f"🎉 <b>Tabriklaymiz, siz muvaffaqiyatli ro'yxatdan o'tdingiz!</b>\n\n"
        f"👤 Ism: <b>{full_name}</b>\n"
        f"📞 Telefon: <b>{phone_number}</b>\n\n"
        f"Endi bot orqali e'lon joylashingiz yoki bozor bo'limidan telefonlarni ko'rishingiz mumkin.",
        reply_markup=get_main_menu(is_admin=is_admin)
    )

@router.message(RegisterStates.phone_number, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    # Telefon raqam formatini tekshirish (+998...)
    clean_phone = re.sub(r"[^\d+]", "", phone)
    if not (clean_phone.startswith("+998") and len(clean_phone) == 13) and not (clean_phone.startswith("998") and len(clean_phone) == 12):
        await message.answer(
            "⚠️ Noto'g'ri telefon raqami formati!\n\n"
            "Iltimos, pastdagi <b>«📱 Telefon raqamimni yuborish»</b> tugmasini bosing yoki <code>+998901234567</code> formatida yozing."
        )
        return

    if not clean_phone.startswith("+"):
        clean_phone = "+" + clean_phone

    data = await state.get_data()
    full_name = data.get("full_name", message.from_user.full_name)
    username = message.from_user.username

    await db.add_user(
        telegram_id=message.from_user.id,
        full_name=full_name,
        phone_number=clean_phone,
        username=username
    )
    await state.clear()

    is_admin = message.from_user.id in config.ADMIN_IDS
    await message.answer(
        f"🎉 <b>Tabriklaymiz, siz muvaffaqiyatli ro'yxatdan o'tdingiz!</b>\n\n"
        f"👤 Ism: <b>{full_name}</b>\n"
        f"📞 Telefon: <b>{clean_phone}</b>\n\n"
        f"Endi bemalol e'lon berishingiz yoki telefon xarid qilishingiz mumkin.",
        reply_markup=get_main_menu(is_admin=is_admin)
    )
