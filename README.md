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
│   │       ├── human.py
│   │       ├── videos.py
│   │       ├── video.py
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
│   └── services
│       ├── user_service.py
│       ├── synthetic_human_service.py
│       ├── video_service.py
│       ├── scraper_service.py
│       ├── scraper
│           ├── competitor_watch.py
│           ├── trend_forecast.py
│           ├── intent_detector.py
│           ├── emotion_analyzer.py
│           ├── competitor_hole.py
│           ├── intent_scorer.py
│           ├── queue.py
│           └── engine.py
│       └── video
│           ├── synthetic_human.py
│           ├── video_generator.py
│           ├── face_swap.py
│           ├── audio_engine.py
│           ├── queue.py
│           ├── manager.py
│           ├── tasks.py
│           └── templates
│               ├── template_video.py
│               └── cinematic_styles.py
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
- Celery Worker: queue `video_render_jobs` dan `scraper_jobs`

### Melihat log backend (aman untuk Compose v1/v2)

Gunakan format ini agar tidak kena error `No such service: --tail`:

```bash
docker-compose logs --tail=50 backend
```

atau untuk Compose v2:

```bash
docker compose logs --tail=50 backend
```

Alternatif cepat lewat Makefile:

```bash
make logs-backend
make logs-worker
```

### Smoke-test backend

Jalankan smoke-test import + endpoint health:

```bash
make smoke
```

Jika ingin cek impor Python saja (tanpa HTTP):

```bash
make smoke-import
```

Untuk cek tambahan endpoint scraper async (butuh Redis/Celery aktif):

```bash
make smoke-scraper
```

### Scraper async (terkoneksi Redis + Celery)

Untuk menjalankan scraper di background worker, panggil endpoint:

```bash
POST /api/v1/scraper/analyze?run_async=true
```

Lalu pantau status:

```bash
GET /api/v1/scraper/status/{job_id}
```

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
- `GET /health/dependencies`
- `POST /users`
- `GET /users`
- `POST /synthetic-humans`
- `GET /synthetic-humans`
- `POST /videos`
- `GET /videos`
- `POST /scraper-data`
- `GET /scraper-data`
- `POST /scraper/analyze`
- `GET /scraper/insights`
- `GET /scraper/status/{job_id}`
- `POST /video/generate`
- `POST /video/swap-face`
- `POST /video/lip-sync`
- `GET /video/status/{job_id}`
- `POST /human/create`
- `GET /human/list`
- `POST /human/train`

## Verifikasi Sinkronisasi Service

Setelah `docker compose up --build`, verifikasi koneksi antar service:

```bash
curl -s http://localhost:8000/api/v1/health/dependencies | jq
```

Output `status: "ok"` berarti backend, PostgreSQL, Redis, dan Celery broker sudah sinkron.

## Catatan

- Tabel database dibuat otomatis saat aplikasi startup.
- Password user di-hash menggunakan `passlib` (bcrypt).
