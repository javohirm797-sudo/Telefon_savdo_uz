import logging
import datetime
from typing import Optional, List, Dict, Any
import asyncpg
import aiosqlite
import config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.is_postgres = False
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.sqlite_db_path = "bot_database.sqlite3"

    async def connect(self):
        """PostgreSQL ga ulanishga harakat qiladi, bo'lmasa SQLite ga ulanadi"""
        try:
            logger.info("PostgreSQL ga ulanish urinilmoqda...")
            db_url = config.DATABASE_URL
            
            # Agar DATABASE_URL berilgan bo'lsa (Neon, Supabase, Render va h.k.)
            if db_url and "localhost" not in db_url and db_url.startswith("postgres"):
                clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
                # asyncpg qo'llab-quvvatlamaydigan qo'shimcha parametrlarni tozalash
                if "channel_binding=" in clean_url:
                    clean_url = clean_url.split("&channel_binding=")[0].split("?channel_binding=")[0]
                
                self.pg_pool = await asyncpg.create_pool(
                    dsn=clean_url,
                    min_size=1,
                    max_size=10,
                    timeout=15.0
                )
            else:
                self.pg_pool = await asyncpg.create_pool(
                    host=config.DB_HOST,
                    port=config.DB_PORT,
                    user=config.DB_USER,
                    password=config.DB_PASSWORD,
                    database=config.DB_NAME,
                    min_size=1,
                    max_size=10,
                    timeout=5.0
                )
            self.is_postgres = True
            logger.info("✅ PostgreSQL ma'lumotlar bazasiga muvaffaqiyatli ulandi!")
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL ga ulanib bo'lmadi ({e}). SQLite bazasiga ulanilmoqda...")
            self.is_postgres = False
            self.pg_pool = None

        await self.create_tables()

    async def create_tables(self):
        """Jadvallarni yaratish"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                # Foydalanuvchilar jadvali
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        telegram_id BIGINT UNIQUE NOT NULL,
                        full_name TEXT NOT NULL,
                        phone_number TEXT NOT NULL,
                        username TEXT,
                        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_blocked BOOLEAN DEFAULT FALSE
                    );
                """)
                # E'lonlar jadvali
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS ads (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        brand TEXT NOT NULL,
                        model TEXT NOT NULL,
                        condition TEXT NOT NULL,
                        memory TEXT NOT NULL,
                        battery TEXT,
                        color TEXT,
                        price TEXT NOT NULL,
                        region TEXT NOT NULL,
                        photo_id TEXT NOT NULL,
                        description TEXT,
                        contact_phone TEXT NOT NULL,
                        contact_username TEXT,
                        is_vip BOOLEAN DEFAULT FALSE,
                        vip_until TIMESTAMP,
                        status VARCHAR(20) DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                # VIP to'lovlar jadvali
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS vip_payments (
                        id SERIAL PRIMARY KEY,
                        ad_id INTEGER NOT NULL,
                        user_id BIGINT NOT NULL,
                        plan_days INTEGER NOT NULL,
                        amount INTEGER NOT NULL,
                        receipt_photo_id TEXT NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        reviewed_at TIMESTAMP
                    );
                """)
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER UNIQUE NOT NULL,
                        full_name TEXT NOT NULL,
                        phone_number TEXT NOT NULL,
                        username TEXT,
                        registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_blocked BOOLEAN DEFAULT 0
                    );
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS ads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        brand TEXT NOT NULL,
                        model TEXT NOT NULL,
                        condition TEXT NOT NULL,
                        memory TEXT NOT NULL,
                        battery TEXT,
                        color TEXT,
                        price TEXT NOT NULL,
                        region TEXT NOT NULL,
                        photo_id TEXT NOT NULL,
                        description TEXT,
                        contact_phone TEXT NOT NULL,
                        contact_username TEXT,
                        is_vip BOOLEAN DEFAULT 0,
                        vip_until DATETIME,
                        status TEXT DEFAULT 'active',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS vip_payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ad_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        plan_days INTEGER NOT NULL,
                        amount INTEGER NOT NULL,
                        receipt_photo_id TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        reviewed_at DATETIME
                    );
                """)
                await conn.commit()

    # ==================== USERS METHODS ====================

    async def add_user(self, telegram_id: int, full_name: str, phone_number: str, username: Optional[str] = None):
        """Yangi foydalanuvchi qo'shish yoki yangilash"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO users (telegram_id, full_name, phone_number, username)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (telegram_id) DO UPDATE 
                    SET full_name = $2, phone_number = $3, username = $4;
                """, telegram_id, full_name, phone_number, username)
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                await conn.execute("""
                    INSERT INTO users (telegram_id, full_name, phone_number, username)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(telegram_id) DO UPDATE 
                    SET full_name = excluded.full_name, phone_number = excluded.phone_number, username = excluded.username;
                """, (telegram_id, full_name, phone_number, username))
                await conn.commit()

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Foydalanuvchini olish"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1;", telegram_id)
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute("SELECT * FROM users WHERE telegram_id = ?;", (telegram_id,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None

    async def get_all_users_count(self) -> int:
        """Jami foydalanuvchilar soni"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                return await conn.fetchval("SELECT COUNT(*) FROM users;")
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                async with conn.execute("SELECT COUNT(*) FROM users;") as cursor:
                    res = await cursor.fetchone()
                    return res[0] if res else 0

    async def get_all_user_ids(self) -> List[int]:
        """Xabar tarqatish uchun barcha user ID lari"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch("SELECT telegram_id FROM users WHERE is_blocked = FALSE;")
                return [r["telegram_id"] for r in rows]
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                async with conn.execute("SELECT telegram_id FROM users WHERE is_blocked = 0;") as cursor:
                    rows = await cursor.fetchall()
                    return [r[0] for r in rows]

    # ==================== ADS METHODS ====================

    async def add_ad(self, data: Dict[str, Any]) -> int:
        """Yangi e'lon qo'shish"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                ad_id = await conn.fetchval("""
                    INSERT INTO ads (
                        user_id, brand, model, condition, memory, battery, 
                        color, price, region, photo_id, description, 
                        contact_phone, contact_username, is_vip, status
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                    ) RETURNING id;
                """, 
                data["user_id"], data["brand"], data["model"], data["condition"],
                data["memory"], data.get("battery", "—"), data.get("color", "—"),
                data["price"], data["region"], data["photo_id"], data.get("description", ""),
                data["contact_phone"], data.get("contact_username", ""),
                data.get("is_vip", False), "active"
                )
                return ad_id
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                cursor = await conn.execute("""
                    INSERT INTO ads (
                        user_id, brand, model, condition, memory, battery, 
                        color, price, region, photo_id, description, 
                        contact_phone, contact_username, is_vip, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    data["user_id"], data["brand"], data["model"], data["condition"],
                    data["memory"], data.get("battery", "—"), data.get("color", "—"),
                    data["price"], data["region"], data["photo_id"], data.get("description", ""),
                    data["contact_phone"], data.get("contact_username", ""),
                    1 if data.get("is_vip", False) else 0, "active"
                ))
                await conn.commit()
                return cursor.lastrowid

    async def get_ad_by_id(self, ad_id: int) -> Optional[Dict[str, Any]]:
        """E'lonni ID bo'yicha olish"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM ads WHERE id = $1;", ad_id)
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute("SELECT * FROM ads WHERE id = ?;", (ad_id,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None

    async def get_active_ads(self, brand: Optional[str] = None, model: Optional[str] = None, region: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Aktiv e'lonlarni olish (VIP e'lonlar birinchi chiqadi)"""
        conditions = ["status = 'active'"]
        params = []

        if brand and brand != "Barcha brendlar":
            params.append(brand)
            conditions.append(f"brand = ${len(params)}" if self.is_postgres else "brand = ?")

        if model and model != "Barcha modellar":
            params.append(model)
            conditions.append(f"model = ${len(params)}" if self.is_postgres else "model = ?")

        if region and region != "Barcha viloyatlar":
            params.append(region)
            conditions.append(f"region = ${len(params)}" if self.is_postgres else "region = ?")

        where_clause = " AND ".join(conditions)

        if self.is_postgres:
            query = f"""
                SELECT * FROM ads 
                WHERE {where_clause}
                ORDER BY is_vip DESC, id DESC
                LIMIT ${len(params)+1} OFFSET ${len(params)+2};
            """
            params.extend([limit, offset])
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(r) for r in rows]
        else:
            query = f"""
                SELECT * FROM ads 
                WHERE {where_clause}
                ORDER BY is_vip DESC, id DESC
                LIMIT ? OFFSET ?;
            """
            params.extend([limit, offset])
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(r) for r in rows]

    async def get_active_ads_count(self, brand: Optional[str] = None, model: Optional[str] = None, region: Optional[str] = None) -> int:
        """Aktiv e'lonlar soni"""
        conditions = ["status = 'active'"]
        params = []

        if brand and brand != "Barcha brendlar":
            params.append(brand)
            conditions.append(f"brand = ${len(params)}" if self.is_postgres else "brand = ?")

        if model and model != "Barcha modellar":
            params.append(model)
            conditions.append(f"model = ${len(params)}" if self.is_postgres else "model = ?")

        if region and region != "Barcha viloyatlar":
            params.append(region)
            conditions.append(f"region = ${len(params)}" if self.is_postgres else "region = ?")

        where_clause = " AND ".join(conditions)

        if self.is_postgres:
            query = f"SELECT COUNT(*) FROM ads WHERE {where_clause};"
            async with self.pg_pool.acquire() as conn:
                return await conn.fetchval(query, *params)
        else:
            query = f"SELECT COUNT(*) FROM ads WHERE {where_clause};"
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                async with conn.execute(query, params) as cursor:
                    res = await cursor.fetchone()
                    return res[0] if res else 0

    async def get_user_ads(self, user_id: int) -> List[Dict[str, Any]]:
        """Foydalanuvchining o'z e'lonlari"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM ads 
                    WHERE user_id = $1 AND status != 'deleted'
                    ORDER BY id DESC;
                """, user_id)
                return [dict(r) for r in rows]
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute("""
                    SELECT * FROM ads 
                    WHERE user_id = ? AND status != 'deleted'
                    ORDER BY id DESC;
                """, (user_id,)) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(r) for r in rows]

    async def update_ad_status(self, ad_id: int, status: str):
        """E'lon holatini yangilash (active, sold, deleted)"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("UPDATE ads SET status = $1 WHERE id = $2;", status, ad_id)
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                await conn.execute("UPDATE ads SET status = ? WHERE id = ?;", (status, ad_id))
                await conn.commit()

    async def set_ad_vip(self, ad_id: int, days: int):
        """E'lonni VIP qilish va muddatini belgilash"""
        vip_until = datetime.datetime.now() + datetime.timedelta(days=days)
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE ads 
                    SET is_vip = TRUE, vip_until = $1 
                    WHERE id = $2;
                """, vip_until, ad_id)
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                await conn.execute("""
                    UPDATE ads 
                    SET is_vip = 1, vip_until = ? 
                    WHERE id = ?;
                """, (vip_until.isoformat(), ad_id))
                await conn.commit()

    # ==================== VIP PAYMENTS METHODS ====================

    async def add_vip_payment(self, ad_id: int, user_id: int, plan_days: int, amount: int, receipt_photo_id: str) -> int:
        """Yangi VIP to'lov so'rovi qo'shish"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                payment_id = await conn.fetchval("""
                    INSERT INTO vip_payments (ad_id, user_id, plan_days, amount, receipt_photo_id, status)
                    VALUES ($1, $2, $3, $4, $5, 'pending')
                    RETURNING id;
                """, ad_id, user_id, plan_days, amount, receipt_photo_id)
                return payment_id
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                cursor = await conn.execute("""
                    INSERT INTO vip_payments (ad_id, user_id, plan_days, amount, receipt_photo_id, status)
                    VALUES (?, ?, ?, ?, ?, 'pending');
                """, (ad_id, user_id, plan_days, amount, receipt_photo_id))
                await conn.commit()
                return cursor.lastrowid

    async def get_vip_payment(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """VIP to'lov so'rovini olish"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM vip_payments WHERE id = $1;", payment_id)
                return dict(row) if row else None
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.execute("SELECT * FROM vip_payments WHERE id = ?;", (payment_id,)) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None

    async def update_vip_payment_status(self, payment_id: int, status: str):
        """VIP to'lov holatini yangilash ('approved', 'rejected')"""
        now = datetime.datetime.now()
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE vip_payments 
                    SET status = $1, reviewed_at = $2 
                    WHERE id = $3;
                """, status, now, payment_id)
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                await conn.execute("""
                    UPDATE vip_payments 
                    SET status = ?, reviewed_at = ? 
                    WHERE id = ?;
                """, (status, now.isoformat(), payment_id))
                await conn.commit()

    # ==================== STATS METHODS ====================

    async def get_stats(self) -> Dict[str, Any]:
        """Admin panel uchun to'liq statistika"""
        if self.is_postgres:
            async with self.pg_pool.acquire() as conn:
                total_users = await conn.fetchval("SELECT COUNT(*) FROM users;")
                total_ads = await conn.fetchval("SELECT COUNT(*) FROM ads WHERE status != 'deleted';")
                active_ads = await conn.fetchval("SELECT COUNT(*) FROM ads WHERE status = 'active';")
                vip_ads = await conn.fetchval("SELECT COUNT(*) FROM ads WHERE is_vip = TRUE AND status = 'active';")
                sold_ads = await conn.fetchval("SELECT COUNT(*) FROM ads WHERE status = 'sold';")
                pending_payments = await conn.fetchval("SELECT COUNT(*) FROM vip_payments WHERE status = 'pending';")
                total_earned = await conn.fetchval("SELECT COALESCE(SUM(amount), 0) FROM vip_payments WHERE status = 'approved';")
                return {
                    "total_users": total_users,
                    "total_ads": total_ads,
                    "active_ads": active_ads,
                    "vip_ads": vip_ads,
                    "sold_ads": sold_ads,
                    "pending_payments": pending_payments,
                    "total_earned": total_earned,
                    "db_type": "PostgreSQL"
                }
        else:
            async with aiosqlite.connect(self.sqlite_db_path) as conn:
                async with conn.execute("SELECT COUNT(*) FROM users;") as c:
                    total_users = (await c.fetchone())[0]
                async with conn.execute("SELECT COUNT(*) FROM ads WHERE status != 'deleted';") as c:
                    total_ads = (await c.fetchone())[0]
                async with conn.execute("SELECT COUNT(*) FROM ads WHERE status = 'active';") as c:
                    active_ads = (await c.fetchone())[0]
                async with conn.execute("SELECT COUNT(*) FROM ads WHERE is_vip = 1 AND status = 'active';") as c:
                    vip_ads = (await c.fetchone())[0]
                async with conn.execute("SELECT COUNT(*) FROM ads WHERE status = 'sold';") as c:
                    sold_ads = (await c.fetchone())[0]
                async with conn.execute("SELECT COUNT(*) FROM vip_payments WHERE status = 'pending';") as c:
                    pending_payments = (await c.fetchone())[0]
                async with conn.execute("SELECT COALESCE(SUM(amount), 0) FROM vip_payments WHERE status = 'approved';") as c:
                    total_earned = (await c.fetchone())[0]
                return {
                    "total_users": total_users,
                    "total_ads": total_ads,
                    "active_ads": active_ads,
                    "vip_ads": vip_ads,
                    "sold_ads": sold_ads,
                    "pending_payments": pending_payments,
                    "total_earned": total_earned,
                    "db_type": "SQLite (Fayl)"
                }

# Global DB instance
db = Database()
