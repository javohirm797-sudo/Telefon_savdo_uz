from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from database.phone_data import PHONE_BRANDS, PHONE_MODELS, PHONE_MEMORY_OPTIONS, PHONE_CONDITIONS, UZBEKISTAN_REGIONS
import config

def get_brands_inline_kb(for_filter: bool = False) -> InlineKeyboardMarkup:
    """Brendlar inline ro'yxati"""
    keyboard = []
    if for_filter:
        keyboard.append([InlineKeyboardButton(text="🌐 Barcha brendlar", callback_data="filter_brand:all")])
        
    row = []
    for brand in PHONE_BRANDS:
        cb_data = f"filter_brand:{brand}" if for_filter else f"set_brand:{brand}"
        row.append(InlineKeyboardButton(text=brand, callback_data=cb_data))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    cancel_cb = "close_view" if for_filter else "cancel_action"
    keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data=cancel_cb)])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_models_inline_kb(brand: str, for_filter: bool = False, page: int = 0) -> InlineKeyboardMarkup:
    """Tanlangan brend bo'yicha modellar ro'yxati (sahifalash bilan)"""
    models = PHONE_MODELS.get(brand, ["Boshqa model"])
    ITEMS_PER_PAGE = 8
    total_pages = (len(models) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_models = models[start_idx:end_idx]

    keyboard = []
    if for_filter and page == 0:
        keyboard.append([InlineKeyboardButton(text=f"🌐 Barcha {brand} modellari", callback_data="filter_model:all")])

    for model in current_models:
        cb_data = f"filter_model:{model}" if for_filter else f"set_model:{model}"
        keyboard.append([InlineKeyboardButton(text=model, callback_data=cb_data)])

    # Pagination buttons
    nav_row = []
    prefix = "filter_model_page" if for_filter else "set_model_page"
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"{prefix}:{brand}:{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"{prefix}:{brand}:{page+1}"))
    if nav_row:
        keyboard.append(nav_row)

    if not for_filter:
        keyboard.append([InlineKeyboardButton(text="✍️ O'zim yozib kiritaman", callback_data="set_model:custom")])
        keyboard.append([InlineKeyboardButton(text="🔙 Brendlarga qaytish", callback_data="back_to_brands")])
    else:
        keyboard.append([InlineKeyboardButton(text="🔙 Brendlarga qaytish", callback_data="back_to_filter_brands")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_memory_inline_kb() -> InlineKeyboardMarkup:
    """Xotira tanlash"""
    keyboard = []
    row = []
    for mem in PHONE_MEMORY_OPTIONS:
        row.append(InlineKeyboardButton(text=mem, callback_data=f"set_mem:{mem}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_condition_inline_kb() -> InlineKeyboardMarkup:
    """Holatini tanlash"""
    keyboard = []
    for cond in PHONE_CONDITIONS:
        keyboard.append([InlineKeyboardButton(text=cond, callback_data=f"set_cond:{cond}")])
    keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_regions_inline_kb(for_filter: bool = False) -> InlineKeyboardMarkup:
    """Viloyatlarni tanlash"""
    keyboard = []
    if for_filter:
        keyboard.append([InlineKeyboardButton(text="🌐 Barcha viloyatlar", callback_data="filter_reg:all")])

    row = []
    for reg in UZBEKISTAN_REGIONS:
        cb_data = f"filter_reg:{reg}" if for_filter else f"set_reg:{reg}"
        row.append(InlineKeyboardButton(text=reg, callback_data=cb_data))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    cancel_cb = "close_view" if for_filter else "cancel_action"
    keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data=cancel_cb)])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_ad_kb() -> InlineKeyboardMarkup:
    """E'lonni tasdiqlash yoki bekor qilish"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ E'lonni chop etish (bepul)", callback_data="confirm_ad_publish")],
        [InlineKeyboardButton(text="⭐️ E'lonni VIP sifatida joylash", callback_data="confirm_ad_vip")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ])

def get_single_ad_contact_kb(ad: dict) -> InlineKeyboardMarkup:
    """1-telefon uchun shaxsiy aloqa tugmalari"""
    keyboard = []
    contact_row = []
    username = ad.get("contact_username", "")
    if username:
        clean_user = username.replace("@", "")
        contact_row.append(InlineKeyboardButton(text="✈️ Telegramda yozish", url=f"https://t.me/{clean_user}"))
    
    phone = ad.get("contact_phone", "")
    if phone:
        contact_row.append(InlineKeyboardButton(text="📞 Telefon raqami", callback_data=f"show_phone:{ad['id']}"))

    if contact_row:
        keyboard.append(contact_row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_two_ads_navigation_kb(ad: dict, current_page: int, total_pages: int, total_count: int) -> InlineKeyboardMarkup:
    """2-telefon uchun shaxsiy aloqa tugmalari va navigatsiya paneli"""
    keyboard = []
    
    # 2-telefonning o'zining aloqa tugmalari
    contact_row = []
    username = ad.get("contact_username", "")
    if username:
        clean_user = username.replace("@", "")
        contact_row.append(InlineKeyboardButton(text="✈️ Telegramda yozish", url=f"https://t.me/{clean_user}"))
    
    phone = ad.get("contact_phone", "")
    if phone:
        contact_row.append(InlineKeyboardButton(text="📞 Telefon raqami", callback_data=f"show_phone:{ad['id']}"))

    if contact_row:
        keyboard.append(contact_row)

    # Navigatsiya (Oldingi / Keyingi sahifa)
    nav_row = []
    if current_page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"view_nav:{current_page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"📄 {current_page + 1}/{total_pages} (jami {total_count})", callback_data="ignore"))
    if current_page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"view_nav:{current_page + 1}"))
    
    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([
        InlineKeyboardButton(text="🔍 Brend bo'yicha filter", callback_data="filter_by_brand"),
        InlineKeyboardButton(text="📍 Hudud bo'yicha", callback_data="filter_by_region")
    ])
    keyboard.append([InlineKeyboardButton(text="🌐 Mobil Ilovada ko'rish (Web App)", web_app=WebAppInfo(url=config.WEBAPP_URL))])
    keyboard.append([InlineKeyboardButton(text="❌ Yopish", callback_data="close_view")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_ad_navigation_kb(ad_id: int, current_index: int, total_count: int, seller_username: str, seller_phone: str) -> InlineKeyboardMarkup:
    """Bozor e'lonlarini ko'rish va aloqa tugmalari (bitta e'lon uchun fallback)"""
    keyboard = []
    
    # Aloqa tugmalari
    contact_row = []
    if seller_username:
        clean_user = seller_username.replace("@", "")
        contact_row.append(InlineKeyboardButton(text="✈️ Telegramda yozish", url=f"https://t.me/{clean_user}"))
    if seller_phone:
        contact_row.append(InlineKeyboardButton(text="📞 Telefon raqami", callback_data=f"show_phone:{ad_id}"))
    
    if contact_row:
        keyboard.append(contact_row)

    # Navigatsiya (Oldingi / Keyingi)
    nav_row = []
    if current_index > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"view_nav:{current_index - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"📄 {current_index + 1}/{total_count}", callback_data="ignore"))
    if current_index < total_count - 1:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"view_nav:{current_index + 1}"))
    
    keyboard.append(nav_row)
    keyboard.append([
        InlineKeyboardButton(text="🔍 Brend bo'yicha filter", callback_data="filter_by_brand"),
        InlineKeyboardButton(text="📍 Hudud bo'yicha", callback_data="filter_by_region")
    ])
    keyboard.append([InlineKeyboardButton(text="❌ Yopish", callback_data="close_view")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ==================== AUCTION KEYBOARDS ====================

def get_auction_min_steps_kb() -> InlineKeyboardMarkup:
    """Auksion minimal stavka qadami tanlash"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="+20 000 so'm", callback_data="auc_step:20000"),
            InlineKeyboardButton(text="+50 000 so'm", callback_data="auc_step:50000")
        ],
        [
            InlineKeyboardButton(text="+100 000 so'm", callback_data="auc_step:100000"),
            InlineKeyboardButton(text="+200 000 so'm", callback_data="auc_step:200000")
        ],
        [InlineKeyboardButton(text="✍️ O'zim kiritaman", callback_data="auc_step:custom")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ])

def get_auction_duration_kb() -> InlineKeyboardMarkup:
    """Auksion davomiyligini tanlash"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏱ 6 soat", callback_data="auc_dur:6"),
            InlineKeyboardButton(text="⏱ 12 soat", callback_data="auc_dur:12")
        ],
        [
            InlineKeyboardButton(text="⏱ 24 soat (1 kun)", callback_data="auc_dur:24"),
            InlineKeyboardButton(text="⏱ 2 kun", callback_data="auc_dur:48")
        ],
        [InlineKeyboardButton(text="⏱ 3 kun", callback_data="auc_dur:72")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ])

