from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import (
    get_two_ads_navigation_kb, get_brands_inline_kb, 
    get_models_inline_kb, get_regions_inline_kb
)
from utils import format_ad_caption

router = Router()

# Foydalanuvchilarning filtrlari va oxirgi yuborilgan xabar ID lari
user_filters = {}
user_ad_messages = {}  # {user_id: [msg_id_1, msg_id_2, ...]}

PAGE_SIZE = 2

async def clear_previous_ad_messages(bot, chat_id: int, user_id: int):
    """Oldingi sahifadagi xabarlarni tozalash (ekranni toza saqlash uchun)"""
    msg_ids = user_ad_messages.get(user_id, [])
    for m_id in msg_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=m_id)
        except Exception:
            pass
    user_ad_messages[user_id] = []

async def show_ad_page(event, user_id: int, page_index: int = 0, is_edit: bool = False):
    """E'lonlar sahifasini 2 tadan qilib chiqarish"""
    bot = event.bot
    chat_id = event.from_user.id if isinstance(event, CallbackQuery) else event.chat.id
    message = event.message if isinstance(event, CallbackQuery) else event

    filt = user_filters.get(user_id, {})
    brand = filt.get("brand")
    model = filt.get("model")
    region = filt.get("region")

    total_count = await db.get_active_ads_count(brand=brand, model=model, region=region)
    
    if total_count == 0:
        filter_desc = []
        if brand: filter_desc.append(f"Brend: <b>{brand}</b>")
        if model: filter_desc.append(f"Model: <b>{model}</b>")
        if region: filter_desc.append(f"Viloyat: <b>{region}</b>")
        filter_text = f" ({', '.join(filter_desc)})" if filter_desc else ""

        text = (
            f"🛍 <b>Ayni paytda faol e'lonlar mavjud emas{filter_text}.</b>\n\n"
            f"Birozdan so'ng qayta tekshirib ko'ring yoki boshqa brend / modelni tanlang."
        )
        await clear_previous_ad_messages(bot, chat_id, user_id)
        try:
            if isinstance(event, CallbackQuery):
                await message.delete()
        except Exception:
            pass
        msg = await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=get_brands_inline_kb(for_filter=True)
        )
        user_ad_messages[user_id] = [msg.message_id]
        return

    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE

    if page_index >= total_pages:
        page_index = total_pages - 1
    if page_index < 0:
        page_index = 0

    offset = page_index * PAGE_SIZE
    ads = await db.get_active_ads(brand=brand, model=model, region=region, limit=PAGE_SIZE, offset=offset)
    if not ads:
        return

    # Oldingi xabarlarni tozalaymiz
    await clear_previous_ad_messages(bot, chat_id, user_id)
    try:
        if isinstance(event, CallbackQuery):
            await message.delete()
    except Exception:
        pass

    sent_msg_ids = []

    if len(ads) == 1:
        # 1 ta e'lon bo'lsa
        ad = ads[0]
        caption = f"📱 <b>[{total_count}/{total_count}] E'lon</b>\n\n" + format_ad_caption(ad, is_preview=False)
        kb = get_ad_navigation_kb(
            ad_id=ad["id"],
            current_index=page_index,
            total_count=total_pages,
            seller_username=ad.get("contact_username", ""),
            seller_phone=ad.get("contact_phone", "")
        )
        msg = await bot.send_photo(
            chat_id=chat_id,
            photo=ad["photo_id"],
            caption=caption,
            reply_markup=kb
        )
        sent_msg_ids.append(msg.message_id)
    else:
        # 2 ta e'lon bo'lsa
        ad1, ad2 = ads[0], ads[1]
        ad1_idx = offset + 1
        ad2_idx = offset + 2

        caption1 = f"📱 <b>[{ad1_idx}/{total_count}] 1-TELEFON:</b>\n\n" + format_ad_caption(ad1, is_preview=False)
        caption2 = f"📱 <b>[{ad2_idx}/{total_count}] 2-TELEFON:</b>\n\n" + format_ad_caption(ad2, is_preview=False)

        kb1 = get_single_ad_contact_kb(ad1)
        msg1 = await bot.send_photo(
            chat_id=chat_id,
            photo=ad1["photo_id"],
            caption=caption1,
            reply_markup=kb1
        )
        sent_msg_ids.append(msg1.message_id)

        kb2 = get_two_ads_navigation_kb(ad2, current_page=page_index, total_pages=total_pages, total_count=total_count)
        msg2 = await bot.send_photo(
            chat_id=chat_id,
            photo=ad2["photo_id"],
            caption=caption2,
            reply_markup=kb2
        )
        sent_msg_ids.append(msg2.message_id)

    user_ad_messages[user_id] = sent_msg_ids

