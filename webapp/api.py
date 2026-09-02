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
    """Telegram photo_id bo'yicha rasmni olib beruvchi tezkor proxy (in-memory kesh bilan)"""
    photo_id = request.match_info.get("photo_id")
    bot = request.app.get("bot")

    if not photo_id or photo_id in ("default", "test_photo_id"):
        placeholder = os.path.join(os.path.dirname(__file__), "banner.jpg")
        if os.path.exists(placeholder):
            return web.FileResponse(placeholder, headers={"Cache-Control": "public, max-age=604800"})
        return web.Response(status=404, text="Photo not found")

    # 1. Tezkor xotira keshi (RAM) — 0 soniyada beradi!
    if photo_id in photo_bytes_cache:
        return web.Response(
            body=photo_bytes_cache[photo_id],
            content_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=604800, immutable"}
        )

    try:
        # 2. URL ni olish
        if photo_id in photo_url_cache:
            file_url = photo_url_cache[photo_id]
        else:
            file_info = await asyncio.wait_for(bot.get_file(photo_id), timeout=3.0)
            file_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file_info.file_path}"
            photo_url_cache[photo_id] = file_url

        # 3. Rasmni yuklash
        session = await get_shared_session()
        async with session.get(file_url, timeout=aiohttp.ClientTimeout(total=3.5)) as resp:
            if resp.status == 200:
                content = await resp.read()
                if len(photo_bytes_cache) < 200:
                    photo_bytes_cache[photo_id] = content
                return web.Response(
                    body=content,
                    content_type="image/jpeg",
                    headers={"Cache-Control": "public, max-age=604800, immutable"}
                )
    except Exception as e:
        logger.warning(f"Tezkor fallback rasm ({photo_id}): {e}")

    # Xato bo'lsa darhol placeholder rasm
    placeholder = os.path.join(os.path.dirname(__file__), "banner.jpg")
    if os.path.exists(placeholder):
        return web.FileResponse(placeholder, headers={"Cache-Control": "public, max-age=86400"})
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

async def api_post_ad(request):
    """Web App orqali yangi e'lon joylash"""
    try:
        data = await request.json()
        user_id = int(data.get("user_id", 0))
        brand = str(data.get("brand", ""))
        model = str(data.get("model", ""))
        price = str(data.get("price", ""))
        phone = str(data.get("contact_phone", ""))

        if not model or not price or not phone:
            return web.json_response({"success": False, "message": "Barcha majburiy maydonlarni to'ldiring!"})

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
            "photo_id": data.get("photo_id", "default"),
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
    app.router.add_get("/api/my_ads", api_get_my_ads)

    # Static assets (css, js, images)
    static_dir = os.path.dirname(__file__)
    app.router.add_static("/static", path=static_dir, name="static")
