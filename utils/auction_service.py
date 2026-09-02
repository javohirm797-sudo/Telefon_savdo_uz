import html
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from aiogram import Bot
from database import db

logger = logging.getLogger(__name__)

def get_time_left_str(end_time) -> str:
    """Qolgan vaqtni chiroyli ko'rsatish"""
    if isinstance(end_time, str):
        try:
            end_dt = datetime.strptime(end_time.split(".")[0], "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                end_dt = datetime.fromisoformat(end_time)
            except Exception:
                return "Aniqlanmadi"
    else:
        end_dt = end_time

    now = datetime.now()
    diff = end_dt - now

    if diff.total_seconds() <= 0:
        return "🛑 Muddat tugagan"

    total_seconds = int(diff.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    parts = []
    if days > 0:
        parts.append(f"{days} kun")
    if hours > 0:
        parts.append(f"{hours} soat")
    if minutes > 0 or not parts:
        parts.append(f"{minutes} daqiqa")

    return " ".join(parts)

def format_auction_caption(auction: Dict[str, Any], is_preview: bool = False) -> str:
    """Auksion matnini formatlash"""
    brand = html.escape(str(auction.get("brand", "")))
    model = html.escape(str(auction.get("model", "")))
    condition = html.escape(str(auction.get("condition", "")))
    memory = html.escape(str(auction.get("memory", "")))
    battery = html.escape(str(auction.get("battery", "—")))
    color = html.escape(str(auction.get("color", "—")))
    region = html.escape(str(auction.get("region", "")))
    description = html.escape(str(auction.get("description", "Mavjud emas")))
    
    start_price = auction.get("start_price", 0)
    current_price = auction.get("current_price", start_price)
    min_step = auction.get("min_step", 50000)
    winner_name = auction.get("current_winner_name")
    winner_str = html.escape(winner_name) if winner_name else "<i>Hali stavka qo'yilmagan</i>"
    
    end_time = auction.get("end_time")
    time_left = get_time_left_str(end_time) if end_time else "24 soat"
    
    phone = html.escape(str(auction.get("contact_phone", "")))
    username = auction.get("contact_username", "")
    username_str = f"@{username}" if username and not username.startswith("@") else (username or "Mavjud emas")

    auc_id_str = f"\n🆔 <b>Auksion ID:</b> #{auction.get('id', 'NEW')}" if not is_preview else ""

    caption = (
        f"🔨 <b>KIMOSHDI SAVDOSI (AUKSION)</b> 🔨\n\n"
        f"📱 <b>Telefon:</b> {brand} {model}\n"
        f"💾 <b>Xotirasi:</b> {memory}\n"
        f"🔋 <b>Batareya (Yomkost):</b> {battery}\n"
        f"🛠 <b>Holati:</b> {condition}\n"
        f"🎨 <b>Rangi:</b> {color}\n"
        f"📍 <b>Hudud:</b> {region}\n\n"
        f"💵 <b>Boshlang'ich narx:</b> {start_price:,} so'm\n"
        f"🔥 <b>Hozirgi eng yuqori taklif:</b> <b>{current_price:,} so'm</b>\n"
        f"👤 <b>Yetakchi xaridor:</b> {winner_str}\n"
        f"📈 <b>Minimal qadam:</b> +{min_step:,} so'm\n"
        f"⏳ <b>Qolgan vaqt:</b> <b>{time_left}</b>\n\n"
        f"📝 <b>Qo'shimcha ma'lumot:</b>\n{description}\n\n"
        f"📞 <b>Sotuvchi:</b> <code>{phone}</code> | {username_str}"
        f"{auc_id_str}\n"
        f"━━━━━━━━━━━━━━\n"
        f"💡 <i>Eng yuqori narx taklif qilgan ishtirokchi telefonni sotib oladi!</i>"
    )
    return caption

async def auction_background_checker(bot: Bot):
    """Muddati o'tgan auksionlarni avtomatik aniqlash va xabar yuborish"""
    while True:
        try:
            await asyncio.sleep(30)  # Har 30 soniyada tekshiradi
            expired_auctions = await db.get_expired_active_auctions()
            for auc in expired_auctions:
                auc_id = auc["id"]
                updated = await db.finish_auction(auc_id)
                seller_id = auc["user_id"]
                winner_id = auc.get("current_winner_id")
                winner_name = auc.get("current_winner_name", "Xaridor")
                item_name = f"{auc.get('brand', '')} {auc.get('model', '')}"
                final_price = auc.get("current_price", auc.get("start_price", 0))

                if winner_id:
                    # G'olibga xabar
                    try:
                        seller_phone = auc.get("contact_phone", "Mavjud emas")
                        seller_user = auc.get("contact_username", "")
                        tg_link = f"@{seller_user}" if seller_user else "Mavjud emas"
                        await bot.send_message(
                            chat_id=winner_id,
                            text=(
                                f"🎉 <b>TABRIKLAYMIZ! SIZ G'OLIB BO'LDINGIZ!</b> 🎉\n\n"
                                f"Siz <b>{item_name}</b> auksionida eng yuqori <b>{final_price:,} so'm</b> "
                                f"stavka bilan g'olib chiqdingiz!\n\n"
                                f"📞 <b>Sotuvchi bilan bog'lanish:</b>\n"
                                f"Telefon: <code>{seller_phone}</code>\n"
                                f"Telegram: {tg_link}\n\n"
                                f"Iltimos, tez orada sotuvchi bilan bog'lanib, telefonni qabul qilib oling!"
                            )
                        )
                    except Exception as e:
                        logger.warning(f"G'olibga xabar yuborishda xatolik: {e}")

                    # Sotuvchiga xabar
                    try:
                        await bot.send_message(
                            chat_id=seller_id,
                            text=(
                                f"🎉 <b>AUKSIONINGIZ MUVAFFAQIYATLI YAKUNLANDI!</b> 🎉\n\n"
                                f"Sizning <b>{item_name}</b> telefoningiz kimoshdi savdosi yakunlandi!\n"
                                f"🏆 <b>G'olib:</b> {winner_name} (ID: <code>{winner_id}</code>)\n"
                                f"💰 <b>Yakuniy narx:</b> <b>{final_price:,} so'm</b>\n\n"
                                f"Xaridorga ham sizning ma'lumotlaringiz yuborildi. Tez orada siz bilan bog'lanadi!"
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Sotuvchiga xabar yuborishda xatolik: {e}")
                else:
                    # Stavka bo'lmagan
                    try:
                        await bot.send_message(
                            chat_id=seller_id,
                            text=(
                                f"⏱ <b>Auksion muddati tugadi.</b>\n\n"
                                f"Sizning <b>{item_name}</b> telefoningiz auksioniga hech kim narx taklif qilmadi.\n"
                                f"Xohlasangiz, narxini pasaytirib qaytadan auksionga yoki oddiy bozorga qo'yishingiz mumkin."
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Sotuvchiga auksion tugash xabarini yuborishda xatolik: {e}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Auksion tekshiruvchisida xatolik: {e}", exc_info=True)
            await asyncio.sleep(10)