@router.message(F.text == "🛍 Telefonlar bozori (E'lonlar)")
@router.message(Command("market"))
async def open_market(message: Message):
    user_id = message.from_user.id
    user_filters[user_id] = {}  # Filterlarni tozalash
    await show_ad_page(message, user_id=user_id, page_index=0, is_edit=False)

@router.callback_query(F.data.startswith("view_nav:"))
async def process_view_nav(call: CallbackQuery):
    page_index = int(call.data.split(":")[1])
    user_id = call.from_user.id
    await show_ad_page(call, user_id=user_id, page_index=page_index, is_edit=True)
    await call.answer()

@router.callback_query(F.data.startswith("show_phone:"))
async def process_show_phone(call: CallbackQuery):
    ad_id = int(call.data.split(":")[1])
    ad = await db.get_ad_by_id(ad_id)
    if ad:
        phone = ad.get("contact_phone", "Mavjud emas")
        await call.answer(f"📞 Sotuvchi raqami:\n{phone}", show_alert=True)
    else:
        await call.answer("E'lon topilmadi.", show_alert=True)

# Filter by Brand
@router.callback_query(F.data == "filter_by_brand")
async def choose_filter_brand(call: CallbackQuery):
    user_id = call.from_user.id
    await clear_previous_ad_messages(call.bot, call.message.chat.id, user_id)
    try:
        await call.message.delete()
    except Exception:
        pass
    msg = await call.message.answer(
        "🔍 <b>Qaysi brend bo'yicha qidirmoqchisiz?</b>",
        reply_markup=get_brands_inline_kb(for_filter=True)
    )
    user_ad_messages[user_id] = [msg.message_id]
    await call.answer()

@router.callback_query(F.data.startswith("filter_brand:"))
async def process_filter_brand(call: CallbackQuery):
    brand = call.data.split(":")[1]
    user_id = call.from_user.id
    if user_id not in user_filters:
        user_filters[user_id] = {}

    if brand == "all":
        user_filters[user_id].pop("brand", None)
        user_filters[user_id].pop("model", None)
        await show_ad_page(call, user_id=user_id, page_index=0, is_edit=False)
    else:
        user_filters[user_id]["brand"] = brand
        user_filters[user_id].pop("model", None)
        await call.message.edit_text(
            f"🔍 <b>{brand}</b> modeli bo'yicha aniqroq tanlaysizmi yoki barchasini ko'rasizmi?",
            reply_markup=get_models_inline_kb(brand=brand, for_filter=True, page=0)
        )
    await call.answer()

@router.callback_query(F.data.startswith("filter_model_page:"))
async def process_filter_model_pagination(call: CallbackQuery):
    parts = call.data.split(":")
    brand = parts[1]
    page = int(parts[2])
    await call.message.edit_text(
        f"🔍 <b>{brand}</b> modellari:",
        reply_markup=get_models_inline_kb(brand=brand, for_filter=True, page=page)
    )
    await call.answer()

@router.callback_query(F.data == "back_to_filter_brands")
async def back_to_filter_brands(call: CallbackQuery):
    await call.message.edit_text(
        "🔍 <b>Brendni tanlang:</b>",
        reply_markup=get_brands_inline_kb(for_filter=True)
    )
    await call.answer()

@router.callback_query(F.data.startswith("filter_model:"))
async def process_filter_model(call: CallbackQuery):
    model = call.data.split(":")[1]
    user_id = call.from_user.id
    if user_id not in user_filters:
        user_filters[user_id] = {}

    if model == "all":
        user_filters[user_id].pop("model", None)
    else:
        user_filters[user_id]["model"] = model

    await show_ad_page(call, user_id=user_id, page_index=0, is_edit=False)
    await call.answer()

# Filter by Region
@router.callback_query(F.data == "filter_by_region")
async def choose_filter_region(call: CallbackQuery):
    user_id = call.from_user.id
    await clear_previous_ad_messages(call.bot, call.message.chat.id, user_id)
    try:
        await call.message.delete()
    except Exception:
        pass
    msg = await call.message.answer(
        "📍 <b>Qaysi viloyat / shahar bo'yicha qidirmoqchisiz?</b>",
        reply_markup=get_regions_inline_kb(for_filter=True)
    )
    user_ad_messages[user_id] = [msg.message_id]
    await call.answer()

@router.callback_query(F.data.startswith("filter_reg:"))
async def process_filter_region(call: CallbackQuery):
    region = call.data.split(":")[1]
    user_id = call.from_user.id
    if user_id not in user_filters:
        user_filters[user_id] = {}

    if region == "all":
        user_filters[user_id].pop("region", None)
    else:
        user_filters[user_id]["region"] = region

    await show_ad_page(call, user_id=user_id, page_index=0, is_edit=False)
    await call.answer()

@router.callback_query(F.data == "ignore")
async def process_ignore(call: CallbackQuery):
    await call.answer()

