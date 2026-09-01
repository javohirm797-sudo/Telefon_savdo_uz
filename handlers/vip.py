from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database import db
from states import VIPPaymentStates
from keyboards import get_main_menu, get_cancel_kb, get_vip_plans_kb, get_admin_verify_payment_kb
from utils import format_vip_info
import config

router = Router()

@router.message(F.text == "⭐️ VIP xizmati")
@router.message(Command("vip"))
async def show_vip_service(message: Message):
    user_id = message.from_user.id
    ads = await db.get_user_ads(user_id)
    active_ads = [a for a in ads if a["status"] == "active" and not a["is_vip"]]

    vip_text = format_vip_info()
    
    if not active_ads:
        await message.answer(
            f"{vip_text}\n\n"
            f"ℹ️ <i>Sizda hozircha VIP qilish uchun faol e'lon mavjud emas. Avval «➕ E'lon joylash» tugmasi orqali e'lon bering.</i>"
        )
        return

    keyboard = []
    for ad in active_ads:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📱 {ad['brand']} {ad['model']} ({ad['price']})",
                callback_data=f"select_ad_for_vip:{ad['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])

    await message.answer(
        f"{vip_text}\n\n"
        f"👇 <b>Qaysi e'loningizni VIP qilmoqchisiz? Tanlang:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith("select_ad_for_vip:"))
async def process_select_ad_for_vip(call: CallbackQuery):
    ad_id = int(call.data.split(":")[1])
    await call.message.edit_text(
        f"⭐️ <b>#{ad_id} raqamli e'loningiz uchun muddatni tanlang:</b>",
        reply_markup=get_vip_plans_kb(ad_id=ad_id)
    )
    await call.answer()

@router.callback_query(F.data.startswith("buy_vip:"))
async def process_buy_vip_plan(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    ad_id = int(parts[1])
    plan_key = parts[2]
    plan = config.VIP_PLANS.get(plan_key)

    if not plan:
        await call.answer("Tarif topilmadi.", show_alert=True)
        return

    await state.set_state(VIPPaymentStates.upload_receipt)
    await state.update_data(
        ad_id=ad_id,
        plan_days=plan["days"],
        amount=plan["price"]
    )

    await call.message.delete()
    await call.message.answer(
        f"⭐️ <b>VIP E'lon To'lovi</b>\n\n"
        f"📌 E'lon ID: <b>#{ad_id}</b>\n"
        f"⏳ Muddat: <b>{plan['days']} kun</b>\n"
        f"💵 To'lov summasi: <b>{plan['price']:,} so'm</b>\n\n"
        f"💳 <b>To'lov uchun karta (Click / Payme / Uzum):</b>\n"
        f"<code>{config.CARD_NUMBER}</code>\n"
        f"👤 <b>Karta egasi:</b> <b>{config.CARD_HOLDER}</b>\n\n"
        f"⚠️ <i>To'lovni amalga oshirgach, to'lov cheki skrinshotini (rasmini) pastga yuboring:</i>",
        reply_markup=get_cancel_kb()
    )
    await call.answer()

@router.message(VIPPaymentStates.upload_receipt, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext, bot: Bot):
    receipt_photo_id = message.photo[-1].file_id
    data = await state.get_data()
    ad_id = data["ad_id"]
    plan_days = data["plan_days"]
    amount = data["amount"]
    user_id = message.from_user.id

    payment_id = await db.add_vip_payment(
        ad_id=ad_id,
        user_id=user_id,
        plan_days=plan_days,
        amount=amount,
        receipt_photo_id=receipt_photo_id
    )
    await state.clear()

    # Foydalanuvchiga xabar
    is_admin = user_id in config.ADMIN_IDS
    await message.answer(
        f"✅ <b>To'lov cheki qabul qilindi!</b>\n\n"
        f"🧾 Chek ID: <b>#{payment_id}</b>\n"
        f"Adminlar to'lovni tekshirib tasdiqlaganlaridan so'ng e'loningiz avtomatik VIP holatiga o'tadi va sizga xabar beriladi.",
        reply_markup=get_main_menu(is_admin=is_admin)
    )

    # Adminlarga yuborish
    ad = await db.get_ad_by_id(ad_id)
    ad_title = f"{ad['brand']} {ad['model']}" if ad else f"ID #{ad_id}"
    username_str = f"@{message.from_user.username}" if message.from_user.username else f"ID: {user_id}"

    admin_caption = (
        f"🔔 <b>YANGI VIP TO'LOV SO'ROVI!</b>\n\n"
        f"🧾 To'lov ID: <b>#{payment_id}</b>\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name} ({username_str})\n"
        f"📱 E'lon: <b>{ad_title}</b> (ID #{ad_id})\n"
        f"⏳ Muddat: <b>{plan_days} kun</b>\n"
        f"💰 Summa: <b>{amount:,} so'm</b>\n"
        f"💳 Karta: {config.CARD_NUMBER} ({config.CARD_HOLDER})"
    )

    admin_kb = get_admin_verify_payment_kb(payment_id=payment_id, ad_id=ad_id, plan_days=plan_days)

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=receipt_photo_id,
                caption=admin_caption,
                reply_markup=admin_kb
            )
        except Exception as e:
            pass

@router.message(VIPPaymentStates.upload_receipt)
async def process_invalid_receipt(message: Message):
    await message.answer(
        "⚠️ Iltimos, to'lov chekining rasmini (skrinshot) yuboring yoki bekor qilish uchun «❌ Bekor qilish» tugmasini bosing."
    )
