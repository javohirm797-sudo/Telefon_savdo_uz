import os
import json
import logging
import aiohttp
from aiohttp import web
from database import db
import config

logger = logging.getLogger(__name__)

# Rasmlar keshi (hot cache)
photo_url_cache = {}
photo_bytes_cache = {}
_shared_session = None

async def get_shared_session():
    global _shared_session
    if _shared_session is None or _shared_session.closed:
        _shared_session = aiohttp.ClientSession()
    return _shared_session

async def serve_index(request):
    """Asosiy Web App sahifasini ochish"""
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    return web.FileResponse(index_path)

async def api_get_ads(request):
    """Faol e'lonlarni JSON formatida olish"""
    brand = request.query.get("brand")
    model = request.query.get("model")
    region = request.query.get("region")
    limit = int(request.query.get("limit", 100))
    offset = int(request.query.get("offset", 0))

    ads = await db.get_active_ads(brand=brand, model=model, region=region, limit=limit, offset=offset)
    
    clean_ads = []
    for ad in ads:
        item = dict(ad)
        if "created_at" in item and item["created_at"]:
            item["created_at"] = str(item["created_at"])
        if "vip_until" in item and item["vip_until"]:
            item["vip_until"] = str(item["vip_until"])
        clean_ads.append(item)

    return web.json_response(clean_ads)

async def api_get_auctions(request):
    """Faol auksionlarni JSON formatida olish"""
    auctions = await db.get_active_auctions(limit=50)
    clean_auc = []
    for auc in auctions:
        item = dict(auc)
        if "end_time" in item and item["end_time"]:
            item["end_time"] = str(item["end_time"])
        if "created_at" in item and item["created_at"]:
            item["created_at"] = str(item["created_at"])
        clean_auc.append(item)
    return web.json_response(clean_auc)

