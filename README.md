# Autoviral

Backend starter untuk proyek **Autoviral** menggunakan **FastAPI**, **SQLAlchemy**, **PostgreSQL**, dan **Redis**.

## Struktur Proyek

```text
.
├── backend
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   ├── api
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── endpoints
│   │       ├── health.py
│   │       ├── users.py
│   │       ├── synthetic_humans.py
│   │       ├── videos.py
│   │       └── scraper_data.py
│   ├── core
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models
│   │   ├── user.py
│   │   ├── synthetic_human.py
│   │   ├── video.py
│   │   └── scraper_data.py
│   ├── tests
│   │   ├── conftest.py
│   │   └── test_api.py
│   └── services
│       ├── user_service.py
│       ├── synthetic_human_service.py
│       ├── video_service.py
│       └── scraper_service.py
└── docker-compose.yml
```

## Model Database

Model SQLAlchemy yang disiapkan:

- `User`: `id`, `email`, `password_hash`, `name`, `created_at`
- `SyntheticHuman`: `id`, `name`, `age`, `gender`, `style`, `user_id`
- `Video`: `id`, `title`, `status`, `file_path`, `human_id`, `user_id`
- `ScraperData`: `id`, `source`, `topic`, `intent_score`, `raw_data`

## Menjalankan dengan Docker Compose (Direkomendasikan)

Jalankan dari root proyek:

```bash
docker compose up --build
```

Service yang tersedia:

- Backend FastAPI: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

## Menjalankan Secara Lokal (Tanpa Docker)

1. Masuk folder backend:

   ```bash
   cd backend
   ```

2. Buat virtual environment dan aktifkan:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependency:

   ```bash
   pip install -r requirements.txt
   ```

4. (Opsional) salin environment:

   ```bash
   cp .env.example .env
   ```

5. Jalankan aplikasi:

   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

6. Buka dokumentasi API:

   - `http://localhost:8000/docs`

## Endpoint Utama

Base path API: `/api/v1`

- `GET /health`
- `POST /users`
- `GET /users`
- `POST /synthetic-humans`
- `GET /synthetic-humans`
- `POST /videos`
- `GET /videos`
- `POST /scraper-data`
- `GET /scraper-data`

## Menjalankan Test Otomatis

Jalankan dari root proyek:

```bash
python3 -m pip install -r backend/requirements.txt
python3 -m pytest -q backend/tests
```

## Catatan

- Tabel database dibuat otomatis saat aplikasi startup.
- Password user di-hash menggunakan `passlib` dengan skema `pbkdf2_sha256`.
