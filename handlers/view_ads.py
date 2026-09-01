from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import (
    get_ad_navigation_kb, get_brands_inline_kb, 
    get_models_inline_kb, get_regions_inline_kb
)
from utils import format_ad_caption

router = Router()

# Global view filter cache or state
user_filters = {}

async def show_ad_page(message_or_call, user_id: int, page_index: int = 0, is_edit: bool = False):
    filt = user_filters.get(user_id, {})
    brand = filt.get("brand")
    model = filt.get("model")
    region = filt.get("region")

    total_count = await db.get_active_ads_count(brand=brand, model=model, region=region)
    
    if total_count == 0:
        text = "🛍 <b>Ayni paytda ushbu parametrlar bo'yicha faol e'lonlar mavjud emas.</b>\n\nBirozdan so'ng qayta tekshirib ko'ring yoki boshqa brendni tanlang."
        if is_edit:
            try:
                await message_or_call.message.delete()
            except Exception:
                pass
            await message_or_call.message.answer(text)
        else:
            await message_or_call.answer(text)
        return

    if page_index >= total_count:
        page_index = total_count - 1
    if page_index < 0:
        page_index = 0

    ads = await db.get_active_ads(brand=brand, model=model, region=region, limit=1, offset=page_index)
    if not ads:
        return

    ad = ads[0]
    caption = format_ad_caption(ad, is_preview=False)
    kb = get_ad_navigation_kb(
        ad_id=ad["id"],
        current_index=page_index,
        total_count=total_count,
        seller_username=ad.get("contact_username", ""),
        seller_phone=ad.get("contact_phone", "")
    )

    if is_edit:
        try:
            media = InputMediaPhoto(media=ad["photo_id"], caption=caption)
            await message_or_call.message.edit_media(media=media, reply_markup=kb)
        except Exception:
            await message_or_call.message.delete()
            await message_or_call.message.answer_photo(
                photo=ad["photo_id"],
                caption=caption,
                reply_markup=kb
            )
    else:
        await message_or_call.answer_photo(
            photo=ad["photo_id"],
            caption=caption,
            reply_markup=kb
        )

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
    await call.message.delete()
    await call.message.answer(
        "🔍 <b>Qaysi brend bo'yicha qidirmoqchisiz?</b>",
        reply_markup=get_brands_inline_kb(for_filter=True)
    )
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
        await call.message.delete()
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

    await call.message.delete()
    await show_ad_page(call, user_id=user_id, page_index=0, is_edit=False)
    await call.answer()

# Filter by Region
@router.callback_query(F.data == "filter_by_region")
async def choose_filter_region(call: CallbackQuery):
    await call.message.delete()
    await call.message.answer(
        "📍 <b>Qaysi viloyat / shahar bo'yicha qidirmoqchisiz?</b>",
        reply_markup=get_regions_inline_kb(for_filter=True)
    )
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

    await call.message.delete()
    await show_ad_page(call, user_id=user_id, page_index=0, is_edit=False)
    await call.answer()

@router.callback_query(F.data == "ignore")
async def process_ignore(call: CallbackQuery):
    await call.answer()
