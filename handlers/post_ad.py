from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import db
from states import PostAdStates, RegisterStates
from keyboards import (
    get_main_menu, get_cancel_kb, get_skip_or_cancel_kb,
    get_brands_inline_kb, get_models_inline_kb, get_memory_inline_kb,
    get_condition_inline_kb, get_regions_inline_kb, get_confirm_ad_kb,
    get_vip_plans_kb
)
from utils import format_ad_caption
import config

router = Router()

@router.message(F.text == "➕ E'lon joylash")
@router.message(Command("post_ad"))
async def start_post_ad(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await message.answer(
            "⚠️ E'lon joylashdan oldin iltimos ro'yxatdan o'ting.\n\nIsmingizni kiriting:",
            reply_markup=get_cancel_kb()
        )
        await state.set_state(RegisterStates.full_name)
        return

    await state.clear()
    await state.update_data(
        user_id=user_id,
        contact_phone=user.get("phone_number", ""),
        contact_username=user.get("username", message.from_user.username or "")
    )
    
    await state.set_state(PostAdStates.brand)
    await message.answer(
        "📱 <b>1-qadam: Telefon brendini tanlang:</b>",
        reply_markup=get_brands_inline_kb()
    )

# 1. Brend tanlandi
@router.callback_query(PostAdStates.brand, F.data.startswith("set_brand:"))
async def process_brand_chosen(call: CallbackQuery, state: FSMContext):
    brand = call.data.split(":")[1]
    await state.update_data(brand=brand)
    
    if brand == "Boshqa brend":
        await state.set_state(PostAdStates.custom_model)
        await call.message.edit_text(
            "✍️ Iltimos, telefoningizning to'liq <b>Brend va Modelini</b> yozib yuboring (Masalan: <i>Sony Xperia 1 V</i>):"
        )
    else:
        await state.set_state(PostAdStates.model)
        await call.message.edit_text(
            f"📱 <b>{brand}</b> brendini tanladingiz.\n\n<b>2-qadam: Modelini tanlang:</b>",
            reply_markup=get_models_inline_kb(brand=brand, page=0)
        )
    await call.answer()

# Brend sahifalash
@router.callback_query(PostAdStates.model, F.data.startswith("set_model_page:"))
async def process_model_pagination(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    brand = parts[1]
    page = int(parts[2])
    await call.message.edit_text(
        f"📱 <b>{brand}</b> modellari:\n\n<b>2-qadam: Modelini tanlang:</b>",
        reply_markup=get_models_inline_kb(brand=brand, page=page)
    )
    await call.answer()

@router.callback_query(PostAdStates.model, F.data == "back_to_brands")
async def back_to_brands_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(PostAdStates.brand)
    await call.message.edit_text(
        "📱 <b>Telefon brendini tanlang:</b>",
        reply_markup=get_brands_inline_kb()
    )
    await call.answer()

# 2. Model tanlandi
@router.callback_query(PostAdStates.model, F.data.startswith("set_model:"))
async def process_model_chosen(call: CallbackQuery, state: FSMContext):
    model = call.data.split(":")[1]
    if model == "custom":
        await state.set_state(PostAdStates.custom_model)
        await call.message.edit_text("✍️ Telefon modelining aniq nomini yozib yuboring:")
    else:
        await state.update_data(model=model)
        await state.set_state(PostAdStates.condition)
        await call.message.edit_text(
            f"Tanlandi: <b>{model}</b>\n\n<b>3-qadam: Telefon holatini tanlang:</b>",
            reply_markup=get_condition_inline_kb()
        )
    await call.answer()

# Custom model kiritilganda
@router.message(PostAdStates.custom_model)
async def process_custom_model(message: Message, state: FSMContext):
    custom_model = message.text.strip()
    data = await state.get_data()
    brand = data.get("brand", "Boshqa")
    if brand == "Boshqa brend":
        await state.update_data(brand=custom_model.split()[0] if custom_model else "Boshqa", model=custom_model)
    else:
        await state.update_data(model=custom_model)

    await state.set_state(PostAdStates.condition)
    await message.answer(
        f"Model: <b>{custom_model}</b>\n\n<b>3-qadam: Telefon holatini tanlang:</b>",
        reply_markup=get_condition_inline_kb()
    )

# 3. Holat tanlandi
@router.callback_query(PostAdStates.condition, F.data.startswith("set_cond:"))
async def process_condition_chosen(call: CallbackQuery, state: FSMContext):
    condition = call.data.split(":")[1]
    await state.update_data(condition=condition)
    
    await state.set_state(PostAdStates.memory)
    await call.message.edit_text(
        f"Holati: <b>{condition}</b>\n\n<b>4-qadam: Telefon xotirasini tanlang:</b>",
        reply_markup=get_memory_inline_kb()
    )
    await call.answer()

# 4. Xotira tanlandi
@router.callback_query(PostAdStates.memory, F.data.startswith("set_mem:"))
async def process_memory_chosen(call: CallbackQuery, state: FSMContext):
    memory = call.data.split(":")[1]
    await state.update_data(memory=memory)
    
    await state.set_state(PostAdStates.battery)
    await call.message.delete()
    await call.message.answer(
        f"Xotirasi: <b>{memory}</b>\n\n"
        f"🔋 <b>5-qadam: Batareya holati (Yomkost / %) ni kiriting:</b>\n"
        f"(Masalan: <i>88%</i>, <i>100%</i> yoki <i>Yangi batareya qo'yilgan</i>).\n\n"
        f"<i>Agar bilmasangiz «⏩ O'tkazib yuborish» tugmasini bosing:</i>",
        reply_markup=get_skip_or_cancel_kb()
    )
    await call.answer()

# 5. Batareya kiritildi yoki o'tkazib yuborildi
@router.message(PostAdStates.battery)
async def process_battery(message: Message, state: FSMContext):
    if message.text == "⏩ O'tkazib yuborish":
        battery = "—"
    else:
        battery = message.text.strip()
    
    await state.update_data(battery=battery)
    await state.set_state(PostAdStates.color)
    await message.answer(
        f"🎨 <b>6-qadam: Telefon rangini kiriting:</b>\n"
        f"(Masalan: <i>Qora (Black)</i>, <i>Natural Titanium</i>, <i>Oq</i>).\n\n"
        f"<i>Yoki «⏩ O'tkazib yuborish» tugmasini bosing:</i>",
        reply_markup=get_skip_or_cancel_kb()
    )

# 6. Rang kiritildi
@router.message(PostAdStates.color)
async def process_color(message: Message, state: FSMContext):
    if message.text == "⏩ O'tkazib yuborish":
        color = "—"
    else:
        color = message.text.strip()

    await state.update_data(color=color)
    await state.set_state(PostAdStates.price)
    await message.answer(
        f"💵 <b>7-qadam: Telefon narxini kiriting:</b>\n"
        f"(Masalan: <i>$650</i>, <i>8 200 000 so'm</i> yoki <i>$450 (kami bor / kelishamiz)</i>):",
        reply_markup=get_cancel_kb()
    )

# 7. Narx kiritildi
@router.message(PostAdStates.price)
async def process_price(message: Message, state: FSMContext):
    price = message.text.strip()
    if len(price) < 2:
        await message.answer("Iltimos, narxni to'g'ri kiriting (Masalan: $500 yoki 6 000 000 so'm):")
        return

    await state.update_data(price=price)
    await state.set_state(PostAdStates.region)
    await message.answer(
        f"Narxi: <b>{price}</b>\n\n<b>8-qadam: Qaysi viloyat / shahardasiz?</b>",
        reply_markup=get_regions_inline_kb()
    )

# 8. Hudud tanlandi
@router.callback_query(PostAdStates.region, F.data.startswith("set_reg:"))
async def process_region_chosen(call: CallbackQuery, state: FSMContext):
    region = call.data.split(":")[1]
    await state.update_data(region=region)
    
    await state.set_state(PostAdStates.photo)
    await call.message.delete()
    await call.message.answer(
        f"📍 Hudud: <b>{region}</b>\n\n"
        f"📷 <b>9-qadam: Telefoningiz rasmini yuboring!</b>\n\n"
        f"⚠️ <b>DIQQAT:</b> Qoidalarga asosan <b>FAQATGINA 1 DONA</b> tiniq rasm yuboring (Albom yoki bir nechta rasm yubormang):",
        reply_markup=get_cancel_kb()
    )
    await call.answer()

# 9. Rasm qabul qilish (FAQAT 1 DONA RASM)
@router.message(PostAdStates.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    # Faqat 1 dona rasm eng yuqori sifatda olinadi
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    
    await state.set_state(PostAdStates.description)
    await message.answer(
        "✅ Rasm qabul qilindi!\n\n"
        "📝 <b>10-qadam: Qo'shimcha ma'lumot yozing:</b>\n"
        "(Masalan: <i>Karopka-dokumenti bor, aybi yo'q, ekranda plyonka, chexol qo'shib beriladi, obmen yo'q</i>).\n\n"
        "<i>Yoki «⏩ O'tkazib yuborish» tugmasini bosing:</i>",
        reply_markup=get_skip_or_cancel_kb()
    )

@router.message(PostAdStates.photo)
async def process_invalid_photo(message: Message):
    await message.answer(
        "⚠️ <b>Iltimos, faqatgina 1 dona telefon rasmini yuboring!</b>\n"
        "Fayl yoki video emas, aynan rasm (Photo) formatida bo'lishi kerak."
    )

# 10. Qo'shimcha ma'lumot
@router.message(PostAdStates.description)
async def process_description(message: Message, state: FSMContext):
    if message.text == "⏩ O'tkazib yuborish":
        description = "Mavjud emas"
    else:
        description = message.text.strip()

    await state.update_data(description=description)
    data = await state.get_data()
    
    await state.set_state(PostAdStates.confirm)
    
    caption = format_ad_caption(data, is_preview=True)
    await message.answer_photo(
        photo=data["photo_id"],
        caption=f"📋 <b>E'LONINGIZ TAYYOR BO'LDI!</b>\n\n{caption}\n\n"
                f"<i>E'lonni bepul chop etish yoki tezroq sotish uchun VIP xizmatidan foydalanishingiz mumkin:</i>",
        reply_markup=get_confirm_ad_kb()
    )

# 11. E'lonni bepul chop etish
@router.callback_query(PostAdStates.confirm, F.data == "confirm_ad_publish")
async def process_publish_free(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["is_vip"] = False
    
    ad_id = await db.add_ad(data)
    await state.clear()
    
    await call.message.delete()
    is_admin = call.from_user.id in config.ADMIN_IDS
    await call.message.answer(
        f"🎉 <b>E'loningiz muvaffaqiyatli qabul qilindi va bozorga joylandi!</b>\n\n"
        f"🆔 E'lon raqami: <b>#{ad_id}</b>\n\n"
        f"Xaridorlar sizning e'loningizni «🛍 Telefonlar bozori» bo'limida ko'rishlari va siz bilan bog'lanishlari mumkin.",
        reply_markup=get_main_menu(is_admin=is_admin)
    )
    await call.answer("E'lon chop etildi!")

# 11. E'lonni VIP sifatida joylash (VIP tarif tanlash)
@router.callback_query(PostAdStates.confirm, F.data == "confirm_ad_vip")
async def process_publish_vip(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["is_vip"] = False
    
    ad_id = await db.add_ad(data)
    await state.clear()
    
    await call.message.delete()
    await call.message.answer(
        f"✅ E'loningiz saqlandi (ID: <b>#{ad_id}</b>)!\n\n"
        f"⭐️ <b>E'loningizni eng yuqoriga chiqarish uchun VIP tarifni tanlang:</b>",
        reply_markup=get_vip_plans_kb(ad_id=ad_id)
    )
    await call.answer()
