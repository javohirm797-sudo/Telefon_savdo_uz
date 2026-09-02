import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from database import db
from states import AuctionCreateStates, AuctionBidStates, RegisterStates
from keyboards import (
    get_main_menu, get_cancel_kb, get_skip_or_cancel_kb,
    get_brands_inline_kb, get_models_inline_kb, get_memory_inline_kb,
    get_condition_inline_kb, get_regions_inline_kb,
    get_auction_min_steps_kb, get_auction_duration_kb, get_confirm_auction_kb,
    get_auction_navigation_kb
)
from utils import format_auction_caption

logger = logging.getLogger(__name__)
router = Router()

user_auction_messages = {}  # {user_id: [msg_id]}

async def clear_previous_auction_messages(bot, chat_id: int, user_id: int):
    msg_ids = user_auction_messages.get(user_id, [])
    for m_id in msg_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=m_id)
        except Exception:
            pass
    user_auction_messages[user_id] = []

# ==================== AUKSIONLARNI KO'RISH ====================

async def show_auction_page(event, user_id: int, page_index: int = 0):
    bot = event.bot
    chat_id = event.from_user.id if isinstance(event, CallbackQuery) else event.chat.id
    message = event.message if isinstance(event, CallbackQuery) else event

    total_count = await db.get_active_auctions_count()
    if total_count == 0:
        await clear_previous_auction_messages(bot, chat_id, user_id)
        try:
            if isinstance(event, CallbackQuery):
                await message.delete()
        except Exception:
            pass
        msg = await bot.send_message(
            chat_id=chat_id,
            text=(
                "🔨 <b>Ayni paytda faol auksionlar mavjud emas.</b>\n\n"
                "Siz birinchi bo'lib telefoningizni auksionga qo'yishingiz mumkin! "
                "Buning uchun pastdagi <b>➕ Auksionga qo'yish</b> tugmasini bosing."
            )
        )
        user_auction_messages[user_id] = [msg.message_id]
        return

    if page_index >= total_count:
        page_index = total_count - 1
    if page_index < 0:
        page_index = 0

    auctions = await db.get_active_auctions(limit=1, offset=page_index)
    if not auctions:
        return

    auction = auctions[0]
    caption = format_auction_caption(auction, is_preview=False)
    kb = get_auction_navigation_kb(
        auction=auction,
        current_index=page_index,
        total_count=total_count,
        viewer_id=user_id
    )

    await clear_previous_auction_messages(bot, chat_id, user_id)
    try:
        if isinstance(event, CallbackQuery):
            await message.delete()
    except Exception:
        pass

    msg = await bot.send_photo(
        chat_id=chat_id,
        photo=auction["photo_id"],
        caption=caption,
        reply_markup=kb
    )
    user_auction_messages[user_id] = [msg.message_id]

@router.message(F.text == "🔨 Kimoshdi (Auksion)")
@router.message(Command("auction"))
async def open_auctions(message: Message):
    user_id = message.from_user.id
    await show_auction_page(message, user_id=user_id, page_index=0)

@router.callback_query(F.data.startswith("auc_nav:"))
async def process_auction_nav(call: CallbackQuery):
    page_index = int(call.data.split(":")[1])
    user_id = call.from_user.id
    await show_auction_page(call, user_id=user_id, page_index=page_index)
    await call.answer()

# ==================== STAVKA QO'YISH (NARX TAKLIF QILISH) ====================

