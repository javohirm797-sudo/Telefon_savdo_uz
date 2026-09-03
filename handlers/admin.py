import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import db
from states import AdminStates
from keyboards import get_admin_panel_kb, get_main_menu, get_cancel_kb, get_admin_verify_payment_kb
import config

router = Router()

# Parol orqali avtorizatsiya qilingan adminlar
authenticated_admins = set(config.ADMIN_IDS)

def is_admin(user_id: int) -> bool:
    return user_id in authenticated_admins or user_id in config.ADMIN_IDS

@router.message(Command("adminjav"))
async def prompt_admin_password(message: Message, state: FSMContext):
    """Maxfiy admin komandasi - parolni so'raydi"""
    await state.set_state(AdminStates.admin_password)
    await message.answer(
        "🔒 <b>MAXFIY ADMIN TIZIMI</b>\n\n"
        "Iltimos, Maxfiy Admin Panelga kirish uchun parolni kiriting:",
        reply_markup=get_cancel_kb()
    )

@router.message(AdminStates.admin_password)
async def verify_admin_password(message: Message, state: FSMContext):
    entered_password = message.text.strip() if message.text else ""
    
    if entered_password == config.ADMIN_PASSWORD:
        authenticated_admins.add(message.from_user.id)
        if message.from_user.id not in config.ADMIN_IDS:
            config.ADMIN_IDS.append(message.from_user.id)

        await state.clear()
        
        stats = await db.get_stats()
        text = (
            f"🔓 <b>XUSH KELIBSIZ, ADMIN! (Parol to'g'ri)</b>\n\n"
            f"📊 <b>Bot Statistikasi:</b>\n"
            f"👥 Jami foydalanuvchilar: <b>{stats['total_users']} ta</b>\n"
            f"📱 Jami e'lonlar: <b>{stats['total_ads']} ta</b>\n"
            f"🟢 Faol e'lonlar: <b>{stats['active_ads']} ta</b>\n"
            f"👑 VIP e'lonlar: <b>{stats['vip_ads']} ta</b>\n"
            f"🤝 Sotilgan telefonlar: <b>{stats['sold_ads']} ta</b>\n\n"
            f"⏳ Kutilayotgan VIP to'lovlar: <b>{stats['pending_payments']} ta</b>\n"
            f"💰 Jami tasdiqlangan tushum: <b>{stats['total_earned']:,} so'm</b>\n\n"
            f"🗄 Ma'lumotlar bazasi: <b>{stats['db_type']}</b>"
        )
        await message.answer(text, reply_markup=get_admin_panel_kb(stats['pending_payments']))
    else:
        await state.clear()
        await message.answer(
            "⛔️ <b>Xato: Maxfiy parol noto'g'ri kiritildi!</b>\n\n"
            "Bosh menyudasiz.",
            reply_markup=get_main_menu()
        )

@router.callback_query(F.data == "adm_stats")
@router.callback_query(F.data == "adm_refresh")
async def process_admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan.", show_alert=True)
        return

    stats = await db.get_stats()
    text = (
        f"🔐 <b>MAXFIY ADMIN BOSHQARUV PANELI (YANGILANDI)</b>\n\n"
        f"📊 <b>Bot Statistikasi:</b>\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']} ta</b>\n"
        f"📱 Jami e'lonlar: <b>{stats['total_ads']} ta</b>\n"
        f"🟢 Faol e'lonlar: <b>{stats['active_ads']} ta</b>\n"
        f"👑 VIP e'lonlar: <b>{stats['vip_ads']} ta</b>\n"
        f"🤝 Sotilgan telefonlar: <b>{stats['sold_ads']} ta</b>\n\n"
        f"⏳ Kutilayotgan VIP to'lovlar: <b>{stats['pending_payments']} ta</b>\n"
        f"💰 Jami tasdiqlangan tushum: <b>{stats['total_earned']:,} so'm</b>\n\n"
        f"🗄 Ma'lumotlar bazasi turi: <b>{stats['db_type']}</b>"
    )
    try:
        await call.message.edit_text(text, reply_markup=get_admin_panel_kb(stats['pending_payments']))
    except Exception:
        pass
    await call.answer("Statistika yangilandi")

