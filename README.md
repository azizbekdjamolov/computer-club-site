# Computer Club Management System

Zamonaviy va professional kompyuter xonasi / computer club boshqaruv tizimi.

## Texnologiyalar

- Backend: Django 5.2
- Database: SQLite (locally) / PostgreSQL (Render production)
- Frontend: HTML5, CSS3 (+ dark/light theme), JavaScript (vanilla)
- Static & speed: WhiteNoise (compressed static), DB indexes, optimized queries
- Charts: Chart.js
- Font: Inter, Icons: Font Awesome
- Server: Gunicorn (production)

## Imkoniyatlar

- **Dashboard**: daromad, band/bosh kompyuterlar, mijozlar, qarzdorlar, xarajatlar, sof foyda
- **Xonalar**: har bir xonaga alohida soatlik narx
- **Kompyuterlar**: bosh / band / rezerv / nosoz holatlari
- **Mijozlar**: tarix, jami sarf, qarz
- **Sessiyalar**: real vaqt hisoblash, stop/add payment, avtomatik bo'shatish
- **To'lovlar**: cash, card, click, payme, uzcard, humo; qaytim hisoblash
- **Rezervatsiyalar**: vaqt conflict tekshiruvlari
- **Xarajatlar**: kategoriyalar bo'yicha
- **Hisobotlar**: kunlik/haftalik/oylik, grafiklar
- **Sozlamalar**: klub nomi, valyuta, auto-refresh, dark mode
- **Global qidiruv** va **notificationlar** (tugashga yaqin sessiya, qarzdorlik)

## Ishlatilgan dastlabki qadamlar (local dev)

```bash
# 1. Virtual environment (ixtiyoriy)
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Paketlarni o'rnatish
pip install -r requirements.txt

# 3. Migratsiya va superuser
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# 4. (Ixtiyoriy) Demo ma'lumotlar
python manage.py loaddata core/fixtures/initial.json

# 5. Ishga tushirish
python manage.py runserver
```

Brauzerda `http://127.0.0.1:8000/` oching va login qiling.
Admin panel: `http://127.0.0.1:8000/admin/`

## Render.com ga deploy qilish (BEPUL)

Loyihada `render.yaml` Blueprint va `build.sh` tayyor. 2 xil usul:

### 1-usul: Blueprint (avtomatik, tavsiya etiladi)

1. Kodni GitHub repo ga push qiling (masalan `computer-club`).
2. [render.com](https://render.com) ga kiring va "New +" -> "Blueprint" ni tanlang.
3. Repo ni tanlang - Render `render.yaml` ni topib, Web Service + PostgreSQL ni avtomatik yaratadi.
4. **Deploy** tugmasini bosing. Taxminan 3-5 daqiqada tayyor.
5. Birinchi marta superuser: Render dashboard -> Service -> **Shell** tab:
   ```
   python manage.py createsuperuser
   ```
6. Yaratilgan URL (`https://computer-club.onrender.com`) oching va login qiling.

### 2-usul: Manual Web Service

1. Render -> "New +" -> "Web Service" -> GitHub repo.
2. Quyidagilarni kiriting:
   - Build Command: `./build.sh`
   - Start Command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 90`
   - Instance Type: Free
3. Env vars:
   - `DJANGO_SECRET_KEY` = (strong random string)
   - `DJANGO_DEBUG` = `False`
   - `DJANGO_ALLOWED_HOSTS` = `*`
   - `DJANGO_TIME_ZONE` = `Asia/Tashkent`
4. Database: Render -> "New +" -> "PostgreSQL" (Free). Qoshilgan PostgreSQL "Internal Database" orqali Web Service ga ulang.
5. Deploy.

## PostgreSQL ga otish (local)

```bash
# Render server ulanish yoki local Postgres
set DATABASE_URL=postgres://user:password@host:5432/dbname   # Windows
# export DATABASE_URL=postgres://...                          # Linux/Mac
python manage.py migrate
```

Yoki env vars orqali: `DB_ENGINE=postgres`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

## Loyiha tuzilishi

```
config/            # settings, urls, wsgi/asgi
core/              # asosiy ilova (models, views, forms, admin, urls, signals)
static/            # CSS va JavaScript
templates/         # HTML shablonlar
core/fixtures/     # demo ma'lumotlar (ixtiyoriy)
render.yaml        # Render Blueprint
build.sh           # Render build skripti
Procfile           # Render start komandasi
requirements.txt
```

## Tez ishlash uchun optimallashtirish

- DB indekslari: session(status, start_time), computer(status), payment(session, created_at), reservation, expense
- Dashboard: `select_related` / `prefetch_related` bilan N+1 savollar yo'q
- Hisobot: kunlik daromad bitta grouped SQL savol orqali (14 ta savol orniga 1 ta)
- Static fayllar: WhiteNoise compressed + manifest
- Gunicorn: 2 worker + 4 thread
- PostgreSQL: `CONN_MAX_AGE=600` (ulanish qayta ishlatiladi)

## Izoh

- Hisob-kitoblar backendda (Django) amalga oshiriladi; JavaScript faqat displey uchun.
- Session tugatilganda kompyuter avtomatik `available` bo'ladi (signal orqali).
- Bitta kompyuterda bir vaqtning o'zida bitta faol sessiya bo'ladi (tekshiruv mavjud).