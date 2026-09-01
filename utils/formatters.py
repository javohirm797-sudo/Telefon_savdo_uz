import html
from typing import Dict, Any
import config

def format_ad_caption(ad: Dict[str, Any], is_preview: bool = False) -> str:
    """E'lon matnini chiroyli va qulay formatda yaratish"""
    is_vip = ad.get("is_vip", False)
    vip_badge = "👑 <b>⭐️ VIP E'LON ⭐️</b>\n" if is_vip else ""
    
    brand = html.escape(str(ad.get("brand", "")))
    model = html.escape(str(ad.get("model", "")))
    condition = html.escape(str(ad.get("condition", "")))
    memory = html.escape(str(ad.get("memory", "")))
    battery = html.escape(str(ad.get("battery", "—")))
    color = html.escape(str(ad.get("color", "—")))
    price = html.escape(str(ad.get("price", "")))
    region = html.escape(str(ad.get("region", "")))
    description = html.escape(str(ad.get("description", "Mavjud emas")))
    phone = html.escape(str(ad.get("contact_phone", "")))
    username = ad.get("contact_username", "")
    username_str = f"@{username}" if username and not username.startswith("@") else (username or "Mavjud emas")
    
    ad_id_str = f"\n🆔 <b>E'lon ID:</b> #{ad.get('id', 'NEW')}" if not is_preview else ""

    caption = (
        f"{vip_badge}"
        f"📱 <b>Telefon:</b> {brand} {model}\n"
        f"💾 <b>Xotirasi:</b> {memory}\n"
        f"🔋 <b>Batareya (Yomkost):</b> {battery}\n"
        f"🛠 <b>Holati:</b> {condition}\n"
        f"🎨 <b>Rangi:</b> {color}\n"
        f"📍 <b>Hudud:</b> {region}\n"
        f"💵 <b>Narxi:</b> <b>{price}</b>\n\n"
        f"📝 <b>Qo'shimcha ma'lumot:</b>\n{description}\n\n"
        f"📞 <b>Telefon:</b> <code>{phone}</code>\n"
        f"✈️ <b>Telegram:</b> {username_str}"
        f"{ad_id_str}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🤖 @TelefonBozorBoti orqali joylandi"
    )
    return caption

def format_owner_info() -> str:
    """Admin / Egasi aloqa ma'lumotlari"""
    return (
        f"👨‍💻 <b>ADMIN / BOZOR EGASI BILAN BOG'LANISH:</b>\n\n"
        f"✈️ <b>Telegram:</b> {config.OWNER_TELEGRAM}\n"
        f"📷 <b>Instagram:</b> {config.OWNER_INSTAGRAM}\n"
        f"📞 <b>Telefon raqam:</b> <code>{config.OWNER_PHONE}</code>\n\n"
        f"💳 <b>To'lov uchun karta:</b>\n"
        f"<code>{config.CARD_NUMBER}</code>\n"
        f"👤 <b>Karta egasi:</b> <b>{config.CARD_HOLDER}</b>\n\n"
        f"<i>Savollar, takliflar yoki reklama bo'yicha yuqoridagi manzillarga murojaat qilishingiz mumkin!</i>"
    )

def format_vip_info() -> str:
    """VIP e'lonlar haqida to'liq ma'lumot va narxlar"""
    return (
        f"👑 <b>⭐️ VIP E'LON XIZMATI ⭐️</b>\n\n"
        f"VIP e'lonning afzalliklari:\n"
        f"• E'loningiz ro'yxatda eng tepada va ajralib turuvchi 👑 VIP belgisi bilan chiqadi.\n"
        f"• Minglab xaridorlar birinchi bo'lib sizning e'loningizni ko'rishadi va tezroq sotiladi!\n\n"
        f"💰 <b>VIP Tariflar:</b>\n"
        f"1️⃣ <b>1 kunlik VIP</b> — {config.VIP_PRICE_1_DAY:,} so'm\n"
        f"2️⃣ <b>2 kunlik VIP</b> — {config.VIP_PRICE_2_DAYS:,} so'm\n"
        f"3️⃣ <b>3 kunlik VIP</b> — {config.VIP_PRICE_3_DAYS:,} so'm\n\n"
        f"💳 <b>To'lov uchun karta:</b>\n"
        f"<code>{config.CARD_NUMBER}</code>\n"
        f"👤 <b>Karta egasi:</b> <b>{config.CARD_HOLDER}</b>\n\n"
        f"<i>To'lovni amalga oshirgach, chekni (skrinshot) botga yuborasiz va admin tasdiqlashi bilan e'loningiz darhol VIP holatiga o'tadi!</i>"
    )