@router.callback_query(F.data == "adm_pending_vip")
async def process_admin_pending_vip(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan.", show_alert=True)
        return

    pending_list = await db.get_pending_vip_payments()
    if not pending_list:
        await call.answer("⭐️ Hozirda kutilayotgan yangi VIP to'lovlar yo'q.", show_alert=True)
        return

    await call.answer(f"{len(pending_list)} ta VIP so'rov topildi")
    await call.message.answer(f"⭐️ <b>KUTILAYOTGAN VIP TO'LOVLAR RO'YXATI ({len(pending_list)} TA):</b>")

    for p in pending_list:
        payment_id = p["id"]
        ad_id = p["ad_id"]
        plan_days = p["plan_days"]
        amount = p["amount"]
        user_id = p["user_id"]
        brand = p.get("brand") or "Telefon"
        model = p.get("model") or ""
        price = p.get("price") or ""
        receipt_photo_id = p.get("receipt_photo_id")

        caption = (
            f"⭐️ <b>VIP TO'LOV SO'ROVI #{payment_id}</b>\n\n"
            f"📱 E'lon: <b>{brand} {model}</b> (ID: #{ad_id})\n"
            f"💰 Narxi: {price}\n"
            f"👤 Mijoz ID: <code>{user_id}</code>\n"
            f"📅 VIP muddati: <b>{plan_days} kun</b>\n"
            f"💵 To'lov summasi: <b>{amount:,} so'm</b>\n\n"
            f"To'lov chekini tekshirib, tasdiqlang:"
        )

        kb = get_admin_verify_payment_kb(payment_id, ad_id, plan_days)
        try:
            if receipt_photo_id and receipt_photo_id not in ("default", "receipt", "test_photo_id"):
                await bot.send_photo(
                    chat_id=call.from_user.id,
                    photo=receipt_photo_id,
                    caption=caption,
                    reply_markup=kb
                )
            else:
                await bot.send_message(
                    chat_id=call.from_user.id,
                    text=caption,
                    reply_markup=kb
                )
        except Exception:
            await bot.send_message(
                chat_id=call.from_user.id,
                text=caption,
                reply_markup=kb
            )

# ==================== VIP TO'LOVNI TASDIQLASH / RAD ETISH ====================

@router.callback_query(F.data.startswith("adm_appr:"))
async def process_approve_payment(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan.", show_alert=True)
        return

    parts = call.data.split(":")
    payment_id = int(parts[1])
    ad_id = int(parts[2])
    plan_days = int(parts[3])

    payment = await db.get_vip_payment(payment_id)
    if not payment or payment["status"] != "pending":
        await call.answer("Bu to'lov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    # Statuslarni yangilash
    await db.update_vip_payment_status(payment_id, "approved")
    await db.set_ad_vip(ad_id, plan_days)

    # Admin xabarini yangilash
    current_caption = call.message.caption or ""
    new_caption = current_caption + f"\n\n✅ <b>TASDIQLANDI ({call.from_user.full_name} tomonidan)! E'lon {plan_days} kunga VIP qilindi.</b>"
    try:
        await call.message.edit_caption(caption=new_caption, reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchiga xabar berish
    user_id = payment["user_id"]
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"🎉 <b>XUSHXABAR!</b>\n\n"
                 f"Sizning <b>#{ad_id}</b> raqamli e'loningiz uchun <b>{plan_days} kunlik VIP xizmati</b> faollashtirildi!\n"
                 f"Endi sizning e'loningiz ro'yxatning eng yuqori qismida chiqadi."
        )
    except Exception:
        pass

    await call.answer("To'lov tasdiqlandi va VIP yoqildi!", show_alert=True)

@router.callback_query(F.data.startswith("adm_rejc:"))
async def process_reject_payment(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan.", show_alert=True)
        return

    parts = call.data.split(":")
    payment_id = int(parts[1])
    ad_id = int(parts[2])

    payment = await db.get_vip_payment(payment_id)
    if not payment or payment["status"] != "pending":
        await call.answer("Bu to'lov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await db.update_vip_payment_status(payment_id, "rejected")

    # Admin xabarini yangilash
    current_caption = call.message.caption or ""
    new_caption = current_caption + f"\n\n❌ <b>RAD ETILDI ({call.from_user.full_name} tomonidan)!</b>"
    try:
        await call.message.edit_caption(caption=new_caption, reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchiga xabar berish
    user_id = payment["user_id"]
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"⚠️ <b>Diqqat:</b>\n\n"
                 f"Sizning <b>#{ad_id}</b> raqamli e'loningiz uchun yuborilgan to'lov cheki admin tomonidan qabul qilinmadi.\n"
                 f"Savollaringiz bo'lsa {config.OWNER_TELEGRAM} bilan bog'laning."
        )
    except Exception:
        pass

    await call.answer("To'lov rad etildi!", show_alert=True)

# ==================== BROADCAST (XABAR TARQATISH) ====================

@router.callback_query(F.data == "adm_broadcast")
async def start_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan.", show_alert=True)
        return

    await state.set_state(AdminStates.broadcast)
    await call.message.delete()
    await call.message.answer(
        "📢 <b>Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing:</b>\n\n"
        "(Matn, rasm yoki reklama xabari yuborishingiz mumkin)",
        reply_markup=get_cancel_kb()
    )
    await call.answer()

@router.message(AdminStates.broadcast)
async def process_broadcast_message(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    await state.clear()
    user_ids = await db.get_all_user_ids()
    
    status_msg = await message.answer(f"⏳ Xabar tarqatish boshlandi... Jami foydalanuvchilar: {len(user_ids)} ta")
    
    success_count = 0
    fail_count = 0

    for uid in user_ids:
        try:
            await message.copy_to(chat_id=uid)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail_count += 1

    await status_msg.edit_text(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"📤 Yuborildi: <b>{success_count} ta</b>\n"
        f"🚫 Yetib bormadi (bloklagan): <b>{fail_count} ta</b>"
    )
    await message.answer("Bosh menyudasiz:", reply_markup=get_main_menu())

# ==================== E'LONNI O'CHIRISH (ADMIN) ====================

@router.callback_query(F.data.startswith("adm_del_ad:"))
async def process_admin_delete_ad_inline(call: CallbackQuery):
    """Bozor ro'yxatida ko'rib turgan e'lonni admin tomonidan o'chirish"""
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan.", show_alert=True)
        return

    ad_id = int(call.data.split(":")[1])
    deleted = await db.admin_delete_ad(ad_id)
    if deleted:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(f"🗑 <b>E'lon #{ad_id} muvaffaqiyatli o'chirildi!</b>")
        await call.answer("E'lon o'chirildi!", show_alert=True)
    else:
        await call.answer("E'lon topilmadi yoki allaqachon o'chirilgan.", show_alert=True)

@router.callback_query(F.data == "adm_del_by_id")
async def start_admin_delete_by_id(call: CallbackQuery, state: FSMContext):
    """Admin panelidan ID orqali e'lon o'chirishni boshlash"""
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat berilmagan.", show_alert=True)
        return

    await state.set_state(AdminStates.delete_ad)
    await call.message.answer(
        "🗑 <b>E'LONNI O'CHIRISH (ADMIN):</b>\n\n"
        "O'chirmoqchi bo'lgan e'loningizning <b>ID raqamini</b> yozing (Masalan: <code>15</code>):",
        reply_markup=get_cancel_kb()
    )
    await call.answer()

@router.message(AdminStates.delete_ad)
async def process_admin_delete_by_id_input(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip().replace("#", "")
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqatgina raqam kiriting (Masalan: 12):")
        return

    ad_id = int(text)
    ad = await db.get_ad_by_id(ad_id)
    if not ad:
        await message.answer(f"❌ <b>#{ad_id}</b> raqamli e'lon bazadan topilmadi!")
        return

    deleted = await db.admin_delete_ad(ad_id)
    await state.clear()
    if deleted:
        await message.answer(
            f"✅ <b>E'LON O'CHIRILDI!</b>\n\n"
            f"📱 E'lon: <b>{ad.get('brand')} {ad.get('model')}</b> (#{ad_id})\n"
            f"💰 Narxi: {ad.get('price')}\n"
            f"👤 Egasi ID: {ad.get('user_id')}\n\n"
            f"Ushbu e'lon bozor ro'yxatidan va Web App'dan butunlay olib tashlandi.",
            reply_markup=get_admin_panel_kb()
        )
    else:
        await message.answer("❌ E'lonni o'chirishda xatolik yuz berdi.", reply_markup=get_admin_panel_kb())
