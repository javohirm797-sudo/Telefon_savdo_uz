from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database import db
from keyboards import get_my_ad_actions_kb, get_vip_plans_kb
from utils import format_ad_caption

router = Router()

@router.message(F.text == "📋 Mening e'lonlarim")
@router.message(Command("my_ads"))
async def show_my_ads(message: Message):
    user_id = message.from_user.id
    ads = await db.get_user_ads(user_id)
    
    if not ads:
        await message.answer(
            "📋 <b>Sizda hali joylangan e'lonlar mavjud emas.</b>\n\n"
            "Telefoningizni sotish uchun <b>«➕ E'lon joylash»</b> tugmasini bosing!"
        )
        return

    await message.answer(f"📋 <b>Sizning e'lonlaringiz soni: {len(ads)} ta</b>\nQuyida ularni boshqarishingiz mumkin:")

    for ad in ads:
        status_text = ""
        if ad["status"] == "sold":
            status_text = "🟢 <b>[SOTILDI]</b>\n"
            
        caption = f"{status_text}" + format_ad_caption(ad, is_preview=False)
        kb = get_my_ad_actions_kb(ad_id=ad["id"], is_vip=bool(ad.get("is_vip")))
        
        await message.answer_photo(
            photo=ad["photo_id"],
            caption=caption,
            reply_markup=kb
        )

@router.callback_query(F.data.startswith("mark_sold:"))
async def process_mark_sold(call: CallbackQuery):
    ad_id = int(call.data.split(":")[1])
    await db.update_ad_status(ad_id=ad_id, status="sold")
    await call.answer("✅ E'loningiz 'Sotildi' deb belgilandi!", show_alert=True)
    await call.message.edit_reply_markup(reply_markup=None)

@router.callback_query(F.data.startswith("delete_ad:"))
async def process_delete_ad(call: CallbackQuery):
    ad_id = int(call.data.split(":")[1])
    await db.update_ad_status(ad_id=ad_id, status="deleted")
    await call.message.delete()
    await call.answer("🗑 E'lon muvaffaqiyatli o'chirildi!", show_alert=True)

@router.callback_query(F.data.startswith("make_vip:"))
async def process_make_vip(call: CallbackQuery):
    ad_id = int(call.data.split(":")[1])
    await call.message.reply(
        f"⭐️ <b>#{ad_id} raqamli e'loningiz uchun VIP tarifni tanlang:</b>",
        reply_markup=get_vip_plans_kb(ad_id=ad_id)
    )
    await call.answer()