def get_confirm_auction_kb() -> InlineKeyboardMarkup:
    """Auksionni tasdiqlash"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Auksionni boshlash", callback_data="confirm_auction_start")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ])

def get_auction_navigation_kb(auction: dict, current_index: int, total_count: int, viewer_id: int) -> InlineKeyboardMarkup:
    """Auksion kartasi va stavka berish tugmalari"""
    keyboard = []
    auc_id = auction["id"]
    min_step = auction.get("min_step", 50000)
    curr_price = auction["current_price"]
    curr_winner = auction.get("current_winner_id")
    
    # Agar hali hech kim stavka qo'ymagan bo'lsa
    next_min_bid = curr_price if not curr_winner else curr_price + min_step
    
    is_owner = (auction["user_id"] == viewer_id)
    
    # Stavka berish tugmalari (agar o'zining auksioni bo'lmasa)
    if not is_owner:
        bid_step_1 = next_min_bid
        bid_step_2 = next_min_bid + min_step
        keyboard.append([
            InlineKeyboardButton(text=f"💰 Stavka: {bid_step_1:,} so'm", callback_data=f"bid_quick:{auc_id}:{bid_step_1}"),
            InlineKeyboardButton(text=f"🔥 {bid_step_2:,} so'm", callback_data=f"bid_quick:{auc_id}:{bid_step_2}")
        ])
        keyboard.append([
            InlineKeyboardButton(text="✍️ O'z summani kiritish", callback_data=f"bid_custom:{auc_id}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(text="👑 Bu sizning auksioningiz", callback_data="ignore")
        ])
        
    keyboard.append([
        InlineKeyboardButton(text="📜 Stavkalar tarixi", callback_data=f"auc_history:{auc_id}")
    ])

    # Navigatsiya
    nav_row = []
    if current_index > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"auc_nav:{current_index - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"🔨 {current_index + 1}/{total_count}", callback_data="ignore"))
    if current_index < total_count - 1:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"auc_nav:{current_index + 1}"))

    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton(text="❌ Yopish", callback_data="close_view")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_my_ad_actions_kb(ad_id: int, is_vip: bool) -> InlineKeyboardMarkup:
    """Foydalanuvchining o'z e'loni boshqaruvi"""
    keyboard = []
    if not is_vip:
        keyboard.append([InlineKeyboardButton(text="⭐️ VIP qilish (Tezroq sotish)", callback_data=f"make_vip:{ad_id}")])
    keyboard.append([
        InlineKeyboardButton(text="🟢 Sotildi deb belgilash", callback_data=f"mark_sold:{ad_id}"),
        InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_ad:{ad_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_vip_plans_kb(ad_id: int) -> InlineKeyboardMarkup:
    """VIP tariflar ro'yxati"""
    keyboard = [
        [InlineKeyboardButton(text=f"⭐️ 1 kun — {config.VIP_PRICE_1_DAY:,} so'm", callback_data=f"buy_vip:{ad_id}:1")],
        [InlineKeyboardButton(text=f"⭐️ 2 kun — {config.VIP_PRICE_2_DAYS:,} so'm", callback_data=f"buy_vip:{ad_id}:2")],
        [InlineKeyboardButton(text=f"⭐️ 3 kun — {config.VIP_PRICE_3_DAYS:,} so'm", callback_data=f"buy_vip:{ad_id}:3")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_verify_payment_kb(payment_id: int, ad_id: int, plan_days: int) -> InlineKeyboardMarkup:
    """Admin uchun to'lovni tasdiqlash/rad etish tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ To'lovni tasdiqlash (VIP yoqish)", callback_data=f"adm_appr:{payment_id}:{ad_id}:{plan_days}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_rejc:{payment_id}:{ad_id}")
        ]
    ])

def get_admin_panel_kb() -> InlineKeyboardMarkup:
    """Maxfiy Admin Panel tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 To'liq Statistika", callback_data="adm_stats")],
        [InlineKeyboardButton(text="📢 Barcha foydalanuvchilarga xabar (Broadcast)", callback_data="adm_broadcast")],
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="adm_refresh")]
    ])