@router.callback_query(F.data.startswith("bid_quick:"))
async def process_quick_bid(call: CallbackQuery):
    parts = call.data.split(":")
    auction_id = int(parts[1])
    bid_amount = int(parts[2])
    user_id = call.from_user.id
    user_name = call.from_user.full_name or "Xaridor"

    success, msg, prev_winner, auc = await db.place_bid(
        auction_id=auction_id,
        user_id=user_id,
        user_name=user_name,
        bid_amount=bid_amount
    )

    if not success:
        await call.answer(f"❌ {msg}", show_alert=True)
        return

    await call.answer(f"✅ {msg}", show_alert=True)

    # Avvalgi stavka egasiga bildirishnoma
    if prev_winner and prev_winner["user_id"] != user_id:
        try:
            item_name = f"{auc.get('brand', '')} {auc.get('model', '')}"
            await call.bot.send_message(
                chat_id=prev_winner["user_id"],
                text=(
                    f"⚠️ <b>DIQQAT! STAVKANGIZDAN OSHIRISHDI!</b>\n\n"
                    f"Siz qatnashayotgan <b>{item_name}</b> auksionida boshqa xaridor "
                    f"yuqoriroq narx (<b>{bid_amount:,} so'm</b>) taklif qildi!\n\n"
                    f"G'oliblikni boy bermaslik uchun tezda botga kiring va yangi stavka qo'ying!"
                )
            )
        except Exception as e:
            logger.warning(f"Prev winner bildirishnoma xatosi: {e}")

    # Sotuvchiga bildirishnoma
    if auc and auc["user_id"] != user_id:
        try:
            item_name = f"{auc.get('brand', '')} {auc.get('model', '')}"
            await call.bot.send_message(
                chat_id=auc["user_id"],
                text=(
                    f"🔔 <b>Auksioningizga yangi taklif!</b>\n\n"
                    f"<b>{item_name}</b> telefoningiz uchun yangi stavka qo'yildi: "
                    f"<b>{bid_amount:,} so'm</b> ({user_name})"
                )
            )
        except Exception as e:
            logger.warning(f"Sotuvchi bildirishnoma xatosi: {e}")

    # Auksion kartasini yangilab ko'rsatamiz
    await show_auction_page(call, user_id=user_id, page_index=0)

@router.callback_query(F.data.startswith("bid_custom:"))
async def process_custom_bid_start(call: CallbackQuery, state: FSMContext):
    auction_id = int(call.data.split(":")[1])
    auction = await db.get_auction_by_id(auction_id)
    if not auction:
        await call.answer("Auksion topilmadi.", show_alert=True)
        return

    curr_winner = auction.get("current_winner_id")
    min_step = auction.get("min_step", 50000)
    curr_price = auction["current_price"]
    required_amount = curr_price if not curr_winner else curr_price + min_step

    await state.set_state(AuctionBidStates.custom_bid)
    await state.update_data(auction_id=auction_id, required_amount=required_amount)

    await call.message.answer(
        f"💰 <b>O'z taklifingizni kiriting:</b>\n\n"
        f"Kamida: <b>{required_amount:,} so'm</b> bo'lishi kerak.\n"
        f"Faqat raqamlarda yozib yuboring (Masalan: <code>{required_amount + 50000}</code>):",
        reply_markup=get_cancel_kb()
    )
    await call.answer()

@router.message(AuctionBidStates.custom_bid)
async def process_custom_bid_submit(message: Message, state: FSMContext):
    data = await state.get_data()
    auction_id = data.get("auction_id")
    user_id = message.from_user.id
    user_name = message.from_user.full_name or "Xaridor"

    raw = message.text.replace(" ", "").replace(",", "").replace(".", "")
    if not raw.isdigit():
        await message.answer("⚠️ Iltimos, narxni faqat raqamlarda kiriting:")
        return

    bid_amount = int(raw)
    success, msg, prev_winner, auc = await db.place_bid(
        auction_id=auction_id,
        user_id=user_id,
        user_name=user_name,
        bid_amount=bid_amount
    )

    if not success:
        await message.answer(f"❌ {msg}\n\nQaytadan kiriting yoki Bekor qilishni bosing:", reply_markup=get_cancel_kb())
        return

    await state.clear()
    is_admin = user_id in [admin_id for admin_id in []]
    await message.answer(f"✅ {msg}", reply_markup=get_main_menu(is_admin=False))

    # Bildirishnomalar
    if prev_winner and prev_winner["user_id"] != user_id:
        try:
            item_name = f"{auc.get('brand', '')} {auc.get('model', '')}"
            await message.bot.send_message(
                chat_id=prev_winner["user_id"],
                text=(
                    f"⚠️ <b>DIQQAT! STAVKANGIZDAN OSHIRISHDI!</b>\n\n"
                    f"Siz qatnashayotgan <b>{item_name}</b> auksionida yangi narx: "
                    f"<b>{bid_amount:,} so'm</b> taklif qilindi!\n\n"
                    f"G'oliblikni saqlab qolish uchun yangi stavka bering!"
                )
            )
        except Exception:
            pass

    if auc and auc["user_id"] != user_id:
        try:
            item_name = f"{auc.get('brand', '')} {auc.get('model', '')}"
            await message.bot.send_message(
                chat_id=auc["user_id"],
                text=(
                    f"🔔 <b>Auksioningizga yangi taklif!</b>\n\n"
                    f"<b>{item_name}</b> uchun yangi narx: <b>{bid_amount:,} so'm</b> ({user_name})"
                )
            )
        except Exception:
            pass

    await show_auction_page(message, user_id=user_id, page_index=0)

