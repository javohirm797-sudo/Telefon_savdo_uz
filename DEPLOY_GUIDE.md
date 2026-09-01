# 🌐 Bepul PostgreSQL va Bepul 24/7 Serverga Joylash Qo'llanmasi

Ushbu qo'llanma orqali botingizni **100% BEPUL bulutli PostgreSQL** bazasiga ulashingiz va kompyuteringizni o'chirib qo'ysangiz ham bot 24 soat to'xtovsiz ishlashi uchun **100% BEPUL serverga** joylashtirishingiz mumkin.

---

## 1-QADAM: 100% Bepul PostgreSQL Bazasi Olish ([Neon.tech](https://neon.tech))

1. Brauzerda **[neon.tech](https://neon.tech)** saytiga kiring.
2. **"Sign Up"** tugmasini bosib, Google yoki GitHub hisobingiz orqali ro'yxatdan o'ting (mutlaqo bepul).
3. Yangi loyiha (Project) yarating:
   - Project name: `telefon-bozor`
   - Region: `Europe (Frankfurt)` yoki o'zingizga yaqin hudud.
   - **"Create project"** tugmasini bosing.
4. Ekranda **Connection Details** (Ulanish ma'lumoti) chiqadi:
   - O'ng tomondan **"Pooled connection"** yoki standart manzilni nusxalang.
   - U quyidagicha ko'rinishda bo'ladi:
     ```
     postgresql://neondb_owner:abc123xyz@ep-cold-sample.eu-central-1.aws.neon.tech/neondb?sslmode=require
     ```
5. Ushbu manzilni loyihangizdagi `.env` faylidagi `DATABASE_URL=` ga joylang:
   ```env
   DATABASE_URL=postgresql://neondb_owner:abc123xyz@ep-cold-sample.eu-central-1.aws.neon.tech/neondb?sslmode=require
   ```
*(Barcha jadvallar bot ishga tushishi bilan Neon PostgreSQL da avtomatik yaratiladi).*

---

## 2-QADAM: Kodlarni GitHub ga Yuklash

1. **[github.com](https://github.com)** ga kiring va yangi repository oching (masalan: `telegram-telefon-savdo-bot`).
2. Kompyuteringizda ushbu papka ichida quyidagi buyruqlarni bering:

```bash
git init
git add .
git commit -m "Initial commit - Telefon Savdo Boti"
git branch -M main
git remote add origin https://github.com/SIZNING_USERNAME/telegram-telefon-savdo-bot.git
git push -u origin main
```

---

## 3-QADAM: 100% Bepul Serverga Joylash ([Render.com](https://render.com))

1. **[render.com](https://render.com)** saytiga kiring va GitHub orqali kiring.
2. Yuqoridagi **"New +"** tugmasini bosing va **"Background Worker"** (yoki **"Web Service"**) ni tanlang.
3. GitHub'dagi `telegram-telefon-savdo-bot` repozitoriyangizni tanlang (**Connect**).
4. Sozlamalarni to'ldiring:
   - **Name**: `telefon-savdo-bot`
   - **Region**: `Frankfurt (EU Central)`
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: `Free` (Bepul)
5. Pastroqqa tushib **"Environment Variables"** (Muhit o'zgaruvchilari) bo'limiga quyidagilarni kiriting:
   - `BOT_TOKEN` = `8959842757:AAFawMAl3d3HbcL7llIDGY3u9XqPf_rJIEU`
   - `ADMIN_IDS` = `8530025653`
   - `ADMIN_PASSWORD` = `Javoh2323..`
   - `DATABASE_URL` = `(1-qadamda Neon.tech dan olgan postgresql://... manzilingiz)`
   - `OWNER_TELEGRAM` = `@JOVIDZE`
   - `OWNER_INSTAGRAM` = `@KURGANSKY_`
   - `OWNER_PHONE` = `+998947762528`
   - `CARD_NUMBER` = `5614-6818-7592-1300`
   - `CARD_HOLDER` = `MAVLONOV JAVOHIR`
   - `VIP_PRICE_1_DAY` = `2999`
   - `VIP_PRICE_2_DAYS` = `3999`
   - `VIP_PRICE_3_DAYS` = `5999`
6. **"Create Background Worker"** (yoki **"Deploy"**) tugmasini bosing!

---

## 4-QADAM: Boshqa Bepul Muqobillar (Alternativalar)

Agar Render.com dan tashqari boshqa joyga qo'ymoqchi bo'lsangiz:
- **[Koyeb.com](https://koyeb.com)** (Bepul, GitHub orqali 2 daqiqada Docker/Python orqali ishlaydi)
- **[Railway.app](https://railway.app)** (Juda oson va tez)
- **[Alwaysdata.com](https://alwaysdata.com)** (100MB bepul Python hosting va PostgreSQL)

---

🎉 **Natija**: Botingiz bulutli PostgreSQL bazasiga ulanadi va 24/7 internetda mutlaqo bepul uzluksiz ishlaydi!