async def api_get_photo(request):
    """Telegram photo_id bo'yicha e'lonning asl rasmini yuklab beruvchi tezyurar proxy"""
    photo_id = request.match_info.get("photo_id")

    if not photo_id or photo_id in ("default", "test_photo_id"):
        return web.Response(status=404, text="Photo not found")

    # 1. Tezkor RAM keshi
    if photo_id in photo_bytes_cache:
        return web.Response(
            body=photo_bytes_cache[photo_id],
            content_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=604800"}
        )

    try:
        session = await get_shared_session()

        # 2. Telegram REST API orqali file_path olish
        if photo_id in photo_url_cache:
            file_url = photo_url_cache[photo_id]
        else:
            api_url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/getFile?file_id={photo_id}"
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return web.Response(status=404)
                data = await resp.json()
                if not data.get("ok"):
                    return web.Response(status=404)
                file_path = data["result"]["file_path"]
                file_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file_path}"
                photo_url_cache[photo_id] = file_url

        # 3. Asl telefon rasmini yuklab foydalanuvchiga yuborish
        async with session.get(file_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                content = await resp.read()
                photo_bytes_cache[photo_id] = content
                return web.Response(
                    body=content,
                    content_type="image/jpeg",
                    headers={"Cache-Control": "public, max-age=604800"}
                )
            return web.Response(status=404)
    except Exception as e:
        logger.warning(f"Rasm yuklashda xatolik ({photo_id}): {e}")
        return web.Response(status=404)

async def api_place_bid(request):
    """Web App orqali auksionga stavka berish"""
    try:
        data = await request.json()
        auction_id = int(data.get("auction_id"))
        user_id = int(data.get("user_id", 0))
        user_name = str(data.get("user_name", "Web Foydalanuvchi"))
        bid_amount = int(data.get("bid_amount", 0))

        if not user_id:
            return web.json_response({"success": False, "message": "Iltimos, Telegram orqali kiring!"})

        success, msg, prev_winner, auc = await db.place_bid(
            auction_id=auction_id,
            user_id=user_id,
            user_name=user_name,
            bid_amount=bid_amount
        )

        # Bildirishnomalar
        bot = request.app.get("bot")
        if bot and success:
            if prev_winner and prev_winner["user_id"] != user_id:
                try:
                    item_name = f"{auc.get('brand', '')} {auc.get('model', '')}"
                    await bot.send_message(
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

        return web.json_response({"success": success, "message": msg})
    except Exception as e:
        logger.error(f"api_place_bid xatosi: {e}")
        return web.json_response({"success": False, "message": str(e)})

async def upload_base64_to_telegram(bot, base64_str: str, caption: str = "") -> str:
    """Base64 rasmni dekod qilib Telegram bot orqali adminga yuborib, photo_id oladi"""
    if not base64_str or len(base64_str) < 100:
        return "default"
    
    try:
        import base64
        from aiogram.types import BufferedInputFile
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]
        img_bytes = base64.b64decode(base64_str)
        
        target_chat = config.ADMIN_IDS[0] if config.ADMIN_IDS else None
        if not target_chat or not bot:
            return "default"
            
        file_input = BufferedInputFile(img_bytes, filename="phone.jpg")
        sent_msg = await bot.send_photo(chat_id=target_chat, photo=file_input, caption=caption)
        if sent_msg and sent_msg.photo:
            return sent_msg.photo[-1].file_id
    except Exception as e:
        logger.error(f"Rasmni Telegramga yuklashda xatolik: {e}")
    return "default"

async def api_post_ad(request):
    """Web App orqali yangi e'lon joylash (rasm bilan)"""
    try:
        data = await request.json()
        user_id = int(data.get("user_id", 0))
        brand = str(data.get("brand", ""))
        model = str(data.get("model", ""))
        price = str(data.get("price", ""))
        phone = str(data.get("contact_phone", ""))
        photo_base64 = data.get("photo_base64", "")

        if not model or not price or not phone:
            return web.json_response({"success": False, "message": "Barcha majburiy maydonlarni to'ldiring!"})

        bot = request.app.get("bot")
        photo_id = "default"
        if photo_base64 and bot:
            photo_id = await upload_base64_to_telegram(
                bot, photo_base64, 
                caption=f"📱 Yangi Web App e'loni: {brand} {model} ({price})\n📞 Telefon: {phone}"
            )

        ad_data = {
            "user_id": user_id,
            "brand": brand,
            "model": model,
            "memory": data.get("memory", "128 GB"),
            "condition": data.get("condition", "Yaxshi"),
            "battery": data.get("battery", "—"),
            "color": data.get("color", "—"),
            "price": price,
            "region": data.get("region", "Toshkent shahri"),
            "photo_id": photo_id,
            "description": data.get("description", ""),
            "contact_phone": phone,
            "contact_username": data.get("contact_username", ""),
            "is_vip": False
        }

        ad_id = await db.add_ad(ad_data)
        return web.json_response({"success": True, "message": "E'lon muvaffaqiyatli joylandi!", "ad_id": ad_id})
    except Exception as e:
        logger.error(f"api_post_ad xatosi: {e}")
        return web.json_response({"success": False, "message": str(e)})

async def api_post_auction(request):
    """Web App orqali auksionga telefon qo'yish (to'lov cheki bilan)"""
    try:
        from keyboards import get_admin_verify_auction_kb
        from datetime import datetime, timedelta
        data = await request.json()
        user_id = int(data.get("user_id", 0))
        brand = str(data.get("brand", ""))
        model = str(data.get("model", "")).strip()
        phone = str(data.get("contact_phone", "")).strip()
        start_price = int(data.get("start_price", 0))
        min_step = int(data.get("min_step", 50000))
        duration_hours = int(data.get("duration_hours", 24))
        photo_base64 = data.get("photo_base64", "")
        receipt_base64 = data.get("receipt_base64", "")

        if not model or not phone or start_price < 10000:
            return web.json_response({"success": False, "message": "Barcha maydonlarni to'g'ri to'ldiring!"})

        if not receipt_base64:
            return web.json_response({"success": False, "message": "Iltimos, 5 000 so'm to'lov chekining rasmini yuklang!"})

        bot = request.app.get("bot")
        photo_id = "default"
        if photo_base64 and bot:
            photo_id = await upload_base64_to_telegram(
                bot, photo_base64,
                caption=f"🔨 Web App Auksion: {brand} {model}\n💵 Boshlang'ich: {start_price:,} so'm"
            )

        receipt_photo_id = "receipt"
        if receipt_base64 and bot:
            receipt_photo_id = await upload_base64_to_telegram(
                bot, receipt_base64,
                caption=f"🧾 Auksion to'lov cheki (Web App)\nTelefon: {brand} {model}\nSumma: 5 000 so'm"
            )

        now = datetime.now()
        end_time = now + timedelta(hours=duration_hours)

        auc_data = {
            "user_id": user_id,
            "brand": brand,
            "model": model,
            "memory": data.get("memory", "128 GB"),
            "condition": data.get("condition", "Yaxshi"),
            "battery": data.get("battery", "—"),
            "color": data.get("color", "—"),
            "region": data.get("region", "Toshkent shahri"),
            "photo_id": photo_id,
            "receipt_photo_id": receipt_photo_id,
            "description": data.get("description", ""),
            "contact_phone": phone,
            "contact_username": data.get("contact_username", ""),
            "start_price": start_price,
            "min_step": min_step,
            "duration_hours": duration_hours,
            "end_time": end_time,
            "status": "pending"
        }

        auc_id = await db.create_auction(auc_data)

        # Adminga Telegram orqali xabar va chekni yuborish
        if bot:
            admin_caption = (
                f"🔨 <b>YANGI AUKSION SO'ROVI VA TO'LOV CHEKI (Web App)!</b>\n\n"
                f"🆔 Auksion ID: <b>#{auc_id}</b>\n"
                f"📱 Telefon: <b>{brand} {model}</b>\n"
                f"💾 Xotira: <b>{auc_data['memory']}</b> | Holati: <b>{auc_data['condition']}</b>\n"
                f"💵 Boshlang'ich narx: <b>{start_price:,} so'm</b>\n"
                f"📈 Minimal qadam: <b>{min_step:,} so'm</b>\n"
                f"⏱ Davomiyligi: <b>{duration_hours} soat</b>\n"
                f"📞 Telefon: <code>{phone}</code>\n"
                f"👤 Foydalanuvchi ID: <code>{user_id}</code>\n"
                f"💰 Xizmat haqi: <b>5 000 so'm</b>\n\n"
                f"<i>Chekni tekshirib, auksionni tasdiqlang:</i>"
            )
            admin_kb = get_admin_verify_auction_kb(auc_id, duration_hours)
            for adm_id in config.ADMIN_IDS:
                try:
                    if receipt_photo_id and receipt_photo_id != "receipt":
                        await bot.send_photo(chat_id=adm_id, photo=receipt_photo_id, caption=admin_caption, reply_markup=admin_kb)
                    else:
                        await bot.send_message(chat_id=adm_id, text=admin_caption, reply_markup=admin_kb)
                except Exception as ex:
                    logger.error(f"Adminga Web App auksion chekini yuborishda xatolik: {ex}")

        return web.json_response({
            "success": True, 
            "message": "Auksion so'rovingiz qabul qilindi! Admin to'lovni tekshirib tasdiqlagach auksion boshlanadi.", 
            "auc_id": auc_id
        })
    except Exception as e:
        logger.error(f"api_post_auction xatosi: {e}")
        return web.json_response({"success": False, "message": str(e)})

async def api_delete_ad(request):
    """Web App profilidan shaxsiy e'lonni o'chirish"""
    try:
        data = await request.json()
        ad_id = int(data.get("ad_id", 0))
        user_id = int(data.get("user_id", 0))

        if not ad_id or not user_id:
            return web.json_response({"success": False, "message": "Ma'lumotlar yetarli emas!"})

        if user_id in config.ADMIN_IDS:
            deleted = await db.admin_delete_ad(ad_id=ad_id)
        else:
            deleted = await db.delete_user_ad(ad_id=ad_id, user_id=user_id)

        if deleted:
            return web.json_response({"success": True, "message": "E'lon muvaffaqiyatli o'chirildi!"})
        else:
            return web.json_response({"success": False, "message": "E'lon topilmadi yoki uni o'chirishga ruxsat yo'q!"})
    except Exception as e:
        logger.error(f"api_delete_ad xatosi: {e}")
        return web.json_response({"success": False, "message": str(e)})

async def api_buy_vip(request):
    """Web App orqali e'longa VIP paket sotib olish so'rovi"""
    try:
        from keyboards import get_admin_verify_payment_kb
        data = await request.json()
        ad_id = int(data.get("ad_id", 0))
        user_id = int(data.get("user_id", 0))
        plan_days = int(data.get("plan_days", 1))
        receipt_base64 = data.get("receipt_base64", "")

        prices = {1: config.VIP_PRICE_1_DAY, 2: config.VIP_PRICE_2_DAYS, 3: config.VIP_PRICE_3_DAYS}
        amount = prices.get(plan_days, config.VIP_PRICE_1_DAY)

        bot = request.app.get("bot")
        receipt_photo_id = "receipt"
        if receipt_base64 and bot:
            receipt_photo_id = await upload_base64_to_telegram(
                bot, receipt_base64, 
                caption=f"⭐️ VIP To'lov cheki (Web App)\n📱 E'lon ID: #{ad_id}\n📅 Reja: {plan_days} kun\n💰 Summa: {amount:,} so'm"
            )

        payment_id = await db.add_vip_payment(
            ad_id=ad_id,
            user_id=user_id,
            plan_days=plan_days,
            amount=amount,
            receipt_photo_id=receipt_photo_id
        )

        if bot and config.ADMIN_IDS:
            admin_caption = (
                f"⭐️ <b>YANGI VIP TO'LOV SO'ROVI (Web App)!</b>\n\n"
                f"🆔 To'lov ID: #{payment_id}\n"
                f"📱 E'lon ID: #{ad_id}\n"
                f"👤 Foydalanuvchi: {user_id}\n"
                f"📅 Reja: <b>{plan_days} kun</b>\n"
                f"💰 Summa: <b>{amount:,} so'm</b>\n\n"
                f"To'lov chekini tekshirib tasdiqlang:"
            )
            for admin_id in config.ADMIN_IDS:
                try:
                    if receipt_photo_id and receipt_photo_id != "receipt":
                        await bot.send_photo(
                            chat_id=admin_id,
                            photo=receipt_photo_id,
                            caption=admin_caption,
                            reply_markup=get_admin_verify_payment_kb(payment_id, ad_id, plan_days)
                        )
                    else:
                        await bot.send_message(
                            chat_id=admin_id,
                            text=admin_caption,
                            reply_markup=get_admin_verify_payment_kb(payment_id, ad_id, plan_days)
                        )
                except Exception as ex:
                    logger.warning(f"Adminga VIP xabar yuborishda xatolik: {ex}")

        return web.json_response({
            "success": True, 
            "message": "To'lov chekingiz adminga yuborildi! Tasdiqlangach, e'loningiz ro'yxatning eng yuqorisiga VIP bo'lib chiqadi!"
        })
    except Exception as e:
        logger.error(f"api_buy_vip xatosi: {e}")
        return web.json_response({"success": False, "message": str(e)})

async def api_get_my_ads(request):
    """Foydalanuvchining o'z e'lonlarini olish"""
    user_id = int(request.query.get("user_id", 0))
    if not user_id:
        return web.json_response([])

    user_ads = await db.get_user_ads(user_id)
    clean = []
    for ad in user_ads:
        item = dict(ad)
        if "created_at" in item and item["created_at"]:
            item["created_at"] = str(item["created_at"])
        if "vip_until" in item and item["vip_until"]:
            item["vip_until"] = str(item["vip_until"])
        clean.append(item)
    return web.json_response(clean)

@web.middleware
async def cors_middleware(request, handler):
    try:
        response = await handler(request)
    except web.HTTPException as ex:
        response = ex
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    if "X-Frame-Options" in response.headers:
        del response.headers["X-Frame-Options"]
    return response

def setup_webapp_routes(app: web.Application, bot):
    """Web App marshrutlarini ro'yxatdan o'tkazish"""
    app["bot"] = bot
    app.middlewares.append(cors_middleware)
    
    # Sahifa
    app.router.add_get("/", serve_index)
    app.router.add_get("/webapp", serve_index)
    
    # API
    app.router.add_get("/api/ads", api_get_ads)
    app.router.add_get("/api/auctions", api_get_auctions)
    app.router.add_get("/api/photo/{photo_id}", api_get_photo)
    app.router.add_post("/api/bid", api_place_bid)
    app.router.add_post("/api/post_ad", api_post_ad)
    app.router.add_post("/api/post_auction", api_post_auction)
    app.router.add_get("/api/my_ads", api_get_my_ads)
    app.router.add_post("/api/delete_ad", api_delete_ad)
    app.router.add_post("/api/buy_vip", api_buy_vip)

    # Static assets (css, js, images)
    static_dir = os.path.dirname(__file__)
    app.router.add_static("/static", path=static_dir, name="static")