# Stavkalar tarixi
@router.callback_query(F.data.startswith("auc_history:"))
async def process_auction_history(call: CallbackQuery):
    auction_id = int(call.data.split(":")[1])
    bids = await db.get_auction_bids(auction_id, limit=8)
    if not bids:
        await call.answer("Ushbu auksionga hali hech qanday stavka qo'yilmagan.", show_alert=True)
        return

    lines = ["📜 <b>So'nggi stavkalar tarixi:</b>\n"]
    for idx, b in enumerate(bids, 1):
        created_str = str(b.get("created_at", ""))[:16]
        lines.append(f"{idx}. {b.get('user_name', 'Foydalanuvchi')} — <b>{b['bid_amount']:,} so'm</b> ({created_str})")

    await call.message.answer("\n".join(lines))
    await call.answer()

# ==================== YANGI AUKSION JOYLASHTIRISH ====================

@router.message(F.text == "➕ Auksionga qo'yish")
@router.message(Command("post_auction"))
async def start_create_auction(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await message.answer(
            "⚠️ Auksion qo'yishdan oldin ro'yxatdan o'ting.\n\nIsmingizni kiriting:",
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
    await state.set_state(AuctionCreateStates.brand)
    await message.answer(
        "🔨 <b>Auksion yaratish — 1-qadam:</b>\n\nTelefon brendini tanlang:",
        reply_markup=get_brands_inline_kb()
    )

@router.callback_query(AuctionCreateStates.brand, F.data.startswith("set_brand:"))
async def process_auc_brand(call: CallbackQuery, state: FSMContext):
    brand = call.data.split(":")[1]
    await state.update_data(brand=brand)
    if brand == "Boshqa brend":
        await state.set_state(AuctionCreateStates.custom_model)
        await call.message.edit_text("✍️ Telefoningizning to'liq <b>Brend va Modelini</b> yozib yuboring:")
    else:
        await state.set_state(AuctionCreateStates.model)
        await call.message.edit_text(
            f"📱 <b>{brand}</b> tanlandi.\n\n<b>2-qadam: Modelini tanlang:</b>",
            reply_markup=get_models_inline_kb(brand=brand, page=0)
        )
    await call.answer()

@router.callback_query(AuctionCreateStates.model, F.data.startswith("set_model_page:"))
async def process_auc_model_page(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    brand, page = parts[1], int(parts[2])
    await call.message.edit_text(
        f"📱 <b>{brand}</b> modellari:\n\n<b>2-qadam: Modelini tanlang:</b>",
        reply_markup=get_models_inline_kb(brand=brand, page=page)
    )
    await call.answer()

@router.callback_query(AuctionCreateStates.model, F.data.startswith("set_model:"))
async def process_auc_model(call: CallbackQuery, state: FSMContext):
    model = call.data.split(":")[1]
    if model == "custom":
        await state.set_state(AuctionCreateStates.custom_model)
        await call.message.edit_text("✍️ Telefon modelining aniq nomini yozib yuboring:")
    else:
        await state.update_data(model=model)
        await state.set_state(AuctionCreateStates.condition)
        await call.message.edit_text(
            f"Tanlandi: <b>{model}</b>\n\n<b>3-qadam: Holatini tanlang:</b>",
            reply_markup=get_condition_inline_kb()
        )
    await call.answer()

@router.message(AuctionCreateStates.custom_model)
async def process_auc_custom_model(message: Message, state: FSMContext):
    data = await state.get_data()
    brand = data.get("brand", "")
    if brand == "Boshqa brend":
        await state.update_data(brand="Boshqa", model=message.text.strip())
    else:
        await state.update_data(model=message.text.strip())

    await state.set_state(AuctionCreateStates.condition)
    await message.answer(
        f"Model: <b>{message.text.strip()}</b>\n\n<b>3-qadam: Holatini tanlang:</b>",
        reply_markup=get_condition_inline_kb()
    )

@router.callback_query(AuctionCreateStates.condition, F.data.startswith("set_cond:"))
async def process_auc_condition(call: CallbackQuery, state: FSMContext):
    cond = call.data.split(":")[1]
    await state.update_data(condition=cond)
    await state.set_state(AuctionCreateStates.memory)
    await call.message.edit_text(
        "💾 <b>4-qadam: Xotira hajmini tanlang:</b>",
        reply_markup=get_memory_inline_kb()
    )
    await call.answer()

@router.callback_query(AuctionCreateStates.memory, F.data.startswith("set_mem:"))
async def process_auc_memory(call: CallbackQuery, state: FSMContext):
    mem = call.data.split(":")[1]
    await state.update_data(memory=mem)
    await state.set_state(AuctionCreateStates.battery)
    await call.message.delete()
    await call.message.answer(
        "🔋 <b>5-qadam: Batareya holati (Yomkost)?</b>\n\nMasalan: <i>85%</i> yoki <i>100%</i> (agar bilmasangiz o'tkazib yuboring):",
        reply_markup=get_skip_or_cancel_kb()
    )
    await call.answer()

@router.message(AuctionCreateStates.battery)
async def process_auc_battery(message: Message, state: FSMContext):
    bat = "—" if message.text == "⏩ O'tkazib yuborish" else message.text.strip()
    await state.update_data(battery=bat)
    await state.set_state(AuctionCreateStates.color)
    await message.answer(
        "🎨 <b>6-qadam: Rangi qanday?</b> (Masalan: <i>Qora</i>, <i>Oq</i>, <i>Titanium</i>):",
        reply_markup=get_skip_or_cancel_kb()
    )

@router.message(AuctionCreateStates.color)
async def process_auc_color(message: Message, state: FSMContext):
    col = "—" if message.text == "⏩ O'tkazib yuborish" else message.text.strip()
    await state.update_data(color=col)
    await state.set_state(AuctionCreateStates.region)
    await message.answer(
        "📍 <b>7-qadam: Qaysi viloyat / shahardasiz?</b>",
        reply_markup=get_regions_inline_kb()
    )

@router.callback_query(AuctionCreateStates.region, F.data.startswith("set_reg:"))
async def process_auc_region(call: CallbackQuery, state: FSMContext):
    reg = call.data.split(":")[1]
    await state.update_data(region=reg)
    await state.set_state(AuctionCreateStates.photo)
    await call.message.delete()
    await call.message.answer(
        "📷 <b>8-qadam: Telefonning sifatli RASMINI yuboring:</b>\n\n(Faqat 1 dona rasm qabul qilinadi):",
        reply_markup=get_cancel_kb()
    )
    await call.answer()

@router.message(AuctionCreateStates.photo, F.photo)
async def process_auc_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(AuctionCreateStates.description)
    await message.answer(
        "📝 <b>9-qadam: Qo'shimcha tavsif yozing:</b>\n\n(Karobka-dokument bormi, usta ko'rganmi, aybi yo'qmi va h.k.):",
        reply_markup=get_skip_or_cancel_kb()
    )

@router.message(AuctionCreateStates.description)
async def process_auc_description(message: Message, state: FSMContext):
    desc = "Mavjud emas" if message.text == "⏩ O'tkazib yuborish" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AuctionCreateStates.start_price)
    await message.answer(
        "💵 <b>10-qadam: Boshlang'ich narxni kiriting (so'mda):</b>\n\n"
        "Auksion mana shu narxdan boshlanadi.\n"
        "Masalan: <code>1500000</code>",
        reply_markup=get_cancel_kb()
    )

@router.message(AuctionCreateStates.start_price)
async def process_auc_start_price(message: Message, state: FSMContext):
    raw = message.text.replace(" ", "").replace(",", "").replace(".", "")
    if not raw.isdigit():
        await message.answer("⚠️ Iltimos, narxni faqat raqamlarda kiriting:")
        return

    price = int(raw)
    if price < 10000:
        await message.answer("⚠️ Boshlang'ich narx kamida 10 000 so'm bo'lishi kerak:")
        return

    await state.update_data(start_price=price)
    await state.set_state(AuctionCreateStates.min_step)
    await message.answer(
        "📈 <b>11-qadam: Minimal stavka qadamini tanlang:</b>\n\n"
        "Har bir yangi taklif kamida qancha miqdorga oshirilishi kerak?",
        reply_markup=get_auction_min_steps_kb()
    )

@router.callback_query(AuctionCreateStates.min_step, F.data.startswith("auc_step:"))
async def process_auc_min_step(call: CallbackQuery, state: FSMContext):
    step_val = call.data.split(":")[1]
    if step_val == "custom":
        await call.message.edit_text("✍️ O'zingiz xohlagan minimal qadamni raqamda yozing (Masalan: 30000):")
    else:
        await state.update_data(min_step=int(step_val))
        await state.set_state(AuctionCreateStates.duration)
        await call.message.edit_text(
            "⏱ <b>12-qadam: Auksion davomiyligini tanlang:</b>\n\n"
            "Belgilangan vaqt tugagach auksion avtomatik to'xtaydi va eng yuqori narx taklif qilgan odam g'olib bo'ladi!",
            reply_markup=get_auction_duration_kb()
        )
    await call.answer()

@router.message(AuctionCreateStates.min_step)
async def process_auc_min_step_text(message: Message, state: FSMContext):
    raw = message.text.replace(" ", "")
    if not raw.isdigit():
        await message.answer("⚠️ Raqamda kiriting:")
        return
    await state.update_data(min_step=int(raw))
    await state.set_state(AuctionCreateStates.duration)
    await message.answer(
        "⏱ <b>12-qadam: Auksion davomiyligini tanlang:</b>",
        reply_markup=get_auction_duration_kb()
    )

@router.callback_query(AuctionCreateStates.duration, F.data.startswith("auc_dur:"))
async def process_auc_duration(call: CallbackQuery, state: FSMContext):
    hours = int(call.data.split(":")[1])
    end_time = datetime.now() + timedelta(hours=hours)
    await state.update_data(end_time=end_time, duration_hours=hours)

    data = await state.get_data()
    caption = format_auction_caption(data, is_preview=True)
    await state.set_state(AuctionCreateStates.confirm)
    await call.message.delete()
    await call.message.answer_photo(
        photo=data["photo_id"],
        caption=f"📋 <b>Auksion ma'lumotlarini tekshiring:</b>\n\n" + caption,
        reply_markup=get_confirm_auction_kb()
    )
    await call.answer()

@router.callback_query(AuctionCreateStates.confirm, F.data == "confirm_auction_start")
async def confirm_auction_start(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    auc_id = await db.create_auction(data)
    await state.clear()
    await call.message.delete()
    await call.message.answer(
        f"🎉 <b>Auksion muvaffaqiyatli boshlandi!</b>\n\n"
        f"Auksion ID: <b>#{auc_id}</b>\n"
        f"Davomiyligi: <b>{data.get('duration_hours', 24)} soat</b>\n\n"
        f"Barcha foydalanuvchilar endi '🔨 Kimoshdi (Auksion)' bo'limida sizning telefoningizni ko'rib, stavka qo'yishlari mumkin!",
        reply_markup=get_main_menu(is_admin=False)
    )
    await call.answer()